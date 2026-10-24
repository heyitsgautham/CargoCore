"""Tests for scripts/check_file_size.py, the CI guard against growing source files."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "check_file_size.py"
spec = importlib.util.spec_from_file_location("check_file_size", SCRIPT)
check_file_size = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_file_size)


def test_files_under_the_limit_pass() -> None:
    assert check_file_size.find_violations({"a.py": 800, "b.vue": 10}, {}, limit=800) == []


def test_new_file_over_the_limit_fails() -> None:
    problems = check_file_size.find_violations({"big.vue": 801}, {}, limit=800)

    assert problems == ["big.vue: 801 lines, over the 800-line limit"]


def test_grandfathered_file_may_shrink_but_not_grow() -> None:
    baseline = {"legacy.py": 1200}

    assert check_file_size.find_violations({"legacy.py": 1100}, baseline, limit=800) == []
    assert check_file_size.find_violations({"legacy.py": 1200}, baseline, limit=800) == []
    assert check_file_size.find_violations({"legacy.py": 1201}, baseline, limit=800) == [
        "legacy.py: 1201 lines, grew past its baseline of 1200"
    ]


def test_tracked_tree_matches_the_committed_baseline() -> None:
    sizes = {p: check_file_size.line_count(p) for p in check_file_size.tracked_source_files()}
    baseline = check_file_size.json.loads(check_file_size.BASELINE.read_text())

    assert check_file_size.find_violations(sizes, baseline) == []
