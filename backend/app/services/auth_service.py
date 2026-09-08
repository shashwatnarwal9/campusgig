"""Registration and session business rules.

This module owns the institutional-email rule, the login lockout policy and the
session lifecycle. It knows nothing about HTTP.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import (
    AccountLocked,
    DuplicateEmail,
    DuplicateRollNo,
    EmailDomainNotAllowed,
    InvalidCredentials,
)
from app.core.security import (
    burn_password_cycles,
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.models.user import User
from app.repositories import session_repo, user_repo
from app.schemas.auth import LoginRequest, RegisterRequest


def _now() -> datetime:
    return datetime.now(UTC)


def assert_institutional_email(email: str) -> None:
    """Exact whole-domain match, case-insensitive.

    Suffix matching is not used on purpose: `endswith("thapar.edu")` accepts
    `x@fakethapar.edu`, and no suffix rule rejects `x@thapar.edu.fake.com`.
    Splitting on the last '@' and comparing the entire domain rejects both.

    With email verification removed this check is the only thing keeping
    non-Thapar accounts out, so it stays backend-enforced and authoritative.
    """
    local, separator, domain = email.strip().lower().rpartition("@")
    if not separator or not local or domain != settings.allowed_email_domain:
        raise EmailDomainNotAllowed()


def register(db: Session, data: RegisterRequest) -> User:
    email = data.email.strip().lower()
    assert_institutional_email(email)

    if user_repo.get_by_email(db, email) is not None:
        raise DuplicateEmail()
    if user_repo.get_by_roll_no(db, data.roll_no) is not None:
        raise DuplicateRollNo()

    try:
        user = user_repo.create(
            db,
            email=email,
            password_hash=hash_password(data.password),
            roll_no=data.roll_no,
            dept=data.dept,
            batch=data.batch,
        )
        db.commit()
    except IntegrityError as exc:  # concurrent signup lost the race
        db.rollback()
        constraint = str(getattr(exc.orig, "diag", None) and exc.orig.diag.constraint_name or "")
        if "roll_no" in constraint:
            raise DuplicateRollNo() from exc
        raise DuplicateEmail() from exc

    return user


def _register_failed_login(db: Session, user: User) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.login_max_failures:
        user.locked_until = _now() + timedelta(minutes=settings.login_lockout_minutes)
        user.failed_login_attempts = 0
    db.commit()


def login(db: Session, data: LoginRequest) -> tuple[User, str, datetime]:
    user = user_repo.get_by_email(db, data.email)

    if user is not None and user.locked_until is not None and user.locked_until > _now():
        raise AccountLocked()

    if user is None:
        # Equalise timing so a missing account costs the same as a wrong password.
        burn_password_cycles()
        raise InvalidCredentials()

    if not verify_password(data.password, user.password_hash):
        _register_failed_login(db, user)
        raise InvalidCredentials()

    user.failed_login_attempts = 0
    user.locked_until = None

    token = generate_session_token()
    expires_at = _now() + timedelta(minutes=settings.session_ttl_minutes)
    session_repo.create(
        db, user_id=user.id, token_hash=hash_session_token(token), expires_at=expires_at
    )
    db.commit()
    return user, token, expires_at


def logout(db: Session, token: str | None) -> None:
    if not token:
        return
    session_repo.delete_by_token_hash(db, hash_session_token(token))
    db.commit()


def user_for_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    session = session_repo.get_live(db, hash_session_token(token), _now())
    return session.user if session else None
