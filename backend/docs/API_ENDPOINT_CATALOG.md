# API Endpoint Catalog

Generated from FastAPI OpenAPI schema on `2026-04-17 15:55:33Z`.

## Summary

- Tags: `18`
- Paths: `244`
- Operations: `303`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Swagger Testing Flow

1. Start the backend.
2. Open `/docs`.
3. Click `Authorize` in Swagger UI.
4. Enter your email or username in the `username` field and your password in the `password` field.
5. Swagger will call `POST /api/v1/auth/token` automatically and store the bearer token.
6. Expand endpoints by tag and test them directly from Swagger.

Manual alternative: call `POST /api/v1/auth/login`, copy the `access_token`, and paste it into `Authorize`.

## Tag Counts

| Tag | Operations |
| --- | ---: |
| AI | 43 |
| Authentication | 13 |
| Customer | 18 |
| Damage Reports | 2 |
| Dev Seed | 2 |
| Finance | 2 |
| Geocoding | 2 |
| Health | 1 |
| Inventory | 19 |
| Labourers | 9 |
| Live Tracking | 2 |
| Logistics Manager | 66 |
| Orders | 34 |
| Rates | 4 |
| Users | 7 |
| Vendor | 31 |
| Warehouse Operations | 37 |
| Warehouses | 11 |

## AI

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/ai/chat` | Send a message to the AI chatbot | Bearer token | `application/json -> ChatRequest` | `200 application/json -> ChatResponse` |
| GET | `/api/v1/ai/contact-submissions` | List support contact submissions | Bearer token | `None` | `200 application/json -> ContactSubmissionListResponse` |
| POST | `/api/v1/ai/contact-submissions/public` | Submit a public contact form | No | `application/json -> ContactSubmissionCreatePublic` | `201 application/json -> ContactSubmissionResponse` |
| DELETE | `/api/v1/ai/contact-submissions/{submission_id}` | Delete a support contact submission | Bearer token | `None` | `204` |
| PUT | `/api/v1/ai/contact-submissions/{submission_id}` | Update a support contact submission | Bearer token | `application/json -> ContactSubmissionUpdate` | `200 application/json -> ContactSubmissionResponse` |
| POST | `/api/v1/ai/contact-submissions/{submission_id}/reply` | Reply to a support contact submission by email | Bearer token | `application/json -> ContactSubmissionReplyRequest` | `200 application/json -> ContactSubmissionResponse` |
| GET | `/api/v1/ai/conversations/{session_id}` | Get conversation history | Bearer token | `None` | `200 application/json -> ConversationHistory` |
| POST | `/api/v1/ai/escalate/{conversation_id}` | Escalate conversation to human agent | Bearer token | `application/json -> EscalateRequest` | `201 application/json -> EscalationResponse` |
| GET | `/api/v1/ai/escalation-center` | List enriched escalations for the Escalation Center UI | Bearer token | `None` | `200 application/json -> EscalationDetailListResponse` |
| PUT | `/api/v1/ai/escalation-center/{escalation_id}/resolve` | Resolve an escalation from the Escalation Center | Bearer token | `None` | `200 application/json -> EscalationResponse` |
| GET | `/api/v1/ai/escalations` | List escalations | Bearer token | `None` | `200 application/json -> EscalationListResponse` |
| PUT | `/api/v1/ai/escalations/{escalation_id}/resolve` | Resolve an escalation | Bearer token | `None` | `200 application/json -> EscalationResponse` |
| POST | `/api/v1/ai/estimate-image` | Analyze a room photo for moving estimate | No | `multipart/form-data -> Body_estimate_image_api_v1_ai_estimate_image_post` | `200 application/json -> None` |
| GET | `/api/v1/ai/knowledge-articles` | List all knowledge base articles | Bearer token | `None` | `200 application/json -> KnowledgeArticleListResponse` |
| POST | `/api/v1/ai/knowledge-articles` | Create a new knowledge base article | Bearer token | `application/json -> KnowledgeArticleCreate` | `201 application/json -> KnowledgeArticleResponse` |
| DELETE | `/api/v1/ai/knowledge-articles/{article_id}` | Delete a knowledge base article | Bearer token | `None` | `204` |
| GET | `/api/v1/ai/knowledge-articles/{article_id}` | Get a single knowledge base article | Bearer token | `None` | `200 application/json -> KnowledgeArticleResponse` |
| PUT | `/api/v1/ai/knowledge-articles/{article_id}` | Update a knowledge base article | Bearer token | `application/json -> KnowledgeArticleUpdate` | `200 application/json -> KnowledgeArticleResponse` |
| POST | `/api/v1/ai/knowledge-articles/{article_id}/like` | Increment the like count on an article | Bearer token | `None` | `200 application/json -> KnowledgeArticleResponse` |
| GET | `/api/v1/ai/recovery-tickets/count` | Count of open AI-analytics recovery tickets for the Logistics Manager | Bearer token | `None` | `200 application/json -> None` |
| GET | `/api/v1/ai/sessions` | List chat sessions | Bearer token | `None` | `200 application/json -> SessionListResponse` |
| GET | `/api/v1/ai/support/analytics` | Support analytics for the AI analytics dashboard | Bearer token | `None` | `200 application/json -> SupportAnalyticsResponse` |
| POST | `/api/v1/ai/support/analytics/insights/{insight_id}/execute` | Create a follow-up ticket for an analytics insight | Bearer token | `None` | `200 application/json -> SupportAnalyticsInsightExecutionResponse` |
| GET | `/api/v1/ai/support/customer-history/{user_id}` | Get customer history summary for support sidebar | Bearer token | `None` | `200 application/json -> CustomerHistoryResponse` |
| GET | `/api/v1/ai/support/damage-reports` | List all damage reports enriched for AI support staff | Bearer token | `None` | `200 application/json -> SupportDamageReportListResponse` |
| POST | `/api/v1/ai/support/damage-reports` | Create a damage report on a customer's behalf | Bearer token | `application/json -> SupportDamageReportCreate` | `201 application/json -> SupportDamageReportItem` |
| POST | `/api/v1/ai/support/damage-reports/{report_id}/message` | Send a message to the customer for a damage report case | Bearer token | `application/json -> SupportMessageCreate` | `201 application/json -> SupportDamageReportItem` |
| PUT | `/api/v1/ai/support/damage-reports/{report_id}/notes` | Update support notes on a damage report | Bearer token | `application/json -> SupportDamageReportNotesUpdate` | `200 application/json -> SupportDamageReportItem` |
| GET | `/api/v1/ai/support/dashboard` | Support dashboard data | Bearer token | `None` | `200 application/json -> SupportDashboardResponse` |
| GET | `/api/v1/ai/support/refund-cases` | List return cases with refund info for AI support staff | Bearer token | `None` | `200 application/json -> SupportRefundCaseListResponse` |
| PUT | `/api/v1/ai/support/refund-cases/{case_id}/urgent` | Set or clear urgency flag on a return case | Bearer token | `application/json -> SupportRefundCaseUrgentUpdate` | `200 application/json -> SupportRefundCaseItem` |
| GET | `/api/v1/ai/support/sessions` | List live support sessions for staff | Bearer token | `None` | `200 application/json -> SupportSessionListResponse` |
| GET | `/api/v1/ai/support/sessions/{session_id}` | Get staff view of a conversation session | Bearer token | `None` | `200 application/json -> SupportSessionDetail` |
| POST | `/api/v1/ai/support/sessions/{session_id}/escalate` | Escalate a support session from the live conversation view | Bearer token | `application/json -> SupportSessionEscalateRequest` | `200 application/json -> EscalationResponse` |
| POST | `/api/v1/ai/support/sessions/{session_id}/reply` | Send a human agent reply in a live conversation | Bearer token | `application/json -> AgentReplyRequest` | `200 application/json -> SupportSessionDetail` |
| POST | `/api/v1/ai/support/sessions/{session_id}/take-over` | Take over a live AI conversation | Bearer token | `None` | `200 application/json -> SupportSessionDetail` |
| GET | `/api/v1/ai/support/settings` | AI support system settings | Bearer token | `None` | `200 application/json -> SupportSettingsResponse` |
| PUT | `/api/v1/ai/support/settings` | Update AI support system settings | Bearer token | `application/json -> SupportSettings` | `200 application/json -> SupportSettingsResponse` |
| GET | `/api/v1/ai/tickets` | List all support tickets | Bearer token | `None` | `200 application/json -> TicketListResponse` |
| POST | `/api/v1/ai/tickets` | Create a new support ticket | Bearer token | `application/json -> TicketCreate` | `201 application/json -> TicketResponse` |
| DELETE | `/api/v1/ai/tickets/{ticket_id}` | Delete a support ticket | Bearer token | `None` | `204` |
| PUT | `/api/v1/ai/tickets/{ticket_id}` | Update a support ticket | Bearer token | `application/json -> TicketUpdate` | `200 application/json -> TicketResponse` |
| POST | `/api/v1/ai/tickets/{ticket_id}/reply` | Reply to a linked vendor ticket from the support dashboard | Bearer token | `application/json -> AgentReplyRequest` | `200 application/json -> TicketResponse` |

## Authentication

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/change-password` | Change password | Bearer token | `application/json -> ChangePasswordRequest` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/auth/forgot-password` | Request password reset email | No | `application/json -> ForgotPasswordRequest` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/auth/google-login` | Login or Register with Google | No | `application/json -> GoogleLoginRequest` | `200 application/json -> LoginResponse` |
| POST | `/api/v1/auth/login` | Issue JWT tokens with user profile | No | `application/json -> UserLogin` | `200 application/json -> LoginResponse` |
| POST | `/api/v1/auth/logout` | Invalidate access token via Redis blacklist | No | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/auth/me` | Get current user profile | Bearer token | `None` | `200 application/json -> UserProfile` |
| PUT | `/api/v1/auth/me` | Update current user profile | Bearer token | `application/json -> UserProfileUpdate` | `200 application/json -> UserProfile` |
| POST | `/api/v1/auth/refresh` | Refresh access token | No | `application/json -> RefreshTokenRequest` | `200 application/json -> TokenResponse` |
| POST | `/api/v1/auth/register` | Self-service sign-up (Individual & Vendor only) | No | `application/json -> UserRegister` | `201 application/json -> RegistrationResponse` |
| POST | `/api/v1/auth/reset-password` | Confirm password reset with token | No | `application/json -> ResetPasswordRequest` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/auth/send-otp` | Send email verification OTP for signup | No | `application/json -> SendOTPRequest` | `200 application/json -> SignupOtpSendResponse` |
| POST | `/api/v1/auth/token` | Issue OAuth2 bearer token for Swagger UI | No | `application/x-www-form-urlencoded -> Body_token_login_api_v1_auth_token_post` | `200 application/json -> TokenResponse` |
| POST | `/api/v1/auth/verify-otp` | Verify email OTP before completing signup | No | `application/json -> VerifyOTPRequest` | `200 application/json -> OTPVerifiedResponse` |

