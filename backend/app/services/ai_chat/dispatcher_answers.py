"""Dispatcher snapshot and the shortcut answers built from it."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import (
    LogisticsDriverProfile,
    LogisticsVehicle,
)
from app.models.order import Order
from app.models.user import User
from app.schemas.ai import (
    ChatResponse,
)
from app.services.ai_chat.conversations import _persist_message
from app.services.ai_chat.staff_intents import _is_dispatcher_chat_context
from app.services.ai_chat.support_handoff import _answer_with_grounded_ai


async def _build_dispatcher_snapshot(ro_db: AsyncSession) -> dict:
    """Fetch live operational data for the dispatcher AI context."""

    # Orders needing driver assignment (released / confirmed, vehicle assigned, no driver yet)
    pending_dispatch_result = await ro_db.execute(
        select(Order)
        .where(
            Order.status.in_(["CONFIRMED", "ASSIGNED"]),
            Order.assigned_driver_id.is_(None),
            Order.assigned_vehicle_id.isnot(None),
        )
        .order_by(Order.created_at.asc())
        .limit(10)
    )
    pending_dispatch = list(pending_dispatch_result.scalars().all())

    # Active in-transit orders
    in_transit_result = await ro_db.execute(
        select(Order, User.name)
        .join(User, User.id == Order.assigned_driver_id, isouter=True)
        .where(Order.status == "IN_TRANSIT")
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    in_transit_rows = in_transit_result.all()

    # Driver availability
    driver_result = await ro_db.execute(
        select(LogisticsDriverProfile, User.name)
        .join(User, User.id == LogisticsDriverProfile.user_id)
        .order_by(User.name.asc())
    )
    driver_rows = driver_result.all()

    # Free drivers (Active status, no current job)
    free_drivers = [
        (profile, name)
        for profile, name in driver_rows
        if (profile.status or "").lower() == "active" and not profile.current_job
    ]

    # Vehicles
    vehicle_result = await ro_db.execute(
        select(LogisticsVehicle)
        .where(LogisticsVehicle.status == "Active")
        .order_by(LogisticsVehicle.code.asc())
        .limit(20)
    )
    active_vehicles = list(vehicle_result.scalars().all())

    # SLA at risk (orders past scheduled time, not yet delivered)
    now = datetime.now(UTC)
    sla_risk_result = await ro_db.execute(
        select(Order)
        .where(
            Order.status.in_(["CONFIRMED", "ASSIGNED", "IN_TRANSIT"]),
            Order.scheduled_at < now,
        )
        .order_by(Order.scheduled_at.asc())
        .limit(5)
    )
    sla_risk = list(sla_risk_result.scalars().all())

    # Today deliveries
    today_count = int(
        (
            await ro_db.execute(
                select(func.count(Order.id)).where(
                    Order.status == "DELIVERED",
                    func.date(Order.delivered_at) == func.current_date(),
                )
            )
        ).scalar_one()
        or 0
    )

    # Build facts list
    driver_status_counts: dict[str, int] = {}
    for profile, _ in driver_rows:
        key = (profile.status or "unknown").strip().lower()
        driver_status_counts[key] = driver_status_counts.get(key, 0) + 1

    facts = [
        f"Total drivers registered: {len(driver_rows)}",
        f"Free/available drivers right now: {len(free_drivers)}",
        f"Driver status breakdown: {', '.join(f'{k}: {v}' for k, v in driver_status_counts.items())}",
        f"Orders waiting for driver assignment: {len(pending_dispatch)}",
        f"Orders currently in transit: {len(in_transit_rows)}",
        f"Active vehicles available: {len(active_vehicles)}",
        f"SLA at risk (overdue): {len(sla_risk)}",
        f"Deliveries completed today: {today_count}",
    ]
    if free_drivers:
        facts.append("Free drivers: " + ", ".join(name for _, name in free_drivers[:5]))
    if pending_dispatch:
        facts.append(
            "Top pending orders needing drivers: "
            + ", ".join(
                f"{o.tracking_code or str(o.id)[:8]} ({o.pickup_addr or 'TBD'} → {o.delivery_addr or 'TBD'})"
                for o in pending_dispatch[:3]
            )
        )
    if sla_risk:
        facts.append(
            "SLA-at-risk orders: "
            + ", ".join(
                f"{o.tracking_code or str(o.id)[:8]} (scheduled {o.scheduled_at.strftime('%H:%M') if o.scheduled_at else 'N/A'})"
                for o in sla_risk[:3]
            )
        )

    return {
        "pending_dispatch": pending_dispatch,
        "in_transit_rows": in_transit_rows,
        "driver_rows": driver_rows,
        "free_drivers": free_drivers,
        "active_vehicles": active_vehicles,
        "sla_risk": sla_risk,
        "today_count": today_count,
        "driver_status_counts": driver_status_counts,
        "facts": facts,
    }


def _is_dispatcher_pending_question(msg: str) -> bool:
    return any(k in msg for k in ["pending order", "ready order", "waiting for driver", "need driver", "unassigned order", "released order", "dispatch queue"])


def _is_dispatcher_driver_question(msg: str) -> bool:
    return any(k in msg for k in ["driver", "who is free", "available driver", "best driver", "suggest driver", "free driver", "driver available", "driver status"])


def _is_dispatcher_fleet_question(msg: str) -> bool:
    return any(k in msg for k in ["vehicle", "fleet", "truck", "van", "lcv"])


def _is_dispatcher_in_transit_question(msg: str) -> bool:
    return any(k in msg for k in ["in transit", "active order", "on route", "in delivery", "currently delivering", "active delivery"])


def _is_dispatcher_sla_question(msg: str) -> bool:
    return any(k in msg for k in ["sla", "overdue", "late", "delay", "at risk", "behind schedule"])


def _dispatcher_pending_message(snapshot: dict) -> str:
    orders = snapshot["pending_dispatch"]
    if not orders:
        return "No orders are currently waiting for driver assignment. All released orders are covered."
    lines = [f"**{len(orders)} order(s)** waiting for driver assignment right now:"]
    for o in orders[:5]:
        lines.append(
            f"- **{o.tracking_code or str(o.id)[:8]}** | {o.pickup_addr or 'TBD'} → {o.delivery_addr or 'TBD'} | Created: {o.created_at.strftime('%d %b %H:%M') if o.created_at else 'N/A'}"
        )
    return "\n".join(lines)


def _dispatcher_driver_message(snapshot: dict) -> str:
    free = snapshot["free_drivers"]
    total = len(snapshot["driver_rows"])
    counts = snapshot["driver_status_counts"]
    lines = [
        f"**{total}** drivers registered. **{len(free)}** are currently free and available.",
        f"Status breakdown: {', '.join(f'{k.capitalize()}: {v}' for k, v in counts.items())}",
    ]
    if free:
        lines.append("Free drivers (best candidates for assignment):")
        for profile, name in free[:5]:
            lines.append(
                f"- **{name}** | Location: {profile.current_location or 'Unknown'} | Efficiency: {profile.efficiency_score}%"
            )
    else:
        lines.append("No drivers are currently free. All drivers are on jobs or off-shift.")
    pending = snapshot["pending_dispatch"]
    if pending and free:
        lines.append(
            f"\nTop match: assign **{free[0][1]}** to order **{pending[0].tracking_code or str(pending[0].id)[:8]}** "
            f"({pending[0].pickup_addr or 'TBD'} → {pending[0].delivery_addr or 'TBD'})."
        )
    return "\n".join(lines)


def _dispatcher_fleet_message(snapshot: dict) -> str:
    vehicles = snapshot["active_vehicles"]
    if not vehicles:
        return "No active vehicles found in the fleet right now."
    lines = [f"**{len(vehicles)}** active vehicles available:"]
    for v in vehicles[:8]:
        lines.append(
            f"- **{v.code}** ({v.vehicle_type}) | Plate: {v.license_plate or 'N/A'} | Status: {v.status}"
        )
    return "\n".join(lines)


def _dispatcher_in_transit_message(snapshot: dict) -> str:
    rows = snapshot["in_transit_rows"]
    if not rows:
        return "No orders are currently in transit."
    lines = [f"**{len(rows)}** order(s) currently in transit:"]
    for o, driver_name in rows[:5]:
        lines.append(
            f"- **{o.tracking_code or str(o.id)[:8]}** | Driver: {driver_name or 'Unassigned'} | {o.pickup_addr or 'TBD'} → {o.delivery_addr or 'TBD'}"
        )
    return "\n".join(lines)


def _dispatcher_sla_message(snapshot: dict) -> str:
    at_risk = snapshot["sla_risk"]
    today = snapshot["today_count"]
    lines = [f"Deliveries completed today: **{today}**."]
    if at_risk:
        lines.append(f"**{len(at_risk)}** order(s) are past their scheduled delivery window (SLA at risk):")
        for o in at_risk:
            lines.append(
                f"- **{o.tracking_code or str(o.id)[:8]}** | Status: {o.status} | Scheduled: {o.scheduled_at.strftime('%d %b %H:%M') if o.scheduled_at else 'N/A'}"
            )
    else:
        lines.append("No SLA breaches detected. All active orders are within their delivery windows.")
    return "\n".join(lines)


async def _try_handle_dispatcher_shortcuts(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    chat_context: str | None,
) -> "ChatResponse | None":
    if not _is_dispatcher_chat_context(user, chat_context):
        return None

    snapshot = await _build_dispatcher_snapshot(ro_db)
    msg = (user_message or "").strip().lower()
    base_message = None

    if _is_dispatcher_pending_question(msg):
        base_message = _dispatcher_pending_message(snapshot)
    elif _is_dispatcher_driver_question(msg):
        base_message = _dispatcher_driver_message(snapshot)
    elif _is_dispatcher_fleet_question(msg):
        base_message = _dispatcher_fleet_message(snapshot)
    elif _is_dispatcher_in_transit_question(msg):
        base_message = _dispatcher_in_transit_message(snapshot)
    elif _is_dispatcher_sla_question(msg):
        base_message = _dispatcher_sla_message(snapshot)

    if not base_message:
        return None

    assistant_message = await _answer_with_grounded_ai(
        user=user,
        user_message=user_message,
        fallback_message=base_message,
        grounding_facts=snapshot["facts"] + [base_message],
    )
    await _persist_message(db, session_id, user.id, "user", user_message, "db_query")
    await _persist_message(db, session_id, user.id, "assistant", assistant_message, "db_query")
    await db.commit()
    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent="db_query",
        sql_generated=None,
    )
