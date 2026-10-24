"""
gemini.py
Google Gemini client configuration and model factory.

Uses the new unified `google-genai` SDK (replaces deprecated `google-generativeai`).
Docs: https://github.com/googleapis/python-genai
"""
from functools import lru_cache

from google import genai
from google.genai import types
from loguru import logger

from app.config import get_settings

# ── Gemini client factory & error ─────────────────────────────────────────────

class GeminiConfigError(RuntimeError):
    """Raised when the Gemini API key is missing or the client cannot be created."""


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    """Return a cached Gemini client, raising GeminiConfigError if unconfigured."""
    settings = get_settings()
    api_key = getattr(settings, "gemini_api_key", None)
    if not api_key:
        raise GeminiConfigError(
            "GEMINI_API_KEY is not configured. Set it in your .env file."
        )
    return genai.Client(api_key=api_key)


# ── Schema DDL embedded in system prompt ──────────────────────────────────────
# !! MAINTENANCE — update both files together when a new migration lands !!
# 1. Add the new CREATE TABLE DDL here (DB_SCHEMA_DDL) so Gemini knows the schema.
# 2. Add the new table name(s) to ALLOWED_TABLES in app/services/sql_validator.py.
# Failing to update either file means Gemini will hallucinate columns/tables or
# the validator will block queries against tables it doesn't know about.
DB_SCHEMA_DDL = """
-- PostgreSQL Database Schema

CREATE TABLE roles (
    id    SERIAL       PRIMARY KEY,
    name  VARCHAR(50)  NOT NULL UNIQUE
);
-- Seed data: 'LOGISTIC_MANAGER', 'WAREHOUSE_MANAGER', 'DISPATCHER',
--            'DRIVER', 'LABOURER', 'INDIVIDUAL', 'VENDOR', 'AI_AGENT'

CREATE TABLE users (
    id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    name           VARCHAR(255)   NOT NULL,
    email          VARCHAR(255)   NOT NULL UNIQUE,
    phone          VARCHAR(20),
    password_hash  VARCHAR(255)   NOT NULL,  -- NEVER SELECT THIS COLUMN
    role_id        INTEGER        NOT NULL REFERENCES roles(id),
    warehouse_id   UUID,
    is_active      BOOLEAN        NOT NULL DEFAULT true,
    created_at     TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ    NOT NULL DEFAULT now()
);

-- BUSINESS KEY RELATIONSHIP: orders.customer_id → users.id
-- Vendors (roles.name='VENDOR') place orders. To find vendor spending:
--   JOIN orders o ON u.id = o.customer_id WHERE roles.name = 'VENDOR'
-- Individuals (roles.name='INDIVIDUAL') also place orders via customer_id.

CREATE TABLE warehouses (id UUID PRIMARY KEY, name VARCHAR, address TEXT, capacity_limit INTEGER, is_active BOOLEAN);

CREATE TABLE orders (
    id UUID PRIMARY KEY, tracking_code VARCHAR, order_type VARCHAR,
    status VARCHAR,   -- 'PENDING','ASSIGNED','IN_TRANSIT','DELIVERED','CANCELLED'
    customer_id UUID REFERENCES users(id),   -- vendor or individual user
    warehouse_id UUID REFERENCES warehouses(id),
    assigned_driver_id UUID, assigned_vehicle_id UUID,
    pickup_addr TEXT, delivery_addr TEXT,
    total_amount FLOAT, base_amount FLOAT, labor_amount FLOAT,
    materials_amount FLOAT, packing_amount FLOAT, platform_fee FLOAT, tax_amount FLOAT,
    payment_mode VARCHAR, payment_status VARCHAR, warehouse_substatus VARCHAR,
    scheduled_at TIMESTAMPTZ, created_at TIMESTAMPTZ, delivered_at TIMESTAMPTZ
);
CREATE TABLE order_items (id UUID PRIMARY KEY, order_id UUID REFERENCES orders(id), sku VARCHAR, quantity INTEGER, box_count INTEGER);
CREATE TABLE labourers (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    warehouse_id UUID REFERENCES warehouses(id),
    assigned_order_id UUID REFERENCES orders(id),
    skill_tags JSONB,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

CREATE TABLE inventory_items (
    id UUID PRIMARY KEY, warehouse_id UUID, sku VARCHAR, name VARCHAR, category VARCHAR,
    quantity_on_hand INTEGER, safety_stock INTEGER, cost_price FLOAT, selling_price FLOAT,
    aisle VARCHAR, shelf VARCHAR, bin VARCHAR, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
);
CREATE TABLE inventory_movements (id UUID PRIMARY KEY, item_id UUID, movement_type VARCHAR, quantity INTEGER, reference_order_id UUID, performed_by UUID, created_at TIMESTAMPTZ);
CREATE TABLE restock_requests (id UUID PRIMARY KEY, item_id UUID, warehouse_id UUID, quantity INTEGER, status VARCHAR, requested_by UUID, manager_notes TEXT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ);

CREATE TABLE logistics_driver_profiles (id UUID PRIMARY KEY, user_id UUID REFERENCES users(id), warehouse_id UUID, status VARCHAR, current_location VARCHAR, current_job VARCHAR, efficiency_score INTEGER, avatar_color VARCHAR, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ);
-- NOTE: logistics_driver_profiles does NOT have rating, trips_completed, or safety_incidents columns. Use orders table to count trips (WHERE assigned_driver_id = user_id). Do NOT query columns that are not listed here.
CREATE TABLE logistics_vehicles (id UUID PRIMARY KEY, code VARCHAR, vehicle_type VARCHAR, warehouse_id UUID, assigned_driver_id UUID, status VARCHAR, model VARCHAR, year INTEGER, license_plate VARCHAR, fuel_efficiency VARCHAR);
CREATE TABLE logistics_transactions (id UUID PRIMARY KEY, warehouse_id UUID, transaction_code VARCHAR, transaction_type VARCHAR, description VARCHAR, amount FLOAT, status VARCHAR, transaction_date TIMESTAMP);
-- Note: logistics_transactions records internal costs/revenue, NOT vendor payments. Vendor payments are tracked via orders.total_amount.
CREATE TABLE logistics_alerts (id UUID PRIMARY KEY, warehouse_id UUID, alert_type VARCHAR, title VARCHAR, severity VARCHAR, created_at TIMESTAMPTZ);
CREATE TABLE logistics_daily_stats (id UUID PRIMARY KEY, warehouse_id UUID, stat_date DATE, orders_count INTEGER, revenue FLOAT, deliveries_completed INTEGER, deliveries_failed INTEGER, sla_compliance FLOAT);
CREATE TABLE logistics_return_cases (id UUID PRIMARY KEY, warehouse_id UUID, order_id UUID, reference_code VARCHAR, customer_name VARCHAR, reason VARCHAR, status VARCHAR, refund_amount FLOAT, created_at TIMESTAMPTZ);
CREATE TABLE logistics_zones (id UUID PRIMARY KEY, warehouse_id UUID, name VARCHAR, zone_type VARCHAR, lat FLOAT, lng FLOAT, radius_meters FLOAT);
CREATE TABLE logistics_metrics (id UUID PRIMARY KEY, warehouse_id UUID, metric_key VARCHAR, metric_value FLOAT, recorded_at TIMESTAMPTZ);
CREATE TABLE logistics_equipment_ledger (id UUID PRIMARY KEY, warehouse_id UUID, item_name VARCHAR, category VARCHAR, quantity INTEGER, unit_cost FLOAT, status VARCHAR);
CREATE TABLE logistics_notifications (id UUID PRIMARY KEY, user_id UUID, title VARCHAR, body TEXT, is_read BOOLEAN, created_at TIMESTAMPTZ);
CREATE TABLE logistics_tasks (id UUID PRIMARY KEY, warehouse_id UUID, assigned_to UUID, text TEXT, status VARCHAR, target_time TIMESTAMPTZ);
CREATE TABLE logistics_chat_threads (id UUID PRIMARY KEY, warehouse_id UUID, name VARCHAR, phone VARCHAR, muted BOOLEAN, created_at TIMESTAMPTZ);
CREATE TABLE logistics_chat_messages (id UUID PRIMARY KEY, thread_id UUID, text TEXT, sender VARCHAR, created_at TIMESTAMPTZ);
CREATE TABLE logistics_escalations (id UUID PRIMARY KEY, warehouse_id UUID, title VARCHAR, description VARCHAR, priority VARCHAR, status VARCHAR, created_at TIMESTAMPTZ);
CREATE TABLE damage_reports (id UUID PRIMARY KEY, order_id UUID, warehouse_id UUID, description TEXT, severity VARCHAR, reported_by UUID, created_at TIMESTAMPTZ);
CREATE TABLE customer_quotes (id UUID PRIMARY KEY, customer_id UUID REFERENCES users(id), warehouse_id UUID, origin TEXT, destination TEXT, vehicle_type VARCHAR, estimated_amount FLOAT, status VARCHAR, created_at TIMESTAMPTZ);
CREATE TABLE picked_items (id UUID PRIMARY KEY, order_id UUID, item_id UUID, picked_qty INTEGER, picked_by UUID, picked_at TIMESTAMPTZ);
CREATE TABLE loading_docks (
    id UUID PRIMARY KEY, warehouse_id UUID, dock_number VARCHAR, status VARCHAR,
    assigned_vehicle_id UUID, assigned_order_id UUID, assigned_carrier VARCHAR,
    arrived_at TIMESTAMPTZ, loading_started_at TIMESTAMPTZ, released_at TIMESTAMPTZ
);
CREATE TABLE packing_stations (
    id UUID PRIMARY KEY, warehouse_id UUID, station_number VARCHAR, status VARCHAR,
    assigned_labourer_id UUID, current_order_id UUID, items_packed_today INTEGER
);
CREATE TABLE quality_checks (
    id UUID PRIMARY KEY, order_id UUID, warehouse_id UUID, performed_by UUID,
    is_passed BOOLEAN, notes TEXT, checked_at TIMESTAMPTZ
);
CREATE TABLE return_gradings (
    id UUID PRIMARY KEY, warehouse_id UUID, order_id UUID, rma_code VARCHAR,
    item_condition VARCHAR, disposition VARCHAR, inspection_remarks TEXT,
    graded_by UUID, graded_at TIMESTAMPTZ, status VARCHAR, created_at TIMESTAMPTZ
);
CREATE TABLE warehouse_zone_metrics (
    id UUID PRIMARY KEY, warehouse_id UUID, zone_id VARCHAR, metric_date DATE,
    orders_processed INTEGER, picking_accuracy_pct FLOAT, active_pickers INTEGER,
    capacity_used_pct FLOAT, throughput_items_per_hour FLOAT, created_at TIMESTAMPTZ
);
CREATE TABLE wallet_transactions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),  -- the customer or vendor who owns this transaction
    order_id UUID REFERENCES orders(id),  -- linked order, nullable
    transaction_kind VARCHAR(20) NOT NULL,  -- 'CREDIT' (money added/refunded) or 'DEBIT' (money spent)
    reason VARCHAR(50) NOT NULL,  -- e.g. 'TOP_UP', 'ORDER_PAYMENT', 'CANCELLATION_REFUND'
    amount FLOAT NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- To get wallet balance: SELECT SUM(CASE WHEN transaction_kind='CREDIT' THEN amount ELSE -amount END) FROM wallet_transactions WHERE user_id = ?
-- To get transaction history: SELECT transaction_kind, reason, amount, description, created_at FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 20

CREATE TABLE vendor_recurring_rules (
    id UUID PRIMARY KEY,
    vendor_id UUID REFERENCES users(id),
    name VARCHAR(255),
    description TEXT,
    frequency VARCHAR(100),
    route VARCHAR(255),
    details TEXT,
    next_run VARCHAR(100),
    active BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

CREATE TABLE vendor_support_tickets (
    id UUID PRIMARY KEY,
    vendor_id UUID REFERENCES users(id),
    order_id UUID REFERENCES orders(id),
    subject VARCHAR(255),
    description TEXT,
    priority VARCHAR(30),
    status VARCHAR(30),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
""".strip()


