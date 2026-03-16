ywa# Backend Development Roadmap
### Logistics & Personal Move Management System
**Stack:** FastAPI · PostgreSQL · SQLAlchemy · Alembic · Redis · Celery  
**Last Updated:** 16 March 2026

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Tech Stack & Tooling](#2-tech-stack--tooling)
3. [Project Structure](#3-project-structure)
4. [Database Schema Design](#4-database-schema-design)
5. [Phase 1 — Foundation](#phase-1--foundation-project-setup--core-auth)
6. [Phase 2 — Core Domain Modules](#phase-2--core-domain-modules)
7. [Phase 3 — Operational Modules](#phase-3--operational-modules)
8. [Phase 4 — Driver Mobile APIs](#phase-4--driver-mobile-apis)
9. [Phase 5 — AI & Intelligence Layer](#phase-5--ai--intelligence-layer)
10. [Phase 6 — Finance, Payroll & Reporting](#phase-6--finance-payroll--reporting)
11. [Phase 7 — Real-Time, Notifications & WebSockets](#phase-7--real-time-notifications--websockets)
12. [Phase 8 — Hardening, Testing & Deployment](#phase-8--hardening-testing--deployment)
13. [API Versioning Strategy](#api-versioning-strategy)
14. [Environment & Configuration](#environment--configuration)

---

## 1. Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                         Clients                                │
│   Vue Web App (LWD / IV / AI)   │   Driver Mobile (PWA)        │
└──────────────────┬─────────────────────────┬───────────────────┘
                   │  HTTPS / WebSocket       │
        ┌──────────▼─────────────────────────▼──────────┐
        │               FastAPI (v1)                    │
        │  Auth · Orders · Inventory · Fleet · Routes   │
        │  Drivers · Finance · AI · Reports · Notifs    │
        └──────┬─────────────┬──────────────┬───────────┘
               │             │              │
        ┌──────▼───┐   ┌─────▼───┐   ┌──────▼──────┐
        │PostgreSQL│   │  Redis  │   │Celery Worker│
        │  (main)  │   │ (cache/ │   │(background  │
        │          │   │ queue)  │   │ tasks)      │
        └──────────┘   └─────────┘   └─────────────┘
               │
        ┌──────▼──────────────────┐
        │  External Services      │
        │  Google Maps·Gemini AI  │
        │  OCR API · SMS/Email    │
        └─────────────────────────┘
```

---

## 2. Tech Stack & Tooling

| Layer | Choice | Purpose |
|---|---|---|
| **Framework** | FastAPI 0.111+ | Async REST API, OpenAPI docs out-of-box |
| **Database** | PostgreSQL 16 | Primary relational store |
| **ORM** | SQLAlchemy 2.0 (async) | DB models and queries |
| **Migrations** | Alembic | Schema versioning |
| **Validation** | Pydantic v2 | Request/response schemas |
| **Auth** | JWT (python-jose) + bcrypt | Token-based auth, password hashing |
| **Cache / Queue Broker** | Redis | Session cache, Celery broker |
| **Task Queue** | Celery | Background jobs: payroll, notifications, AI calls |
| **Real-Time** | FastAPI WebSockets | Live GPS, driver status, chat |
| **File Storage** | Local/S3-compatible | PoD photos, fuel receipts, damage images |
| **AI / LLM** | Google Gemini API | Natural language analytics, volume estimator |
| **Maps** | Google Maps Platform | Geocoding, route optimization, geofencing |
| **Testing** | pytest + httpx | Unit and integration tests |
| **Containerization** | Docker + Docker Compose | Dev and production parity |
| **Linting** | ruff + black | Code quality |

---

## 3. Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory
│   ├── config.py                # Settings (pydantic-settings)
│   ├── database.py              # Async engine, session factory
│   ├── dependencies.py          # Shared FastAPI Depends()
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── ai_conversation.py
│   │   ├── escalation.py
│   │   ├── order.py
│   │   ├── inventory.py
│   │   ├── fleet.py
│   │   ├── route.py
│   │   ├── finance.py
│   │   ├── geofence.py
│   │   └── ...
│   │
│   ├── schemas/                 # Pydantic schemas (request / response)
│   │   └── (mirrors models/)
│   │
│   ├── routers/                 # Route handlers, grouped by domain
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── orders.py
│   │   ├── inventory.py
│   │   ├── fleet.py
│   │   ├── routes.py
│   │   ├── drivers.py
│   │   ├── warehouse.py
│   │   ├── finance.py
│   │   ├── geofencing.py
│   │   ├── ai.py
│   │   ├── notifications.py
│   │   └── reports.py
│   │
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py
│   │   ├── order_service.py
│   │   ├── route_service.py
│   │   ├── payroll_service.py
│   │   ├── ai_service.py
│   │   ├── sql_validator.py
│   │   └── ...
│   │
│   ├── tasks/                   # Celery async tasks
│   │   ├── celery_app.py
│   │   ├── notification_tasks.py
│   │   ├── payroll_tasks.py
│   │   └── ai_tasks.py
│   │
│   ├── utils/                   # Helpers (JWT, file upload, geocoding)
│   │   ├── jwt.py
│   │   ├── hashing.py
│   │   ├── redis.py
│   │   ├── file_upload.py
│   │   ├── maps.py
│   │   └── gemini.py
│   │
│   └── middleware/
│       ├── auth_middleware.py
│       └── logging_middleware.py
│
├── alembic/                     # DB migrations
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── conftest.py
│   └── test_*/
│
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 4. Database Schema Design

### Core Tables

| Table | Key Columns | Notes |
|---|---|---|
| `users` | id, name, email, phone, password_hash, role, warehouse_id, is_active | Central identity table for all roles |
| `roles` | id, name (ENUM: LOGISTIC_MANAGER, WAREHOUSE_MANAGER, DISPATCHER, DRIVER, LABOURER, INDIVIDUAL, VENDOR, AI_AGENT) | RBAC roles |
| `warehouses` | id, name, address, lat, lng, manager_id, floor_plan_json | Multi-warehouse support |
| `orders` | id, order_type, status, customer_id, pickup_addr, delivery_addr, scheduled_at, assigned_driver_id, warehouse_id | Core order entity |
| `order_items` | id, order_id, sku_id, quantity, box_count, estimated_volume | Line items per order |
| `vehicles` | id, registration, type, capacity_kg, capacity_cbm, current_driver_id, warehouse_id, status, last_lat, last_lng | Fleet |
| `routes` | id, order_id, driver_id, vehicle_id, planned_polyline, actual_polyline, status, started_at, completed_at | Route execution |
| `route_stops` | id, route_id, stop_type, address, lat, lng, sequence, arrived_at, departed_at, status | Individual stops |
| `inventory_items` | id, warehouse_id, sku, name, category, unit, quantity_on_hand, safety_stock, aisle, shelf, bin | WMS |
| `inventory_movements` | id, item_id, movement_type, quantity, reference_order_id, performed_by, timestamp | Audit trail |
| `labourers` | id, user_id, warehouse_id, skill_tags, assigned_order_id | Labour roster |
| `geofences` | id, name, warehouse_id, polygon_json, trigger_action, is_active | Digital boundaries |
| `geofence_events` | id, geofence_id, vehicle_id, driver_id, event_type (ENTER/EXIT), timestamp | Geofence log |
| `proof_of_delivery` | id, order_id, driver_id, photo_url, signature_url, qr_code, captured_at, notes | PoD |
| `cod_payments` | id, order_id, driver_id, amount, collected_at, status, reconciled_by | COD cash tracking |
| `payroll_records` | id, user_id, period_start, period_end, base_pay, distance_bonus, performance_bonus, total, status | Payroll |
| `fuel_receipts` | id, driver_id, vehicle_id, amount, liters, photo_url, ocr_data_json, submitted_at, approved_by | Fuel expense |
| `damage_reports` | id, order_id, driver_id, photo_urls, description, severity, reported_at, resolved_at | Damage logs |
| `notifications` | id, user_id, type, title, body, is_read, created_at | In-app notifications |
| `audit_logs` | id, user_id, action, entity_type, entity_id, old_value, new_value, timestamp | Full audit trail |
| `ai_conversations` | id, session_id, user_id, role, message, created_at, intent, sql_generated, query_result | AI support chat |
| `escalations` | id, conversation_id, reason, escalated_to_user_id, escalated_at, resolved_at, status | AI escalations |

---

## Phase 1 — Foundation: Project Setup & Core Auth

**Goal:** Running FastAPI server connected to PostgreSQL with full auth system.

### Milestones

- [x] **1.1 — Project Scaffolding**
  - Initialize `backend/` directory with the structure above
  - Set up `pyproject.toml` / `requirements.txt`
  - Configure `docker-compose.yml` with `app`, `db` (postgres), `redis` services
  - Set up `Dockerfile` for the FastAPI app

- [x] **1.2 — Database Connection**
  - Configure async SQLAlchemy engine with `asyncpg` driver
  - Set up `get_db()` dependency for session management
  - Configure Alembic for migration management
  - Create initial migration with `users` and `roles` tables

- [x] **1.3 — Authentication System**
  - User registration with bcrypt password hashing
  - JWT access token (15 min) + refresh token (7 days)
  - Role-based `require_role()` dependency
  - Secure logout via Redis token blacklist

### API Endpoints

```
POST   /api/v1/auth/register          # Create new user account
POST   /api/v1/auth/login             # Issue JWT tokens
POST   /api/v1/auth/refresh           # Refresh access token
POST   /api/v1/auth/logout            # Invalidate token (Redis)
GET    /api/v1/auth/me                # Get current user profile
PUT    /api/v1/auth/me                # Update profile
POST   /api/v1/auth/change-password   # Change password
POST   /api/v1/auth/forgot-password   # Send reset email
POST   /api/v1/auth/reset-password    # Confirm reset with token
```

---

## Phase 2 — Core Domain Modules

**Goal:** Order lifecycle, user management, and warehouse/inventory APIs.

### Milestones

- [x] **2.1 — User Management (Logistic Manager)**
  - CRUD for users across all roles
  - Assign/revoke roles and warehouse affiliations
  - Activate / deactivate accounts
  - Paginated user list with filters

  ```
  GET    /api/v1/users                        # List all users (paginated, filterable by role)
  POST   /api/v1/users                        # Create user (by manager)
  GET    /api/v1/users/{id}                   # Get user detail
  PUT    /api/v1/users/{id}                   # Update user
  DELETE /api/v1/users/{id}                   # Soft delete
  POST   /api/v1/users/{id}/assign-role       # Assign role
  POST   /api/v1/users/{id}/assign-warehouse  # Assign to warehouse
  ```

- [x] **2.2 — Warehouse Management**
  - CRUD for warehouse hubs
  - Upload/store floor plan grid (JSON)
  - Warehouse capacity KPIs

  ```
  GET    /api/v1/warehouses                   # List all warehouses
  POST   /api/v1/warehouses                   # Create warehouse
  GET    /api/v1/warehouses/{id}              # Get detail
  PUT    /api/v1/warehouses/{id}              # Update
  DELETE /api/v1/warehouses/{id}              # Delete
  PUT    /api/v1/warehouses/{id}/floor-plan   # Upload digitized floor plan JSON
  GET    /api/v1/warehouses/{id}/kpis         # Capacity, utilization, staff stats
  ```

- [x] **2.3 — Order Management**
  - Individual and Vendor booking flows
  - Full order status lifecycle: `DRAFT → CONFIRMED → ASSIGNED → IN_TRANSIT → DELIVERED → CLOSED`
  - Order item management
  - Customer-facing order tracking (public endpoint)

  ```
  POST   /api/v1/orders                        # Create order (Individual/Vendor)
  GET    /api/v1/orders                        # List orders (role-filtered)
  GET    /api/v1/orders/{id}                   # Get full order detail
  PUT    /api/v1/orders/{id}                   # Update order details (pre-assignment)
  POST   /api/v1/orders/{id}/confirm           # Manager confirms order
  POST   /api/v1/orders/{id}/assign            # Assign driver + vehicle
  POST   /api/v1/orders/{id}/cancel            # Cancel order
  GET    /api/v1/orders/track/{tracking_code}  # Public tracking (no auth)
  GET    /api/v1/orders/{id}/items             # Get order items
  POST   /api/v1/orders/{id}/items             # Add/update items
  ```

- [x] **2.4 — Inventory Management (Warehouse Manager)**
  - SKU CRUD with location (Aisle/Shelf/Bin)
  - Stock movement recording (inbound/outbound/adjustment)
  - Safety stock alerts
  - Picking list generation for an order

  ```
  GET    /api/v1/inventory                             # List SKUs (warehouse-scoped)
  POST   /api/v1/inventory                             # Add new SKU
  GET    /api/v1/inventory/{id}                        # SKU detail
  PUT    /api/v1/inventory/{id}                        # Update SKU / location
  DELETE /api/v1/inventory/{id}                        # Remove SKU
  POST   /api/v1/inventory/movements                   # Record stock movement
  GET    /api/v1/inventory/movements                   # Movement history (auditable)
  GET    /api/v1/inventory/low-stock                   # Items below safety stock threshold
  POST   /api/v1/inventory/pick-list/{order_id}        # Generate picking list for order
  ```

- [x] **2.5 — Labour Management (Warehouse Manager)**
  - Labourer roster CRUD
  - Assign labourers to orders
  - Attendance and check-in tracking

  ```
  GET    /api/v1/labourers                       # List labourers
  POST   /api/v1/labourers                       # Register labourer
  GET    /api/v1/labourers/{id}                  # Detail
  PUT    /api/v1/labourers/{id}                  # Update
  POST   /api/v1/labourers/{id}/assign/{order_id}# Assign to order
  POST   /api/v1/labourers/{id}/check-in         # Clock in
  POST   /api/v1/labourers/{id}/check-out        # Clock out
  GET    /api/v1/labourers/availability           # Available labourers today
  ```

---

## Phase 3 — Operational Modules

**Goal:** Fleet management, route optimization, geofencing, and dispatcher APIs.

### Milestones

- [ ] **3.1 — Fleet Management (Logistic Manager)**
  - Vehicle CRUD with capacity and type
  - Bind/unbind driver to vehicle
  - Live GPS location update endpoint

  ```
  GET    /api/v1/fleet                            # List all vehicles
  POST   /api/v1/fleet                            # Create vehicle
  GET    /api/v1/fleet/{id}                       # Vehicle detail
  PUT    /api/v1/fleet/{id}                       # Update vehicle
  DELETE /api/v1/fleet/{id}                       # Delete vehicle
  POST   /api/v1/fleet/{id}/bind-driver           # Bind driver to vehicle
  POST   /api/v1/fleet/{id}/unbind-driver         # Unbind driver
  PUT    /api/v1/fleet/{id}/location              # Update GPS position (called by driver app)
  GET    /api/v1/fleet/live-map                   # All vehicles with live position
  ```

- [ ] **3.2 — Route Management (Dispatcher)**
  - Create and assign routes to drivers
  - Auto-batch multiple orders into single route (TSP solver)
  - Query Google Maps Directions API for polylines
  - Real-time route progress updates

  ```
  POST   /api/v1/routes                           # Create route for driver
  GET    /api/v1/routes                           # List routes (dispatcher-scoped)
  GET    /api/v1/routes/{id}                      # Route detail with stops
  PUT    /api/v1/routes/{id}                      # Update route
  POST   /api/v1/routes/optimize                  # AI-powered TSP route optimization
  GET    /api/v1/routes/{id}/stops                # List stops
  PUT    /api/v1/routes/{id}/stops/{stop_id}      # Update stop status
  POST   /api/v1/routes/{id}/re-optimize          # Re-optimize on crisis/breakdown
  GET    /api/v1/routes/driver/{driver_id}/active # Active route for a driver
  ```

- [ ] **3.3 — Geofencing (Logistic Manager)**
  - Define polygon geofences around warehouses/delivery zones
  - Trigger events on vehicle enter/exit
  - Security alerts for unauthorized movement

  ```
  GET    /api/v1/geofences                        # List geofences
  POST   /api/v1/geofences                        # Create geofence (polygon JSON)
  GET    /api/v1/geofences/{id}                   # Detail
  PUT    /api/v1/geofences/{id}                   # Update
  DELETE /api/v1/geofences/{id}                   # Delete
  POST   /api/v1/geofences/check                  # Check if lat/lng is inside any geofence
  GET    /api/v1/geofences/events                 # Geofence event history
  ```

- [ ] **3.4 — Manifest Center (Dispatcher)**
  - Generate digital manifests per route
  - Export manifest as PDF

  ```
  GET    /api/v1/manifests/route/{route_id}       # Get manifest for a route
  POST   /api/v1/manifests/route/{route_id}/generate  # Generate/regenerate manifest
  GET    /api/v1/manifests/route/{route_id}/export    # Download manifest PDF
  ```

---

## Phase 4 — Driver Mobile APIs

**Goal:** All endpoints consumed by the Driver PWA — shift lifecycle, delivery execution, and proofs.

### Milestones

- [ ] **4.1 — Shift Management**
  ```
  POST   /api/v1/driver/shift/start             # Start shift (vehicle binding, pre-inspection)
  POST   /api/v1/driver/shift/end               # End shift (generate summary)
  GET    /api/v1/driver/shift/summary           # Today's shift summary
  POST   /api/v1/driver/vehicle-inspection      # Submit pre/post-shift inspection checklist
  ```

- [ ] **4.2 — Delivery Execution**
  ```
  GET    /api/v1/driver/manifest                # Driver's active manifest
  PUT    /api/v1/driver/location                # Push live GPS position
  POST   /api/v1/driver/stop/{stop_id}/arrive   # Mark arrival at stop (triggers geofence)
  POST   /api/v1/driver/stop/{stop_id}/depart   # Mark departure
  POST   /api/v1/driver/stop/{stop_id}/pod      # Submit Proof of Delivery (photo, signature, QR)
  POST   /api/v1/driver/stop/{stop_id}/cod      # Record COD collection
  POST   /api/v1/driver/stop/{stop_id}/damage   # Submit damage report
  ```

- [ ] **4.3 — Incidents & Support**
  ```
  POST   /api/v1/driver/crisis                  # Report breakdown / emergency
  POST   /api/v1/driver/deviation               # Log unauthorized route deviation
  POST   /api/v1/driver/fuel-receipt            # Upload fuel receipt (OCR processed)
  ```

- [ ] **4.4 — Driver Performance & Earnings**
  ```
  GET    /api/v1/driver/wallet                  # Earnings breakdown
  GET    /api/v1/driver/safety-score            # Safety score details
  GET    /api/v1/driver/performance             # Historical performance
  GET    /api/v1/driver/offline-queue           # Pending offline actions to sync
  POST   /api/v1/driver/offline-queue/sync      # Bulk sync offline operations
  ```

---

## Phase 5 — AI & Intelligence Layer

**Goal:** Gemini AI integration for NL analytics, volume estimator, and AI support bot.

### Milestones

- [x] **5.1 — AI Support Bot (Customer Facing) — Core done, escalations remaining**
  - [x] Session-based chat with order context
  - [x] Intent classification: db_query, general, greeting, error
  - [x] NL-to-SQL pipeline (Gemini function-calling → SQL validator → read-only DB → natural language summary)
  - [ ] Sentiment analysis — escalation trigger if score falls below threshold
  - [x] Autonomous escalation: manual trigger via API
  - [ ] Autonomous escalation: auto-trigger on sentiment threshold

  **Done:**
  ```
  POST   /api/v1/ai/chat                          # Send message to AI bot
  GET    /api/v1/ai/conversations/{session_id}    # Get conversation history
  GET    /api/v1/ai/sessions                      # List user's chat sessions
  POST   /api/v1/ai/escalate/{conversation_id}    # Manually escalate to human
  GET    /api/v1/ai/escalations                   # List active escalations (human agent view)
  PUT    /api/v1/ai/escalations/{id}/resolve      # Resolve escalation
  ```

- [ ] **5.2 — Natural Language Analytics (Manager)**
  - RAG pipeline on top of PostgreSQL data
  - Accepts plain-English queries and returns structured charts/data
  - **Note:** NL-to-SQL is already working inside the Phase 5.1 chat endpoint (intent `db_query`).
    5.2 is a *separate, dedicated* manager-facing interface: structured JSON output with chart
    config, preset query suggestions, and no conversational context — designed for dashboards,
    not chat. The `/api/v1/ai/query` endpoint must still be built as its own thing.

  ```
  POST   /api/v1/ai/query                         # NL query → data + chart config
  GET    /api/v1/ai/query/suggestions             # Preset example queries
  ```

- [ ] **5.3 — AI Volume Estimator (Individual/Vendor)**
  - Accept room photos via upload
  - Call Gemini Vision API to estimate box count, labourer count, vehicle type

  ```
  POST   /api/v1/ai/volume-estimate               # Upload photos → estimate response
  ```

- [ ] **5.4 — Predictive Labor Scaling (Logistic Manager)**
  - Analyse historical order volumes per hub
  - Suggest staff reallocation across warehouses

  ```
  GET    /api/v1/ai/labor-forecast                # Predictions for next 7 days per warehouse
  GET    /api/v1/ai/labor-recommendations         # Cross-hub staff shift suggestions
  ```

- [ ] **5.5 — Smart Parking Assistant (Driver)**
  ```
  GET    /api/v1/ai/parking-suggestions           # Suggest parking near delivery address
  ```

- [ ] **5.6 — Knowledge Base Management (AI Agent)**
  ```
  GET    /api/v1/ai/knowledge-base                # List KB articles
  POST   /api/v1/ai/knowledge-base                # Add article
  PUT    /api/v1/ai/knowledge-base/{id}           # Update article
  DELETE /api/v1/ai/knowledge-base/{id}           # Delete article
  ```

---

## Phase 6 — Finance, Payroll & Reporting

**Goal:** COD reconciliation, payroll automation, invoicing, and analytics reports.

### Milestones

- [ ] **6.1 — COD & Payments**
  ```
  GET    /api/v1/finance/cod                      # List COD transactions
  PUT    /api/v1/finance/cod/{id}/reconcile       # Mark COD as reconciled
  GET    /api/v1/finance/cod/summary              # COD totals per driver / date
  ```

- [ ] **6.2 — Payroll**
  - Auto-calculate pay: base + distance bonus + performance bonus
  - Celery task runs payroll at end of each pay period

  ```
  GET    /api/v1/finance/payroll                  # List payroll records
  POST   /api/v1/finance/payroll/run              # Trigger payroll calculation (Celery task)
  GET    /api/v1/finance/payroll/{id}             # Payroll record detail
  POST   /api/v1/finance/payroll/{id}/approve     # Approve a payroll record
  ```

- [ ] **6.3 — Invoicing (Vendor)**
  ```
  GET    /api/v1/finance/invoices                 # List invoices
  POST   /api/v1/finance/invoices                 # Generate invoice for order
  GET    /api/v1/finance/invoices/{id}            # Invoice detail
  GET    /api/v1/finance/invoices/{id}/download   # Download PDF
  ```

- [ ] **6.4 — Reports & Analytics**
  ```
  GET    /api/v1/reports/kpis                     # Top-level KPI summary
  GET    /api/v1/reports/orders                   # Order volume over time
  GET    /api/v1/reports/drivers                  # Driver performance report
  GET    /api/v1/reports/fleet                    # Fleet utilization
  GET    /api/v1/reports/warehouse/{id}           # Warehouse metrics
  GET    /api/v1/reports/finance                  # Revenue and cost report
  POST   /api/v1/reports/export                   # Export report as CSV/PDF (Celery)
  ```

- [ ] **6.5 — Reverse Logistics**
  ```
  POST   /api/v1/reverse-logistics/return         # Create return order
  GET    /api/v1/reverse-logistics                 # List return orders
  PUT    /api/v1/reverse-logistics/{id}/status     # Update return status
  POST   /api/v1/reverse-logistics/{id}/refund     # Trigger refund process
  ```

---

## Phase 7 — Real-Time, Notifications & WebSockets

**Goal:** Live GPS map, driver status updates, and in-app + push notifications.

### Milestones

- [ ] **7.1 — WebSocket Connections**
  ```
  WS     /api/v1/ws/fleet-map                     # Live vehicle positions (Logistic/Dispatcher)
  WS     /api/v1/ws/route/{route_id}              # Live route progress for a specific route
  WS     /api/v1/ws/ai-chat/{session_id}          # Streaming AI chat responses
  WS     /api/v1/ws/notifications/{user_id}       # Real-time in-app notifications
  ```

- [ ] **7.2 — Notification System**
  - In-app notification store (DB backed)
  - Celery tasks for email/SMS dispatch
  - Driver "arriving soon" push notification (triggered at 50m geofence)

  ```
  GET    /api/v1/notifications                    # User's notifications (unread first)
  POST   /api/v1/notifications/{id}/read          # Mark as read
  POST   /api/v1/notifications/read-all           # Mark all as read
  ```

---

## Phase 8 — Hardening, Testing & Deployment

**Goal:** Production-ready, secure, well-tested deployment.

### Milestones

- [ ] **8.1 — Testing**
  - Unit tests: service layer (pytest + mock DB)
  - Integration tests: full request lifecycle with test PostgreSQL
  - Auth edge cases: expired tokens, role violations
  - Target: ≥ 80% coverage

- [ ] **8.2 — Security Hardening**
  - Rate limiting (slowapi / Redis)
  - CORS locked to frontend origin
  - Request validation (Pydantic strict mode)
  - SQL injection prevention (ORM only, no raw queries)
  - File upload validation (MIME type, size limits)
  - Sensitive data masking in logs

- [ ] **8.3 — Performance**
  - Database indexes on: `order.status`, `route.driver_id`, `inventory.warehouse_id`, `users.role`
  - Redis caching for expensive aggregate queries (KPIs, reports)
  - Pagination enforced on all list endpoints (default max 100)
  - Connection pooling tuned for async workload

- [ ] **8.4 — Deployment**
  - Dockerfile multi-stage build
  - `docker-compose.yml` for full local stack (app + DB + Redis)
  - Environment variables documented in `.env.example`
  - Health check endpoint: `GET /health`
  - Alembic migration run on container startup
  - Structured JSON logging (uvicorn + loguru)

---

## API Versioning Strategy

All endpoints are prefixed with `/api/v1/`. When breaking changes are introduced, a `/api/v2/` prefix will be used with a deprecation notice on v1. Non-breaking additions (new fields, new endpoints) do not require a version bump.

---

## Environment & Configuration

The following environment variables are required (stored in `.env`):

```dotenv
# App
APP_ENV=development
SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/logistics_db

# Redis
REDIS_URL=redis://redis:6379/0

# Google APIs
GOOGLE_MAPS_API_KEY=
GEMINI_API_KEY=

# File Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10

# Email / SMS (optional for Phase 1)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
```

---

## Implementation Priority Summary

| Phase | Module | Priority | Estimated Effort |
|---|---|---|---|
| 1 | Foundation & Auth | 🔴 Critical | 1 week |
| 2 | Users, Orders, Inventory, Labour | 🔴 Critical | 2 weeks |
| 3 | Fleet, Routes, Geofencing, Manifests | 🔴 Critical | 2 weeks |
| 4 | Driver Mobile APIs | 🟠 High | 1.5 weeks |
| 5 | AI & Intelligence | 🟠 High | 2 weeks |
| 6 | Finance, Payroll, Reports | 🟡 Medium | 1.5 weeks |
| 7 | Real-Time & WebSockets | 🟡 Medium | 1 week |
| 8 | Hardening, Tests, Deployment | 🟢 Ongoing | 1 week |

**Total estimated first-pass: ~12 weeks**
