# Phase D Backend API Test Matrix

Date: 2026-04-17
Scope: Backend pytest only (contract + integration + unit)
Evidence Source: tests/reports/API_TEST_EVIDENCE.json

## Summary

- Recorded API evidence cases: 86
- Unique API operations covered in evidence: 44
- Current case status: 86 PASS, 0 FAIL
- Full regression baseline: 653 passed in 10.21s

## Matrix Legend

- Positive: happy-path behavior validation
- Auth Negative: unauthorized or role guard behavior
- Validation Negative: schema, request-shape, or business-rule negative case
- Contract: OpenAPI path/shape assertions
- Flow: multi-endpoint business flow covered in integration tests

## Endpoint Group Matrix

| Group | Endpoints in Scope | Positive Cases | Auth Negative Cases | Validation/Business Negative Cases | Contract Coverage | Integration Flow Coverage |
|---|---|---|---|---|---|---|
| Authentication | /api/v1/auth/register, /login, /token, /me, /change-password, /send-otp, /verify-otp | AUTH-INT-001, AUTH-INT-003, AUTH-INT-004, AUTH-INT-007, AUTH-INT-008, AUTH-INT-009, AUTH-INT-010 | AUTH-INT-005, AUTH-INT-006 | AUTH-INT-002, AUTH-CON-004 | AUTH-CON-002, AUTH-CON-003, AUTH-CON-004 | Signup/login/token/profile/password/otp sequence in tests/integration/test_auth_api.py |
| Orders Core | /api/v1/orders, /api/v1/orders/{order_id}, /items, /delivery-otp/send, /track/{tracking_code} | ORD-INT-001, ORD-INT-002, ORD-INT-003, ORD-INT-004, ORD-INT-007, ORD-INT-008, ORD-INT-009 | ORD-INT-006 | ORD-INT-005, ORD-INT-010 | ORD-CON-002, ORD-CON-003, ORD-CON-004 | Order create -> list -> detail -> update -> item operations -> OTP/tracking in tests/integration/test_orders_api.py |
| Public and Health | /health, selected public tracking schema checks | PUB-CON-002 | PUB-CON-003 | - | PUB-CON-002, PUB-CON-003 | Public service sanity and schema checks |
| Tracking Legacy | /api/v1/tracking/drivers, /api/v1/tracking/orders/{order_id}/driver | TRK-INT-002, TRK-INT-003 | TRK-INT-001 | TRK-INT-004 (null driver assignment path) | Included via contract checks in tracking-related suites | Driver visibility and order-driver lookup coverage |
| Customer and Vendor | /api/v1/customer/settings, /customer/damage-reports, /vendor/settings, /vendor/support-tickets | CV-INT-001, CV-INT-004 | CV-INT-003, CV-INT-006 | CV-INT-002, CV-INT-005 | CV-CON-001, CV-CON-002 | Customer and vendor settings/support behavior in tests/integration/test_customer_vendor_api.py |
| Finance and Rates | /api/v1/finance/summary, /finance/payroll/run, /api/v1/rates | FR-INT-001, FR-INT-003, FR-INT-005, FR-INT-006 | FR-INT-002, FR-INT-008 | FR-INT-004, FR-INT-007 | FR-CON-001, FR-CON-002 | Finance summary + payroll + rates read/update flow in tests/integration/test_finance_rates_api.py |
| Warehouse Operations | /api/v1/warehouses/{warehouse_id}/operations/inbound, /inbound/schedule, /loading-docks | WHOPS-INT-001, WHOPS-INT-002, WHOPS-INT-005 | WHOPS-INT-003 | WHOPS-INT-004 | WHOPS-CON-001, WHOPS-CON-002 | Inbound overview -> schedule -> dock listing flow in tests/integration/test_warehouse_operations_api.py |
| Logistics and Tracking (Phase C) | /api/v1/logistics/alerts, /logistics/tasks, /api/v1/tracking/drivers, /tracking/orders/{order_id}/driver | LT-INT-001, LT-INT-004 | LT-INT-002, LT-INT-005 | LT-INT-003 | LT-CON-001, LT-CON-002 | Alerts and tracking flow with DB override in tests/integration/test_logistics_tracking_api.py |
| AI Support Flows (Phase C) | /api/v1/ai/contact-submissions/public, /contact-submissions, /ai/tickets | AISUP-INT-001, AISUP-INT-004, AISUP-INT-006 | AISUP-INT-002, AISUP-INT-005 | AISUP-INT-003 | AISUP-CON-001, AISUP-CON-002 | Public contact -> staff submissions/tickets flow in tests/integration/test_ai_support_flows_api.py |
| Sprint 2 AI, Damage, Dispatcher | /api/v1/ai/support/*, /api/v1/damage-reports*, /api/v1/orders/assignment-preview, /ai-driver-suggestions, /return-suggestions, /optimize-routes, /batch-assign | S2-INT-001, S2-INT-002, S2-INT-003, S2-INT-005, S2-INT-006, S2-INT-008, S2-INT-009, S2-INT-010, S2-INT-011 | S2-CON-001, S2-CON-002, S2-CON-003 | S2-INT-004, S2-INT-007 | Contract and parity checks in tests/contract/test_sprint2_updates_contract.py and tests/contract/test_openapi_backend_parity_contract.py | Support analytics + damage review + dispatcher optimization sequence in Sprint 2 integration suites |

## Supporting Test File Index

- tests/contract/test_openapi_backend_parity_contract.py
- tests/contract/test_sprint2_updates_contract.py
- tests/contract/test_customer_vendor_contract.py
- tests/contract/test_finance_rates_contract.py
- tests/contract/test_warehouse_operations_contract.py
- tests/contract/test_logistics_tracking_contract.py
- tests/contract/test_ai_support_flows_contract.py
- tests/integration/test_customer_vendor_api.py
- tests/integration/test_finance_rates_api.py
- tests/integration/test_warehouse_operations_api.py
- tests/integration/test_logistics_tracking_api.py
- tests/integration/test_ai_support_flows_api.py
- tests/integration/test_ai_support_api.py
- tests/integration/test_damage_review_api.py
- tests/integration/test_dispatcher_order_intelligence_api.py

## Residual Coverage Notes

- This matrix is endpoint-group and flow oriented for Sprint 2 and Phase C/Phase D deliverables.
- It does not claim 1:1 coverage for every OpenAPI path; parity is guarded by tests/contract/test_openapi_backend_parity_contract.py.
- Additional breadth can be expanded using tests/tools/scan_missing_endpoint_statuses.py if review scope requires endpoint-by-endpoint execution evidence.
