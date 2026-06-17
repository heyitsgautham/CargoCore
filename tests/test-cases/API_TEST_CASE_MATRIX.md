# API Test Case Matrix

Suite root: tests/
Scope: Repository-level tests only. backend/* is read-only.

| Case ID | Category | Endpoint / Component | Scenario | Expected Result | Test Function |
|---|---|---|---|---|---|
| AUTH-INT-001 | Integration | POST /api/v1/auth/register | Valid self-registration payload | 201 with registration payload | test_auth_register_success |
| AUTH-INT-002 | Integration | POST /api/v1/auth/register | Invalid role payload | 422 validation error | test_auth_register_invalid_role_returns_422 |
| AUTH-INT-003 | Integration | POST /api/v1/auth/login | Valid login payload | 200 with access + refresh token | test_auth_login_success |
| AUTH-INT-004 | Integration | POST /api/v1/auth/token | OAuth2 form login | 200 with bearer token fields | test_auth_token_login_success |
| AUTH-INT-005 | Integration | POST /api/v1/auth/logout | Missing auth header | 401 missing/invalid authorization | test_auth_logout_missing_header_returns_401 |
| AUTH-INT-006 | Integration | GET /api/v1/auth/me | Unauthenticated access | 401 not authenticated | test_auth_me_requires_authentication |
| AUTH-INT-007 | Integration | GET /api/v1/auth/me | Authenticated profile fetch | 200 with profile fields | test_auth_me_success |
| AUTH-INT-008 | Integration | POST /api/v1/auth/change-password | Valid password change request | 200 success message | test_auth_change_password_success |
| AUTH-INT-009 | Integration | POST /api/v1/auth/send-otp | Valid OTP send payload | 200 OTP send response | test_auth_send_otp_success |
| AUTH-INT-010 | Integration | POST /api/v1/auth/verify-otp | Valid OTP verify payload | 200 verified true | test_auth_verify_otp_success |
| ORD-INT-001 | Integration | POST /api/v1/orders | Minimal valid create payload | 201 with order response | test_orders_create_success |
| ORD-INT-002 | Integration | GET /api/v1/orders | List orders page 1 | 200 paginated order list | test_orders_list_success |
| ORD-INT-003 | Integration | GET /api/v1/orders/{order_id} | Fetch single order | 200 with matching id | test_orders_get_success |
| ORD-INT-004 | Integration | PUT /api/v1/orders/{order_id} | Update pickup address | 200 with updated field | test_orders_update_success |
| ORD-INT-005 | Integration | POST /api/v1/orders | Invalid create payload | 422 validation error | test_orders_create_validation_error_422 |
| ORD-INT-006 | Integration | GET /api/v1/orders | Unauthenticated list request | 401 not authenticated | test_orders_requires_authentication |
| ORD-INT-007 | Integration | GET /api/v1/orders/{order_id}/items | Get order items | 200 list of items | test_orders_get_items_success |
| ORD-INT-008 | Integration | POST /api/v1/orders/{order_id}/items | Upsert order items | 200 list of upserted items | test_orders_upsert_items_success |
| ORD-INT-009 | Integration | POST /api/v1/orders/{order_id}/delivery-otp/send | Driver sends delivery OTP | 200 otp send payload | test_orders_send_delivery_otp_success_for_driver |
| ORD-INT-010 | Integration | GET /api/v1/orders/track/{tracking_code} | Unknown tracking code behavior | 404 with tracking not-found detail | test_orders_track_unknown_returns_404 |
| ORD-INT-011 | Integration | POST /api/v1/orders/{order_id}/customer-rating | Submit valid customer rating | 200 with customer_rating reflected in response | test_orders_customer_rating_success |
| ORD-INT-012 | Integration | POST /api/v1/orders/{order_id}/customer-rating | Submit invalid rating (>5) | 422 validation error | test_orders_customer_rating_validation_error_422 |
| ORD-INT-013 | Integration | POST /api/v1/orders/{order_id}/customer-rating | Submit customer rating without authentication | 401 not authenticated | test_orders_customer_rating_requires_authentication |
| TRK-INT-001 | Integration | GET /api/v1/tracking/drivers | Unauthenticated tracking request | 401 not authenticated | test_tracking_requires_authentication |
| TRK-INT-002 | Integration | GET /api/v1/tracking/drivers | Authenticated active drivers request | 200 with driver location list | test_tracking_active_drivers_success |
| TRK-INT-003 | Integration | GET /api/v1/tracking/orders/{order_id}/driver | Authenticated order-driver lookup | 200 with driver location object | test_tracking_order_driver_success |
| TRK-INT-004 | Integration | GET /api/v1/tracking/orders/{order_id}/driver | Unassigned/unknown order-driver lookup | 200 with null body | test_tracking_order_driver_returns_null_when_unassigned |
| AUTH-CON-001 | Contract | OpenAPI auth paths | Validate auth endpoint declarations | Required paths and methods exist | test_openapi_auth_paths_and_methods_exist |
| AUTH-CON-002 | Contract | POST /api/v1/auth/register | Validate response field contract | Required keys and types present | test_register_response_contract |
| AUTH-CON-003 | Contract | POST /api/v1/auth/login | Validate login response contract | Required keys and nested user fields | test_login_response_contract |
| AUTH-CON-004 | Contract | POST /api/v1/auth/register | Validate 422 payload contract | detail list exists | test_register_validation_error_contract |
| ORD-CON-001 | Contract | OpenAPI order paths | Validate orders endpoint declarations | Required paths and methods exist | test_openapi_orders_paths_exist |
| ORD-CON-002 | Contract | POST /api/v1/orders | Validate order create contract | Required response keys present | test_order_create_contract |
| ORD-CON-003 | Contract | GET /api/v1/orders | Validate list response contract | Pagination + items contract | test_order_list_contract |
| ORD-CON-004 | Contract | GET /api/v1/orders/{order_id}/items | Validate order-items contract | Item field contract | test_order_items_contract |
| PUB-CON-001 | Contract | OpenAPI global paths | Validate health and tracking declarations | Core paths and version present | test_openapi_global_paths_and_version |
| PUB-CON-002 | Contract | GET /health | Validate runtime health contract | 200 with {status: ok} | test_health_endpoint_contract |
| PUB-CON-003 | Contract | GET /api/v1/tracking/drivers | Validate tracking schema declaration + unauth runtime behavior | OpenAPI schema ref exists + runtime 401 | test_tracking_schema_contract_defined |
| DOC-CON-001 | Contract | OpenAPI metadata extensions | Validate user story and API mapping blocks exist | x-user-stories and x-api-mapping are present and non-empty | test_openapi_has_user_story_mapping_blocks |
| DOC-CON-002 | Contract | OpenAPI operation documentation | Validate all operations include descriptions | No operations missing description | test_all_operations_have_descriptions |
| DOC-CON-003 | Contract | OpenAPI secured error responses | Validate secured operations document 401 responses | No secured operation missing 401 response docs | test_secured_operations_document_401_response |
| UNIT-BLD-001 | Unit | sample_data.make_fake_user | Default fake user generation | LOGISTIC_MANAGER role and stable fields | test_make_fake_user_defaults |
| UNIT-BLD-002 | Unit | sample_data.make_user_profile_dict | Profile payload shape | Required profile keys exist | test_make_user_profile_dict_shape |
| UNIT-BLD-003 | Unit | sample_data.make_registration_response | Pending approval registration variant | pending_approval true and null tokens | test_make_registration_response_pending_approval |
| UNIT-BLD-004 | Unit | sample_data.make_login_response | Login payload generator | token fields and user object | test_make_login_response_has_tokens_and_user |
| UNIT-BLD-005 | Unit | sample_data.make_order_response | Order response generator | Order contract keys present | test_make_order_response_contract_keys |
| UNIT-BLD-006 | Unit | sample_data.make_order_list_response | Order list generator | Pagination and item list shape | test_make_order_list_response_contract_keys |
| UNIT-SCH-001 | Unit | ai.ChatRequest | Validate non-empty chat message constraint | Empty message rejected | test_chat_request_rejects_empty_message |
| UNIT-SCH-002 | Unit | ai.EscalateRequest | Validate non-empty escalation reason | Empty reason rejected | test_escalate_request_rejects_empty_reason |
| UNIT-SCH-003 | Unit | auth.UserRegister | Validate minimum password length | Short password rejected | test_user_register_rejects_short_password |
| UNIT-SCH-004 | Unit | auth.UserLogin | Validate email field min length | Too-short email string rejected | test_user_login_rejects_short_email_field |
| UNIT-SCH-005 | Unit | auth.ChangePasswordRequest | Validate minimum new password length | Short new password rejected | test_change_password_rejects_short_new_password |
| UNIT-SCH-006 | Unit | auth.VerifyOTPRequest | Validate 6-digit OTP contract | OTP length mismatch rejected | test_verify_otp_rejects_short_otp |
| UNIT-SCH-007 | Unit | inventory.InventoryCreate | Validate non-negative quantity_on_hand | Negative quantity rejected | test_inventory_create_rejects_negative_quantity |
| UNIT-SCH-008 | Unit | inventory.InventoryMovementCreate | Validate quantity > 0 | Zero quantity rejected | test_inventory_movement_create_rejects_zero_quantity |
| UNIT-SCH-009 | Unit | inventory.RestockRequestStatusUpdate | Validate status regex contract | Non APPROVED/REJECTED status rejected | test_restock_status_update_rejects_invalid_status |
| UNIT-SCH-010 | Unit | logistics.LogisticsAiQueryRequest | Validate query minimum length | One-character query rejected | test_logistics_ai_query_rejects_one_character_query |
| UNIT-SCH-011 | Unit | logistics.LogisticsVehicleCreate | Validate bounded year field | Out-of-range year rejected | test_logistics_vehicle_create_rejects_out_of_range_year |
| UNIT-SCH-012 | Unit | logistics.LogisticsDriverCreate | Validate minimum name length | Single-character name rejected | test_logistics_driver_create_rejects_short_name |
| UNIT-SCH-013 | Unit | orders.OrderCreate | Validate pickup address minimum length | Short pickup address rejected | test_order_create_rejects_short_pickup_address |
| UNIT-SCH-014 | Unit | orders.CancelOrderRequest | Validate cancellation reason minimum length | Short reason rejected | test_cancel_order_request_rejects_short_reason |
| UNIT-SCH-015 | Unit | orders.OrderItemUpsert | Validate quantity > 0 | Non-positive quantity rejected | test_order_item_upsert_rejects_non_positive_quantity |
| UNIT-SCH-016 | Unit | users.UserAdminCreate | Validate admin password minimum length | Short password rejected | test_user_admin_create_rejects_short_password |
| UNIT-SCH-017 | Unit | users.AssignRoleRequest | Validate role max length | Role longer than 50 chars rejected | test_assign_role_request_rejects_too_long_role |
| UNIT-SCH-018 | Unit | wallet.WalletPaymentRequest | Validate amount greater-than-zero | Zero amount rejected | test_wallet_payment_request_rejects_zero_amount |
| UNIT-SCH-019 | Unit | warehouse.WarehouseCreate | Validate minimum address length | Short address rejected | test_warehouse_create_rejects_short_address |
| UNIT-SCH-020 | Unit | warehouse_operations.ConfirmPickItemRequest | Validate quantity_picked > 0 | Zero quantity rejected | test_confirm_pick_item_request_rejects_zero_quantity |
| UNIT-SCH-021 | Unit | warehouse_operations.AssignTruckRequest | Validate non-empty carrier | Empty carrier rejected | test_assign_truck_request_rejects_empty_carrier |
| UNIT-SCH-022 | Unit | warehouse_operations.ZoneMetricsCreate | Validate accuracy upper bound <=100 | Accuracy above 100 rejected | test_zone_metrics_create_rejects_accuracy_above_100 |
| UNIT-SCH-023 | Unit | orders.CustomerRatingRequest | Validate rating range between 1 and 5 | Rating above 5 is rejected | test_customer_rating_request_rejects_out_of_range_rating |
