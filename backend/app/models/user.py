import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    Enum,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UserRole(enum.StrEnum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # CITEXT makes uniqueness case-insensitive at the database level, not just in
    # application code. Values are still normalised to lowercase before insert.
    email: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)
    # The UML's `emailHash`, derived by PostgreSQL so it can never drift from email.
    email_hash: Mapped[str] = mapped_column(
        Text,
        Computed("encode(sha256(lower(email::text)::bytea), 'hex')", persisted=True),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    roll_no: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    dept: Mapped[str] = mapped_column(Text, nullable=False)
    batch: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, server_default=UserRole.STUDENT.value
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Profile. Files live on disk under MEDIA_ROOT; only the relative path is
    # stored so the storage backend can change without a data migration.
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("batch BETWEEN 1900 AND 2100", name="ck_users_batch_range"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User {self.id} roll_no={self.roll_no}>"
