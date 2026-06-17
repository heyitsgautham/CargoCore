# Logistics & Move Management API
**Version:** 1.0.0
**Description:** Backend API for the Logistics & Personal Move Management System
---

## AI

### POST `/api/v1/ai/estimate-image`
**Summary:** Analyze a room photo for moving estimate
**Description:** Upload an image. Gemini Vision detects items and returns a moving estimate.

**Request Body:**
- Content-Type: `multipart/form-data`
- Schema: `Body_estimate_image_api_v1_ai_estimate_image_post`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/ai/chat`
**Summary:** Send a message to the AI chatbot
**Description:** Send a natural language message. The AI decides whether to query the database or respond directly. Pass `session_id` to continue an existing conversation, or omit it to start a new one.

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `ChatRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/ai/conversations/{session_id}`
**Summary:** Get conversation history
**Description:** Retrieve all messages for a specific conversation session.

**Authentication Required:** Yes

**Parameters:**
- `session_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/ai/sessions`
**Summary:** List chat sessions
**Description:** List all conversation sessions for the current user, most recent first.

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/ai/escalate/{conversation_id}`
**Summary:** Escalate conversation to human agent
**Description:** Flag a conversation for human review. The conversation must belong to the requesting user.

**Authentication Required:** Yes

**Parameters:**
- `conversation_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `EscalateRequest`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/ai/escalations`
**Summary:** List escalations
**Description:** Human agent view: list all escalations. Use ?status=OPEN or ?status=RESOLVED to filter.

**Authentication Required:** Yes

**Parameters:**
- `status` (query) [Optional] - *string* - Filter by status: OPEN or RESOLVED

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/ai/escalations/{escalation_id}/resolve`
**Summary:** Resolve an escalation
**Description:** Mark an escalation as resolved. Restricted to LOGISTIC_MANAGER and AI_AGENT roles.

**Authentication Required:** Yes

**Parameters:**
- `escalation_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Authentication

### POST `/api/v1/auth/register`
**Summary:** Self-service sign-up (Individual & Vendor only)
**Description:** Creates a new account for **INDIVIDUAL** or **VENDOR** roles only. Logistic Manager is pre-seeded at deployment. Warehouse Manager, Dispatcher, and Driver accounts are provisioned by the Logistic Manager via the /users admin endpoint.

**Request Body:**
- Content-Type: `application/json`
- Schema: `UserRegister`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/login`
**Summary:** Issue JWT tokens with user profile

**Request Body:**
- Content-Type: `application/json`
- Schema: `UserLogin`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/token`
**Summary:** Issue OAuth2 bearer token for Swagger UI
**Description:** Form-based OAuth2 password flow endpoint used by Swagger UI's `Authorize` dialog. Enter your email or username in the `username` field. Use `/api/v1/auth/login` if you need the JSON response that also includes the user profile.

**Request Body:**
- Content-Type: `application/x-www-form-urlencoded`
- Schema: `Body_token_login_api_v1_auth_token_post`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/refresh`
**Summary:** Refresh access token

**Request Body:**
- Content-Type: `application/json`
- Schema: `RefreshTokenRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/logout`
**Summary:** Invalidate access token via Redis blacklist

**Parameters:**
- `authorization` (header) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/auth/me`
**Summary:** Get current user profile

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### PUT `/api/v1/auth/me`
**Summary:** Update current user profile

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `UserProfileUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/change-password`
**Summary:** Change password

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `ChangePasswordRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/forgot-password`
**Summary:** Request password reset email

**Request Body:**
- Content-Type: `application/json`
- Schema: `ForgotPasswordRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/reset-password`
**Summary:** Confirm password reset with token

**Request Body:**
- Content-Type: `application/json`
- Schema: `ResetPasswordRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/send-otp`
**Summary:** Send email verification OTP for signup

**Request Body:**
- Content-Type: `application/json`
- Schema: `SendOTPRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/verify-otp`
**Summary:** Verify email OTP before completing signup

**Request Body:**
- Content-Type: `application/json`
- Schema: `VerifyOTPRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/auth/google-login`
**Summary:** Login or Register with Google

