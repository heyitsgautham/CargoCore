"""
ai.py
AI chatbot endpoints — thin router, all logic in ai_service.
"""
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from google.genai import types as genai_types
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_ro_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.ai import (
    AgentReplyRequest,
    ChatRequest,
    ChatResponse,
    ContactSubmissionCreatePublic,
    ContactSubmissionListResponse,
    ContactSubmissionReplyRequest,
    ContactSubmissionResponse,
    ContactSubmissionUpdate,
    ConversationHistory,
    CustomerHistoryResponse,
    EscalateRequest,
    EscalationDetailListResponse,
    EscalationListResponse,
    EscalationResponse,
    SessionListResponse,
    SupportAnalyticsInsightExecutionResponse,
    SupportAnalyticsResponse,
    SupportDamageReportCreate,
    SupportDamageReportItem,
    SupportDamageReportListResponse,
    SupportDamageReportNotesUpdate,
    SupportDashboardResponse,
    SupportMessageCreate,
    SupportRefundCaseItem,
    SupportRefundCaseListResponse,
    SupportRefundCaseUrgentUpdate,
    SupportSessionDetail,
    SupportSessionEscalateRequest,
    SupportSessionListResponse,
    SupportSettings,
    SupportSettingsResponse,
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.schemas.ai_config import (
    KnowledgeArticleCreate,
    KnowledgeArticleListResponse,
    KnowledgeArticleResponse,
    KnowledgeArticleUpdate,
)
from app.services import ai_service, ai_support_service
from app.utils.gemini import generate_with_fallback

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])
SUPPORT_ROLES = ("LOGISTIC_MANAGER", "AI_AGENT", "AI_SUPPORT", "CUSTOMER_SUPPORT")
SUPPORT_MANAGER_ROLES = ("LOGISTIC_MANAGER",)


# ── Vision Estimator ──────────────────────────────────────────────────────────

_VISION_PROMPT = """
You are a logistics AI that analyzes room/space images for moving estimates.

Analyze the image and return ONLY valid JSON (no markdown, no explanation) in this exact format:
{
  "detected_space": "e.g. Master Bedroom / Living Room",
  "confidence": 92,
  "items": [
    {"name": "Item name", "qty": 1, "fragile": false},
    {"name": "Another item", "qty": 2, "fragile": true}
  ],
  "metrics": {
    "boxes_needed": 12,
    "laborers": 2,
    "bubble_wrap_rolls": 3,
    "heavy_items": 2,
    "estimated_volume_cubic_feet": 95
  },
  "vehicle_recommendation": {
    "type": "tempo",
    "display_name": "Tata Ace / 1.5 Ton Tempo",
    "reason": "Brief reason for vehicle choice"
  },
  "estimated_base_cost_inr": 4500
}

Rules:
- List actual visible furniture/items (beds, wardrobes, TVs, sofas, etc.)
- Mark item as fragile:true if it's glass, electronics, mirrors, crockery etc.
- boxes_needed = estimate based on item volume
- vehicle type must be one of: mini-truck, tempo, lcv, hcv
- estimated_base_cost_inr = rough cost in Indian Rupees (without distance)
- If image is not of a room/space, still return valid JSON but with detected_space: "Unknown / Not a room"
"""


