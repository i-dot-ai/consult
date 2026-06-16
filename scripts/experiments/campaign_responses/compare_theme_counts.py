"""Compare theme counts across clustered_themes.json files in subdirectories."""

import json
import sys
from pathlib import Path


def compare_theme_counts(search_dir: Path) -> None:
    files = sorted(search_dir.glob("*/clustered_themes.json"))
    if not files:
        print(f"No clustered_themes.json files found under {search_dir}")
        sys.exit(1)

    rows = []
    for path in files:
        with path.open() as f:
            data = json.load(f)
        rows.append((path.parent.name, len(data["theme_nodes"])))

    name_width = max(len(name) for name, _ in rows)
    header = f"{'Subdirectory':<{name_width}} | Themes"
    print(header)
    print("-" * len(header))
    for name, count in rows:
        print(f"{name:<{name_width}} | {count}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compare_theme_counts.py <directory>")
        sys.exit(1)

    compare_theme_counts(Path(sys.argv[1]))