**Request Body:**
- Content-Type: `application/json`
- Schema: `GoogleLoginRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Customer

### GET `/api/v1/customer/dashboard`
**Summary:** Get Dashboard

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/customer/tracking`
**Summary:** Get Tracking

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/customer/payments`
**Summary:** Get Payments

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/customer/profile`
**Summary:** Get Profile

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/customer/quotes`
**Summary:** Get Quotes

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/customer/quotes/{quote_id}/convert`
**Summary:** Convert Quote

**Authentication Required:** Yes

**Parameters:**
- `quote_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/customer/damage-reports`
**Summary:** Get Damage Reports

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/customer/damage-reports`
**Summary:** Create Damage Report

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `CustomerDamageReportCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/customer/settings`
**Summary:** Get Settings

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### PUT `/api/v1/customer/settings`
**Summary:** Update Settings

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `CustomerSettings`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/customer/wallet`
**Summary:** Get Wallet

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

## Finance

### GET `/api/v1/finance/summary`
**Summary:** Get Finance Summary
**Description:** Live-computed financial summary.
Returns ₹0 for all values when the database is empty.

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

## Geocoding

### GET `/api/v1/geocoding/search`
**Summary:** Search Addresses
**Description:** Search for addresses using OpenStreetMap Nominatim.
No authentication required - public endpoint.

**Parameters:**
- `q` (query) [Required] - *string* - Search query for address
- `limit` (query) [Optional] - *integer* - Maximum number of results

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/geocoding/reverse`
**Summary:** Reverse Geocode
**Description:** Reverse geocode coordinates to address.
No authentication required - public endpoint.

**Parameters:**
- `lat` (query) [Required] - *number* - Latitude
- `lon` (query) [Required] - *number* - Longitude

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Health

### GET `/health`
**Summary:** Health Check

**Responses:**
- **200**: Successful Response

---

## Inventory

### GET `/api/v1/inventory`
**Summary:** List Inventory

**Authentication Required:** Yes

**Parameters:**
- `page` (query) [Optional] - *integer* - N/A
- `page_size` (query) [Optional] - *integer* - N/A
- `warehouse_id` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/inventory`
**Summary:** Create Inventory Item

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `InventoryCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/inventory/categories`
**Summary:** List Inventory Categories

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/inventory/movements`
**Summary:** Create Inventory Movement

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `InventoryMovementCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/inventory/movements`
**Summary:** List Inventory Movements

**Authentication Required:** Yes

**Parameters:**
- `page` (query) [Optional] - *integer* - N/A
- `page_size` (query) [Optional] - *integer* - N/A
- `item_id` (query) [Optional] - *string* - N/A
- `warehouse_id` (query) [Optional] - *string* - N/A
- `reference_order_id` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/inventory/low-stock`
**Summary:** Low Stock

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/inventory/{item_id}`
**Summary:** Get Inventory Item

**Authentication Required:** Yes

**Parameters:**
- `item_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/inventory/{item_id}`
**Summary:** Update Inventory Item

**Authentication Required:** Yes

**Parameters:**
- `item_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `InventoryUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### DELETE `/api/v1/inventory/{item_id}`
**Summary:** Delete Inventory Item

**Authentication Required:** Yes

**Parameters:**
- `item_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/inventory/pick-list/{order_id}`
**Summary:** Pick List

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/inventory/restock-requests`
**Summary:** Create Restock Request

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `RestockRequestCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/inventory/restock-requests`
**Summary:** List Restock Requests

**Authentication Required:** Yes

**Parameters:**
- `page` (query) [Optional] - *integer* - N/A
- `page_size` (query) [Optional] - *integer* - N/A
- `warehouse_id` (query) [Optional] - *string* - N/A
- `status_filter` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/inventory/restock-requests/{request_id}/status`
**Summary:** Update Restock Request Status

**Authentication Required:** Yes

**Parameters:**
- `request_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `RestockRequestStatusUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/inventory/restock-requests/{request_id}/escalate`
**Summary:** Escalate Restock Request
**Description:** Escalate a pending restock request to Logistics Manager urgently.

**Authentication Required:** Yes

**Parameters:**
- `request_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Labourers

### GET `/api/v1/labourers`
**Summary:** List Labourers

**Authentication Required:** Yes

**Parameters:**
- `page` (query) [Optional] - *integer* - N/A
- `page_size` (query) [Optional] - *integer* - N/A
- `warehouse_id` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/labourers`
**Summary:** Create Labourer

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `LabourerCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/labourers/availability`
**Summary:** Availability

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/labourers/{labourer_id}`
**Summary:** Get Labourer

**Authentication Required:** Yes

**Parameters:**
- `labourer_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/labourers/{labourer_id}`
**Summary:** Update Labourer

**Authentication Required:** Yes

**Parameters:**
- `labourer_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LabourerUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### DELETE `/api/v1/labourers/{labourer_id}`
**Summary:** Delete Labourer