@router.post(
    "/estimate-image",
    summary="Analyze a room photo for moving estimate",
    description="Upload an image. Gemini Vision detects items and returns a moving estimate.",
)
async def estimate_image(
    file: UploadFile = File(..., description="Room photo — JPG or PNG, max 15 MB"),
):
    """Analyze a room photo with Gemini Vision and return a moving estimate."""
    # Validate
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, or WebP images are accepted.",
        )

    raw = await file.read()
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be smaller than 15 MB.",
        )

    # Build inline image part using the new SDK
    image_part = genai_types.Part.from_bytes(data=raw, mime_type=file.content_type)
    text_part  = genai_types.Part.from_text(text=_VISION_PROMPT)

    try:
        response = await generate_with_fallback(
            contents=[genai_types.Content(role="user", parts=[image_part, text_part])],
            config=genai_types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        result_text = response.text.strip()
        # Strip markdown fences if model wraps despite mime type setting
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        return json.loads(result_text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an unexpected response. Please try again.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini Vision error: {str(e)}",
        )




@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the AI chatbot",
    description=(
        "Send a natural language message. The AI decides whether to query the "
        "database or respond directly. Pass `session_id` to continue an existing "
        "conversation, or omit it to start a new one."
    ),
)
async def chat(
    data: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    ro_db: Annotated[AsyncSession, Depends(get_ro_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await ai_service.chat(
            db=db,
            ro_db=ro_db,
            user=user,
            session_id=data.session_id,
            user_message=data.message,
            chat_context=data.context,
            order_id=data.order_id,
        )
    except Exception:
        # Safety net — never let an unhandled exception reach the client as 500
        import traceback
        traceback.print_exc()
        return ChatResponse(
            session_id=data.session_id or __import__("uuid").uuid4(),
            message="Sorry, an unexpected error occurred. Please try again.",
            intent="error",
            sql_generated=None,
            linked_order_id=data.order_id,
        )


@router.get(
    "/conversations/{session_id}",
    response_model=ConversationHistory,
    summary="Get conversation history",
    description="Retrieve all messages for a specific conversation session.",
)
async def get_conversation(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    history = await ai_service.get_conversation_history(
        db=db, session_id=session_id, user_id=user.id
    )
    if not history.messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you don't have access to it.",
        )
    return history


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="List chat sessions",
    description="List all conversation sessions for the current user, most recent first.",
)
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await ai_service.get_user_sessions(db=db, user_id=user.id)


@router.post(
    "/escalate/{conversation_id}",
    response_model=EscalationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Escalate conversation to human agent",
    description="Flag a conversation for human review. The conversation must belong to the requesting user.",
)
async def escalate_conversation(
    conversation_id: UUID,
    data: EscalateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await ai_service.escalate_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user.id,
            reason=data.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/escalations",
    response_model=EscalationListResponse,
    summary="List escalations",
    description="Human agent view: list all escalations. Use ?status=OPEN or ?status=RESOLVED to filter.",
)
async def list_escalations(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    status: str | None = Query(default=None, description="Filter by status: OPEN or RESOLVED"),
):
    escalations = await ai_service.list_escalations(db=db, status_filter=status)
    return EscalationListResponse(escalations=escalations)


@router.put(
    "/escalations/{escalation_id}/resolve",
    response_model=EscalationResponse,
    summary="Resolve an escalation",
    description="Mark an escalation as resolved. Restricted to LOGISTIC_MANAGER and AI_AGENT roles.",
)
async def resolve_escalation(
    escalation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    try:
        return await ai_service.resolve_escalation(db=db, escalation_id=escalation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/contact-submissions/public",
    response_model=ContactSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a public contact form",
    description="Public website contact form endpoint used by the Contact page.",
)
async def create_public_contact_submission(
    data: ContactSubmissionCreatePublic,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ai_support_service.create_public_contact_submission(db=db, data=data)


@router.get(
    "/contact-submissions",
    response_model=ContactSubmissionListResponse,
    summary="List support contact submissions",
)
async def list_contact_submissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.list_contact_submissions(db=db)


@router.put(
    "/contact-submissions/{submission_id}",
    response_model=ContactSubmissionResponse,
    summary="Update a support contact submission",
)
async def update_contact_submission(
    submission_id: UUID,
    data: ContactSubmissionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.update_contact_submission(
        db=db,
        submission_id=submission_id,
        data=data,
    )


@router.post(
    "/contact-submissions/{submission_id}/reply",
    response_model=ContactSubmissionResponse,
    summary="Reply to a support contact submission by email",
)
async def reply_to_contact_submission(
    submission_id: UUID,
    data: ContactSubmissionReplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.reply_to_contact_submission(
        db=db,
        submission_id=submission_id,
        data=data,
        actor=user,
    )


@router.delete(
    "/contact-submissions/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a support contact submission",
)
async def delete_contact_submission(
    submission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    await ai_support_service.delete_contact_submission(db=db, submission_id=submission_id)


@router.get(
    "/support/dashboard",
    response_model=SupportDashboardResponse,
    summary="Support dashboard data",
)
async def get_support_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_support_dashboard(db=db)


@router.get(
    "/support/settings",
    response_model=SupportSettingsResponse,
    summary="AI support system settings",
)
async def get_support_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_support_settings(db=db)


@router.put(
    "/support/settings",
    response_model=SupportSettingsResponse,
    summary="Update AI support system settings",
)
async def update_support_settings(
    data: SupportSettings,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.update_support_settings(db=db, user=user, data=data)


@router.get(
    "/support/analytics",
    response_model=SupportAnalyticsResponse,
    summary="Support analytics for the AI analytics dashboard",
)
async def get_support_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    time_range: str = Query(default="7D", alias="range"),
):
    return await ai_support_service.get_support_analytics(db=db, time_range=time_range)


@router.post(
    "/support/analytics/insights/{insight_id}/execute",
    response_model=SupportAnalyticsInsightExecutionResponse,
    summary="Create a follow-up ticket for an analytics insight",
)
async def execute_support_analytics_insight(
    insight_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    time_range: str = Query(default="7D", alias="range"),
):
    return await ai_support_service.execute_support_analytics_insight(
        db=db,
        insight_id=insight_id,
        time_range=time_range,
    )


@router.get(
    "/support/sessions",
    response_model=SupportSessionListResponse,
    summary="List live support sessions for staff",
)
async def list_support_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    search: str | None = Query(default=None),
):
    return await ai_support_service.list_support_sessions(db=db, search=search)


@router.get(
    "/support/sessions/{session_id}",
    response_model=SupportSessionDetail,
    summary="Get staff view of a conversation session",
)
async def get_support_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_support_session_detail(db=db, session_id=session_id)


@router.post(
    "/support/sessions/{session_id}/take-over",
    response_model=SupportSessionDetail,
    summary="Take over a live AI conversation",
)
async def take_over_support_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.take_over_support_session(
        db=db,
        session_id=session_id,
        agent=user,
    )


@router.post(
    "/support/sessions/{session_id}/reply",
    response_model=SupportSessionDetail,
    summary="Send a human agent reply in a live conversation",
)
async def reply_to_support_session(
    session_id: UUID,
    data: AgentReplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.reply_to_support_session(
        db=db,
        session_id=session_id,
        agent=user,
        data=data,
    )


@router.post(
    "/support/sessions/{session_id}/escalate",
    response_model=EscalationResponse,
    summary="Escalate a support session from the live conversation view",
)
async def escalate_support_session(
    session_id: UUID,
    data: SupportSessionEscalateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.escalate_support_session(
        db=db,
        session_id=session_id,
        agent=user,
        data=data,
    )


# ── Escalation Center (enriched) ─────────────────────────────────────────────

@router.get(
    "/escalation-center",
    response_model=EscalationDetailListResponse,
    summary="List enriched escalations for the Escalation Center UI",
)
async def list_escalation_center(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
    status: str | None = Query(default=None, description="OPEN or RESOLVED"),
):
    return await ai_support_service.list_enriched_escalations(db=db, status_filter=status)


@router.put(
    "/escalation-center/{escalation_id}/resolve",
    response_model=EscalationResponse,
    summary="Resolve an escalation from the Escalation Center",
)
async def resolve_escalation_center(
    escalation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    try:
        return await ai_service.resolve_escalation(db=db, escalation_id=escalation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Support Tickets ───────────────────────────────────────────────────────────

@router.get(
    "/tickets",
    response_model=TicketListResponse,
    summary="List all support tickets",
)
async def list_tickets(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.list_tickets(db=db)


@router.get(
    "/recovery-tickets/count",
    summary="Count of open AI-analytics recovery tickets for the Logistics Manager",
)
async def recovery_tickets_count(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_recovery_tickets_count(db=db)


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
)
async def create_ticket(
    data: TicketCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.create_ticket(db=db, data=data, actor=user)


@router.put(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="Update a support ticket",
)
async def update_ticket(
    ticket_id: UUID,
    data: TicketUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.update_ticket(db=db, ticket_id=ticket_id, data=data, actor=user)


@router.post(
    "/tickets/{ticket_id}/reply",
    response_model=TicketResponse,
    summary="Reply to a linked vendor ticket from the support dashboard",
)
async def reply_to_ticket(
    ticket_id: UUID,
    data: AgentReplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.reply_to_ticket(db=db, ticket_id=ticket_id, data=data, actor=user)


@router.delete(
    "/tickets/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a support ticket",
)
async def delete_ticket(
    ticket_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    await ai_support_service.delete_ticket(db=db, ticket_id=ticket_id, actor=user)


# ── AI Support — Reverse Logistics (Damage Reports) ──────────────────────────

@router.get(
    "/support/damage-reports",
    response_model=SupportDamageReportListResponse,
    summary="List all damage reports enriched for AI support staff",
)
async def list_support_damage_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.list_support_damage_reports(db=db)


@router.post(
    "/support/damage-reports",
    response_model=SupportDamageReportItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a damage report on a customer's behalf",
)
async def create_support_damage_report(
    data: SupportDamageReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.create_support_damage_report(db=db, data=data)


@router.put(
    "/support/damage-reports/{report_id}/notes",
    response_model=SupportDamageReportItem,
    summary="Update support notes on a damage report",
)
async def update_damage_report_notes(
    report_id: UUID,
    data: SupportDamageReportNotesUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.update_damage_report_notes(db=db, report_id=report_id, data=data)


@router.post(
    "/support/damage-reports/{report_id}/message",
    response_model=SupportDamageReportItem,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to the customer for a damage report case",
)
async def send_support_message(
    report_id: UUID,
    data: SupportMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.send_support_message(db=db, report_id=report_id, data=data, agent=user)


# ── AI Support — Refund Center ────────────────────────────────────────────────

@router.get(
    "/support/refund-cases",
    response_model=SupportRefundCaseListResponse,
    summary="List return cases with refund info for AI support staff",
)
async def list_support_refund_cases(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.list_support_refund_cases(db=db)


@router.put(
    "/support/refund-cases/{case_id}/urgent",
    response_model=SupportRefundCaseItem,
    summary="Set or clear urgency flag on a return case",
)
async def flag_refund_case_urgent(
    case_id: UUID,
    data: SupportRefundCaseUrgentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.flag_refund_case_urgent(db=db, case_id=case_id, data=data)


# ── AI Support — Customer History ─────────────────────────────────────────────

@router.get(
    "/support/customer-history/{user_id}",
    response_model=CustomerHistoryResponse,
    summary="Get customer history summary for support sidebar",
)
async def get_customer_history(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.get_customer_history(db=db, user_id=user_id)


# ── Knowledge Base CRUD ───────────────────────────────────────────────────────

@router.get(
    "/knowledge-articles",
    response_model=KnowledgeArticleListResponse,
    summary="List all knowledge base articles",
)
async def list_knowledge_articles(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    active_only: bool = Query(True),
    audience: str | None = Query(None),
):
    return await ai_support_service.list_knowledge_articles(
        db=db, active_only=active_only, audience=audience
    )


@router.post(
    "/knowledge-articles",
    response_model=KnowledgeArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge base article",
)
async def create_knowledge_article(
    data: KnowledgeArticleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.create_knowledge_article(db=db, data=data, actor=user)


@router.get(
    "/knowledge-articles/{article_id}",
    response_model=KnowledgeArticleResponse,
    summary="Get a single knowledge base article",
)
async def get_knowledge_article(
    article_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    article = await ai_support_service.get_knowledge_article_by_id(db=db, article_id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.put(
    "/knowledge-articles/{article_id}",
    response_model=KnowledgeArticleResponse,
    summary="Update a knowledge base article",
)
async def update_knowledge_article(
    article_id: str,
    data: KnowledgeArticleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    article = await ai_support_service.update_knowledge_article(
        db=db, article_id=article_id, data=data, actor=user
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.delete(
    "/knowledge-articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a knowledge base article",
)
async def delete_knowledge_article(
    article_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    deleted = await ai_support_service.delete_knowledge_article(db=db, article_id=article_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Article not found")


@router.post(
    "/knowledge-articles/{article_id}/like",
    response_model=KnowledgeArticleResponse,
    summary="Increment the like count on an article",
)
async def like_knowledge_article(
    article_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    article = await ai_support_service.like_knowledge_article(db=db, article_id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
