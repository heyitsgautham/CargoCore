"""
test_ai_endpoints.py
Integration tests for the AI chatbot API endpoints.

All Gemini API calls are mocked — no real LLM calls in tests.
Uses the new google-genai SDK patterns (client.aio.models.generate_content).
"""
import uuid
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.ai_conversation import AIConversation
from app.models.escalation import Escalation
from app.models.order import Order
from app.models.support_ticket import SupportTicket
from app.models.user import Role, User
from tests.conftest import REGISTER_PAYLOAD


@contextmanager
def _patch_gemini(**kwargs):
    """Patch the Gemini client everywhere the chat flow builds one."""
    with ExitStack() as stack:
        mocks = [
            stack.enter_context(patch(f"app.services.ai_chat.{module}.get_gemini_client", **kwargs))
            for module in ("chat", "support_handoff")
        ]
        yield mocks[0]

# ── Helpers ───────────────────────────────────────────────────────────────────


def _mock_gemini_text_response(text: str):
    """Create a mock Gemini response that returns plain text (no function call)."""
    response = MagicMock()
    response.function_calls = None  # No function calls
    response.text = text

    # Provide candidate content for multi-turn follow-up
    content = MagicMock()
    content.role = "model"
    content.parts = [MagicMock(text=text)]
    candidate = MagicMock()
    candidate.content = content
    response.candidates = [candidate]
    return response


def _mock_gemini_function_call_response(fn_name: str, args: dict):
    """Create a mock Gemini response that wants to call a function."""
    fc = MagicMock()
    fc.name = fn_name
    fc.args = args

    response = MagicMock()
    response.function_calls = [fc]

    # Candidate content needed for building follow-up contents
    content = MagicMock()
    content.role = "model"
    content.parts = [MagicMock()]
    candidate = MagicMock()
    candidate.content = content
    response.candidates = [candidate]
    return response


def _mock_gemini_client(responses: list):
    """Create a mock Gemini client whose aio.models.generate_content returns
    responses sequentially (async)."""
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(side_effect=responses)
    return client


async def _promote_user_to_role(db_session, email: str, role_name: str) -> User:
    user = (
        await db_session.execute(
            select(User).where(User.email == email)
        )
    ).scalar_one()
    role = (
        await db_session.execute(
            select(Role).where(Role.name == role_name)
        )
    ).scalar_one()
    user.role_id = role.id
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── Test: General (non-DB) queries ────────────────────────────────────────────