**Authentication Required:** Yes

**Parameters:**
- `labourer_id` (path) [Required] - *string* - N/A

**Responses:**
- **204**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/labourers/{labourer_id}/assign/{order_id}`
**Summary:** Assign Labourer

**Authentication Required:** Yes

**Parameters:**
- `labourer_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/labourers/{labourer_id}/check-in`
**Summary:** Check In

**Authentication Required:** Yes

**Parameters:**
- `labourer_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/labourers/{labourer_id}/check-out`
**Summary:** Check Out

**Authentication Required:** Yes

**Parameters:**
- `labourer_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Live Tracking

### GET `/api/v1/tracking/drivers`
**Summary:** Get Active Driver Locations
**Description:** Get real-time locations of all active drivers.
Used by dispatchers/warehouse managers for live map view.

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/tracking/orders/{order_id}/driver`
**Summary:** Get Order Driver Location
**Description:** Get real-time location of the driver assigned to a specific order.
Used by customers to track their delivery.

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Logistics Manager

### GET `/api/v1/logistics/bootstrap`
**Summary:** Bootstrap

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/logistics/ai/query`
**Summary:** Ai Query

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsAiQueryRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/logistics/vehicles`
**Summary:** List Vehicles

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/logistics/vehicles`
**Summary:** Create Vehicle

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsVehicleCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/logistics/drivers`
**Summary:** List Drivers

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/logistics/drivers`
**Summary:** Create Driver

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsDriverCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/logistics/drivers/{driver_id}`
**Summary:** Update Driver

**Authentication Required:** Yes

**Parameters:**
- `driver_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsDriverUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/logistics/vehicles/{vehicle_id}`
**Summary:** Update Vehicle

**Authentication Required:** Yes

**Parameters:**
- `vehicle_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsVehicleUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/logistics/transactions`
**Summary:** Create Transaction

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsTransactionCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/logistics/capital-investment`
**Summary:** Create Capital Investment

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `CapitalInvestmentCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/logistics/returns/{case_id}`
**Summary:** Update Return Case

**Authentication Required:** Yes

**Parameters:**
- `case_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsReturnCaseUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/logistics/zones`
**Summary:** Create Zone

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsZoneCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/logistics/zones/{zone_id}`
**Summary:** Update Zone

**Authentication Required:** Yes

**Parameters:**
- `zone_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsZoneUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### DELETE `/api/v1/logistics/zones/{zone_id}`
**Summary:** Delete Zone

**Authentication Required:** Yes

**Parameters:**
- `zone_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/logistics/chats/{thread_id}/messages`
**Summary:** Add Chat Message

**Authentication Required:** Yes

**Parameters:**
- `thread_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsChatMessageCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/logistics/tasks/{task_id}`
**Summary:** Update Task

**Authentication Required:** Yes

**Parameters:**
- `task_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsTaskUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/logistics/notifications/{notification_id}`
**Summary:** Update Notification

**Authentication Required:** Yes

**Parameters:**
- `notification_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsNotificationUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/logistics/notifications/mark-all-read`
**Summary:** Mark All Notifications Read

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### DELETE `/api/v1/logistics/notifications`
**Summary:** Clear Notifications

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/logistics/alerts`
**Summary:** Create Alert

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/logistics/alerts/{alert_id}/resolve`
**Summary:** Resolve Alert

**Authentication Required:** Yes

**Parameters:**
- `alert_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/logistics/documents`
**Summary:** Create Document

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsDocumentCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/logistics/documents/{doc_id}/status`
**Summary:** Update Document Status

**Authentication Required:** Yes

**Parameters:**
- `doc_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LogisticsDocumentUpdateStatus`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/logistics/drivers/me/dashboard`
**Summary:** Get Driver Dashboard

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/logistics/drivers/me/shift`
**Summary:** Get Driver Shift

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/logistics/drivers/me/hos`
**Summary:** Get Driver Hos

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/logistics/drivers/me/crew`
**Summary:** Get Driver Crew

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/logistics/drivers/me/crew/{labourer_id}/check-in`
**Summary:** Check In Driver Crew Member

