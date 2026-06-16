"""Compare theme counts across clustered_themes.json files in subdirectories."""

import json
import sys
from collections import defaultdict
from pathlib import Path


def compare_theme_counts(search_dir: Path) -> None:
    files = sorted(search_dir.rglob("clustered_themes.json"))
    if not files:
        print(f"No clustered_themes.json files found under {search_dir}")
        sys.exit(1)

    by_subdir: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for path in files:
        with path.open() as f:
            data = json.load(f)
        relative = path.parent.relative_to(search_dir)
        top_level = relative.parts[0]
        subdir = str(Path(*relative.parts[1:])) if len(relative.parts) > 1 else "."
        by_subdir[subdir].append((top_level, len(data["theme_nodes"])))

    for subdir, rows in sorted(by_subdir.items()):
        print(f"\n{subdir}")
        name_width = max(len(r[0]) for r in rows)
        header = f"  {'Top-level':<{name_width}} | Themes"
        print(header)
        print("  " + "-" * (len(header) - 2))
        for top, count in rows:
            print(f"  {top:<{name_width}} | {count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare theme counts across clustered_themes.json files.")
    parser.add_argument("directory", type=Path, help="Directory to search recursively for clustered_themes.json files")
    args = parser.parse_args()

    compare_theme_counts(args.directory)