## Customer

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| DELETE | `/api/v1/customer/account` | Delete Account | Bearer token | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/customer/damage-reports` | Get Damage Reports | Bearer token | `None` | `200 application/json -> CustomerDamageReportsResponse` |
| POST | `/api/v1/customer/damage-reports` | Create Damage Report | Bearer token | `application/json -> CustomerDamageReportCreate` | `200 application/json -> CustomerDamageReport` |
| GET | `/api/v1/customer/dashboard` | Get Dashboard | Bearer token | `None` | `200 application/json -> None` |
| DELETE | `/api/v1/customer/notifications` | Clear Notifications | Bearer token | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/customer/notifications` | Get Notifications | Bearer token | `None` | `200 application/json -> array[LogisticsNotificationItem]` |
| POST | `/api/v1/customer/notifications/mark-all-read` | Mark All Notifications Read | Bearer token | `None` | `200 application/json -> MessageResponse` |
| PUT | `/api/v1/customer/notifications/{notification_id}` | Update Notification | Bearer token | `application/json -> LogisticsNotificationUpdate` | `200 application/json -> LogisticsNotificationItem` |
| GET | `/api/v1/customer/payments` | Get Payments | Bearer token | `None` | `200 application/json -> CustomerPaymentsSummary` |
| GET | `/api/v1/customer/profile` | Get Profile | Bearer token | `None` | `200 application/json -> CustomerProfileResponse` |
| GET | `/api/v1/customer/quotes` | Get Quotes | Bearer token | `None` | `200 application/json -> CustomerQuotesResponse` |
| POST | `/api/v1/customer/quotes/{quote_id}/convert` | Convert Quote | Bearer token | `None` | `200 application/json -> None` |
| GET | `/api/v1/customer/settings` | Get Settings | Bearer token | `None` | `200 application/json -> CustomerSettingsResponse` |
| PUT | `/api/v1/customer/settings` | Update Settings | Bearer token | `application/json -> CustomerSettings` | `200 application/json -> CustomerSettingsResponse` |
| GET | `/api/v1/customer/tracking` | Get Tracking | Bearer token | `None` | `200 application/json -> CustomerTrackingResponse` |
| GET | `/api/v1/customer/wallet` | Get Wallet | Bearer token | `None` | `200 application/json -> WalletSummary` |
| POST | `/api/v1/customer/wallet/backfill-debits` | Backfill Wallet Debits | Bearer token | `None` | `200 application/json -> None` |
| POST | `/api/v1/customer/wallet/top-up` | Top Up Wallet | Bearer token | `application/json -> WalletTopUpRequest` | `200 application/json -> WalletTopUpResponse` |

