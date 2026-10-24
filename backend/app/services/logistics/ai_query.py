"""Answers logistics manager questions from live data, with Gemini when it is configured."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.logistics import (
    LogisticsAiQueryResponse,
)
from app.services.logistics.bootstrap import build_bootstrap


async def answer_ai_query(db: AsyncSession, query: str) -> LogisticsAiQueryResponse:
    """
    AI-powered query handler for Logistic Manager.
    Provides comprehensive insights across all operational areas.
    """
    bootstrap = await build_bootstrap(db)
    lower_query = query.lower()

    # Greetings
    if any(keyword in lower_query for keyword in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy")):
        stats = bootstrap.dashboard_stats
        greetings = ["Hey there!", "Hello!", "Hi!", "Howdy!"]
        import random
        greeting = random.choice(greetings)
        return LogisticsAiQueryResponse(
            text=f"{greeting} Great to see you! I'm your Cargo-Core AI assistant. Right now you have <b>{stats.orders_today} orders</b> today and <b>{stats.active_deliveries}</b> active deliveries. What would you like to know about?",
            data={
                "orders_today": stats.orders_today,
                "active_deliveries": stats.active_deliveries,
                "open_alerts": len(bootstrap.alerts),
                "tip": "Try asking: 'How are my drivers doing?' or 'Show fleet status'",
            },
        )

    # Dashboard / Overview queries
    if any(keyword in lower_query for keyword in ("dashboard", "overview", "summary", "status", "today", "how are we doing", "what's happening")):
        stats = bootstrap.dashboard_stats
        greeting = "Great question! " if stats.delivery_success >= 90 else "Here's the scoop! "
        mood = "Things are looking solid today!" if stats.delivery_success >= 90 else "We've got some work to do, but nothing we can't handle!"
        return LogisticsAiQueryResponse(
            text=f"{greeting}You've got <b>{stats.orders_today} orders</b> rolling today with a <b>{stats.delivery_success}%</b> success rate. {stats.active_deliveries} deliveries are currently on the road. {mood}",
            data={
                "orders_today": stats.orders_today,
                "active_deliveries": stats.active_deliveries,
                "processing": stats.processing,
                "delivery_success": f"{stats.delivery_success}%",
                "revenue_today": f"${stats.revenue_today:,.0f}",
                "active_alerts": len(bootstrap.alerts),
            },
        )

    # Risk / Bottleneck queries
    if any(keyword in lower_query for keyword in ("risk", "bottleneck", "delay", "alert", "problem", "issue", "warning")):
        top_alert = bootstrap.alerts[0] if bootstrap.alerts else None
        if top_alert:
            text = f"Heads up! I spotted something worth watching: <b>{top_alert.title}</b>. Don't worry though, I've got a recommendation ready for you below!"
        else:
            text = "Awesome news! I've scanned everything and there are <b>no major issues</b> right now. Your operations are running smoothly!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "active_alerts": len(bootstrap.alerts),
                "highest_risk": top_alert.title if top_alert else "None - All Clear!",
                "affected_hub": top_alert.location if top_alert else "Network-wide stable",
                "recommendation": top_alert.recommendation if top_alert else "Keep up the great work!",
            },
        )

    # Driver queries
    if any(keyword in lower_query for keyword in ("driver", "drivers", "delivery personnel", "delivery staff")):
        active_drivers = [d for d in bootstrap.drivers if d.status == "active"]
        idle_drivers = [d for d in bootstrap.drivers if d.status == "idle"]
        issues = [d for d in bootstrap.drivers if d.status in ("breakdown", "deviation")]
        total = len(bootstrap.drivers)
        if total == 0:
            text = "Hmm, looks like we don't have any drivers registered yet. Want me to help you set some up?"
        elif len(issues) == 0:
            text = f"Your driver team is looking great! <b>{len(active_drivers)}</b> drivers are active and crushing it out there, with <b>{len(idle_drivers)}</b> ready for their next assignment."
        else:
            text = f"Quick driver update: <b>{len(active_drivers)}</b> are active, <b>{len(idle_drivers)}</b> are standing by, and <b>{len(issues)}</b> need some attention. Let's take care of those!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_drivers": total,
                "active": len(active_drivers),
                "idle": len(idle_drivers),
                "breakdown_deviation": len(issues),
                "avg_efficiency": f"{sum(d.efficiency_score for d in bootstrap.drivers) / max(total, 1):.0f}%" if bootstrap.drivers else "N/A",
            },
        )

    # Vehicle / Fleet queries
    if any(keyword in lower_query for keyword in ("vehicle", "vehicles", "fleet", "truck", "van", "maintenance")):
        active_vehicles = [v for v in bootstrap.vehicles if v.status == "Active"]
        in_shop = [v for v in bootstrap.vehicles if v.status == "In Shop"]
        scheduled = [v for v in bootstrap.vehicles if v.status == "Scheduled"]
        total = len(bootstrap.vehicles)
        if total == 0:
            text = "No vehicles in the system yet! Ready to add your first one?"
        elif len(in_shop) == 0 and len(scheduled) == 0:
            text = f"Your fleet is in top shape! All <b>{len(active_vehicles)} vehicles</b> are active and ready to roll. Nice work keeping them maintained!"
        else:
            text = f"Fleet check complete! <b>{len(active_vehicles)}</b> vehicles are road-ready, <b>{len(in_shop)}</b> are getting some TLC in the shop, and <b>{len(scheduled)}</b> have upcoming service."
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_vehicles": total,
                "active": len(active_vehicles),
                "in_maintenance": len(in_shop),
                "scheduled_service": len(scheduled),
                "vehicle_types": list(set(v.vehicle_type for v in bootstrap.vehicles)) if bootstrap.vehicles else [],
            },
        )

    # Order / Delivery queries
    if any(keyword in lower_query for keyword in ("order", "orders", "delivery", "deliveries", "shipment", "shipping")):
        stats = bootstrap.dashboard_stats
        mood = "Fantastic pace!" if stats.delivery_success >= 95 else ("Solid numbers!" if stats.delivery_success >= 85 else "Let's push for more!")
        return LogisticsAiQueryResponse(
            text=f"Here's your delivery pulse: <b>{stats.orders_today} orders</b> today with <b>{stats.active_deliveries}</b> packages en route. Success rate sitting at <b>{stats.delivery_success}%</b>. {mood}",
            data={
                "orders_today": stats.orders_today,
                "in_transit": stats.active_deliveries,
                "processing": stats.processing,
                "success_rate": f"{stats.delivery_success}%",
                "orders_trend": f"{'+' if stats.orders_trend > 0 else ''}{stats.orders_trend}%",
            },
        )

    # Returns / RMA queries
    if any(keyword in lower_query for keyword in ("return", "returns", "rma", "refund", "damaged")):
        pending_returns = [r for r in bootstrap.returns if r.status.lower() == "pending"]
        approved_returns = [r for r in bootstrap.returns if r.status.lower() == "approved"]
        total_refunds = sum(r.refund_amount for r in bootstrap.returns if r.refund_amount)
        if len(bootstrap.returns) == 0:
            text = "No returns to worry about right now! That's a good sign - customers are happy!"
        elif len(pending_returns) == 0:
            text = f"Returns are all caught up! <b>{len(approved_returns)}</b> cases have been processed. Great job staying on top of things!"
        else:
            text = f"RMA update: You've got <b>{len(pending_returns)}</b> returns waiting for your review out of <b>{len(bootstrap.returns)}</b> total. Let's get those taken care of!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_returns": len(bootstrap.returns),
                "pending_review": len(pending_returns),
                "approved": len(approved_returns),
                "total_refunds": f"${total_refunds:,.0f}",
            },
        )

    # Revenue / Finance queries
    if any(keyword in lower_query for keyword in ("revenue", "forecast", "financial", "finance", "money", "cash", "payment", "cod", "payroll")):
        revenue = bootstrap.finance_summary.get('total_revenue', 0)
        expenses = bootstrap.finance_summary.get('total_expenses', 0)
        net = revenue - expenses
        mood = "Looking profitable!" if net > 0 else "Let's work on improving those margins!"
        return LogisticsAiQueryResponse(
            text=f"Here's your financial snapshot! Revenue at <b>₹{revenue:,.0f}</b> with expenses of <b>₹{expenses:,.0f}</b>. Net position: <b>₹{net:,.0f}</b>. {mood}",
            data={
                "total_revenue": f"₹{revenue:,.0f}",
                "total_expenses": f"₹{expenses:,.0f}",
                "pending_cod": f"₹{bootstrap.finance_summary.get('pending_cod', 0):,.0f}",
                "payroll_due": f"₹{bootstrap.finance_summary.get('total_payroll_due', 0):,.0f}",
                "net_position": f"₹{net:,.0f}",
            },
        )

    # Hub / Warehouse queries
    if any(keyword in lower_query for keyword in ("hub", "hubs", "warehouse", "warehouses", "underperform", "efficiency")):
        if bootstrap.hubs:
            best_hub = max(bootstrap.hubs, key=lambda h: h.efficiency)
            worst_hub = min(bootstrap.hubs, key=lambda h: h.efficiency)
            return LogisticsAiQueryResponse(
                text=f"Hub performance check! Your star performer is <b>{best_hub.name}</b> crushing it at <b>{best_hub.efficiency}%</b> efficiency! <b>{worst_hub.name}</b> could use some love - sitting at {worst_hub.efficiency}%. Want me to dig deeper?",
                data={
                    "total_hubs": len(bootstrap.hubs),
                    "best_hub": best_hub.name,
                    "best_efficiency": f"{best_hub.efficiency}%",
                    "needs_attention": worst_hub.name,
                    "lowest_efficiency": f"{worst_hub.efficiency}%",
                },
            )
        return LogisticsAiQueryResponse(
            text="No hubs set up yet! Let's get your first warehouse configured to start tracking performance.",
            data={"total_hubs": 0},
        )

    # Inventory / Stock queries
    if any(keyword in lower_query for keyword in ("stock", "inventory", "supplies", "materials", "packing")):
        low_items = [item for item in bootstrap.inventory if "Low" in item.get("status", "")]
        total = len(bootstrap.inventory)
        if total == 0:
            text = "No inventory items tracked yet. Ready to add some supplies to monitor?"
        elif len(low_items) == 0:
            text = f"Inventory looking healthy! All <b>{total} items</b> are well-stocked. No reorders needed right now!"
        else:
            text = f"Heads up! <b>{len(low_items)} items</b> are running low and need restocking soon. I've listed the top ones below so you can take action!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_items": total,
                "low_stock_count": len(low_items),
                "low_stock_items": [item["name"] for item in low_items[:5]] if low_items else ["All stocked up!"],
                "status": "Action Required" if low_items else "All Good!",
            },
        )

    # Staff / Team queries
    if any(keyword in lower_query for keyword in ("staff", "team", "employee", "user", "workforce", "labor", "labourer")):
        users_by_role = {}
        for user in bootstrap.users:
            role = user.get("role", "Unknown")
            users_by_role[role] = users_by_role.get(role, 0) + 1
        total = len(bootstrap.users)
        active = len([u for u in bootstrap.users if u.get("is_active", True)])
        if total == 0:
            text = "No team members registered yet. Time to build your dream team!"
        else:
            text = f"Team check! You've got <b>{total} awesome people</b> on board, with <b>{active}</b> currently active. Here's the breakdown by role:"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_staff": total,
                "by_role": users_by_role if users_by_role else {"No roles": 0},
                "active": active,
            },
        )

    # Task queries
    if any(keyword in lower_query for keyword in ("task", "tasks", "todo", "pending", "action")):
        priority_tasks = [t for t in bootstrap.tasks if t.status == "Priority"]
        done_tasks = [t for t in bootstrap.tasks if t.status == "Done"]
        total = len(bootstrap.tasks)
        if total == 0:
            text = "No tasks on your plate right now! Enjoy the breather, or add something new to stay productive."
        elif len(priority_tasks) == 0:
            text = f"You're on top of things! <b>{len(done_tasks)}</b> tasks completed. No urgent items waiting!"
        else:
            text = f"Quick task update: <b>{len(priority_tasks)} priority items</b> need your attention. I've listed the top ones below - let's knock them out!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_tasks": total,
                "priority": len(priority_tasks),
                "completed": len(done_tasks),
                "priority_items": [t.text for t in priority_tasks[:3]] if priority_tasks else ["All caught up!"],
            },
        )

    # Escalation queries
    if any(keyword in lower_query for keyword in ("escalation", "escalations", "urgent", "critical", "approval")):
        open_escalations = [e for e in bootstrap.escalations if e.status == "OPEN"]
        high_priority = [e for e in open_escalations if e.priority == "High"]
        if len(open_escalations) == 0:
            text = "All clear on escalations! No pending approvals or urgent matters. Your team is handling things well!"
        elif len(high_priority) > 0:
            text = f"Attention needed! <b>{len(high_priority)} high-priority</b> escalations require your review. Let's get these resolved!"
        else:
            text = f"You have <b>{len(open_escalations)} open escalations</b> to review. None are critical, but let's not keep them waiting too long!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_open": len(open_escalations),
                "high_priority": len(high_priority),
                "titles": [e.title for e in open_escalations[:3]] if open_escalations else ["No escalations pending"],
            },
        )

    # Zone queries
    if any(keyword in lower_query for keyword in ("zone", "zones", "area", "coverage", "geofence")):
        active_zones = [z for z in bootstrap.zones if z.status == "Active"]
        alert_zones = [z for z in bootstrap.zones if z.status == "Alert"]
        total = len(bootstrap.zones)
        if total == 0:
            text = "No delivery zones configured yet. Set some up to better organize your coverage areas!"
        elif len(alert_zones) > 0:
            text = f"Zone check: <b>{len(alert_zones)} zones</b> are in alert status - might need some attention. {len(active_zones)} zones running smoothly!"
        else:
            text = f"All <b>{len(active_zones)} delivery zones</b> are active and running perfectly! Great coverage management!"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "total_zones": total,
                "active": len(active_zones),
                "alert_status": len(alert_zones),
                "zone_types": list(set(z.zone_type for z in bootstrap.zones)) if bootstrap.zones else ["None configured"],
            },
        )

    # Notification queries
    if any(keyword in lower_query for keyword in ("notification", "notifications", "message", "unread")):
        unread = [n for n in bootstrap.notifications if not n.read]
        total = len(bootstrap.notifications)
        if total == 0:
            text = "Your notification inbox is empty! All caught up!"
        elif len(unread) == 0:
            text = f"You've read all <b>{total}</b> notifications! Nothing new waiting for you."
        else:
            text = f"You have <b>{len(unread)} unread</b> notifications out of {total} total. Here are the most recent ones:"
        return LogisticsAiQueryResponse(
            text=text,
            data={
                "unread": len(unread),
                "total": total,
                "recent": [n.title for n in bootstrap.notifications[:3]] if bootstrap.notifications else ["No notifications"],
            },
        )

    # Performance / SLA queries
    if any(keyword in lower_query for keyword in ("performance", "sla", "kpi", "metric", "trend")):
        stats = bootstrap.dashboard_stats
        avg_sla = sum(stats.sla_week) / len(stats.sla_week) if stats.sla_week else 0
        mood = "Outstanding work!" if avg_sla >= 95 else ("Solid performance!" if avg_sla >= 85 else "Room for improvement - let's strategize!")
        return LogisticsAiQueryResponse(
            text=f"Performance report: <b>{stats.delivery_success}%</b> delivery success with <b>{avg_sla:.1f}%</b> average SLA compliance this week. {mood}",
            data={
                "delivery_success": f"{stats.delivery_success}%",
                "avg_sla_week": f"{avg_sla:.1f}%",
                "sla_trend": stats.sla_week[-3:] if len(stats.sla_week) >= 3 else stats.sla_week,
                "orders_trend": f"{stats.orders_trend}%",
                "revenue_trend": f"{stats.revenue_trend}%",
            },
        )

    # Help / What can you do queries
    if any(keyword in lower_query for keyword in ("help", "what can you", "capabilities", "features", "how to")):
        return LogisticsAiQueryResponse(
            text="Hey there! I'm your Logistics AI assistant, and I'm here to make your life easier! Just ask me about <b>orders</b>, <b>drivers</b>, <b>vehicles</b>, <b>inventory</b>, <b>finances</b>, <b>returns</b>, or anything else logistics-related. I've got real-time insights ready for you!",
            data={
                "available_topics": [
                    "Dashboard & Overview",
                    "Drivers & Delivery Staff",
                    "Vehicles & Fleet",
                    "Orders & Deliveries",
                    "Returns & RMA",
                    "Finance & Revenue",
                    "Hubs & Warehouses",
                    "Inventory & Stock",
                    "Staff & Workforce",
                    "Tasks & To-dos",
                    "Escalations",
                    "Delivery Zones",
                    "Performance & SLA",
                ],
            },
        )

    # Default response with system overview
    return LogisticsAiQueryResponse(
        text="Hey! I didn't quite catch that, but no worries! Try asking me about <b>dashboard status</b>, <b>driver updates</b>, <b>fleet health</b>, <b>order tracking</b>, <b>inventory levels</b>, or <b>financial overview</b>. I'm here to help you stay on top of your logistics operations!",
        data={
            "active_hubs": len(bootstrap.hubs),
            "active_drivers": len(bootstrap.drivers),
            "total_vehicles": len(bootstrap.vehicles),
            "orders_today": bootstrap.dashboard_stats.orders_today,
            "open_returns": len([r for r in bootstrap.returns if r.status.lower() == "pending"]),
            "open_alerts": len(bootstrap.alerts),
        },
    )
