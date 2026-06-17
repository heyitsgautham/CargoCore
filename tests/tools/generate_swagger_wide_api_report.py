from __future__ import annotations

import asyncio
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    LongTable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
TESTS_DIR = ROOT_DIR / "tests"
REPORTS_DIR = TESTS_DIR / "reports"
TOOLS_DIR = TESTS_DIR / "tools"

OPENAPI_YAML = TESTS_DIR / "api-docs" / "openapi.swagger.yaml"
EVIDENCE_JSON = REPORTS_DIR / "API_TEST_EVIDENCE.json"
MISMATCH_NARRATIVE_MD = REPORTS_DIR / "PHASE_D_MISMATCH_NARRATIVE.md"
SCAN_SCRIPT = TOOLS_DIR / "scan_missing_endpoint_statuses.py"

OUTPUT_MD = REPORTS_DIR / "SWAGGER_WIDE_API_TEST_REPORT.md"
OUTPUT_PDF = REPORTS_DIR / "SWAGGER_WIDE_API_TEST_REPORT.pdf"
OUTPUT_MATRIX_JSON = REPORTS_DIR / "SWAGGER_WIDE_OPERATION_MATRIX.json"
OUTPUT_SCAN_JSON = REPORTS_DIR / "SWAGGER_WIDE_PROBE_SCAN_RESULTS.json"

METHOD_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b", re.IGNORECASE)
PATH_RE = re.compile(r"(/api/v1/[^\s,+*]+|/health)")
TEST_DEF_RE = re.compile(r"^\s*(?:async\s+def|def)\s+(test_[A-Za-z0-9_]+)\s*\(", re.MULTILINE)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _normalize_operation(operation: str) -> str:
    text = operation.strip()
    if not text:
        return ""
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return text.upper()
    method, path = parts
    return f"{method.upper()} {path.strip()}"


def _extract_status_code(value: Any) -> int | None:
    if not isinstance(value, dict):
        return None
    status = value.get("status_code")
    if isinstance(status, int):
        return status
    if isinstance(status, str) and status.isdigit():
        return int(status)
    return None


def _json_compact(value: Any, max_len: int = 180) -> str:
    try:
        rendered = json.dumps(value, ensure_ascii=True, sort_keys=True)
    except Exception:
        rendered = str(value)
    if len(rendered) <= max_len:
        return rendered
    return rendered[: max_len - 3] + "..."


def _extract_operations_from_endpoint_text(endpoint: str) -> set[str]:
    text = endpoint.strip()
    if not text:
        return set()

    methods = [m.upper() for m in METHOD_RE.findall(text)]
    paths = PATH_RE.findall(text)
    if not methods or not paths:
        return set()

    operations: set[str] = set()
    if len(paths) == 1 and len(methods) >= 1:
        for method in methods:
            operations.add(_normalize_operation(f"{method} {paths[0]}"))
        return operations

    if len(paths) == len(methods):
        for method, path in zip(methods, paths):
            operations.add(_normalize_operation(f"{method} {path}"))
        return operations

    for method in methods:
        for path in paths:
            operations.add(_normalize_operation(f"{method} {path}"))
    return operations


def _load_openapi_operations() -> dict[str, list[int]]:
    spec = _read_yaml(OPENAPI_YAML, default={})
    if not isinstance(spec, dict):
        return {}

    operations: dict[str, list[int]] = {}
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return operations

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, op_spec in path_item.items():
            if str(method).lower() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                continue
            operation = _normalize_operation(f"{str(method).upper()} {path}")
            statuses: list[int] = []
            if isinstance(op_spec, dict):
                responses = op_spec.get("responses", {})
                if isinstance(responses, dict):
                    for status_code in responses:
                        code_text = str(status_code)
                        if code_text.isdigit():
                            statuses.append(int(code_text))
            operations[operation] = sorted(set(statuses))

    return operations


