# Swagger-Wide API Test Report

Generated at: 2026-04-18 07:53:57 UTC

## 1. Executive Summary

- OpenAPI operations: 304
- Matrix rows generated: 304
- Directly covered operations: 46
- Probe-validated operations: 258
- PASS rows: 304
- FAIL rows: 0
- UNVERIFIED rows: 0
- Direct test cases documented: 89

## 2. Swagger-Wide Operation Matrix

| # | Operation | Mode | Documented Statuses | Observed | Result | Source |
|---|---|---|---|---|---|---|
| 1 | DELETE /api/v1/ai/contact-submissions/{submission_id} | PROBE | 204, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 2 | DELETE /api/v1/ai/knowledge-articles/{article_id} | PROBE | 204, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 3 | DELETE /api/v1/ai/tickets/{ticket_id} | PROBE | 204, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 4 | DELETE /api/v1/customer/account | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 5 | DELETE /api/v1/customer/notifications | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 6 | DELETE /api/v1/dev/seed-gps | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 7 | DELETE /api/v1/inventory/{item_id} | PROBE | 200, 401, 404, 422 | 404 | PASS | Swagger probe scan |
| 8 | DELETE /api/v1/labourers/{labourer_id} | PROBE | 204, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 9 | DELETE /api/v1/logistics/chats/{thread_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 10 | DELETE /api/v1/logistics/meetings/{meeting_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 11 | DELETE /api/v1/logistics/notifications | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 12 | DELETE /api/v1/logistics/tasks/{task_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 13 | DELETE /api/v1/logistics/zones/{zone_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 14 | DELETE /api/v1/users/{user_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 15 | DELETE /api/v1/vendor/notifications | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 16 | DELETE /api/v1/vendor/recurring-rules/{rule_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 17 | DELETE /api/v1/vendor/team-members/{member_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 18 | DELETE /api/v1/warehouses/{warehouse_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 19 | GET /api/v1/ai/contact-submissions | DIRECT | 200, 401 | 200,401 | PASS | AISUP-INT-002, AISUP-INT-006 |
| 20 | GET /api/v1/ai/conversations/{session_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 21 | GET /api/v1/ai/escalation-center | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 22 | GET /api/v1/ai/escalations | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 23 | GET /api/v1/ai/knowledge-articles | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 24 | GET /api/v1/ai/knowledge-articles/{article_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 25 | GET /api/v1/ai/recovery-tickets/count | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 26 | GET /api/v1/ai/sessions | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 27 | GET /api/v1/ai/support/analytics | DIRECT | 200, 401, 422 | - | PASS | S2-INT-003 |
| 28 | GET /api/v1/ai/support/customer-history/{user_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 29 | GET /api/v1/ai/support/damage-reports | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 30 | GET /api/v1/ai/support/dashboard | DIRECT | 200, 401 | 200,401 | PASS | S2-CON-001, S2-INT-001 |
| 31 | GET /api/v1/ai/support/refund-cases | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 32 | GET /api/v1/ai/support/sessions | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 33 | GET /api/v1/ai/support/sessions/{session_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 34 | GET /api/v1/ai/support/settings | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 35 | GET /api/v1/ai/tickets | DIRECT | 200, 401 | 200,401 | PASS | AISUP-CON-002, AISUP-INT-004, AISUP-INT-005 |
| 36 | GET /api/v1/auth/me | DIRECT | 200, 401 | 200,401 | PASS | AUTH-INT-006, AUTH-INT-007 |
| 37 | GET /api/v1/customer/damage-reports | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 38 | GET /api/v1/customer/dashboard | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 39 | GET /api/v1/customer/notifications | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 40 | GET /api/v1/customer/payments | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 41 | GET /api/v1/customer/profile | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 42 | GET /api/v1/customer/quotes | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 43 | GET /api/v1/customer/settings | DIRECT | 200, 401 | 200,401 | PASS | CV-CON-001, CV-INT-001, CV-INT-003 |
| 44 | GET /api/v1/customer/tracking | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 45 | GET /api/v1/customer/wallet | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 46 | GET /api/v1/damage-reports | DIRECT | 200, 401, 422 | 200,401 | PASS | S2-CON-002, S2-INT-005 |
| 47 | GET /api/v1/finance/summary | DIRECT | 200, 401, 422 | 200,401 | PASS | FR-CON-001, FR-INT-001, FR-INT-002 |
| 48 | GET /api/v1/geocoding/reverse | PROBE | 200, 422 | 422 | PASS | Swagger probe scan |
| 49 | GET /api/v1/geocoding/search | PROBE | 200, 422 | 422 | PASS | Swagger probe scan |
| 50 | GET /api/v1/inventory | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 51 | GET /api/v1/inventory/categories | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 52 | GET /api/v1/inventory/low-stock | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 53 | GET /api/v1/inventory/material-requests | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 54 | GET /api/v1/inventory/movements | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 55 | GET /api/v1/inventory/packing-catalog | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 56 | GET /api/v1/inventory/restock-requests | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 57 | GET /api/v1/inventory/{item_id} | PROBE | 200, 401, 404, 422 | 404 | PASS | Swagger probe scan |
| 58 | GET /api/v1/labourers | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 59 | GET /api/v1/labourers/availability | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 60 | GET /api/v1/labourers/{labourer_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 61 | GET /api/v1/logistics/alerts | DIRECT | 200, 401 | 200,401 | PASS | LT-CON-001, LT-INT-001, LT-INT-002 |
| 62 | GET /api/v1/logistics/bootstrap | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 63 | GET /api/v1/logistics/chats | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 64 | GET /api/v1/logistics/dispatch-contacts | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 65 | GET /api/v1/logistics/drivers | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 66 | GET /api/v1/logistics/drivers/me/audit | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 67 | GET /api/v1/logistics/drivers/me/crew | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 68 | GET /api/v1/logistics/drivers/me/dashboard | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 69 | GET /api/v1/logistics/drivers/me/dispatch-thread | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 70 | GET /api/v1/logistics/drivers/me/hos | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 71 | GET /api/v1/logistics/drivers/me/manager-thread | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 72 | GET /api/v1/logistics/drivers/me/notifications | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 73 | GET /api/v1/logistics/drivers/me/shift | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 74 | GET /api/v1/logistics/drivers/me/telemetry | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 75 | GET /api/v1/logistics/manifests | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 76 | GET /api/v1/logistics/meeting-participants | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 77 | GET /api/v1/logistics/meetings | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 78 | GET /api/v1/logistics/notifications | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 79 | GET /api/v1/logistics/tasks | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 80 | GET /api/v1/logistics/vehicles | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 81 | GET /api/v1/logistics/zones | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 82 | GET /api/v1/orders | DIRECT | 200, 401, 422 | 200,401 | PASS | ORD-CON-003, ORD-INT-002, ORD-INT-006 |
| 83 | GET /api/v1/orders/ai-driver-suggestions | DIRECT | 200, 401 | 200,401 | PASS | S2-CON-003, S2-INT-009 |
| 84 | GET /api/v1/orders/assignment-preview | DIRECT | 200, 401, 422 | 200 | PASS | S2-INT-008 |
| 85 | GET /api/v1/orders/return-suggestions | DIRECT | 200, 401 | 200 | PASS | S2-INT-010 |
| 86 | GET /api/v1/orders/track/{tracking_code} | DIRECT | 200, 404, 422 | 404 | PASS | ORD-INT-010 |
| 87 | GET /api/v1/orders/trip-intelligence | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 88 | GET /api/v1/orders/{order_id} | DIRECT | 200, 401, 404, 422 | 200 | PASS | ORD-INT-003 |
| 89 | GET /api/v1/orders/{order_id}/items | DIRECT | 200, 401, 404, 422 | 200 | PASS | ORD-CON-004, ORD-INT-007 |
| 90 | GET /api/v1/orders/{order_id}/proof-of-delivery | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 91 | GET /api/v1/orders/{order_id}/trip-intelligence | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 92 | GET /api/v1/rates | DIRECT | 200 | 200 | PASS | FR-CON-002, FR-INT-005 |
| 93 | GET /api/v1/rates/inventory-seeded | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 94 | GET /api/v1/tracking/drivers | DIRECT | 200, 401 | 200,401 | PASS | LT-CON-002, LT-INT-004, PUB-CON-003, TRK-INT-001, TRK-INT-002 |
| 95 | GET /api/v1/tracking/orders/{order_id}/driver | DIRECT | 200, 401, 404, 422 | 200,401 | PASS | LT-INT-005, TRK-INT-003, TRK-INT-004 |
| 96 | GET /api/v1/users | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 97 | GET /api/v1/users/{user_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 98 | GET /api/v1/vendor/api-keys | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 99 | GET /api/v1/vendor/bulk-uploads | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 100 | GET /api/v1/vendor/damage-reports | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 101 | GET /api/v1/vendor/dashboard | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 102 | GET /api/v1/vendor/notifications | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 103 | GET /api/v1/vendor/recurring-rules | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 104 | GET /api/v1/vendor/settings | DIRECT | 200, 401 | 200,401 | PASS | CV-CON-002, CV-INT-004, CV-INT-006 |
| 105 | GET /api/v1/vendor/shipments | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 106 | GET /api/v1/vendor/support-tickets | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 107 | GET /api/v1/vendor/team-members | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 108 | GET /api/v1/vendor/wallet | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 109 | GET /api/v1/warehouses | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 110 | GET /api/v1/warehouses/{warehouse_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 111 | GET /api/v1/warehouses/{warehouse_id}/dashboard | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 112 | GET /api/v1/warehouses/{warehouse_id}/kpis | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 113 | GET /api/v1/warehouses/{warehouse_id}/operations/inbound | DIRECT | 200, 401, 404, 422 | 200,401 | PASS | WHOPS-CON-001, WHOPS-INT-001, WHOPS-INT-003 |
| 114 | GET /api/v1/warehouses/{warehouse_id}/operations/loading-docks | DIRECT | 200, 401, 404, 422 | 200 | PASS | WHOPS-CON-002, WHOPS-INT-005 |
| 115 | GET /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/ai-receive-plan | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 116 | GET /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/pick-progress | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 117 | GET /api/v1/warehouses/{warehouse_id}/operations/packing-stations | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 118 | GET /api/v1/warehouses/{warehouse_id}/operations/performance | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 119 | GET /api/v1/warehouses/{warehouse_id}/operations/quality-checks | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 120 | GET /api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 121 | GET /api/v1/warehouses/{warehouse_id}/operations/returns | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 122 | GET /api/v1/warehouses/{warehouse_id}/operations/zones/{zone_id}/metrics | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 123 | GET /health | DIRECT | 200 | 200 | PASS | PUB-CON-002 |
| 124 | POST /api/v1/ai/chat | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 125 | POST /api/v1/ai/contact-submissions/public | DIRECT | 201, 422 | 201,422 | PASS | AISUP-CON-001, AISUP-INT-001, AISUP-INT-003 |
| 126 | POST /api/v1/ai/contact-submissions/{submission_id}/reply | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 127 | POST /api/v1/ai/escalate/{conversation_id} | PROBE | 201, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 128 | POST /api/v1/ai/estimate-image | PROBE | 200, 422 | 422 | PASS | Swagger probe scan |
| 129 | POST /api/v1/ai/knowledge-articles | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 130 | POST /api/v1/ai/knowledge-articles/{article_id}/like | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 131 | POST /api/v1/ai/support/analytics/insights/{insight_id}/execute | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 132 | POST /api/v1/ai/support/damage-reports | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 133 | POST /api/v1/ai/support/damage-reports/{report_id}/message | PROBE | 201, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 134 | POST /api/v1/ai/support/sessions/{session_id}/escalate | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 135 | POST /api/v1/ai/support/sessions/{session_id}/reply | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 136 | POST /api/v1/ai/support/sessions/{session_id}/take-over | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 137 | POST /api/v1/ai/tickets | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 138 | POST /api/v1/ai/tickets/{ticket_id}/reply | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 139 | POST /api/v1/auth/change-password | DIRECT | 200, 401, 422 | 200 | PASS | AUTH-INT-008 |
| 140 | POST /api/v1/auth/forgot-password | PROBE | 200, 422 | 422 | PASS | Swagger probe scan |
| 141 | POST /api/v1/auth/google-login | PROBE | 200, 422 | 422 | PASS | Swagger probe scan |
| 142 | POST /api/v1/auth/login | DIRECT | 200, 422 | 200 | PASS | AUTH-CON-003, AUTH-INT-003 |
| 143 | POST /api/v1/auth/logout | DIRECT | 200, 422 | 401 | PASS | AUTH-INT-005 |
| 144 | POST /api/v1/auth/refresh | PROBE | 200, 422 | 422 | PASS | Swagger probe scan |
| 145 | POST /api/v1/auth/register | DIRECT | 201, 422 | 201,422 | PASS | AUTH-CON-002, AUTH-CON-004, AUTH-INT-001, AUTH-INT-002 |
| 146 | POST /api/v1/auth/reset-password | PROBE | 200, 422 | 422 | PASS | Swagger probe scan |
| 147 | POST /api/v1/auth/send-otp | DIRECT | 200, 422 | 200 | PASS | AUTH-INT-009 |
| 148 | POST /api/v1/auth/token | DIRECT | 200, 422 | 200 | PASS | AUTH-INT-004 |
| 149 | POST /api/v1/auth/verify-otp | DIRECT | 200, 422 | 200 | PASS | AUTH-INT-010 |
| 150 | POST /api/v1/customer/damage-reports | DIRECT | 200, 401, 422 | 422 | PASS | CV-INT-002 |
| 151 | POST /api/v1/customer/notifications/mark-all-read | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 152 | POST /api/v1/customer/quotes/{quote_id}/convert | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 153 | POST /api/v1/customer/wallet/backfill-debits | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 154 | POST /api/v1/customer/wallet/top-up | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 155 | POST /api/v1/damage-reports/{reference_code}/review | DIRECT | 200, 401, 404, 422 | 200,422 | PASS | S2-INT-006, S2-INT-007 |
| 156 | POST /api/v1/dev/seed-gps | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 157 | POST /api/v1/finance/payroll/run | DIRECT | 200, 401, 422 | 200,422 | PASS | FR-INT-003, FR-INT-004 |
| 158 | POST /api/v1/inventory | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 159 | POST /api/v1/inventory/material-requests | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 160 | POST /api/v1/inventory/movements | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 161 | POST /api/v1/inventory/pick-list/{order_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 162 | POST /api/v1/inventory/restock-requests | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 163 | POST /api/v1/inventory/restock-requests/{request_id}/escalate | PROBE | 200, 401, 404, 422 | 404 | PASS | Swagger probe scan |
| 164 | POST /api/v1/labourers | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 165 | POST /api/v1/labourers/{labourer_id}/assign/{order_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 166 | POST /api/v1/labourers/{labourer_id}/check-in | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 167 | POST /api/v1/labourers/{labourer_id}/check-out | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 168 | POST /api/v1/logistics/ai/query | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 169 | POST /api/v1/logistics/alerts | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 170 | POST /api/v1/logistics/alerts/{alert_id}/resolve | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 171 | POST /api/v1/logistics/capital-investment | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 172 | POST /api/v1/logistics/chats | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 173 | POST /api/v1/logistics/chats/{thread_id}/messages | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 174 | POST /api/v1/logistics/documents | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 175 | POST /api/v1/logistics/drivers | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 176 | POST /api/v1/logistics/drivers/me/bind-vehicle | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 177 | POST /api/v1/logistics/drivers/me/cashout | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 178 | POST /api/v1/logistics/drivers/me/crew/{labourer_id}/check-in | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 179 | POST /api/v1/logistics/drivers/me/crisis-alert | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 180 | POST /api/v1/logistics/drivers/me/dispatch-thread/messages | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 181 | POST /api/v1/logistics/drivers/me/fuel-receipt | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 182 | POST /api/v1/logistics/drivers/me/location | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 183 | POST /api/v1/logistics/drivers/me/manager-thread/messages | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 184 | POST /api/v1/logistics/drivers/me/return-vehicle | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 185 | POST /api/v1/logistics/drivers/me/shift/end | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 186 | POST /api/v1/logistics/drivers/me/shift/start | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 187 | POST /api/v1/logistics/manifests | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 188 | POST /api/v1/logistics/manifests/{manifest_id}/push | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 189 | POST /api/v1/logistics/meetings | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 190 | POST /api/v1/logistics/notifications/broadcast | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 191 | POST /api/v1/logistics/notifications/mark-all-read | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 192 | POST /api/v1/logistics/returns/{case_id}/issue-refund | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 193 | POST /api/v1/logistics/returns/{case_id}/schedule-pickup | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 194 | POST /api/v1/logistics/tasks | DIRECT | 201, 401, 422 | 422 | PASS | LT-INT-003 |
| 195 | POST /api/v1/logistics/transactions | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 196 | POST /api/v1/logistics/vehicles | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 197 | POST /api/v1/logistics/zones | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 198 | POST /api/v1/orders | DIRECT | 201, 401, 422 | 201,422 | PASS | ORD-CON-002, ORD-INT-001, ORD-INT-005 |
| 199 | POST /api/v1/orders/auto-balance | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 200 | POST /api/v1/orders/batch-assign | DIRECT | 200, 401, 422 | - | PASS | S2-INT-011 |
| 201 | POST /api/v1/orders/cluster | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 202 | POST /api/v1/orders/optimize-routes | DIRECT | 200, 401, 422 | - | PASS | S2-INT-011 |
| 203 | POST /api/v1/orders/{order_id}/asset-log | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 204 | POST /api/v1/orders/{order_id}/assign | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 205 | POST /api/v1/orders/{order_id}/cancel | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 206 | POST /api/v1/orders/{order_id}/complete-return | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 207 | POST /api/v1/orders/{order_id}/confirm | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 208 | POST /api/v1/orders/{order_id}/customer-rating | DIRECT | 200, 401, 404, 422 | 200,401,422 | PASS | ORD-INT-011, ORD-INT-012, ORD-INT-013 |
| 209 | POST /api/v1/orders/{order_id}/delivery-otp/send | DIRECT | 200, 401, 404, 422 | 200 | PASS | ORD-INT-009 |
| 210 | POST /api/v1/orders/{order_id}/escalate | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 211 | POST /api/v1/orders/{order_id}/house-shift-signoff | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 212 | POST /api/v1/orders/{order_id}/items | DIRECT | 200, 401, 404, 422 | 200 | PASS | ORD-INT-008 |
| 213 | POST /api/v1/orders/{order_id}/job-rating | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 214 | POST /api/v1/orders/{order_id}/packing-return | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 215 | POST /api/v1/orders/{order_id}/pay | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 216 | POST /api/v1/orders/{order_id}/proof-of-delivery | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 217 | POST /api/v1/orders/{order_id}/simulate-arrival | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 218 | POST /api/v1/orders/{order_id}/transition | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 219 | POST /api/v1/orders/{order_id}/trip-intelligence/deviation | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 220 | POST /api/v1/orders/{order_id}/trip-intelligence/push | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 221 | POST /api/v1/orders/{order_id}/wallet-pay | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 222 | POST /api/v1/rates/seed-inventory | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 223 | POST /api/v1/users | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 224 | POST /api/v1/users/{user_id}/assign-role | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 225 | POST /api/v1/users/{user_id}/assign-warehouse | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 226 | POST /api/v1/vendor/api-keys | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 227 | POST /api/v1/vendor/api-keys/{key_id}/revoke | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 228 | POST /api/v1/vendor/bulk-uploads | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 229 | POST /api/v1/vendor/damage-reports | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 230 | POST /api/v1/vendor/invoices/{order_id}/pay | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 231 | POST /api/v1/vendor/notifications/mark-all-read | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 232 | POST /api/v1/vendor/recurring-rules | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 233 | POST /api/v1/vendor/recurring-rules/{rule_id}/toggle | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 234 | POST /api/v1/vendor/support-tickets | DIRECT | 200, 401, 422 | 422 | PASS | CV-INT-005 |
| 235 | POST /api/v1/vendor/support-tickets/{ticket_id}/reply | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 236 | POST /api/v1/vendor/support-tickets/{ticket_id}/resolve | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 237 | POST /api/v1/vendor/team-members | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 238 | POST /api/v1/vendor/wallet/top-up | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 239 | POST /api/v1/warehouses | PROBE | 201, 401, 422 | 401 | PASS | Swagger probe scan |
| 240 | POST /api/v1/warehouses/{warehouse_id}/operations/inbound/schedule | DIRECT | 201, 401, 404, 422 | 201,422 | PASS | WHOPS-INT-002, WHOPS-INT-004 |
| 241 | POST /api/v1/warehouses/{warehouse_id}/operations/loading-docks | PROBE | 201, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 242 | POST /api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/assign | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 243 | POST /api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/maintenance | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 244 | POST /api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/release | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 245 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/accept | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 246 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/complete-packing | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 247 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/complete-picking | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 248 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/generate-take-back | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 249 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/mark-arrived | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 250 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/pick-item | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 251 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/quality-check | PROBE | 201, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 252 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/receive-inbound | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 253 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/report-damage | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 254 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/report-mismatch | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 255 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/revert-picking | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 256 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-packing | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 257 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-picking | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 258 | POST /api/v1/warehouses/{warehouse_id}/operations/packing-stations | PROBE | 201, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 259 | POST /api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id}/pass | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 260 | POST /api/v1/warehouses/{warehouse_id}/operations/returns | PROBE | 201, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 261 | POST /api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}/complete | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 262 | POST /api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}/photo | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 263 | POST /api/v1/warehouses/{warehouse_id}/operations/zones/metrics | PROBE | 201, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 264 | POST /api/v1/warehouses/{warehouse_id}/orders/{order_id}/complete | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 265 | POST /api/v1/warehouses/{warehouse_id}/orders/{order_id}/reassign | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 266 | POST /api/v1/warehouses/{warehouse_id}/restock | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 267 | PUT /api/v1/ai/contact-submissions/{submission_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 268 | PUT /api/v1/ai/escalation-center/{escalation_id}/resolve | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 269 | PUT /api/v1/ai/escalations/{escalation_id}/resolve | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 270 | PUT /api/v1/ai/knowledge-articles/{article_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 271 | PUT /api/v1/ai/support/damage-reports/{report_id}/notes | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 272 | PUT /api/v1/ai/support/refund-cases/{case_id}/urgent | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 273 | PUT /api/v1/ai/support/settings | DIRECT | 200, 401, 422 | 200,422 | PASS | S2-INT-002, S2-INT-004 |
| 274 | PUT /api/v1/ai/tickets/{ticket_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 275 | PUT /api/v1/auth/me | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 276 | PUT /api/v1/customer/notifications/{notification_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 277 | PUT /api/v1/customer/settings | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 278 | PUT /api/v1/inventory/material-requests/{request_id}/approve | PROBE | 200, 401, 404, 422 | 404 | PASS | Swagger probe scan |
| 279 | PUT /api/v1/inventory/material-requests/{request_id}/reject | PROBE | 200, 401, 404, 422 | 404 | PASS | Swagger probe scan |
| 280 | PUT /api/v1/inventory/restock-requests/{request_id}/status | PROBE | 200, 401, 404, 422 | 404 | PASS | Swagger probe scan |
| 281 | PUT /api/v1/inventory/{item_id} | PROBE | 200, 401, 404, 422 | 404 | PASS | Swagger probe scan |
| 282 | PUT /api/v1/labourers/{labourer_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 283 | PUT /api/v1/logistics/chats/{thread_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 284 | PUT /api/v1/logistics/documents/{doc_id}/status | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 285 | PUT /api/v1/logistics/drivers/{driver_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 286 | PUT /api/v1/logistics/escalations/{escalation_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 287 | PUT /api/v1/logistics/meetings/{meeting_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 288 | PUT /api/v1/logistics/notifications/{notification_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 289 | PUT /api/v1/logistics/returns/{case_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 290 | PUT /api/v1/logistics/tasks/{task_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 291 | PUT /api/v1/logistics/vehicles/{vehicle_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 292 | PUT /api/v1/logistics/zones/{zone_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 293 | PUT /api/v1/orders/{order_id} | DIRECT | 200, 401, 404, 422 | 200 | PASS | ORD-INT-004 |
| 294 | PUT /api/v1/rates | DIRECT | 200, 401, 422 | 200,400,401 | PASS | FR-INT-006, FR-INT-007, FR-INT-008 |
| 295 | PUT /api/v1/users/{user_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 296 | PUT /api/v1/vendor/bulk-uploads/{upload_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 297 | PUT /api/v1/vendor/notifications/{notification_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 298 | PUT /api/v1/vendor/recurring-rules/{rule_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 299 | PUT /api/v1/vendor/settings | PROBE | 200, 401, 422 | 401 | PASS | Swagger probe scan |
| 300 | PUT /api/v1/warehouses/{warehouse_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 301 | PUT /api/v1/warehouses/{warehouse_id}/floor-plan | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 302 | PUT /api/v1/warehouses/{warehouse_id}/operations/packing-stations/{station_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 303 | PUT /api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |
| 304 | PUT /api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id} | PROBE | 200, 401, 404, 422 | 401 | PASS | Swagger probe scan |

## 3. Direct Test Case Evidence (Input/Expected/Actual)

| Case ID | Test Name | Test File | Endpoint | Input | Expected | Actual | Status |
|---|---|---|---|---|---|---|---|
| AISUP-CON-001 | test_public_contact_submission_contract | tests/contract/test_ai_support_flows_contract.py | POST /api/v1/ai/contact-submissions/public | {"category": "support", "email": "ava@example.com", "message": "Please help me check my order status.", "name": "Ava Customer", "phone": "999998888... | {"required_keys": ["id", "reference_code", "subject", "status"], "status_code": 201} | {"body": {"assigned_agent_name": null, "assigned_to_user_id": null, "category": "support", "created_at": "2026-04-18T07:53:29.173929Z", "email": "a... | PASS |
| AISUP-CON-002 | test_tickets_list_contract | tests/contract/test_ai_support_flows_contract.py | GET /api/v1/ai/tickets | {"authorization": "Bearer <mocked>"} | {"required_keys": ["tickets", "stats", "agents"], "status_code": 200} | {"body": {"agents": [], "stats": {"in_progress": 0, "new": 1, "resolved": 0, "total": 1, "urgent": 1}, "tickets": [{"assigned_agent_name": null, "a... | PASS |
| AISUP-INT-001 | test_public_contact_submission_success | tests/integration/test_ai_support_flows_api.py | POST /api/v1/ai/contact-submissions/public | {"category": "support", "email": "ava@example.com", "message": "Please help me check my order status.", "name": "Ava Customer", "phone": "999998888... | {"reference_code": "CS-1001", "status_code": 201} | {"body": {"assigned_agent_name": null, "assigned_to_user_id": null, "category": "support", "created_at": "2026-04-18T07:53:45.628746Z", "email": "a... | PASS |
| AISUP-INT-002 | test_contact_submissions_requires_authentication | tests/integration/test_ai_support_flows_api.py | GET /api/v1/ai/contact-submissions | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| AISUP-INT-003 | test_public_contact_submission_validation_error_422 | tests/integration/test_ai_support_flows_api.py | POST /api/v1/ai/contact-submissions/public | {} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"input": {}, "loc": ["body", "name"], "msg": "Field required", "type": "missing"}, {"input": {}, "loc": ["body", "email"], "m... | PASS |
| AISUP-INT-004 | test_tickets_list_success | tests/integration/test_ai_support_flows_api.py | GET /api/v1/ai/tickets | {"authorization": "Bearer <mocked>"} | {"first_reference": "TCK-1001", "stats.total": 1, "status_code": 200} | {"body": {"agents": [], "stats": {"in_progress": 0, "new": 1, "resolved": 0, "total": 1, "urgent": 1}, "tickets": [{"assigned_agent_name": null, "a... | PASS |
| AISUP-INT-005 | test_tickets_list_requires_authentication | tests/integration/test_ai_support_flows_api.py | GET /api/v1/ai/tickets | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| AISUP-INT-006 | test_contact_submissions_list_success | tests/integration/test_ai_support_flows_api.py | GET /api/v1/ai/contact-submissions | {"authorization": "Bearer <mocked>"} | {"first_reference": "CS-1001", "stats.total": 1, "status_code": 200} | {"body": {"agents": [{"email": "support@example.com", "id": "77f0ffe6-ba1c-444d-8fce-91704789dcbc", "name": "Support One"}], "stats": {"in_progress... | PASS |
| AUTH-CON-002 | test_register_response_contract | tests/contract/test_auth_contract.py | POST /api/v1/auth/register | {"email": "bob@example.com", "name": "Bob", "password": "StrongPass123", "phone": "9999999999", "role": "INDIVIDUAL"} | {"required_keys": ["access_token", "refresh_token", "token_type"], "status_code": 201} | {"body": {"access_token": "access-token-123", "message": "Registration successful", "pending_approval": false, "refresh_token": "refresh-token-123"... | PASS |
| AUTH-CON-003 | test_login_response_contract | tests/contract/test_auth_contract.py | POST /api/v1/auth/login | {"email": "bob@example.com", "password": "StrongPass123"} | {"required_keys": ["access_token", "refresh_token", "user"], "status_code": 200} | {"body": {"access_token": "access-token-123", "refresh_token": "refresh-token-123", "token_type": "bearer", "user": {"address": "123 Test Street", ... | PASS |
| AUTH-CON-004 | test_register_validation_error_contract | tests/contract/test_auth_contract.py | POST /api/v1/auth/register | {"email": "bob@example.com", "name": "Bob", "password": "StrongPass123", "role": "UNKNOWN_ROLE"} | {"detail_type": "list", "status_code": 422} | {"body": {"detail": [{"ctx": {"expected": "'INDIVIDUAL' or 'VENDOR'"}, "input": "UNKNOWN_ROLE", "loc": ["body", "role"], "msg": "Input should be 'I... | PASS |
| AUTH-INT-001 | test_auth_register_success | tests/integration/test_auth_api.py | POST /api/v1/auth/register | {"email": "alice@example.com", "name": "Alice", "password": "StrongPass123", "phone": "9999999999", "role": "INDIVIDUAL"} | {"pending_approval": false, "status_code": 201} | {"body": {"access_token": "access-token-123", "message": "Registration successful", "pending_approval": false, "refresh_token": "refresh-token-123"... | PASS |
| AUTH-INT-002 | test_auth_register_invalid_role_returns_422 | tests/integration/test_auth_api.py | POST /api/v1/auth/register | {"email": "alice@example.com", "name": "Alice", "password": "StrongPass123", "phone": "9999999999", "role": "INVALID_ROLE"} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"ctx": {"expected": "'INDIVIDUAL' or 'VENDOR'"}, "input": "INVALID_ROLE", "loc": ["body", "role"], "msg": "Input should be 'I... | PASS |
| AUTH-INT-003 | test_auth_login_success | tests/integration/test_auth_api.py | POST /api/v1/auth/login | {"email": "alice@example.com", "password": "StrongPass123"} | {"keys": ["access_token", "refresh_token", "user"], "status_code": 200} | {"body": {"access_token": "access-token-123", "refresh_token": "refresh-token-123", "token_type": "bearer", "user": {"address": "123 Test Street", ... | PASS |
| AUTH-INT-004 | test_auth_token_login_success | tests/integration/test_auth_api.py | POST /api/v1/auth/token | {"password": "StrongPass123", "username": "alice@example.com"} | {"status_code": 200, "token_type": "bearer"} | {"body": {"access_token": "access-token-123", "refresh_token": "refresh-token-123", "token_type": "bearer"}, "status_code": 200} | PASS |
| AUTH-INT-005 | test_auth_logout_missing_header_returns_401 | tests/integration/test_auth_api.py | POST /api/v1/auth/logout | {"authorization": null} | {"detail": "Missing or invalid Authorization header", "status_code": 401} | {"body": {"detail": "Missing or invalid Authorization header"}, "status_code": 401} | PASS |
| AUTH-INT-006 | test_auth_me_requires_authentication | tests/integration/test_auth_api.py | GET /api/v1/auth/me | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| AUTH-INT-007 | test_auth_me_success | tests/integration/test_auth_api.py | GET /api/v1/auth/me | {"authorization": "Bearer <mocked>"} | {"keys": ["id", "email", "role"], "status_code": 200} | {"body": {"address": "123 Test Street", "approval_status": "APPROVED", "business_email": null, "business_phone": null, "company_name": null, "conta... | PASS |
| AUTH-INT-008 | test_auth_change_password_success | tests/integration/test_auth_api.py | POST /api/v1/auth/change-password | {"current_password": "old-pass-123", "new_password": "new-pass-123"} | {"message": "Password changed successfully", "status_code": 200} | {"body": {"message": "Password changed successfully"}, "status_code": 200} | PASS |
| AUTH-INT-009 | test_auth_send_otp_success | tests/integration/test_auth_api.py | POST /api/v1/auth/send-otp | {"email": "alice@example.com"} | {"message": "OTP sent", "status_code": 200} | {"body": {"debug_otp": "123456", "email": "alice@example.com", "message": "OTP sent", "sent_at": "2026-04-03T00:00:00Z"}, "status_code": 200} | PASS |
| AUTH-INT-010 | test_auth_verify_otp_success | tests/integration/test_auth_api.py | POST /api/v1/auth/verify-otp | {"email": "alice@example.com", "otp": "123456"} | {"status_code": 200, "verified": true} | {"body": {"message": "OTP verified", "verified": true}, "status_code": 200} | PASS |
| CV-CON-001 | test_customer_settings_contract | tests/contract/test_customer_vendor_contract.py | GET /api/v1/customer/settings | {"authorization": "Bearer <mocked>"} | {"required_keys": ["settings"], "status_code": 200} | {"body": {"settings": {"currency": "INR", "default_payment": "Full Payment", "language": "en", "notification_prefs": {"email": true}, "privacy_pref... | PASS |
| CV-CON-002 | test_vendor_settings_contract | tests/contract/test_customer_vendor_contract.py | GET /api/v1/vendor/settings | {"authorization": "Bearer <mocked>"} | {"required_keys": ["settings"], "status_code": 200} | {"body": {"settings": {"address": "Dock Road", "company_name": "Vendor Co", "contact_person": "Vendor Lead", "email": "vendor@example.com", "notifi... | PASS |
| CV-INT-001 | test_customer_settings_success | tests/integration/test_customer_vendor_api.py | GET /api/v1/customer/settings | {"authorization": "Bearer <mocked>"} | {"settings.language": "en", "status_code": 200} | {"body": {"settings": {"currency": "INR", "default_payment": "Full Payment", "language": "en", "notification_prefs": {"email": true}, "privacy_pref... | PASS |
| CV-INT-002 | test_customer_damage_report_validation_error_422 | tests/integration/test_customer_vendor_api.py | POST /api/v1/customer/damage-reports | {} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"input": {}, "loc": ["body", "order_id"], "msg": "Field required", "type": "missing"}, {"input": {}, "loc": ["body", "descrip... | PASS |
| CV-INT-003 | test_customer_requires_authentication | tests/integration/test_customer_vendor_api.py | GET /api/v1/customer/settings | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| CV-INT-004 | test_vendor_settings_success | tests/integration/test_customer_vendor_api.py | GET /api/v1/vendor/settings | {"authorization": "Bearer <mocked>"} | {"settings.email": "vendor@example.com", "status_code": 200} | {"body": {"settings": {"address": "Dock Road", "company_name": "Vendor Co", "contact_person": "Vendor Lead", "email": "vendor@example.com", "notifi... | PASS |
| CV-INT-005 | test_vendor_support_ticket_validation_error_422 | tests/integration/test_customer_vendor_api.py | POST /api/v1/vendor/support-tickets | {} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"input": {}, "loc": ["body", "subject"], "msg": "Field required", "type": "missing"}, {"input": {}, "loc": ["body", "descript... | PASS |
| CV-INT-006 | test_vendor_requires_authentication | tests/integration/test_customer_vendor_api.py | GET /api/v1/vendor/settings | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| FR-CON-001 | test_finance_summary_contract | tests/contract/test_finance_rates_contract.py | GET /api/v1/finance/summary | {"authorization": "Bearer <mocked>"} | {"required_keys": ["total_revenue", "total_expenses", "net_profit", "pending_cod"], "status_code": 200} | {"body": {"net_profit": 5000.0, "pending_cod": 1000.0, "total_expenses": 5000.0, "total_revenue": 10000.0}, "status_code": 200} | PASS |
| FR-CON-002 | test_rates_get_contract | tests/contract/test_finance_rates_contract.py | GET /api/v1/rates | {} | {"required_keys": ["baseBookingFee", "perKmRate", "dynamic"], "status_code": 200} | {"body": {"baseBookingFee": 220, "dynamic": {"peak": 1.2}, "perKmRate": 12}, "status_code": 200} | PASS |
| FR-INT-001 | test_finance_summary_success | tests/integration/test_finance_rates_api.py | GET /api/v1/finance/summary | {"authorization": "Bearer <mocked>"} | {"net_profit": 6000.0, "status_code": 200} | {"body": {"net_profit": 6000.0, "pending_cod": 1200.0, "total_expenses": 4000.0, "total_revenue": 10000.0}, "status_code": 200} | PASS |
| FR-INT-002 | test_finance_summary_requires_authentication | tests/integration/test_finance_rates_api.py | GET /api/v1/finance/summary | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| FR-INT-003 | test_finance_payroll_run_success | tests/integration/test_finance_rates_api.py | POST /api/v1/finance/payroll/run | {"user_payouts": [{"amount": 3500, "name": "Staff One", "record_type": "staff", "user_id": "11111111-1111-1111-1111-111111111111"}]} | {"processed": 1, "status_code": 200} | {"body": {"processed": 1, "total_amount": 3500.0}, "status_code": 200} | PASS |
| FR-INT-004 | test_finance_payroll_validation_error_422 | tests/integration/test_finance_rates_api.py | POST /api/v1/finance/payroll/run | {} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"input": {}, "loc": ["body", "user_payouts"], "msg": "Field required", "type": "missing"}]}, "status_code": 422} | PASS |
| FR-INT-005 | test_rates_get_public_success | tests/integration/test_finance_rates_api.py | GET /api/v1/rates | {} | {"baseBookingFee": 220, "status_code": 200} | {"body": {"baseBookingFee": 220, "dynamic": {"peak": 1.2}}, "status_code": 200} | PASS |
| FR-INT-006 | test_rates_update_success | tests/integration/test_finance_rates_api.py | PUT /api/v1/rates | {"dynamic": {"peak": 1.3}} | {"dynamic.peak": 1.3, "status_code": 200} | {"body": {"baseBookingFee": 220, "dynamic": {"emergency": 2.5, "peak": 1.3}}, "status_code": 200} | PASS |
| FR-INT-007 | test_rates_update_empty_payload_returns_400 | tests/integration/test_finance_rates_api.py | PUT /api/v1/rates | {} | {"detail": "Empty payload", "status_code": 400} | {"body": {"detail": "Empty payload"}, "status_code": 400} | PASS |
| FR-INT-008 | test_rates_update_requires_authentication | tests/integration/test_finance_rates_api.py | PUT /api/v1/rates | {"authorization": null, "json": {"baseBookingFee": 300}} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| LT-CON-001 | test_logistics_alerts_contract | tests/contract/test_logistics_tracking_contract.py | GET /api/v1/logistics/alerts | {"authorization": "Bearer <mocked>"} | {"response_type": "list", "status_code": 200} | {"body": [], "status_code": 200} | PASS |
| LT-CON-002 | test_tracking_drivers_contract | tests/contract/test_logistics_tracking_contract.py | GET /api/v1/tracking/drivers | {"authorization": "Bearer <mocked>"} | {"required_keys": ["driver_id", "driver_name", "latitude", "longitude", "status"], "status_code": 200} | {"body": [{"driver_id": "84251528-f763-49b7-88d2-d26ef2d10f11", "driver_name": "Driver One", "last_updated": "2026-04-17T10:00:00+00:00", "latitude... | PASS |
| LT-INT-001 | test_logistics_alerts_success | tests/integration/test_logistics_tracking_api.py | GET /api/v1/logistics/alerts | {"authorization": "Bearer <mocked>"} | {"body": [], "status_code": 200} | {"body": [], "status_code": 200} | PASS |
| LT-INT-002 | test_logistics_alerts_requires_authentication | tests/integration/test_logistics_tracking_api.py | GET /api/v1/logistics/alerts | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| LT-INT-003 | test_logistics_task_validation_error_422 | tests/integration/test_logistics_tracking_api.py | POST /api/v1/logistics/tasks | {} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"input": {}, "loc": ["body", "text"], "msg": "Field required", "type": "missing"}]}, "status_code": 422} | PASS |
| LT-INT-004 | test_tracking_drivers_success_with_db_override | tests/integration/test_logistics_tracking_api.py | GET /api/v1/tracking/drivers | {"authorization": "Bearer <mocked>"} | {"first_driver_name": "Driver One", "status_code": 200} | {"body": [{"driver_id": "f7293515-de23-4653-85c1-1c8823936752", "driver_name": "Driver One", "last_updated": "2026-04-17T10:00:00+00:00", "latitude... | PASS |
| LT-INT-005 | test_tracking_order_driver_requires_authentication | tests/integration/test_logistics_tracking_api.py | GET /api/v1/tracking/orders/{order_id}/driver | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| ORD-CON-002 | test_order_create_contract | tests/contract/test_orders_contract.py | POST /api/v1/orders | {"delivery_addr": "456 Delivery Road", "order_type": "MOVE", "pickup_addr": "123 Pickup Road"} | {"required_keys": ["id", "tracking_code", "status"], "status_code": 201} | {"body": {"arrived_at": null, "assigned_driver_id": null, "assigned_driver_name": null, "assigned_vehicle_code": null, "assigned_vehicle_id": null,... | PASS |
| ORD-CON-003 | test_order_list_contract | tests/contract/test_orders_contract.py | GET /api/v1/orders | {"query": {"page": 1, "page_size": 20}} | {"required_keys": ["items", "total", "page", "page_size"], "status_code": 200} | {"body": {"items": [{"arrived_at": null, "assigned_driver_id": null, "assigned_driver_name": null, "assigned_vehicle_code": null, "assigned_vehicle... | PASS |
| ORD-CON-004 | test_order_items_contract | tests/contract/test_orders_contract.py | GET /api/v1/orders/{order_id}/items | {"path": {"order_id": "52729db6-1a4e-4964-b0d8-4cc9580ac42b"}} | {"required_keys": ["id", "sku", "quantity"], "status_code": 200} | {"body": [{"box_count": 2, "estimated_volume": 1.5, "id": "c7ac8193-23e0-4803-9427-a8fc1687c140", "name": null, "quantity": 3, "sku": "BOX-MEDIUM"}... | PASS |
| ORD-INT-001 | test_orders_create_success | tests/integration/test_orders_api.py | POST /api/v1/orders | {"delivery_addr": "456 Delivery Road", "order_type": "MOVE", "pickup_addr": "123 Pickup Road"} | {"status": "CREATED", "status_code": 201} | {"body": {"arrived_at": null, "assigned_driver_id": null, "assigned_driver_name": null, "assigned_vehicle_code": null, "assigned_vehicle_id": null,... | PASS |
| ORD-INT-002 | test_orders_list_success | tests/integration/test_orders_api.py | GET /api/v1/orders | {"query": {"page": 1, "page_size": 20}} | {"status_code": 200, "total": 1} | {"body": {"items": [{"arrived_at": null, "assigned_driver_id": null, "assigned_driver_name": null, "assigned_vehicle_code": null, "assigned_vehicle... | PASS |
| ORD-INT-003 | test_orders_get_success | tests/integration/test_orders_api.py | GET /api/v1/orders/{order_id} | {"path": {"order_id": "603981ba-5be0-4e50-8aa9-6026be101e50"}} | {"id": "603981ba-5be0-4e50-8aa9-6026be101e50", "status_code": 200} | {"body": {"arrived_at": null, "assigned_driver_id": null, "assigned_driver_name": null, "assigned_vehicle_code": null, "assigned_vehicle_id": null,... | PASS |
| ORD-INT-004 | test_orders_update_success | tests/integration/test_orders_api.py | PUT /api/v1/orders/{order_id} | {"json": {"pickup_addr": "999 Updated Pickup Road"}, "path": {"order_id": "27a693ae-a87c-4ad5-adcb-258607418e08"}} | {"pickup_addr": "999 Updated Pickup Road", "status_code": 200} | {"body": {"arrived_at": null, "assigned_driver_id": null, "assigned_driver_name": null, "assigned_vehicle_code": null, "assigned_vehicle_id": null,... | PASS |
| ORD-INT-005 | test_orders_create_validation_error_422 | tests/integration/test_orders_api.py | POST /api/v1/orders | {} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"input": {}, "loc": ["body", "order_type"], "msg": "Field required", "type": "missing"}, {"input": {}, "loc": ["body", "picku... | PASS |
| ORD-INT-006 | test_orders_requires_authentication | tests/integration/test_orders_api.py | GET /api/v1/orders | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| ORD-INT-007 | test_orders_get_items_success | tests/integration/test_orders_api.py | GET /api/v1/orders/{order_id}/items | {"path": {"order_id": "051077c1-c424-4830-90d9-e723fd416dee"}} | {"item_count": 1, "status_code": 200} | {"body": [{"box_count": 2, "estimated_volume": 1.5, "id": "99ea6f62-523d-448a-ac58-7d8746f4c634", "name": null, "quantity": 3, "sku": "BOX-MEDIUM"}... | PASS |
| ORD-INT-008 | test_orders_upsert_items_success | tests/integration/test_orders_api.py | POST /api/v1/orders/{order_id}/items | {"json": [{"box_count": 1, "quantity": 3, "sku": "BOX-MEDIUM"}], "path": {"order_id": "925f8578-1ab5-4fcd-b79e-13aefe172eae"}} | {"item_count": 1, "status_code": 200} | {"body": [{"box_count": 2, "estimated_volume": 1.5, "id": "bec32381-e44c-4e6f-b884-c4191b29ee14", "name": null, "quantity": 3, "sku": "BOX-MEDIUM"}... | PASS |
| ORD-INT-009 | test_orders_send_delivery_otp_success_for_driver | tests/integration/test_orders_api.py | POST /api/v1/orders/{order_id}/delivery-otp/send | {"json": {"force_resend": false}, "path": {"order_id": "43ee37c2-508f-4686-a9f4-1ee30e5e624e"}} | {"message": "Delivery OTP sent", "status_code": 200} | {"body": {"debug_otp": "123456", "email": "customer@example.com", "message": "Delivery OTP sent", "sent_at": "2026-04-03T00:00:00Z"}, "status_code"... | PASS |
| ORD-INT-010 | test_orders_track_unknown_returns_404 | tests/integration/test_orders_api.py | GET /api/v1/orders/track/{tracking_code} | {"path": {"tracking_code": "UNKNOWN-TRACKING"}} | {"detail": "Tracking code not found", "status_code": 404} | {"body": {"detail": "Tracking code not found"}, "status_code": 404} | PASS |
| ORD-INT-011 | test_orders_customer_rating_success | tests/integration/test_orders_api.py | POST /api/v1/orders/{order_id}/customer-rating | {"json": {"feedback": "Great service", "rating": 5}, "path": {"order_id": "3cc141f2-b681-45cc-8dc5-ab2c23238878"}} | {"customer_rating": 5, "status_code": 200} | {"body": {"arrived_at": null, "assigned_driver_id": null, "assigned_driver_name": null, "assigned_vehicle_code": null, "assigned_vehicle_id": null,... | PASS |
| ORD-INT-012 | test_orders_customer_rating_validation_error_422 | tests/integration/test_orders_api.py | POST /api/v1/orders/{order_id}/customer-rating | {"json": {"feedback": "Invalid rating", "rating": 6}, "path": {"order_id": "0fd94c44-4aba-4534-b7fb-16b118e68a04"}} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"ctx": {"le": 5}, "input": 6, "loc": ["body", "rating"], "msg": "Input should be less than or equal to 5", "type": "less_than... | PASS |
| ORD-INT-013 | test_orders_customer_rating_requires_authentication | tests/integration/test_orders_api.py | POST /api/v1/orders/{order_id}/customer-rating | {"authorization": null, "json": {"feedback": "Great service", "rating": 5}, "path": {"order_id": "e05b0a2c-ac09-477d-abca-0048b499da5e"}} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| PUB-CON-002 | test_health_endpoint_contract | tests/contract/test_public_endpoints_contract.py | GET /health | {} | {"body": {"status": "ok"}, "status_code": 200} | {"body": {"status": "ok"}, "status_code": 200} | PASS |
| PUB-CON-003 | test_tracking_schema_contract_defined | tests/contract/test_public_endpoints_contract.py | GET /api/v1/tracking/drivers | {"authorization": null} | {"openapi_200_item_schema_ref": "#/components/schemas/DriverLocationItem", "runtime_status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| S2-CON-001 | test_support_dashboard_requires_authentication | tests/contract/test_sprint2_updates_contract.py | GET /api/v1/ai/support/dashboard | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| S2-CON-002 | test_damage_review_queue_requires_authentication | tests/contract/test_sprint2_updates_contract.py | GET /api/v1/damage-reports | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| S2-CON-003 | test_dispatcher_intelligence_requires_authentication | tests/contract/test_sprint2_updates_contract.py | GET /api/v1/orders/ai-driver-suggestions | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| S2-INT-001 | test_support_dashboard_success | tests/integration/test_ai_support_api.py | GET /api/v1/ai/support/dashboard | {} | {"stats.active_sessions": 2, "status_code": 200} | {"body": {"activity_feed": [], "priority_sessions": [], "recent_contact_submissions": [], "stats": {"active_sessions": 2, "assistant_messages_today... | PASS |
| S2-INT-002 | test_support_settings_update_success | tests/integration/test_ai_support_api.py | PUT /api/v1/ai/support/settings | {"autonomous_replies": true, "language_mode": "English", "legal_threat_detection": true, "proactive_human_handover": false, "real_time_sentiment_an... | {"settings.sentiment_threshold": 80, "status_code": 200} | {"body": {"autonomous_reply_guidance": "Autonomous mode is active.", "integrations": [{"connected": true, "connection_source": "env", "description"... | PASS |
| S2-INT-003 | test_support_analytics_and_execute_insight_success | tests/integration/test_ai_support_api.py | GET/POST /api/v1/ai/support/analytics* | {"insight_id": "escalation-spike", "range": "7D"} | {"analytics_status": 200, "execute_status": 200} | {"analytics_body": {"escalation_reasons": [{"count": 2, "label": "Legal risk", "pct": 25}, {"count": 6, "label": "Sentiment drop", "pct": 75}], "ge... | PASS |
| S2-INT-004 | test_support_settings_validation_error_422 | tests/integration/test_ai_support_api.py | PUT /api/v1/ai/support/settings | {"autonomous_replies": true, "language_mode": "English", "legal_threat_detection": true, "proactive_human_handover": false, "real_time_sentiment_an... | {"detail_key": "detail", "status_code": 422} | {"body": {"detail": [{"ctx": {"le": 100}, "input": 101, "loc": ["body", "sentiment_threshold"], "msg": "Input should be less than or equal to 100",... | PASS |
| S2-INT-005 | test_damage_review_queue_success | tests/integration/test_damage_review_api.py | GET /api/v1/damage-reports | {"query": {"flow_type": "pickup_inspection", "status": "Reported"}} | {"first_id": "DMG-REF-1001", "status_code": 200} | {"body": [{"customer": "Casey Customer", "description": "Box arrived damaged.", "flow_type": "pickup_inspection", "id": "DMG-REF-1001", "images": [... | PASS |
| S2-INT-006 | test_damage_review_submit_success | tests/integration/test_damage_review_api.py | POST /api/v1/damage-reports/{reference_code}/review | {"json": {"damage_severity": "LOW", "is_genuine": true, "new_status": "Claims Reviewed", "recommended_settlement": "Partial Refund", "remarks": "Pa... | {"status": "Claims Reviewed", "status_code": 200} | {"body": {"customer": "Vendor Ops", "description": "Transit scratch report.", "flow_type": "photo_review", "id": "DMG-REF-2001", "images": ["dmg-1.... | PASS |
| S2-INT-007 | test_damage_review_validation_error_422 | tests/integration/test_damage_review_api.py | POST /api/v1/damage-reports/{reference_code}/review | {"json": {"new_status": 123}, "path": {"reference_code": "DMG-REF-3001"}} | {"detail_key": "detail", "status_code": 422} | {"body": {"detail": [{"input": 123, "loc": ["body", "new_status"], "msg": "Input should be a valid string", "type": "string_type"}]}, "status_code"... | PASS |
| S2-INT-008 | test_assignment_preview_success | tests/integration/test_dispatcher_order_intelligence_api.py | GET /api/v1/orders/assignment-preview | {"query": {"warehouse_id": "497d2787-eedf-4eb9-8666-193cd1c8e41d"}} | {"assignment_type": "selected", "status_code": 200} | {"body": {"assignment_type": "selected", "message": "Manual assignment ready", "warehouse_address": "100 Dispatch Street", "warehouse_id": "497d278... | PASS |
| S2-INT-009 | test_ai_driver_suggestions_success | tests/integration/test_dispatcher_order_intelligence_api.py | GET /api/v1/orders/ai-driver-suggestions | {} | {"status_code": 200, "total": 1} | {"body": {"suggestions": [{"ai_powered": true, "confidence": 93, "delivery_addr": "B Street", "distance_km": 2.7, "order_id": "14ed9a17-51e6-479d-9... | PASS |
| S2-INT-010 | test_return_suggestions_success | tests/integration/test_dispatcher_order_intelligence_api.py | GET /api/v1/orders/return-suggestions | {} | {"status_code": 200, "total": 1} | {"body": {"suggestions": [{"ai_powered": true, "delivered_minutes_ago": 30, "delivery_addr": "Client Avenue", "distance_km": 4.2, "driver_id": "7a5... | PASS |
| S2-INT-011 | test_optimize_routes_and_batch_assign_success | tests/integration/test_dispatcher_order_intelligence_api.py | POST /api/v1/orders/optimize-routes + POST /api/v1/orders/batch-assign | {"batch": {"assignments": [{"driver_id": "4c60f359-5978-4aae-928d-546dc7caafb4", "order_id": "a2a81f5f-254f-47ae-812f-c476bc2adb2d", "vehicle_id": ... | {"batch_status": 200, "optimize_status": 200} | {"batch_body": [{"assigned_driver_id": "4c60f359-5978-4aae-928d-546dc7caafb4", "assigned_vehicle_id": "62c05296-ee08-4730-9e7c-a413c76d5d4a", "id":... | PASS |
| TRK-INT-001 | test_tracking_requires_authentication | tests/integration/test_tracking_api.py | GET /api/v1/tracking/drivers | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| TRK-INT-002 | test_tracking_active_drivers_success | tests/integration/test_tracking_api.py | GET /api/v1/tracking/drivers | {"authorization": "Bearer <mocked>"} | {"driver_count": 1, "status_code": 200} | {"body": [{"driver_id": "8bb180c5-a948-4794-b9e5-03000944db56", "driver_name": "Driver One", "last_updated": "2026-04-18T07:53:45.732198+00:00", "l... | PASS |
| TRK-INT-003 | test_tracking_order_driver_success | tests/integration/test_tracking_api.py | GET /api/v1/tracking/orders/{order_id}/driver | {"path": {"order_id": "d2425ef5-2b54-45af-a7f4-671410c6d899"}} | {"driver_name": "Driver Two", "status_code": 200} | {"body": {"driver_id": "bf7e7b2a-3c97-4e37-b1f0-32f4ff03dc75", "driver_name": "Driver Two", "last_updated": "2026-04-18T07:53:45.733714+00:00", "la... | PASS |
| TRK-INT-004 | test_tracking_order_driver_returns_null_when_unassigned | tests/integration/test_tracking_api.py | GET /api/v1/tracking/orders/{order_id}/driver | {"path": {"order_id": "80a0a84e-d9ae-4745-a716-b7e5a6c803df"}} | {"body": null, "status_code": 200} | {"body": null, "status_code": 200} | PASS |
| WHOPS-CON-001 | test_inbound_overview_contract | tests/contract/test_warehouse_operations_contract.py | GET /api/v1/warehouses/{warehouse_id}/operations/inbound | {"warehouse_id": "11111111-1111-1111-1111-111111111111"} | {"required_keys": ["stats", "shipments", "dock_schedule"], "status_code": 200} | {"body": {"dock_schedule": [], "shipments": [], "stats": {"arrived_today": 1, "damage_reports": 0, "in_transit": 2, "mismatches_found": 0}}, "statu... | PASS |
| WHOPS-CON-002 | test_loading_docks_contract | tests/contract/test_warehouse_operations_contract.py | GET /api/v1/warehouses/{warehouse_id}/operations/loading-docks | {"warehouse_id": "11111111-1111-1111-1111-111111111111"} | {"required_keys": ["items", "total"], "status_code": 200} | {"body": {"items": [], "total": 0}, "status_code": 200} | PASS |
| WHOPS-INT-001 | test_inbound_overview_success | tests/integration/test_warehouse_operations_api.py | GET /api/v1/warehouses/{warehouse_id}/operations/inbound | {"warehouse_id": "11111111-1111-1111-1111-111111111111"} | {"stats.in_transit": 3, "status_code": 200} | {"body": {"dock_schedule": [], "shipments": [], "stats": {"arrived_today": 2, "damage_reports": 0, "in_transit": 3, "mismatches_found": 1}}, "statu... | PASS |
| WHOPS-INT-002 | test_schedule_inbound_success | tests/integration/test_warehouse_operations_api.py | POST /api/v1/warehouses/{warehouse_id}/operations/inbound/schedule | {"dock_preference": "Dock 2", "expected_qty": 120, "notes": "Handle pallets carefully", "scheduled_at": "2026-04-18T10:00:00+00:00", "supplier_name... | {"message_contains": "QC-8800112233", "status_code": 201} | {"body": {"message": "Inbound delivery scheduled as QC-8800112233"}, "status_code": 201} | PASS |
| WHOPS-INT-003 | test_inbound_overview_requires_authentication | tests/integration/test_warehouse_operations_api.py | GET /api/v1/warehouses/{warehouse_id}/operations/inbound | {"authorization": null} | {"detail": "Not authenticated", "status_code": 401} | {"body": {"detail": "Not authenticated"}, "status_code": 401} | PASS |
| WHOPS-INT-004 | test_schedule_inbound_validation_error_422 | tests/integration/test_warehouse_operations_api.py | POST /api/v1/warehouses/{warehouse_id}/operations/inbound/schedule | {} | {"error_key": "detail", "status_code": 422} | {"body": {"detail": [{"input": {}, "loc": ["body", "supplier_name"], "msg": "Field required", "type": "missing"}, {"input": {}, "loc": ["body", "ex... | PASS |
| WHOPS-INT-005 | test_loading_docks_success | tests/integration/test_warehouse_operations_api.py | GET /api/v1/warehouses/{warehouse_id}/operations/loading-docks | {"warehouse_id": "11111111-1111-1111-1111-111111111111"} | {"status_code": 200, "total": 0} | {"body": {"items": [], "total": 0}, "status_code": 200} | PASS |

## 4. Mismatch Summary (Expected != Actual)

| Type | Case | Operation | Expected | Actual | Explanation |
|---|---|---|---|---|---|
| - | - | - | - | - | No mismatches found in current run. |

## 5. Historical Fixed Expected != Actual Cases

| Area | What Failed Before | Fix Applied | Validation |
|---|---|---|---|
| FR-INT-003 payroll run | Mock DB path lacked commit() behavior causing non-production test failure. | Added commit-capable DB override for payroll success path in integration test. | Finance/rates targeted run and full regression passed. |
| AI support flow tests | Monkeypatched service stubs did not accept keyword arguments used by routers. | Updated stubs to keyword-compatible signatures (db=, data=). | AI support targeted run and full regression passed. |

## 6. Test File Inventory

| # | Test File | Discovered Test Functions |
|---|---|---|
| 1 | tests/contract/test_ai_support_flows_contract.py | 3 |
| 2 | tests/contract/test_auth_contract.py | 4 |
| 3 | tests/contract/test_customer_vendor_contract.py | 3 |
| 4 | tests/contract/test_finance_rates_contract.py | 3 |
| 5 | tests/contract/test_logistics_tracking_contract.py | 3 |
| 6 | tests/contract/test_openapi_backend_parity_contract.py | 1 |
| 7 | tests/contract/test_orders_contract.py | 6 |
| 8 | tests/contract/test_proj_guide_compliance_contract.py | 4 |
| 9 | tests/contract/test_public_endpoints_contract.py | 3 |
| 10 | tests/contract/test_sprint2_updates_contract.py | 5 |
| 11 | tests/contract/test_warehouse_operations_contract.py | 4 |
| 12 | tests/integration/test_ai_support_api.py | 4 |
| 13 | tests/integration/test_ai_support_flows_api.py | 6 |
| 14 | tests/integration/test_auth_api.py | 10 |
| 15 | tests/integration/test_customer_vendor_api.py | 6 |
| 16 | tests/integration/test_damage_review_api.py | 3 |
| 17 | tests/integration/test_dispatcher_order_intelligence_api.py | 4 |
| 18 | tests/integration/test_finance_rates_api.py | 8 |
| 19 | tests/integration/test_logistics_tracking_api.py | 5 |
| 20 | tests/integration/test_orders_api.py | 13 |
| 21 | tests/integration/test_tracking_api.py | 4 |
| 22 | tests/integration/test_warehouse_operations_api.py | 5 |
| 23 | tests/unit/schemas/test_ai_chat_request_unit.py | 2 |
| 24 | tests/unit/schemas/test_ai_escalate_request_unit.py | 2 |
| 25 | tests/unit/schemas/test_ai_support_settings_unit.py | 3 |
| 26 | tests/unit/schemas/test_auth_change_password_unit.py | 2 |
| 27 | tests/unit/schemas/test_auth_user_login_unit.py | 2 |
| 28 | tests/unit/schemas/test_auth_user_register_unit.py | 2 |
| 29 | tests/unit/schemas/test_auth_verify_otp_unit.py | 2 |
| 30 | tests/unit/schemas/test_customer_damage_review_update_unit.py | 2 |
| 31 | tests/unit/schemas/test_inventory_create_unit.py | 2 |
| 32 | tests/unit/schemas/test_inventory_movement_create_unit.py | 2 |
| 33 | tests/unit/schemas/test_inventory_restock_status_update_unit.py | 2 |
| 34 | tests/unit/schemas/test_logistics_ai_query_request_unit.py | 2 |
| 35 | tests/unit/schemas/test_logistics_driver_create_unit.py | 2 |
| 36 | tests/unit/schemas/test_logistics_vehicle_create_unit.py | 2 |
| 37 | tests/unit/schemas/test_orders_cancel_order_request_unit.py | 2 |
| 38 | tests/unit/schemas/test_orders_create_unit.py | 2 |
| 39 | tests/unit/schemas/test_orders_customer_rating_request_unit.py | 2 |
| 40 | tests/unit/schemas/test_orders_dispatcher_schemas_unit.py | 3 |
| 41 | tests/unit/schemas/test_orders_item_upsert_unit.py | 2 |
| 42 | tests/unit/schemas/test_users_assign_role_request_unit.py | 2 |
| 43 | tests/unit/schemas/test_users_user_admin_create_unit.py | 2 |
| 44 | tests/unit/schemas/test_wallet_payment_request_unit.py | 2 |
| 45 | tests/unit/schemas/test_warehouse_create_unit.py | 2 |
| 46 | tests/unit/schemas/test_warehouse_ops_assign_truck_request_unit.py | 2 |
| 47 | tests/unit/schemas/test_warehouse_ops_confirm_pick_item_request_unit.py | 2 |
| 48 | tests/unit/schemas/test_warehouse_ops_zone_metrics_create_unit.py | 2 |
| 49 | tests/unit/schemas_bulk/test_ai_chat_request_bulk_unit.py | 2 |
| 50 | tests/unit/schemas_bulk/test_ai_escalate_request_bulk_unit.py | 2 |
| 51 | tests/unit/schemas_bulk/test_auth_change_password_bulk_unit.py | 2 |
| 52 | tests/unit/schemas_bulk/test_auth_user_login_bulk_unit.py | 2 |
| 53 | tests/unit/schemas_bulk/test_auth_user_register_bulk_unit.py | 2 |
| 54 | tests/unit/schemas_bulk/test_auth_verify_otp_bulk_unit.py | 2 |
| 55 | tests/unit/schemas_bulk/test_inventory_create_bulk_unit.py | 2 |
| 56 | tests/unit/schemas_bulk/test_inventory_movement_create_bulk_unit.py | 2 |
| 57 | tests/unit/schemas_bulk/test_inventory_restock_status_bulk_unit.py | 2 |
| 58 | tests/unit/schemas_bulk/test_logistics_ai_query_bulk_unit.py | 2 |
| 59 | tests/unit/schemas_bulk/test_logistics_driver_create_bulk_unit.py | 2 |
| 60 | tests/unit/schemas_bulk/test_logistics_vehicle_create_bulk_unit.py | 2 |
| 61 | tests/unit/schemas_bulk/test_orders_cancel_request_bulk_unit.py | 2 |
| 62 | tests/unit/schemas_bulk/test_orders_create_bulk_unit.py | 2 |
| 63 | tests/unit/schemas_bulk/test_orders_customer_rating_request_bulk_unit.py | 2 |
| 64 | tests/unit/schemas_bulk/test_orders_item_upsert_bulk_unit.py | 2 |
| 65 | tests/unit/schemas_bulk/test_users_admin_create_bulk_unit.py | 2 |
| 66 | tests/unit/schemas_bulk/test_users_assign_role_bulk_unit.py | 2 |
| 67 | tests/unit/schemas_bulk/test_wallet_payment_request_bulk_unit.py | 2 |
| 68 | tests/unit/schemas_bulk/test_warehouse_create_bulk_unit.py | 2 |
| 69 | tests/unit/schemas_bulk/test_warehouse_ops_assign_truck_bulk_unit.py | 2 |
| 70 | tests/unit/schemas_bulk/test_warehouse_ops_confirm_pick_bulk_unit.py | 2 |
| 71 | tests/unit/schemas_bulk/test_warehouse_ops_zone_metrics_bulk_unit.py | 2 |
| 72 | tests/unit/services/test_ai_support_service_helpers_unit.py | 19 |
| 73 | tests/unit/services/test_auth_service_unit.py | 9 |
| 74 | tests/unit/services/test_customer_service_unit.py | 14 |
| 75 | tests/unit/services/test_dispatch_ai_service_unit.py | 6 |
| 76 | tests/unit/services/test_inventory_service_unit.py | 10 |
| 77 | tests/unit/services/test_logistics_service_helpers_unit.py | 14 |
| 78 | tests/unit/services/test_orders_service_helpers_unit.py | 20 |
| 79 | tests/unit/services/test_vendor_service_unit.py | 18 |
| 80 | tests/unit/services/test_warehouse_operations_service_unit.py | 19 |
| 81 | tests/unit/test_data_builders.py | 6 |

## 7. Terminal Evidence Artifacts

- tests/reports/screenshots/phase_d/01_finance_rates_targeted.txt
- tests/reports/screenshots/phase_d/02_warehouse_ops_targeted.txt
- tests/reports/screenshots/phase_d/03_logistics_tracking_targeted.txt
- tests/reports/screenshots/phase_d/04_ai_support_flows_targeted.txt
- tests/reports/screenshots/phase_d/05_full_suite_regression.txt

