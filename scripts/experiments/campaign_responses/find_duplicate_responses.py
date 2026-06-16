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
CHUNK_SIZE = 150


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


def normalise(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines())


def chunk_text(text: str) -> list[str]:
    norm = normalise(text)
    return [
        norm[i : i + CHUNK_SIZE]
        for i in range(0, len(norm), CHUNK_SIZE)
        if len(norm[i : i + CHUNK_SIZE]) >= MIN_TEXT_LENGTH
    ]


def find_clusters(entries: list[dict]) -> list[list[dict]]:
    # Union-Find: merge any two responses that share a 150-char chunk
    entry_map = {str(e["themefinder_id"]): e for e in entries}
    parent = {eid: eid for eid in entry_map}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    chunk_to_ids: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        for chunk in chunk_text(entry["text"]):
            chunk_to_ids[hash_text(chunk)].append(str(entry["themefinder_id"]))

    for ids in chunk_to_ids.values():
        for i in range(1, len(ids)):
            union(ids[0], ids[i])

    components: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        components[find(str(entry["themefinder_id"]))].append(entry)

    return sorted(
        [c for c in components.values() if len(c) > 2],
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

    include_non_cluster = input("  Include non-cluster responses in output? [y/n]: ").strip().lower() == "y"

    target = prompt_int("  How many cluster responses do you want in the output? ", min_val=0)

    # Cycle through the unique cluster responses to fill the target count
    expanded = [dict(chosen[i % len(chosen)]) for i in range(target)]

    # Shuffle and reassign sequential integer IDs to match the original format
    combined = (non_cluster if include_non_cluster else []) + expanded
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

    n_non_cluster = len(non_cluster) if include_non_cluster else 0
    print(f"  Written {n_non_cluster + target} responses to {output_path}")
    print(f"  ({n_non_cluster} original + {target} cluster)")


def summarise_questions(question_dirs: list[Path]) -> list[tuple[Path, list[list[dict]], int]]:
    """Return (dir, clusters, total_responses) for each question dir."""
    summaries = []
    for question_dir in question_dirs:
        responses_path = question_dir / "responses.jsonl"
        if not responses_path.exists():
            continue
        entries = load_responses(responses_path)
        clusters = find_clusters(entries)
        summaries.append((question_dir, clusters, len(entries)))
    return summaries


def prompt_question_selection(summaries: list[tuple[Path, list[list[dict]], int]]) -> list[Path]:
    """Show all questions with their top-3 cluster sizes and ask which to include."""
    print("\nAvailable questions:\n")
    for i, (question_dir, clusters, total) in enumerate(summaries, 1):
        top3 = ", ".join(str(len(c)) for c in clusters[:3]) if clusters else "none"
        cluster_label = f"top cluster sizes: {top3}" if clusters else "no clusters found"
        print(f"  [{i}] {question_dir.name}  ({total} responses, {cluster_label})")
    print()

    while True:
        raw = input("  Enter question numbers to include (e.g. 1,3,4) or 'all': ").strip()
        if raw.lower() == "all":
            return [s[0] for s in summaries]
        parts = [p.strip() for p in raw.split(",")]
        if all(p.isdigit() and 1 <= int(p) <= len(summaries) for p in parts):
            return [summaries[int(p) - 1][0] for p in parts]
        print(f"  Enter comma-separated numbers between 1 and {len(summaries)}, or 'all'.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find duplicate response clusters and produce balanced output datasets.")
    parser.add_argument("inputs_dir", type=Path, help="Directory containing question_* subdirectories")
    parser.add_argument("output_dir", type=Path, help="Directory to write output datasets")
    args = parser.parse_args()

    inputs_dir = args.inputs_dir
    output_dir = args.output_dir

    if not inputs_dir.exists():
        print(f"Error: {inputs_dir} does not exist.")
        sys.exit(1)

    question_dirs = sorted(
        (d for d in inputs_dir.iterdir() if d.is_dir() and "question" in d.name),
        key=lambda d: [int(p) if p.isdigit() else p for p in d.name.replace("_", " ").split()],
    )

    if not question_dirs:
        print("No question directories found.")
        sys.exit(1)

    print("Scanning questions...")
    summaries = summarise_questions(question_dirs)

    if not summaries:
        print("No questions with responses found.")
        sys.exit(1)

    selected_dirs = prompt_question_selection(summaries)
    output_dir.mkdir(parents=True, exist_ok=True)

    for question_dir in selected_dirs:
        print(f"\n{'='*60}")
        print(f"  {question_dir.name}")
        print(f"{'='*60}")
        process_question(question_dir, output_dir)

    print("\nDone.")
