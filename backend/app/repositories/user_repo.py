import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    # `email` is CITEXT, so this comparison is case-insensitive in the database.
    return db.scalar(select(User).where(User.email == email))


def get_by_roll_no(db: Session, roll_no: str) -> User | None:
    return db.scalar(select(User).where(User.roll_no == roll_no))


def create(
    db: Session,
    *,
    email: str,
    password_hash: str,
    roll_no: str,
    dept: str,
    batch: int,
) -> User:
    """Always creates a STUDENT. Role is never taken from caller input, so no
    request payload can mint an administrator."""
    user = User(
        email=email,
        password_hash=password_hash,
        roll_no=roll_no,
        dept=dept,
        batch=batch,
        role=UserRole.STUDENT,
    )
    db.add(user)
    db.flush()
    return user
