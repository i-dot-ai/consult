"""Build consult_data_template.xlsx — an opinionated Q.U. workbook skeleton.

Generates a single .xlsx file at the root of the repo with sheets:
Active issues, Responses, Demographics, Open questions, Closed questions,
Hybrid questions, plus a hidden Issues sheet that drives the audit.

Per-sheet checks (cells go pink when the rule is broken AND the violation
is also listed on the Issues sheet with an explanation and fix):
- Required fields must be populated whenever the row contains any data.
- Column-ID cells must look like Excel column letters (1-3 uppercase A-Z).
- Question-number cells must be whole numbers >= 1 (also integer-formatted).

Cross-sheet checks (mirror the validations in setup_consultation.py):
- Column letters referenced by Q.U. rows must match a populated Responses
  column header.
- No duplicate column references across the four Q.U. sheets.
- question_number values must be globally unique across Open/Closed/Hybrid.
- Total Q.U. column count must not exceed Responses column count - 1.
- Closed-side columns should have ≤20% unique values (else: looks like free text).
- Open-side columns should have >20% unique values (else: looks multichoice).
- Every Responses column should be referenced by Q.U. or Demographics.
- Every Responses column with data must have a header in row 1.
- Q.U. sheets are locked to their defined column count: Demographics A–B,
  Open/Closed A–C, Hybrid A–D. Off-limit columns reject input via data
  validation and pink-fill anything pasted in.

- Q.U. question_text should be similar to its Responses header. Implemented
  as character-4-gram Jaccard similarity. The intersection size is one
  SUMPRODUCT over MID(a, SEQUENCE(na), 4) — no LAMBDA / LET / REDUCE
  (this Excel build doesn't support them; see label_similarity_debugging.md).
  Inputs are truncated to LABEL_MAX_LEN chars to keep recompute fast.
  Approximation of setup_consultation.py's SequenceMatcher ratio —
  threshold tuned independently.

One check from setup_consultation.py is deliberately not implemented here:
integer extraction from question text. It needs regex which Excel lacks.

The Responses sheet is pre-populated with dummy data so the checks can be
exercised end-to-end by filling in the Q.U. sheets.

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
  When using any of these, write the cell with
  `worksheet.write_dynamic_array_formula` (not `write_formula`) so
  xlsxwriter emits the array tag and the workbook's metadata part —
  otherwise Excel flags the file as malformed.

Default to scalar formulas. Reach for the four supported dynamic-array
functions only when there's no clean scalar alternative.

Run:
    uv run python build_consult_data_template.py
"""

import random
from pathlib import Path

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

OUTPUT_PATH = Path(__file__).resolve().parent / "consult_data_template.xlsx"

DATA_ROWS = 100000  # rows pre-wired with checks on each Q.U. sheet
RESPONSE_DATA_LAST_ROW = 2000  # upper bound for response rows used in uniqueness helpers
QU_RANGE_LAST_ROW = 1001  # upper bound for cross-Q.U. COUNTIF ranges (duplicate checks)
UNIQUENESS_THRESHOLD = 0.2  # mirrors setup_consultation.UNIQUENESS_RATIO_THRESHOLD
def _column_letters_up_to(last: str) -> list[str]:
    """All Excel column letters from A through `last`, inclusive (1-2 letters)."""
    out = [chr(ord("A") + i) for i in range(26)]
    if len(last) == 1:
        return out[: ord(last) - ord("A") + 1]
    out += [a + b for a in out[:26] for b in out[:26]]  # AA..ZZ
    end_idx = 26 + (ord(last[0]) - ord("A")) * 26 + (ord(last[1]) - ord("A")) + 1
    return out[:end_idx]


RESPONSE_LETTERS = _column_letters_up_to("ZZ")  # A..ZZ audited as response cols
RESPONSE_LAST_LETTER = "ZZ"  # last column the audit covers
# Hidden helper sheet holding per-column uniqueness ratios and counts.
# Lives on its own sheet so a user can't accidentally overwrite the formulas
# while editing Responses. Keeps the per-row uniqueness checks O(1) lookups
# instead of O(n²) volatile re-computes.
HELPER_SHEET = "_helpers"
HELPER_RATIO_ROW = 1  # Excel row 1 of the helper sheet
HELPER_COUNT_ROW = 2  # Excel row 2 of the helper sheet

# Label-similarity helper layout: one BLOCK per (Q.U. sheet, letter-field),
# each block is LABEL_SIM_FIELDS columns wide so every intermediate step
# lives in its own cell (debuggable by inspection).
#
# Per-row layout within a block:
#   L      | column letter from the Q.U. sheet
#   H      | Responses header at that column
#   a      | LOWER(TRIM(LEFT(Q,150))) of the Q.U. question_text
#   b      | LOWER(TRIM(LEFT(H,150))) of the Responses header
#   na     | LEN(a) - 3   (number of 4-grams in a)
#   nb     | LEN(b) - 3   (number of 4-grams in b)
#   inter  | size of trigram intersection (computed inline)
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
    ("Open questions", "A"),
    ("Closed questions", "A"),
    ("Hybrid questions", "A"),
    ("Hybrid questions", "D"),
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


