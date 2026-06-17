import pytest
from pydantic import ValidationError

from app.schemas.ai import ChatRequest


def test_chat_request_accepts_valid_message() -> None:
    model = ChatRequest(message="Hello chatbot")
    assert model.message == "Hello chatbot"
    assert model.session_id is None


def test_chat_request_rejects_empty_message() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(message="")
