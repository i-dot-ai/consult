"""CLI script to set up a new consultation for ThemeFinder.

Pipeline overview
-----------------
Given a consultation's raw response file (CSV/XLSX) and its Question
Understanding (Q.U.) workbook, this script:

  1. **Loads** the responses file. Auto-detects the three layout patterns
     we see in practice (single header, header + blank separator, two-tier
     header). Renames columns to Excel letters (A, B, ..., AA, ...) and
     adds a ``themefinder_id``.
  2. **Loads** the Q.U. workbook's Demographic / Open / Hybrid /
     Multiple Choice sheets. Auto-detects the optional instruction
     sub-header row that some templates carry.
  3. **Numbers** questions: uses ``question_number`` from the Q.U. sheet
     when every value parses as an integer; otherwise falls back to
     numbering by Excel-column order. Numbers must be globally unique
     because they become output directory names.
  4. **Validates** Q.U. against the responses (see
     ``setup_consultation_checks.md`` for the full rule list). On any
     issue, prompts before continuing — unless ``--until validate`` is
     passed, in which case it just reports.
  5. **Builds** the ThemeFinder input layout under
     ``<consultation>/inputs/``: ``respondents.jsonl`` plus a
     ``question_part_<n>/`` per question with ``question.json``,
     ``responses.jsonl`` and/or ``multi_choice.jsonl``.
  6. **Uploads** the inputs to ``s3://i-dot-ai-prod-consult-data/
     app_data/consultations/<name>/inputs/`` (gated by an interactive
     "proceed?" prompt; warns if data already exists at that prefix).

Usage
-----
Run from the consult repo root via::

    make setup-consultation name=my_consultation

or directly::

    cd backend && uv run python ../scripts/setup_consultation.py my_consultation

Stop early with ``--until validate`` (skip build + upload) or
``--until build`` (skip upload only). Pass ``--responses`` and ``--qu``
to bypass interactive file selection.
"""

import argparse
import json
import logging
import re
import sys
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import boto3
import botocore.exceptions
import pandas as pd

logger = logging.getLogger(__name__)


CONFLUENCE_URL = "https://incubatorforartificialintelligence.atlassian.net/wiki/spaces/Consult/pages/136445956/1.2+Set+up+the+consultation+in+the+app"

VALID_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# Maps question type -> list of column-ID fields in the Q.U. sheet.
COL_ID_FIELDS: dict[str, list[str]] = {
    "open": ["column_name"],
    "hybrid": ["open_column", "closed_column"],
    "closed": ["column_name"],
}

# The primary column used for sorting/numbering (first entry in each list).
PRIMARY_COL_ID_FIELD: dict[str, str] = {
    key: fields[0] for key, fields in COL_ID_FIELDS.items()
}

# Sheet name(s), expected column count, and column names for each Q.U. sheet type.
# First name in each tuple is the canonical (current) name; subsequent entries
# are legacy aliases we still accept when loading older workbooks.
QU_SHEET_SPECS: dict[str, tuple[tuple[str, ...], int, list[str]]] = {
    "open": (
        ("Open Questions", "Open questions"),
        3,
        ["column_name", "question_number", "question_text"],
    ),
    "hybrid": (
        ("Hybrid Questions", "Hybrid questions"),
        4,
        ["open_column", "question_number", "question_text", "closed_column"],
    ),
    "closed": (
        ("Multiple Choice Questions", "Multiple Choice"),
        3,
        ["column_name", "question_number", "question_text"],
    ),
}

DEMOGRAPHIC_SHEET_ALIASES: tuple[str, ...] = ("Demographics", "Demographic")

# Characters stripped from free-text columns during ingestion.
CHARACTERS_TO_REMOVE: list[str] = ["/", "\\", "- Text", "_x000D_"]

# Values that signify a missing/blank response. Matched case-insensitively
# after stripping whitespace and surrounding punctuation.
NULL_LIKE_VALUES: frozenset[str] = frozenset(
    {
        "",
        "-",
    }
)


def _normalise_null_like(df: pd.DataFrame) -> pd.DataFrame:
    """Replace null-type signifiers (the values in ``NULL_LIKE_VALUES``) with NaN.

    Operates only on object/string columns and leaves the themefinder_id alone.
    Comparison is done on a stripped, lowercased copy so we don't lose the
    original casing of real responses. Today the matched values are ``""`` and
    ``"-"``; if more signifiers turn up in real data (e.g. ``"n/a"``,
    ``"none"``), add them to ``NULL_LIKE_VALUES``.
    """
    for col in df.columns:
        if col == "themefinder_id":
            continue
        if not (
            pd.api.types.is_object_dtype(df[col])
            or pd.api.types.is_string_dtype(df[col])
        ):
            continue
        stripped = df[col].astype(str).str.strip().str.lower()
        mask = stripped.isin(NULL_LIKE_VALUES) & df[col].notna()
        if mask.any():
            df.loc[mask, col] = pd.NA
    return df


def to_snake_case(s: str) -> str:
    """Convert a string to snake_case."""
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    s = re.sub(r"[\s\-]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_").lower()


# --- Data processing functions ---


def get_excel_column_name(n: int) -> str:
    """Convert number to Excel column name (e.g., 0->A, 25->Z, 26->AA)."""
    result = ""
    n += 1
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def excel_column_to_number(col: str) -> int:
    """Convert Excel column name to number for sorting (A=1, Z=26, AA=27).

    Raises TypeError if `col` is not a str, and ValueError if it is empty
    or contains any character outside A-Z / a-z.
    """
    if not isinstance(col, str):
        raise TypeError(f"col must be str, got {type(col).__name__}")
    if not col:
        raise ValueError(f"col must be a non-empty string, got {col!r}")
    result = 0
    for c in col.upper():
        if not ("A" <= c <= "Z"):
            raise ValueError(f"invalid character {c!r} in column {col!r}")
        result = result * 26 + (ord(c) - ord("A") + 1)
    return result


