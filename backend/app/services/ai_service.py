"""Core orchestration layer for the AI chatbot.

Handles Gemini interaction, SQL validation and execution, and conversation
persistence with the async `google-genai` client. The code lives in
app/services/ai_chat/, one module per concern, and is re-exported here so the
routers keep a single import path.
"""

from app.services.ai_chat.chat import (
    chat as chat,
)
from app.services.ai_chat.conversations import (
    get_conversation_history as get_conversation_history,
)
from app.services.ai_chat.conversations import (
    get_user_sessions as get_user_sessions,
)
from app.services.ai_chat.escalations import (
    escalate_conversation as escalate_conversation,
)
from app.services.ai_chat.escalations import (
    list_escalations as list_escalations,
)
from app.services.ai_chat.escalations import (
    resolve_escalation as resolve_escalation,
)