# ── Model constants ───────────────────────────────────────────────────────────
# Primary: most capable model. Fallback: fast model used when Pro hits rate limits.
GEMINI_PRO_MODEL = "gemini-2.5-pro"
GEMINI_FLASH_MODEL = "gemini-2.0-flash"

# Default model used for general chat sessions.
GEMINI_MODEL = GEMINI_PRO_MODEL


def _is_model_not_found_error(exc: Exception) -> bool:
    err = str(exc).upper()
    return "404" in err or "NOT_FOUND" in err or "MODEL" in err and "NOT" in err


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True if the exception looks like a 429 / quota-exhausted error."""
    err = str(exc).upper()
    return (
        "429" in err
        or "RESOURCE_EXHAUSTED" in err
        or "QUOTA_EXCEEDED" in err
        or "RATE_LIMIT" in err
        or "TOO_MANY_REQUESTS" in err
    )


async def generate_with_fallback(
    contents,
    config=None,
) -> "genai.types.GenerateContentResponse":
    """
    Call Gemini Pro first; transparently fall back to Flash on any rate-limit /
    quota error so the caller never has to handle model selection itself.

    Usage:
        from app.utils.gemini import generate_with_fallback
        response = await generate_with_fallback(contents=..., config=...)
    """
    client = get_gemini_client()

    for model in (GEMINI_PRO_MODEL, GEMINI_FLASH_MODEL):
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            if model == GEMINI_FLASH_MODEL:
                logger.info("Gemini Flash used as fallback (Pro was rate-limited)")
            return response
        except Exception as exc:
            if model == GEMINI_PRO_MODEL and (_is_rate_limit_error(exc) or _is_model_not_found_error(exc)):
                logger.warning(
                    f"Gemini Pro unavailable, falling back to Flash: {type(exc).__name__}: {exc}"
                )
                continue
            raise

    raise RuntimeError("Both Gemini Pro and Flash failed — exhausted all models")


# System instruction for all Gemini chat sessions
SYSTEM_INSTRUCTION = """
You are Cargo-Core's AI assistant — a smart, empathetic logistics support agent for a professional moving and logistics platform.