# Matches valid Excel column IDs: 1-3 uppercase letters, possibly with trailing whitespace.
# Used to distinguish real data rows from instruction sub-header rows in Q.U. files.
_EXCEL_COL_RE = re.compile(r"^[A-Z]{1,3}\s*$")


def _load_qu_sheet(
    path: Path,
    sheet_name: str | tuple[str, ...],
    n_columns: int,
    column_names: list[str],
) -> pd.DataFrame | None:
    """Load a single sheet from a Question Understanding Excel file.

    Supports both the legacy layout (3 preamble rows + optional instruction
    sub-header row, then data) and the current template (single header row,
    then data). We auto-detect the data start by scanning for the first row
    whose first cell is a valid Excel column ID (e.g. "A", "AC", "BF").
    Any preamble / header / instruction rows above that are discarded.

    `sheet_name` may be a single name or a tuple of candidate names (used to
    accept legacy sheet titles like "Multiple Choice" alongside the current
    "Multiple Choice Questions").
    """
    candidates = (sheet_name,) if isinstance(sheet_name, str) else sheet_name
    df = None
    matched_name = None
    for candidate in candidates:
        try:
            df = pd.read_excel(path, sheet_name=candidate, header=None)
            matched_name = candidate
            break
        except ValueError:
            # pandas raises ValueError("Worksheet named '...' not found") when
            # the sheet is absent. Real I/O / parse errors are not caught here.
            continue
    if df is None:
        return None

    if df.empty:
        return None

    # Only keep the columns we expect — some files have extra unnamed columns
    # (e.g. abbreviated titles or notes in columns 4-5 of Multiple Choice)
    df = df.iloc[:, :n_columns]

    # Drop fully-empty rows (preamble blank rows and trailing empties)
    df = df.dropna(how="all").reset_index(drop=True)

    if df.empty:
        return None

    # Find the first row whose leading cell looks like an Excel column letter.
    # Everything above it is preamble / header / instruction text.
    data_start = None
    for i in range(len(df)):
        if _EXCEL_COL_RE.match(str(df.iloc[i, 0]).strip()):
            data_start = i
            break
    if data_start is None:
        return None
    if data_start > 0:
        logger.info(
            "Skipping %d preamble row(s) on sheet '%s'", data_start, matched_name
        )
        df = df.iloc[data_start:].reset_index(drop=True)

    if df.empty:
        return None

    df.columns = column_names

    # Strip whitespace from column-ID fields — some files have "C " instead of "C"
    for col in column_names:
        if "column" in col.lower():
            df[col] = df[col].astype(str).str.strip()

    return df


def _parse_question_numbers(values: pd.Series) -> list[int] | None:
    """Try to parse question numbers from a Series. Returns list of ints or None if any fail."""
    parsed = []
    for val in values.astype(str):
        try:
            parsed.append(int(val.strip()))
        except ValueError:
            return None
    return parsed


def _extract_numbers(text: str) -> list[int]:
    """Extract all integers from a string."""
    return [int(x) for x in re.findall(r"\d+", str(text))]


