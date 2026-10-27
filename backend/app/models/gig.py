import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.user import User


class GigCategory(enum.StrEnum):
    ACADEMIC_HELP = "ACADEMIC_HELP"
    DESIGN = "DESIGN"
    DEVELOPMENT = "DEVELOPMENT"
    WRITING = "WRITING"
    TUTORING = "TUTORING"
    EVENTS = "EVENTS"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    OTHER = "OTHER"


class GigState(enum.StrEnum):
    """Milestone 1 only browses OPEN gigs. CLOSED exists so the listing filter is
    provably doing something; the richer lifecycle arrives with contracts."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Gig(Base, TimestampMixin):
    __tablename__ = "gigs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    poster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[GigCategory] = mapped_column(
        Enum(GigCategory, name="gig_category"), nullable=False
    )
    budget: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Expected effort, distinct from the deadline: "two days of work, due in three weeks".
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[GigState] = mapped_column(
        Enum(GigState, name="gig_state"), nullable=False, server_default=GigState.OPEN.value
    )

    poster: Mapped[User] = relationship(User, lazy="joined")

    @property
    def short_description(self) -> str:
        """Card-sized excerpt. Derived here so the API schema can read it straight
        off the ORM object instead of every caller re-truncating."""
        collapsed = " ".join(self.description.split())
        return collapsed if len(collapsed) <= 160 else collapsed[:157].rstrip() + "..."

    __table_args__ = (
        CheckConstraint("char_length(title) BETWEEN 5 AND 200", name="ck_gigs_title_length"),
        CheckConstraint("budget > 0", name="ck_gigs_budget_positive"),
        CheckConstraint(
            "duration_days IS NULL OR duration_days BETWEEN 1 AND 365",
            name="ck_gigs_duration_range",
        ),
        Index("ix_gigs_state_created_at", "state", text("created_at DESC")),
        Index("ix_gigs_category", "category"),
    )
