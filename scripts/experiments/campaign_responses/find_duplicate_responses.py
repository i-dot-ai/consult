#!/usr/bin/env python3
"""Identify groups of identical responses in a responses.jsonl file using MD5 hashing."""

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


MIN_TEXT_LENGTH = 20


def hash_text(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def find_duplicate_responses(path: Path) -> None:
    groups: dict[str, list[dict]] = defaultdict(list)

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if len(entry["text"]) < MIN_TEXT_LENGTH:
                continue
            key = hash_text(entry["text"])
            groups[key].append(entry)

    duplicates = sorted(
        [entries for entries in groups.values() if len(entries) > 2],
        key=len,
        reverse=True,
    )

    if not duplicates:
        print("No duplicate responses found.")
        return

    print(f"Found {len(duplicates)} group(s) of identical responses:\n")
    for i, entries in enumerate(duplicates, 1):
        ids = [str(e["themefinder_id"]) for e in entries]
        preview = entries[0]["text"][:120].replace("\n", " ")
        print(f"Group {i} ({len(entries)} responses) — IDs: {', '.join(ids)}")
        print(f"  Text: {preview!r}")
        print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <responses.jsonl>")
        sys.exit(1)

    find_duplicate_responses(Path(sys.argv[1]))