def validate_data(
    question_sheets: dict[str, pd.DataFrame],
    original_headers: dict[str, str],
    responses_df: pd.DataFrame,
    demographic_columns: list[str] | None = None,
    demographic_labels: list[str] | None = None,
    interactive: bool = True,
) -> None:
    """Validate Q.U. sheets against response data.

    Prints summaries of responses and Q.U. sheets, then checks for:
    - Q.U. columns that don't exist in the response data
    - More Q.U. columns referenced than response columns available
    - Duplicate column references across Q.U. sheets
    - Low string similarity between Q.U. labels and response headers
    - Mismatched numbers extracted from Q.U. labels vs response headers
    - Demographic column value distributions
    - Response columns not referenced by any question or demographic
    If any issues found, prompts user to confirm before continuing.
    """
    issues: list[str] = []

    # ── Response summary ──────────────────────────────────────────────
    n_rows, n_cols = responses_df.shape
    resp_col_count = n_cols - 1  # exclude themefinder_id
    total_cells = n_rows * resp_col_count
    nan_count = int(responses_df.drop(columns=["themefinder_id"]).isna().sum().sum())
    nan_pct = (nan_count / total_cells * 100) if total_cells else 0
    print(
        f"\n  Response data: {n_rows} rows x {resp_col_count} cols, "
        f"{nan_count}/{total_cells} NaN ({nan_pct:.1f}%)"
    )

    # ── Demographics ──────────────────────────────────────────────────
    if demographic_columns and demographic_labels:
        print(f"\n  Demographics ({len(demographic_columns)} field(s)):")
        for col_id, label in zip(demographic_columns, demographic_labels):
            if col_id not in responses_df.columns:
                print(f"    ✗ {label} (col {col_id}) — not found in response data")
                issues.append(
                    f"Demographic column {col_id} ({label}) not in response data"
                )
                continue
            series = responses_df[col_id].fillna("Not Provided")
            n_unique = series.nunique()
            n_missing = int((series == "Not Provided").sum())
            missing_pct = n_missing / n_rows * 100 if n_rows else 0
            print(
                f"    {label} (col {col_id}): {n_unique} unique, {n_missing} missing ({missing_pct:.1f}%)"
            )
            for value, count in series.value_counts().head(5).items():
                pct = count / n_rows * 100
                print(f"      {value}: {count} ({pct:.1f}%)")

    # ── Q.U. summary ────────────────────────────────────────────────────
    all_qu_columns: set[str] = set()
    total_questions = 0
    print("\n  Question Understanding:")
    for sheet_key, df in question_sheets.items():
        n_questions = len(df)
        total_questions += n_questions
        cols_in_sheet: set[str] = set()
        for col_field in COL_ID_FIELDS[sheet_key]:
            cols_in_sheet.update(df[col_field].astype(str).str.strip().tolist())
        all_qu_columns.update(cols_in_sheet)
        print(
            f"    {sheet_key}: {n_questions} question(s), {len(cols_in_sheet)} column(s)"
        )
    print(f"    Total: {total_questions} question(s), {len(all_qu_columns)} column(s)")

    # ── Missing fields in Q.U. rows ─────────────────────────────────────
    incomplete_rows: list[str] = []
    for sheet_key, df in question_sheets.items():
        sheet_name = QU_SHEET_SPECS[sheet_key][0][0]
        expected_fields = QU_SHEET_SPECS[sheet_key][2]
        for idx, row in df.iterrows():
            missing = [
                f
                for f in expected_fields
                if pd.isna(row.get(f)) or str(row.get(f)).strip() in ("", "nan")
            ]
            if missing:
                q_text = str(row.get("question_text", "")).strip()
                label = q_text[:50] + "..." if len(q_text) > 50 else q_text
                incomplete_rows.append(
                    f'      "{sheet_name}" row {idx + 1}: missing {", ".join(missing)}'
                    f"  ({label!r})"
                    if label
                    else ""
                )
    if incomplete_rows:
        print("\n  ⚠ Q.U. rows with missing fields:")
        for line in incomplete_rows:
            print(line)
        issues.append(f"Incomplete Q.U. rows: {len(incomplete_rows)}")

    # ── Column ID format check ────────────────────────────────────────
    bad_col_ids: list[str] = []
    for sheet_key, df in question_sheets.items():
        for col_field in COL_ID_FIELDS[sheet_key]:
            for _, row in df.iterrows():
                val = str(row[col_field]).strip()
                if not _EXCEL_COL_RE.match(val):
                    bad_col_ids.append(f"      {sheet_key}.{col_field} = {val!r}")
    if bad_col_ids:
        print(
            "\n  ⚠ Column IDs that don't look like Excel columns (expected 'A', 'B', 'AA', ...):"
        )
        for line in bad_col_ids:
            print(line)
        issues.append("Non-Excel column IDs found in Q.U. sheets")

    # ── Duplicate column reference check ─────────────────────────────────
    col_refs: list[tuple[str, str, int]] = []  # (col_id, sheet_key, q_num)
    for sheet_key, df in question_sheets.items():
        for _, row in df.iterrows():
            q_num = row["question_number"]
            for col_field in COL_ID_FIELDS[sheet_key]:
                col_refs.append((str(row[col_field]).strip(), sheet_key, q_num))
    seen: dict[str, list[tuple[str, int]]] = {}
    for col_id, sheet_key, q_num in col_refs:
        seen.setdefault(col_id, []).append((sheet_key, q_num))
    dupes = {col_id: refs for col_id, refs in seen.items() if len(refs) > 1}
    if dupes:
        print("\n  ⚠ Columns referenced more than once across Q.U. sheets:")
        for col_id, refs in sorted(
            dupes.items(), key=lambda x: excel_column_to_number(x[0].strip())
        ):
            ref_strs = [f"Q{q_num} ({sheet_key})" for sheet_key, q_num in refs]
            print(f"      Column {col_id}: {', '.join(ref_strs)}")
        issues.append(
            f"Duplicate column references: {', '.join(sorted(dupes, key=lambda x: excel_column_to_number(x.strip())))}"
        )

    # ── Column existence check ────────────────────────────────────────
    if len(all_qu_columns) > resp_col_count:
        msg = f"Q.U. references {len(all_qu_columns)} columns but response data only has {resp_col_count}"
        print(f"\n  ⚠ {msg}")
        issues.append(msg)

    max_resp_col = (
        max(original_headers, key=lambda x: excel_column_to_number(x.strip())) if original_headers else "?"
    )
    missing_cols = sorted(
        [c for c in all_qu_columns if c not in original_headers],
        key=lambda x: excel_column_to_number(x.strip()),
    )
    if missing_cols:
        print(
            f"\n  ⚠ Q.U. references columns not in response data (max is {max_resp_col}):"
        )
        for col_id in missing_cols:
            print(f"      {col_id}")
        issues.append(f"Q.U. references missing columns: {', '.join(missing_cols)}")

    # ── Column data type checks ─────────────────────────────────────────
    # Open vs closed is decided purely by uniqueness ratio (n_unique /
    # n_responses). Empirically (see analyse_open_closed_detector.py) a
    # threshold of 0.2 separates the two classes well: closed columns sit
    # well below it and free-text columns well above.
    UNIQUENESS_RATIO_THRESHOLD = 0.2

    def _uniqueness_ratio(col_id: str) -> tuple[int, int, float] | None:
        """Return (n_unique, n_responses, ratio) for a column, or None if empty."""
        if col_id not in responses_df.columns:
            return None
        series = responses_df[col_id].dropna().astype(str)
        n_responses = len(series)
        if n_responses == 0:
            return None
        n_unique = int(series.nunique())
        return n_unique, n_responses, n_unique / n_responses

    def _check_looks_like_multichoice(
        col_id: str,
        q_num: int,
        sheet_key: str,
        col_role: str,
    ) -> None:
        """Warn if a closed column has a uniqueness ratio above the threshold."""
        stats = _uniqueness_ratio(col_id)
        if stats is None:
            return
        n_unique, n_responses, ratio = stats
        if ratio <= UNIQUENESS_RATIO_THRESHOLD:
            return
        sheet_name = QU_SHEET_SPECS[sheet_key][0][0]
        msg = (
            f'Column {col_id} (Q{q_num}, {col_role}) — on Q.U. sheet "{sheet_name}" — '
            f"looks like free text, not multichoice: "
            f"{n_unique}/{n_responses} responses are unique "
            f"({ratio:.0%}, expected ≤{UNIQUENESS_RATIO_THRESHOLD:.0%})"
        )
        print(f"\n  ⚠ {msg}")
        issues.append(msg)

    def _check_looks_like_free_text(
        col_id: str,
        q_num: int,
        sheet_key: str,
        col_role: str,
    ) -> None:
        """Warn if an open column has a uniqueness ratio below the threshold."""
        stats = _uniqueness_ratio(col_id)
        if stats is None:
            return
        n_unique, n_responses, ratio = stats
        if ratio >= UNIQUENESS_RATIO_THRESHOLD:
            return
        sheet_name = QU_SHEET_SPECS[sheet_key][0][0]
        msg = (
            f'Column {col_id} (Q{q_num}, {col_role}) — on Q.U. sheet "{sheet_name}" — '
            f"only {n_unique}/{n_responses} responses are unique ({ratio:.0%}) — "
            f"expected >{UNIQUENESS_RATIO_THRESHOLD:.0%} for free text. "
            f'Should this be on the "Multiple Choice" sheet instead?'
        )
        print(f"\n  ⚠ {msg}")
        issues.append(msg)

    for sheet_key in ("closed", "hybrid", "open"):
        df = question_sheets.get(sheet_key)
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            q_num = row["question_number"]
            if sheet_key == "closed":
                _check_looks_like_multichoice(
                    str(row["column_name"]).strip(),
                    q_num,
                    sheet_key,
                    "closed column",
                )
            elif sheet_key == "hybrid":
                _check_looks_like_multichoice(
                    str(row["closed_column"]).strip(),
                    q_num,
                    sheet_key,
                    "closed part",
                )
                _check_looks_like_free_text(
                    str(row["open_column"]).strip(),
                    q_num,
                    sheet_key,
                    "open part",
                )
            elif sheet_key == "open":
                _check_looks_like_free_text(
                    str(row["column_name"]).strip(),
                    q_num,
                    sheet_key,
                    "open column",
                )

    # ── Label matching ────────────────────────────────────────────────
    label_issues: list[tuple[str, list[str], str, str]] = []
    for sheet_key, df in question_sheets.items():
        for _, row in df.iterrows():
            for col_field in COL_ID_FIELDS[sheet_key]:
                col_id = str(row[col_field]).strip()
                qu_label = str(row.get("question_text", "")).strip()
                resp_header = original_headers.get(col_id)

                if resp_header is None:
                    continue  # already reported above

                ratio = SequenceMatcher(
                    None, qu_label.lower(), resp_header.lower(), autojunk=False
                ).ratio()
                qu_nums = set(_extract_numbers(qu_label))
                resp_nums = set(_extract_numbers(resp_header))

                problems: list[str] = []
                if ratio < 0.4:
                    problems.append(f"low similarity ({ratio:.0%})")
                if qu_nums and resp_nums and qu_nums != resp_nums:
                    problems.append(
                        f"number mismatch (Q.U.:{sorted(qu_nums)} vs resp:{sorted(resp_nums)})"
                    )

                if problems:
                    label_issues.append((col_id, problems, qu_label, resp_header))

    if label_issues:
        print(f"\n  ⚠ Label mismatches ({len(label_issues)}):")
        for col_id, problems, qu_label, resp_header in label_issues:
            print(f"\n      col {col_id}: {', '.join(problems)}")
            print(f"      ┌ Q.U.:   {qu_label}")
            print(f"      └ Resp: {resp_header}")
        issues.extend(["Label mismatch"] * len(label_issues))

    # ── Unreferenced columns check ──────────────────────────────────────
    # Flag response columns not referenced by any question or demographic.
    demographic_set = set(demographic_columns) if demographic_columns else set()
    all_resp_cols = set(responses_df.columns) - {"themefinder_id"}
    referenced_cols = all_qu_columns | demographic_set
    unreferenced = [
        col
        for col in sorted(all_resp_cols - referenced_cols, key= lambda x: excel_column_to_number(x.strip()))
        if "response id" not in str(original_headers.get(col, "")).lower()
    ]
    if unreferenced:
        print(
            f"\n  ⚠ {len(unreferenced)} response column(s) not referenced by any question or demographic:"
        )
        for col_id in unreferenced:
            series = responses_df[col_id].dropna().astype(str)
            n_responses = len(series)
            n_unique = series.nunique()
            header = original_headers.get(col_id, "?")
            if len(header) > 60:
                header = header[:57] + "..."
            print(
                f'      {col_id}: "{header}" — {n_responses} non-null, {n_unique} unique'
            )
        print("      Should any of these be included as demographics?")
        issues.append(f"Unreferenced columns: {', '.join(unreferenced)}")

    # ── Result ────────────────────────────────────────────────────────
    if issues:
        print(f"\n  Found {len(issues)} issue(s).")
        if interactive:
            answer = input("  Continue anyway? (y/n): ").strip().lower()
            if answer != "y":
                print("Aborting.")
                sys.exit(1)
    else:
        print("\n  ✓ Validation passed.")