def _discover_test_name_index() -> tuple[dict[str, list[str]], list[dict[str, Any]]]:
    test_roots = [TESTS_DIR / "contract", TESTS_DIR / "integration", TESTS_DIR / "unit"]
    mapping: dict[str, list[str]] = {}
    inventory: list[dict[str, Any]] = []

    for root in test_roots:
        if not root.exists():
            continue
        for file_path in sorted(root.rglob("test_*.py")):
            rel = file_path.relative_to(ROOT_DIR).as_posix()
            content = file_path.read_text(encoding="utf-8")
            discovered = TEST_DEF_RE.findall(content)
            inventory.append({
                "file": rel,
                "test_count": len(discovered),
            })
            for test_name in discovered:
                mapping.setdefault(test_name, []).append(rel)

    return mapping, inventory


def _load_probe_scan_rows() -> list[dict[str, Any]]:
    if not SCAN_SCRIPT.exists():
        return []

    spec = importlib.util.spec_from_file_location("scan_missing_endpoint_statuses", SCAN_SCRIPT)
    if spec is None or spec.loader is None:
        return []

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    rows = asyncio.run(module.run_scan())
    if not isinstance(rows, list):
        return []
    OUTPUT_SCAN_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return [row for row in rows if isinstance(row, dict)]


def _build_matrix_rows(
    openapi_operations: dict[str, list[int]],
    evidence_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    evidence_by_operation: dict[str, list[dict[str, Any]]] = {}

    for row in evidence_rows:
        endpoint = str(row.get("endpoint", ""))
        operations = _extract_operations_from_endpoint_text(endpoint)
        for operation in operations:
            if operation in openapi_operations:
                evidence_by_operation.setdefault(operation, []).append(row)

    probe_by_operation = {
        _normalize_operation(str(row.get("operation", ""))): row
        for row in probe_rows
        if str(row.get("operation", "")).strip()
    }

    matrix_rows: list[dict[str, Any]] = []
    direct_case_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []

    for operation in sorted(openapi_operations):
        documented = openapi_operations.get(operation, [])
        direct_rows = evidence_by_operation.get(operation, [])

        if direct_rows:
            observed_codes = sorted(
                {
                    code
                    for code in (_extract_status_code(item.get("actual_output")) for item in direct_rows)
                    if code is not None
                }
            )
            has_direct_mismatch = False
            case_ids: list[str] = []
            for item in direct_rows:
                case_id = str(item.get("case_id", "-")).strip() or "-"
                case_ids.append(case_id)
                expected = _extract_status_code(item.get("expected_output"))
                actual = _extract_status_code(item.get("actual_output"))
                if expected is not None and actual is not None and expected != actual:
                    has_direct_mismatch = True
                    mismatch_rows.append(
                        {
                            "type": "DIRECT",
                            "operation": operation,
                            "case_id": case_id,
                            "expected": expected,
                            "actual": actual,
                            "explanation": "Expected and actual status differ in direct pytest evidence.",
                        }
                    )

            result = "FAIL" if has_direct_mismatch else ("PASS" if all(str(item.get("status", "")).upper() == "PASS" for item in direct_rows) else "FAIL")
            observed_text = ",".join(str(code) for code in observed_codes) if observed_codes else "-"
            matrix_rows.append(
                {
                    "operation": operation,
                    "mode": "DIRECT",
                    "documented_statuses": documented,
                    "observed_status": observed_text,
                    "result": result,
                    "source": ", ".join(sorted(set(case_ids))),
                }
            )
            continue

        probe = probe_by_operation.get(operation)
        if probe:
            actual_status = probe.get("actual_status", "-")
            result = "FAIL" if bool(probe.get("mismatch")) else "PASS"
            expected_statuses = probe.get("expected_statuses", documented)
            matrix_rows.append(
                {
                    "operation": operation,
                    "mode": "PROBE",
                    "documented_statuses": expected_statuses,
                    "observed_status": str(actual_status),
                    "result": result,
                    "source": "Swagger probe scan",
                }
            )
            if bool(probe.get("mismatch")):
                mismatch_rows.append(
                    {
                        "type": "PROBE",
                        "operation": operation,
                        "case_id": "PROBE",
                        "expected": expected_statuses,
                        "actual": actual_status,
                        "explanation": "Probe status is outside expected status set.",
                    }
                )
            continue

        matrix_rows.append(
            {
                "operation": operation,
                "mode": "UNVERIFIED",
                "documented_statuses": documented,
                "observed_status": "-",
                "result": "UNVERIFIED",
                "source": "No probe row",
            }
        )

    # Build direct case appendix rows once (all evidence rows)
    for row in evidence_rows:
        direct_case_rows.append(
            {
                "case_id": str(row.get("case_id", "-")),
                "test_name": str(row.get("test_name", "-")),
                "endpoint": str(row.get("endpoint", "-")),
                "input": row.get("input", {}),
                "expected": row.get("expected_output", {}),
                "actual": row.get("actual_output", {}),
                "status": str(row.get("status", "-")),
            }
        )

    counts = {
        "openapi_operations": len(openapi_operations),
        "matrix_rows": len(matrix_rows),
        "direct_operations": sum(1 for row in matrix_rows if row["mode"] == "DIRECT"),
        "probe_operations": sum(1 for row in matrix_rows if row["mode"] == "PROBE"),
        "pass_rows": sum(1 for row in matrix_rows if row["result"] == "PASS"),
        "fail_rows": sum(1 for row in matrix_rows if row["result"] == "FAIL"),
        "unverified_rows": sum(1 for row in matrix_rows if row["result"] == "UNVERIFIED"),
        "direct_case_count": len(direct_case_rows),
        "mismatch_count": len(mismatch_rows),
    }

    return matrix_rows, direct_case_rows, mismatch_rows, counts


def _write_markdown(
    matrix_rows: list[dict[str, Any]],
    direct_case_rows: list[dict[str, Any]],
    mismatch_rows: list[dict[str, Any]],
    counts: dict[str, Any],
    test_name_to_files: dict[str, list[str]],
    file_inventory: list[dict[str, Any]],
) -> None:
    lines: list[str] = []
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines.append("# Swagger-Wide API Test Report")
    lines.append("")
    lines.append(f"Generated at: {generated_at}")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(f"- OpenAPI operations: {counts['openapi_operations']}")
    lines.append(f"- Matrix rows generated: {counts['matrix_rows']}")
    lines.append(f"- Directly covered operations: {counts['direct_operations']}")
    lines.append(f"- Probe-validated operations: {counts['probe_operations']}")
    lines.append(f"- PASS rows: {counts['pass_rows']}")
    lines.append(f"- FAIL rows: {counts['fail_rows']}")
    lines.append(f"- UNVERIFIED rows: {counts['unverified_rows']}")
    lines.append(f"- Direct test cases documented: {counts['direct_case_count']}")
    lines.append("")

    lines.append("## 2. Swagger-Wide Operation Matrix")
    lines.append("")
    lines.append("| # | Operation | Mode | Documented Statuses | Observed | Result | Source |")
    lines.append("|---|---|---|---|---|---|---|")
    for idx, row in enumerate(matrix_rows, start=1):
        documented = ", ".join(str(code) for code in row["documented_statuses"]) if row["documented_statuses"] else "-"
        lines.append(
            f"| {idx} | {row['operation']} | {row['mode']} | {documented} | {row['observed_status']} | {row['result']} | {row['source']} |"
        )
    lines.append("")

    lines.append("## 3. Direct Test Case Evidence (Input/Expected/Actual)")
    lines.append("")
    lines.append("| Case ID | Test Name | Test File | Endpoint | Input | Expected | Actual | Status |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in direct_case_rows:
        files = test_name_to_files.get(row["test_name"], [])
        test_file = ", ".join(files) if files else "-"
        lines.append(
            "| {case_id} | {test_name} | {test_file} | {endpoint} | {input} | {expected} | {actual} | {status} |".format(
                case_id=row["case_id"],
                test_name=row["test_name"],
                test_file=test_file,
                endpoint=row["endpoint"],
                input=_json_compact(row["input"], max_len=150),
                expected=_json_compact(row["expected"], max_len=150),
                actual=_json_compact(row["actual"], max_len=150),
                status=row["status"],
            )
        )
    lines.append("")

    lines.append("## 4. Mismatch Summary (Expected != Actual)")
    lines.append("")
    lines.append("| Type | Case | Operation | Expected | Actual | Explanation |")
    lines.append("|---|---|---|---|---|---|")
    if mismatch_rows:
        for row in mismatch_rows:
            expected_value = row["expected"]
            if isinstance(expected_value, list):
                expected_text = ", ".join(str(code) for code in expected_value)
            else:
                expected_text = str(expected_value)
            lines.append(
                f"| {row['type']} | {row['case_id']} | {row['operation']} | {expected_text} | {row['actual']} | {row['explanation']} |"
            )
    else:
        lines.append("| - | - | - | - | - | No mismatches found in current run. |")
    lines.append("")

    lines.append("## 5. Historical Fixed Expected != Actual Cases")
    lines.append("")
    lines.append("| Area | What Failed Before | Fix Applied | Validation |")
    lines.append("|---|---|---|---|")
    lines.append("| FR-INT-003 payroll run | Mock DB path lacked commit() behavior causing non-production test failure. | Added commit-capable DB override for payroll success path in integration test. | Finance/rates targeted run and full regression passed. |")
    lines.append("| AI support flow tests | Monkeypatched service stubs did not accept keyword arguments used by routers. | Updated stubs to keyword-compatible signatures (db=, data=). | AI support targeted run and full regression passed. |")
    lines.append("")

    lines.append("## 6. Test File Inventory")
    lines.append("")
    lines.append("| # | Test File | Discovered Test Functions |")
    lines.append("|---|---|---|")
    for idx, row in enumerate(file_inventory, start=1):
        lines.append(f"| {idx} | {row['file']} | {row['test_count']} |")
    lines.append("")

    lines.append("## 7. Terminal Evidence Artifacts")
    lines.append("")
    lines.append("- tests/reports/screenshots/phase_d/01_finance_rates_targeted.txt")
    lines.append("- tests/reports/screenshots/phase_d/02_warehouse_ops_targeted.txt")
    lines.append("- tests/reports/screenshots/phase_d/03_logistics_tracking_targeted.txt")
    lines.append("- tests/reports/screenshots/phase_d/04_ai_support_flows_targeted.txt")
    lines.append("- tests/reports/screenshots/phase_d/05_full_suite_regression.txt")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_pdf(
    matrix_rows: list[dict[str, Any]],
    direct_case_rows: list[dict[str, Any]],
    mismatch_rows: list[dict[str, Any]],
    counts: dict[str, Any],
    test_name_to_files: dict[str, list[str]],
    file_inventory: list[dict[str, Any]],
) -> None:
    palette = {
        "cover_bg": colors.HexColor("#061A34"),
        "cover_primary": colors.HexColor("#1D63AA"),
        "cover_ring_outer": colors.HexColor("#0E2A4F"),
        "cover_ring_inner": colors.HexColor("#214D81"),
        "cover_text": colors.HexColor("#A7C6E8"),
        "content_title": colors.HexColor("#123B68"),
        "content_text": colors.HexColor("#334E68"),
        "header_bg": colors.HexColor("#F4F8FC"),
        "table_header": colors.HexColor("#123B68"),
        "table_grid": colors.HexColor("#D7E2EE"),
        "table_alt": colors.HexColor("#F8FBFF"),
        "pass": colors.HexColor("#2F855A"),
        "fail": colors.HexColor("#C53030"),
        "warn": colors.HexColor("#D69E2E"),
        "accent": colors.HexColor("#1D63AA"),
    }

    styles = getSampleStyleSheet()
    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=palette["content_title"],
        spaceBefore=2,
        spaceAfter=8,
    )
    subheading_style = ParagraphStyle(
        "SubheadingStyle",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=palette["content_title"],
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=13,
        textColor=palette["content_text"],
        spaceAfter=6,
    )
    body_small_style = ParagraphStyle(
        "BodySmallStyle",
        parent=body_style,
        fontSize=8.2,
        leading=11,
        spaceAfter=4,
    )
    table_cell_style = ParagraphStyle(
        "TableCellStyle",
        parent=body_small_style,
        fontSize=6.8,
        leading=8.2,
        wordWrap="LTR",
    )
    table_cell_center_style = ParagraphStyle(
        "TableCellCenterStyle",
        parent=table_cell_style,
        alignment=TA_CENTER,
    )

    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=32,
        rightMargin=32,
        topMargin=40,
        bottomMargin=26,
        title="Swagger-Wide API Test Report",
        author="QuadCore-Devs",
    )

    def _draw_cover(canvas: Any, page_doc: Any) -> None:
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(palette["cover_bg"])
        canvas.rect(0, 0, width, height, stroke=0, fill=1)

        canvas.setFillColor(palette["cover_primary"])
        canvas.rect(0, 0, 12, height, stroke=0, fill=1)
        canvas.rect(0, 0, width, 46, stroke=0, fill=1)

        canvas.setFillColor(palette["cover_ring_outer"])
        canvas.circle(width + 34, height + 16, 142, stroke=0, fill=1)
        canvas.setFillColor(palette["cover_ring_inner"])
        canvas.circle(width + 34, height + 16, 104, stroke=0, fill=1)

        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 33)
        canvas.drawString(56, height - 170, "SWAGGER-WIDE")
        canvas.drawString(56, height - 212, "API TEST REPORT")

        canvas.setFillColor(palette["cover_text"])
        canvas.setFont("Helvetica-Bold", 20)
        canvas.drawString(56, height - 257, "CargoCore Backend Quality Reference")

        canvas.setStrokeColor(palette["cover_primary"])
        canvas.setLineWidth(2.4)
        canvas.line(200, height - 312, 370, height - 312)

        canvas.setFillColor(palette["cover_text"])
        canvas.setFont("Helvetica", 14)
        canvas.drawString(56, height - 356, "Comprehensive OpenAPI operation coverage with direct pytest")
        canvas.drawString(56, height - 380, "evidence and swagger-driven probe validation.")

        canvas.setFillColor(colors.HexColor("#7BB1DF"))
        canvas.setFont("Helvetica", 10.5)
        metrics_line = (
            f"{counts['openapi_operations']} operations | "
            f"{counts['pass_rows']} pass | "
            f"{counts['fail_rows']} fail | "
            f"{counts['direct_case_count']} direct cases"
        )
        canvas.drawString(56, height - 427, metrics_line)
        canvas.restoreState()

    def _draw_content_chrome(canvas: Any, page_doc: Any) -> None:
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(palette["header_bg"])
        canvas.rect(0, height - 40, width, 40, stroke=0, fill=1)
        canvas.setFillColor(palette["accent"])
        canvas.rect(0, height - 40, 9, 40, stroke=0, fill=1)

        canvas.setStrokeColor(palette["table_grid"])
        canvas.setLineWidth(0.7)
        canvas.line(page_doc.leftMargin, height - 41, width - page_doc.rightMargin, height - 41)

        canvas.setFont("Helvetica-Bold", 9.5)
        canvas.setFillColor(palette["content_title"])
        canvas.drawString(page_doc.leftMargin, height - 24, "CargoCore - Swagger-Wide API Test Report")
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(palette["content_text"])
        canvas.drawRightString(width - page_doc.rightMargin, height - 24, f"Page {max(1, page_doc.page - 1)}")

        canvas.setFont("Helvetica", 8)
        canvas.drawString(page_doc.leftMargin, 14, "Swagger-wide API quality evidence")
        canvas.drawRightString(width - page_doc.rightMargin, 14, "QuadCore-Devs Quality Engineering")
        canvas.restoreState()

    cover_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="cover-frame")
    content_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin + 18,
        doc.width,
        doc.height - 30,
        id="content-frame",
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[cover_frame], onPage=_draw_cover),
            PageTemplate(id="content", frames=[content_frame], onPage=_draw_content_chrome),
        ]
    )

    status_data = [
        max(int(counts["pass_rows"]), 0),
        max(int(counts["fail_rows"]), 0),
        max(int(counts["unverified_rows"]), 0),
    ]
    if sum(status_data) == 0:
        status_data = [1, 0, 0]

    status_pie = Pie()
    status_pie.x = 18
    status_pie.y = 18
    status_pie.width = 112
    status_pie.height = 112
    status_pie.data = status_data
    status_pie.labels = [
        f"PASS {status_data[0]}",
        f"FAIL {status_data[1]}",
        f"UNVERIFIED {status_data[2]}",
    ]
    status_pie.sideLabels = True
    status_pie.simpleLabels = False
    status_pie.slices.strokeColor = colors.white
    status_pie.slices.strokeWidth = 0.7
    status_pie.slices[0].fillColor = palette["pass"]
    status_pie.slices[1].fillColor = palette["fail"]
    status_pie.slices[2].fillColor = palette["warn"]
    status_drawing = Drawing(150, 142)
    status_drawing.add(status_pie)

    coverage_data = [
        max(int(counts["direct_operations"]), 0),
        max(int(counts["probe_operations"]), 0),
    ]
    coverage_chart = VerticalBarChart()
    coverage_chart.x = 18
    coverage_chart.y = 24
    coverage_chart.height = 100
    coverage_chart.width = 120
    coverage_chart.data = [coverage_data]
    coverage_chart.categoryAxis.categoryNames = ["DIRECT", "PROBE"]
    coverage_chart.categoryAxis.labels.boxAnchor = "n"
    coverage_chart.categoryAxis.labels.fontName = "Helvetica"
    coverage_chart.categoryAxis.labels.fontSize = 7
    coverage_chart.valueAxis.valueMin = 0
    max_coverage = max(coverage_data) if coverage_data else 1
    coverage_chart.valueAxis.valueMax = max(max_coverage + int(max_coverage * 0.2) + 1, 5)
    coverage_chart.valueAxis.valueStep = max(1, int(coverage_chart.valueAxis.valueMax / 4))
    coverage_chart.valueAxis.labels.fontName = "Helvetica"
    coverage_chart.valueAxis.labels.fontSize = 7
    coverage_chart.bars[0].fillColor = palette["accent"]
    coverage_chart.bars[0].strokeColor = colors.HexColor("#184E84")
    coverage_chart.barWidth = 30
    coverage_chart.barSpacing = 8
    coverage_chart.groupSpacing = 16
    coverage_drawing = Drawing(150, 142)
    coverage_drawing.add(coverage_chart)

    summary_data = [
        ["Metric", "Value"],
        ["OpenAPI operations", str(counts["openapi_operations"])],
        ["Directly covered operations", str(counts["direct_operations"])],
        ["Probe-validated operations", str(counts["probe_operations"])],
        ["PASS rows", str(counts["pass_rows"])],
        ["FAIL rows", str(counts["fail_rows"])],
        ["UNVERIFIED rows", str(counts["unverified_rows"])],
        ["Direct test cases", str(counts["direct_case_count"])],
    ]
    summary_table = Table(summary_data, colWidths=[170, 70], hAlign="LEFT")
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), palette["table_header"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8.3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [palette["table_alt"], colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, palette["table_grid"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ]
        )
    )

    summary_layout = Table(
        [
            [
                Paragraph("Executive Metrics", subheading_style),
                Paragraph("Result Mix", subheading_style),
                Paragraph("Coverage Split", subheading_style),
            ],
            [summary_table, status_drawing, coverage_drawing],
        ],
        colWidths=[260, 136, 136],
        hAlign="LEFT",
    )
    summary_layout.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story: list[Any] = [
        Spacer(1, 2),
        NextPageTemplate("content"),
        PageBreak(),
        Paragraph("1. Executive Summary", section_style),
        Paragraph(
            "This report combines direct pytest case evidence with swagger-wide probe validation to produce "
            "a complete operation-level API verification matrix.",
            body_style,
        ),
        Spacer(1, 6),
        summary_layout,
        Spacer(1, 12),
        Paragraph(
            f"Coverage quality: {counts['pass_rows']} PASS rows, {counts['fail_rows']} FAIL rows, "
            f"{counts['unverified_rows']} UNVERIFIED rows.",
            body_small_style,
        ),
        PageBreak(),
        Paragraph("2. Swagger-Wide Operation Matrix", section_style),
        Paragraph(
            "Each OpenAPI operation appears exactly once. DIRECT rows come from pytest evidence, "
            "while PROBE rows come from the contract-driven missing-endpoint scanner.",
            body_style,
        ),
    ]

    def _result_label(result: str) -> Paragraph:
        value = result.upper().strip()
        if value == "PASS":
            text = '<font color="#2F855A"><b>PASS</b></font>'
        elif value == "FAIL":
            text = '<font color="#C53030"><b>FAIL</b></font>'
        else:
            text = '<font color="#975A16"><b>UNVERIFIED</b></font>'
        return Paragraph(text, table_cell_center_style)

    matrix_table_data: list[list[Any]] = [["#", "Operation", "Mode", "Doc", "Obs", "Result", "Source"]]
    for idx, row in enumerate(matrix_rows, start=1):
        documented = ", ".join(str(code) for code in row["documented_statuses"]) if row["documented_statuses"] else "-"
        matrix_table_data.append(
            [
                Paragraph(str(idx), table_cell_center_style),
                Paragraph(str(row["operation"]), table_cell_style),
                Paragraph(str(row["mode"]), table_cell_center_style),
                Paragraph(documented, table_cell_center_style),
                Paragraph(str(row["observed_status"]), table_cell_center_style),
                _result_label(str(row["result"])),
                Paragraph(str(row["source"]), table_cell_style),
            ]
        )

    matrix_table = LongTable(
        matrix_table_data,
        repeatRows=1,
        hAlign="LEFT",
        colWidths=[24, 180, 48, 72, 42, 56, 109],
    )
    matrix_table_style: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), palette["table_header"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.1),
        ("GRID", (0, 0), (-1, -1), 0.33, palette["table_grid"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for idx, row in enumerate(matrix_rows, start=1):
        matrix_table_style.append(("BACKGROUND", (0, idx), (-1, idx), palette["table_alt"] if idx % 2 else colors.white))
        result_value = str(row["result"]).upper()
        if result_value == "FAIL":
            matrix_table_style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#FFF3F3")))
        elif result_value == "UNVERIFIED":
            matrix_table_style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#FFFBEF")))
    matrix_table.setStyle(TableStyle(matrix_table_style))
    story.append(matrix_table)

    story.extend(
        [
            PageBreak(),
            Paragraph("3. Direct Test Case Evidence", section_style),
            Paragraph(
                "Direct rows preserve test input, expected output, and actual output to maintain traceability "
                "for reviewer verification.",
                body_style,
            ),
        ]
    )

    case_table_data: list[list[Any]] = [["Case", "Test", "File", "Endpoint", "Input", "Expected", "Actual", "Status"]]
    for row in direct_case_rows:
        files = test_name_to_files.get(row["test_name"], [])
        file_text = ", ".join(files) if files else "-"
        case_table_data.append(
            [
                Paragraph(str(row["case_id"]), table_cell_style),
                Paragraph(str(row["test_name"]), table_cell_style),
                Paragraph(file_text, table_cell_style),
                Paragraph(str(row["endpoint"]), table_cell_style),
                Paragraph(_json_compact(row["input"], 85), table_cell_style),
                Paragraph(_json_compact(row["expected"], 85), table_cell_style),
                Paragraph(_json_compact(row["actual"], 85), table_cell_style),
                _result_label(str(row["status"])),
            ]
        )

    case_table = LongTable(
        case_table_data,
        repeatRows=1,
        hAlign="LEFT",
        colWidths=[42, 72, 72, 92, 64, 64, 64, 37],
    )
    case_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A497A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.32, palette["table_grid"]),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [palette["table_alt"], colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(case_table)

    story.extend(
        [
            PageBreak(),
            Paragraph("4. Mismatch and Historical Fixes", section_style),
            Paragraph(
                "Mismatch rows highlight expected vs actual status differences discovered by either direct tests "
                "or probe validation.",
                body_style,
            ),
        ]
    )

    mismatch_table_data: list[list[Any]] = [["Type", "Case", "Operation", "Expected", "Actual", "Explanation"]]
    if mismatch_rows:
        for row in mismatch_rows:
            expected = row["expected"]
            expected_text = ", ".join(str(code) for code in expected) if isinstance(expected, list) else str(expected)
            mismatch_table_data.append(
                [
                    Paragraph(str(row["type"]), table_cell_center_style),
                    Paragraph(str(row["case_id"]), table_cell_center_style),
                    Paragraph(str(row["operation"]), table_cell_style),
                    Paragraph(expected_text, table_cell_center_style),
                    Paragraph(str(row["actual"]), table_cell_center_style),
                    Paragraph(str(row["explanation"]), table_cell_style),
                ]
            )
    else:
        mismatch_table_data.append(
            [
                Paragraph("-", table_cell_center_style),
                Paragraph("-", table_cell_center_style),
                Paragraph("No mismatches found in current run.", table_cell_style),
                Paragraph("-", table_cell_center_style),
                Paragraph("-", table_cell_center_style),
                Paragraph("Current operation matrix is fully aligned.", table_cell_style),
            ]
        )

    mismatch_table = Table(mismatch_table_data, hAlign="LEFT", colWidths=[42, 42, 170, 90, 44, 143])
    mismatch_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7B2020")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#EACACA")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFF5F5"), colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(mismatch_table)

    story.extend(
        [
            Spacer(1, 8),
            Paragraph("Historical fixes from this sprint", subheading_style),
            Paragraph(
                "- FR-INT-003 payroll run: commit-capable DB override fixed mocked DB commit path in the integration flow.",
                body_small_style,
            ),
            Paragraph(
                "- AI support flow tests: keyword-compatible monkeypatch signatures fixed router call mismatch.",
                body_small_style,
            ),
            PageBreak(),
            Paragraph("5. Test File Inventory and Evidence Artifacts", section_style),
        ]
    )

    inventory_data: list[list[Any]] = [["#", "Test File", "Discovered Test Functions"]]
    for idx, row in enumerate(file_inventory, start=1):
        inventory_data.append(
            [
                Paragraph(str(idx), table_cell_center_style),
                Paragraph(str(row["file"]), table_cell_style),
                Paragraph(str(row["test_count"]), table_cell_center_style),
            ]
        )
    inventory_table = LongTable(inventory_data, repeatRows=1, hAlign="LEFT", colWidths=[28, 391, 112])
    inventory_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), palette["table_header"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.35, palette["table_grid"]),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [palette["table_alt"], colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(inventory_table)

    artifact_rows = [
        ["Artifact", "Purpose"],
        ["tests/reports/screenshots/phase_d/01_finance_rates_targeted.txt", "Finance and rates targeted run output"],
        ["tests/reports/screenshots/phase_d/02_warehouse_ops_targeted.txt", "Warehouse operations targeted run output"],
        ["tests/reports/screenshots/phase_d/03_logistics_tracking_targeted.txt", "Logistics and tracking targeted run output"],
        ["tests/reports/screenshots/phase_d/04_ai_support_flows_targeted.txt", "AI support flows targeted run output"],
        ["tests/reports/screenshots/phase_d/05_full_suite_regression.txt", "Full suite regression output"],
    ]
    artifact_table = Table(artifact_rows, colWidths=[330, 201], hAlign="LEFT")
    artifact_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A497A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [palette["table_alt"], colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.35, palette["table_grid"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(Spacer(1, 10))
    story.append(Paragraph("Terminal evidence artifacts", subheading_style))
    story.append(artifact_table)

    doc.build(story)


def build_report() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    openapi_operations = _load_openapi_operations()
    evidence_rows = _read_json(EVIDENCE_JSON, default=[])
    if not isinstance(evidence_rows, list):
        raise SystemExit("API_TEST_EVIDENCE.json must contain an array.")

    test_name_to_files, file_inventory = _discover_test_name_index()
    probe_rows = _load_probe_scan_rows()

    matrix_rows, direct_case_rows, mismatch_rows, counts = _build_matrix_rows(
        openapi_operations,
        evidence_rows,
        probe_rows,
    )

    OUTPUT_MATRIX_JSON.write_text(json.dumps(matrix_rows, indent=2), encoding="utf-8")
    _write_markdown(matrix_rows, direct_case_rows, mismatch_rows, counts, test_name_to_files, file_inventory)
    _build_pdf(matrix_rows, direct_case_rows, mismatch_rows, counts, test_name_to_files, file_inventory)


if __name__ == "__main__":
    build_report()
    print(f"Generated markdown report: {OUTPUT_MD}")
    print(f"Generated PDF report: {OUTPUT_PDF}")
    print(f"Generated matrix JSON: {OUTPUT_MATRIX_JSON}")
    print(f"Generated probe scan JSON: {OUTPUT_SCAN_JSON}")
