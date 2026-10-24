"""Analytics range buckets, number formatting, trend wording, insights and sentiment labels."""

import re
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.schemas.ai import (
    SupportAnalyticsInsight,
)
from app.services.support.common import (
    ANALYTICS_RANGES,
    NEGATIVE_KEYWORDS,
    POSITIVE_KEYWORDS,
)
from app.utils.gemini import GEMINI_FLASH_MODEL, get_gemini_client


def _normalize_analytics_range(value: str | None) -> str:
    normalized = (value or "7D").strip().upper()
    if normalized not in ANALYTICS_RANGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analytics range must be one of: 24H, 7D, 30D, 90D",
        )
    return normalized


def _analytics_bucket_starts(range_name: str, now: datetime) -> list[datetime]:
    current = now.astimezone(UTC)
    if range_name == "24H":
        end = current.replace(minute=0, second=0, microsecond=0)
        return [end - timedelta(hours=index) for index in range(23, -1, -1)]
    if range_name == "7D":
        end = current.replace(hour=0, minute=0, second=0, microsecond=0)
        return [end - timedelta(days=index) for index in range(6, -1, -1)]
    if range_name == "30D":
        end = current.replace(hour=0, minute=0, second=0, microsecond=0)
        return [end - timedelta(days=index) for index in range(29, -1, -1)]

    week_start = (current - timedelta(days=current.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return [week_start - timedelta(weeks=index) for index in range(12, -1, -1)]


def _next_analytics_window_start(range_name: str, bucket_start: datetime) -> datetime:
    if range_name == "24H":
        return bucket_start + timedelta(hours=1)
    if range_name in {"7D", "30D"}:
        return bucket_start + timedelta(days=1)
    return bucket_start + timedelta(weeks=1)


def _analytics_label(range_name: str, bucket_start: datetime) -> str:
    if range_name == "24H":
        return bucket_start.strftime("%H:%M")
    if range_name == "7D":
        return bucket_start.strftime("%a")
    return bucket_start.strftime("%d %b")


def _bucket_for_datetime(value: datetime, range_name: str) -> datetime:
    current = value.astimezone(UTC)
    if range_name == "24H":
        return current.replace(minute=0, second=0, microsecond=0)
    if range_name in {"7D", "30D"}:
        return current.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = current - timedelta(days=current.weekday())
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)


def _percent_delta(current: float, previous: float) -> float:
    if previous <= 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100


def _format_count(value: float) -> str:
    return f"{int(round(value)):,}"


def _format_currency(value: float) -> str:
    if value >= 1000:
        return f"₹{value / 1000:.1f}k"
    return f"₹{value:.0f}"


def _format_duration_seconds(value: float) -> str:
    if value <= 0:
        return "0s"
    if value >= 60:
        return f"{int(round(value / 60))}m"
    return f"{int(round(value))}s"


def _trend_descriptor(
    current: float,
    previous: float,
    previous_label: str,
    *,
    formatter,
    inverse: bool = False,
) -> tuple[str, str]:
    delta = current - previous
    if abs(delta) < 0.01:
        return (f"Flat vs previous {previous_label}", "neutral")

    improved = delta < 0 if inverse else delta > 0
    if previous > 0 and not inverse:
        magnitude = abs(_percent_delta(current, previous))
        message = f"{'+' if improved else '-'}{magnitude:.1f}% vs previous {previous_label}"
    else:
        message = f"{'-' if delta < 0 else '+'}{formatter(abs(delta))} vs previous {previous_label}"
    return (message, "positive" if improved else "negative")


def _escalation_reason_label(reason: str | None) -> str:
    normalized = (reason or "").lower()
    if any(keyword in normalized for keyword in ("refund", "billing", "charge", "payment")):
        return "Refund Dispute"
    if any(keyword in normalized for keyword in ("delay", "late", "delivery", "tracking", "shipment")):
        return "Late Delivery"
    if any(keyword in normalized for keyword in ("damage", "damaged", "broken", "missing")):
        return "Damaged Item"
    if any(keyword in normalized for keyword in ("driver", "rude", "conduct", "behavior", "behaviour")):
        return "Driver Conduct"
    return "Other"


def _analytics_ticket_marker(insight_id: str) -> str:
    return f"[analytics:{insight_id}]"


def _extract_analytics_ticket_marker(notes: str | None) -> str | None:
    match = re.search(r"\[analytics:([a-z0-9_-]+)\]", notes or "", flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


def _build_analytics_insights(
    *,
    top_reason_label: str,
    top_reason_pct: int,
    negative_sessions: int,
    total_sessions: int,
    open_contact_forms: int,
    urgent_tickets: int,
    under_review_damage_reports: int,
    executed_insight_ids: set[str],
) -> list[SupportAnalyticsInsight]:
    insights: list[SupportAnalyticsInsight] = []
    negative_ratio = (negative_sessions / total_sessions) if total_sessions else 0

    if top_reason_label == "Refund Dispute" and top_reason_pct >= 20:
        insights.append(
            SupportAnalyticsInsight(
                id="optimize_refund_playbooks",
                icon="rule_settings",
                title="Optimize Refund Playbooks",
                text=(
                    f"{top_reason_pct}% of escalations in this window were tied to refund disputes."
                    " Queue a support follow-up so the team can tighten refund macros and automation rules."
                ),
                tone="purple",
                action_label="Create Follow-up Ticket",
                executed="optimize_refund_playbooks" in executed_insight_ids,
            )
        )

    if (
        top_reason_label == "Late Delivery"
        or negative_ratio >= 0.3
        or top_reason_pct >= 20
    ):
        insights.append(
            SupportAnalyticsInsight(
                id="stabilize_delivery_comms",
                icon="notifications_active",
                title="Stabilize Delivery Communications",
                text=(
                    f"{negative_sessions} of {total_sessions} recent conversations show negative sentiment,"
                    " and delivery-related escalations remain a leading driver."
                    " Open a logistics follow-up so proactive updates can be improved."
                ),
                tone="blue" if negative_ratio < 0.4 else "red",
                action_label="Open Recovery Ticket",
                executed="stabilize_delivery_comms" in executed_insight_ids,
            )
        )

    if open_contact_forms > 0 or urgent_tickets > 0:
        insights.append(
            SupportAnalyticsInsight(
                id="clear_contact_backlog",
                icon="inbox_customize",
                title="Clear Contact Backlog",
                text=(
                    f"{open_contact_forms} open contact requests and {urgent_tickets} urgent support tickets"
                    " still need attention. Create a queue review task so the team can rebalance work."
                ),
                tone="amber",
                action_label="Create Queue Review Ticket",
                executed="clear_contact_backlog" in executed_insight_ids,
            )
        )

    if under_review_damage_reports > 0:
        insights.append(
            SupportAnalyticsInsight(
                id="fast_track_damage_reviews",
                icon="inventory_2",
                title="Fast-Track Damage Reviews",
                text=(
                    f"{under_review_damage_reports} damage reports are still under review."
                    " Open a dedicated follow-up so support and operations can shorten resolution time."
                ),
                tone="green",
                action_label="Open Damage Review Task",
                executed="fast_track_damage_reviews" in executed_insight_ids,
            )
        )

    if not insights:
        insights.append(
            SupportAnalyticsInsight(
                id="clear_contact_backlog",
                icon="insights",
                title="Maintain Current Support Quality",
                text=(
                    "No major risk spike was detected in this window."
                    " Create a lightweight review ticket if you want the team to document what is working well."
                ),
                tone="blue",
                action_label="Create Review Ticket",
                executed="clear_contact_backlog" in executed_insight_ids,
            )
        )

    deduped: list[SupportAnalyticsInsight] = []
    seen: set[str] = set()
    for insight in insights:
        if insight.id in seen:
            continue
        seen.add(insight.id)
        deduped.append(insight)
    return deduped[:4]


def _keyword_sentiment_label(text: str | None) -> str:
    """Keyword-based fallback — used when Gemini is unavailable."""
    normalized = (text or "").lower()
    negative_hits = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in normalized)
    positive_hits = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in normalized)
    if negative_hits >= 2:
        return "Negative"
    if positive_hits > negative_hits:
        return "Positive"
    return "Neutral"