def load_and_number_question_sheets(
    question_understanding_path: Path,
) -> dict[str, pd.DataFrame]:
    """Load all question sheets, truncate to useful columns, and assign question numbers.

    If any question_number value across any sheet cannot be parsed as an integer,
    falls back to numbering all questions sequentially by sorting their Excel column
    IDs across all sheets.

    Raises:
        ValueError: if question numbers are not globally unique across all sheets
                    after numbering (numbers are used as output directory names).
    """
    sheets: dict[str, pd.DataFrame] = {}

    for sheet_key, (sheet_aliases, ncols, col_names) in QU_SHEET_SPECS.items():
        df = _load_qu_sheet(question_understanding_path, sheet_aliases, ncols, col_names)
        if df is not None:
            sheets[sheet_key] = df

    if not sheets:
        return sheets

    # Check whether all question_number values can be parsed as integers
    needs_fallback = False
    for df in sheets.values():
        if _parse_question_numbers(df["question_number"]) is None:
            needs_fallback = True
            break

    if needs_fallback:
        # Report which values are non-numeric
        print(
            "\n  ⚠ Non-numeric question numbers found in Q.U. sheets"
            " — a column ID-based fallback will be applied:"
        )
        for key, df in sheets.items():
            sheet_name = QU_SHEET_SPECS[key][0][0]
            for idx, val in enumerate(df["question_number"].astype(str)):
                try:
                    int(val.strip())
                except ValueError:
                    print(
                        f'      "{sheet_name}" row {idx + 1}: '
                        f"question_number = {val!r} (not a valid integer)"
                    )

        # Collect (excel_col_id, sheet_key, df_index) from every row across all sheets
        all_entries: list[tuple[str, str, int]] = []
        for key, df in sheets.items():
            for idx in df.index:
                all_entries.append(
                    (str(df.at[idx, PRIMARY_COL_ID_FIELD[key]]).strip(), key, idx)
                )

        # Sort by Excel column order and assign sequential numbers
        all_entries.sort(key=lambda x: excel_column_to_number(x[0].strip()))
        number_map: dict[tuple[str, int], int] = {}
        for i, (_, key, idx) in enumerate(all_entries, 1):
            number_map[(key, idx)] = i

        for key, df in sheets.items():
            df["question_number"] = [number_map[(key, idx)] for idx in df.index]
    else:
        for key, df in sheets.items():
            df["question_number"] = _parse_question_numbers(df["question_number"])

    # Show final numbering, sorted by question number
    all_rows: list[tuple[int, str, str, str]] = []
    for key, df in sheets.items():
        for _, row in df.iterrows():
            col = str(row.get(PRIMARY_COL_ID_FIELD[key], "?")).strip()
            label = str(row.get("question_text", ""))
            if len(label) > 120:
                label = label[:117] + "..."
            all_rows.append((row["question_number"], col, key, label))
    all_rows.sort()
    print("\n  Question numbering:")
    for q_num, col, key, label in all_rows:
        print(f"    Q{q_num:>3}  col {col:<4}  [{key}]  {label}")

    # Validate global uniqueness (numbers are used as directory names)
    all_numbers: list[tuple[str, int]] = []
    for key, df in sheets.items():
        for num in df["question_number"].tolist():
            all_numbers.append((key, num))
    seen: dict[int, list[str]] = {}
    for key, num in all_numbers:
        seen.setdefault(num, []).append(key)
    duplicates = {num: keys for num, keys in seen.items() if len(keys) > 1}
    if duplicates:
        detail = ", ".join(
            f"question_number={num} appears in [{', '.join(keys)}]"
            for num, keys in sorted(duplicates.items())
        )
        raise ValueError(f"Non-unique question numbers found across sheets: {detail}")

    return sheets


