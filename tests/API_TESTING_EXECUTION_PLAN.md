# API Testing Execution Plan

Scope owner: Testing team

## Objective
Create five testing outcomes without changing frontend or backend application logic:
1. Swagger-compatible YAML API documentation.
2. Proper API test cases.
3. Input, expected output, and actual output for each test case.
4. A mismatch showcase where actual and expected differ.
5. Pytest test code submission for selected APIs.

Execution directive:
- Keep existing tests under `backend/tests/` unchanged (development regression tests).
- Create and maintain a separate test suite only under `tests/` at repo root.

## Hard Scope Boundaries
- Allowed: files under `tests/` only (test code, test reports, test utilities, test docs).
- Not allowed: any edits under `backend/*` (including `backend/tests/`, `backend/app/`, `backend/docs/`, configs, scripts, or any other backend path).
- Not allowed: any edits in frontend modules (for example `src/`, `driver-app/src/`).
- Existing app behavior is treated as system-under-test and must not be changed.

## Outcome-Based Deliverables

### Outcome 1: Swagger-Compatible YAML
Deliverable:
- `tests/api-docs/openapi.swagger.yaml`

Plan:
- Use current API source of truth: `backend/docs/openapi.json`.
- Convert JSON OpenAPI schema to YAML format.
- Validate YAML using Swagger/OpenAPI validator.

Acceptance criteria:
- YAML is syntactically valid.
- `openapi` version and paths are preserved.
- Validation command passes.

### Outcome 2: Proper API Test Cases
Deliverables:
- `tests/test-cases/API_TEST_CASE_MATRIX.md`
- `tests/integration/` (API behavior tests)
- `tests/contract/` (response contract tests)
- `tests/unit/` (test utilities/helpers for this suite)

Plan:
- Build a risk-based test matrix for a representative API set.
- Include at least:
  - Positive flow (2xx).
  - Input validation (4xx).
  - Auth/authorization behavior (401/403 where applicable).
  - Contract checks for critical response fields.
- Start with existing high-value endpoint groups:
  - Authentication (`/api/v1/auth/*`)
  - Orders (`/api/v1/orders*`)
  - Tracking and public geocoding endpoints
  - Health endpoint (`/health`)

Acceptance criteria:
- Each endpoint group has both happy-path and negative-path coverage.
- Test matrix includes case ID, endpoint, method, purpose, and priority.

### Outcome 3: Input + Expected + Actual Per Test Case
Deliverables:
- `tests/reports/API_TEST_EVIDENCE.md`
- Optional machine-readable companion: `tests/reports/API_TEST_EVIDENCE.json`

Plan:
- Standardize evidence rows per executed case with this template:

| Case ID | Endpoint | Input | Expected Output | Actual Output | Status |
|---|---|---|---|---|---|

- Input: request payload/query/path/headers used.
- Expected output: expected status code + key contract assertions.
- Actual output: real status code + response snapshot from pytest execution.

Acceptance criteria:
- Every executed case has all 3 fields captured (input, expected, actual).
- Evidence is traceable to a pytest test function name.

### Outcome 4: Mismatch Showcase (Expected vs Actual)
Deliverable:
- `tests/reports/API_MISMATCH_SHOWCASE.md`

Plan:
- Capture failing or intentionally exploratory cases where expected and actual differ.
- For each mismatch, document:
  - Endpoint + test case ID.
  - Input used.
  - Expected result.
  - Actual result.
  - Difference summary and likely root-cause category (contract mismatch, validation gap, auth issue, etc.).

Acceptance criteria:
- At least one concrete mismatch example is documented if discovered.
- If no mismatch is found, explicitly state "No mismatch observed in current scope".

### Outcome 5: Pytest Code Submission
Deliverables:
- `tests/integration/test_auth_api.py`
- `tests/integration/test_orders_api.py`
- `tests/integration/test_tracking_api.py`
- `tests/contract/test_auth_contract.py`
- `tests/contract/test_orders_contract.py`
- `tests/contract/test_public_endpoints_contract.py`
- `tests/unit/test_data_builders.py` (or equivalent helper-focused unit tests)

Plan:
- Build isolated pytest setup inside `tests/` (no changes to backend fixtures).
- Use black-box API testing style against running API (for example via base URL env var).
- Organize tests by folder intent: unit, integration, and contract.

Acceptance criteria:
- Tests run via pytest without changing app source code.
- Assertions cover status code and critical response fields.
- Tests are readable and traceable to test matrix IDs.

## Proposed Execution Phases

### Phase 1: Baseline and Scope Lock
- Confirm testing-only scope and target endpoint set.
- Freeze legacy `backend/tests/` as read-only for this initiative.
- Create directory structure only under `tests/` (`unit/`, `integration/`, `contract/`, `reports/`, `api-docs/`, `test-cases/`).

### Phase 2: API Documentation Artifact
- Generate `tests/api-docs/openapi.swagger.yaml` from current OpenAPI JSON.
- Validate and freeze as test-time contract artifact.

### Phase 3: Test Design
- Build `tests/test-cases/API_TEST_CASE_MATRIX.md`.
- Assign case IDs and map each case to planned pytest function names.

### Phase 4: Pytest Implementation
- Add pytest modules in `tests/integration/`, `tests/contract/`, and `tests/unit/`.
- Implement positive, negative, and contract checks.

### Phase 5: Execution and Evidence Capture
- Run pytest for contract suite.
- Generate `tests/reports/API_TEST_EVIDENCE.md` with input/expected/actual per case.

### Phase 6: Mismatch Reporting
- Create/update `tests/reports/API_MISMATCH_SHOWCASE.md`.
- Record real mismatches or explicitly state none found.

## Suggested Run Commands
Run from repository root:

```bash
pytest -q tests
```

Optional focused runs:

```bash
pytest -q tests/integration/test_auth_api.py
pytest -q tests/contract/test_orders_contract.py
```

If backend app imports are needed in tests, use:

```bash
PYTHONPATH=backend pytest -q tests
```

## Definition of Done
- All five outcomes are created as artifacts in test-related locations.
- No files under `backend/*` are modified.
- Existing `backend/tests/` remains untouched.
- Pytest code is submitted and executable.
- Evidence and mismatch reporting are complete and reviewable.