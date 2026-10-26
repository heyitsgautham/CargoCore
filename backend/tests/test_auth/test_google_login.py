"""Signing in and signing up with a Google ID token at POST /api/v1/auth/google-login."""

import pytest

from app.services import auth_google
from tests.conftest import REGISTER_PAYLOAD

URL = "/api/v1/auth/google-login"


@pytest.fixture()
def google_configured(monkeypatch):
    monkeypatch.setattr(auth_google.settings, "google_client_id", "test-client.apps.googleusercontent.com")


def _google_says(monkeypatch, **claims):
    def verify(credential, _request, audience, clock_skew_in_seconds):
        assert audience == "test-client.apps.googleusercontent.com"
        if credential == "bad-token":
            raise ValueError("Token used too late")
        return {"email_verified": True, **claims}

    monkeypatch.setattr(auth_google.id_token, "verify_oauth2_token", verify)


async def test_google_login_is_refused_when_no_client_id_is_set(client, monkeypatch):
    monkeypatch.setattr(auth_google.settings, "google_client_id", "")

    response = await client.post(URL, json={"credential": "anything"})

    assert response.status_code == 503


async def test_an_invalid_google_token_is_rejected(client, google_configured, monkeypatch):
    _google_says(monkeypatch, email="someone@example.com")

    response = await client.post(URL, json={"credential": "bad-token"})

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid Google token")


async def test_an_unverified_google_email_is_rejected(client, google_configured, monkeypatch):
    _google_says(monkeypatch, email="someone@example.com", email_verified=False)

    response = await client.post(URL, json={"credential": "good-token"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Google account email is not verified"


async def test_a_new_google_user_is_signed_up_as_an_individual(client, google_configured, monkeypatch):
    _google_says(monkeypatch, email="new.google.user@example.com", name="New Google User")

    response = await client.post(URL, json={"credential": "good-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "new.google.user@example.com"
    assert body["user"]["role"] == "INDIVIDUAL"


async def test_a_new_google_vendor_waits_for_approval(client, google_configured, monkeypatch):
    _google_says(monkeypatch, email="new.vendor@example.com", name="Vendor Co")

    response = await client.post(URL, json={"credential": "good-token", "role": "VENDOR"})

    assert response.status_code == 403
    assert "must approve it" in response.json()["detail"]


async def test_an_existing_user_signs_in_with_google(client, registered_user_tokens, google_configured, monkeypatch):
    _google_says(monkeypatch, email=REGISTER_PAYLOAD["email"])

    response = await client.post(URL, json={"credential": "good-token"})

    assert response.status_code == 200
    assert response.json()["user"]["email"] == REGISTER_PAYLOAD["email"]


async def test_google_sign_up_cannot_pick_a_staff_role(client, google_configured, monkeypatch):
    _google_says(monkeypatch, email="sneaky@example.com")

    response = await client.post(URL, json={"credential": "good-token", "role": "LOGISTIC_MANAGER"})

    assert response.status_code == 422