**Authentication Required:** Yes

**Parameters:**
- `labourer_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/logistics/drivers/me/telemetry`
**Summary:** Get Driver Telemetry

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/logistics/drivers/me/bind-vehicle`
**Summary:** Bind Driver Vehicle

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `DriverVehicleBindRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/logistics/drivers/me/shift/start`
**Summary:** Start Shift

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/logistics/drivers/me/shift/end`
**Summary:** End Shift

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/logistics/drivers/me/location`
**Summary:** Update Driver Location

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `LocationUpdateParams`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Orders

### POST `/api/v1/orders`
**Summary:** Create Order

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `OrderCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/orders`
**Summary:** List Orders

**Authentication Required:** Yes

**Parameters:**
- `page` (query) [Optional] - *integer* - N/A
- `page_size` (query) [Optional] - *integer* - N/A
- `status_filter` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/cluster`
**Summary:** Cluster Orders

**Authentication Required:** Yes

**Parameters:**
- `radius_km` (query) [Optional] - *number* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/optimize-routes`
**Summary:** Optimize Routes

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/orders/batch-assign`
**Summary:** Batch Assign Orders

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `BatchConfirmRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/orders/{order_id}`
**Summary:** Get Order

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/orders/{order_id}`
**Summary:** Update Order

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `OrderUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/confirm`
**Summary:** Confirm Order

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/assign`
**Summary:** Assign Order

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `OrderAssignRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/transition`
**Summary:** Transition Order

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/cancel`
**Summary:** Cancel Order

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `CancelOrderRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/wallet-pay`
**Summary:** Pay Order With Wallet

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `WalletPaymentRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/orders/track/{tracking_code}`
**Summary:** Track Order

**Parameters:**
- `tracking_code` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/orders/{order_id}/items`
**Summary:** Get Order Items

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/items`
**Summary:** Upsert Items

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/delivery-otp/send`
**Summary:** Send Delivery Otp

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `DeliveryOtpSendRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/proof-of-delivery`
**Summary:** Upload Proof Of Delivery

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `PODRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/orders/{order_id}/proof-of-delivery`
**Summary:** Get Proof Of Delivery Html
**Description:** Generate and return Proof of Delivery HTML document with real data.

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/orders/{order_id}/pay`
**Summary:** Pay Order
**Description:** Record a payment for an order. Online (Razorpay) or COD by driver.

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `PayOrderRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Rates

### GET `/api/v1/rates`
**Summary:** Get current rate configuration

**Responses:**
- **200**: Successful Response

---

### PUT `/api/v1/rates`
**Summary:** Update rate configuration (LOGISTIC_MANAGER only)

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Users

### GET `/api/v1/users`
**Summary:** List Users

**Authentication Required:** Yes

**Parameters:**
- `page` (query) [Optional] - *integer* - N/A
- `page_size` (query) [Optional] - *integer* - N/A
- `role` (query) [Optional] - *string* - N/A
- `warehouse_id` (query) [Optional] - *string* - N/A
- `is_active` (query) [Optional] - *string* - N/A
- `search` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/users`
**Summary:** Create User

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `UserAdminCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/users/{user_id}`
**Summary:** Get User

**Authentication Required:** Yes

**Parameters:**
- `user_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/users/{user_id}`
**Summary:** Update User

**Authentication Required:** Yes

**Parameters:**
- `user_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `UserAdminUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### DELETE `/api/v1/users/{user_id}`
**Summary:** Soft Delete User

**Authentication Required:** Yes

**Parameters:**
- `user_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/users/{user_id}/assign-role`
**Summary:** Assign Role

**Authentication Required:** Yes

**Parameters:**
- `user_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `AssignRoleRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/users/{user_id}/assign-warehouse`
**Summary:** Assign Warehouse

**Authentication Required:** Yes

**Parameters:**
- `user_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `AssignWarehouseRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Vendor

