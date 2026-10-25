"""The customer support desk over HTTP: contact forms, chat sessions, tickets, damage reports, refunds and the knowledge base."""

from unittest.mock import AsyncMock

import pytest

from app.services.support import contacts as support_contacts

pytestmark = pytest.mark.asyncio

AI = "/api/v1/ai"


async def test_public_contact_form_is_triaged_and_answered(client, world, monkeypatch):
    sent_mail = AsyncMock(return_value=True)
    monkeypatch.setattr(support_contacts, "send_email", sent_mail)
    agent = world.headers("AI_AGENT")
    submitted = await client.post(
        f"{AI}/contact-submissions/public",
        json={
            "name": "Meera",
            "email": "meera@example.com",
            "phone": "9000011111",
            "subject": "Quote for a 2BHK move",
            "category": "sales",
            "priority": "high",
            "message": "Moving from Whitefield to Hebbal next month.",
        },
    )
    assert submitted.status_code in (200, 201), submitted.text
    submission_id = submitted.json()["id"]

    triaged = await client.put(
        f"{AI}/contact-submissions/{submission_id}",
        json={"status": "in_progress", "priority": "urgent", "assigned_to_user_id": str(world.users["AI_AGENT"].id)},
        headers=agent,
    )
    assert triaged.status_code == 200, triaged.text

    bad_status = await client.put(f"{AI}/contact-submissions/{submission_id}", json={"status": "lost"}, headers=agent)
    assert bad_status.status_code in (400, 422)

    replied = await client.post(f"{AI}/contact-submissions/{submission_id}/reply", json={"message": "We will call you today."}, headers=agent)
    assert replied.status_code == 200, replied.text
    assert sent_mail.await_args.args[0] == "meera@example.com"

    listing = await client.get(f"{AI}/contact-submissions", headers=agent)
    assert submission_id in {row["id"] for row in listing.json()["submissions"]}

    removed = await client.delete(f"{AI}/contact-submissions/{submission_id}", headers=agent)
    assert removed.status_code in (200, 204), removed.text


async def test_chat_session_is_taken_over_answered_and_escalated(client, world):
    customer = world.headers("INDIVIDUAL")
    chat = await client.post(
        f"{AI}/chat",
        json={
            "message": f"Where is my order {world.order.tracking_code}?",
            "context": "support_chat",
            "order_id": str(world.order.id),
        },
        headers=customer,
    )
    assert chat.status_code == 200, chat.text
    session_id = chat.json()["session_id"]
    assert chat.json()["linked_order_id"] == str(world.order.id)

    history = await client.get(f"{AI}/conversations/{session_id}", headers=customer)
    assert history.status_code == 200, history.text
    sessions = await client.get(f"{AI}/sessions", headers=customer)
    assert session_id in sessions.text

    agent = world.headers("AI_AGENT")
    listed = await client.get(f"{AI}/support/sessions", headers=agent)
    assert session_id in listed.text
    detail = await client.get(f"{AI}/support/sessions/{session_id}", headers=agent)
    assert detail.status_code == 200, detail.text

    taken = await client.post(f"{AI}/support/sessions/{session_id}/take-over", headers=agent)
    assert taken.status_code == 200, taken.text
    replied = await client.post(f"{AI}/support/sessions/{session_id}/reply", json={"message": "It is out for delivery."}, headers=agent)
    assert replied.status_code == 200, replied.text

    escalated = await client.post(f"{AI}/support/sessions/{session_id}/escalate", json={"reason": "Wants a call back"}, headers=agent)
    assert escalated.status_code == 200, escalated.text

    center = await client.get(f"{AI}/escalation-center", headers=agent)
    assert center.status_code == 200, center.text
    for escalation in center.json()["escalations"][:1]:
        resolved = await client.put(f"{AI}/escalation-center/{escalation['id']}/resolve", headers=agent)
        assert resolved.status_code == 200, resolved.text

    dashboard = await client.get(f"{AI}/support/dashboard", headers=agent)
    assert dashboard.status_code == 200, dashboard.text


