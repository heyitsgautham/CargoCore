from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT_DIR / "tests" / "reports"

EVIDENCE_JSON = REPORTS_DIR / "API_TEST_EVIDENCE.json"
MISMATCH_JSON = REPORTS_DIR / "API_MISMATCH_CASES.json"
COVERAGE_JSON = REPORTS_DIR / "coverage.json"

EVIDENCE_MD = REPORTS_DIR / "API_TEST_EVIDENCE.md"
MISMATCH_MD = REPORTS_DIR / "API_MISMATCH_SHOWCASE.md"


def _read_json(path: Path) -> Any:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _to_inline_json(value: Any, limit: int = 220) -> str:
    text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _escape_table_cell(text: str) -> str:
    return text.replace("|", "\\|")


def _coverage_percent() -> float | None:
    if not COVERAGE_JSON.exists():
        return None
    data = _read_json(COVERAGE_JSON)
    return float(data.get("totals", {}).get("percent_covered", 0.0))


def write_evidence_markdown(evidence_rows: list[dict[str, Any]]) -> None:
    passed = sum(1 for row in evidence_rows if row.get("status") == "PASS")
    total = len(evidence_rows)
    failed = total - passed

    lines = [
        "# API Test Evidence",
        "",
        "## Summary",
        f"- Total recorded API cases: {total}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
    ]

    coverage = _coverage_percent()
    if coverage is not None:
        lines.append(f"- Pytest coverage (tests scope): {coverage:.2f}%")

    lines.extend(
        [
            "",
            "## Case Evidence",
            "",
            "| Case ID | Endpoint | Input | Expected Output | Actual Output | Status |",
            "|---|---|---|---|---|---|",
        ]
    )

    for row in evidence_rows:
        lines.append(
            "| {case_id} | {endpoint} | {input_data} | {expected} | {actual} | {status} |".format(
                case_id=_escape_table_cell(str(row.get("case_id", ""))),
                endpoint=_escape_table_cell(str(row.get("endpoint", ""))),
                input_data=_escape_table_cell(_to_inline_json(row.get("input"))),
                expected=_escape_table_cell(_to_inline_json(row.get("expected_output"))),
                actual=_escape_table_cell(_to_inline_json(row.get("actual_output"))),
                status=_escape_table_cell(str(row.get("status", ""))),
            )
        )

    EVIDENCE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mismatch_markdown(mismatch_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# API Mismatch Showcase",
        "",
        "## Summary",
        f"- Total mismatches recorded: {len(mismatch_rows)}",
        "",
    ]

    if not mismatch_rows:
        lines.append("No mismatch observed in current scope.")
        MISMATCH_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    lines.extend(
        [
            "## Mismatch Details",
            "",
            "| Case ID | Endpoint | Input | Expected Output | Actual Output | Difference Summary |",
            "|---|---|---|---|---|---|",
        ]
    )

    for row in mismatch_rows:
        lines.append(
            "| {case_id} | {endpoint} | {input_data} | {expected} | {actual} | {summary} |".format(
                case_id=_escape_table_cell(str(row.get("case_id", ""))),
                endpoint=_escape_table_cell(str(row.get("endpoint", ""))),
                input_data=_escape_table_cell(_to_inline_json(row.get("input"))),
                expected=_escape_table_cell(_to_inline_json(row.get("expected_output"))),
                actual=_escape_table_cell(_to_inline_json(row.get("actual_output"))),
                summary=_escape_table_cell(str(row.get("difference_summary", ""))),
            )
        )

    MISMATCH_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    evidence_rows = _read_json(EVIDENCE_JSON)
    mismatch_rows = _read_json(MISMATCH_JSON)

    if not isinstance(evidence_rows, list):
        raise SystemExit("Evidence JSON must contain a list.")
    if not isinstance(mismatch_rows, list):
        raise SystemExit("Mismatch JSON must contain a list.")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_evidence_markdown(evidence_rows)
    write_mismatch_markdown(mismatch_rows)


if __name__ == "__main__":
    main()
