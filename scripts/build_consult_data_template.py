"""Build consult_data_template.xlsx — an opinionated workbook skeleton.

Generates a single .xlsx file at the root of the repo with sheets:
Guide, Active issues, Responses, Demographics, Open Questions, Closed
questions, Hybrid Questions, plus a hidden Issues sheet that drives the
audit. The four metadata sheets (Demographics, Open, Closed, Hybrid)
together tell Consult how to interpret each column on Responses.

Per-sheet checks (cells go pink when the rule is broken AND the violation
is also listed on the Issues sheet with an explanation and fix):
- Required fields must be populated whenever the row contains any data.
- Column-ID cells must look like Excel column letters (1-3 uppercase A-Z).
- Question-number cells must be whole numbers >= 1 (also integer-formatted).

Cross-sheet checks (mirror the validations in setup_consultation.py):
- Column letters referenced by metadata rows must match a populated Responses
  column header.
- No duplicate column references across the Open / Closed / Hybrid sheets.
- question_number values must be globally unique across Open/Closed/Hybrid.
- Total referenced-column count must not exceed Responses column count - 1.
- Closed-side columns should have ≤20% unique values (else: looks like free text).
- Open-side columns should have >20% unique values (else: looks multichoice).
- Every Responses column should be referenced by one of Demographics /
  Open / Closed / Hybrid.
- Every Responses column with data must have a header in row 1.
- Metadata sheets are locked to their defined column count: Demographics A–B,
  Open/Closed A–C, Hybrid A–D. Off-limit columns reject input via data
  validation and pink-fill anything pasted in.

- question_text on Open/Closed/Hybrid should be similar to its Responses
  header. Implemented as character-4-gram Jaccard similarity. The
  intersection size is one SUMPRODUCT over MID(a, SEQUENCE(na), 4) —
  no LAMBDA / LET / REDUCE (this Excel build doesn't support them; see
  label_similarity_debugging.md). Inputs are truncated to LABEL_MAX_LEN
  chars to keep recompute fast. Approximation of setup_consultation.py's
  SequenceMatcher ratio — threshold tuned independently.

One check from setup_consultation.py is deliberately not implemented here:
integer extraction from question text. It needs regex which Excel lacks.

The Responses sheet is pre-populated with dummy data so the checks can be
exercised end-to-end by filling in the metadata sheets.

Excel-version compatibility constraint
--------------------------------------
The target deployment runs an Excel build that does NOT support the
name-binding family of modern functions. **Do not use** `LAMBDA`, `LET`,
`REDUCE`, `MAP`, `BYROW`, `MAKEARRAY`, `SCAN`, defined-name `LAMBDA`s,
or anything else that takes a callback. Cells using them open with a
repair dialog and the formulas get stripped on load — even when the
`_xlfn.` / `_xlpm.` prefixes and the `cm="1"` / `xl/metadata.xml`
dynamic-array metadata are emitted correctly. Confirmed empirically;
see `label_similarity_debugging.md` for the full evidence.

Functions that ARE safe to use here:
- All pre-2020 Excel functions.
- Four dynamic-array additions: `SEQUENCE`, `FILTER`, `UNIQUE`, `VSTACK`.
  When the cell actually SPILLS (i.e. the dynamic array is the formula's
  final output), write it with `worksheet.write_dynamic_array_formula`
  (not `write_formula`) so xlsxwriter emits the cm="1" array tag and the
  workbook's metadata part — otherwise Excel flags the file as malformed.
  When the dynamic-array result is collapsed to a scalar by an outer
  function — e.g. `ROWS(UNIQUE(...))`, `SUMPRODUCT(--ISNUMBER(SEARCH(MID(
  ...,SEQUENCE(n),k),...)))` — plain `write_formula` is fine; only the
  spilling case needs the array tag. (See `build_helpers_sheet`'s ratio
  formula and the inter-only branch of `build_label_similarity_helpers`
  for the two patterns used here.)

Default to scalar formulas. Reach for the four supported dynamic-array
functions only when there's no clean scalar alternative.

Run:
    uv run python build_consult_data_template.py
"""

import random
from pathlib import Path
from typing import NamedTuple

import xlsxwriter

from build_consult_data_dummy_content import (
    DUMMY_AGE_BANDS,
    DUMMY_AGREE,
    DUMMY_ORG_TYPES,
    DUMMY_REASONS,
    DUMMY_REGIONS,
    DUMMY_RECOMMEND,
    DUMMY_SUGGESTIONS,
    DUMMY_PRIORITY,
    DUMMY_HEADERS,
    DUMMY_EXPLANATIONS,
)

VERSION = "v005"
OUTPUT_PATH = (
    Path(__file__).resolve().parent / f"consult_data_template_{VERSION}.xlsx"
)

# --- Audit bounds -----------------------------------------------------------
# Four independent "how far do we look" axes. Each governs a different layer
# of the audit; bumping one doesn't imply bumping the others.
#
#   DATA_ROWS              — per-metadata-sheet:  # of rows pre-wired with
#                            per-cell data validation + conditional formats.
#                            Bounded purely by edit-time UX; cheap to inflate.
#   AUDIT_WINDOW           — per-metadata-sheet:  # of source rows the Issues
#                            sheet evaluates rules against. One Issues row
#                            per (sheet, source row, rule), so the audit grid
#                            grows linearly. Anything past this is silently
#                            unchecked — bump if real consultations exceed it.
#   QU_RANGE_LAST_ROW      — per-metadata-sheet:  upper bound on the ranges
#                            used by cross-sheet COUNTIF lookups (duplicate
#                            column / duplicate question_number checks).
#                            COUNTIF cost is linear in range size.
#   RESPONSE_DATA_LAST_ROW — Responses sheet:    upper bound on rows covered
#                            by uniqueness ratio, missing-header, and
#                            unreferenced-column checks. The uniqueness
#                            formula is O(n²) per populated column, so 8k
#                            keeps recompute snappy while staying well past
#                            the point where the unique-vs-free-text signal
#                            stabilises.
#   RESPONSE_LAST_LETTER   — Responses sheet:    last column the audit covers
#                            (A..ZZ → 702 columns). One header-empty and one
#                            unreferenced-column rule row is emitted per
#                            letter, so the audit grid widens linearly.
DATA_ROWS = 100000
AUDIT_WINDOW = 50
QU_RANGE_LAST_ROW = 1001
RESPONSE_DATA_LAST_ROW = 8000
RESPONSE_LAST_LETTER = "ZZ"

UNIQUENESS_THRESHOLD = 0.2  # mirrors setup_consultation.UNIQUENESS_RATIO_THRESHOLD

# --- Sheet names ------------------------------------------------------------
# Single source of truth — sheet renames are one-line.
SHEET_GUIDE = "Guide"
SHEET_ACTIVE = "Active issues"
SHEET_RESPONSES = "Responses"
SHEET_DEMOGRAPHICS = "Demographics"
SHEET_OPEN = "Open Questions"
SHEET_CLOSED = "Multiple Choice Questions"
SHEET_HYBRID = "Hybrid Questions"
SHEET_ISSUES = "Issues"
HELPER_SHEET = "_helpers"  # hidden; users shouldn't see or edit it

# --- Hidden helper sheet layout --------------------------------------------
# Per-Responses-column uniqueness ratio + count live on their own sheet so
# users can't accidentally overwrite them. Per-row uniqueness checks become
# O(1) INDEX lookups instead of O(n²) volatile recomputes.
#
# Row constants below are Excel 1-indexed (matching how they appear in
# formulas). xlsxwriter calls subtract 1 at the write site.
HELPER_RATIO_ROW = 1  # Excel row 1: ratio of unique non-empty values per column
HELPER_COUNT_ROW = 2  # Excel row 2: count of non-empty values per column

# Label-similarity helper layout: one BLOCK per (metadata sheet, letter-field),
# each block is LABEL_SIM_FIELDS columns wide so every intermediate step
# lives in its own cell (debuggable by inspection).
#
# Per-row layout within a block:
#   L      | column letter from the metadata sheet
#   H      | Responses header at that column
#   a      | LOWER(TRIM(LEFT(Q,LABEL_MAX_LEN))) of the metadata-sheet question_text
#   b      | LOWER(TRIM(LEFT(H,LABEL_MAX_LEN))) of the Responses header
#   na     | LEN(a) - 3   (number of 4-grams in a)
#   nb     | LEN(b) - 3   (number of 4-grams in b)
#   inter  | size of 4-gram intersection (computed inline)
#   sim    | Jaccard similarity = inter / (na + nb - inter), or "" if degenerate
#
# Blocks are laid out left-to-right starting at column A of the helper sheet.
# Cap inputs at 200 chars before computing 4-grams.
LABEL_MAX_LEN = 200
LABEL_SIMILARITY_THRESHOLD = 0.33
HELPER_SIM_START_ROW = 5  # Excel row where per-row data begins (row 4 holds headers)
LABEL_SIM_FIELDS = ["L", "H", "a", "b", "na", "nb", "inter", "sim"]
LABEL_SIM_BLOCK_WIDTH = len(LABEL_SIM_FIELDS)
LABEL_SIM_BLOCKS = [
    (SHEET_OPEN, "A"),
    (SHEET_CLOSED, "A"),
    (SHEET_HYBRID, "A"),
    (SHEET_HYBRID, "D"),
]


