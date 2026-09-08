import hashlib

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import DEFAULT_AUTH_SECRET, Settings
from app.core.security import hash_password
from app.models.user import User, UserRole


def test_app_starts_and_health_responds(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_health(client):
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_openapi_document_builds(client):
    assert client.get("/openapi.json").status_code == 200


def _user(db, **overrides) -> User:
    fields = {
        "email": "model.test@thapar.edu",
        "password_hash": hash_password("CampusGig123"),
        "roll_no": "102100001",
        "dept": "Computer Science",
        "batch": 2026,
    }
    fields.update(overrides)
    user = User(**fields)
    db.add(user)
    db.commit()
    return user


def test_user_defaults(db):
    user = _user(db)
    db.refresh(user)
    assert user.id is not None
    assert user.role is UserRole.STUDENT
    assert user.failed_login_attempts == 0
    assert user.created_at is not None


def test_email_hash_is_generated_by_the_database(db):
    user = _user(db, email="Hash.Check@thapar.edu")
    db.refresh(user)
    expected = hashlib.sha256(b"hash.check@thapar.edu").hexdigest()
    assert user.email_hash == expected


def test_duplicate_email_is_rejected_case_insensitively(db):
    _user(db)
    with pytest.raises(IntegrityError):
        _user(db, email="MODEL.TEST@thapar.edu", roll_no="102100002")
    db.rollback()


def test_duplicate_roll_no_is_rejected(db):
    _user(db)
    with pytest.raises(IntegrityError):
        _user(db, email="other@thapar.edu")
    db.rollback()


def test_batch_check_constraint(db):
    with pytest.raises(IntegrityError):
        _user(db, batch=1234, roll_no="102100003", email="batch@thapar.edu")
    db.rollback()


def test_production_refuses_default_auth_secret():
    with pytest.raises(ValueError, match="AUTH_SECRET"):
        Settings(
            environment="production",
            auth_secret=DEFAULT_AUTH_SECRET,
            _env_file=None,
        )