### GET `/api/v1/vendor/dashboard`
**Summary:** Get Dashboard

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/vendor/shipments`
**Summary:** Get Shipments

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### GET `/api/v1/vendor/settings`
**Summary:** Get Settings

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### PUT `/api/v1/vendor/settings`
**Summary:** Update Settings

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorSettings`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/vendor/damage-reports`
**Summary:** Get Damage Reports

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/vendor/damage-reports`
**Summary:** Create Damage Report

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorDamageReportCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/vendor/team-members`
**Summary:** List Team Members

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/vendor/team-members`
**Summary:** Create Team Member

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorTeamMemberCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### DELETE `/api/v1/vendor/team-members/{member_id}`
**Summary:** Delete Team Member

**Authentication Required:** Yes

**Parameters:**
- `member_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/vendor/api-keys`
**Summary:** List Api Keys

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/vendor/api-keys`
**Summary:** Create Api Key

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorApiKeyCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/vendor/api-keys/{key_id}/revoke`
**Summary:** Revoke Api Key

**Authentication Required:** Yes

**Parameters:**
- `key_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/vendor/recurring-rules`
**Summary:** List Recurring Rules

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/vendor/recurring-rules`
**Summary:** Create Recurring Rule

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorRecurringRuleCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/vendor/recurring-rules/{rule_id}`
**Summary:** Update Recurring Rule

**Authentication Required:** Yes

**Parameters:**
- `rule_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorRecurringRuleCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### DELETE `/api/v1/vendor/recurring-rules/{rule_id}`
**Summary:** Delete Recurring Rule

**Authentication Required:** Yes

**Parameters:**
- `rule_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/vendor/recurring-rules/{rule_id}/toggle`
**Summary:** Toggle Recurring Rule

**Authentication Required:** Yes

**Parameters:**
- `rule_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/vendor/bulk-uploads`
**Summary:** List Bulk Uploads

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/vendor/bulk-uploads`
**Summary:** Create Bulk Upload

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorBulkUploadCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/vendor/bulk-uploads/{upload_id}`
**Summary:** Update Bulk Upload

**Authentication Required:** Yes

**Parameters:**
- `upload_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorBulkUploadUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/vendor/support-tickets`
**Summary:** List Support Tickets

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

### POST `/api/v1/vendor/support-tickets`
**Summary:** Create Support Ticket

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorSupportTicketCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/vendor/support-tickets/{ticket_id}/reply`
**Summary:** Reply Support Ticket

**Authentication Required:** Yes

**Parameters:**
- `ticket_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorSupportReplyCreate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/vendor/invoices/{order_id}/pay`
**Summary:** Pay Invoice

**Authentication Required:** Yes

**Parameters:**
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `VendorInvoicePayRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/vendor/support-tickets/{ticket_id}/resolve`
**Summary:** Resolve Support Ticket

**Authentication Required:** Yes

**Parameters:**
- `ticket_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/vendor/wallet`
**Summary:** Get Wallet

**Authentication Required:** Yes

**Responses:**
- **200**: Successful Response

---

