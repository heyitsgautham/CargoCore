import pytest
from pydantic import ValidationError

from app.schemas.ai import SupportSettings


def _valid_payload() -> dict:
    return {
        "tone": "Professional and empathetic",
        "language_mode": "English",
        "sentiment_threshold": 75,
        "refund_limit_inr": 12000,
        "system_prompt": "You are the support assistant. Keep responses concise, accurate, and action oriented.",
        "autonomous_replies": True,
        "legal_threat_detection": True,
        "real_time_sentiment_analysis": True,
        "proactive_human_handover": False,
    }


def test_support_settings_accepts_valid_payload() -> None:
    model = SupportSettings(**_valid_payload())
    assert model.sentiment_threshold == 75
    assert model.refund_limit_inr == 12000


def test_support_settings_rejects_invalid_threshold() -> None:
    payload = _valid_payload()
    payload["sentiment_threshold"] = 101
    with pytest.raises(ValidationError):
        SupportSettings(**payload)


def test_support_settings_rejects_short_system_prompt() -> None:
    payload = _valid_payload()
    payload["system_prompt"] = "Too short"
    with pytest.raises(ValidationError):
        SupportSettings(**payload)
