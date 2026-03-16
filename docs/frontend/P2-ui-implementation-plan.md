# Phase 2 UI Implementation Plan
### Frontend Execution + Hard Pre-Push Checklist
**Project:** Logistics & Personal Move Management System  
**Date:** 16 March 2026  
**Owner:** Frontend Teammate  
**Reviewer:** Backend Owner (You)

---

## Objective

Complete UI integration for all Phase 2 backend modules before Phase 3 starts.

Scope to implement in UI:
- User Management
- Warehouse Management
- Order Management
- Inventory Management
- Labour Management

---

## Ground Rules

- UI must consume only published backend contracts.
- Do not assume backend field names; use OpenAPI and sample payloads.
- Any backend mismatch must be logged as a blocker ticket.
- No phase handover unless hard checklist is fully green.

---

## Team Workflow

1. Pull latest stable branch from main.
2. Import API spec and generate or update API client.
3. Implement module UI in this order:
   - Users
   - Warehouses
   - Orders
   - Inventory
   - Labour
4. Run module-level QA and checklist.
5. Raise integration issues immediately.
6. Only merge when all checks pass.

---

## Module Plan

## 1) Users UI

### Screens
- User list with pagination and filters
- Create user form
- Edit user form
- Assign role modal
- Assign warehouse modal

### Must-have flows
- Create user -> appears in list
- Assign role -> role badge updates without refresh
- Assign warehouse -> warehouse field updates
- Deactivate user -> state updates and actions restricted

### API dependencies
- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{id}`
- `PUT /api/v1/users/{id}`
- `DELETE /api/v1/users/{id}`
- `POST /api/v1/users/{id}/assign-role`
- `POST /api/v1/users/{id}/assign-warehouse`

---

## 2) Warehouses UI

### Screens
- Warehouse list
- Warehouse create/edit form
- Floor plan JSON upload/update panel
- KPI dashboard card set per warehouse

### Must-have flows
- Create warehouse -> visible in selectors in other modules
- Update floor plan JSON -> persisted and retrievable
- KPI view loads and handles empty state

### API dependencies
- `GET /api/v1/warehouses`
- `POST /api/v1/warehouses`
- `GET /api/v1/warehouses/{id}`
- `PUT /api/v1/warehouses/{id}`
- `DELETE /api/v1/warehouses/{id}`
- `PUT /api/v1/warehouses/{id}/floor-plan`
- `GET /api/v1/warehouses/{id}/kpis`

---

## 3) Orders UI

### Screens
- Order list with status filter
- Order create form
- Order detail with items section
- Confirm / assign / cancel action bar
- Public order tracking page

### Must-have flows
- Create order in `DRAFT`
- Add/update items
- Confirm order -> status update
- Assign order -> driver/vehicle assignment visible
- Cancel order -> reason shown
- Public tracking works without login

### API dependencies
- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{id}`
- `PUT /api/v1/orders/{id}`
- `POST /api/v1/orders/{id}/confirm`
- `POST /api/v1/orders/{id}/assign`
- `POST /api/v1/orders/{id}/cancel`
- `GET /api/v1/orders/track/{tracking_code}`
- `GET /api/v1/orders/{id}/items`
- `POST /api/v1/orders/{id}/items`

---

## 4) Inventory UI

### Screens
- SKU list with warehouse scope
- SKU create/edit forms
- Stock movement form + history table
- Low-stock panel
- Pick-list generator by order

### Must-have flows
- Create SKU and validate uniqueness handling
- Inbound and outbound movement updates quantity
- Low-stock highlights threshold breaches
- Pick-list returns required vs available quantities

### API dependencies
- `GET /api/v1/inventory`
- `POST /api/v1/inventory`
- `GET /api/v1/inventory/{id}`
- `PUT /api/v1/inventory/{id}`
- `DELETE /api/v1/inventory/{id}`
- `POST /api/v1/inventory/movements`
- `GET /api/v1/inventory/movements`
- `GET /api/v1/inventory/low-stock`
- `POST /api/v1/inventory/pick-list/{order_id}`

---

## 5) Labour UI

### Screens
- Labourer list
- Labourer create/edit forms
- Assign labourer to order action
- Check-in / check-out controls
- Availability list

### Must-have flows
- Create labourer profile
- Assign to order and prevent double assignment
- Check-in then check-out sequence enforced
- Availability excludes assigned labourers

### API dependencies
- `GET /api/v1/labourers`
- `POST /api/v1/labourers`
- `GET /api/v1/labourers/{id}`
- `PUT /api/v1/labourers/{id}`
- `POST /api/v1/labourers/{id}/assign/{order_id}`
- `POST /api/v1/labourers/{id}/check-in`
- `POST /api/v1/labourers/{id}/check-out`
- `GET /api/v1/labourers/availability`

---

## Hard Pre-Push UI Checklist

All items below are mandatory before merge.

## A) Contract and Data Integrity
- [ ] All endpoints mapped through a single API client layer.
- [ ] No hardcoded mock fields in production code paths.
- [ ] Pagination and filters send correct query params.
- [ ] Enum values are consumed exactly as backend returns.
- [ ] Date/time values rendered in a consistent timezone format.

## B) Authorization and Role Safety
- [ ] Role-restricted actions are hidden or disabled in UI.
- [ ] Unauthorized API responses (`401`, `403`) show safe UX states.
- [ ] Session expiry redirects user correctly to login.

## C) Validation and Error Handling
- [ ] Form validation mirrors backend constraints where feasible.
- [ ] `422` validation errors show field-level messages.
- [ ] `409` conflict errors show actionable user guidance.
- [ ] Network failure and timeout states have retry paths.

## D) Functional Journeys (Smoke)
- [ ] Full Users journey passes end-to-end.
- [ ] Full Warehouses journey passes end-to-end.
- [ ] Full Orders journey passes end-to-end.
- [ ] Full Inventory journey passes end-to-end.
- [ ] Full Labour journey passes end-to-end.

## E) UI/UX Quality Gate
- [ ] No broken layouts at 1440px, 1024px, 768px, 390px.
- [ ] Tables handle empty, loading, and large-data states.
- [ ] Destructive actions require confirmation dialog.
- [ ] Success/error toasts are consistent and non-duplicative.
- [ ] Keyboard navigation works for critical forms and modals.

## F) Quality and Release
- [ ] Lint and tests pass in frontend CI.
- [ ] Build passes without warnings that affect behavior.
- [ ] No console errors in core Phase 2 flows.
- [ ] PR includes screenshots or video for each module flow.
- [ ] PR description includes API contract version used.

---

## Sign-Off Template (Use in PR)

- Backend contract version: `<commit/tag>`
- Modules completed: `<users/warehouses/orders/inventory/labour>`
- Smoke tests executed: `<list>`
- Known limitations: `<list or none>`
- Blocking issues: `<list or none>`
- QA result: `PASS / FAIL`

---