## Damage Reports

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/damage-reports` | List Damage Reports | Bearer token | `None` | `200 application/json -> array[DamageReviewQueueItem]` |
| POST | `/api/v1/damage-reports/{reference_code}/review` | Review Damage Report | Bearer token | `application/json -> DamageReviewUpdate` | `200 application/json -> DamageReviewQueueItem` |

## Dev Seed

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| DELETE | `/api/v1/dev/seed-gps` | Clear Seeded Gps | Bearer token | `None` | `200 application/json -> None` |
| POST | `/api/v1/dev/seed-gps` | Seed Gps Coordinates | Bearer token | `None` | `200 application/json -> None` |

## Finance

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/finance/payroll/run` | Run Payroll | Bearer token | `application/json -> PayrollRunRequest` | `200 application/json -> Response Run Payroll Api V1 Finance Payroll Run Post` |
| GET | `/api/v1/finance/summary` | Get Finance Summary | Bearer token | `None` | `200 application/json -> Response Get Finance Summary Api V1 Finance Summary Get` |

## Geocoding

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/geocoding/reverse` | Reverse Geocode | No | `None` | `200 application/json -> Response Reverse Geocode Api V1 Geocoding Reverse Get` |
| GET | `/api/v1/geocoding/search` | Search Addresses | No | `None` | `200 application/json -> array[object]` |

## Health

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/health` | Health Check | No | `None` | `200 application/json -> None` |

## Inventory

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/inventory` | List Inventory | Bearer token | `None` | `200 application/json -> InventoryListResponse` |
| POST | `/api/v1/inventory` | Create Inventory Item | Bearer token | `application/json -> InventoryCreate` | `201 application/json -> InventoryResponse` |
| GET | `/api/v1/inventory/categories` | List Inventory Categories | Bearer token | `None` | `200 application/json -> array[string]` |
| GET | `/api/v1/inventory/low-stock` | Low Stock | Bearer token | `None` | `200 application/json -> array[InventoryResponse]` |
| GET | `/api/v1/inventory/material-requests` | List Material Requests | Bearer token | `None` | `200 application/json -> MaterialRequestListResponse` |
| POST | `/api/v1/inventory/material-requests` | Create Material Request | Bearer token | `application/json -> MaterialRequestCreate` | `201 application/json -> MaterialRequestResponse` |
| PUT | `/api/v1/inventory/material-requests/{request_id}/approve` | Approve Material Request | Bearer token | `application/json -> MaterialRequestApprove` | `200 application/json -> MaterialRequestResponse` |
| PUT | `/api/v1/inventory/material-requests/{request_id}/reject` | Reject Material Request | Bearer token | `application/json -> MaterialRequestReject` | `200 application/json -> MaterialRequestResponse` |
| GET | `/api/v1/inventory/movements` | List Inventory Movements | Bearer token | `None` | `200 application/json -> array[InventoryMovementResponse]` |
| POST | `/api/v1/inventory/movements` | Create Inventory Movement | Bearer token | `application/json -> InventoryMovementCreate` | `201 application/json -> InventoryMovementResponse` |
| GET | `/api/v1/inventory/packing-catalog` | Get Packing Catalog | Bearer token | `None` | `200 application/json -> array[PackingCatalogItem]` |
| POST | `/api/v1/inventory/pick-list/{order_id}` | Pick List | Bearer token | `None` | `200 application/json -> PickingListResponse` |
| GET | `/api/v1/inventory/restock-requests` | List Restock Requests | Bearer token | `None` | `200 application/json -> RestockRequestListResponse` |
| POST | `/api/v1/inventory/restock-requests` | Create Restock Request | Bearer token | `application/json -> RestockRequestCreate` | `201 application/json -> RestockRequestResponse` |
| POST | `/api/v1/inventory/restock-requests/{request_id}/escalate` | Escalate Restock Request | Bearer token | `None` | `200 application/json -> RestockRequestResponse` |
| PUT | `/api/v1/inventory/restock-requests/{request_id}/status` | Update Restock Request Status | Bearer token | `application/json -> RestockRequestStatusUpdate` | `200 application/json -> RestockRequestResponse` |
| DELETE | `/api/v1/inventory/{item_id}` | Delete Inventory Item | Bearer token | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/inventory/{item_id}` | Get Inventory Item | Bearer token | `None` | `200 application/json -> InventoryResponse` |
| PUT | `/api/v1/inventory/{item_id}` | Update Inventory Item | Bearer token | `application/json -> InventoryUpdate` | `200 application/json -> InventoryResponse` |

## Labourers

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/labourers` | List Labourers | Bearer token | `None` | `200 application/json -> LabourerListResponse` |
| POST | `/api/v1/labourers` | Create Labourer | Bearer token | `application/json -> LabourerCreate` | `201 application/json -> LabourerResponse` |
| GET | `/api/v1/labourers/availability` | Availability | Bearer token | `None` | `200 application/json -> LabourAvailabilityResponse` |
| DELETE | `/api/v1/labourers/{labourer_id}` | Delete Labourer | Bearer token | `None` | `204` |
| GET | `/api/v1/labourers/{labourer_id}` | Get Labourer | Bearer token | `None` | `200 application/json -> LabourerResponse` |
| PUT | `/api/v1/labourers/{labourer_id}` | Update Labourer | Bearer token | `application/json -> LabourerUpdate` | `200 application/json -> LabourerResponse` |
| POST | `/api/v1/labourers/{labourer_id}/assign/{order_id}` | Assign Labourer | Bearer token | `None` | `200 application/json -> AssignLabourResponse` |
| POST | `/api/v1/labourers/{labourer_id}/check-in` | Check In | Bearer token | `None` | `200 application/json -> LabourAttendanceResponse` |
| POST | `/api/v1/labourers/{labourer_id}/check-out` | Check Out | Bearer token | `None` | `200 application/json -> LabourAttendanceResponse` |

## Live Tracking

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/tracking/drivers` | Get Active Driver Locations | Bearer token | `None` | `200 application/json -> array[DriverLocationItem]` |
| GET | `/api/v1/tracking/orders/{order_id}/driver` | Get Order Driver Location | Bearer token | `None` | `200 application/json -> DriverLocationItem / null` |

