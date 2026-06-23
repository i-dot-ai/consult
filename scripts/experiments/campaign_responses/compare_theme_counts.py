"""Compare theme counts across runs and consultations, showing mean and stddev per question.

Expected structure:
  <search_dir>/<consultation_name>/outputs/run_<n>/.../<question_part_N>/clustered_themes.json
"""

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path


def _natural_sort_key(name: str) -> list[int | str]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def compare_theme_counts(search_dir: Path) -> None:
    files = sorted(search_dir.rglob("clustered_themes.json"))
    if not files:
        print(f"No clustered_themes.json files found under {search_dir}")
        sys.exit(1)

    # question -> consultation -> [counts across runs]
    data: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    # question -> consultation -> consensus theme count (excluded from mean/stddev)
    consensus_counts: dict[str, dict[str, int]] = defaultdict(dict)

    for path in files:
        parts = path.relative_to(search_dir).parts
        consultation = parts[0]
        question = path.parent.name
        with path.open() as f:
            count = len(json.load(f)["theme_nodes"])
        if "consensus" in parts[1:-1]:
            consensus_counts[question][consultation] = count
        else:
            data[question][consultation].append(count)

    for question, consultations in sorted(data.items()):
        rows = []
        for consultation, counts in sorted(consultations.items(), key=lambda item: _natural_sort_key(item[0])):
            mean = sum(counts) / len(counts)
            stddev = math.sqrt(sum((c - mean) ** 2 for c in counts) / len(counts)) if len(counts) > 1 else 0.0
            consensus = consensus_counts.get(question, {}).get(consultation)
            rows.append((consultation, mean, stddev, len(counts), sorted(counts), consensus))

        name_width = max(len(r[0]) for r in rows)
        header = f"  {'Consultation':<{name_width}} | Mean   | Stddev | Runs | Counts | Consensus"
        print(f"\n{question}")
        print(header)
        print("  " + "-" * (len(header) - 2))
        for name, mean, stddev, runs, counts, consensus in rows:
            consensus_str = "-" if consensus is None else str(consensus)
            print(f"  {name:<{name_width}} | {mean:6.1f} | {stddev:6.2f} | {runs:4} | {counts!s:<20} | {consensus_str}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare theme counts across runs and consultations per question.")
    parser.add_argument("directory", type=Path, help="Directory containing consultation subdirectories")
    args = parser.parse_args()

    compare_theme_counts(args.directory)
