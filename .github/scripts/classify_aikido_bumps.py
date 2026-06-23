"""
Classify version bump types (major/minor/patch) in Aikido autofix PRs.

Parses git diffs of uv.lock and package-lock.json files to find all changed
package versions, then writes has_major and bump_count to GITHUB_OUTPUT.

Exit codes:
  0 - completed classification (all minor/patch, or no lockfile changes)
  1 - script error
"""

import json
import os
import re
import subprocess
import sys


def parse_semver(ver: str) -> tuple[int, int, int]:
    ver = ver.lstrip("v")
    parts = re.split(r"[.\-+]", ver)
    try:
        return (
            int(parts[0]),
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0,
        )
    except (ValueError, IndexError):
        return (0, 0, 0)


def classify_bump(old: str, new: str) -> str:
    o, n = parse_semver(old), parse_semver(new)
    if n[0] > o[0]:
        return "major"
    elif n[1] > o[1]:
        return "minor"
    else:
        return "patch"


def parse_uv_lock(lines: list[str]) -> list[dict]:
    """Extract (name, old_version, new_version) changes from a uv.lock diff."""
    bumps = []
    current_name = None
    for i, line in enumerate(lines):
        m = re.match(r"^[ ]name = \"([^\"]+)\"", line)
        if m:
            current_name = m.group(1)
        m_old = re.match(r'^-version = "([^"]+)"$', line)
        if m_old and current_name:
            # The +version line may be many lines ahead (after wheel URL lines)
            for j in range(i + 1, min(i + 300, len(lines))):
                m_new = re.match(r'^\+version = "([^"]+)"$', lines[j])
                if m_new:
                    bumps.append((current_name, m_old.group(1), m_new.group(1)))
                    break
    return bumps


def parse_package_lock(lines: list[str]) -> list[dict]:
    """Extract (name, old_version, new_version) changes from a package-lock.json diff."""
    bumps = []
    current_pkg = None
    for i, line in enumerate(lines):
        m = re.match(r'^[+ ] {4}"node_modules/([^"]+)": \{', line)
        if m:
            current_pkg = m.group(1)
        m_old = re.match(r'^-\s+"version": "([^"]+)"', line)
        if m_old and current_pkg:
            for j in range(i + 1, min(i + 5, len(lines))):
                m_new = re.match(r'^\+\s+"version": "([^"]+)"', lines[j])
                if m_new:
                    bumps.append((current_pkg, m_old.group(1), m_new.group(1)))
                    break
    return bumps


def main() -> None:
    base_sha = os.environ.get("BASE_SHA")
    head_sha = os.environ.get("HEAD_SHA")

    if not base_sha or not head_sha:
        print("ERROR: BASE_SHA and HEAD_SHA environment variables must be set", file=sys.stderr)
        sys.exit(1)

    changed_files = subprocess.run(
        ["git", "diff", "--name-only", base_sha, head_sha],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip().split("\n")

    all_bumps = []
    has_major = False

    for lockfile in changed_files:
        if not (lockfile.endswith("uv.lock") or lockfile.endswith("package-lock.json")):
            continue

        diff = subprocess.run(
            ["git", "diff", base_sha, head_sha, "--", lockfile],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        lines = diff.split("\n")

        if lockfile.endswith("uv.lock"):
            raw = parse_uv_lock(lines)
        else:
            raw = parse_package_lock(lines)

        for pkg, old, new in raw:
            bump = classify_bump(old, new)
            all_bumps.append({"pkg": pkg, "old": old, "new": new, "type": bump, "file": lockfile})
            if bump == "major":
                has_major = True

    print("=== Dependency Bump Report ===")
    if all_bumps:
        for b in all_bumps:
            marker = "  <-- MAJOR" if b["type"] == "major" else ""
            print(f"  [{b['type']:5}] {b['pkg']}: {b['old']} -> {b['new']} ({b['file']}){marker}")
    else:
        print("  (no lockfile version changes detected)")

    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"has_major={'true' if has_major else 'false'}\n")
            f.write(f"bump_count={len(all_bumps)}\n")


if __name__ == "__main__":
    main()
