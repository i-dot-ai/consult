"""Convert a filled consult_data_template workbook to a Citizen Space style CSV.

Lets data prepared in the Q.U. template go through the Citizen Space survey
import without being re-keyed. Question wording comes from the mapping
sheets so the importer sees the full question, not the abbreviated export
header. Nothing is added beyond that: no ID, notes or metadata columns.

Usage:
    uv run python convert_template_to_citizen_space.py [template.xlsx] [out.csv]
"""

import argparse
import csv
import sys
from pathlib import Path

import openpyxl
from openpyxl.utils import column_index_from_string

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE / "consult_data_template_v005.xlsx"

# Citizen Space's own wording, so the two halves of a hybrid stay distinct.
HYBRID_CLOSED_SUFFIX = " - Please select one answer"
HYBRID_OPEN_SUFFIX = " - Please explain below"


def _rows(ws) -> list[tuple]:
    """Mapping-sheet rows below the header, skipping blank ones."""
    return [r for r in ws.iter_rows(min_row=2, values_only=True) if r and r[0]]


def _col_index(letter: str, headers: list, sheet: str) -> int:
    """Zero-based Responses index for a column letter, failing loudly if unusable."""
    letter = str(letter).strip().upper()
    idx = column_index_from_string(letter) - 1
    if idx >= len(headers) or not headers[idx]:
        raise ValueError(f"{sheet}: column '{letter}' has no header on the Responses sheet")
    return idx


def build_columns(wb) -> list[tuple[int, str]]:
    """Return (Responses column index, output header) for every mapped column.

    Raises ValueError if a column is mapped twice or two outputs share a header,
    since a duplicate header would silently collapse in most CSV parsers.
    """
    headers = [c for c in next(wb["Responses"].iter_rows(min_row=1, max_row=1, values_only=True))]
    # (sheet, column letter, header) in one place so validation is uniform.
    mapped: dict[int, str] = {}

    def add(idx: int, header: str, sheet: str) -> None:
        if idx in mapped:
            raise ValueError(f"{sheet}: Responses column {idx + 1} is mapped more than once")
        mapped[idx] = str(header).strip()

    for letter, *_ in _rows(wb["Demographics"]):
        idx = _col_index(letter, headers, "Demographics")
        # The label is a short filter name; the question wording only exists in the header.
        add(idx, headers[idx], "Demographics")
    for sheet in ("Open Questions", "Multiple Choice Questions"):
        for letter, _num, text in (r[:3] for r in _rows(wb[sheet])):
            add(_col_index(letter, headers, sheet), text, sheet)
    for open_letter, _num, text, closed_letter in (r[:4] for r in _rows(wb["Hybrid Questions"])):
        add(_col_index(open_letter, headers, "Hybrid Questions"), f"{text}{HYBRID_OPEN_SUFFIX}", "Hybrid Questions")
        add(_col_index(closed_letter, headers, "Hybrid Questions"), f"{text}{HYBRID_CLOSED_SUFFIX}", "Hybrid Questions")

    out = sorted(mapped.items())
    seen: set[str] = set()
    for _, header in out:
        if header in seen:
            raise ValueError(f"Duplicate output header: {header!r}")
        seen.add(header)
    return out


def convert(template: Path, output: Path) -> tuple[int, list[str]]:
    """Write the CSV; return (respondent rows written, headers of unmapped columns)."""
    wb = openpyxl.load_workbook(template, data_only=True)
    columns = build_columns(wb)
    responses = list(wb["Responses"].iter_rows(min_row=2, values_only=True))
    mapped_idx = {i for i, _ in columns}
    first_row = next(wb["Responses"].iter_rows(min_row=1, max_row=1, values_only=True))
    # Column A is the respondent id, deliberately not exported.
    unmapped = [str(h) for i, h in enumerate(first_row) if h and i not in mapped_idx and i != 0]

    written = 0
    # utf-8-sig matches the BOM Citizen Space exports carry.
    with output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([h for _, h in columns])
        for row in responses:
            if not any(c not in (None, "") for c in row):
                continue
            writer.writerow(
                ["" if (v := row[i] if i < len(row) else None) is None else v for i, _ in columns]
            )
            written += 1
    return written, unmapped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("template", nargs="?", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("output", nargs="?", type=Path)
    args = parser.parse_args()
    output = args.output or args.template.with_name(f"{args.template.stem} - Citizen Space.csv")
    try:
        written, unmapped = convert(args.template, output)
    except ValueError as e:
        sys.exit(f"error: {e}")
    for header in unmapped:
        print(f"warning: Responses column not mapped on any sheet, dropped: {header!r}", file=sys.stderr)
    print(f"Wrote {written} rows to {output}")


if __name__ == "__main__":
    main()
