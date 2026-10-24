"""Restricts generated SQL to the tables and rows a role may read."""

import re
import uuid
from datetime import datetime
from decimal import Decimal

from app.models.user import User
from app.services.ai_chat.constants import (
    SELF_SERVICE_ALLOWED_TABLES,
    SELF_SERVICE_ROLES,
    WAREHOUSE_MANAGER_ALLOWED_TABLES,
)
from app.services.ai_chat.intents import _role_name
from app.services.sql_validator import SQLValidationError


def _scope_sql_for_user(sql: str, user: User) -> str:
    role = _role_name(user)
    if role == "WAREHOUSE_MANAGER":
        warehouse_id = str(getattr(user, "warehouse_id", "") or "")
        user_id = str(user.id)
        if not warehouse_id:
            raise SQLValidationError("This warehouse manager account is not linked to a warehouse.")

        tables = _extract_table_names_for_scope(sql)
        disallowed = tables - WAREHOUSE_MANAGER_ALLOWED_TABLES
        if disallowed:
            raise SQLValidationError(
                "Warehouse manager AI access is limited to current-warehouse operational data. "
                f"Disallowed table(s): {sorted(disallowed)}"
            )

        scoped_sources = {
            "warehouses": f"(SELECT * FROM warehouses WHERE id = '{warehouse_id}'::uuid)",
            "orders": f"(SELECT * FROM orders WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "order_items": (
                "(SELECT oi.* FROM order_items oi "
                "JOIN orders o ON o.id = oi.order_id "
                f"WHERE o.warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "picked_items": (
                "(SELECT pi.* FROM picked_items pi "
                "JOIN orders o ON o.id = pi.order_id "
                f"WHERE o.warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "inventory_items": f"(SELECT * FROM inventory_items WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "inventory_movements": (
                "(SELECT im.* FROM inventory_movements im "
                "JOIN inventory_items ii ON ii.id = im.item_id "
                f"WHERE ii.warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "restock_requests": f"(SELECT * FROM restock_requests WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "labourers": f"(SELECT * FROM labourers WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "users": (
                "(SELECT * FROM users "
                f"WHERE warehouse_id = '{warehouse_id}'::uuid OR id = '{user_id}'::uuid)"
            ),
            "loading_docks": f"(SELECT * FROM loading_docks WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "packing_stations": f"(SELECT * FROM packing_stations WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "quality_checks": f"(SELECT * FROM quality_checks WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "return_gradings": f"(SELECT * FROM return_gradings WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "warehouse_zone_metrics": (
                f"(SELECT * FROM warehouse_zone_metrics WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_return_cases": (
                f"(SELECT * FROM logistics_return_cases WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_alerts": f"(SELECT * FROM logistics_alerts WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "logistics_daily_stats": (
                f"(SELECT * FROM logistics_daily_stats WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_driver_profiles": (
                f"(SELECT * FROM logistics_driver_profiles WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_vehicles": (
                f"(SELECT * FROM logistics_vehicles WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_transactions": (
                f"(SELECT * FROM logistics_transactions WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_zones": f"(SELECT * FROM logistics_zones WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "logistics_metrics": f"(SELECT * FROM logistics_metrics WHERE warehouse_id = '{warehouse_id}'::uuid)",
            "logistics_chat_threads": (
                f"(SELECT * FROM logistics_chat_threads WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_chat_messages": (
                "(SELECT m.* FROM logistics_chat_messages m "
                "JOIN logistics_chat_threads t ON t.id = m.thread_id "
                f"WHERE t.warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "logistics_escalations": (
                f"(SELECT * FROM logistics_escalations WHERE warehouse_id = '{warehouse_id}'::uuid)"
            ),
            "damage_reports": (
                "(SELECT dr.* FROM damage_reports dr "
                "JOIN orders o ON o.id = dr.order_id "
                f"WHERE o.warehouse_id = '{warehouse_id}'::uuid)"
            ),
        }

        scoped_sql = _normalize_common_sql_aliases(sql)
        for table, subquery in scoped_sources.items():
            pattern = rf"(?i)\b(FROM|JOIN)\s+{table}\b"
            scoped_sql = re.sub(
                pattern,
                lambda m, sq=subquery, alias=table: f"{m.group(1)} {sq} {alias}",
                scoped_sql,
            )
        return scoped_sql

    if role not in SELF_SERVICE_ROLES:
        return sql

    tables = _extract_table_names_for_scope(sql)
    disallowed = tables - SELF_SERVICE_ALLOWED_TABLES
    if disallowed:
        raise SQLValidationError(
            "This account can only access personal shipment/payment data. "
            f"Disallowed table(s): {sorted(disallowed)}"
        )

    user_id = str(user.id)
    scoped_sources = {
        "orders": (
            "(SELECT * FROM orders WHERE customer_id = "
            f"'{user_id}'::uuid)"
        ),
        "order_items": (
            "(SELECT oi.* FROM order_items oi "
            "JOIN orders o ON o.id = oi.order_id "
            f"WHERE o.customer_id = '{user_id}'::uuid)"
        ),
        "picked_items": (
            "(SELECT pi.* FROM picked_items pi "
            "JOIN orders o ON o.id = pi.order_id "
            f"WHERE o.customer_id = '{user_id}'::uuid)"
        ),
        "customer_quotes": (
            "(SELECT * FROM customer_quotes WHERE customer_id = "
            f"'{user_id}'::uuid)"
        ),
        "damage_reports": (
            "(SELECT dr.* FROM damage_reports dr "
            "JOIN orders o ON o.id = dr.order_id "
            f"WHERE o.customer_id = '{user_id}'::uuid)"
        ),
        "users": (
            "(SELECT * FROM users WHERE id = "
            f"'{user_id}'::uuid)"
        ),
        "wallet_transactions": (
            "(SELECT * FROM wallet_transactions WHERE user_id = "
            f"'{user_id}'::uuid)"
        ),
        "vendor_recurring_rules": (
            "(SELECT * FROM vendor_recurring_rules WHERE vendor_id = "
            f"'{user_id}'::uuid)"
        ),
        "vendor_support_tickets": (
            "(SELECT * FROM vendor_support_tickets WHERE vendor_id = "
            f"'{user_id}'::uuid)"
        ),
    }

    scoped_sql = _normalize_common_sql_aliases(sql)
    for table, subquery in scoped_sources.items():
        pattern = rf"(?i)\b(FROM|JOIN)\s+{table}\b"
        scoped_sql = re.sub(
            pattern,
            lambda m, sq=subquery, t=table: f"{m.group(1)} {sq} {t}",
            scoped_sql,
        )

    return scoped_sql


def _normalize_common_sql_aliases(sql: str) -> str:
    normalized = sql
    replacements = {
        "customer_name": "customer_id",
        "customer_phone": "customer_id",
        "order_date": "created_at",
        "pickup_address": "pickup_addr",
        "delivery_address": "delivery_addr",
        "base_cost": "base_amount",
        "labor_cost": "labor_amount",
    }
    for old, new in replacements.items():
        normalized = re.sub(rf"(?i)\b{old}\b", new, normalized)
    return normalized


def _make_json_serializable(data: list[dict]) -> list[dict]:
    """Convert non-JSON-serializable types to strings."""
    serialized = []
    for row in data:
        clean_row = {}
        for key, value in row.items():
            if isinstance(value, (datetime,)):
                clean_row[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                clean_row[key] = str(value)
            elif isinstance(value, Decimal):
                # Convert Decimal to float (or int if it's a whole number)
                clean_row[key] = int(value) if value == value.to_integral_value() else float(value)
            elif isinstance(value, bytes):
                clean_row[key] = value.decode("utf-8", errors="replace")
            else:
                clean_row[key] = value
        serialized.append(clean_row)
    return serialized


def _format_results_fallback(results: list[dict], columns: list[str]) -> str:
    """Format query results as a readable string when Gemini fails to respond."""
    if not results:
        return "The query returned no results."

    if len(results) == 1 and len(columns) == 1:
        # Single value (e.g., COUNT)
        val = list(results[0].values())[0]
        return f"Result: {val}"

    # Simple table format
    lines = [f"Query returned {len(results)} row(s):"]
    lines.append(" | ".join(columns))
    lines.append("-" * (len(" | ".join(columns))))
    for row in results[:20]:  # Cap display at 20 rows
        lines.append(" | ".join(str(row.get(c, "")) for c in columns))

    if len(results) > 20:
        lines.append(f"... and {len(results) - 20} more rows")

    return "\n".join(lines)


def _extract_table_names_for_scope(sql: str) -> set[str]:
    pattern = r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    matches = re.findall(pattern, sql, re.IGNORECASE)
    tables: set[str] = set()
    for match in matches:
        name = match.lower().strip()
        if name not in {"select", "lateral", "unnest", "generate_series", "values"}:
            tables.add(name)
    return tables
