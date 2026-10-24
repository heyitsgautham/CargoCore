"""Fail CI when source files grow past the size limit.

Files under backend/app, frontend/src and driver-app/src may not exceed LIMIT lines.
Files that were already over the limit are listed in scripts/file_size_baseline.json
with their line count, and they may shrink but not grow. Run with --update after
splitting a file to lower or drop its baseline entry.

    python scripts/check_file_size.py           # check
    python scripts/check_file_size.py --update  # rewrite the baseline from the tree
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

LIMIT = 800
ROOTS = ("backend/app/", "frontend/src/", "driver-app/src/")
SUFFIXES = (".py", ".js", ".vue", ".ts")
REPO = Path(__file__).resolve().parent.parent
BASELINE = REPO / "scripts" / "file_size_baseline.json"


def tracked_source_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", *ROOTS], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return sorted(p for p in out.splitlines() if p.endswith(SUFFIXES))


def line_count(path: str) -> int:
    with open(REPO / path, encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def find_violations(sizes: dict[str, int], baseline: dict[str, int], limit: int = LIMIT) -> list[str]:
    problems = []
    for path, lines in sorted(sizes.items()):
        allowed = baseline.get(path, limit)
        if lines > max(allowed, limit):
            if path in baseline:
                problems.append(f"{path}: {lines} lines, grew past its baseline of {allowed}")
            else:
                problems.append(f"{path}: {lines} lines, over the {limit}-line limit")
    return problems


def main(argv: list[str]) -> int:
    sizes = {path: line_count(path) for path in tracked_source_files()}
    if "--update" in argv:
        over = {path: lines for path, lines in sizes.items() if lines > LIMIT}
        BASELINE.write_text(json.dumps(over, indent=2, sort_keys=True) + "\n")
        print(f"Baseline lists {len(over)} files over {LIMIT} lines.")
        return 0

    baseline = json.loads(BASELINE.read_text()) if BASELINE.exists() else {}
    problems = find_violations(sizes, baseline)
    for problem in problems:
        print(problem)
    if problems:
        print("Split the file, or run --update only if a split brought it down.")
        return 1
    print(f"{len(sizes)} source files checked, {len(baseline)} grandfathered over {LIMIT} lines.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