def create_respondents_jsonl(
    df: pd.DataFrame,
    demographic_columns: list[str],
    demographic_labels: list[str],
    output_dir: Path,
) -> None:
    # Work on a copy — callers don't expect their dataframe to be rewritten
    # (rename, derived `demographic_data` column).
    df = df.copy()
    for c in demographic_columns:
        df[c] = (
            df[c]
            .astype(str)
            .str.replace("_x000D_", "", regex=False)
            .apply(_strip_control_chars)
        )
        df[c] = df[c].apply(
            lambda x: list(dict.fromkeys(x.rstrip(",").split(",")))
        )
    df.rename(columns=dict(zip(demographic_columns, demographic_labels)), inplace=True)
    df["demographic_data"] = df[demographic_labels].to_dict(orient="records")
    df[["themefinder_id", "demographic_data"]].to_json(
        output_dir / "respondents.jsonl", orient="records", lines=True
    )


def _collapse_other_specify(value: object) -> object:
    """Collapse "Other (please specify): ..." style answers down to "Other".

    Operates per comma-separated token so multi-select cells are handled
    correctly. A token is collapsed only when it equals "Other" or starts
    with "Other (" — substring matches like "Other religion" or "Mother"
    are left untouched (the previous behavior of `"Other" in x` lost real
    answers).
    """
    if not isinstance(value, str):
        return value
    parts = []
    for tok in value.split(","):
        stripped = tok.strip()
        if stripped == "Other" or stripped.startswith("Other ("):
            parts.append("Other")
        else:
            parts.append(stripped)
    return ",".join(parts)


def _strip_control_chars(text: str) -> str:
    """Remove unicode control characters (category 'C*') while preserving
    printable unicode such as accents, smart quotes, and non-breaking hyphens."""
    return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")


def _clean_text_column(series: pd.Series) -> pd.Series:
    """Strip control characters and known noise strings from a text column.

    Preserves printable unicode (e.g. 'Community‑based' with U+2011) so legitimate
    option names and free-text aren't mangled.
    """
    series = series.astype(str).apply(_strip_control_chars)
    for bad_string in CHARACTERS_TO_REMOVE:
        series = series.apply(lambda x, bs=bad_string: x.replace(bs, " "))
    return series.str.strip()


