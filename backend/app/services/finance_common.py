"""Helpers the finance recorders and the finance summary share: today's date, warehouse resolution and legacy order revenue."""

from datetime import UTC, date, datetime
from uuid import UUID

from app.models.logistics import LogisticsTransaction
from app.models.order import Order

# ── helpers ────────────────────────────────────────────────────────────────


def _today() -> date:
    return datetime.now(UTC).date()


def _coerce_uuid(value) -> UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def resolve_transaction_warehouse_id(
    tx: LogisticsTransaction,
    order_warehouse_by_id: dict[UUID, UUID | None],
    order_warehouse_by_tracking: dict[str, UUID | None],
    user_warehouse_by_id: dict[UUID, UUID | None],
) -> UUID | None:
    if tx.warehouse_id:
        return tx.warehouse_id

    metadata = tx.metadata_json or {}

    order_id = _coerce_uuid(metadata.get("order_id"))
    if order_id in order_warehouse_by_id:
        return order_warehouse_by_id[order_id]

    tracking_code = metadata.get("tracking_code")
    if tracking_code and tracking_code in order_warehouse_by_tracking:
        return order_warehouse_by_tracking[tracking_code]

    user_id = _coerce_uuid(metadata.get("user_id") or metadata.get("collected_by"))
    if user_id in user_warehouse_by_id:
        return user_warehouse_by_id[user_id]

    return None


def _legacy_order_revenue_amount(order: Order, recorded_payment_total: float) -> float:
    if recorded_payment_total > 0:
        return 0.0
    if order.payment_status != "paid":
        return 0.0
    if order.status in {"CANCELLED", "DRAFT"}:
        return 0.0
    return float(order.paid_amount or order.total_amount or 0.0)
