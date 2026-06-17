# Phase D Evidence Checklist

Date: 2026-04-17
Checklist Source: tests/proj-guide.md (Sprint 2 Do/Don't)

## A. Updated API Documentation

- [x] Updated Swagger-compatible YAML exists
  - tests/api-docs/openapi.swagger.yaml
- [x] Parity guard exists to prevent drift
  - tests/contract/test_openapi_backend_parity_contract.py

## B. Updated API Tests (pytest)

- [x] Contract coverage for updated domains
  - tests/contract/test_finance_rates_contract.py
  - tests/contract/test_warehouse_operations_contract.py
  - tests/contract/test_logistics_tracking_contract.py
  - tests/contract/test_ai_support_flows_contract.py
  - tests/contract/test_customer_vendor_contract.py
  - tests/contract/test_sprint2_updates_contract.py
- [x] Integration coverage for updated domains
  - tests/integration/test_finance_rates_api.py
  - tests/integration/test_warehouse_operations_api.py
  - tests/integration/test_logistics_tracking_api.py
  - tests/integration/test_ai_support_flows_api.py
  - tests/integration/test_ai_support_api.py
  - tests/integration/test_damage_review_api.py
  - tests/integration/test_dispatcher_order_intelligence_api.py

## C. Input/Expected/Actual Evidence

- [x] Evidence JSON present and updated
  - tests/reports/API_TEST_EVIDENCE.json
- [x] Human-readable evidence markdown regenerated
  - tests/reports/API_TEST_EVIDENCE.md
- [x] Mismatch summary markdown regenerated
  - tests/reports/API_MISMATCH_SHOWCASE.md

## D. Expected != Actual Narrative

- [x] Mismatch narrative document added with root cause and fix details
  - tests/reports/PHASE_D_MISMATCH_NARRATIVE.md

## E. Terminal Grabs (4-5 Key APIs)

- [x] Finance/Rates targeted batch terminal output
  - tests/reports/screenshots/phase_d/01_finance_rates_targeted.txt
- [x] Warehouse Operations targeted batch terminal output
  - tests/reports/screenshots/phase_d/02_warehouse_ops_targeted.txt
- [x] Logistics/Tracking targeted batch terminal output
  - tests/reports/screenshots/phase_d/03_logistics_tracking_targeted.txt
- [x] AI Support Flows targeted batch terminal output
  - tests/reports/screenshots/phase_d/04_ai_support_flows_targeted.txt
- [x] Full suite terminal output
  - tests/reports/screenshots/phase_d/05_full_suite_regression.txt

## F. Matrix and Packaging Artifacts

- [x] Formal test matrix created
  - tests/reports/PHASE_D_TEST_MATRIX.md
- [x] Packaging runbook and zip instructions created
  - tests/reports/PYTEST_SUBMISSION_RUNBOOK.md

## G. Final Suite Status

- [x] Full suite run captured
  - Result: 653 passed in 10.21s
  - Evidence: tests/reports/screenshots/phase_d/05_full_suite_regression.txt