def create_question_inputs(
    df: pd.DataFrame,
    questions: list[dict],
    question_type: str,
    output_dir: Path,
    sample_size: int | None = None,
) -> None:
    """Write responses.jsonl, multi_choice.jsonl, and question.json for each question."""
    has_free_text = question_type in ("open", "hybrid")
    has_options = question_type in ("closed", "hybrid")

    for question in questions:
        q_num = question["question_number"]

        # Select relevant columns and drop empty rows
        if question_type == "hybrid":
            open_col = question["open_column"]
            closed_col = question["closed_column"]
            data_cols = [closed_col, open_col]
            answers = df[["themefinder_id"] + data_cols].dropna(
                subset=data_cols, how="all"
            )
            answers[closed_col] = answers[closed_col].fillna("Not Provided")
            answers[open_col] = answers[open_col].fillna("Not Provided")
        else:
            col = question["column_name"]
            data_cols = [col]
            answers = df[["themefinder_id"] + data_cols].dropna()

        # Skip questions with no responses — the loader discovers questions by
        # folder existence, so omitting the folder drops the question cleanly
        # from the consultation. Writing an empty .jsonl file would produce a
        # blank-line file that breaks the import step.
        if answers.empty:
            print(
                f"  ⚠ Q{q_num} ({question_type}): no responses after dropping nulls"
                f" — skipping question_part_{q_num}"
            )
            continue

        q_dir = output_dir / f"question_part_{q_num}"
        q_dir.mkdir(parents=True, exist_ok=True)

        if sample_size is not None and sample_size < len(answers):
            answers = answers.sample(sample_size)

        # Clean text columns
        for c in data_cols:
            answers[c] = _clean_text_column(answers[c])

        # Write multi_choice.jsonl
        if has_options:
            options_col = (
                question["closed_column"]
                if question_type == "hybrid"
                else question["column_name"]
            )
            answers[options_col] = answers[options_col].apply(
                lambda x: list(dict.fromkeys(x.rstrip(",").split(",")))
            )
            answers.rename(columns={options_col: "options"}, inplace=True)
            answers[["themefinder_id", "options"]].to_json(
                q_dir / "multi_choice.jsonl", orient="records", lines=True
            )

        # Write responses.jsonl
        if has_free_text:
            text_col = (
                question["open_column"]
                if question_type == "hybrid"
                else question["column_name"]
            )
            # For hybrid, text_col is already the original name (not renamed)
            answers.rename(columns={text_col: "text"}, inplace=True)
            answers[["themefinder_id", "text"]].to_json(
                q_dir / "responses.jsonl", orient="records", lines=True
            )

        # Write question.json
        question_data: dict = {
            "question_number": q_num,
            "question_text": question["question_text"],
            "has_free_text": has_free_text,
        }
        if has_options:
            # "Not Provided" is a sentinel we fill in for missing hybrid
            # cells — it's not a real option and must not leak into the
            # canonical option list on question.json.
            question_data["multi_choice_options"] = sorted(
                {item for sublist in answers["options"] for item in sublist}
                - {"Not Provided"}
            )
        with open(q_dir / "question.json", "w") as f:
            json.dump(question_data, f, indent=4)


# --- CLI logic ---


def find_data_files(consultation_dir: Path) -> list[Path]:
    """Find CSV and Excel files in the consultation directory, ignoring temp files."""
    files = []
    for f in consultation_dir.iterdir():
        if f.name.startswith("~$"):
            continue
        if f.suffix.lower() in VALID_EXTENSIONS:
            files.append(f)
    return sorted(files)


def _is_subheader_row(row: pd.Series) -> bool:
    """Detect whether a row is a descriptive sub-header rather than data.

    Two-tier header files have short IDs on row 0 and long question text on
    row 1.  Data rows have shorter, more varied values with more NaN cells.
    """
    non_null_1 = row.dropna()
    if len(non_null_1) == 0:
        return False

    # Sub-header rows are nearly fully populated (>90% non-null)
    fill_ratio = len(non_null_1) / len(row)
    if fill_ratio < 0.9:
        return False

    # Sub-header rows have long descriptive text (median length > 25 chars)
    median_len = non_null_1.astype(str).str.len().median()
    return median_len > 25