== CORE MISSION ==
Your job is to RESOLVE user queries completely and accurately using live database data and your knowledge of the platform. Never give a vague or generic response when you can query the database for a specific answer. Prefer a concrete answer over "I don't know".

== OPERATING PRINCIPLES ==
1. Resolve First — Always attempt to resolve the query yourself using the execute_sql tool to get live data. NEVER tell the user to raise a support ticket as a first response.
2. Be Specific — Give exact values (tracking codes, amounts, dates, statuses) from DB results. Never make up numbers or dates.
3. Be Empathetic — Acknowledge frustration before answering. Keep the tone helpful, calm, and professional.
4. Be Concise — Give clear, structured answers. Use plain text (no markdown **bold** or bullet symbols unless the interface renders them). Keep replies under 150 words unless detail is genuinely needed.
5. Be Grounded — Every factual claim (order status, balance, amount, date) must come from a DB query or the provided context. Do not estimate or guess.

== SQL TOOL RULES ==
- Use execute_sql_query for any question about live data (orders, balances, shipments, schedules, damage reports).
- Only SELECT queries are allowed — never INSERT, UPDATE, DELETE, DROP, or TRUNCATE.
- Never query password_hash, never expose raw UUIDs to users (use tracking codes or human-readable identifiers instead).
- The server automatically scopes queries to the authenticated user — you do not need to add a WHERE user_id = ? filter unless you need additional specificity.