def _sim_block_col(sheet: str, letter_field: str, field: str) -> str:
    """Excel column letter (e.g. 'C', 'AA') for a field within the block for (sheet, letter_field)."""
    block_idx = LABEL_SIM_BLOCKS.index((sheet, letter_field))
    field_idx = LABEL_SIM_FIELDS.index(field)
    return _idx_to_letter(block_idx * LABEL_SIM_BLOCK_WIDTH + field_idx)

ISSUE_BG = "#FCE4D6"  # warning amber
ERROR_BG = "#F4B6B6"  # error red
HEADER_BG = "#D9E1F2"

SEVERITY_BY_VKIND = {
    "required": "Error",
    "column_id": "Error",
    "integer": "Error",
    "missing_response": "Error",
    "duplicate_column": "Warning",
    "duplicate_qnum": "Error",
    "closed_uniqueness": "Warning",
    "open_uniqueness": "Warning",
    "label_similarity": "Warning",
}
SEVERITY_WORKBOOK_COUNT = "Error"
SEVERITY_MISSING_HEADER = "Error"
SEVERITY_UNREFERENCED = "Warning"


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
        "warning_fill": wb.add_format({"bg_color": ISSUE_BG}),
        "error_fill": wb.add_format({"bg_color": ERROR_BG}),
        "error_count": wb.add_format({"bold": True, "font_size": 14, "font_color": "#C00000"}),
        "warning_count": wb.add_format({"bold": True, "font_size": 14, "font_color": "#B25E00"}),
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
    col_idx = _col_letter_to_idx(col_letter)
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
                f"${col_letter}2<>INT(${col_letter}2),"
                f"${col_letter}2<1))"
            ),
            "format": fmts["issue_fill"],
        },
    )


