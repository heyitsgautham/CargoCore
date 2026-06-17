import pytest
from pydantic import ValidationError

from app.schemas.ai import EscalateRequest


def test_escalate_request_accepts_reason() -> None:
    model = EscalateRequest(reason="Need human intervention")
    assert model.reason == "Need human intervention"


def test_escalate_request_rejects_empty_reason() -> None:
    with pytest.raises(ValidationError):
        EscalateRequest(reason="")