## Logistics Manager

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/logistics/ai/query` | Ai Query | Bearer token | `application/json -> LogisticsAiQueryRequest` | `200 application/json -> LogisticsAiQueryResponse` |
| GET | `/api/v1/logistics/alerts` | List Alerts | Bearer token | `None` | `200 application/json -> array[LogisticsAlertItem]` |
| POST | `/api/v1/logistics/alerts` | Create Alert | Bearer token | `application/json -> Payload` | `200 application/json -> Response Create Alert Api V1 Logistics Alerts Post` |
| POST | `/api/v1/logistics/alerts/{alert_id}/resolve` | Resolve Alert | Bearer token | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/logistics/bootstrap` | Bootstrap | Bearer token | `None` | `200 application/json -> LogisticsBootstrapResponse` |
| POST | `/api/v1/logistics/capital-investment` | Create Capital Investment | Bearer token | `application/json -> CapitalInvestmentCreate` | `201 application/json -> Response Create Capital Investment Api V1 Logistics Capital Investment Post` |
| GET | `/api/v1/logistics/chats` | List Chats | Bearer token | `None` | `200 application/json -> array[LogisticsChatThreadItem]` |
| POST | `/api/v1/logistics/chats` | Create Chat | Bearer token | `application/json -> LogisticsChatThreadCreate` | `201 application/json -> LogisticsChatThreadItem` |
| DELETE | `/api/v1/logistics/chats/{thread_id}` | Delete Chat | Bearer token | `None` | `200 application/json -> MessageResponse` |
| PUT | `/api/v1/logistics/chats/{thread_id}` | Update Chat | Bearer token | `application/json -> LogisticsChatThreadUpdate` | `200 application/json -> LogisticsChatThreadItem` |
| POST | `/api/v1/logistics/chats/{thread_id}/messages` | Add Chat Message | Bearer token | `application/json -> LogisticsChatMessageCreate` | `200 application/json -> LogisticsChatThreadItem` |
| GET | `/api/v1/logistics/dispatch-contacts` | Get Dispatch Contacts | Bearer token | `None` | `200 application/json -> array[DispatchContactItem]` |
| POST | `/api/v1/logistics/documents` | Create Document | Bearer token | `application/json -> LogisticsDocumentCreate` | `201 application/json -> LogisticsDocumentItem` |
| PUT | `/api/v1/logistics/documents/{doc_id}/status` | Update Document Status | Bearer token | `application/json -> LogisticsDocumentUpdateStatus` | `200 application/json -> LogisticsDocumentItem` |
| GET | `/api/v1/logistics/drivers` | List Drivers | Bearer token | `None` | `200 application/json -> array[LogisticsDriverItem]` |
| POST | `/api/v1/logistics/drivers` | Create Driver | Bearer token | `application/json -> LogisticsDriverCreate` | `201 application/json -> LogisticsDriverItem` |
| GET | `/api/v1/logistics/drivers/me/audit` | Get Driver Audit | Bearer token | `None` | `200 application/json -> array[DriverAuditEventItem]` |
| POST | `/api/v1/logistics/drivers/me/bind-vehicle` | Bind Driver Vehicle | Bearer token | `application/json -> DriverVehicleBindRequest` | `200 application/json -> LogisticsVehicleItem` |
| POST | `/api/v1/logistics/drivers/me/cashout` | Request Cashout | Bearer token | `application/json -> DriverCashoutRequest` | `200 application/json -> Response Request Cashout Api V1 Logistics Drivers Me Cashout Post` |
| GET | `/api/v1/logistics/drivers/me/crew` | Get Driver Crew | Bearer token | `None` | `200 application/json -> array[DriverCrewMemberItem]` |
| POST | `/api/v1/logistics/drivers/me/crew/{labourer_id}/check-in` | Check In Driver Crew Member | Bearer token | `None` | `200 application/json -> DriverCrewMemberItem` |
| POST | `/api/v1/logistics/drivers/me/crisis-alert` | Send Driver Crisis Alert | Bearer token | `application/json -> Payload` | `200 application/json -> Response Send Driver Crisis Alert Api V1 Logistics Drivers Me Crisis Alert Post` |
| GET | `/api/v1/logistics/drivers/me/dashboard` | Get Driver Dashboard | Bearer token | `None` | `200 application/json -> DriverDashboardContext` |
| GET | `/api/v1/logistics/drivers/me/dispatch-thread` | Get Dispatch Thread | Bearer token | `None` | `200 application/json -> DriverDispatchThreadItem` |
| POST | `/api/v1/logistics/drivers/me/dispatch-thread/messages` | Send Dispatch Message | Bearer token | `application/json -> DriverDispatchMessageCreate` | `200 application/json -> DriverDispatchThreadItem` |
| POST | `/api/v1/logistics/drivers/me/fuel-receipt` | Submit Fuel Receipt | Bearer token | `application/json -> DriverFuelReceiptCreate` | `200 application/json -> Response Submit Fuel Receipt Api V1 Logistics Drivers Me Fuel Receipt Post` |
| GET | `/api/v1/logistics/drivers/me/hos` | Get Driver Hos | Bearer token | `None` | `200 application/json -> DriverHosSummary` |
| POST | `/api/v1/logistics/drivers/me/location` | Update Driver Location | Bearer token | `application/json -> LocationUpdateParams` | `200 application/json -> Response Update Driver Location Api V1 Logistics Drivers Me Location Post` |
| GET | `/api/v1/logistics/drivers/me/manager-thread` | Get Manager Thread | Bearer token | `None` | `200 application/json -> DriverDispatchThreadItem` |
| POST | `/api/v1/logistics/drivers/me/manager-thread/messages` | Send Manager Message | Bearer token | `application/json -> DriverDispatchMessageCreate` | `200 application/json -> DriverDispatchThreadItem` |
| GET | `/api/v1/logistics/drivers/me/notifications` | Get Driver Notifications | Bearer token | `None` | `200 application/json -> array[LogisticsNotificationItem]` |
| POST | `/api/v1/logistics/drivers/me/return-vehicle` | Return Vehicle | Bearer token | `application/json -> VehicleReturnRequest` | `200 application/json -> Response Return Vehicle Api V1 Logistics Drivers Me Return Vehicle Post` |
| GET | `/api/v1/logistics/drivers/me/shift` | Get Driver Shift | Bearer token | `None` | `200 application/json -> DriverShiftSummary` |
| POST | `/api/v1/logistics/drivers/me/shift/end` | End Shift | Bearer token | `None` | `200 application/json -> Response End Shift Api V1 Logistics Drivers Me Shift End Post` |
| POST | `/api/v1/logistics/drivers/me/shift/start` | Start Shift | Bearer token | `None` | `200 application/json -> Response Start Shift Api V1 Logistics Drivers Me Shift Start Post` |
| GET | `/api/v1/logistics/drivers/me/telemetry` | Get Driver Telemetry | Bearer token | `None` | `200 application/json -> DriverTelemetryResponse` |
| PUT | `/api/v1/logistics/drivers/{driver_id}` | Update Driver | Bearer token | `application/json -> LogisticsDriverUpdate` | `200 application/json -> LogisticsDriverItem` |
| PUT | `/api/v1/logistics/escalations/{escalation_id}` | Update Escalation Status | Bearer token | `application/json -> LogisticsEscalationStatusUpdate` | `200 application/json -> LogisticsEscalationItem` |
| GET | `/api/v1/logistics/manifests` | List Manifests | Bearer token | `None` | `200 application/json -> array[LogisticsManifestItem]` |
| POST | `/api/v1/logistics/manifests` | Create Manifest | Bearer token | `application/json -> LogisticsManifestCreate` | `201 application/json -> LogisticsManifestItem` |
| POST | `/api/v1/logistics/manifests/{manifest_id}/push` | Push Manifest | Bearer token | `None` | `200 application/json -> LogisticsManifestItem` |
| GET | `/api/v1/logistics/meeting-participants` | List Meeting Participants | Bearer token | `None` | `200 application/json -> array[LogisticsMeetingParticipantItem]` |
| GET | `/api/v1/logistics/meetings` | List Meetings | Bearer token | `None` | `200 application/json -> array[LogisticsMeetingItem]` |
| POST | `/api/v1/logistics/meetings` | Create Meeting | Bearer token | `application/json -> LogisticsMeetingCreate` | `201 application/json -> LogisticsMeetingItem` |
| DELETE | `/api/v1/logistics/meetings/{meeting_id}` | Delete Meeting | Bearer token | `None` | `200 application/json -> MessageResponse` |
| PUT | `/api/v1/logistics/meetings/{meeting_id}` | Update Meeting | Bearer token | `application/json -> LogisticsMeetingUpdate` | `200 application/json -> LogisticsMeetingItem` |
| DELETE | `/api/v1/logistics/notifications` | Clear Notifications | Bearer token | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/logistics/notifications` | Get Notifications | Bearer token | `None` | `200 application/json -> array[LogisticsNotificationItem]` |
| POST | `/api/v1/logistics/notifications/broadcast` | Send Broadcast | Bearer token | `application/json -> Payload` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/logistics/notifications/mark-all-read` | Mark All Notifications Read | Bearer token | `None` | `200 application/json -> MessageResponse` |
| PUT | `/api/v1/logistics/notifications/{notification_id}` | Update Notification | Bearer token | `application/json -> LogisticsNotificationUpdate` | `200 application/json -> LogisticsNotificationItem` |
| PUT | `/api/v1/logistics/returns/{case_id}` | Update Return Case | Bearer token | `application/json -> LogisticsReturnCaseUpdate` | `200 application/json -> LogisticsReturnCaseItem` |
| POST | `/api/v1/logistics/returns/{case_id}/issue-refund` | Issue Return Refund | Bearer token | `None` | `200 application/json -> None` |
| POST | `/api/v1/logistics/returns/{case_id}/schedule-pickup` | Schedule Return Pickup | Bearer token | `None` | `200 application/json -> LogisticsReturnCaseItem` |
| GET | `/api/v1/logistics/tasks` | List Tasks | Bearer token | `None` | `200 application/json -> array[LogisticsTaskItem]` |
| POST | `/api/v1/logistics/tasks` | Create Task | Bearer token | `application/json -> LogisticsTaskCreate` | `201 application/json -> LogisticsTaskItem` |
| DELETE | `/api/v1/logistics/tasks/{task_id}` | Delete Task | Bearer token | `None` | `200 application/json -> MessageResponse` |
| PUT | `/api/v1/logistics/tasks/{task_id}` | Update Task | Bearer token | `application/json -> LogisticsTaskUpdate` | `200 application/json -> LogisticsTaskItem` |
| POST | `/api/v1/logistics/transactions` | Create Transaction | Bearer token | `application/json -> LogisticsTransactionCreate` | `201 application/json -> LogisticsTransactionItem` |
| GET | `/api/v1/logistics/vehicles` | List Vehicles | Bearer token | `None` | `200 application/json -> array[LogisticsVehicleItem]` |
| POST | `/api/v1/logistics/vehicles` | Create Vehicle | Bearer token | `application/json -> LogisticsVehicleCreate` | `201 application/json -> LogisticsVehicleItem` |
| PUT | `/api/v1/logistics/vehicles/{vehicle_id}` | Update Vehicle | Bearer token | `application/json -> LogisticsVehicleUpdate` | `200 application/json -> LogisticsVehicleItem` |
| GET | `/api/v1/logistics/zones` | List Zones | Bearer token | `None` | `200 application/json -> array[LogisticsZoneItem]` |
| POST | `/api/v1/logistics/zones` | Create Zone | Bearer token | `application/json -> LogisticsZoneCreate` | `201 application/json -> LogisticsZoneItem` |
| DELETE | `/api/v1/logistics/zones/{zone_id}` | Delete Zone | Bearer token | `None` | `200 application/json -> MessageResponse` |
| PUT | `/api/v1/logistics/zones/{zone_id}` | Update Zone | Bearer token | `application/json -> LogisticsZoneUpdate` | `200 application/json -> LogisticsZoneItem` |

