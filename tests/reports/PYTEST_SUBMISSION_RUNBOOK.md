# Pytest Submission Runbook

Date: 2026-04-17
Scope: Backend pytest package for Sprint 2 updated APIs

## 1. Environment

- OS: macOS/Linux shell compatible
- Python: use project virtualenv
- Working directory: repository root

## 2. Install and Setup

```bash
cd /Users/gauthamkrishna/Projects/QuadCore-Devs
python -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt
```

If project dependencies are already installed in .venv, skip installation.

## 3. Standard Test Commands

### Default backend pytest suite

```bash
cd /Users/gauthamkrishna/Projects/QuadCore-Devs
./.venv/bin/python -m pytest -q
```

Expected baseline from Phase D validation:
- 653 passed

### Key targeted API batches

```bash
./.venv/bin/python -m pytest tests/integration/test_finance_rates_api.py tests/contract/test_finance_rates_contract.py -q
./.venv/bin/python -m pytest tests/integration/test_warehouse_operations_api.py tests/contract/test_warehouse_operations_contract.py -q
./.venv/bin/python -m pytest tests/integration/test_logistics_tracking_api.py tests/contract/test_logistics_tracking_contract.py -q
./.venv/bin/python -m pytest tests/integration/test_ai_support_flows_api.py tests/contract/test_ai_support_flows_contract.py -q
```

## 4. Included Package Content

The submission package includes:

- pytest.ini
- tests/conftest.py
- tests/contract/
- tests/integration/
- tests/unit/
- tests/utils/
- tests/api-docs/openapi.swagger.yaml
- tests/reports/PHASE_D_TEST_MATRIX.md
- tests/reports/PHASE_D_MISMATCH_NARRATIVE.md
- tests/reports/PHASE_D_EVIDENCE_CHECKLIST.md
- tests/reports/API_TEST_EVIDENCE.json
- tests/reports/API_TEST_EVIDENCE.md
- tests/reports/API_MISMATCH_CASES.json
- tests/reports/API_MISMATCH_SHOWCASE.md
- tests/reports/screenshots/phase_d/

## 5. Build the Zip Package

```bash
cd /Users/gauthamkrishna/Projects/QuadCore-Devs
zip -r tests/reports/backend-pytest-submission-2026-04-17.zip \
  pytest.ini \
  tests/conftest.py \
  tests/contract \
  tests/integration \
  tests/unit \
  tests/utils \
  tests/api-docs/openapi.swagger.yaml \
  tests/reports/PHASE_D_TEST_MATRIX.md \
  tests/reports/PHASE_D_MISMATCH_NARRATIVE.md \
  tests/reports/PHASE_D_EVIDENCE_CHECKLIST.md \
  tests/reports/PYTEST_SUBMISSION_RUNBOOK.md \
  tests/reports/API_TEST_EVIDENCE.json \
  tests/reports/API_TEST_EVIDENCE.md \
  tests/reports/API_MISMATCH_CASES.json \
  tests/reports/API_MISMATCH_SHOWCASE.md \
  tests/reports/screenshots/phase_d \
  -x '*/__pycache__/*' '*.pyc'
```

## 6. Verify Zip Contents

```bash
cd /Users/gauthamkrishna/Projects/QuadCore-Devs
unzip -l tests/reports/backend-pytest-submission-2026-04-17.zip
```

Reference output from this Phase D run:
- 106 files in archive
- Approximate uncompressed size: 1,040,040 bytes

## 7. Traceability

- Plan and completion status: docs/plans/2026-04-17-backend-pytest-coverage-status-and-plan.md
- Matrix: tests/reports/PHASE_D_TEST_MATRIX.md
- Mismatch narrative: tests/reports/PHASE_D_MISMATCH_NARRATIVE.md
- Evidence checklist: tests/reports/PHASE_D_EVIDENCE_CHECKLIST.md