async def test_tickets_are_raised_worked_and_closed(client, world):
    agent = world.headers("AI_AGENT")
    created = await client.post(
        f"{AI}/tickets",
        json={"title": "Refund delay", "description": "Customer waiting 5 days", "priority": "high", "category": "billing", "customer_name": "Asha"},
        headers=agent,
    )
    assert created.status_code in (200, 201), created.text
    ticket_id = created.json()["id"]

    worked = await client.put(f"{AI}/tickets/{ticket_id}", json={"status": "in_progress", "notes": "Chasing finance"}, headers=agent)
    assert worked.status_code == 200, worked.text
    # Chat replies only go to tickets linked to a vendor ticket; this one came from the desk.
    replied = await client.post(f"{AI}/tickets/{ticket_id}/reply", json={"message": "Finance approved the refund."}, headers=agent)
    assert replied.status_code == 400
    closed = await client.put(f"{AI}/tickets/{ticket_id}", json={"status": "resolved"}, headers=agent)
    assert closed.json()["status"] == "resolved"

    listing = await client.get(f"{AI}/tickets", headers=agent)
    assert ticket_id in {t["id"] for t in listing.json()["tickets"]}
    count = await client.get(f"{AI}/recovery-tickets/count", headers=world.headers("LOGISTIC_MANAGER"))
    assert count.status_code == 200, count.text

    removed = await client.delete(f"{AI}/tickets/{ticket_id}", headers=agent)
    assert removed.status_code in (200, 204), removed.text


async def test_damage_reports_and_refund_cases(client, world):
    agent = world.headers("AI_AGENT")
    report = await client.post(
        f"{AI}/support/damage-reports",
        json={
            "customer_id": str(world.users["INDIVIDUAL"].id),
            "order_id": str(world.order.id),
            "description": "Mirror cracked in transit",
            "flow_type": "photo_review",
        },
        headers=agent,
    )
    assert report.status_code in (200, 201), report.text
    report_id = report.json()["id"]

    notes = await client.put(f"{AI}/support/damage-reports/{report_id}/notes", json={"support_notes": "Photos look genuine"}, headers=agent)
    assert notes.status_code == 200, notes.text
    message = await client.post(f"{AI}/support/damage-reports/{report_id}/message", json={"text": "We are reviewing it"}, headers=agent)
    assert message.status_code in (200, 201), message.text

    reports = await client.get(f"{AI}/support/damage-reports", headers=agent)
    assert reports.status_code == 200, reports.text

    cases = await client.get(f"{AI}/support/refund-cases", headers=agent)
    assert cases.status_code == 200, cases.text
    for case in cases.json()["cases"][:1]:
        flagged = await client.put(
            f"{AI}/support/refund-cases/{case['id']}/urgent", json={"is_urgent": True, "urgent_reason": "Chargeback threat"}, headers=agent
        )
        assert flagged.status_code == 200, flagged.text

    history = await client.get(f"{AI}/support/customer-history/{world.users['INDIVIDUAL'].id}", headers=agent)
    assert history.status_code == 200, history.text


async def test_settings_analytics_and_knowledge_base(client, world):
    agent = world.headers("AI_AGENT")
    settings = await client.put(
        f"{AI}/support/settings",
        json={
            "tone": "friendly",
            "language_mode": "auto",
            "sentiment_threshold": 30,
            "refund_limit_inr": 2000,
            "system_prompt": "You are CargoCore's support assistant.",
            "autonomous_replies": True,
        },
        headers=agent,
    )
    assert settings.status_code == 200, settings.text
    assert (await client.get(f"{AI}/support/settings", headers=agent)).json()["settings"]["refund_limit_inr"] == 2000

    for time_range in ("24H", "7D", "30D", "90D"):
        analytics = await client.get(f"{AI}/support/analytics?range={time_range}", headers=agent)
        assert analytics.status_code == 200, (time_range, analytics.text)

    article = await client.post(
        f"{AI}/knowledge-articles",
        json={
            "title": "How refunds work",
            "content": "Refunds reach the wallet within 3 working days.",
            "audience": "INDIVIDUAL",
            "keywords": ["refund", "wallet"],
            "category": "Billing",
        },
        headers=agent,
    )
    assert article.status_code in (200, 201), article.text
    article_id = article.json()["id"]

    edited = await client.put(f"{AI}/knowledge-articles/{article_id}", json={"title": "How refunds reach your wallet"}, headers=agent)
    assert edited.status_code == 200, edited.text
    liked = await client.post(f"{AI}/knowledge-articles/{article_id}/like", headers=world.headers("INDIVIDUAL"))
    assert liked.status_code == 200, liked.text

    found = await client.get(f"{AI}/knowledge-articles?audience=INDIVIDUAL", headers=world.headers("INDIVIDUAL"))
    assert article_id in found.text

    removed = await client.delete(f"{AI}/knowledge-articles/{article_id}", headers=agent)
    assert removed.status_code in (200, 204), removed.text


async def test_support_desk_is_closed_to_customers(client, world):
    response = await client.get(f"{AI}/support/dashboard", headers=world.headers("INDIVIDUAL"))
    assert response.status_code == 403
