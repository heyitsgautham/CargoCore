from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import auth_headers, make_order, make_user

pytestmark = pytest.mark.asyncio


async def test_rma_chart_counts_orders_per_week(client: AsyncClient, db_session: AsyncSession) -> None:
    """The Reports page plots these four weeks, oldest first, against RMA cases."""
    manager = await make_user(db_session, "LOGISTIC_MANAGER")
    customer = await make_user(db_session, "INDIVIDUAL")
    now = datetime.now(UTC)
    # 3 orders this week, 2 last week, 1 three weeks back, and 1 too old for the chart
    for days_ago in (0, 2, 6, 8, 13, 24, 40):
        await make_order(db_session, customer, created_at=now - timedelta(days=days_ago, hours=1))

    response = await client.get("/api/v1/logistics/bootstrap", headers=auth_headers(manager))

    assert response.status_code == 200
    chart = response.json()["report_metrics"]["rma_vs_orders"]
    assert chart["labels"] == ["Week 1", "Week 2", "Week 3", "Week 4"]
    assert chart["orders"] == [1, 0, 2, 3]