def _idx_to_letter(idx: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA, ..."""
    s = ""
    n = idx
    while True:
        n, rem = divmod(n, 26)
        s = chr(ord("A") + rem) + s
        if n == 0:
            return s
        n -= 1


def _letter_to_idx(letter: str) -> int:
    """A -> 0, Z -> 25, AA -> 26, ..."""
    n = 0
    for ch in letter:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


# A..ZZ — the column range the audit covers on the Responses sheet.
RESPONSE_LETTERS = [_idx_to_letter(i) for i in range(_letter_to_idx(RESPONSE_LAST_LETTER) + 1)]


def _sim_block_col(sheet: str, letter_field: str, field: str) -> str:
    """Excel column letter (e.g. 'C', 'AA') for a field within the block for (sheet, letter_field)."""
    block_idx = LABEL_SIM_BLOCKS.index((sheet, letter_field))
    field_idx = LABEL_SIM_FIELDS.index(field)
    return _idx_to_letter(block_idx * LABEL_SIM_BLOCK_WIDTH + field_idx)


ISSUE_BG = "#FCE4D6"  # warning amber
ERROR_BG = "#F4B6B6"  # error red
HEADER_BG = "#D9E1F2"

SEVERITY_TO_CHECK = "To check"  # heuristic flag — may be a real problem, may be fine
# Severity per rule kind. Keys are vkinds (used by per-metadata-row rules and
# their VIOLATION_FNS entries), plus workbook-level rule kinds whose names
# don't map to a violation function but share the same severity vocabulary.
SEVERITY_BY_VKIND = {
    "required": "Error",
    "column_id": "Error",
    "integer": "Error",
    "missing_response": "Error",
    "duplicate_column": SEVERITY_TO_CHECK,
    "duplicate_qnum": "Error",
    "closed_uniqueness": SEVERITY_TO_CHECK,
    "open_uniqueness": SEVERITY_TO_CHECK,
    "label_similarity": SEVERITY_TO_CHECK,
    # Workbook-level rules (no entry in VIOLATION_FNS — emitted directly).
    "workbook_count": "Error",
    "missing_header": "Error",
    "unreferenced": SEVERITY_TO_CHECK,
}


def make_formats(wb) -> dict:
    return {
        "header": wb.add_format({"bold": True, "bg_color": HEADER_BG}),
        "title": wb.add_format({"bold": True, "font_size": 14}),
        "bold_right": wb.add_format({"bold": True, "align": "right"}),
        "count": wb.add_format({"bold": True, "font_size": 14}),
        "italic_wrap": wb.add_format(
            {"italic": True, "text_wrap": True, "valign": "top"}
        ),
        "italic": wb.add_format({"italic": True}),
        "issue_fill": wb.add_format({"bg_color": ISSUE_BG}),
        "error_fill": wb.add_format({"bg_color": ERROR_BG}),
        "error_count": wb.add_format(
            {"bold": True, "font_size": 14, "font_color": "#C00000"}
        ),
        "warning_count": wb.add_format(
            {"bold": True, "font_size": 14, "font_color": "#B25E00"}
        ),
        "integer": wb.add_format({"num_format": "0"}),
        "wrap": wb.add_format({"text_wrap": True, "valign": "top"}),
    }


def write_headers(ws, headers: list[str], widths: list[int], header_fmt) -> None:
    for i, (h, w) in enumerate(zip(headers, widths)):
        ws.set_column(i, i, w)
        ws.write(0, i, h, header_fmt)


def add_integer_check(ws, col_letter: str, fmts: dict) -> None:
    """Format a column as integer; reject and pink-fill non-whole values."""
    last = DATA_ROWS + 1
    col_idx = _letter_to_idx(col_letter)
    # Apply integer number format to the data range via set_column.
    # Header (row 0) is written separately with header_fmt which overrides.
    ws.set_column(col_idx, col_idx, None, fmts["integer"])
    rng = f"{col_letter}2:{col_letter}{last}"
    ws.data_validation(
        rng,
        {
            "validate": "integer",
            "criteria": ">=",
            "value": 1,
            "ignore_blank": True,
            "error_title": "Invalid question number",
            "error_message": "Question number must be a whole number ≥ 1.",
        },
    )
    ws.conditional_format(
        rng,
        {
            "type": "formula",
            "criteria": (
                f'=AND(${col_letter}2<>"",'
                f"OR(NOT(ISNUMBER(${col_letter}2)),"
                f"IFERROR(${col_letter}2<>INT(${col_letter}2),TRUE),"
                f"${col_letter}2<1))"
            ),
            "format": fmts["issue_fill"],
        },
    )


def _column_id_valid(cell_ref: str) -> str:
    """Excel formula returning TRUE when `cell_ref` looks like an Excel column ID."""
    pad = f'TRIM({cell_ref})&"AAA"'
    chars = ",".join(
        f"AND(CODE(MID({pad},{i},1))>=65,CODE(MID({pad},{i},1))<=90)" for i in (1, 2, 3)
    )
    return f"AND(LEN(TRIM({cell_ref}))>=1,LEN(TRIM({cell_ref}))<=3,{chars})"


def add_column_id_check(ws, col_letter: str, fmts: dict) -> None:
    """Reject and pink-fill values that aren't 1-3 uppercase A-Z letters."""
    last = DATA_ROWS + 1
    rng = f"{col_letter}2:{col_letter}{last}"
    ws.data_validation(
        rng,
        {
            "validate": "custom",
            "value": "=" + _column_id_valid(f"{col_letter}2"),
            "ignore_blank": True,
            "error_title": "Invalid column ID",
            "error_message": "Column ID must be 1-3 uppercase letters (e.g. A, BF, AAC).",
        },
    )
    ws.conditional_format(
        rng,
        {
            "type": "formula",
            "criteria": (
                f'=AND(${col_letter}2<>"",NOT({_column_id_valid(f"${col_letter}2")}))'
            ),
            "format": fmts["issue_fill"],
        },
    )


def add_offlimit_columns_check(
    ws, first_offlimit: str, sheet_label: str, fmts: dict
) -> None:
    """Block typing into columns at/after `first_offlimit` and pink-fill any data there.

    Pairs a custom-formula data validation (rejects new input) with a CF rule
    (highlights anything pasted in). Doesn't extend an Issues row — the workbook-
    level audit appender handles the cross-cutting "data found out of range" message.
    """
    last_row = DATA_ROWS + 1
    rng = f"{first_offlimit}2:XFD{last_row}"
    ws.data_validation(
        rng,
        {
            "validate": "custom",
            "value": "=FALSE()",
            "ignore_blank": True,
            "error_title": "Out of range",
            "error_message": (
                f'The "{sheet_label}" sheet only uses columns up to '
                f"{chr(ord(first_offlimit) - 1)}. Don't add data here."
            ),
        },
    )
    ws.conditional_format(
        rng,
        {
            "type": "formula",
            # Relative reference (no $ on column) so each cell checks itself,
            # not the top-left of the CF range.
            "criteria": f'={first_offlimit}2<>""',
            "format": fmts["issue_fill"],
        },
    )


def add_required_field_checks(ws, letters: list[str], fmts: dict) -> None:
    """Pink-fill blank cells in `letters` when any sibling on the row has data."""
    last = DATA_ROWS + 1
    for letter in letters:
        siblings = [s for s in letters if s != letter]
        sibling_check = (
            "OR(" + ",".join(f'${s}2<>""' for s in siblings) + ")"
            if siblings
            else "TRUE"
        )
        ws.conditional_format(
            f"{letter}2:{letter}{last}",
            {
                "type": "formula",
                "criteria": f'=AND(${letter}2="",{sibling_check})',
                "format": fmts["issue_fill"],
            },
        )


def _letter_to_col_num(target: str) -> str:
    """Excel formula converting a 1-3 letter column ID to a column number."""
    t = f"TRIM({target})"
    return (
        f"CHOOSE(LEN({t}),"
        f"CODE({t})-64,"
        f"(CODE(LEFT({t},1))-64)*26+(CODE(RIGHT({t},1))-64),"
        f"(CODE(LEFT({t},1))-64)*676+(CODE(MID({t},2,1))-64)*26+(CODE(RIGHT({t},1))-64)"
        f")"
    )


def _missing_response_formula(target: str) -> str:
    """TRUE when `target` is non-blank and Responses!<target>1 is empty/out of range."""
    col_num = _letter_to_col_num(target)
    return f'AND({target}<>"",IFERROR(INDEX({SHEET_RESPONSES}!$A$1:$XFD$1,1,{col_num}),"")="")'


def highlight_missing_response_column(ws, col_letter: str, fmts: dict) -> None:
    """Pink-fill cells whose letter does not match a populated Responses header."""
    last = DATA_ROWS + 1
    ws.conditional_format(
        f"{col_letter}2:{col_letter}{last}",
        {
            "type": "formula",
            "criteria": "=" + _missing_response_formula(f"${col_letter}2"),
            "format": fmts["issue_fill"],
        },
    )


def write_dummy_responses(ws, fmts: dict, n_rows: int = 40, seed: int = 42) -> None:
    rng = random.Random(seed)
    widths = [14, 12, 10, 18, 18, 60, 12, 60, 60, 12]
    for i, w in enumerate(widths):
        ws.set_column(i, i, w)
    for i, h in enumerate(DUMMY_HEADERS):
        ws.write(0, i, h, fmts["header"])

    def maybe(value, p_blank: float = 0.05):
        return "" if rng.random() < p_blank else value

    # Conditional format: pink-fill any header cell across A1:ZZ1 that's empty
    # while its column has data below. Mirrors the Issues-sheet rule and gives
    # immediate visual feedback at the point of edit.
    ws.conditional_format(
        f"A1:{RESPONSE_LAST_LETTER}1",
        {
            "type": "formula",
            "criteria": f'=AND(A$1="",COUNTA(A$2:A${RESPONSE_DATA_LAST_ROW})>0)',
            "format": fmts["issue_fill"],
        },
    )

    for r in range(n_rows):
        row = r + 1  # 0-indexed
        ws.write(row, 0, f"R{r + 1:04d}")
        ws.write(row, 1, maybe(rng.choice(DUMMY_REGIONS)))
        ws.write(row, 2, maybe(rng.choice(DUMMY_AGE_BANDS)))
        ws.write(row, 3, maybe(rng.choice(DUMMY_ORG_TYPES)))
        ws.write(row, 4, maybe(rng.choice(DUMMY_AGREE)))
        ws.write(row, 5, maybe(rng.choice(DUMMY_REASONS), 0.15))
        ws.write(row, 6, maybe(rng.choice(DUMMY_PRIORITY)))
        ws.write(row, 7, maybe(rng.choice(DUMMY_EXPLANATIONS), 0.2))
        ws.write(row, 8, maybe(rng.choice(DUMMY_SUGGESTIONS), 0.3))
        ws.write(row, 9, maybe(rng.choice(DUMMY_RECOMMEND)))


def build_helpers_sheet(ws) -> None:
    """Hidden sheet with per-Responses-column uniqueness ratio (row 1) and count (row 2).

    Runs once per column rather than once per audit row. Non-volatile (no INDIRECT).
    Hidden so users can't overwrite it.
    """
    for col_idx, letter in enumerate(RESPONSE_LETTERS):
        src = f"{SHEET_RESPONSES}!{letter}2:{letter}{RESPONSE_DATA_LAST_ROW}"
        ratio = f'=IFERROR(ROWS(UNIQUE(FILTER({src},{src}<>"")))/COUNTA({src}),0)'
        count = f"=COUNTA({src})"
        ws.write_formula(HELPER_RATIO_ROW - 1, col_idx, ratio)
        ws.write_formula(HELPER_COUNT_ROW - 1, col_idx, count)
    ws.write(2, 0, "Internal helpers — do not edit. Hidden by default.")


def _inter_formula(a_cell: str, b_cell: str, na_cell: str) -> str:
    """4-gram intersection size as a single SUMPRODUCT over a SEQUENCE array.

    SEQUENCE(na) yields 1..na; MID broadcasts over it to produce the array
    of 4-grams of `a`; SEARCH broadcasts each gram against `b`; ISNUMBER
    coerces position-or-error to TRUE/FALSE; SUMPRODUCT sums the 0/1s.
    Confirmed to evaluate correctly in the target Excel build — SEQUENCE
    is on the supported dynamic-array list (see label_similarity_debugging.md).
    """
    return (
        f"SUMPRODUCT(--ISNUMBER(SEARCH(MID({a_cell},SEQUENCE({na_cell}),4),{b_cell})))"
    )


def build_label_similarity_helpers(ws) -> None:
    """Per-metadata-row 4-gram Jaccard similarity, exploded across LABEL_SIM_FIELDS columns.

    Each block (one per metadata sheet/letter-field) holds 8 columns: L, H, a, b,
    na, nb, inter, sim. The exploded layout keeps each cell single-purpose
    and inspectable on the (hidden) `_helpers` sheet. The Issues sheet reads
    only the `sim` column.
    """
    qtext_field = "C"  # question_text column on every metadata sheet
    for sheet, letter_field in LABEL_SIM_BLOCKS:
        cols = {f: _sim_block_col(sheet, letter_field, f) for f in LABEL_SIM_FIELDS}
        for f in LABEL_SIM_FIELDS:
            ws.write(
                HELPER_SIM_START_ROW - 2,
                _letter_to_idx(cols[f]),
                f"{sheet[:6]} {letter_field} {f}",
            )

        for r in range(2, AUDIT_WINDOW + 2):
            helper_row = HELPER_SIM_START_ROW + (r - 2)
            qu_letter = f"'{sheet}'!${letter_field}${r}"
            qu_qtext = f"'{sheet}'!${qtext_field}${r}"

            L_cell = f"${cols['L']}${helper_row}"
            H_cell = f"${cols['H']}${helper_row}"
            a_cell = f"${cols['a']}${helper_row}"
            b_cell = f"${cols['b']}${helper_row}"
            na_cell = f"${cols['na']}${helper_row}"
            nb_cell = f"${cols['nb']}${helper_row}"
            inter_cell = f"${cols['inter']}${helper_row}"

            ws.write_formula(helper_row - 1, _letter_to_idx(cols["L"]), f"={qu_letter}")
            ws.write_formula(
                helper_row - 1,
                _letter_to_idx(cols["H"]),
                f'=IFERROR(INDEX({SHEET_RESPONSES}!$1:$1,1,{_letter_to_col_num(L_cell)}),"")',
            )
            ws.write_formula(
                helper_row - 1,
                _letter_to_idx(cols["a"]),
                f"=LOWER(TRIM(LEFT({qu_qtext},{LABEL_MAX_LEN})))",
            )
            ws.write_formula(
                helper_row - 1,
                _letter_to_idx(cols["b"]),
                f"=LOWER(TRIM(LEFT({H_cell},{LABEL_MAX_LEN})))",
            )
            ws.write_formula(
                helper_row - 1, _letter_to_idx(cols["na"]), f"=MAX(LEN({a_cell})-3,0)"
            )
            ws.write_formula(
                helper_row - 1, _letter_to_idx(cols["nb"]), f"=MAX(LEN({b_cell})-3,0)"
            )
            inter_body = _inter_formula(a_cell, b_cell, na_cell)
            inter_col = _letter_to_idx(cols["inter"])
            # SEQUENCE inside `inter` is a dynamic-array function — needs the
            # cm="1" / metadata.xml markers that write_dynamic_array_formula
            # emits. Plain write_formula here ships an inconsistent file and
            # Excel hits the repair dialog on open.
            ws.write_dynamic_array_formula(
                helper_row - 1,
                inter_col,
                helper_row - 1,
                inter_col,
                f"=IF(OR({na_cell}<=0,{nb_cell}<=0),0,{inter_body})",
            )
            ws.write_formula(
                helper_row - 1,
                _letter_to_idx(cols["sim"]),
                f'=IF(OR({L_cell}="",{a_cell}="",{b_cell}="",'
                f'{na_cell}<=0,{nb_cell}<=0),"",'
                f"{inter_cell}/({na_cell}+{nb_cell}-{inter_cell}))",
            )


def write_data_rows(ws, rows: list[tuple]) -> None:
    """Write tuples of values starting at row 2 (0-indexed: row 1)."""
    for r, values in enumerate(rows, start=1):
        for c, v in enumerate(values):
            ws.write(r, c, v)


# --- Issues sheet (live audit log) ---


def _qu_cell(sheet: str, col: str, r: int) -> str:
    return f"'{sheet}'!${col}${r}"


def _violation_required(sheet: str, all_cols: list[str], col: str, r: int) -> str:
    target = _qu_cell(sheet, col, r)
    siblings = [c for c in all_cols if c != col]
    sibling_check = (
        "OR(" + ",".join(f'{_qu_cell(sheet, c, r)}<>""' for c in siblings) + ")"
    )
    return f'AND({target}="",{sibling_check})'


def _violation_column_id(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    target = _qu_cell(sheet, col, r)
    return f'AND({target}<>"",NOT({_column_id_valid(target)}))'


def _violation_integer(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    target = _qu_cell(sheet, col, r)
    return (
        f'AND({target}<>"",'
        f"OR(NOT(ISNUMBER({target})),"
        f"IFERROR({target}<>INT({target}),TRUE),"
        f"{target}<1))"
    )


def _qu_col_ranges() -> list[str]:
    """Ranges holding column-letter references across Open/Closed/Hybrid sheets.

    Bounded at QU_RANGE_LAST_ROW (~1000) rather than DATA_ROWS (100k); COUNTIF cost
    is linear in range size and rows beyond row ~1000 won't be audited anyway.
    """
    last = QU_RANGE_LAST_ROW
    return [
        f"'{SHEET_OPEN}'!$A$2:$A${last}",
        f"'{SHEET_CLOSED}'!$A$2:$A${last}",
        f"'{SHEET_HYBRID}'!$A$2:$A${last}",
        f"'{SHEET_HYBRID}'!$D$2:$D${last}",
    ]


def _qu_qnum_ranges() -> list[str]:
    """Ranges holding question_number values across Open/Closed/Hybrid sheets."""
    last = QU_RANGE_LAST_ROW
    return [
        f"'{SHEET_OPEN}'!$B$2:$B${last}",
        f"'{SHEET_CLOSED}'!$B$2:$B${last}",
        f"'{SHEET_HYBRID}'!$B$2:$B${last}",
    ]


def _all_referenced_col_ranges() -> list[str]:
    """Open/Closed/Hybrid column ranges plus Demographics — used by 'unreferenced response' check."""
    last = QU_RANGE_LAST_ROW
    return _qu_col_ranges() + [f"'{SHEET_DEMOGRAPHICS}'!$A$2:$A${last}"]


def _violation_duplicate_column(
    sheet: str, _all_cols: list[str], col: str, r: int
) -> str:
    target = _qu_cell(sheet, col, r)
    counts = "+".join(f"COUNTIF({rng},{target})" for rng in _qu_col_ranges())
    return f'AND({target}<>"",({counts})>1)'


def _violation_duplicate_qnum(
    sheet: str, _all_cols: list[str], col: str, r: int
) -> str:
    target = _qu_cell(sheet, col, r)
    counts = "+".join(f"COUNTIF({rng},{target})" for rng in _qu_qnum_ranges())
    return f'AND({target}<>"",ISNUMBER({target}),({counts})>1)'


def _uniqueness_violation(target: str, *, op: str) -> str:
    """Common scaffold: target is a non-empty letter, column has data, ratio op threshold.

    Reads pre-computed ratio and count from hidden helper rows on Responses
    (HELPER_RATIO_ROW / HELPER_COUNT_ROW) via INDEX. Non-volatile, O(1) per row.
    """
    col_num = _letter_to_col_num(target)
    ratio = (
        f"IFERROR(INDEX({HELPER_SHEET}!${HELPER_RATIO_ROW}:${HELPER_RATIO_ROW},"
        f"1,{col_num}),0)"
    )
    count = (
        f"IFERROR(INDEX({HELPER_SHEET}!${HELPER_COUNT_ROW}:${HELPER_COUNT_ROW},"
        f"1,{col_num}),0)"
    )
    return f'AND({target}<>"",{count}>0,{ratio}{op}{UNIQUENESS_THRESHOLD})'


def _violation_closed_uniqueness(
    sheet: str, _all_cols: list[str], col: str, r: int
) -> str:
    return _uniqueness_violation(_qu_cell(sheet, col, r), op=">")


def _violation_open_uniqueness(
    sheet: str, _all_cols: list[str], col: str, r: int
) -> str:
    return _uniqueness_violation(_qu_cell(sheet, col, r), op="<")


def _violation_label_similarity(
    sheet: str, _all_cols: list[str], col: str, r: int
) -> str:
    """Read the precomputed similarity from _helpers; fire when below threshold.

    Note: `col` here doubles as the letter_field key into LABEL_SIM_BLOCKS —
    i.e. the metadata-sheet column whose cell contains the Responses column
    letter to compare against ("A" for Open/Closed, "A" or "D" for Hybrid).
    Other VIOLATION_FNS entries treat `col` as "the column being validated";
    label_similarity is the only rule that also uses it as a block selector.
    """
    sim_col = _sim_block_col(sheet, col, "sim")
    helper_row = HELPER_SIM_START_ROW + (r - 2)
    helper_cell = f"{HELPER_SHEET}!${sim_col}${helper_row}"
    return f"AND(ISNUMBER({helper_cell}),{helper_cell}<{LABEL_SIMILARITY_THRESHOLD})"


VIOLATION_FNS = {
    "required": _violation_required,
    "column_id": _violation_column_id,
    "integer": _violation_integer,
    "missing_response": lambda sheet, _cols, col, r: _missing_response_formula(
        _qu_cell(sheet, col, r)
    ),
    "duplicate_column": _violation_duplicate_column,
    "duplicate_qnum": _violation_duplicate_qnum,
    "closed_uniqueness": _violation_closed_uniqueness,
    "open_uniqueness": _violation_open_uniqueness,
    "label_similarity": _violation_label_similarity,
}


class MetaCol(NamedTuple):
    """One column on a metadata sheet (Demographics / Open / Closed / Hybrid)."""

    id: str  # Excel column letter on the metadata sheet ("A", "B", ...)
    header: str
    width: int
    comment: str
    comment_size: tuple[int, int]  # (width, height) of the cell comment box
    checks: tuple[str, ...] = ()  # subset of {"column_id", "integer", "missing_response"}


class MetaSheet(NamedTuple):
    """A metadata sheet's full build spec — headers, comments, checks, sample rows."""

    name: str
    columns: tuple[MetaCol, ...]
    samples: tuple[tuple, ...]


# Comment text for fields that are identical across Open / Closed / Hybrid.
_QNUM_COMMENT = (
    "A whole number ≥ 1. Must be unique across all Open, Closed and Hybrid "
    "questions. Used to order the questions as they appear in the Consult application."
)
_QNUM_CHECKS = ("integer",)
_LETTER_CHECKS = ("column_id", "missing_response")

METADATA_SHEETS: tuple[MetaSheet, ...] = (
    MetaSheet(
        name=SHEET_DEMOGRAPHICS,
        columns=(
            MetaCol(
                id="A",
                header="Column letter (in Responses sheet)",
                width=32,
                comment=(
                    "The Excel column letter (A, B, ..., AA, ...) of the column on the "
                    "Responses sheet that holds this demographic. Look at the Responses tab "
                    "and find the column whose header matches what you want to track."
                ),
                comment_size=(260, 120),
                checks=_LETTER_CHECKS,
            ),
            MetaCol(
                id="B",
                header="Demographics label",
                width=36,
                comment=(
                    "Short, human-readable name for this demographic — e.g. 'Region', "
                    "'Age band', 'Organisation type'. Shown to analysts in the dashboard."
                ),
                comment_size=(260, 100),
            ),
        ),
        samples=(
            ("B", "Region"),
            ("C", "Age band"),
            ("D", "Organisation type"),
        ),
    ),
    MetaSheet(
        name=SHEET_OPEN,
        columns=(
            MetaCol(
                id="A",
                header="Column letter (in Responses sheet)",
                width=32,
                comment=(
                    "The Excel column letter on the Responses sheet that holds the "
                    "free-text responses for this question. E.g. if Responses!I1 contains "
                    "the question header, type 'I' here."
                ),
                comment_size=(260, 120),
                checks=_LETTER_CHECKS,
            ),
            MetaCol(
                id="B",
                header="Question number",
                width=18,
                comment=_QNUM_COMMENT,
                comment_size=(260, 100),
                checks=_QNUM_CHECKS,
            ),
            MetaCol(
                id="C",
                header="Question text (full wording shown to respondent)",
                width=70,
                comment=(
                    "Paste the question as it appeared to respondents, "
                    "including any context required . The text should make sense on its own — an "
                    "analyst reading just this row should understand what was asked."
                ),
                comment_size=(280, 130),
            ),
        ),
        samples=(("I", 3, "Do you have any other suggestions or comments?"),),
    ),
    MetaSheet(
        name=SHEET_CLOSED,
        columns=(
            MetaCol(
                id="A",
                header="Column letter (in Responses sheet)",
                width=32,
                comment=(
                    "The Excel column letter on the Responses sheet that holds the "
                    "multiple-choice responses for this question."
                ),
                comment_size=(260, 100),
                checks=_LETTER_CHECKS,
            ),
            MetaCol(
                id="B",
                header="Question number",
                width=18,
                comment=_QNUM_COMMENT,
                comment_size=(260, 100),
                checks=_QNUM_CHECKS,
            ),
            MetaCol(
                id="C",
                header="Question text (full wording shown to respondent)",
                width=70,
                comment=(
                    "Paste the question wording as it appeared to respondents. Make sure "
                    "it makes sense and has enough context to be understood on its own."
                ),
                comment_size=(260, 80),
            ),
        ),
        samples=(("J", 4, "Would you recommend this approach to others?"),),
    ),
    MetaSheet(
        name=SHEET_HYBRID,
        columns=(
            MetaCol(
                id="A",
                header="Free-text column letter (in Responses)",
                width=32,
                comment=(
                    "Excel column letter on the Responses sheet for the FREE-TEXT part of "
                    "this hybrid question (the 'why?' / 'please explain')."
                ),
                comment_size=(280, 110),
                checks=_LETTER_CHECKS,
            ),
            MetaCol(
                id="B",
                header="Question number",
                width=18,
                comment=_QNUM_COMMENT,
                comment_size=(260, 100),
                checks=_QNUM_CHECKS,
            ),
            MetaCol(
                id="C",
                header="Question text (full wording shown to respondent)",
                width=70,
                comment=(
                    "Paste the question as it appeared to respondents, and it should have "
                    "enough context to make sense on its own (e.g. 'How satisfied are you "
                    "with X?')."
                ),
                comment_size=(260, 80),
            ),
            MetaCol(
                id="D",
                header="Multiple-choice column letter (in Responses)",
                width=32,
                comment=(
                    "Excel column letter on the Responses sheet for the MULTIPLE-CHOICE part "
                    "of this hybrid question (the agree/disagree / yes-no answer)."
                ),
                comment_size=(280, 110),
                checks=_LETTER_CHECKS,
            ),
        ),
        samples=(
            ("F", 1, "What is your level of support for the proposal, and why?", "E"),
            ("H", 2, "How important is this issue, and please explain.", "G"),
        ),
    ),
)


def build_metadata_sheet(ws, meta: MetaSheet, fmts: dict) -> None:
    """Wire up one metadata sheet: headers, comments, per-column checks, samples.

    Check order (column_id → integer → missing_response) and per-column iteration
    order match the original hand-rolled main() blocks so the workbook output
    stays content-identical.
    """
    write_headers(
        ws,
        [c.header for c in meta.columns],
        [c.width for c in meta.columns],
        fmts["header"],
    )
    for c in meta.columns:
        cw, ch = c.comment_size
        ws.write_comment(f"{c.id}1", c.comment, {"width": cw, "height": ch})

    add_required_field_checks(ws, [c.id for c in meta.columns], fmts)
    for c in meta.columns:
        if "column_id" in c.checks:
            add_column_id_check(ws, c.id, fmts)
    for c in meta.columns:
        if "integer" in c.checks:
            add_integer_check(ws, c.id, fmts)
    for c in meta.columns:
        if "missing_response" in c.checks:
            highlight_missing_response_column(ws, c.id, fmts)

    first_offlimit = _idx_to_letter(_letter_to_idx(meta.columns[-1].id) + 1)
    add_offlimit_columns_check(ws, first_offlimit, meta.name, fmts)
    write_data_rows(ws, list(meta.samples))


class Rule(NamedTuple):
    """One audit rule on a metadata sheet.

    `col` is the column letter being checked. `vkind` keys into VIOLATION_FNS.
    `message` may contain `{value}` — substituted with the offending cell's
    value at audit time. `fix` is the static "how to fix" text shown to users.
    """

    col: str
    label: str
    vkind: str
    message: str
    fix: str


QU_AUDIT_SCHEMA: dict[str, dict] = {
    SHEET_DEMOGRAPHICS: {
        "cols": ["A", "B"],
        "rules": [
            Rule(
                "A",
                "Missing column ID",
                "required",
                "This row is missing a column ID, so it is unclear which column on the Responses sheet should be used.",
                "Type the Excel column letter (e.g. B or AC) from the Responses sheet that holds this demographic.",
            ),
            Rule(
                "B",
                "Missing label",
                "required",
                "This row has no label, so this demographic will be unnamed in your results.",
                "Type a short, human-readable name for this demographic, e.g. 'Region' or 'Age group'.",
            ),
            Rule(
                "A",
                "Invalid column ID format",
                "column_id",
                "'{value}' isn't a valid Excel column letter, so we can't find this column on the Responses sheet.",
                "Use 1-3 capital letters only — A, B, …, Z, AA, AB, …, ZZZ. No numbers or symbols.",
            ),
            Rule(
                "A",
                "Column not in Responses",
                "missing_response",
                "Column '{value}' has no header on the Responses sheet, so there may be no responses to compare to in that column.",
                "Check for a typo in the column letter, or add a header (and the responses) into that column on Responses.",
            ),
        ],
    },
    SHEET_OPEN: {
        "cols": ["A", "B", "C"],
        "rules": [
            Rule(
                "A",
                "Missing column ID",
                "required",
                "This row has no column ID, so it is unclear which column on the Responses sheet should be used.",
                "Type the Excel column letter from the Responses sheet (e.g. B or AC) that holds the free-text responses for this question.",
            ),
            Rule(
                "B",
                "Missing question_number",
                "required",
                "This row has no question number. This number is used to order the questions as they appear in the Consult application.",
                "Enter a whole number (e.g. 1 or higher) that has not been used by another question yet. Each number must be unique across the Open, Closed, and Hybrid sheets.",
            ),
            Rule(
                "C",
                "Missing question_text",
                "required",
                "This row has no question wording. The AI model will not have any context for interpreting the responses, which will lead to poor results.",
                "Paste the question as it appeared to respondents, and it should have enough context to make sense on its own (e.g. 'How satisfied are you with X?', NOT 'Satisfaction').",
            ),
            Rule(
                "A",
                "Invalid column ID format",
                "column_id",
                "'{value}' isn't a valid Excel column letter.",
                "Use 1-3 capital letters only (e.g. A, BF, AAC). No numbers or symbols.",
            ),
            Rule(
                "B",
                "Question number must be a whole integer >= 1",
                "integer",
                "'{value}' isn't a whole number of 1 or more. Question numbers are used to order the questions as they appear in the Consult application, so they need to be plain whole numbers.",
                "Replace it with a whole number such as 1, 2, 3. Decimals, text, and 0 aren't allowed.",
            ),
            Rule(
                "A",
                "Column not in Responses",
                "missing_response",
                "Column '{value}' has no header on the Responses sheet, which may mean there are no responses to analyse in this column.",
                "Double-check the column letter for typos, or paste the responses (with a header in row 1) into that column on Responses sheet.",
            ),
            Rule(
                "A",
                "Duplicate column reference",
                "duplicate_column",
                "Column '{value}' is already used by another row. Each Excel column should feed only one question.",
                "Pick a different column letter, or remove the duplicate row from the Open / Closed / Hybrid sheets.",
            ),
            Rule(
                "B",
                "Duplicate question_number",
                "duplicate_qnum",
                "Question number '{value}' is already used by another row. Numbers must be unique because they're used to order the questions as they appear in the Consult application.",
                "Renumber one of the rows so every question across Open, Closed, and Hybrid has its own unique number.",
            ),
            Rule(
                "A",
                "Open column looks multichoice",
                "open_uniqueness",
                "Column '{value}' has very few different responses (≤20% are unique). That usually means it's a multiple-choice question rather than free text.",
                "If respondents picked from a list, move this row to the Multiple Choice Questions sheet. If it really is free text, you can ignore this warning.",
            ),
            Rule(
                "A",
                "question_text differs from Responses header",
                "label_similarity",
                "The question wording on this row doesn't closely match the header in column '{value}' on Responses, so the wrong column may have been chosen.",
                "Check the column letter is correct, or update the question wording so it matches the header on the Responses sheet.",
            ),
        ],
    },
    SHEET_CLOSED: {
        "cols": ["A", "B", "C"],
        "rules": [
            Rule(
                "A",
                "Missing column ID",
                "required",
                "This row has no column ID, so it is unclear which column on the Responses sheet should be used.",
                "Type the Excel column letter from the Responses sheet (e.g. B or AC) that holds the multiple-choice responses for this question.",
            ),
            Rule(
                "B",
                "Missing question_number",
                "required",
                "This row has no question number. Numbers identify each question in your results and are used to order the questions as they appear in the Consult application.",
                "Enter a whole number 1 or higher. Each number must be unique across the Open, Closed, and Hybrid sheets.",
            ),
            Rule(
                "C",
                "Missing question_text",
                "required",
                "This row has no question wording. The AI model will not have any context for interpreting the responses, which will lead to poor results.",
                "Paste the question as it appeared to respondents, and it should have enough context to make sense on its own (e.g. 'How satisfied are you with X?', NOT 'Satisfaction').",
            ),
            Rule(
                "A",
                "Invalid column ID format",
                "column_id",
                "'{value}' isn't a valid Excel column letter, so Themefinder can't find this column on the Responses sheet.",
                "Use 1-3 capital letters only (e.g. A, BF, AAC). No numbers or symbols.",
            ),
            Rule(
                "B",
                "Question number must be a whole integer >= 1",
                "integer",
                "'{value}' isn't a whole number of 1 or more. Question numbers are used to order the questions as they appear in the Consult application, so they need to be plain whole numbers.",
                "Replace it with a whole number such as 1, 2, 3. Decimals, text, and 0 aren't allowed.",
            ),
            Rule(
                "A",
                "Column not in Responses",
                "missing_response",
                "Column '{value}' has no header on the Responses sheet, which may mean there are no responses to analyse in this column.",
                "Double-check the column letter for typos, or paste the responses (with a header in row 1) into that column on Responses sheet.",
            ),
            Rule(
                "A",
                "Duplicate column reference",
                "duplicate_column",
                "Column '{value}' is already used by another row. Each Excel column should feed only one question.",
                "Pick a different column letter, or remove the duplicate row from the Open / Closed / Hybrid sheets.",
            ),
            Rule(
                "B",
                "Duplicate question_number",
                "duplicate_qnum",
                "Question number '{value}' is already used by another row. Numbers must be unique because they're used to order the questions as they appear in the Consult application.",
                "Renumber one of the rows so every question across Open, Closed, and Hybrid has its own unique number.",
            ),
            Rule(
                "A",
                "Closed column looks like free text",
                "closed_uniqueness",
                "Column '{value}' has lots of different responses (>20% are unique). That usually means it's a free-text question rather than multiple choice.",
                "If respondents typed their own responses, move this row to the Open Questions sheet. If it really is multiple choice, you can ignore this warning.",
            ),
            Rule(
                "A",
                "question_text differs from Responses header",
                "label_similarity",
                "The question wording on this row doesn't closely match the header in column '{value}' on Responses, so the wrong column may have been chosen.",
                "Check the column letter is correct, or update the question wording so it matches the header on the Responses sheet.",
            ),
        ],
    },
    SHEET_HYBRID: {
        "cols": ["A", "B", "C", "D"],
        "rules": [
            Rule(
                "A",
                "Missing open_column",
                "required",
                "This row has no open_column value, so it is unclear which column on the Responses sheet holds the free-text part of this hybrid question.",
                "Type the Excel column letter from Responses that holds the free-text part of this hybrid question.",
            ),
            Rule(
                "B",
                "Missing question_number",
                "required",
                "This row has no question number. Numbers identify each question in your results and are used to order the questions as they appear in the Consult app.",
                "Enter a whole number 1 or higher. Each number must be unique across the Open, Closed, and Hybrid sheets.",
            ),
            Rule(
                "C",
                "Missing question_text",
                "required",
                "This row has no question wording, so the AI model will not have any context for interpreting the responses, which will lead to poor results.",
                "Paste the question exactly as it appeared to respondents, including any indication that it's a hybrid question (e.g. 'What do you think of X, and why?')."
                "It should have enough context to make sense on its own.",
            ),
            Rule(
                "D",
                "Missing closed_column",
                "required",
                "This row has no column letter for the multiple-choice part, so it is unclear which column on the Responses sheet holds those responses.",
                "Type the Excel column letter from Responses sheet (e.g. B, CF) that holds the multiple-choice part of this hybrid question.",
            ),
            Rule(
                "A",
                "Invalid open_column format",
                "column_id",
                "'{value}' isn't a valid Excel column letter, so it can't be found on the Responses sheet.",
                "Use 1-3 capital letters only (e.g. A, BF, AAC). No numbers or symbols. Enter the column letter for the free-text part of this hybrid question.",
            ),
            Rule(
                "D",
                "Invalid closed_column format",
                "column_id",
                "'{value}' isn't a valid Excel column letter, so it can't be found on the Responses sheet.",
                "Use 1-3 capital letters only (e.g. A, BF, AAC). No numbers or symbols. Enter the column letter for the multiple-choice part of this hybrid question.",
            ),
            Rule(
                "B",
                "Question number must be a whole integer >= 1",
                "integer",
                "'{value}' isn't a whole number of 1 or more. Question numbers are used to order the questions as they appear in the Consult application, so they need to be plain whole numbers.",
                "Replace it with a whole number such as 1, 2, 3. Decimals, text, and 0 aren't allowed.",
            ),
            Rule(
                "A",
                "open_column not in Responses",
                "missing_response",
                "Column '{value}' has no header on the Responses sheet, so there may be no free-text responses to compare to in that column.",
                "Double-check the column letter for typos, or paste the responses (with a header in row 1) into that column on Responses.",
            ),
            Rule(
                "D",
                "closed_column not in Responses",
                "missing_response",
                "Column '{value}' has no header on the Responses sheet, so there may be no multiple-choice responses to analyse.",
                "Double-check the column letter for typos, or paste the responses (with a header in row 1) into that column on Responses.",
            ),
            Rule(
                "A",
                "Duplicate column reference",
                "duplicate_column",
                "Column '{value}' is already used by another row. Each Excel column should feed only one question.",
                "Pick a different column letter, or remove the duplicate row from the Open / Closed / Hybrid sheets.",
            ),
            Rule(
                "D",
                "Duplicate column reference",
                "duplicate_column",
                "Column '{value}' is already used by another row. Each Excel column should feed only one question.",
                "Pick a different column letter, or remove the duplicate row from the Open / Closed / Hybrid sheets.",
            ),
            Rule(
                "B",
                "Duplicate question_number",
                "duplicate_qnum",
                "Question number '{value}' is already used by another row. Numbers must be unique because they're used to order the questions as they appear in the Consult app.",
                "Renumber one of the rows so every question across Open, Closed, and Hybrid has its own unique number.",
            ),
            Rule(
                "A",
                "Open column looks multichoice",
                "open_uniqueness",
                "Column '{value}' on the Responses sheet has very few different responses (≤20% are unique), which looks more like multiple choice than free text.",
                "If respondents picked from a list, this column belongs in the Multiple Choice Questions sheet (or as the closed_column of a hybrid). If it really is free text, you can ignore this warning.",
            ),
            Rule(
                "D",
                "Closed column looks like free text",
                "closed_uniqueness",
                "Column '{value}' on the Responses sheet has lots of different responses (>20% are unique), which looks more like free text than multiple choice.",
                "If respondents typed their own responses, this column belongs in the Open Questions sheet (or as the open_column of a hybrid). If it really is multiple choice, you can ignore this warning.",
            ),
            Rule(
                "A",
                "question_text differs from open_column header",
                "label_similarity",
                "The question wording doesn't closely match the header for column '{value}' on Responses, so the wrong free-text column may have been chosen.",
                "Check the open_column letter is correct, or update the question wording so it matches the Responses header.",
            ),
            Rule(
                "D",
                "question_text differs from closed_column header",
                "label_similarity",
                "The question wording doesn't closely match the header for column '{value}' on Responses, so the wrong multiple-choice column may have been chosen.",
                "Check the closed_column letter is correct, or update the question wording so it matches the Responses header.",
            ),
        ],
    },
}


def _xl_str(s: str) -> str:
    """Wrap a Python string as an Excel string literal (double-quote escaping)."""
    return '"' + s.replace('"', '""') + '"'


def _issue_text_formula(target: str, msg_tmpl: str) -> str:
    """Build an Excel string expression for the issue message, substituting {value}."""
    if "{value}" not in msg_tmpl:
        return _xl_str(msg_tmpl)
    parts = msg_tmpl.split("{value}")
    pieces: list[str] = []
    for i, part in enumerate(parts):
        if part:
            pieces.append(_xl_str(part))
        if i < len(parts) - 1:
            pieces.append(target)
    return "&".join(pieces)


def _label_similarity_msg_formula(sheet: str, target: str, r: int) -> str:
    """Issue-cell expression for label_similarity rules.

    Includes the question_text and the Responses header on separate lines
    (CHAR(10)) so the user can compare them at a glance. Wrap-text on the
    Issue column makes the linebreaks render as multiple lines.
    """
    qtext = _qu_cell(sheet, "C", r)
    header = f'INDIRECT("{SHEET_RESPONSES}!"&{target}&"1")'
    blank_line = "CHAR(10)&CHAR(10)"
    pieces = [
        _xl_str("The question wording below doesn't closely match the "
                "Responses header for column "),
        target,
        _xl_str("."),
        blank_line,
        _xl_str("Question text:"),
        "CHAR(10)",
        qtext,
        blank_line,
        _xl_str("Responses header for column "),
        target,
        _xl_str(":"),
        "CHAR(10)",
        header,
    ]
    return "&".join(pieces)


def _workbook_count_rule_row() -> dict:
    """Total distinct metadata-sheet column count vs Responses column count.

    Uses VSTACK/UNIQUE/FILTER (Excel 365 / 2021+); pre-365 Excel will show a
    #NAME? in the Issue cell, which is harmless — the count check just won't fire.
    """
    vstack_args = ",".join(_qu_col_ranges())
    distinct_count = (
        f"IFERROR(ROWS(UNIQUE(FILTER(VSTACK({vstack_args}),"
        f'VSTACK({vstack_args})<>""))),0)'
    )
    resp_count = f"COUNTA({SHEET_RESPONSES}!$1:$1)-1"
    violation = f"({distinct_count})>({resp_count})"
    msg = (
        f'"Your question setup points at "&{distinct_count}&" different column(s), '
        f'but Responses only has "&({resp_count})&" column(s) of data — '
        f"some of the columns you have referenced don't exist.\""
    )
    fix_text = (
        "Either remove the questions / demographics that point to columns "
        "that aren't in Responses, or add the missing columns (with headers "
        "and responses) to the Responses sheet."
    )
    return {
        "sheet": "(workbook)",
        "cell": "-",
        "rule": "Referenced column count exceeds Responses",
        "severity": SEVERITY_BY_VKIND["workbook_count"],
        "issue_formula": f'=IF({violation},{msg},"")',
        "fix": fix_text,
    }


def _missing_header_rule_rows() -> list[dict]:
    """One row per A..Z that fires when a Responses column has data but no header."""
    rows: list[dict] = []
    for letter in RESPONSE_LETTERS:
        header = f"{SHEET_RESPONSES}!${letter}$1"
        data_range = f"{SHEET_RESPONSES}!${letter}$2:${letter}${RESPONSE_DATA_LAST_ROW}"
        violation = f'AND({header}="",COUNTA({data_range})>0)'
        msg = (
            f'"Column {letter} on Responses has responses but no header in row 1, '
            f'so nobody (and Themefinder) knows what this column is."'
        )
        fix_text = (
            f"Type a short header in Responses!{letter}1 describing what this "
            "column contains (e.g. the question or demographic name), or "
            "delete the data in that column if it isn't needed."
        )
        rows.append(
            {
                "sheet": SHEET_RESPONSES,
                "cell": f"{letter}1",
                "rule": "Missing header",
                "severity": SEVERITY_BY_VKIND["missing_header"],
                "issue_formula": f'=IF({violation},{msg},"")',
                "fix": fix_text,
            }
        )
    return rows


def _unreferenced_response_rule_rows() -> list[dict]:
    """One row per A..Z asking whether that Responses column is referenced.

    Fires when Responses!<L>1 is non-empty, isn't a "Response ID"-style header,
    and no Demographics / Open / Closed / Hybrid row references letter L.
    """
    ref_ranges = _all_referenced_col_ranges()
    rows: list[dict] = []
    for letter in RESPONSE_LETTERS:
        header = f"{SHEET_RESPONSES}!${letter}$1"
        # COUNTIF with literal letter — note doubled "" for embedding in string.
        ref_count = "+".join(f'COUNTIF({rng},"{letter}")' for rng in ref_ranges)
        violation = (
            f'AND({header}<>"",'
            f'ISERROR(SEARCH("response id",LOWER({header}))),'
            f"({ref_count})=0)"
        )
        msg = (
            f'"Responses column {letter} ("""&{header}&""") has data, but no '
            f"question or demographic is set up to use it — so it won't appear "
            f'in your results."'
        )
        fix_text = (
            f"If you want this column analysed, add a row pointing to "
            f"column {letter} on the Open, Closed, Hybrid, or Demographics "
            "sheet. If it isn't needed, delete the column on Responses."
        )
        rows.append(
            {
                "sheet": SHEET_RESPONSES,
                "cell": f"{letter}1",
                "rule": "Unreferenced response column",
                "severity": SEVERITY_BY_VKIND["unreferenced"],
                "issue_formula": f'=IF({violation},{msg},"")',
                "fix": fix_text,
            }
        )
    return rows


def build_issues_sheet(ws, fmts: dict) -> int:
    """Issues sheet: one row per (sheet, source row, rule); column E is a live formula.

    Layout: A=Sheet, B=Cell, C=Rule, D=Severity, E=Issue, F=How to fix.
    Returns the last data row (1-indexed Excel row) so other sheets can reference it.
    """
    widths = [18, 10, 34, 12, 70, 60]
    for i, w in enumerate(widths):
        # Issue (E) and How-to-fix (F) wrap so multi-line CHAR(10) messages render.
        fmt = fmts["wrap"] if i in (4, 5) else None
        ws.set_column(i, i, w, fmt)

    ws.merge_range("A1:F1", "Outstanding issues", fmts["title"])
    ws.write("A2", "Outstanding issues:", fmts["bold_right"])

    ws.merge_range(
        "A3:F3",
        (
            "Source audit log — every (sheet, row, rule) combination. The "
            "Active issues sheet pulls only the rows where the Issue column is "
            "non-empty, via FILTER(). Hidden by default; unhide via right-click "
            "on a tab → Unhide if you need to inspect raw rules."
        ),
        fmts["italic_wrap"],
    )
    ws.set_row(2, 30)

    for i, h in enumerate(["Sheet", "Cell", "Rule", "Severity", "Issue", "How to fix"]):
        ws.write(3, i, h, fmts["header"])

    rows: list[dict] = []
    for sheet_name, schema in QU_AUDIT_SCHEMA.items():
        cols = schema["cols"]
        for r in range(2, AUDIT_WINDOW + 2):
            for rule in schema["rules"]:
                target = _qu_cell(sheet_name, rule.col, r)
                violation = VIOLATION_FNS[rule.vkind](sheet_name, cols, rule.col, r)
                if rule.vkind == "label_similarity":
                    msg_expr = _label_similarity_msg_formula(sheet_name, target, r)
                else:
                    msg_expr = _issue_text_formula(target, rule.message)
                rows.append(
                    {
                        "sheet": sheet_name,
                        "cell": f"{rule.col}{r}",
                        "rule": rule.label,
                        "severity": SEVERITY_BY_VKIND[rule.vkind],
                        "issue_formula": f'=IF({violation},{msg_expr},"")',
                        "fix": rule.fix,
                    }
                )

    rows.append(_workbook_count_rule_row())
    rows.extend(_missing_header_rule_rows())
    rows.extend(_unreferenced_response_rule_rows())

    # Sort: severity (Error before "To check" before everything else) then rule label.
    severity_rank = {"Error": 0, SEVERITY_TO_CHECK: 1}
    rows.sort(key=lambda r: (severity_rank.get(r["severity"], 99), r["rule"]))

    audit_row = 4  # 0-indexed; Excel row 5 is the first data row
    for row in rows:
        ws.write(audit_row, 0, row["sheet"])
        ws.write(audit_row, 1, row["cell"])
        ws.write(audit_row, 2, row["rule"])
        ws.write(audit_row, 3, row["severity"])
        ws.write_formula(audit_row, 4, row["issue_formula"])
        ws.write(audit_row, 5, row["fix"])
        # Tall enough for wrapped Issue + How-to-fix content; label_similarity
        # rows expand to ~7 lines once the question text + Responses header
        # are spliced in, so give those extra room.
        is_label_sim = row["rule"].startswith("question_text differs")
        ws.set_row(audit_row, 120 if is_label_sim else 75)
        audit_row += 1

    last_excel_row = audit_row  # last data row (Excel 1-indexed) since we incremented after last write
    ws.write_formula(
        "B2",
        f'=SUMPRODUCT(--(E5:E{last_excel_row}<>""))',
        fmts["count"],
    )
    ws.autofilter(f"A4:F{last_excel_row}")
    ws.freeze_panes(4, 0)
    return last_excel_row


def build_active_issues_sheet(ws, wb, source_last_row: int, fmts: dict) -> None:
    """Live view of Issues filtered to non-empty Issue cells, via FILTER().

    Dynamic-array FILTER recalculates with the source formulas, so this sheet
    auto-updates whenever a new violation fires — no manual reapply needed.
    Separate Errors and Warnings counts at the top; severity column is colour-coded.
    """
    widths = [18, 10, 34, 12, 70, 60]
    for i, w in enumerate(widths):
        fmt = fmts["wrap"] if i in (4, 5) else None
        ws.set_column(i, i, w, fmt)
    # Column G is the only writable column on this sheet — users record what
    # they checked / why a "To check" was acceptable. Format with locked=False
    # so worksheet protection (set below) leaves it editable while everything
    # else (A–F) is read-only.
    notes_fmt = wb.add_format(
        {"text_wrap": True, "valign": "top", "locked": False, "bg_color": "#FFFCE6"}
    )
    ws.set_column("G:G", 50, notes_fmt)

    ws.merge_range("A1:G1", SHEET_ACTIVE, fmts["title"])

    err_count = f'=COUNTIF(D5:D{source_last_row},"Error")'
    warn_count = f'=COUNTIF(D5:D{source_last_row},"{SEVERITY_TO_CHECK}")'
    ws.write("A2", "Errors:", fmts["bold_right"])
    ws.write_formula("B2", err_count, fmts["error_count"])
    ws.write("C2", "To check:", fmts["bold_right"])
    ws.write_formula("D2", warn_count, fmts["warning_count"])

    ws.merge_range(
        "A3:G3",
        "Errors MUST be fixed before running the consultation — they will stop the "
        'pipeline. "To check" items are heuristic flags; please review each one '
        "and confirm it's intentional (they may be fine). This sheet updates "
        "automatically as you edit the Demographics, Open, Closed and Hybrid "
        "sheets. See the Guide tab for what each sheet is for and what good "
        "questions look like. The 'My Notes' column on the right is the only "
        "editable column — use it to record what you checked.",
        fmts["italic_wrap"],
    )
    ws.set_row(2, 36)

    headers = [
        "Sheet",
        "Cell",
        "Rule",
        "Severity",
        "Issue",
        "How to fix",
        "My Notes — you can provide a short description of what you checked here",
    ]
    notes_header_fmt = wb.add_format(
        {"bold": True, "bg_color": "#FFE699", "text_wrap": True, "valign": "top"}
    )
    for i, h in enumerate(headers):
        fmt = notes_header_fmt if i == 6 else fmts["header"]
        ws.write(3, i, h, fmt)
    ws.set_row(3, 32)

    formula = (
        f"=FILTER({SHEET_ISSUES}!A5:F{source_last_row},"
        f'IFERROR({SHEET_ISSUES}!E5:E{source_last_row}<>"",TRUE),'
        f'"No outstanding issues — fill in the Demographics, Open, Closed and Hybrid sheets to begin.")'
    )
    ws.write_dynamic_array_formula("A5", formula)

    # Set generous row heights so wrapped Issue / How-to-fix text shows in full.
    # FILTER spill order isn't known at build time, so use a uniform tall height
    # across all data rows; label_similarity messages need ~7 lines.
    for excel_row_idx in range(
        4, source_last_row
    ):  # 0-indexed; Excel rows 5..source_last_row
        ws.set_row(excel_row_idx, 120)

    # Colour-code the severity column on whatever rows the FILTER spills into.
    # Generous bound so the rule still applies if the spill grows.
    cf_range = "D5:D2000"
    ws.conditional_format(
        cf_range,
        {"type": "formula", "criteria": '=$D5="Error"', "format": fmts["error_fill"]},
    )
    ws.conditional_format(
        cf_range,
        {
            "type": "formula",
            "criteria": f'=$D5="{SEVERITY_TO_CHECK}"',
            "format": fmts["issue_fill"],
        },
    )
    ws.freeze_panes(4, 0)
    # Lock the Active issues sheet — it's a live derived view of the Issues
    # source, so any user edit just creates noise. No password; protection
    # is a soft guard. Cells stay selectable so users can copy/inspect, and
    # the underlying FILTER formula and conditional formats keep recalculating.
    ws.protect(
        "",
        {
            "select_locked_cells": True,
            "select_unlocked_cells": True,
            "autofilter": True,
        },
    )


def build_guide_sheet(ws, wb, fmts: dict) -> None:
    """Front-of-workbook orientation: how to use the file, sheet roles, examples.

    Lays out content top-to-bottom in column A (with column B as a wide
    "explanation" column) so users can scroll through linearly without
    needing to know the structure in advance.
    """
    excel_only_fmt = wb.add_format(
        {
            "bold": True,
            "font_size": 14,
            "font_color": "#9C0006",
            "bg_color": "#FFE699",
            "text_wrap": True,
            "valign": "top",
            "align": "left",
            "border": 2,
            "border_color": "#9C0006",
        }
    )
    section_fmt = wb.add_format(
        {
            "bold": True,
            "font_size": 13,
            "bg_color": "#D9E1F2",
            "valign": "top",
        }
    )
    body_fmt = wb.add_format({"text_wrap": True, "valign": "top"})
    body_bold_fmt = wb.add_format({"text_wrap": True, "valign": "top", "bold": True})
    good_fmt = wb.add_format(
        {
            "text_wrap": True,
            "valign": "top",
            "bg_color": "#E2EFDA",
            "border": 1,
            "border_color": "#A9D08E",
        }
    )
    bad_fmt = wb.add_format(
        {
            "text_wrap": True,
            "valign": "top",
            "bg_color": "#FCE4D6",
            "border": 1,
            "border_color": "#E0928E",
        }
    )
    error_chip = wb.add_format(
        {
            "bold": True,
            "bg_color": ERROR_BG,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
        }
    )
    tocheck_chip = wb.add_format(
        {
            "bold": True,
            "bg_color": ISSUE_BG,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
        }
    )

    ws.set_column("A:A", 16)
    ws.set_column("B:B", 60)
    ws.set_column("C:C", 60)
    ws.hide_gridlines(2)

    header_fmt = wb.add_format(
        {"bold": True, "bg_color": HEADER_BG, "border": 1, "valign": "top"}
    )

    ws.merge_range("A1:C1", "Consultation data template — Guide", fmts["title"])
    ws.set_row(0, 26)

    ws.merge_range(
        "A2:C4",
        "⚠  OPEN THIS FILE IN MICROSOFT EXCEL ONLY.\n\n"
        "Google Sheets, Apple Numbers and LibreOffice strip out the "
        "formulas this workbook relies on. The Active issues tab will "
        "appear empty or broken in those apps. If you don't have Excel, ask "
        "your team — don't fill the workbook in elsewhere and copy-paste across.",
        excel_only_fmt,
    )
    for r in range(1, 4):
        ws.set_row(r, 28)

    row = 5  # 0-indexed; Excel row 6

    def section(title: str) -> None:
        nonlocal row
        ws.merge_range(row, 0, row, 2, title, section_fmt)
        ws.set_row(row, 22)
        row += 1

    def kv(key: str, value: str, value_fmt=None, height: int = 38) -> None:
        nonlocal row
        ws.write(row, 0, key, body_bold_fmt)
        ws.merge_range(row, 1, row, 2, value, value_fmt or body_fmt)
        ws.set_row(row, height)
        row += 1

    def example_pair(
        good: str,
        bad: str,
        why_good: str = "",
        why_bad: str = "",
        height: int = 60,
    ) -> None:
        nonlocal row
        # Three-column table header: <Blank> | Example | Why
        ws.write(row, 0, "", header_fmt)
        ws.write(row, 1, "Example", header_fmt)
        ws.write(row, 2, "Why", header_fmt)
        ws.set_row(row, 22)
        row += 1
        ws.write(row, 0, "Good", good_fmt)
        ws.write(row, 1, good, good_fmt)
        ws.write(row, 2, why_good, good_fmt)
        ws.set_row(row, height)
        row += 1
        ws.write(row, 0, "Bad", bad_fmt)
        ws.write(row, 1, bad, bad_fmt)
        ws.write(row, 2, why_bad, bad_fmt)
        ws.set_row(row, height)
        row += 1
        # Spacer
        row += 1

    section("How to use this workbook to format your consultation data for 'Consult'")
    ws.merge_range(
        row,
        0,
        row,
        2,
        "The Responses sheet holds your raw responses. The Demographics, Open "
        "questions, Multiple Choice Questions and Hybrid Questions sheets sit "
        "alongside it and tell Consult how to interpret each column on "
        "Responses — which columns hold demographics, which hold free-text, "
        "which hold multiple-choice, and what each question was actually "
        "asking. Without these sheets, Consult sees an undifferentiated grid "
        "of responses; with them, it can theme the right columns the right way.",
        body_fmt,
    )
    ws.set_row(row, 100)
    row += 1
    kv(
        "1. Paste responses into the Responses Sheet",
        "Replace the dummy data on the Responses tab with your real survey "
        "export. The first row must contain headers (e.g. the question text or demographic name) and the rows below must contain responses from each respondent. Each question or demographic should be in its own column.",
        height=50,
    )
    kv(
        "2. Fill in Demographics, Open, Closed and Hybrid sheets",
        "These four sheets are how you tell Consult to interpret your data. "
        "For each row, type the column LETTER (e.g. A, D, BF) from the "
        "Responses sheet plus the metadata (question text, etc.) so Consult "
        "knows what that column contains.",
        height=80,
    )
    kv(
        "3. Watch Active issues",
        "Every edit re-runs the checks against the data you have provided. Active issues lists everything "
        "currently flagged — fix Errors, review 'To check' items.",
        height=50,
    )
    kv(
        "4. Confirm no errors remain",
        "When Active issues shows zero Errors, the workbook may be ready for "
        " to share with iAI. Some warnings may be false positives, but do check each one and confirm it's intentional.",
        height=38,
    )
    row += 1

    section("Severity — what Errors and 'To check' mean")
    ws.write(row, 0, "Error", error_chip)
    ws.write(
        row,
        1,
        "MUST be fixed before running the consultation. The pipeline cannot "
        "proceed — e.g. a row references a column letter that doesn't exist on "
        "Responses, or a question_number is missing or duplicated.",
        body_fmt,
    )
    ws.set_row(row, 60)
    row += 1
    ws.write(row, 0, "To check", tocheck_chip)
    ws.write(
        row,
        1,
        "Please review each one and decided whether a fix is needed. "
        "For example, there might be a mismatch between the label "
        "that you have provided in the question_text column and the header on the Responses sheet, which causes a 'To check' flag — if you intended those to be different, you can ignore the warning. ",
        body_fmt,
    )
    ws.set_row(row, 80)
    row += 2

    section("What each sheet is for")
    sheets_overview = [
        (
            "Active issues",
            "Live dashboard. Lists every Error and 'To check' item across the "
            "workbook, updated as you edit. Start and end your session here.",
        ),
        (
            "Responses",
            "Your raw survey export. Each "
            "column holds the respondents' responses to one question or one demographic. Row 1 is the "
            "header for each column.",
        ),
        (
            "Demographics",
            "Maps Responses columns that hold demographics (e.g. region, age, "
            "organisation type) to short labels. Used to filter and segment results.",
        ),
        (
            "Open Questions",
            "One row per free-text question. Points at a Responses column whose "
            "responses are free and open text.",
        ),
        (
            "Multiple Choice Questions",
            "One row per multiple-choice question. Points at a Responses column "
            "whose responses come from a fixed list (e.g. Yes/No, Agree/Disagree, …).",
        ),
        (
            "Hybrid Questions",
            "One row per question that has BOTH a multiple-choice part and a "
            "free-text 'why?' part — points at the two Responses columns that hold them.",
        ),
    ]
    for name, desc in sheets_overview:
        kv(name, desc, height=52)
    row += 1

    section("What good question text looks like")
    ws.merge_range(
        row,
        0,
        row,
        2,
        "IMPORTANT: the Question text is the title that Consult — and the AI "
        "model behind it — sees when analysing each response. It is the "
        "model's main signal for what was actually asked. If the question "
        "text is vague, truncated, or missing the framing the respondent "
        "saw, the model will misinterpret responses and the themes it generates "
        "will be off. Treat this column as the prompt you're giving the AI: "
        "give it enough context to understand the question on its own, "
        "without you in the room to explain.",
        body_fmt,
    )
    ws.set_row(row, 110)
    row += 1
    rules = [
        "Reads as a complete, standalone question — the AI model (and any "
        "analyst) should be able to understand what respondents were asked "
        "from this row alone.",
        "Includes the preamble or framing that appeared with the question on "
        "the form (e.g. 'Considering the proposed boundary changes, …'). "
        "Without it, the model loses the topic the question is about.",
        "Matches the wording on the Responses header reasonably closely (the "
        "label-similarity check flags large mismatches as 'To check').",
        "Is a single question with just enough context — not a paragraph of "
        "background. Don't paste in policy notes or explanatory waffle that "
        "wasn't shown to respondents; that adds noise the model has to wade "
        "through.",
        "No leading numbering like 'Q1.' / 'Question 3:' — put the number in "
        "the Question number column instead.",
    ]
    for rule in rules:
        ws.write(row, 0, "•", body_bold_fmt)
        ws.merge_range(row, 1, row, 2, rule, body_fmt)
        ws.set_row(row, 38)
        row += 1
    row += 1

    section("Examples — Open Questions")
    example_pair(
        good="What role would you and/or your organisation play in achieving "
        "the proposed outcomes?",
        why_good="Reads as a full, self-contained question. The AI knows it's "
        "asking about the respondent's role in delivering the proposal — so "
        "it can correctly group responses like 'we'd run training' under a "
        "'role: training provider' theme.",
        bad="role played",
        why_bad="Two words with no context. The model has no idea what role, "
        "in what, or whose. It can't tell whether 'we organised workshops' "
        "is on-topic or not, so themes will be generic and noisy.",
        height=44,
    )
    example_pair(
        good="Considering the proposal in section 3, please explain the most "
        "important factors to achieving the proposed outcomes.",
        why_good="Names the proposal being asked about and the type of "
        "answer expected (factors, not opinions). The model can anchor "
        "themes to 'enablers of the section 3 proposal'.",
        bad="Section 3 — see attached policy paper for the full background "
        "and context, including the previous consultation responses from "
        "2023, the impact assessment, and the equality screening. Free text.",
        why_bad="Mostly background admin that the respondent never saw. The "
        "actual question is buried (or missing). The model wastes its "
        "context budget on irrelevant framing.",
        height=78,
    )

    section("Examples — Multiple Choice Questions")
    example_pair(
        good="To what extent do you agree or disagree that the proposed "
        "councils are the right size to be efficient?",
        why_good="Specifies the dimension being judged (size → efficiency) "
        "and the scale of answer. Free-text rationales attached to it can "
        "be themed against that specific claim.",
        bad="Q3 size",
        why_bad="Just an internal reference. The model doesn't know what "
        "about size was being judged, what the scale was, or which proposal.",
        height=44,
    )

    section("Examples — Hybrid Questions")
    example_pair(
        good="Where do each of the proposed outcomes sit on a scale from very "
        "useful to not useful at all? Please explain your answer.",
        why_good="Captures both halves of the hybrid in one sentence: the "
        "scale (very useful → not useful) and the prompt for free-text "
        "reasoning. The model can connect each rating with its rationale.",
        bad="See attached. (open + closed combined)",
        why_bad="Tells the AI nothing — there's no attached document at "
        "analysis time. Themes will collapse across unrelated outcomes "
        "because the model can't tell them apart.",
        height=60,
    )

    section("Examples — Demographics labels")
    example_pair(
        good="Organisation type",
        why_good="Short, neutral, fits in dashboard filter chips. Analysts "
        "can scan a dropdown of demographics and immediately know what "
        "this one slices by.",
        bad="Q12 — In which of the following capacities are you responding to "
        "this consultation? (please tick one)",
        why_bad="That's the question wording, not a label. It won't fit in "
        "a filter UI and 'Q12' is meaningless to anyone outside the "
        "drafting team.",
        height=44,
    )

    section("Cross-sheet column references")
    ws.merge_range(
        row,
        0,
        row,
        2,
        "Whenever Demographics, Open, Closed or Hybrid asks for a 'column "
        "letter', it always means a column on the Responses sheet. So if "
        "Responses!I1 has the header 'What role would you play?', type 'I' in "
        "the column-letter cell on the relevant Demographics / Open / Closed "
        "/ Hybrid sheet. The workbook automatically pink-fills cells whose "
        "letter doesn't match a populated Responses header.",
        body_fmt,
    )
    ws.set_row(row, 96)
    row += 1

    ws.freeze_panes(1, 0)
    # Lock the Guide so users can't accidentally edit the orientation copy.
    # No password — protection is a soft guard against typos, not a security
    # boundary. Allow selecting cells so links and text can still be copied.
    ws.protect(
        "",
        {
            "select_locked_cells": True,
            "select_unlocked_cells": True,
        },
    )


def main() -> None:
    wb = xlsxwriter.Workbook(str(OUTPUT_PATH))
    fmts = make_formats(wb)

    # Sheet creation order determines tab order.
    ws_guide = wb.add_worksheet(SHEET_GUIDE)
    ws_active = wb.add_worksheet(SHEET_ACTIVE)
    ws_resp = wb.add_worksheet(SHEET_RESPONSES)
    meta_sheets = {m.name: wb.add_worksheet(m.name) for m in METADATA_SHEETS}
    ws_issues = wb.add_worksheet(SHEET_ISSUES)
    ws_helpers = wb.add_worksheet(HELPER_SHEET)

    write_dummy_responses(ws_resp, fmts)
    build_helpers_sheet(ws_helpers)
    build_label_similarity_helpers(ws_helpers)

    for meta in METADATA_SHEETS:
        build_metadata_sheet(meta_sheets[meta.name], meta, fmts)

    last_audit_row = build_issues_sheet(ws_issues, fmts)
    build_active_issues_sheet(ws_active, wb, last_audit_row, fmts)
    build_guide_sheet(ws_guide, wb, fmts)
    ws_issues.hide()
    ws_helpers.hide()
    ws_guide.activate()
    ws_guide.set_first_sheet()

    wb.close()
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
