# Swagger-Wide API Test PDF Design

Date: 2026-04-18
Owner: Backend QA / API Validation
Status: Approved by user to proceed ("Go ahead")

## 1. Goal

Produce a single report package that is a one-stop view for API quality by combining:
1. Direct pytest evidence for updated APIs.
2. Swagger-wide execution visibility for all OpenAPI operations.
3. PDF deliverable suitable for reviewer submission.

Target outputs:
- tests/reports/SWAGGER_WIDE_API_TEST_REPORT.md
- tests/reports/SWAGGER_WIDE_API_TEST_REPORT.pdf
- tests/reports/SWAGGER_WIDE_OPERATION_MATRIX.json

## 2. Current Baseline

- OpenAPI surface: 303 operations (tests/api-docs/openapi.swagger.yaml)
- Direct evidence rows: 86 (tests/reports/API_TEST_EVIDENCE.json)
- Direct covered OpenAPI operations: ~45
- Remaining operations handled via probe scan and status validation.

## 3. Approach Options

### Option A: Test-Cases-Only PDF
- Build PDF strictly from direct pytest evidence.
- Pros: clean, high-confidence behavior coverage.
- Cons: not a true one-stop view for all Swagger operations.

### Option B: Swagger-Wide Probe-Only PDF
- Build PDF from operation probes for all endpoints.
- Pros: complete operation breadth.
- Cons: weaker depth (many are auth/validation probes, not full business-flow tests).

### Option C (Recommended): Hybrid One-Stop PDF
- Merge direct pytest evidence + swagger-wide probe coverage.
- Mark each operation as DIRECT or PROBE.
- Include mismatch section and fix notes.
- Pros: complete breadth + strong depth where tests exist.
- Cons: larger report and more data normalization work.

Recommendation: Option C.

## 4. Report Structure

1. Executive summary
   - Total operations, direct-covered operations, probe-covered operations, mismatches.
2. Swagger-wide operation matrix (all operations)
   - Operation, documented statuses, observed status, result, evidence mode.
3. Direct test case appendix
   - Case ID, test name, endpoint, input, expected, actual, status.
4. Mismatch and fix section
   - Current probe mismatches.
   - Historical expected!=actual fixes already resolved.
5. Test file inventory
   - Contract, integration, unit file list and discovered test function counts.
6. Terminal evidence section
   - Key run artifacts for reviewer traceability.

## 5. Data Sources

- OpenAPI source: tests/api-docs/openapi.swagger.yaml
- Direct evidence: tests/reports/API_TEST_EVIDENCE.json
- Existing mismatch narrative: tests/reports/PHASE_D_MISMATCH_NARRATIVE.md
- Probe scanner logic: tests/tools/scan_missing_endpoint_statuses.py
- Terminal evidence logs: tests/reports/screenshots/phase_d/*.txt

## 6. Normalization Rules

To avoid undercounting operations when evidence endpoints are combined strings:
- Extract methods via regex (GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS).
- Extract paths via regex (/api/v1/... or /health).
- Pair methods and paths by deterministic rules:
  1. One path + many methods -> map each method to that path.
  2. Equal number of methods and paths -> zip pair.
  3. Otherwise -> method x path cross product fallback.

## 7. Acceptance Criteria

1. Markdown and PDF are generated successfully.
2. Matrix includes every OpenAPI operation exactly once.
3. Every operation has a result row (DIRECT or PROBE) with status.
4. PDF includes input/expected/actual for direct showcased APIs.
5. PDF includes at least one expected!=actual case with explanation.
6. PDF references 4-5 terminal evidence artifacts.

## 8. Risks and Mitigations

- Risk: Probe results may over-represent 401 responses for auth-protected APIs.
  - Mitigation: Explicitly mark probe mode and keep direct pytest evidence separate.
- Risk: Some endpoints may return 404 while spec omits it.
  - Mitigation: Keep mismatch section as a quality gap list with recommended schema fixes.

## 9. Implementation Checklist

1. Build hybrid report generator script.
2. Generate operation matrix JSON.
3. Generate markdown report.
4. Render PDF report.
5. Verify output files and summarize mismatches.
