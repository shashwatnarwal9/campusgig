import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.session import UserSession


def create(
    db: Session, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
) -> UserSession:
    session = UserSession(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(session)
    db.flush()
    return session


def get_live(db: Session, token_hash: str, now: datetime) -> UserSession | None:
    return db.scalar(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.expires_at > now,
        )
    )


def delete_by_token_hash(db: Session, token_hash: str) -> int:
    result = db.execute(delete(UserSession).where(UserSession.token_hash == token_hash))
    return result.rowcount or 0


def delete_expired(db: Session, now: datetime) -> int:
    result = db.execute(delete(UserSession).where(UserSession.expires_at <= now))
    return result.rowcount or 0
