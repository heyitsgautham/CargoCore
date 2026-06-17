from __future__ import annotations

from tests.utils import sample_data


def test_make_fake_user_defaults() -> None:
    user = sample_data.make_fake_user()
    assert user.role.name == "LOGISTIC_MANAGER"
    assert user.email == "test.user@example.com"


def test_make_user_profile_dict_shape() -> None:
    profile = sample_data.make_user_profile_dict(role_name="INDIVIDUAL")
    assert profile["role"] == "INDIVIDUAL"
    assert "id" in profile
    assert "created_at" in profile


def test_make_registration_response_pending_approval() -> None:
    payload = sample_data.make_registration_response(pending_approval=True, role_name="VENDOR")
    assert payload["pending_approval"] is True
    assert payload["access_token"] is None
    assert payload["user"]["role"] == "VENDOR"


def test_make_login_response_has_tokens_and_user() -> None:
    payload = sample_data.make_login_response()
    assert payload["token_type"] == "bearer"
    assert "access_token" in payload
    assert "user" in payload


def test_make_order_response_contract_keys() -> None:
    payload = sample_data.make_order_response(status="CONFIRMED")
    assert payload["status"] == "CONFIRMED"
    assert "tracking_code" in payload
    assert isinstance(payload["items"], list)


def test_make_order_list_response_contract_keys() -> None:
    payload = sample_data.make_order_list_response(total=5)
    assert payload["total"] == 5
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert len(payload["items"]) == 1