## Warehouse Operations

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/accept`
**Summary:** Accept Order
**Description:** Accept an order into the warehouse queue (sets warehouse_substatus = AWAITING_PICK).

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/receive-inbound`
**Summary:** Receive Inbound
**Description:** Mark vendor goods as physically received — transitions AWAITING_INBOUND → AWAITING_PICK.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-picking`
**Summary:** Start Picking
**Description:** Start picking process for an order.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `StartPickingRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/revert-picking`
**Summary:** Revert Picking
**Description:** Undo start-picking: revert order from PICKING back to AWAITING_PICK.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/complete-picking`
**Summary:** Complete Picking
**Description:** Complete picking process for an order.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/pick-item`
**Summary:** Confirm Pick Item
**Description:** Confirm picking of a specific item (supports partial picking).

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `ConfirmPickItemRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/pick-progress`
**Summary:** Get Pick Progress
**Description:** Get picking progress for an order.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/operations/packing-stations`
**Summary:** List Packing Stations
**Description:** Get all packing stations for a warehouse.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/packing-stations`
**Summary:** Create Packing Station
**Description:** Create a new packing station.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `PackingStationCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/warehouses/{warehouse_id}/operations/packing-stations/{station_id}`
**Summary:** Update Packing Station
**Description:** Update a packing station.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `station_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `PackingStationUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/start-packing`
**Summary:** Start Packing
**Description:** Start packing process for an order.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `StartPackingRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/complete-packing`
**Summary:** Complete Packing
**Description:** Complete packing process for an order.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/orders/{order_id}/quality-check`
**Summary:** Create Quality Check
**Description:** Create a new quality check for an order.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/operations/quality-checks`
**Summary:** List Quality Checks
**Description:** List quality checks for a warehouse, optionally filtered by order.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id}`
**Summary:** Get Quality Check
**Description:** Get a quality check by ID.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `check_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id}`
**Summary:** Update Quality Check
**Description:** Update a quality check.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `check_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `QualityCheckUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/quality-checks/{check_id}/pass`
**Summary:** Pass Quality Check
**Description:** Mark a quality check as passed and advance order to QC_PASSED.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `check_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/operations/loading-docks`
**Summary:** List Loading Docks
**Description:** Get all loading docks for a warehouse.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/loading-docks`
**Summary:** Create Loading Dock
**Description:** Create a new loading dock.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `LoadingDockCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/assign`
**Summary:** Assign Truck To Dock
**Description:** Assign a truck to a loading dock.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `dock_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `AssignTruckRequest`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/release`
**Summary:** Release Dock
**Description:** Release a loading dock after verification.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `dock_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `DockVerificationData`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/loading-docks/{dock_id}/maintenance`
**Summary:** Set Dock Maintenance
**Description:** Set dock maintenance status.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `dock_id` (path) [Required] - *string* - N/A
- `is_maintenance` (query) [Optional] - *boolean* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/operations/returns`
**Summary:** List Return Gradings
**Description:** Get all return gradings for a warehouse.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `status_filter` (query) [Optional] - *string* - N/A
- `page` (query) [Optional] - *integer* - N/A
- `page_size` (query) [Optional] - *integer* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/returns`
**Summary:** Create Return Grading
**Description:** Create a new return grading.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `ReturnGradingCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}`
**Summary:** Update Return Grading
**Description:** Update a return grading.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `grading_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `ReturnGradingUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}/photo`
**Summary:** Upload Damage Photo
**Description:** Upload a damage photo for a return grading.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `grading_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `multipart/form-data`
- Schema: `Body_upload_damage_photo_api_v1_warehouses__warehouse_id__operations_returns__grading_id__photo_post`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/returns/{grading_id}/complete`
**Summary:** Complete Return Grading
**Description:** Mark a return grading as completed.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `grading_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/operations/zones/{zone_id}/metrics`
**Summary:** Get Zone Metrics
**Description:** Get metrics for a specific zone.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `zone_id` (path) [Required] - *string* - N/A
- `date_from` (query) [Optional] - *string* - N/A
- `date_to` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/operations/zones/metrics`
**Summary:** Record Zone Metrics
**Description:** Record metrics for a zone (upsert for today).

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `ZoneMetricsCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/operations/performance`
**Summary:** Get Performance
**Description:** Get performance metrics for a warehouse.

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `time_range` (query) [Optional] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

## Warehouses

### GET `/api/v1/warehouses`
**Summary:** List Warehouses

**Authentication Required:** Yes

**Parameters:**
- `page` (query) [Optional] - *integer* - N/A
- `page_size` (query) [Optional] - *integer* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses`
**Summary:** Create Warehouse

**Authentication Required:** Yes

**Request Body:**
- Content-Type: `application/json`
- Schema: `WarehouseCreate`

**Responses:**
- **201**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}`
**Summary:** Get Warehouse

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/warehouses/{warehouse_id}`
**Summary:** Update Warehouse

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `WarehouseUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### DELETE `/api/v1/warehouses/{warehouse_id}`
**Summary:** Delete Warehouse

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### PUT `/api/v1/warehouses/{warehouse_id}/floor-plan`
**Summary:** Update Floor Plan

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Request Body:**
- Content-Type: `application/json`
- Schema: `FloorPlanUpdate`

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/kpis`
**Summary:** Warehouse Kpis

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### GET `/api/v1/warehouses/{warehouse_id}/dashboard`
**Summary:** Warehouse Dashboard

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/orders/{order_id}/complete`
**Summary:** Mark Order Complete

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/orders/{order_id}/reassign`
**Summary:** Reassign Order To Labor

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A
- `order_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---

### POST `/api/v1/warehouses/{warehouse_id}/restock`
**Summary:** Process Restock

**Authentication Required:** Yes

**Parameters:**
- `warehouse_id` (path) [Required] - *string* - N/A

**Responses:**
- **200**: Successful Response
- **422**: Validation Error

---
