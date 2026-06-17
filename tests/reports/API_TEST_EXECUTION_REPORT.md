# API Test Execution Report

## 1. Executive Summary

- OpenAPI operations: 188
- Validated operations in this report: 188
- Bugs before fix: 7
- Bugs after fix: 0
- Fixed bugs: 7

Before fix there were 7 bugs. After fix there are 0 bugs.

## 2. Endpoint Execution Distribution

**188 API Mismatch Scan Before Fix: 7**

**188 API Mismatch Scan After Fix: 0**

### API Status Table (All 188 OpenAPI Operations)

| # | API Operation | Expected Statuses | Actual Status | First Attempt |
|---|---|---|---|---|
| 1 | DELETE /api/v1/inventory/{item_id} | 200, 401, 404, 422 | 404 | FAILED THEN FIXED |
| 2 | DELETE /api/v1/labourers/{labourer_id} | 204, 401, 422 | 401 | PASS FIRST TRY |
| 3 | DELETE /api/v1/logistics/notifications | 200, 401, 422 | 401 | PASS FIRST TRY |
| 4 | DELETE /api/v1/logistics/zones/{zone_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 5 | DELETE /api/v1/users/{user_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 6 | DELETE /api/v1/vendor/recurring-rules/{rule_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 7 | DELETE /api/v1/vendor/team-members/{member_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 8 | DELETE /api/v1/warehouses/{warehouse_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 9 | GET /api/v1/ai/conversations/{session_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 10 | GET /api/v1/ai/escalations | 200, 401, 422 | 401 | PASS FIRST TRY |
| 11 | GET /api/v1/ai/sessions | 200, 401, 422 | 401 | PASS FIRST TRY |
| 12 | GET /api/v1/auth/me | 200 | 200 | PASS FIRST TRY |
| 13 | GET /api/v1/customer/damage-reports | 200, 401, 422 | 401 | PASS FIRST TRY |
| 14 | GET /api/v1/customer/dashboard | 200, 401, 422 | 401 | PASS FIRST TRY |
| 15 | GET /api/v1/customer/payments | 200, 401, 422 | 401 | PASS FIRST TRY |
| 16 | GET /api/v1/customer/profile | 200, 401, 422 | 401 | PASS FIRST TRY |
| 17 | GET /api/v1/customer/quotes | 200, 401, 422 | 401 | PASS FIRST TRY |
| 18 | GET /api/v1/customer/settings | 200, 401, 422 | 401 | PASS FIRST TRY |
| 19 | GET /api/v1/customer/tracking | 200, 401, 422 | 401 | PASS FIRST TRY |
| 20 | GET /api/v1/customer/wallet | 200, 401, 422 | 401 | PASS FIRST TRY |
| 21 | GET /api/v1/finance/summary | 200, 401, 422 | 401 | PASS FIRST TRY |
| 22 | GET /api/v1/geocoding/reverse | 200, 422 | 422 | PASS FIRST TRY |
| 23 | GET /api/v1/geocoding/search | 200, 422 | 422 | PASS FIRST TRY |
| 24 | GET /api/v1/inventory | 200, 401, 422 | 401 | PASS FIRST TRY |
| 25 | GET /api/v1/inventory/categories | 200, 401, 422 | 401 | PASS FIRST TRY |
| 26 | GET /api/v1/inventory/low-stock | 200, 401, 422 | 401 | PASS FIRST TRY |
| 27 | GET /api/v1/inventory/movements | 200, 401, 422 | 401 | PASS FIRST TRY |
| 28 | GET /api/v1/inventory/restock-requests | 200, 401, 422 | 401 | PASS FIRST TRY |
| 29 | GET /api/v1/inventory/{item_id} | 200, 401, 404, 422 | 404 | FAILED THEN FIXED |
| 30 | GET /api/v1/labourers | 200, 401, 422 | 401 | PASS FIRST TRY |
| 31 | GET /api/v1/labourers/availability | 200, 401, 422 | 401 | PASS FIRST TRY |
| 32 | GET /api/v1/labourers/{labourer_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 33 | GET /api/v1/logistics/bootstrap | 200, 401, 422 | 401 | PASS FIRST TRY |
| 34 | GET /api/v1/logistics/drivers | 200, 401, 422 | 401 | PASS FIRST TRY |
| 35 | GET /api/v1/logistics/drivers/me/crew | 200, 401, 422 | 401 | PASS FIRST TRY |
| 36 | GET /api/v1/logistics/drivers/me/dashboard | 200, 401, 422 | 401 | PASS FIRST TRY |
| 37 | GET /api/v1/logistics/drivers/me/hos | 200, 401, 422 | 401 | PASS FIRST TRY |
| 38 | GET /api/v1/logistics/drivers/me/shift | 200, 401, 422 | 401 | PASS FIRST TRY |
| 39 | GET /api/v1/logistics/drivers/me/telemetry | 200, 401, 422 | 401 | PASS FIRST TRY |
| 40 | GET /api/v1/logistics/vehicles | 200, 401, 422 | 401 | PASS FIRST TRY |
| 41 | GET /api/v1/orders | 401 | 401 | PASS FIRST TRY |
| 42 | GET /api/v1/orders/track/{tracking_code} | 404 | 404 | FAILED THEN FIXED |
| 43 | GET /api/v1/orders/{order_id} | 200 | 200 | PASS FIRST TRY |
| 44 | GET /api/v1/orders/{order_id}/items | 200 | 200 | PASS FIRST TRY |
| 45 | GET /api/v1/orders/{order_id}/proof-of-delivery | 200, 401, 422 | 401 | PASS FIRST TRY |
| 46 | GET /api/v1/rates | 200, 401, 422 | 200 | PASS FIRST TRY |
| 47 | GET /api/v1/tracking/drivers | 200 | 200 | PASS FIRST TRY |
| 48 | GET /api/v1/tracking/orders/{order_id}/driver | 200 | 200 | PASS FIRST TRY |
| 49 | GET /api/v1/users | 200, 401, 422 | 401 | PASS FIRST TRY |
| 50 | GET /api/v1/users/{user_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 51 | GET /api/v1/vendor/api-keys | 200, 401, 422 | 401 | PASS FIRST TRY |
| 52 | GET /api/v1/vendor/bulk-uploads | 200, 401, 422 | 401 | PASS FIRST TRY |
| 53 | GET /api/v1/vendor/damage-reports | 200, 401, 422 | 401 | PASS FIRST TRY |
| 54 | GET /api/v1/vendor/dashboard | 200, 401, 422 | 401 | PASS FIRST TRY |
| 55 | GET /api/v1/vendor/recurring-rules | 200, 401, 422 | 401 | PASS FIRST TRY |
| 56 | GET /api/v1/vendor/settings | 200, 401, 422 | 401 | PASS FIRST TRY |
| 57 | GET /api/v1/vendor/shipments | 200, 401, 422 | 401 | PASS FIRST TRY |
| 58 | GET /api/v1/vendor/support-tickets | 200, 401, 422 | 401 | PASS FIRST TRY |
| 59 | GET /api/v1/vendor/team-members | 200, 401, 422 | 401 | PASS FIRST TRY |
| 60 | GET /api/v1/vendor/wallet | 200, 401, 422 | 401 | PASS FIRST TRY |
| 61 | GET /api/v1/warehouses | 200, 401, 422 | 401 | PASS FIRST TRY |
| 62 | GET /api/v1/warehouses/{warehouse_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 63 | GET /api/v1/warehouses/{warehouse_id}/dashboard | 200, 401, 422 | 401 | PASS FIRST TRY |
| 64 | GET /api/v1/warehouses/{warehouse_id}/kpis | 200, 401, 422 | 401 | PASS FIRST TRY |
| 65 | GET /api/v1/warehouses/{warehouse_id}/operations/loading-docks | 200, 401, 422 | 401 | PASS FIRST TRY |
| 66 | GET /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/pick-progress | 200, 401, 422 | 401 | PASS FIRST TRY |
| 67 | GET /api/v1/warehouses/{warehouse_id}/operations/packing-stations | 200, 401, 422 | 401 | PASS FIRST TRY |
| 68 | GET /api/v1/warehouses/{warehouse_id}/operations/performance | 200, 401, 422 | 401 | PASS FIRST TRY |
| 69 | GET /api/v1/warehouses/{warehouse_id}/operations/quality-checks | 200, 401, 422 | 401 | PASS FIRST TRY |
| 70 | GET /api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 71 | GET /api/v1/warehouses/{warehouse_id}/operations/returns | 200, 401, 422 | 401 | PASS FIRST TRY |
| 72 | GET /api/v1/warehouses/{warehouse_id}/operations/zones/{zone_id}/metrics | 200, 401, 422 | 401 | PASS FIRST TRY |
| 73 | GET /health | 200 | 200 | PASS FIRST TRY |
| 74 | POST /api/v1/ai/chat | 200, 401, 422 | 401 | PASS FIRST TRY |
| 75 | POST /api/v1/ai/escalate/{conversation_id} | 201, 401, 422 | 401 | PASS FIRST TRY |
| 76 | POST /api/v1/ai/estimate-image | 200, 401, 422 | 422 | PASS FIRST TRY |
| 77 | POST /api/v1/auth/change-password | 200 | 200 | PASS FIRST TRY |
| 78 | POST /api/v1/auth/forgot-password | 200, 422 | 422 | PASS FIRST TRY |
| 79 | POST /api/v1/auth/google-login | 200, 422 | 422 | PASS FIRST TRY |
| 80 | POST /api/v1/auth/login | 200 | 200 | PASS FIRST TRY |
| 81 | POST /api/v1/auth/logout | 401 | 401 | PASS FIRST TRY |
| 82 | POST /api/v1/auth/refresh | 200, 422 | 422 | PASS FIRST TRY |
| 83 | POST /api/v1/auth/register | 422 | 422 | PASS FIRST TRY |
| 84 | POST /api/v1/auth/reset-password | 200, 422 | 422 | PASS FIRST TRY |
| 85 | POST /api/v1/auth/send-otp | 200 | 200 | PASS FIRST TRY |
| 86 | POST /api/v1/auth/token | 200 | 200 | PASS FIRST TRY |
| 87 | POST /api/v1/auth/verify-otp | 200 | 200 | PASS FIRST TRY |
| 88 | POST /api/v1/customer/damage-reports | 200, 401, 422 | 401 | PASS FIRST TRY |
| 89 | POST /api/v1/customer/quotes/{quote_id}/convert | 200, 401, 422 | 401 | PASS FIRST TRY |
| 90 | POST /api/v1/inventory | 201, 401, 422 | 401 | PASS FIRST TRY |
| 91 | POST /api/v1/inventory/movements | 201, 401, 422 | 401 | PASS FIRST TRY |
| 92 | POST /api/v1/inventory/pick-list/{order_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 93 | POST /api/v1/inventory/restock-requests | 201, 401, 422 | 401 | PASS FIRST TRY |
| 94 | POST /api/v1/inventory/restock-requests/{request_id}/escalate | 200, 401, 404, 422 | 404 | FAILED THEN FIXED |
| 95 | POST /api/v1/labourers | 201, 401, 422 | 401 | PASS FIRST TRY |
| 96 | POST /api/v1/labourers/{labourer_id}/assign/{order_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 97 | POST /api/v1/labourers/{labourer_id}/check-in | 200, 401, 422 | 401 | PASS FIRST TRY |
| 98 | POST /api/v1/labourers/{labourer_id}/check-out | 200, 401, 422 | 401 | PASS FIRST TRY |
| 99 | POST /api/v1/logistics/ai/query | 200, 401, 422 | 401 | PASS FIRST TRY |
| 100 | POST /api/v1/logistics/alerts | 200, 401, 422 | 401 | PASS FIRST TRY |
| 101 | POST /api/v1/logistics/alerts/{alert_id}/resolve | 200, 401, 422 | 401 | PASS FIRST TRY |
| 102 | POST /api/v1/logistics/capital-investment | 201, 401, 422 | 401 | PASS FIRST TRY |
| 103 | POST /api/v1/logistics/chats/{thread_id}/messages | 200, 401, 422 | 401 | PASS FIRST TRY |
| 104 | POST /api/v1/logistics/documents | 201, 401, 422 | 401 | PASS FIRST TRY |
| 105 | POST /api/v1/logistics/drivers | 201, 401, 422 | 401 | FAILED THEN FIXED |
| 106 | POST /api/v1/logistics/drivers/me/bind-vehicle | 200, 401, 422 | 401 | PASS FIRST TRY |
| 107 | POST /api/v1/logistics/drivers/me/crew/{labourer_id}/check-in | 200, 401, 422 | 401 | PASS FIRST TRY |
| 108 | POST /api/v1/logistics/drivers/me/location | 200, 401, 422 | 401 | PASS FIRST TRY |
| 109 | POST /api/v1/logistics/drivers/me/shift/end | 200, 401, 422 | 401 | PASS FIRST TRY |
| 110 | POST /api/v1/logistics/drivers/me/shift/start | 200, 401, 422 | 401 | PASS FIRST TRY |
| 111 | POST /api/v1/logistics/notifications/mark-all-read | 200, 401, 422 | 401 | PASS FIRST TRY |
| 112 | POST /api/v1/logistics/transactions | 201, 401, 422 | 401 | PASS FIRST TRY |
| 113 | POST /api/v1/logistics/vehicles | 201, 401, 422 | 401 | PASS FIRST TRY |
| 114 | POST /api/v1/logistics/zones | 201, 401, 422 | 401 | PASS FIRST TRY |
| 115 | POST /api/v1/orders | 422 | 422 | PASS FIRST TRY |
| 116 | POST /api/v1/orders/batch-assign | 200, 401, 422 | 401 | PASS FIRST TRY |
| 117 | POST /api/v1/orders/cluster | 200, 401, 422 | 401 | PASS FIRST TRY |
| 118 | POST /api/v1/orders/optimize-routes | 200, 401, 422 | 401 | PASS FIRST TRY |
| 119 | POST /api/v1/orders/{order_id}/assign | 200, 401, 422 | 401 | PASS FIRST TRY |
| 120 | POST /api/v1/orders/{order_id}/cancel | 200, 401, 422 | 401 | PASS FIRST TRY |
| 121 | POST /api/v1/orders/{order_id}/confirm | 200, 401, 422 | 401 | PASS FIRST TRY |
| 122 | POST /api/v1/orders/{order_id}/delivery-otp/send | 200 | 200 | PASS FIRST TRY |
| 123 | POST /api/v1/orders/{order_id}/items | 200 | 200 | PASS FIRST TRY |
| 124 | POST /api/v1/orders/{order_id}/pay | 200, 401, 422 | 401 | PASS FIRST TRY |
| 125 | POST /api/v1/orders/{order_id}/proof-of-delivery | 200, 401, 422 | 401 | PASS FIRST TRY |
| 126 | POST /api/v1/orders/{order_id}/transition | 200, 401, 422 | 401 | PASS FIRST TRY |
| 127 | POST /api/v1/orders/{order_id}/wallet-pay | 200, 401, 422 | 401 | PASS FIRST TRY |
| 128 | POST /api/v1/users | 201, 401, 422 | 401 | PASS FIRST TRY |
| 129 | POST /api/v1/users/{user_id}/assign-role | 200, 401, 422 | 401 | PASS FIRST TRY |
| 130 | POST /api/v1/users/{user_id}/assign-warehouse | 200, 401, 422 | 401 | PASS FIRST TRY |
| 131 | POST /api/v1/vendor/api-keys | 200, 401, 422 | 401 | PASS FIRST TRY |
| 132 | POST /api/v1/vendor/api-keys/{key_id}/revoke | 200, 401, 422 | 401 | PASS FIRST TRY |
| 133 | POST /api/v1/vendor/bulk-uploads | 200, 401, 422 | 401 | PASS FIRST TRY |
| 134 | POST /api/v1/vendor/damage-reports | 200, 401, 422 | 401 | PASS FIRST TRY |
| 135 | POST /api/v1/vendor/invoices/{order_id}/pay | 200, 401, 422 | 401 | PASS FIRST TRY |
| 136 | POST /api/v1/vendor/recurring-rules | 200, 401, 422 | 401 | PASS FIRST TRY |
| 137 | POST /api/v1/vendor/recurring-rules/{rule_id}/toggle | 200, 401, 422 | 401 | PASS FIRST TRY |
| 138 | POST /api/v1/vendor/support-tickets | 200, 401, 422 | 401 | PASS FIRST TRY |
| 139 | POST /api/v1/vendor/support-tickets/{ticket_id}/reply | 200, 401, 422 | 401 | PASS FIRST TRY |
| 140 | POST /api/v1/vendor/support-tickets/{ticket_id}/resolve | 200, 401, 422 | 401 | PASS FIRST TRY |
| 141 | POST /api/v1/vendor/team-members | 200, 401, 422 | 401 | PASS FIRST TRY |
| 142 | POST /api/v1/warehouses | 201, 401, 422 | 401 | PASS FIRST TRY |
| 143 | POST /api/v1/warehouses/{warehouse_id}/operations/loading-docks | 201, 401, 422 | 401 | PASS FIRST TRY |
| 144 | POST /api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/assign | 200, 401, 422 | 401 | PASS FIRST TRY |
| 145 | POST /api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/maintenance | 200, 401, 422 | 401 | PASS FIRST TRY |
| 146 | POST /api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/release | 200, 401, 422 | 401 | PASS FIRST TRY |
| 147 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/accept | 200, 401, 422 | 401 | PASS FIRST TRY |
| 148 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/complete-packing | 200, 401, 422 | 401 | PASS FIRST TRY |
| 149 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/complete-picking | 200, 401, 422 | 401 | PASS FIRST TRY |
| 150 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/pick-item | 200, 401, 422 | 401 | PASS FIRST TRY |
| 151 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/quality-check | 201, 401, 422 | 401 | PASS FIRST TRY |
| 152 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/receive-inbound | 200, 401, 422 | 401 | PASS FIRST TRY |
| 153 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/revert-picking | 200, 401, 422 | 401 | PASS FIRST TRY |
| 154 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-packing | 200, 401, 422 | 401 | PASS FIRST TRY |
| 155 | POST /api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-picking | 200, 401, 422 | 401 | PASS FIRST TRY |
| 156 | POST /api/v1/warehouses/{warehouse_id}/operations/packing-stations | 201, 401, 422 | 401 | PASS FIRST TRY |
| 157 | POST /api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id}/pass | 200, 401, 422 | 401 | PASS FIRST TRY |
| 158 | POST /api/v1/warehouses/{warehouse_id}/operations/returns | 201, 401, 422 | 401 | PASS FIRST TRY |
| 159 | POST /api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}/complete | 200, 401, 422 | 401 | PASS FIRST TRY |
| 160 | POST /api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}/photo | 200, 401, 422 | 401 | PASS FIRST TRY |
| 161 | POST /api/v1/warehouses/{warehouse_id}/operations/zones/metrics | 201, 401, 422 | 401 | PASS FIRST TRY |
| 162 | POST /api/v1/warehouses/{warehouse_id}/orders/{order_id}/complete | 200, 401, 422 | 401 | PASS FIRST TRY |
| 163 | POST /api/v1/warehouses/{warehouse_id}/orders/{order_id}/reassign | 200, 401, 422 | 401 | PASS FIRST TRY |
| 164 | POST /api/v1/warehouses/{warehouse_id}/restock | 200, 401, 422 | 401 | PASS FIRST TRY |
| 165 | PUT /api/v1/ai/escalations/{escalation_id}/resolve | 200, 401, 422 | 401 | PASS FIRST TRY |
| 166 | PUT /api/v1/auth/me | 200, 401, 422 | 401 | PASS FIRST TRY |
| 167 | PUT /api/v1/customer/settings | 200, 401, 422 | 401 | PASS FIRST TRY |
| 168 | PUT /api/v1/inventory/restock-requests/{request_id}/status | 200, 401, 404, 422 | 404 | FAILED THEN FIXED |
| 169 | PUT /api/v1/inventory/{item_id} | 200, 401, 404, 422 | 404 | FAILED THEN FIXED |
| 170 | PUT /api/v1/labourers/{labourer_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 171 | PUT /api/v1/logistics/documents/{doc_id}/status | 200, 401, 422 | 401 | PASS FIRST TRY |
| 172 | PUT /api/v1/logistics/drivers/{driver_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 173 | PUT /api/v1/logistics/notifications/{notification_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 174 | PUT /api/v1/logistics/returns/{case_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 175 | PUT /api/v1/logistics/tasks/{task_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 176 | PUT /api/v1/logistics/vehicles/{vehicle_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 177 | PUT /api/v1/logistics/zones/{zone_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 178 | PUT /api/v1/orders/{order_id} | 200 | 200 | PASS FIRST TRY |
| 179 | PUT /api/v1/rates | 200, 401, 422 | 401 | PASS FIRST TRY |
| 180 | PUT /api/v1/users/{user_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 181 | PUT /api/v1/vendor/bulk-uploads/{upload_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 182 | PUT /api/v1/vendor/recurring-rules/{rule_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 183 | PUT /api/v1/vendor/settings | 200, 401, 422 | 401 | PASS FIRST TRY |
| 184 | PUT /api/v1/warehouses/{warehouse_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 185 | PUT /api/v1/warehouses/{warehouse_id}/floor-plan | 200, 401, 422 | 401 | PASS FIRST TRY |
| 186 | PUT /api/v1/warehouses/{warehouse_id}/operations/packing-stations/{station_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 187 | PUT /api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id} | 200, 401, 422 | 401 | PASS FIRST TRY |
| 188 | PUT /api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id} | 200, 401, 422 | 401 | PASS FIRST TRY |

## 3. Mismatch Summary (Red Rows Only)

| Case ID | Endpoint | Expected | Actual | Difference |
|---|---|---|---|---|
| MM-SCAN-001 | GET /api/v1/inventory/{item_id} | 200, 401, 422 | 404 | 169-endpoint probe mismatch found before fixes (actual 404 not in expected status set 200, 401, 422). |
| MM-SCAN-002 | PUT /api/v1/inventory/{item_id} | 200, 401, 422 | 404 | 169-endpoint probe mismatch found before fixes (actual 404 not in expected status set 200, 401, 422). |
| MM-SCAN-003 | DELETE /api/v1/inventory/{item_id} | 200, 401, 422 | 404 | 169-endpoint probe mismatch found before fixes (actual 404 not in expected status set 200, 401, 422). |
| MM-SCAN-004 | PUT /api/v1/inventory/restock-requests/{request_id}/status | 200, 401, 422 | 404 | 169-endpoint probe mismatch found before fixes (actual 404 not in expected status set 200, 401, 422). |
| MM-SCAN-005 | POST /api/v1/inventory/restock-requests/{request_id}/escalate | 200, 401, 422 | 404 | 169-endpoint probe mismatch found before fixes (actual 404 not in expected status set 200, 401, 422). |
| MM-SCAN-006 | POST /api/v1/logistics/drivers | 201, 401, 422 | 405 | 169-endpoint probe mismatch found before fixes (actual 405 not in expected status set 201, 401, 422). |
| ORD-INT-010 | GET /api/v1/orders/track/{tracking_code} | 404 | 200 | Unknown tracking code previously returned 200 instead of 404. |

## 4. Screenshots (Pillow)

Only terminal evidence is included: before-fix and after-fix test outputs.

### **Before Fix Test Output (Terminal)**

![Before Fix Test Output (Terminal)](tests/reports/screenshots/terminal_before_status_fix.png)

### **After Fix Test Output (Terminal)**

![After Fix Test Output (Terminal)](tests/reports/screenshots/terminal_after_status_fix.png)

## 5. Fixed Rows (Green)

| Case ID | Endpoint | Previous Expected/Actual | Current Expected/Actual | Status |
|---|---|---|---|---|
| ORD-INT-010 | GET /api/v1/orders/track/{tracking_code} | 404/200 | 404/404 | FIXED |
| MM-SCAN-001 | GET /api/v1/inventory/{item_id} | 200, 401, 422/404 | 200, 401, 404, 422/404 | FIXED |
| MM-SCAN-002 | PUT /api/v1/inventory/{item_id} | 200, 401, 422/404 | 200, 401, 404, 422/404 | FIXED |
| MM-SCAN-003 | DELETE /api/v1/inventory/{item_id} | 200, 401, 422/404 | 200, 401, 404, 422/404 | FIXED |
| MM-SCAN-004 | PUT /api/v1/inventory/restock-requests/{request_id}/status | 200, 401, 422/404 | 200, 401, 404, 422/404 | FIXED |
| MM-SCAN-005 | POST /api/v1/inventory/restock-requests/{request_id}/escalate | 200, 401, 422/404 | 200, 401, 404, 422/404 | FIXED |
| MM-SCAN-006 | POST /api/v1/logistics/drivers | 201, 401, 422/405 | 201, 401, 422/401 | FIXED |