## Orders

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/orders` | List Orders | Bearer token | `None` | `200 application/json -> OrderListResponse` |
| POST | `/api/v1/orders` | Create Order | Bearer token | `application/json -> OrderCreate` | `201 application/json -> OrderResponse` |
| GET | `/api/v1/orders/ai-driver-suggestions` | Get Ai Driver Suggestions | Bearer token | `None` | `200 application/json -> DriverSuggestionResponse` |
| GET | `/api/v1/orders/assignment-preview` | Get Assignment Preview | Bearer token | `None` | `200 application/json -> OrderAssignmentPreview` |
| POST | `/api/v1/orders/auto-balance` | Auto Balance Drivers | Bearer token | `None` | `200 application/json -> None` |
| POST | `/api/v1/orders/batch-assign` | Batch Assign Orders | Bearer token | `application/json -> BatchConfirmRequest` | `200 application/json -> None` |
| POST | `/api/v1/orders/cluster` | Cluster Orders | Bearer token | `None` | `200 application/json -> None` |
| POST | `/api/v1/orders/optimize-routes` | Optimize Routes | Bearer token | `None` | `200 application/json -> None` |
| GET | `/api/v1/orders/return-suggestions` | Get Return Trip Suggestions | Bearer token | `None` | `200 application/json -> ReturnTripResponse` |
| GET | `/api/v1/orders/track/{tracking_code}` | Track Order | No | `None` | `200 application/json -> None` |
| GET | `/api/v1/orders/trip-intelligence` | List Trip Intelligence | Bearer token | `None` | `200 application/json -> array[OrderTripIntelligenceItem]` |
| GET | `/api/v1/orders/{order_id}` | Get Order | Bearer token | `None` | `200 application/json -> OrderResponse` |
| PUT | `/api/v1/orders/{order_id}` | Update Order | Bearer token | `application/json -> OrderUpdate` | `200 application/json -> OrderResponse` |
| POST | `/api/v1/orders/{order_id}/asset-log` | Save Asset Log | Bearer token | `application/json -> AssetLogRequest` | `200 application/json -> None` |
| POST | `/api/v1/orders/{order_id}/assign` | Assign Order | Bearer token | `application/json -> OrderAssignRequest` | `200 application/json -> OrderResponse` |
| POST | `/api/v1/orders/{order_id}/cancel` | Cancel Order | Bearer token | `application/json -> CancelOrderRequest` | `200 application/json -> OrderResponse` |
| POST | `/api/v1/orders/{order_id}/complete-return` | Complete Return Order | Bearer token | `None` | `200 application/json -> OrderResponse` |
| POST | `/api/v1/orders/{order_id}/confirm` | Confirm Order | Bearer token | `None` | `200 application/json -> OrderResponse` |
| POST | `/api/v1/orders/{order_id}/delivery-otp/send` | Send Delivery Otp | Bearer token | `application/json -> DeliveryOtpSendRequest` | `200 application/json -> DeliveryOtpSendResponse` |
| POST | `/api/v1/orders/{order_id}/escalate` | Escalate Order | Bearer token | `application/json -> OrderEscalateRequest` | `200 application/json -> LogisticsEscalationItem` |
| POST | `/api/v1/orders/{order_id}/house-shift-signoff` | House Shift Signoff | Bearer token | `application/json -> HouseShiftSignoffRequest` | `200 application/json -> OrderResponse` |
| GET | `/api/v1/orders/{order_id}/items` | Get Order Items | Bearer token | `None` | `200 application/json -> array[OrderItemResponse]` |
| POST | `/api/v1/orders/{order_id}/items` | Upsert Items | Bearer token | `application/json -> array[OrderItemUpsert]` | `200 application/json -> array[OrderItemResponse]` |
| POST | `/api/v1/orders/{order_id}/job-rating` | Submit Job Rating | Bearer token | `application/json -> JobRatingRequest` | `200 application/json -> OrderResponse` |
| POST | `/api/v1/orders/{order_id}/packing-return` | Submit Packing Return | Bearer token | `application/json -> PackingReturnRequest` | `200 application/json -> OrderResponse` |
| POST | `/api/v1/orders/{order_id}/pay` | Pay Order | Bearer token | `application/json -> PayOrderRequest` | `200 application/json -> None` |
| GET | `/api/v1/orders/{order_id}/proof-of-delivery` | Get Proof Of Delivery Html | Bearer token | `None` | `200 text/html -> string` |
| POST | `/api/v1/orders/{order_id}/proof-of-delivery` | Upload Proof Of Delivery | Bearer token | `application/json -> PODRequest` | `200 application/json -> OrderResponse` |
| POST | `/api/v1/orders/{order_id}/simulate-arrival` | Simulate Driver Arrival | Bearer token | `None` | `200 application/json -> Response Simulate Driver Arrival Api V1 Orders  Order Id  Simulate Arrival Post` |
| POST | `/api/v1/orders/{order_id}/transition` | Transition Order | Bearer token | `application/json -> Data` | `200 application/json -> OrderResponse` |
| GET | `/api/v1/orders/{order_id}/trip-intelligence` | Get Trip Intelligence | Bearer token | `None` | `200 application/json -> OrderTripIntelligenceItem` |
| POST | `/api/v1/orders/{order_id}/trip-intelligence/deviation` | Report Trip Deviation | Bearer token | `application/json -> TripDeviationReportRequest` | `200 application/json -> Response Report Trip Deviation Api V1 Orders  Order Id  Trip Intelligence Deviation Post` |
| POST | `/api/v1/orders/{order_id}/trip-intelligence/push` | Push Trip Command | Bearer token | `application/json -> TripCommandPushRequest` | `200 application/json -> Response Push Trip Command Api V1 Orders  Order Id  Trip Intelligence Push Post` |
| POST | `/api/v1/orders/{order_id}/wallet-pay` | Pay Order With Wallet | Bearer token | `application/json -> WalletPaymentRequest` | `200 application/json -> WalletPaymentResponse` |

## Rates

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/rates` | Get current rate configuration | No | `None` | `200 application/json -> Response Get Rates Api V1 Rates Get` |
| PUT | `/api/v1/rates` | Update rate configuration (LOGISTIC_MANAGER only) | Bearer token | `application/json -> Payload` | `200 application/json -> Response Update Rates Api V1 Rates Put` |
| GET | `/api/v1/rates/inventory-seeded` | Check if packing materials have been seeded to inventory (LOGISTIC_MANAGER only) | Bearer token | `None` | `200 application/json -> Response Check Inventory Seeded Api V1 Rates Inventory Seeded Get` |
| POST | `/api/v1/rates/seed-inventory` | One-time seed packing materials from rate governance to all warehouse inventories (LOGISTIC_MANAGER only) | Bearer token | `None` | `200 application/json -> Response Seed Inventory Api V1 Rates Seed Inventory Post` |