# Simple in-process cache so repeated polls for the same message text
# don't fire a new Gemini call.  Evicts oldest half when it fills up.
_SENTIMENT_CACHE: dict[str, str] = {}
_SENTIMENT_CACHE_MAX = 500


async def _sentiment_label(text: str | None) -> str:
    """Use Gemini Flash to classify message sentiment as Positive, Neutral, or Negative.

    Falls back to keyword matching if Gemini is unavailable or returns an
    unexpected value.
    """
    if not text or not text.strip():
        return "Neutral"

    cache_key = text[:500]
    if cache_key in _SENTIMENT_CACHE:
        return _SENTIMENT_CACHE[cache_key]

    label = "Neutral"
    try:
        client = get_gemini_client()
        prompt = (
            "Classify the sentiment of this customer support message as exactly one of: "
            "Positive, Neutral, or Negative.\n"
            "Reply with ONLY that single word — no punctuation, no explanation.\n\n"
            f"Message: {text[:300]}"
        )
        response = await client.aio.models.generate_content(
            model=GEMINI_FLASH_MODEL,
            contents=prompt,
        )
        raw = (response.text or "").strip().strip(".").capitalize()
        if raw in ("Positive", "Neutral", "Negative"):
            label = raw
        else:
            label = _keyword_sentiment_label(text)
    except Exception:
        label = _keyword_sentiment_label(text)

    if len(_SENTIMENT_CACHE) >= _SENTIMENT_CACHE_MAX:
        keys = list(_SENTIMENT_CACHE.keys())
        for k in keys[: _SENTIMENT_CACHE_MAX // 2]:
            del _SENTIMENT_CACHE[k]
    _SENTIMENT_CACHE[cache_key] = label
    return label


def _analytics_sentiment_label(text: str | None) -> str:
    """Fast local sentiment for dashboard aggregation.

    The analytics endpoint may score many messages at once, so it should never
    block on an external LLM call just to render charts.
    """
    if not text or not text.strip():
        return "Neutral"

    cache_key = f"analytics:{text[:500]}"
    if cache_key in _SENTIMENT_CACHE:
        return _SENTIMENT_CACHE[cache_key]

    label = _keyword_sentiment_label(text)
    if len(_SENTIMENT_CACHE) >= _SENTIMENT_CACHE_MAX:
        keys = list(_SENTIMENT_CACHE.keys())
        for k in keys[: _SENTIMENT_CACHE_MAX // 2]:
            del _SENTIMENT_CACHE[k]
    _SENTIMENT_CACHE[cache_key] = label
    return label
