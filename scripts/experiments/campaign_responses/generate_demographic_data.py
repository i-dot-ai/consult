"""Generate a JSONL file with fixed demographic data for every themefinder_id found
across all responses.jsonl files in a directory tree."""

import json
import sys
from pathlib import Path

DEMOGRAPHIC_DATA = {
    "In what capacity are you responding to this consultation": ["As a member of the public"],
    "Do you consider yourself to have a health condition or a disability?": ["Yes"],
    "response_source": ["MS Forms"],
    "Where do you live?": ["England"],
}


def collect_themefinder_ids(search_dir: Path) -> set[int]:
    ids: set[int] = set()
    response_files = list(search_dir.rglob("responses.jsonl"))
    if not response_files:
        print(f"No responses.jsonl files found under {search_dir}")
        return ids

    for path in response_files:
        with path.open() as f:
            for line in f:
                if line.strip():
                    ids.add(json.loads(line)["themefinder_id"])
        print(f"  {path} — {len(ids)} unique IDs so far")

    return ids


def generate_demographic_data(search_dir: Path, output_path: Path) -> None:
    print(f"Scanning {search_dir} for responses.jsonl files...")
    ids = collect_themefinder_ids(search_dir)

    with output_path.open("w") as f:
        for tid in sorted(ids):
            f.write(json.dumps({"themefinder_id": tid, "demographic_data": DEMOGRAPHIC_DATA}) + "\n")

    print(f"Written {len(ids)} entries to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_demographic_data.py <search_dir> <output.jsonl>")
        sys.exit(1)

    generate_demographic_data(Path(sys.argv[1]), Path(sys.argv[2]))