## Users

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/users` | List Users | Bearer token | `None` | `200 application/json -> UserListResponse` |
| POST | `/api/v1/users` | Create User | Bearer token | `application/json -> UserAdminCreate` | `201 application/json -> UserAdminResponse` |
| DELETE | `/api/v1/users/{user_id}` | Soft Delete User | Bearer token | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/users/{user_id}` | Get User | Bearer token | `None` | `200 application/json -> UserAdminResponse` |
| PUT | `/api/v1/users/{user_id}` | Update User | Bearer token | `application/json -> UserAdminUpdate` | `200 application/json -> UserAdminResponse` |
| POST | `/api/v1/users/{user_id}/assign-role` | Assign Role | Bearer token | `application/json -> AssignRoleRequest` | `200 application/json -> UserAdminResponse` |
| POST | `/api/v1/users/{user_id}/assign-warehouse` | Assign Warehouse | Bearer token | `application/json -> AssignWarehouseRequest` | `200 application/json -> UserAdminResponse` |

## Vendor

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/vendor/api-keys` | List Api Keys | Bearer token | `None` | `200 application/json -> array[VendorApiKeyResponse]` |
| POST | `/api/v1/vendor/api-keys` | Create Api Key | Bearer token | `application/json -> VendorApiKeyCreate` | `200 application/json -> VendorApiKeyResponse` |
| POST | `/api/v1/vendor/api-keys/{key_id}/revoke` | Revoke Api Key | Bearer token | `None` | `200 application/json -> VendorApiKeyResponse` |
| GET | `/api/v1/vendor/bulk-uploads` | List Bulk Uploads | Bearer token | `None` | `200 application/json -> array[VendorBulkUploadResponse]` |
| POST | `/api/v1/vendor/bulk-uploads` | Create Bulk Upload | Bearer token | `application/json -> VendorBulkUploadCreate` | `200 application/json -> VendorBulkUploadResponse` |
| PUT | `/api/v1/vendor/bulk-uploads/{upload_id}` | Update Bulk Upload | Bearer token | `application/json -> VendorBulkUploadUpdate` | `200 application/json -> VendorBulkUploadResponse` |
| GET | `/api/v1/vendor/damage-reports` | Get Damage Reports | Bearer token | `None` | `200 application/json -> VendorDamageReportsResponse` |
| POST | `/api/v1/vendor/damage-reports` | Create Damage Report | Bearer token | `application/json -> VendorDamageReportCreate` | `200 application/json -> VendorDamageReport` |
| GET | `/api/v1/vendor/dashboard` | Get Dashboard | Bearer token | `None` | `200 application/json -> VendorDashboardResponse` |
| POST | `/api/v1/vendor/invoices/{order_id}/pay` | Pay Invoice | Bearer token | `application/json -> VendorInvoicePayRequest` | `200 application/json -> VendorInvoiceRecord` |
| DELETE | `/api/v1/vendor/notifications` | Clear Notifications | Bearer token | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/vendor/notifications` | Get Notifications | Bearer token | `None` | `200 application/json -> array[LogisticsNotificationItem]` |
| POST | `/api/v1/vendor/notifications/mark-all-read` | Mark All Notifications Read | Bearer token | `None` | `200 application/json -> MessageResponse` |
| PUT | `/api/v1/vendor/notifications/{notification_id}` | Update Notification | Bearer token | `application/json -> LogisticsNotificationUpdate` | `200 application/json -> LogisticsNotificationItem` |
| GET | `/api/v1/vendor/recurring-rules` | List Recurring Rules | Bearer token | `None` | `200 application/json -> array[VendorRecurringRuleResponse]` |
| POST | `/api/v1/vendor/recurring-rules` | Create Recurring Rule | Bearer token | `application/json -> VendorRecurringRuleCreate` | `200 application/json -> VendorRecurringRuleResponse` |
| DELETE | `/api/v1/vendor/recurring-rules/{rule_id}` | Delete Recurring Rule | Bearer token | `None` | `200 application/json -> None` |
| PUT | `/api/v1/vendor/recurring-rules/{rule_id}` | Update Recurring Rule | Bearer token | `application/json -> VendorRecurringRuleCreate` | `200 application/json -> VendorRecurringRuleResponse` |
| POST | `/api/v1/vendor/recurring-rules/{rule_id}/toggle` | Toggle Recurring Rule | Bearer token | `None` | `200 application/json -> VendorRecurringRuleResponse` |
| GET | `/api/v1/vendor/settings` | Get Settings | Bearer token | `None` | `200 application/json -> VendorSettingsResponse` |
| PUT | `/api/v1/vendor/settings` | Update Settings | Bearer token | `application/json -> VendorSettings` | `200 application/json -> VendorSettingsResponse` |
| GET | `/api/v1/vendor/shipments` | Get Shipments | Bearer token | `None` | `200 application/json -> VendorShipmentsResponse` |
| GET | `/api/v1/vendor/support-tickets` | List Support Tickets | Bearer token | `None` | `200 application/json -> array[VendorSupportTicketResponse]` |
| POST | `/api/v1/vendor/support-tickets` | Create Support Ticket | Bearer token | `application/json -> VendorSupportTicketCreate` | `200 application/json -> VendorSupportTicketResponse` |
| POST | `/api/v1/vendor/support-tickets/{ticket_id}/reply` | Reply Support Ticket | Bearer token | `application/json -> VendorSupportReplyCreate` | `200 application/json -> VendorSupportTicketResponse` |
| POST | `/api/v1/vendor/support-tickets/{ticket_id}/resolve` | Resolve Support Ticket | Bearer token | `None` | `200 application/json -> VendorSupportTicketResponse` |
| GET | `/api/v1/vendor/team-members` | List Team Members | Bearer token | `None` | `200 application/json -> array[VendorTeamMemberResponse]` |
| POST | `/api/v1/vendor/team-members` | Create Team Member | Bearer token | `application/json -> VendorTeamMemberCreate` | `200 application/json -> VendorTeamMemberResponse` |
| DELETE | `/api/v1/vendor/team-members/{member_id}` | Delete Team Member | Bearer token | `None` | `200 application/json -> None` |
| GET | `/api/v1/vendor/wallet` | Get Wallet | Bearer token | `None` | `200 application/json -> WalletSummary` |
| POST | `/api/v1/vendor/wallet/top-up` | Top Up Wallet | Bearer token | `application/json -> WalletTopUpRequest` | `200 application/json -> WalletTopUpResponse` |

