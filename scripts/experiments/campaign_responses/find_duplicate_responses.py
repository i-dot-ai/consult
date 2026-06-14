#!/usr/bin/env python3
"""Find duplicate response clusters across questions and produce balanced output datasets."""

import hashlib
import json
import random
import shutil
import sys
from collections import defaultdict
from pathlib import Path


MIN_TEXT_LENGTH = 20


def hash_text(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def load_responses(path: Path) -> list[dict]:
    entries = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if len(entry["text"]) >= MIN_TEXT_LENGTH:
                entries.append(entry)
    return entries


def find_clusters(entries: list[dict]) -> list[list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        groups[hash_text(entry["text"])].append(entry)
    return sorted(
        [g for g in groups.values() if len(g) > 2],
        key=len,
        reverse=True,
    )


def prompt_int(prompt: str, min_val: int = 1) -> int:
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and int(raw) >= min_val:
            return int(raw)
        print(f"  Please enter an integer >= {min_val}.")


def process_question(question_dir: Path, output_dir: Path) -> None:
    responses_path = question_dir / "responses.jsonl"
    if not responses_path.exists():
        print("  No responses.jsonl found, skipping.")
        return

    all_entries = load_responses(responses_path)
    clusters = find_clusters(all_entries)

    if not clusters:
        print("  No duplicate clusters found.")
        return

    print(f"\n  Found {len(clusters)} cluster(s):\n")
    for i, cluster in enumerate(clusters, 1):
        preview = cluster[0]["text"][:100].replace("\n", " ")
        print(f"  [{i}] {len(cluster)} responses — {preview!r}")
    print()

    while True:
        raw = input("  Choose a cluster ID (or 's' to skip): ").strip()
        if raw.lower() == "s":
            return
        if raw.isdigit() and 1 <= int(raw) <= len(clusters):
            chosen = clusters[int(raw) - 1]
            break
        print(f"  Enter a number 1–{len(clusters)} or 's' to skip.")

    cluster_ids = {str(e["themefinder_id"]) for e in chosen}
    non_cluster = [e for e in all_entries if str(e["themefinder_id"]) not in cluster_ids]
    print(f"\n  {len(non_cluster)} responses outside the chosen cluster.")

    target = prompt_int("  How many cluster responses do you want in the output? ")

    # Cycle through the unique cluster responses to fill the target count
    expanded = [dict(chosen[i % len(chosen)]) for i in range(target)]

    # Shuffle and reassign sequential integer IDs to match the original format
    combined = non_cluster + expanded
    random.shuffle(combined)
    for i, entry in enumerate(combined, 1):
        entry["themefinder_id"] = i

    output_question_dir = output_dir / "inputs" / question_dir.name
    output_question_dir.mkdir(parents=True, exist_ok=True)

    # Copy question.json alongside so the dir is usable by find_themes
    question_json = question_dir / "question.json"
    if question_json.exists():
        shutil.copy(question_json, output_question_dir / "question.json")

    output_path = output_question_dir / "responses.jsonl"
    with output_path.open("w") as f:
        for entry in combined:
            f.write(json.dumps(entry) + "\n")

    print(f"  Written {len(non_cluster) + len(expanded)} responses to {output_path}")
    print(f"  ({len(non_cluster)} original + {target} cluster)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <consultation_inputs_dir> <output_dir>")
        print("  consultation_inputs_dir: path containing question_* subdirectories")
        sys.exit(1)

    inputs_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not inputs_dir.exists():
        print(f"Error: {inputs_dir} does not exist.")
        sys.exit(1)

    question_dirs = sorted(d for d in inputs_dir.iterdir() if d.is_dir() and "question" in d.name)

    if not question_dirs:
        print("No question directories found.")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    for question_dir in question_dirs:
        print(f"\n{'='*60}")
        print(f"  {question_dir.name}")
        print(f"{'='*60}")
        process_question(question_dir, output_dir)

    print("\nDone.")
