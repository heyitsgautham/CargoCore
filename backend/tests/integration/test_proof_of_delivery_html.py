from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import auth_headers, make_order, make_user

pytestmark = pytest.mark.asyncio

PAYLOAD = '<img src=x onerror="alert(1)">'


async def test_proof_of_delivery_html_escapes_customer_text(client: AsyncClient, db_session: AsyncSession) -> None:
    """Names and addresses are typed by customers, so the POD page must show them as text."""
    customer = await make_user(db_session, "INDIVIDUAL", name=f"Asha {PAYLOAD}")
    order = await make_order(
        db_session,
        customer,
        delivery_addr=f"{PAYLOAD} 12 MG Road, Bengaluru, KA 560001",
        pod_signature='x" onload="alert(2)',
        pod_photos=['y" onerror="alert(3)'],
    )

    response = await client.get(f"/api/v1/orders/{order.id}/proof-of-delivery", headers=auth_headers(customer))

    assert response.status_code == 200
    html = response.text
    assert "<img src=x" not in html
    assert 'onerror="alert' not in html
    assert 'onload="alert' not in html
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in html
