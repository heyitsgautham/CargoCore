import pytest
from pydantic import ValidationError

from app.schemas.logistics import LogisticsAiQueryRequest


def test_logistics_ai_query_accepts_valid_text() -> None:
    model = LogisticsAiQueryRequest(query="Show pending orders")
    assert model.query == "Show pending orders"


def test_logistics_ai_query_rejects_one_character_query() -> None:
    with pytest.raises(ValidationError):
        LogisticsAiQueryRequest(query="a")
