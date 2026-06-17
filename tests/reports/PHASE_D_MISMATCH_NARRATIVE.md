# Phase D Mismatch Narrative

Date: 2026-04-17
Scope: Backend pytest evidence and Sprint 2/Phase C completion

## Current Mismatch Status

- API mismatch artifact: tests/reports/API_MISMATCH_CASES.json
- Current recorded mismatches: 0
- Evidence markdown summary confirms no active mismatches in scope.

## Required Expected != Actual Showcase

The following real failures occurred during this run cycle and were fixed before final validation.

### 1) Finance payroll integration path failed before fix

- Area: tests/integration/test_finance_rates_api.py
- Case: FR-INT-003 (payroll run success)
- Expected: 200 with processed=1
- Actual before fix: test failure due missing async commit support on mocked DB dependency

Root cause:
- Endpoint logic commits through db.commit().
- Default mocked DB fixture did not provide commit() for this path.

Fix applied:
- Added a test-local dependency override using a commit-capable DB stub for the payroll success test.

Why this is correct:
- The override mirrors required DB behavior for the route without changing application runtime code.
- The fix is isolated to the test path that needs commit semantics.

Validation after fix:
- Targeted: 11 passed for finance/rates integration+contract batch
- Included in final full run: 653 passed

### 2) AI support flow monkeypatch signatures mismatched router invocation

- Areas:
  - tests/integration/test_ai_support_flows_api.py
  - tests/contract/test_ai_support_flows_contract.py
- Cases impacted before fix:
  - Public contact submission and tickets/submissions list flows (AISUP integration and contract cases)
- Expected: passing test flow with mocked services
- Actual before fix: TypeError from monkeypatched stubs not accepting keyword arguments used by route handlers (db=, data=)

Root cause:
- Route handlers call service methods with keyword args.
- Monkeypatched test stubs were positional-only in failing functions.

Fix applied:
- Updated monkeypatched async stubs to keyword-compatible signatures, including keyword-only parameters where needed.

Why this is correct:
- Test doubles now match the production call contract for service entrypoints.
- No application behavior changes; only test seam alignment.

Validation after fix:
- Targeted AI support flows rerun: 9 passed
- Included in final full run: 653 passed

## Final Validation Evidence

- tests/reports/screenshots/phase_d/01_finance_rates_targeted.txt
- tests/reports/screenshots/phase_d/02_warehouse_ops_targeted.txt
- tests/reports/screenshots/phase_d/03_logistics_tracking_targeted.txt
- tests/reports/screenshots/phase_d/04_ai_support_flows_targeted.txt
- tests/reports/screenshots/phase_d/05_full_suite_regression.txt

These logs provide terminal-grab evidence for key API groups and full-suite stability after fixes.