def load_responses(
    path: Path, sheet_name: str | None = None
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load responses from CSV or Excel file.

    Returns the DataFrame (with columns renamed to Excel letters) and a
    dict mapping Excel column letter -> original column header string.

    When `sheet_name` is given (new single-workbook format), responses are
    read from that sheet. Otherwise the whole file is treated as the response
    grid (legacy two-file format).

    Handles three layout patterns automatically:
      - Single header row, then data  (LGR files)
      - Header row, blank row, then data  (SCR files)
      - Two header rows (short IDs + full question text), then data  (Biomass)
    """
    ext = path.suffix.lower()
    if ext == ".csv":
        read_fn = pd.read_csv
        read_kwargs: dict = {}
    else:
        read_fn = pd.read_excel
        read_kwargs = {"sheet_name": sheet_name} if sheet_name else {}

    # Read first 3 rows raw to detect layout
    raw = read_fn(path, header=None, nrows=3, **read_kwargs)

    header_row = 0

    if len(raw) > 1 and _is_subheader_row(raw.iloc[1]):
        # Two-tier header — use row 1 (full question text) as the header
        logger.info("Detected two-tier header in %s, using row 2 as header", path.name)
        header_row = 1

    # Full read with detected layout
    df = read_fn(path, header=header_row, **read_kwargs)

    # Drop all-NaN rows (handles blank separator rows and trailing empties)
    df = df.dropna(how="all").reset_index(drop=True)

    # Replace null-type signifiers ("-", "N/A", "none", ...) with NaN so the
    # rest of the pipeline treats them as missing rather than as text answers.
    df = _normalise_null_like(df)

    # Re-drop fully-empty rows in case normalisation emptied any.
    df = df.dropna(how="all").reset_index(drop=True)

    original_headers = {
        get_excel_column_name(i): str(col) for i, col in enumerate(df.columns)
    }
    df.columns = [get_excel_column_name(i) for i in range(len(df.columns))]
    df["themefinder_id"] = range(1, len(df) + 1)
    return df, original_headers


def _prompt_format() -> str:
    """Ask the user whether they have a single-workbook (new) or two-file (old) input."""
    print("\nWhich input format are you using?")
    print("  [1] new — single workbook with a 'Responses' sheet plus Q.U. sheets")
    print("  [2] old — two separate files: a responses file + a Q.U. workbook")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return "new"
        if choice == "2":
            return "old"
        print("Invalid choice, try again.")


def prompt_file_selection(files: list[Path], role: str) -> Path:
    """Ask the user to select which file serves a given role."""
    print(f"\nWhich file is the {role}?")
    for i, f in enumerate(files, 1):
        print(f"  [{i}] {f.name}")
    while True:
        choice = input(f"Enter number (1-{len(files)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice) - 1]
        print("Invalid choice, try again.")


PIPELINE_STAGES = ("validate", "build", "upload")
FORMATS = ("old", "new")
RESPONSES_SHEET_NAME = "Responses"

# Roots under which `_safe_replace_output_dir` will agree to move an existing
# directory out of the way. Anything outside these is refused — protects users
# who point `--dir` at an unrelated path.
_SAFE_OUTPUT_ROOTS: tuple[Path, ...] = (
    (Path(__file__).resolve().parent / "consultations").resolve(),
    (Path.cwd() / "consultations").resolve(),
)


def _safe_replace_output_dir(output_dir: Path) -> None:
    """Move an existing `output_dir` aside (timestamped backup) rather than rmtree it.

    Refuses to touch paths that aren't under one of the project's
    consultations roots, so a stray `--dir /some/unrelated/path` can't
    nuke real data. If the dir doesn't exist, this is a no-op.
    """
    if not output_dir.exists():
        return
    resolved = output_dir.resolve()
    if not any(resolved.is_relative_to(root) for root in _SAFE_OUTPUT_ROOTS):
        raise SystemExit(
            f"Refusing to replace {resolved}: not under any of "
            f"{[str(r) for r in _SAFE_OUTPUT_ROOTS]}. "
            "Move or delete the directory manually if you want to overwrite it."
        )
    backup = output_dir.with_name(f"{output_dir.name}.bak.{int(time.time())}")
    output_dir.rename(backup)
    print(f"  Moved existing {output_dir.name}/ -> {backup.name}/")


def run_pipeline(
    responses_path: Path,
    question_understanding_path: Path,
    output_dir: Path,
    until: str = "upload",
    fmt: str = "old",
) -> None:
    """Run the setup pipeline: load → validate → build → upload.

    `fmt` is "old" (two separate files: responses + Q.U. workbook) or
    "new" (single workbook with a "Responses" sheet plus Q.U. sheets — in
    which case `responses_path` and `question_understanding_path` point at
    the same file).
    """

    responses_sheet = RESPONSES_SHEET_NAME if fmt == "new" else None

    # ── Load ──────────────────────────────────────────────────────────
    print(f"\nLoading responses from: {responses_path.name}")
    responses_df, original_headers = load_responses(
        responses_path, sheet_name=responses_sheet
    )
    # The pipeline mutates `responses_df` (fillna, Other-collapse, demographic
    # rename via create_respondents_jsonl). Defensive copy keeps callers' df
    # intact in case they're reusing it.
    responses_df = responses_df.copy()
    print(f"  Loaded {len(responses_df)} responses")

    question_sheets = load_and_number_question_sheets(question_understanding_path)

    demographic_columns: list[str] | None = None
    demographic_labels: list[str] | None = None
    demographic_info = _load_qu_sheet(
        question_understanding_path,
        DEMOGRAPHIC_SHEET_ALIASES,
        2,
        ["column_id", "label"],
    )
    if demographic_info is not None:
        demographic_columns = demographic_info["column_id"].tolist()
        demographic_labels = [
            label.replace("/", "-") for label in demographic_info["label"].tolist()
        ]

    # ── Validate ──────────────────────────────────────────────────────
    validate_data(
        question_sheets,
        original_headers,
        responses_df,
        demographic_columns,
        demographic_labels,
        interactive=until != "validate",
    )

    if until == "validate":
        return

    # ── Build ─────────────────────────────────────────────────────────
    _safe_replace_output_dir(output_dir)
    output_dir.mkdir(parents=True)

    # Demographics
    if demographic_columns and demographic_labels:
        print("Writing demographics...")
        for c in demographic_columns:
            responses_df[c] = responses_df[c].fillna("Not Provided")
            responses_df[c] = responses_df[c].apply(_collapse_other_specify)
        create_respondents_jsonl(
            responses_df, demographic_columns, demographic_labels, output_dir
        )
    else:
        print("  No demographic data found, skipping.")

    # Questions
    for qtype in ("open", "hybrid", "closed"):
        q_df = question_sheets.get(qtype)
        if q_df is None or q_df.empty:
            print(f"  No {qtype} questions found, skipping.")
            continue
        # Skip open questions where the response column is entirely NaN
        if qtype == "open":
            all_nan = responses_df[q_df["column_name"].tolist()].isna().all()
            q_df = q_df[~q_df["column_name"].isin(all_nan[all_nan].index)]
        print(f"Writing {qtype} questions...")
        create_question_inputs(
            responses_df, q_df.to_dict(orient="records"), qtype, output_dir
        )

    print(f"\nAll input files written to: {output_dir}")


DEFAULT_S3_BUCKET = "i-dot-ai-prod-consult-data"


def upload_inputs_to_s3(local_dir: Path, bucket: str, s3_prefix: str) -> None:
    """Upload all files in local_dir to s3://bucket/s3_prefix, preserving directory structure.

    Checks for existing objects at the S3 prefix before uploading. If any exist,
    warns and requires confirmation. Always prompts before uploading.
    """
    files = [f for f in local_dir.rglob("*") if f.is_file()]
    if not files:
        print(f"No files found in {local_dir} to upload.")
        return

    s3 = boto3.client("s3")

    # Check for existing data at this S3 prefix
    print(f"\nChecking for existing data at s3://{bucket}/{s3_prefix} ...")
    existing = s3.list_objects_v2(Bucket=bucket, Prefix=s3_prefix, MaxKeys=10)
    existing_keys = [obj["Key"] for obj in existing.get("Contents", [])]
    if existing_keys:
        print(f"  Found {len(existing_keys)} existing object(s) at this prefix:")
        for key in existing_keys:
            print(f"    {key}")
        if existing.get("IsTruncated"):
            print("    ... (more objects not shown)")
        logger.warning(
            "Uploading will overwrite existing data at s3://%s/%s",
            bucket,
            s3_prefix,
        )

    print(f"\nReady to upload {len(files)} file(s) to s3://{bucket}/{s3_prefix}")
    for file_path in files:
        relative = file_path.relative_to(local_dir).as_posix()
        print(f"  {relative}")
    answer = input("Proceed with upload? (y/n): ").strip().lower()
    if answer != "y":
        print("Upload skipped.")
        return

    for file_path in files:
        relative = file_path.relative_to(local_dir).as_posix()
        s3_key = s3_prefix + relative
        print(f"  Uploading {relative} -> s3://{bucket}/{s3_key}")
        s3.upload_file(str(file_path), bucket, s3_key)
    print("Upload complete.")


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Set up a new consultation for ThemeFinder."
    )
    parser.add_argument(
        "name", nargs="?", help="Consultation name (used as folder name)"
    )
    parser.add_argument(
        "--dir",
        type=Path,
        help="Path to consultation directory (skip interactive prompt)",
    )
    parser.add_argument(
        "--responses",
        type=Path,
        help="Path to response data file (skip file selection)",
    )
    parser.add_argument(
        "--qu",
        type=Path,
        help="Path to question understanding file (skip file selection)",
    )
    parser.add_argument(
        "--until",
        choices=PIPELINE_STAGES,
        default="upload",
        help="How far to run the pipeline: validate, build, or upload (default: upload)",
    )
    parser.add_argument(
        "--format",
        choices=FORMATS,
        dest="fmt",
        help=(
            "Input format: 'old' (two files: responses + Q.U. workbook) or "
            "'new' (single workbook with a 'Responses' sheet plus Q.U. sheets). "
            "Prompted if omitted."
        ),
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_S3_BUCKET,
        help=f"S3 bucket to upload to (default: {DEFAULT_S3_BUCKET})",
    )
    args = parser.parse_args()

    fmt = args.fmt or _prompt_format()

    name = args.name
    if not name and args.dir:
        # Derive name from directory
        name = args.dir.resolve().name
    if not name:
        name = input("Enter consultation name: ").strip()
        if not name:
            print("Error: consultation name cannot be empty.")
            sys.exit(1)

    original_name = name
    name = to_snake_case(name)
    if name != original_name:
        print(f"Using consultation name: {name} (rewrote from {original_name!r})")
    else:
        print(f"Using consultation name: {name}")

    base_dir = Path(__file__).resolve().parent / "consultations"

    # Step 1: Resolve consultation directory
    if args.dir:
        consultation_dir = args.dir.resolve()
    else:
        consultation_dir = base_dir / name
    consultation_dir.mkdir(parents=True, exist_ok=True)
    print(f"Consultation directory: {consultation_dir}")

    # Step 2: Resolve file paths
    if fmt == "new":
        # Single workbook contains both responses and Q.U. sheets.
        if args.responses:
            responses_path = args.responses.resolve()
            if not responses_path.exists():
                print(f"Error: file not found: {responses_path}")
                sys.exit(1)
        else:
            print(
                "\nPlease copy the consultation data workbook (single .xlsx with"
                " a 'Responses' sheet plus Q.U. sheets) into:"
            )
            print(f"  {consultation_dir}")
            input("\nPress Enter when the file is in place...")
            files = find_data_files(consultation_dir)
            if not files:
                print(
                    f"\nError: Expected an .xlsx data file but found none in"
                    f" {consultation_dir}."
                )
                sys.exit(1)
            if len(files) == 1:
                responses_path = files[0]
                print(f"\nUsing '{responses_path.name}' as the consultation workbook.")
            else:
                responses_path = prompt_file_selection(files, "consultation workbook")
        qu_path = responses_path
        print(f"Consultation workbook: {responses_path.name}")
    elif args.responses and args.qu:
        responses_path = args.responses.resolve()
        qu_path = args.qu.resolve()
        for label, path in [("Responses", responses_path), ("Q.U.", qu_path)]:
            if not path.exists():
                print(f"Error: {label} file not found: {path}")
                sys.exit(1)
        print(f"Responses file: {responses_path.name}")
        print(f"Q.U. file: {qu_path.name}")
    else:
        if not (args.responses or args.qu):
            print(
                "\nPlease copy the consultation response data and the template question"
                " understanding file into:"
            )
            print(f"  {consultation_dir}")
            input("\nPress Enter when the files are in place...")

        files = find_data_files(consultation_dir)
        if len(files) < 2:
            print(
                f"\nError: Expected at least 2 data files (.csv/.xlsx/.xls) but found"
                f" {len(files)}."
            )
            print("Please add the missing files and re-run the script.")
            sys.exit(1)

        if args.responses:
            responses_path = args.responses.resolve()
        else:
            responses_path = prompt_file_selection(files, "consultation response data")

        if args.qu:
            qu_path = args.qu.resolve()
        else:
            remaining = [f for f in files if f != responses_path]
            if len(remaining) == 1:
                qu_path = remaining[0]
                print(
                    f"\nUsing '{qu_path.name}' as the template question understanding file."
                )
            else:
                qu_path = prompt_file_selection(
                    remaining, "template question understanding data"
                )

    # Step 3: Run pipeline
    output_dir = consultation_dir / "inputs"
    run_pipeline(responses_path, qu_path, output_dir, until=args.until, fmt=fmt)

    if args.until == "validate":
        return

    # Step 4: Upload inputs to S3
    if args.until == "upload":
        s3_prefix = f"app_data/consultations/{name}/inputs/"
        try:
            upload_inputs_to_s3(output_dir, args.bucket, s3_prefix)
        except botocore.exceptions.NoCredentialsError as e:
            print(f"\nAWS error: {e}")
            print("\nTo fix, either:")
            print("1. Run: aws-vault exec first")
            print("2. Re-run with UNTIL=build to skip the upload step")
            sys.exit(1)

    # Step 5: Point to Confluence
    print("\n" + "=" * 60)
    print("Setup complete! For further instructions, see:")
    print(f"  {CONFLUENCE_URL}")
    print("=" * 60)


if __name__ == "__main__":
    main()
