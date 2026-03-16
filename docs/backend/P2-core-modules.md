# Phase 2 - Core Domain Modules
### Implementation Plan
**Project:** Logistics & Personal Move Management System  
**Stack:** FastAPI · PostgreSQL · SQLAlchemy (async) · Alembic · Pydantic v2  
**Created:** 16 March 2026  
**Estimated Effort:** 3-4 weeks  
**Priority:** High

---

## Table of Contents
1. [Goal](#goal)
2. [Scope](#scope)
3. [Dependencies from Phase 1](#dependencies-from-phase-1)
4. [Implementation Order](#implementation-order)
5. [Milestone 2.1 - User Management](#milestone-21---user-management)
6. [Milestone 2.2 - Warehouse Management](#milestone-22---warehouse-management)
7. [Milestone 2.3 - Order Management](#milestone-23---order-management)
8. [Milestone 2.4 - Inventory Management](#milestone-24---inventory-management)
9. [Milestone 2.5 - Labour Management](#milestone-25---labour-management)
10. [Cross-Cutting Engineering Tasks](#cross-cutting-engineering-tasks)
11. [Testing Strategy](#testing-strategy)
12. [Frontend Integration Contract](#frontend-integration-contract)
13. [Teammate Hand-Off Checklist](#teammate-hand-off-checklist)
14. [Parallel Work Plan (You on Phase 3, Team on Frontend)](#parallel-work-plan-you-on-phase-3-team-on-frontend)
15. [Known Conflict Areas and Mitigations](#known-conflict-areas-and-mitigations)
16. [Definition of Done](#definition-of-done)

---

## Goal

Deliver production-ready backend APIs for:
- User administration and role assignment
- Warehouse and floor-plan management
- End-to-end order lifecycle and tracking
- Inventory with stock movement auditability
- Labour roster and assignment operations

At the end of Phase 2, frontend teams must be able to build manager dashboards and workflows using stable API contracts.

---

## Scope

### In Scope
- SQLAlchemy models and Alembic migrations for Phase 2 entities
- Pydantic schemas for all request/response contracts
- Routers and service-layer business logic for milestones 2.1 to 2.5
- RBAC enforcement and warehouse scoping
- Pagination, filtering, search, and soft-delete behavior
- Integration and unit tests for all high-risk business flows

### Out of Scope
- Fleet, route optimization, geofencing, and dispatcher workflows (Phase 3)
- Driver mobile execution flows (Phase 4)
- AI extensions beyond current Phase 5.1 work

---

## Dependencies from Phase 1

Before Phase 2 starts, verify:
- Auth and `get_current_user` dependency are stable
- `require_role()` authorization checks are reusable
- Database session lifecycle and migration flow are stable
- Redis is optional for Phase 2 (only needed if caching is introduced)

---

## Implementation Order

Recommended delivery sequence (to reduce rework):
1. **Data model and migration baseline** for warehouses, orders, inventory, labour
2. **2.1 User Management** (enables role-based administration)
3. **2.2 Warehouse Management** (used by users, inventory, and labour)
4. **2.3 Order Management** (core lifecycle)
5. **2.4 Inventory Management** (ties into order fulfillment)
6. **2.5 Labour Management** (ties into order execution)
7. **Cross-cutting hardening** (audit logs, filters, docs, test coverage)

---

## Milestone 2.1 - User Management

### Deliverables
- Admin CRUD for users (soft delete)
- Assign/revoke role and warehouse
- Account activation/deactivation
- Paginated/filterable listing

### Backend Tasks
- Add/expand `User` fields as needed: `warehouse_id`, `is_active`, timestamps
- Add service functions for:
  - create user (manager-only)
  - update user profile/admin fields
  - deactivate/reactivate user
  - assign role
  - assign warehouse
- Add list endpoint with filters: role, warehouse, active status, search by name/email

### API Contract
- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{id}`
- `PUT /api/v1/users/{id}`
- `DELETE /api/v1/users/{id}`
- `POST /api/v1/users/{id}/assign-role`
- `POST /api/v1/users/{id}/assign-warehouse`

### Acceptance Criteria
- Only authorized roles can create/modify users
- Inactive users cannot authenticate for protected routes
- Pagination metadata is returned consistently

---

## Milestone 2.2 - Warehouse Management

### Deliverables
- Warehouse CRUD APIs
- Floor plan JSON upload/update
- Warehouse KPI endpoint

### Backend Tasks
- Create `warehouses` model/table with geo and capacity fields
- Add optional `floor_plan_json` validation schema
- Implement KPI aggregation service:
  - capacity utilization
  - user count by role
  - inventory counts and low-stock totals

### API Contract
- `GET /api/v1/warehouses`
- `POST /api/v1/warehouses`
- `GET /api/v1/warehouses/{id}`
- `PUT /api/v1/warehouses/{id}`
- `DELETE /api/v1/warehouses/{id}`
- `PUT /api/v1/warehouses/{id}/floor-plan`
- `GET /api/v1/warehouses/{id}/kpis`

### Acceptance Criteria
- Floor plan payload is validated before save
- Warehouse deletion is blocked if dependent active records exist
- KPI endpoint responds under agreed SLA with realistic data volumes

---

## Milestone 2.3 - Order Management

### Deliverables
- Individual/Vendor order creation
- Full status lifecycle with guards
- Driver/vehicle assignment hooks (simple now, optimized in Phase 3)
- Public tracking endpoint
- Order items sub-resource

### Backend Tasks
- Create `orders` and `order_items` tables
- Enforce state machine:
  - `DRAFT -> CONFIRMED -> ASSIGNED -> IN_TRANSIT -> DELIVERED -> CLOSED`
  - cancellation rules by state
- Generate unique tracking code
- Build role-scoped listing and details
- Add service methods for confirm, assign, cancel

### API Contract
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

### Acceptance Criteria
- Invalid state transitions are rejected with clear errors
- Public tracking endpoint hides sensitive data
- Assignment actions are auditable

---

## Milestone 2.4 - Inventory Management

### Deliverables
- SKU CRUD and location mapping
- Inventory movement ledger (inbound/outbound/adjustment)
- Low-stock endpoint
- Picking list generation by order

### Backend Tasks
- Create `inventory_items` and `inventory_movements` tables
- Add strict movement validation (no negative stock from outbound)
- Add safety stock checks and low-stock query
- Generate picking list from order item requirements vs stock

### API Contract
- `GET /api/v1/inventory`
- `POST /api/v1/inventory`
- `GET /api/v1/inventory/{id}`
- `PUT /api/v1/inventory/{id}`
- `DELETE /api/v1/inventory/{id}`
- `POST /api/v1/inventory/movements`
- `GET /api/v1/inventory/movements`
- `GET /api/v1/inventory/low-stock`
- `POST /api/v1/inventory/pick-list/{order_id}`

### Acceptance Criteria
- Movement history is immutable and traceable
- Stock levels remain consistent under concurrent updates
- Picking list reflects real-time inventory state

---

## Milestone 2.5 - Labour Management

### Deliverables
- Labourer registry and profile management
- Labour assignment to orders
- Check-in/check-out attendance
- Availability endpoint for daily operations

### Backend Tasks
- Create `labourers` table and order-labour link if many-to-many is required
- Add attendance event model/table (`check_in`, `check_out` with timestamps)
- Add availability calculation (not assigned, active, within shift window)

### API Contract
- `GET /api/v1/labourers`
- `POST /api/v1/labourers`
- `GET /api/v1/labourers/{id}`
- `PUT /api/v1/labourers/{id}`
- `POST /api/v1/labourers/{id}/assign/{order_id}`
- `POST /api/v1/labourers/{id}/check-in`
- `POST /api/v1/labourers/{id}/check-out`
- `GET /api/v1/labourers/availability`

### Acceptance Criteria
- Double assignment conflicts are prevented
- Attendance records are ordered and non-duplicated for same shift
- Availability reflects assignment and attendance state

---

## Cross-Cutting Engineering Tasks

- Introduce domain-specific enums for statuses and movement types
- Add shared pagination response schema
- Add filter/query parameter validation
- Add DB indexes for high-traffic lookups (status, warehouse_id, created_at, tracking_code)
- Add structured audit logs for critical writes (assignments, state changes)
- Keep router thin and business logic in service layer
- Update OpenAPI examples and error schema consistency

---

## Testing Strategy

### Unit Tests
- Order state transition rules
- Inventory movement invariants
- Role and permission guard logic
- KPI aggregation calculations

### Integration Tests
- End-to-end order lifecycle
- User role assignment and scoping
- Pick-list generation from order items + stock
- Labour assignment and attendance workflow
- Public tracking endpoint contract and redaction checks

### Suggested Test Matrix
- Success path tests for every endpoint
- Validation failures (400/422)
- Authorization failures (401/403)
- Not found scenarios (404)
- Conflict scenarios (409) for state and assignment collisions

---

## Frontend Integration Contract

To allow parallel frontend work, provide these artifacts at each milestone completion:
- Updated OpenAPI spec from `/docs` or exported JSON
- Example request/response payloads for each endpoint
- Known error codes and messages (422/403/409 formats)
- Seed data script for frontend sandbox use
- Changelog entry for any contract change

Minimum contract stability rule:
- After a milestone is marked done, avoid breaking response shapes.
- If change is unavoidable, version it (or feature-flag it) and announce in changelog.

---

## Teammate Hand-Off Checklist

Use this checklist each time a Phase 2 milestone is handed to frontend.

### 1) Backend Owner Preparation (before hand-off)
- Confirm endpoint behavior in Swagger at `/docs` with real example calls.
- Export or snapshot OpenAPI JSON and share in team channel.
- Provide 3 payload examples per endpoint:
  - happy path request/response
  - validation failure (`422`)
  - authorization/permission failure (`403` or `401`)
- Share seed data IDs required by frontend (user IDs, warehouse IDs, order IDs).
- Document enum values used by UI logic (`status`, `movement_type`, `role`).

### 2) Frontend Teammate Setup
- Pull latest backend branch and backend docs for the milestone.
- Confirm local env points to correct API base URL.
- Import API collection or typed client from OpenAPI.
- Build UI against response contracts first, then edge/error states.
- Add UI handling for server errors with user-safe messages.

### 3) Contract Verification Steps
- Validate required fields render correctly in the UI table/forms.
- Validate pagination (`page`, `page_size`, `total`) in list pages.
- Validate filter query params map correctly to backend.
- Validate state transition actions only show when allowed.
- Validate role-restricted actions are hidden/disabled for unauthorized users.

### 4) Integration Smoke Tests
- Users: create user -> assign role -> assign warehouse -> deactivate -> list filters.
- Warehouse: create -> update floor plan -> fetch KPIs.
- Orders: create -> add items -> confirm -> assign -> track.
- Inventory: create SKU -> inbound movement -> outbound movement -> low-stock list -> pick-list.
- Labour: create labourer -> check-in -> assign order -> check-out -> availability list.

### 5) Handoff Completion Criteria
- Frontend confirms all target flows are integrated without blockers.
- Backend confirms no contract changes are pending for that milestone.
- Any mismatch is logged as a ticket with: endpoint, expected shape, actual shape.
- Milestone marked "integration done" in sprint board.

### 6) Communication Template (copy/paste)
- Milestone: `2.x`
- Endpoints ready: `<list>`
- OpenAPI version/tag: `<commit-sha or tag>`
- Seed data: `<ids/sample records>`
- Known constraints: `<short bullets>`
- Breaking changes since last hand-off: `none` or `<details>`

---

## Parallel Work Plan (You on Phase 3, Team on Frontend)

**Yes, this is workable** if you lock API contracts before moving forward.

### Recommended Team Split
- **You:** Start Phase 3 backend modules on separate feature branches
- **Frontend teammate(s):** Integrate UI flows for completed Phase 2 endpoints
- **One owner (can be rotating):** API contract guardian, release notes, mock data quality

### Working Model
1. Finish one Phase 2 milestone completely (code + tests + docs).
2. Publish contract pack (OpenAPI + examples + seed data).
3. Frontend starts integration immediately for that milestone.
4. You continue with next backend module (Phase 3), avoiding edits to already stabilized Phase 2 response shapes.

---

## Known Conflict Areas and Mitigations

### Likely Conflicts
- Endpoint path/verb changes after frontend starts integration
- Response schema drift (field rename, nested structure changes)
- Enum/status value changes without frontend update
- Auth/RBAC policy changes affecting visible UI actions
- Shared files merge conflicts (`main.py`, router imports, schema index files)

### Mitigations
- Freeze endpoint contracts milestone-by-milestone
- Add contract tests (schema snapshots or typed client checks)
- Use feature branches per domain (`phase2-orders`, `phase3-fleet`, frontend feature branches)
- Keep one weekly API sync for backend + frontend owners
- Add deprecation windows for renamed fields (serve both old/new briefly)
- Prefer additive changes over breaking changes

### Practical Merge Strategy
- Backend Phase 2 fixes: small PRs focused on one module
- Phase 3 work: isolated routers/services and independent migrations
- Frontend: pin to tagged backend contract versions

---

## Definition of Done

Phase 2 is complete when:
- All milestone endpoints are implemented and integrated in router
- Alembic migrations are applied cleanly on fresh DB
- Test suite for Phase 2 passes in CI
- OpenAPI docs include all Phase 2 contracts with examples
- Frontend has no blocker issues for manager workflows
- No critical defects in role checks, order transitions, or stock accounting

---

## Suggested Week-by-Week Timeline

- **Week 1:** Data model baseline + Milestones 2.1 and 2.2
- **Week 2:** Milestone 2.3 (orders + item lifecycle)
- **Week 3:** Milestones 2.4 and 2.5
- **Week 4 (buffer):** Hardening, performance tuning, bug fixes, contract freeze