## Warehouse Operations

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/inbound` | Get Inbound Overview | Bearer token | `None` | `200 application/json -> InboundResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/inbound/schedule` | Schedule Inbound Delivery | Bearer token | `application/json -> ScheduleInboundRequest` | `201 application/json -> MessageResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/loading-docks` | List Loading Docks | Bearer token | `None` | `200 application/json -> LoadingDockListResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/loading-docks` | Create Loading Dock | Bearer token | `application/json -> LoadingDockCreate` | `201 application/json -> LoadingDockResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/assign` | Assign Truck To Dock | Bearer token | `application/json -> AssignTruckRequest` | `200 application/json -> LoadingDockResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/maintenance` | Set Dock Maintenance | Bearer token | `None` | `200 application/json -> LoadingDockResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/release` | Release Dock | Bearer token | `application/json -> DockVerificationData` | `200 application/json -> LoadingDockResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/accept` | Accept Order | Bearer token | `None` | `200 application/json -> PickingResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/ai-receive-plan` | Get Inbound Receive Plan | Bearer token | `None` | `200 application/json -> InboundReceivePlanResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/complete-packing` | Complete Packing | Bearer token | `None` | `200 application/json -> PickingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/complete-picking` | Complete Picking | Bearer token | `None` | `200 application/json -> PickingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/generate-take-back` | Generate Take Back | Bearer token | `None` | `200 application/json -> PickingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/mark-arrived` | Mark Arrived | Bearer token | `None` | `200 application/json -> PickingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/pick-item` | Confirm Pick Item | Bearer token | `application/json -> ConfirmPickItemRequest` | `200 application/json -> PickedItemResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/pick-progress` | Get Pick Progress | Bearer token | `None` | `200 application/json -> PickProgressResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/quality-check` | Create Quality Check | Bearer token | `None` | `201 application/json -> QualityCheckResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/receive-inbound` | Receive Inbound | Bearer token | `None` | `200 application/json -> PickingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/report-damage` | Report Inbound Damage | Bearer token | `application/json -> InboundDamageReport` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/report-mismatch` | Report Inbound Mismatch | Bearer token | `application/json -> InboundMismatchReport` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/revert-picking` | Revert Picking | Bearer token | `None` | `200 application/json -> PickingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-packing` | Start Packing | Bearer token | `application/json -> StartPackingRequest` | `200 application/json -> PickingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-picking` | Start Picking | Bearer token | `application/json -> StartPickingRequest` | `200 application/json -> PickingResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/packing-stations` | List Packing Stations | Bearer token | `None` | `200 application/json -> PackingStationListResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/packing-stations` | Create Packing Station | Bearer token | `application/json -> PackingStationCreate` | `201 application/json -> PackingStationResponse` |
| PUT | `/api/v1/warehouses/{warehouse_id}/operations/packing-stations/{station_id}` | Update Packing Station | Bearer token | `application/json -> PackingStationUpdate` | `200 application/json -> PackingStationResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/performance` | Get Performance | Bearer token | `None` | `200 application/json -> PerformanceResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/quality-checks` | List Quality Checks | Bearer token | `None` | `200 application/json -> QualityCheckListResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id}` | Get Quality Check | Bearer token | `None` | `200 application/json -> QualityCheckResponse` |
| PUT | `/api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id}` | Update Quality Check | Bearer token | `application/json -> QualityCheckUpdate` | `200 application/json -> QualityCheckResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id}/pass` | Pass Quality Check | Bearer token | `None` | `200 application/json -> QualityCheckResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/returns` | List Return Gradings | Bearer token | `None` | `200 application/json -> ReturnGradingListResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/returns` | Create Return Grading | Bearer token | `application/json -> ReturnGradingCreate` | `201 application/json -> ReturnGradingResponse` |
| PUT | `/api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}` | Update Return Grading | Bearer token | `application/json -> ReturnGradingUpdate` | `200 application/json -> ReturnGradingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}/complete` | Complete Return Grading | Bearer token | `None` | `200 application/json -> ReturnGradingResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}/photo` | Upload Damage Photo | Bearer token | `multipart/form-data -> Body_upload_damage_photo_api_v1_warehouses__warehouse_id__operations_returns__grading_id__photo_post` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/operations/zones/metrics` | Record Zone Metrics | Bearer token | `application/json -> ZoneMetricsCreate` | `201 application/json -> ZoneMetricsResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/operations/zones/{zone_id}/metrics` | Get Zone Metrics | Bearer token | `None` | `200 application/json -> ZoneMetricsListResponse` |

