import pytest
from pydantic import ValidationError

from app.schemas.wallet import WalletPaymentRequest


VALID_CASES = [{'amount': 0.01}, {'amount': 0.1}, {'amount': 1.0}, {'amount': 5.5}, {'amount': 10.0}, {'amount': 100.0}, {'amount': 500.0}, {'amount': 1000.0}]
INVALID_CASES = [{'amount': 0.0}, {'amount': -0.01}, {'amount': -1.0}, {'amount': -5.0}, {'amount': -10.0}, {'amount': -50.0}, {'amount': -100.0}, {'amount': -999.0}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_wallet_payment_request_bulk_unit_valid_bulk(payload) -> None:
    model = WalletPaymentRequest(**payload)
    assert isinstance(model, WalletPaymentRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_wallet_payment_request_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        WalletPaymentRequest(**payload)
