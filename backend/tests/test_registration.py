import pytest
from sqlalchemy import select

from app.models.user import User, UserRole
from tests.conftest import VALID_PASSWORD, registration_payload

REGISTER = "/api/v1/auth/register"


def error_code(response) -> str:
    return response.json()["detail"]["code"]


def test_valid_thapar_registration(client):
    response = client.post(REGISTER, json=registration_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "student@thapar.edu"
    assert "user_id" in body


def test_registration_does_not_log_the_user_in(client):
    """Signup creates the account and nothing else; the client sends the student
    to the login page."""
    response = client.post(REGISTER, json=registration_payload())
    assert "set-cookie" not in response.headers
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize(
    "email",
    [
        "student@gmail.com",
        "student@thapar.ac.in",
        "student@thapar.edu.fake.com",
        "student@fakethapar.edu",
        "student@sub.thapar.edu",
        "student@thapar.edu.in",
    ],
)
def test_non_institutional_domains_are_rejected(client, email):
    response = client.post(REGISTER, json=registration_payload(email=email))
    assert response.status_code == 400
    assert error_code(response) == "email_domain_not_allowed"


@pytest.mark.parametrize(
    "email", ["Student@Thapar.Edu", "STUDENT@THAPAR.EDU", "  student@thapar.edu  "]
)
def test_domain_check_is_case_insensitive_and_trims(client, email, db):
    response = client.post(REGISTER, json=registration_payload(email=email))
    assert response.status_code == 201
    assert db.scalar(select(User.email)) == "student@thapar.edu"


def test_duplicate_email_is_rejected(client, register_user):
    register_user()
    response = client.post(REGISTER, json=registration_payload(roll_no="102103111"))
    assert response.status_code == 409
    assert error_code(response) == "email_already_registered"


def test_duplicate_email_differing_only_by_case_is_rejected(client, register_user):
    register_user()
    response = client.post(
        REGISTER, json=registration_payload(email="STUDENT@thapar.edu", roll_no="102103112")
    )
    assert response.status_code == 409
    assert error_code(response) == "email_already_registered"


def test_duplicate_roll_no_is_rejected(client, register_user):
    register_user()
    response = client.post(REGISTER, json=registration_payload(email="other@thapar.edu"))
    assert response.status_code == 409
    assert error_code(response) == "roll_no_already_registered"


@pytest.mark.parametrize("password", ["short1", "alllettersonly", "12345678", "nodigitshere", ""])
def test_weak_passwords_are_rejected(client, password):
    response = client.post(REGISTER, json=registration_payload(password=password))
    assert response.status_code == 422
    assert error_code(response) == "validation_error"


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"batch": 1200},
        {"batch": "not-a-number"},
        {"dept": ""},
        {"roll_no": "x"},
    ],
)
def test_invalid_registration_data_is_rejected(client, overrides):
    response = client.post(REGISTER, json=registration_payload(**overrides))
    assert response.status_code == 422


def test_password_is_hashed_never_stored_plaintext(client, register_user, db):
    register_user()
    user = db.scalar(select(User))
    assert user.password_hash != VALID_PASSWORD
    assert VALID_PASSWORD not in user.password_hash
    assert user.password_hash.startswith("$2b$")


def test_registration_response_never_leaks_secrets(client):
    body = client.post(REGISTER, json=registration_payload()).text
    assert VALID_PASSWORD not in body
    assert "password" not in body.lower()
    assert "hash" not in body.lower()


def test_registration_always_creates_a_student(client, register_user, db):
    register_user()
    assert db.scalar(select(User.role)) is UserRole.STUDENT


def test_role_cannot_be_injected_through_the_payload(client, db):
    response = client.post(REGISTER, json={**registration_payload(), "role": "ADMIN"})
    assert response.status_code == 201
    assert db.scalar(select(User.role)) is UserRole.STUDENT


def test_registered_user_can_log_in_immediately(client, register_user):
    payload = register_user()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200