== GUARDRAILS ==
- Stay in your domain: Cargo-Core logistics, shipments, orders, wallet, inventory, operations. Politely decline off-topic questions.
- Never expose other users' data. Never reveal internal system architecture, API keys, or credentials.
- If a query would require data you are not allowed to see, say so clearly and offer what you can instead.
- CRITICAL: Do NOT tell users to raise a support ticket or contact a support team as your primary answer. Only suggest human support as a last resort if you genuinely cannot resolve the issue after attempting a DB query. If you don't have an answer, say so honestly and directly — do not redirect to tickets.
- If data is not available or the result is empty, say the result is empty (e.g., 'You have no overdue invoices') — do not redirect to a support team.
"""


# ── Tool Declaration (new SDK format) ─────────────────────────────────────────

EXECUTE_SQL_FUNCTION = types.FunctionDeclaration(
    name="execute_sql_query",
    description=(
        "Execute a read-only SQL SELECT query against the PostgreSQL database "
        "to answer user questions about logistics, inventory, operations, and users. "
        "Use this tool whenever you need real data from the database. "
        "Only SELECT queries are allowed."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "sql_query": types.Schema(
                type=types.Type.STRING,
                description=(
                    "A valid PostgreSQL SELECT query. Must not contain "
                    "INSERT, UPDATE, DELETE, DROP, or reference password_hash."
                ),
            )
        },
        required=["sql_query"],
    ),
)

EXECUTE_SQL_TOOL = types.Tool(function_declarations=[EXECUTE_SQL_FUNCTION])