def _col_letter_to_idx(letter: str) -> int:
    n = 0
    for ch in letter:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def _column_id_valid(cell_ref: str) -> str:
    """Excel formula returning TRUE when `cell_ref` looks like an Excel column ID."""
    pad = f'TRIM({cell_ref})&"AAA"'
    chars = ",".join(
        f"AND(CODE(MID({pad},{i},1))>=65,CODE(MID({pad},{i},1))<=90)"
        for i in (1, 2, 3)
    )
    return (
        f"AND("
        f"LEN(TRIM({cell_ref}))>=1,"
        f"LEN(TRIM({cell_ref}))<=3,"
        f"{chars})"
    )


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
                f'=AND(${col_letter}2<>"",'
                f"NOT({_column_id_valid(f'${col_letter}2')}))"
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
    return (
        f'AND({target}<>"",'
        f'IFERROR(INDEX(Responses!$A$1:$XFD$1,1,{col_num}),"")="")'
    )


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

    The expensive O(n²) SUMPRODUCT/COUNTIF runs once per Responses column instead
    of once per Q.U. audit row, and depends only on Responses cells — so editing
    Q.U. sheets doesn't trigger recompute. INDIRECT is dropped, so these aren't
    volatile either. Lives on its own sheet so users can't overwrite it while
    editing Responses.
    """
    for col_idx, letter in enumerate(RESPONSE_LETTERS):
        src = f"Responses!{letter}2:{letter}{RESPONSE_DATA_LAST_ROW}"
        ratio = (
            f'=IFERROR(SUMPRODUCT(({src}<>"")/COUNTIF({src},{src}&""))'
            f"/COUNTA({src}),0)"
        )
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
        f"SUMPRODUCT(--ISNUMBER(SEARCH("
        f"MID({a_cell},SEQUENCE({na_cell}),4),{b_cell})))"
    )


def build_label_similarity_helpers(ws) -> None:
    """Per-Q.U.-row 4-gram Jaccard similarity, exploded across LABEL_SIM_FIELDS columns.

    Each block (one per Q.U. sheet/letter-field) holds 8 columns: L, H, a, b,
    na, nb, inter, sim. The exploded layout keeps each cell single-purpose
    and inspectable on the (hidden) `_helpers` sheet. The Issues sheet reads
    only the `sim` column.
    """
    qtext_field = "C"  # question_text column on every Q.U. sheet
    for sheet, letter_field in LABEL_SIM_BLOCKS:
        cols = {f: _sim_block_col(sheet, letter_field, f) for f in LABEL_SIM_FIELDS}
        for f in LABEL_SIM_FIELDS:
            ws.write(
                HELPER_SIM_START_ROW - 2,
                _col_idx(cols[f]),
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

            ws.write_formula(helper_row - 1, _col_idx(cols["L"]), f"={qu_letter}")
            ws.write_formula(
                helper_row - 1,
                _col_idx(cols["H"]),
                f'=IFERROR(INDEX(Responses!$1:$1,1,{_letter_to_col_num(L_cell)}),"")',
            )
            ws.write_formula(
                helper_row - 1,
                _col_idx(cols["a"]),
                f"=LOWER(TRIM(LEFT({qu_qtext},{LABEL_MAX_LEN})))",
            )
            ws.write_formula(
                helper_row - 1,
                _col_idx(cols["b"]),
                f"=LOWER(TRIM(LEFT({H_cell},{LABEL_MAX_LEN})))",
            )
            ws.write_formula(
                helper_row - 1, _col_idx(cols["na"]), f"=MAX(LEN({a_cell})-3,0)"
            )
            ws.write_formula(
                helper_row - 1, _col_idx(cols["nb"]), f"=MAX(LEN({b_cell})-3,0)"
            )
            inter_body = _inter_formula(a_cell, b_cell, na_cell)
            inter_col = _col_idx(cols["inter"])
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
                _col_idx(cols["sim"]),
                f'=IF(OR({L_cell}="",{a_cell}="",{b_cell}="",'
                f'{na_cell}<=0,{nb_cell}<=0),"",'
                f"{inter_cell}/({na_cell}+{nb_cell}-{inter_cell}))",
            )


def _col_idx(letter: str) -> int:
    """Excel column letter to 0-based index (A=0, Z=25, AA=26)."""
    n = 0
    for ch in letter:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def write_data_rows(ws, rows: list[tuple]) -> None:
    """Write tuples of values starting at row 2 (0-indexed: row 1)."""
    for r, values in enumerate(rows, start=1):
        for c, v in enumerate(values):
            ws.write(r, c, v)


# --- Issues sheet (live audit log) ---

AUDIT_WINDOW = 50  # source rows audited per Q.U. sheet


def _qu_cell(sheet: str, col: str, r: int) -> str:
    return f"'{sheet}'!${col}${r}"


def _violation_required(sheet: str, all_cols: list[str], col: str, r: int) -> str:
    target = _qu_cell(sheet, col, r)
    siblings = [c for c in all_cols if c != col]
    sibling_check = "OR(" + ",".join(f'{_qu_cell(sheet, c, r)}<>""' for c in siblings) + ")"
    return f'AND({target}="",{sibling_check})'


def _violation_column_id(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    target = _qu_cell(sheet, col, r)
    return f'AND({target}<>"",NOT({_column_id_valid(target)}))'


def _violation_integer(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    target = _qu_cell(sheet, col, r)
    return (
        f'AND({target}<>"",'
        f"OR(NOT(ISNUMBER({target})),"
        f"{target}<>INT({target}),"
        f"{target}<1))"
    )


def _violation_missing_response(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    return _missing_response_formula(_qu_cell(sheet, col, r))


def _qu_col_ranges() -> list[str]:
    """Ranges holding column-letter references across Open/Closed/Hybrid sheets.

    Bounded at QU_RANGE_LAST_ROW (~1000) rather than DATA_ROWS (100k); COUNTIF cost
    is linear in range size and rows beyond row ~1000 won't be audited anyway.
    """
    last = QU_RANGE_LAST_ROW
    return [
        f"'Open questions'!$A$2:$A${last}",
        f"'Closed questions'!$A$2:$A${last}",
        f"'Hybrid questions'!$A$2:$A${last}",
        f"'Hybrid questions'!$D$2:$D${last}",
    ]


def _qu_qnum_ranges() -> list[str]:
    """Ranges holding question_number values across Open/Closed/Hybrid sheets."""
    last = QU_RANGE_LAST_ROW
    return [
        f"'Open questions'!$B$2:$B${last}",
        f"'Closed questions'!$B$2:$B${last}",
        f"'Hybrid questions'!$B$2:$B${last}",
    ]


def _all_referenced_col_ranges() -> list[str]:
    """Q.U. column ranges plus Demographics — used by 'unreferenced response' check."""
    last = QU_RANGE_LAST_ROW
    return _qu_col_ranges() + [f"'Demographics'!$A$2:$A${last}"]


def _violation_duplicate_column(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    target = _qu_cell(sheet, col, r)
    counts = "+".join(f"COUNTIF({rng},{target})" for rng in _qu_col_ranges())
    return f'AND({target}<>"",({counts})>1)'


def _violation_duplicate_qnum(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
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
    return (
        f'AND({target}<>"",'
        f"{count}>0,"
        f"{ratio}{op}{UNIQUENESS_THRESHOLD})"
    )


def _violation_closed_uniqueness(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    return _uniqueness_violation(_qu_cell(sheet, col, r), op=">")


def _violation_open_uniqueness(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    return _uniqueness_violation(_qu_cell(sheet, col, r), op="<")


def _violation_label_similarity(sheet: str, _all_cols: list[str], col: str, r: int) -> str:
    """Read the precomputed similarity from _helpers; fire when below threshold."""
    sim_col = _sim_block_col(sheet, col, "sim")
    helper_row = HELPER_SIM_START_ROW + (r - 2)
    helper_cell = f"{HELPER_SHEET}!${sim_col}${helper_row}"
    return (
        f"AND(ISNUMBER({helper_cell}),"
        f"{helper_cell}<{LABEL_SIMILARITY_THRESHOLD})"
    )


VIOLATION_FNS = {
    "required": _violation_required,
    "column_id": _violation_column_id,
    "integer": _violation_integer,
    "missing_response": _violation_missing_response,
    "duplicate_column": _violation_duplicate_column,
    "duplicate_qnum": _violation_duplicate_qnum,
    "closed_uniqueness": _violation_closed_uniqueness,
    "open_uniqueness": _violation_open_uniqueness,
    "label_similarity": _violation_label_similarity,
}


QU_AUDIT_SCHEMA: dict[str, dict] = {
    "Demographics": {
        "cols": ["A", "B"],
        "rules": [
            ("A", "Missing column ID", "required",
             "This row has a label but no column letter, so Themefinder won't know which column on the Responses sheet to read.",
             "Type the Excel column letter (e.g. B, AC) from the Responses sheet that holds this demographic."),
            ("B", "Missing label", "required",
             "This row has a column letter but no label, so this demographic will be unnamed in your results.",
             "Type a short, human-readable name for this demographic, e.g. 'Region' or 'Age group'."),
            ("A", "Invalid column ID format", "column_id",
             "'{value}' isn't a valid Excel column letter, so Themefinder can't find this column on the Responses sheet.",
             "Use 1-3 capital letters only — A, B, …, Z, AA, AB, …, ZZZ. No numbers or symbols."),
            ("A", "Column not in Responses", "missing_response",
             "Column '{value}' has no header on the Responses sheet, so there's nothing for Themefinder to read.",
             "Check for a typo in the column letter, or add a header (and the answers) into that column on Responses."),
        ],
    },
    "Open questions": {
        "cols": ["A", "B", "C"],
        "rules": [
            ("A", "Missing column_name", "required",
             "This row has question details but no column letter, so Themefinder won't know where the free-text answers live.",
             "Type the Excel column letter from the Responses sheet that holds the free-text answers for this question."),
            ("B", "Missing question_number", "required",
             "This row has no question number. Numbers identify each question in your results and are used as output folder names.",
             "Enter a whole number 1 or higher. Each number must be unique across the Open, Closed, and Hybrid sheets."),
            ("C", "Missing question_text", "required",
             "This row has no question wording, which will make the results hard to interpret.",
             "Paste the full question exactly as it appeared to respondents."),
            ("A", "Invalid column ID format", "column_id",
             "'{value}' isn't a valid Excel column letter, so Themefinder can't find this column on the Responses sheet.",
             "Use 1-3 capital letters only (e.g. A, BF, AAC). No numbers or symbols."),
            ("B", "Question number must be a whole integer >= 1", "integer",
             "'{value}' isn't a whole number of 1 or more. Question numbers are used as output folder names, so they need to be plain whole numbers.",
             "Replace it with a whole number such as 1, 2, 3. Decimals, text, and 0 aren't allowed."),
            ("A", "Column not in Responses", "missing_response",
             "Column '{value}' has no header on the Responses sheet, so there are no answers for Themefinder to analyse.",
             "Double-check the column letter for typos, or paste the answers (with a header in row 1) into that column on Responses."),
            ("A", "Duplicate column reference", "duplicate_column",
             "Column '{value}' is already used by another row. Each Excel column should feed only one question.",
             "Pick a different column letter, or remove the duplicate row from the Open / Closed / Hybrid sheets."),
            ("B", "Duplicate question_number", "duplicate_qnum",
             "Question number '{value}' is already used by another row. Numbers must be unique because they're used as output folder names.",
             "Renumber one of the rows so every question across Open, Closed, and Hybrid has its own unique number."),
            ("A", "Open column looks multichoice", "open_uniqueness",
             "Column '{value}' has very few different answers (≤20% are unique). That usually means it's a multiple-choice question rather than free text.",
             "If respondents picked from a list, move this row to the Closed questions sheet. If it really is free text, you can ignore this warning."),
            ("A", "question_text differs from Responses header", "label_similarity",
             "The question wording on this row doesn't closely match the header in column '{value}' on Responses, so the wrong column may have been chosen.",
             "Check the column letter is correct, or update the question wording so it matches the header on the Responses sheet."),
        ],
    },
    "Closed questions": {
        "cols": ["A", "B", "C"],
        "rules": [
            ("A", "Missing column_name", "required",
             "This row has question details but no column letter, so Themefinder won't know where the multiple-choice answers live.",
             "Type the Excel column letter from the Responses sheet that holds the multiple-choice answers for this question."),
            ("B", "Missing question_number", "required",
             "This row has no question number. Numbers identify each question in your results and are used as output folder names.",
             "Enter a whole number 1 or higher. Each number must be unique across the Open, Closed, and Hybrid sheets."),
            ("C", "Missing question_text", "required",
             "This row has no question wording, which will make the results hard to interpret.",
             "Paste the full question exactly as it appeared to respondents."),
            ("A", "Invalid column ID format", "column_id",
             "'{value}' isn't a valid Excel column letter, so Themefinder can't find this column on the Responses sheet.",
             "Use 1-3 capital letters only (e.g. A, BF, AAC). No numbers or symbols."),
            ("B", "Question number must be a whole integer >= 1", "integer",
             "'{value}' isn't a whole number of 1 or more. Question numbers are used as output folder names, so they need to be plain whole numbers.",
             "Replace it with a whole number such as 1, 2, 3. Decimals, text, and 0 aren't allowed."),
            ("A", "Column not in Responses", "missing_response",
             "Column '{value}' has no header on the Responses sheet, so there are no answers for Themefinder to analyse.",
             "Double-check the column letter for typos, or paste the answers (with a header in row 1) into that column on Responses."),
            ("A", "Duplicate column reference", "duplicate_column",
             "Column '{value}' is already used by another row. Each Excel column should feed only one question.",
             "Pick a different column letter, or remove the duplicate row from the Open / Closed / Hybrid sheets."),
            ("B", "Duplicate question_number", "duplicate_qnum",
             "Question number '{value}' is already used by another row. Numbers must be unique because they're used as output folder names.",
             "Renumber one of the rows so every question across Open, Closed, and Hybrid has its own unique number."),
            ("A", "Closed column looks like free text", "closed_uniqueness",
             "Column '{value}' has lots of different answers (>20% are unique). That usually means it's a free-text question rather than multiple choice.",
             "If respondents typed their own answers, move this row to the Open questions sheet. If it really is multiple choice, you can ignore this warning."),
            ("A", "question_text differs from Responses header", "label_similarity",
             "The question wording on this row doesn't closely match the header in column '{value}' on Responses, so the wrong column may have been chosen.",
             "Check the column letter is correct, or update the question wording so it matches the header on the Responses sheet."),
        ],
    },
    "Hybrid questions": {
        "cols": ["A", "B", "C", "D"],
        "rules": [
            ("A", "Missing open_column", "required",
             "This row has question details but no column letter for the free-text part, so Themefinder won't know where those answers live.",
             "Type the Excel column letter from Responses that holds the free-text part of this hybrid question."),
            ("B", "Missing question_number", "required",
             "This row has no question number. Numbers identify each question in your results and are used as output folder names.",
             "Enter a whole number 1 or higher. Each number must be unique across the Open, Closed, and Hybrid sheets."),
            ("C", "Missing question_text", "required",
             "This row has no question wording, which will make the results hard to interpret.",
             "Paste the full question exactly as it appeared to respondents."),
            ("D", "Missing closed_column", "required",
             "This row has no column letter for the multiple-choice part, so Themefinder won't know where those answers live.",
             "Type the Excel column letter from Responses that holds the multiple-choice part of this hybrid question."),
            ("A", "Invalid open_column format", "column_id",
             "'{value}' isn't a valid Excel column letter, so Themefinder can't find the free-text column on Responses.",
             "Use 1-3 capital letters only (e.g. A, BF, AAC). No numbers or symbols."),
            ("D", "Invalid closed_column format", "column_id",
             "'{value}' isn't a valid Excel column letter, so Themefinder can't find the multiple-choice column on Responses.",
             "Use 1-3 capital letters only (e.g. A, BF, AAC). No numbers or symbols."),
            ("B", "Question number must be a whole integer >= 1", "integer",
             "'{value}' isn't a whole number of 1 or more. Question numbers are used as output folder names, so they need to be plain whole numbers.",
             "Replace it with a whole number such as 1, 2, 3. Decimals, text, and 0 aren't allowed."),
            ("A", "open_column not in Responses", "missing_response",
             "Column '{value}' has no header on the Responses sheet, so there are no free-text answers to analyse.",
             "Double-check the column letter for typos, or paste the answers (with a header in row 1) into that column on Responses."),
            ("D", "closed_column not in Responses", "missing_response",
             "Column '{value}' has no header on the Responses sheet, so there are no multiple-choice answers to analyse.",
             "Double-check the column letter for typos, or paste the answers (with a header in row 1) into that column on Responses."),
            ("A", "Duplicate column reference", "duplicate_column",
             "Column '{value}' is already used by another row. Each Excel column should feed only one question.",
             "Pick a different column letter, or remove the duplicate row from the Open / Closed / Hybrid sheets."),
            ("D", "Duplicate column reference", "duplicate_column",
             "Column '{value}' is already used by another row. Each Excel column should feed only one question.",
             "Pick a different column letter, or remove the duplicate row from the Open / Closed / Hybrid sheets."),
            ("B", "Duplicate question_number", "duplicate_qnum",
             "Question number '{value}' is already used by another row. Numbers must be unique because they're used as output folder names.",
             "Renumber one of the rows so every question across Open, Closed, and Hybrid has its own unique number."),
            ("A", "Open column looks multichoice", "open_uniqueness",
             "Column '{value}' has very few different answers (≤20% are unique), which looks more like multiple choice than free text.",
             "If respondents picked from a list, this column belongs in the Closed questions sheet (or as the closed_column of a hybrid). If it really is free text, you can ignore this warning."),
            ("D", "Closed column looks like free text", "closed_uniqueness",
             "Column '{value}' has lots of different answers (>20% are unique), which looks more like free text than multiple choice.",
             "If respondents typed their own answers, this column belongs in the Open questions sheet (or as the open_column of a hybrid). If it really is multiple choice, you can ignore this warning."),
            ("A", "question_text differs from open_column header", "label_similarity",
             "The question wording doesn't closely match the header for column '{value}' on Responses, so the wrong free-text column may have been chosen.",
             "Check the open_column letter is correct, or update the question wording so it matches the Responses header."),
            ("D", "question_text differs from closed_column header", "label_similarity",
             "The question wording doesn't closely match the header for column '{value}' on Responses, so the wrong multiple-choice column may have been chosen.",
             "Check the closed_column letter is correct, or update the question wording so it matches the Responses header."),
        ],
    },
}


def _issue_text_formula(target: str, msg_tmpl: str) -> str:
    """Build an Excel string expression for the issue message, substituting {value}."""
    if "{value}" not in msg_tmpl:
        return '"' + msg_tmpl.replace('"', '""') + '"'
    parts = msg_tmpl.split("{value}")
    pieces: list[str] = []
    for i, part in enumerate(parts):
        if part:
            pieces.append('"' + part.replace('"', '""') + '"')
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
    header = f'INDIRECT("Responses!"&{target}&"1")'
    return (
        f'"The question wording below doesn'"'"'t closely match the '
        f'Responses header for column "&{target}&"."'
        f'&CHAR(10)&CHAR(10)'
        f'&"Question text:"&CHAR(10)&{qtext}'
        f'&CHAR(10)&CHAR(10)'
        f'&"Responses header for column "&{target}&":"&CHAR(10)&{header}'
    )


def _workbook_level_rule_rows() -> list[dict]:
    """Rules that aren't tied to a single Q.U. row.

    Currently: total distinct Q.U. column count vs Responses column count.
    Uses VSTACK/UNIQUE/FILTER (Excel 365 / 2021+); pre-365 Excel will show a
    #NAME? in the Issue cell, which is harmless — the count check just won't fire.
    """
    vstack_args = ",".join(_qu_col_ranges())
    distinct_count = (
        f'IFERROR(ROWS(UNIQUE(FILTER(VSTACK({vstack_args}),'
        f'VSTACK({vstack_args})<>""))),0)'
    )
    resp_count = "COUNTA(Responses!$1:$1)-1"
    violation = f"({distinct_count})>({resp_count})"
    msg = (
        f'"Your question setup points at "&{distinct_count}&" different column(s), '
        f'but Responses only has "&({resp_count})&" column(s) of data — '
        f'some of the columns you have referenced don\'t exist."'
    )
    fix_text = (
        "Either remove the questions / demographics that point to columns "
        "that aren't in Responses, or add the missing columns (with headers "
        "and answers) to the Responses sheet."
    )
    return [{
        "sheet": "(workbook)",
        "cell": "-",
        "rule": "Q.U. column count exceeds Responses",
        "severity": SEVERITY_WORKBOOK_COUNT,
        "issue_formula": f'=IF({violation},{msg},"")',
        "fix": fix_text,
    }]


def _missing_header_rule_rows() -> list[dict]:
    """One row per A..Z that fires when a Responses column has data but no header."""
    rows: list[dict] = []
    for letter in RESPONSE_LETTERS:
        header = f"Responses!${letter}$1"
        data_range = f"Responses!${letter}$2:${letter}${RESPONSE_DATA_LAST_ROW}"
        violation = f'AND({header}="",COUNTA({data_range})>0)'
        msg = (
            f'"Column {letter} on Responses has answers but no header in row 1, '
            f'so nobody (and Themefinder) knows what this column is."'
        )
        fix_text = (
            f"Type a short header in Responses!{letter}1 describing what this "
            "column contains (e.g. the question or demographic name), or "
            "delete the data in that column if it isn't needed."
        )
        rows.append({
            "sheet": "Responses",
            "cell": f"{letter}1",
            "rule": "Missing header",
            "severity": SEVERITY_MISSING_HEADER,
            "issue_formula": f'=IF({violation},{msg},"")',
            "fix": fix_text,
        })
    return rows


def _unreferenced_response_rule_rows() -> list[dict]:
    """One row per A..Z asking whether that Responses column is referenced.

    Fires when Responses!<L>1 is non-empty, isn't a "Response ID"-style header,
    and no Q.U. or Demographics row references letter L.
    """
    ref_ranges = _all_referenced_col_ranges()
    rows: list[dict] = []
    for letter in RESPONSE_LETTERS:
        header = f"Responses!${letter}$1"
        # COUNTIF with literal letter — note doubled "" for embedding in string.
        ref_count = "+".join(
            f'COUNTIF({rng},"{letter}")' for rng in ref_ranges
        )
        violation = (
            f'AND({header}<>"",'
            f'ISERROR(SEARCH("response id",LOWER({header}))),'
            f"({ref_count})=0)"
        )
        msg = (
            f'"Responses column {letter} ("""&{header}&""") has data, but no '
            f'question or demographic is set up to use it — so it won\'t appear '
            f'in your results."'
        )
        fix_text = (
            f"If you want this column analysed, add a row pointing to "
            f"column {letter} on the Open, Closed, Hybrid, or Demographics "
            "sheet. If it isn't needed, delete the column on Responses."
        )
        rows.append({
            "sheet": "Responses",
            "cell": f"{letter}1",
            "rule": "Unreferenced response column",
            "severity": SEVERITY_UNREFERENCED,
            "issue_formula": f'=IF({violation},{msg},"")',
            "fix": fix_text,
        })
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
            for target_col, label, vkind, msg_tmpl, fix_text in schema["rules"]:
                target = _qu_cell(sheet_name, target_col, r)
                violation = VIOLATION_FNS[vkind](sheet_name, cols, target_col, r)
                if vkind == "label_similarity":
                    msg_expr = _label_similarity_msg_formula(sheet_name, target, r)
                else:
                    msg_expr = _issue_text_formula(target, msg_tmpl)
                rows.append({
                    "sheet": sheet_name,
                    "cell": f"{target_col}{r}",
                    "rule": label,
                    "severity": SEVERITY_BY_VKIND[vkind],
                    "issue_formula": f'=IF({violation},{msg_expr},"")',
                    "fix": fix_text,
                })

    rows.extend(_workbook_level_rule_rows())
    rows.extend(_missing_header_rule_rows())
    rows.extend(_unreferenced_response_rule_rows())

    # Sort: severity (Error before Warning before everything else) then rule label.
    severity_rank = {"Error": 0, "Warning": 1}
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


def build_active_issues_sheet(ws, source_last_row: int, fmts: dict) -> None:
    """Live view of Issues filtered to non-empty Issue cells, via FILTER().

    Dynamic-array FILTER recalculates with the source formulas, so this sheet
    auto-updates whenever a new violation fires — no manual reapply needed.
    Separate Errors and Warnings counts at the top; severity column is colour-coded.
    """
    widths = [18, 10, 34, 12, 70, 60]
    for i, w in enumerate(widths):
        fmt = fmts["wrap"] if i in (4, 5) else None
        ws.set_column(i, i, w, fmt)

    ws.merge_range("A1:F1", "Active issues", fmts["title"])

    err_count = (
        f'=SUMPRODUCT((Issues!E5:E{source_last_row}<>"")*'
        f'(Issues!D5:D{source_last_row}="Error"))'
    )
    warn_count = (
        f'=SUMPRODUCT((Issues!E5:E{source_last_row}<>"")*'
        f'(Issues!D5:D{source_last_row}="Warning"))'
    )
    ws.write("A2", "Errors:", fmts["bold_right"])
    ws.write_formula("B2", err_count, fmts["error_count"])
    ws.write("C2", "Warnings:", fmts["bold_right"])
    ws.write_formula("D2", warn_count, fmts["warning_count"])

    ws.merge_range(
        "A3:F3",
        "Errors must be fixed before running the consultation. Warnings are "
        "heuristic — review and override if intentional. Updates automatically "
        "as you edit the Q.U. sheets.",
        fmts["italic_wrap"],
    )
    ws.set_row(2, 30)

    for i, h in enumerate(["Sheet", "Cell", "Rule", "Severity", "Issue", "How to fix"]):
        ws.write(3, i, h, fmts["header"])

    formula = (
        f'=FILTER(Issues!A5:F{source_last_row},'
        f'Issues!E5:E{source_last_row}<>"",'
        f'"No outstanding issues — fill in the Q.U. sheets to begin.")'
    )
    ws.write_dynamic_array_formula("A5", formula)

    # Set generous row heights so wrapped Issue / How-to-fix text shows in full.
    # FILTER spill order isn't known at build time, so use a uniform tall height
    # across all data rows; label_similarity messages need ~7 lines.
    for excel_row_idx in range(4, source_last_row):  # 0-indexed; Excel rows 5..source_last_row
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
        {"type": "formula", "criteria": '=$D5="Warning"', "format": fmts["warning_fill"]},
    )
    ws.freeze_panes(4, 0)


def main() -> None:
    wb = xlsxwriter.Workbook(str(OUTPUT_PATH))
    fmts = make_formats(wb)

    # Sheet creation order determines tab order.
    ws_active = wb.add_worksheet("Active issues")
    ws_resp = wb.add_worksheet("Responses")
    ws_demo = wb.add_worksheet("Demographics")
    ws_open = wb.add_worksheet("Open questions")
    ws_closed = wb.add_worksheet("Closed questions")
    ws_hyb = wb.add_worksheet("Hybrid questions")
    ws_issues = wb.add_worksheet("Issues")
    ws_helpers = wb.add_worksheet(HELPER_SHEET)

    write_dummy_responses(ws_resp, fmts)
    build_helpers_sheet(ws_helpers)
    build_label_similarity_helpers(ws_helpers)

    write_headers(ws_demo, ["column_id", "label"], [12, 36], fmts["header"])
    add_required_field_checks(ws_demo, ["A", "B"], fmts)
    add_column_id_check(ws_demo, "A", fmts)
    highlight_missing_response_column(ws_demo, "A", fmts)
    add_offlimit_columns_check(ws_demo, "C", "Demographics", fmts)
    write_data_rows(
        ws_demo,
        [
            ("B", "Region"),
            ("C", "Age band"),
            ("D", "Organisation type"),
        ],
    )

    write_headers(
        ws_open,
        ["column_name", "question_number", "question_text"],
        [14, 18, 70],
        fmts["header"],
    )
    add_required_field_checks(ws_open, ["A", "B", "C"], fmts)
    add_column_id_check(ws_open, "A", fmts)
    add_integer_check(ws_open, "B", fmts)
    highlight_missing_response_column(ws_open, "A", fmts)
    add_offlimit_columns_check(ws_open, "D", "Open questions", fmts)
    write_data_rows(
        ws_open,
        [("I", 3, "Do you have any other suggestions or comments?")],
    )

    write_headers(
        ws_closed,
        ["column_name", "question_number", "question_text"],
        [14, 18, 70],
        fmts["header"],
    )
    add_required_field_checks(ws_closed, ["A", "B", "C"], fmts)
    add_column_id_check(ws_closed, "A", fmts)
    add_integer_check(ws_closed, "B", fmts)
    highlight_missing_response_column(ws_closed, "A", fmts)
    add_offlimit_columns_check(ws_closed, "D", "Closed questions", fmts)
    write_data_rows(
        ws_closed,
        [("J", 4, "Would you recommend this approach to others?")],
    )

    write_headers(
        ws_hyb,
        ["open_column", "question_number", "question_text", "closed_column"],
        [14, 18, 70, 14],
        fmts["header"],
    )
    add_required_field_checks(ws_hyb, ["A", "B", "C", "D"], fmts)
    add_column_id_check(ws_hyb, "A", fmts)
    add_column_id_check(ws_hyb, "D", fmts)
    add_integer_check(ws_hyb, "B", fmts)
    highlight_missing_response_column(ws_hyb, "A", fmts)
    highlight_missing_response_column(ws_hyb, "D", fmts)
    add_offlimit_columns_check(ws_hyb, "E", "Hybrid questions", fmts)
    write_data_rows(
        ws_hyb,
        [
            ("F", 1, "What is your level of support for the proposal, and why?", "E"),
            ("H", 2, "How important is this issue, and please explain.", "G"),
        ],
    )

    last_audit_row = build_issues_sheet(ws_issues, fmts)
    build_active_issues_sheet(ws_active, last_audit_row, fmts)
    ws_issues.hide()
    ws_helpers.hide()
    ws_active.activate()
    ws_active.set_first_sheet()

    wb.close()
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
