import pytest
from pydantic import ValidationError

from app.schemas.wallet import WalletPaymentRequest


def test_wallet_payment_request_accepts_positive_amount() -> None:
    model = WalletPaymentRequest(amount=100.5)
    assert model.amount == 100.5


def test_wallet_payment_request_rejects_zero_amount() -> None:
    with pytest.raises(ValidationError):
        WalletPaymentRequest(amount=0)
