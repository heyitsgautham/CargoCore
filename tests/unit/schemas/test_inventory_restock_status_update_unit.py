import pytest
from pydantic import ValidationError

from app.schemas.inventory import RestockRequestStatusUpdate


def test_restock_status_update_accepts_approved() -> None:
    model = RestockRequestStatusUpdate(status="APPROVED")
    assert model.status == "APPROVED"


def test_restock_status_update_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        RestockRequestStatusUpdate(status="PENDING")