@pytest.mark.asyncio
class TestChatGeneral:
    async def test_greeting_returns_text(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """A greeting should get a direct text response, no SQL."""
        token = registered_user_tokens["access_token"]

        text_response = _mock_gemini_text_response("Hello! How can I help you today?")
        mock_client = _mock_gemini_client([text_response])

        with _patch_gemini(return_value=mock_client):
            resp = await client.post(
                "/api/v1/ai/chat",
                json={"message": "Hello!"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Hello! How can I help you today?"
        assert data["intent"] == "greeting"
        assert data["sql_generated"] is None
        assert "session_id" in data

    async def test_general_question(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """A general question should get a direct text response."""
        token = registered_user_tokens["access_token"]

        text_response = _mock_gemini_text_response(
            "Logistics management involves planning, implementing, and controlling the flow of goods."
        )
        mock_client = _mock_gemini_client([text_response])

        with _patch_gemini(return_value=mock_client):
            resp = await client.post(
                "/api/v1/ai/chat",
                json={"message": "What is logistics management?"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "logistics" in data["message"].lower()
        assert data["intent"] == "general"
        assert data["sql_generated"] is None

    async def test_logistics_manager_greeting_is_role_specific(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        await _promote_user_to_role(db_session, REGISTER_PAYLOAD["email"], "LOGISTIC_MANAGER")

        resp = await client.post(
            "/api/v1/ai/chat",
            json={"message": "hi", "context": "logistic_manager"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "greeting"
        assert "hub performance" in data["message"].lower()
        assert "wallet balance" not in data["message"].lower()
        assert "your account" not in data["message"].lower()

    async def test_logistics_manager_help_is_role_specific(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        await _promote_user_to_role(db_session, REGISTER_PAYLOAD["email"], "LOGISTIC_MANAGER")

        resp = await client.post(
            "/api/v1/ai/chat",
            json={"message": "what can you do", "context": "logistic_manager"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "general"
        message = data["message"].lower()
        assert "dashboard overview" in message
        assert "fleet utilization" in message
        assert "your account" not in message


# ── Test: Database queries ────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestChatDatabaseQuery:
    async def test_count_query(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """A data question should trigger function call → SQL → response."""
        token = registered_user_tokens["access_token"]

        # First response: Gemini wants to call execute_sql_query
        fn_call_response = _mock_gemini_function_call_response(
            "execute_sql_query",
            {"sql_query": "SELECT COUNT(*) as total FROM users"},
        )
        # Second response: After receiving query results, Gemini answers
        final_response = _mock_gemini_text_response(
            "There is currently 1 registered user in the system."
        )
        mock_client = _mock_gemini_client([fn_call_response, final_response])

        with _patch_gemini(return_value=mock_client):
            resp = await client.post(
                "/api/v1/ai/chat",
                json={"message": "How many users are registered?"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "db_query"
        assert data["sql_generated"] is not None
        assert "SELECT COUNT" in data["sql_generated"]

    async def test_tracking_code_query_falls_back_without_crashing(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        user = (
            await db_session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()

        db_session.add(
            Order(
                tracking_code="QC-TEST123",
                order_type="INDIVIDUAL",
                status="PENDING",
                customer_id=user.id,
                pickup_addr="Warehouse Alpha",
                delivery_addr="Destination Beta",
            )
        )
        await db_session.commit()

        failing_client = MagicMock()
        failing_client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("quota exceeded")
        )

        with _patch_gemini(return_value=failing_client):
            resp = await client.post(
                "/api/v1/ai/chat",
                json={"message": "QC-TEST123 order status"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "error"
        assert "QC-TEST123" in data["message"]
        assert "Warehouse Alpha" in data["message"]
        assert "Destination Beta" in data["message"]

    async def test_direct_order_status_shortcut_uses_order_addresses(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        user = (
            await db_session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()

        db_session.add(
            Order(
                tracking_code="QC-TEST456",
                order_type="INDIVIDUAL",
                status="ASSIGNED",
                customer_id=user.id,
                pickup_addr="Dock A",
                delivery_addr="Store B",
            )
        )
        await db_session.commit()

        resp = await client.post(
            "/api/v1/ai/chat",
            json={"message": "where is my order"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "db_query"
        assert "Dock A" in data["message"]
        assert "Store B" in data["message"]


# ── Test: SQL validation errors ───────────────────────────────────────────────


@pytest.mark.asyncio
class TestChatSQLValidation:
    async def test_malicious_sql_rejected(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """If Gemini generates a malicious query, it should be rejected."""
        token = registered_user_tokens["access_token"]

        # Gemini tries to DROP TABLE
        fn_call_response = _mock_gemini_function_call_response(
            "execute_sql_query",
            {"sql_query": "DROP TABLE users"},
        )
        # After rejection, Gemini should explain
        error_response = _mock_gemini_text_response(
            "I'm sorry, I was unable to run that query. Could you rephrase?"
        )
        mock_client = _mock_gemini_client([fn_call_response, error_response])

        with _patch_gemini(return_value=mock_client):
            resp = await client.post(
                "/api/v1/ai/chat",
                json={"message": "Drop the users table"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "error"

    async def test_password_hash_query_rejected(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """Queries referencing password_hash should be rejected."""
        token = registered_user_tokens["access_token"]

        fn_call_response = _mock_gemini_function_call_response(
            "execute_sql_query",
            {"sql_query": "SELECT name, password_hash FROM users"},
        )
        error_response = _mock_gemini_text_response(
            "I cannot access password data for security reasons."
        )
        mock_client = _mock_gemini_client([fn_call_response, error_response])

        with _patch_gemini(return_value=mock_client):
            resp = await client.post(
                "/api/v1/ai/chat",
                json={"message": "Show me user passwords"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "error"


# ── Test: Authentication ──────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestChatAuth:
    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        """Chat endpoint requires authentication."""
        resp = await client.post(
            "/api/v1/ai/chat",
            json={"message": "Hello"},
        )
        assert resp.status_code == 401

    async def test_sessions_unauthenticated_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/ai/sessions")
        assert resp.status_code == 401

    async def test_conversation_unauthenticated_returns_401(self, client: AsyncClient):
        session_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/ai/conversations/{session_id}")
        assert resp.status_code == 401


# ── Test: Conversation persistence & retrieval ────────────────────────────────


@pytest.mark.asyncio
class TestConversationPersistence:
    async def test_session_id_returned(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """A new chat should return a session_id."""
        token = registered_user_tokens["access_token"]

        text_response = _mock_gemini_text_response("Hi there!")
        mock_client = _mock_gemini_client([text_response])

        with _patch_gemini(return_value=mock_client):
            resp = await client.post(
                "/api/v1/ai/chat",
                json={"message": "Hi"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] is not None

    async def test_conversation_not_found(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """Requesting a non-existent conversation returns 404."""
        token = registered_user_tokens["access_token"]
        fake_session = uuid.uuid4()
        resp = await client.get(
            f"/api/v1/ai/conversations/{fake_session}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_sessions_empty(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """New user should have no sessions."""
        token = registered_user_tokens["access_token"]
        resp = await client.get(
            "/api/v1/ai/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["sessions"] == []

    async def test_human_handoff_request_creates_open_escalation(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        user = (
            await db_session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()

        resp = await client.post(
            "/api/v1/ai/chat",
            json={"message": "I am not satisfied with the AI reply. Connect me to a human agent."},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["intent"] == "handover"
        assert payload["requires_human"] is True
        assert "human support" in payload["message"].lower()

        messages = (
            await db_session.execute(
                select(AIConversation)
                .where(AIConversation.user_id == user.id)
                .order_by(AIConversation.created_at.asc())
            )
        ).scalars().all()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].intent == "handover"
        assert messages[1].role == "assistant"
        assert messages[1].intent == "handover"

        escalation = (
            await db_session.execute(
                select(Escalation)
                .join(AIConversation, Escalation.conversation_id == AIConversation.id)
                .where(AIConversation.user_id == user.id, Escalation.status == "OPEN")
            )
        ).scalar_one()
        assert "human support" in escalation.reason.lower()

        ticket = (
            await db_session.execute(
                select(SupportTicket).where(
                    SupportTicket.notes.contains(f"[meta:linked_session_id={payload['session_id']}]")
                )
            )
        ).scalar_one()
        assert ticket.status == "new"
        assert "[meta:source=ai_handoff]" in (ticket.notes or "")

    async def test_resolving_ai_handoff_escalation_resolves_linked_ticket(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        user = (
            await db_session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()

        handoff_resp = await client.post(
            "/api/v1/ai/chat",
            json={"message": "Please connect me to a human support agent."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert handoff_resp.status_code == 200
        session_id = handoff_resp.json()["session_id"]

        ai_agent_role = (
            await db_session.execute(select(Role).where(Role.name == "AI_AGENT"))
        ).scalar_one()
        user.role_id = ai_agent_role.id
        await db_session.commit()

        escalation = (
            await db_session.execute(
                select(Escalation)
                .join(AIConversation, Escalation.conversation_id == AIConversation.id)
                .where(AIConversation.session_id == uuid.UUID(session_id))
            )
        ).scalar_one()

        resolve_resp = await client.put(
            f"/api/v1/ai/escalation-center/{escalation.id}/resolve",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resolve_resp.status_code == 200

        ticket = (
            await db_session.execute(
                select(SupportTicket).where(
                    SupportTicket.notes.contains(f"[meta:linked_session_id={session_id}]")
                )
            )
        ).scalar_one()
        assert ticket.status == "resolved"
        assert ticket.resolved_at is not None

    async def test_severe_negative_support_message_creates_escalation_and_ticket(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        user = (
            await db_session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()

        resp = await client.post(
            "/api/v1/ai/chat",
            json={
                "message": "This is terrible service and I am very angry. This is unacceptable.",
                "context": "support_chat",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["intent"] == "handover"
        assert payload["requires_human"] is True
        assert "negative" in payload["human_handoff_reason"].lower()

        escalation = (
            await db_session.execute(
                select(Escalation)
                .join(AIConversation, Escalation.conversation_id == AIConversation.id)
                .where(
                    AIConversation.user_id == user.id,
                    AIConversation.session_id == uuid.UUID(payload["session_id"]),
                    Escalation.status == "OPEN",
                )
            )
        ).scalar_one()
        assert "negative" in escalation.reason.lower()

        ticket = (
            await db_session.execute(
                select(SupportTicket).where(
                    SupportTicket.notes.contains(f"[meta:linked_session_id={payload['session_id']}]")
                )
            )
        ).scalar_one()
        assert ticket.status == "new"
        assert ticket.category == "general"
        assert "[meta:source=ai_handoff]" in (ticket.notes or "")

    async def test_resolving_ai_handoff_ticket_resolves_escalation_and_closes_chat(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        user = (
            await db_session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()

        handoff_resp = await client.post(
            "/api/v1/ai/chat",
            json={"message": "I need human help with this issue."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert handoff_resp.status_code == 200
        session_id = handoff_resp.json()["session_id"]

        ticket = (
            await db_session.execute(
                select(SupportTicket).where(
                    SupportTicket.notes.contains(f"[meta:linked_session_id={session_id}]")
                )
            )
        ).scalar_one()

        ai_agent_role = (
            await db_session.execute(select(Role).where(Role.name == "AI_AGENT"))
        ).scalar_one()
        user.role_id = ai_agent_role.id
        await db_session.commit()

        resolve_resp = await client.put(
            f"/api/v1/ai/tickets/{ticket.id}",
            json={"status": "resolved"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resolve_resp.status_code == 200

        escalation = (
            await db_session.execute(
                select(Escalation)
                .join(AIConversation, Escalation.conversation_id == AIConversation.id)
                .where(AIConversation.session_id == uuid.UUID(session_id))
            )
        ).scalar_one()
        assert escalation.status == "RESOLVED"
        assert escalation.resolved_at is not None

        close_message = (
            await db_session.execute(
                select(AIConversation).where(
                    AIConversation.session_id == uuid.UUID(session_id),
                    AIConversation.intent == "support_session_closed",
                )
            )
        ).scalar_one_or_none()
        assert close_message is not None


# ── Test: Gemini unconfigured ─────────────────────────────────────────────────


@pytest.mark.asyncio
class TestGeminiUnconfigured:
    async def test_returns_error_when_no_api_key(
        self, client: AsyncClient, registered_user_tokens: dict
    ):
        """If Gemini API key is missing, chat should return a helpful error."""
        token = registered_user_tokens["access_token"]

        from app.utils.gemini import GeminiConfigError

        with _patch_gemini(
            side_effect=GeminiConfigError("Gemini API key is not configured."),
        ):
            resp = await client.post(
                "/api/v1/ai/chat",
                json={"message": "Hello"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "error"
        assert "not configured" in data["message"].lower()


@pytest.mark.asyncio
class TestSupportAnalytics:
    async def test_support_analytics_endpoint_returns_dynamic_payload(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        user = (
            await db_session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()
        ai_agent_role = (
            await db_session.execute(select(Role).where(Role.name == "AI_AGENT"))
        ).scalar_one()
        user.role_id = ai_agent_role.id

        now = datetime.now(UTC)

        ai_resolved_session_id = uuid.uuid4()
        escalated_session_id = uuid.uuid4()

        ai_user_message = AIConversation(
            session_id=ai_resolved_session_id,
            user_id=user.id,
            role="user",
            message="Where is my package?",
            created_at=now - timedelta(hours=5),
        )
        ai_reply_message = AIConversation(
            session_id=ai_resolved_session_id,
            user_id=user.id,
            role="assistant",
            message="Your shipment is on time and heading to the delivery zone.",
            intent="general",
            created_at=now - timedelta(hours=4, minutes=55),
        )
        escalated_user_message = AIConversation(
            session_id=escalated_session_id,
            user_id=user.id,
            role="user",
            message="I need a refund because the order is delayed and this is urgent.",
            created_at=now - timedelta(hours=3),
        )
        escalated_reply_message = AIConversation(
            session_id=escalated_session_id,
            user_id=user.id,
            role="assistant",
            message="A human agent is reviewing this delay and refund request.",
            intent="handover",
            author_user_id=user.id,
            created_at=now - timedelta(hours=2, minutes=50),
        )
        db_session.add_all(
            [
                ai_user_message,
                ai_reply_message,
                escalated_user_message,
                escalated_reply_message,
            ]
        )
        await db_session.flush()

        db_session.add(
            Escalation(
                conversation_id=escalated_reply_message.id,
                reason="Refund dispute because of a late delivery",
                status="OPEN",
                escalated_to_user_id=user.id,
                escalated_at=now - timedelta(hours=2, minutes=45),
            )
        )
        await db_session.commit()

        with patch(
            "app.services.ai_support_service.get_gemini_client",
            side_effect=AssertionError("Support analytics should not call Gemini"),
        ):
            resp = await client.get(
                "/api/v1/ai/support/analytics?range=7D",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["range"] == "7D"
        assert len(data["metrics"]) == 4
        assert len(data["resolution_chart"]["labels"]) == 7
        assert len(data["sentiment_chart"]["labels"]) == 7
        assert any(reason["label"] == "Refund Dispute" and reason["count"] == 1 for reason in data["escalation_reasons"])
        assert any(insight["id"] == "optimize_refund_playbooks" for insight in data["insights"])

    async def test_execute_support_analytics_insight_creates_ticket(
        self,
        client: AsyncClient,
        db_session,
        registered_user_tokens: dict,
    ):
        token = registered_user_tokens["access_token"]
        user = (
            await db_session.execute(
                select(User).where(User.email == REGISTER_PAYLOAD["email"])
            )
        ).scalar_one()
        ai_agent_role = (
            await db_session.execute(select(Role).where(Role.name == "AI_AGENT"))
        ).scalar_one()
        user.role_id = ai_agent_role.id

        now = datetime.now(UTC)
        session_id = uuid.uuid4()

        user_message = AIConversation(
            session_id=session_id,
            user_id=user.id,
            role="user",
            message="Need refund help for my delayed shipment.",
            created_at=now - timedelta(hours=4),
        )
        handover_message = AIConversation(
            session_id=session_id,
            user_id=user.id,
            role="assistant",
            message="A support agent will help with this refund delay.",
            intent="handover",
            author_user_id=user.id,
            created_at=now - timedelta(hours=3, minutes=55),
        )
        db_session.add_all([user_message, handover_message])
        await db_session.flush()
        db_session.add(
            Escalation(
                conversation_id=handover_message.id,
                reason="Refund dispute caused by a delayed delivery",
                status="OPEN",
                escalated_to_user_id=user.id,
                escalated_at=now - timedelta(hours=3, minutes=50),
            )
        )
        await db_session.commit()

        analytics_resp = await client.get(
            "/api/v1/ai/support/analytics?range=7D",
            headers={"Authorization": f"Bearer {token}"},
        )
        insight_id = analytics_resp.json()["insights"][0]["id"]

        execute_resp = await client.post(
            f"/api/v1/ai/support/analytics/insights/{insight_id}/execute?range=7D",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert execute_resp.status_code == 200
        payload = execute_resp.json()
        assert payload["insight_id"] == insight_id
        assert payload["ticket_reference_code"].startswith("TK-")

        created_ticket = (
            await db_session.execute(
                select(SupportTicket).where(SupportTicket.reference_code == payload["ticket_reference_code"])
            )
        ).scalar_one()
        assert created_ticket.title
        assert f"[analytics:{insight_id}]" in (created_ticket.notes or "")

        refreshed_analytics = await client.get(
            "/api/v1/ai/support/analytics?range=7D",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert refreshed_analytics.status_code == 200
        refreshed_data = refreshed_analytics.json()
        selected_insight = next(item for item in refreshed_data["insights"] if item["id"] == insight_id)
        assert selected_insight["executed"] is True
