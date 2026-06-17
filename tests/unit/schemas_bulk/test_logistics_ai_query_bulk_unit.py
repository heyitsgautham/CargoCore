import pytest
from pydantic import ValidationError

from app.schemas.logistics import LogisticsAiQueryRequest


VALID_CASES = [{'query': 'qq'}, {'query': 'qqq'}, {'query': 'qqqqq'}, {'query': 'qqqqqqqqqq'}, {'query': 'qqqqqqqqqqqqqqqqqqqq'}, {'query': 'qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq'}, {'query': 'qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq'}, {'query': 'qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq'}]
INVALID_CASES = [{'query': ''}, {'query': 'a'}, {'query': ' '}, {'query': '\t'}, {'query': '\n'}, {'query': 'x'}, {'query': '?'}, {'query': '1'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_logistics_ai_query_bulk_unit_valid_bulk(payload) -> None:
    model = LogisticsAiQueryRequest(**payload)
    assert isinstance(model, LogisticsAiQueryRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_logistics_ai_query_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        LogisticsAiQueryRequest(**payload)