## Warehouses

| Method | Path | Feature | Auth | Request Body | Success Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/warehouses` | List Warehouses | Bearer token | `None` | `200 application/json -> WarehouseListResponse` |
| POST | `/api/v1/warehouses` | Create Warehouse | Bearer token | `application/json -> WarehouseCreate` | `201 application/json -> WarehouseResponse` |
| DELETE | `/api/v1/warehouses/{warehouse_id}` | Delete Warehouse | Bearer token | `None` | `200 application/json -> MessageResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}` | Get Warehouse | Bearer token | `None` | `200 application/json -> WarehouseResponse` |
| PUT | `/api/v1/warehouses/{warehouse_id}` | Update Warehouse | Bearer token | `application/json -> WarehouseUpdate` | `200 application/json -> WarehouseResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/dashboard` | Warehouse Dashboard | Bearer token | `None` | `200 application/json -> WarehouseDashboardResponse` |
| PUT | `/api/v1/warehouses/{warehouse_id}/floor-plan` | Update Floor Plan | Bearer token | `application/json -> FloorPlanUpdate` | `200 application/json -> WarehouseResponse` |
| GET | `/api/v1/warehouses/{warehouse_id}/kpis` | Warehouse Kpis | Bearer token | `None` | `200 application/json -> WarehouseKPIResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/orders/{order_id}/complete` | Mark Order Complete | Bearer token | `None` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/orders/{order_id}/reassign` | Reassign Order To Labor | Bearer token | `None` | `200 application/json -> MessageResponse` |
| POST | `/api/v1/warehouses/{warehouse_id}/restock` | Process Restock | Bearer token | `None` | `200 application/json -> MessageResponse` |

