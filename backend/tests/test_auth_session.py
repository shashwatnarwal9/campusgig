from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.models.session import UserSession
from app.models.user import User
from tests.conftest import VALID_PASSWORD

LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"
EMAIL = "student@thapar.edu"


def error_code(response) -> str:
    return response.json()["detail"]["code"]


def test_successful_login_sets_an_httponly_cookie(client, register_user, db):
    register_user()
    response = client.post(LOGIN, json={"email": EMAIL, "password": VALID_PASSWORD})
    assert response.status_code == 200

    cookie_header = response.headers["set-cookie"]
    assert settings.session_cookie_name in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header.lower().replace("samesite=lax", "SameSite=lax")
    # the raw token is never persisted, only its hash
    stored = db.scalar(select(UserSession.token_hash))
    assert stored not in cookie_header


def test_login_is_case_insensitive_on_email(client, register_user):
    register_user()
    response = client.post(LOGIN, json={"email": "STUDENT@THAPAR.EDU", "password": VALID_PASSWORD})
    assert response.status_code == 200


def test_incorrect_password_is_rejected(client, register_user):
    register_user()
    response = client.post(LOGIN, json={"email": EMAIL, "password": "WrongPass123"})
    assert response.status_code == 401
    assert error_code(response) == "invalid_credentials"


def test_nonexistent_account_is_indistinguishable_from_a_wrong_password(client, register_user):
    register_user()
    wrong_password = client.post(LOGIN, json={"email": EMAIL, "password": "WrongPass123"})
    unknown_user = client.post(
        LOGIN, json={"email": "ghost@thapar.edu", "password": "WrongPass123"}
    )
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_login_response_never_contains_secrets(client, register_user):
    register_user()
    body = client.post(LOGIN, json={"email": EMAIL, "password": VALID_PASSWORD}).text
    assert "password" not in body.lower()
    assert "hash" not in body.lower()


def test_me_returns_the_authenticated_user(client, logged_in):
    logged_in()
    response = client.get(ME)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == EMAIL
    assert body["role"] == "STUDENT"
    for leaked in ("password_hash", "email_hash", "failed_login_attempts", "locked_until"):
        assert leaked not in body


def test_me_without_authentication_is_401(client):
    response = client.get(ME)
    assert response.status_code == 401
    assert error_code(response) == "not_authenticated"


def test_me_with_a_forged_cookie_is_401(client):
    client.cookies.set(settings.session_cookie_name, "not-a-real-session-token")
    response = client.get(ME)
    assert response.status_code == 401


def test_logout_invalidates_the_session(client, logged_in, db):
    logged_in()
    assert client.get(ME).status_code == 200

    response = client.post(LOGOUT)
    assert response.status_code == 200
    assert db.scalar(select(UserSession)) is None
    assert client.get(ME).status_code == 401


def test_logout_without_a_session_is_harmless(client):
    assert client.post(LOGOUT).status_code == 200


def test_expired_session_is_rejected(client, logged_in, db):
    logged_in()
    session = db.scalar(select(UserSession))
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    assert client.get(ME).status_code == 401


def test_protected_gig_endpoints_require_authentication(client):
    assert client.get("/api/v1/gigs").status_code == 401
    assert (
        client.get("/api/v1/gigs/00000000-0000-0000-0000-000000000000").status_code == 401
    )


def test_repeated_failures_lock_the_account(client, register_user, db):
    register_user()
    for _ in range(settings.login_max_failures):
        failed = client.post(LOGIN, json={"email": EMAIL, "password": "WrongPass123"})
        assert failed.status_code == 401

    locked = client.post(LOGIN, json={"email": EMAIL, "password": VALID_PASSWORD})
    assert locked.status_code == 429
    assert error_code(locked) == "account_locked"

    db.expire_all()
    user = db.scalar(select(User))
    assert user.locked_until is not None


def test_successful_login_resets_the_failure_counter(client, register_user, db):
    register_user()
    client.post(LOGIN, json={"email": EMAIL, "password": "WrongPass123"})
    client.post(LOGIN, json={"email": EMAIL, "password": VALID_PASSWORD})
    db.expire_all()
    user = db.scalar(select(User))
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_sessions_are_per_login_and_independent(client, register_user, db):
    register_user()
    client.post(LOGIN, json={"email": EMAIL, "password": VALID_PASSWORD})
    first_cookie = client.cookies.get(settings.session_cookie_name)
    client.post(LOGIN, json={"email": EMAIL, "password": VALID_PASSWORD})
    second_cookie = client.cookies.get(settings.session_cookie_name)

    assert first_cookie != second_cookie
    assert db.scalar(select(UserSession.id).where(UserSession.token_hash.is_not(None))) is not None

    # logging out of the second session must not revive it
    client.post(LOGOUT)
    assert client.get(ME).status_code == 401
