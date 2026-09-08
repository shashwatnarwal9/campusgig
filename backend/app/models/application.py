import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.gig import Gig
from app.models.user import User


class ApplicationStatus(enum.StrEnum):
    APPLIED = "APPLIED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class Application(Base, TimestampMixin):
    """A student's application to work a gig.

    Deliberately not a bid: there is no counter-offer, no price negotiation and
    no contract. Those belong to later milestones.
    """

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    gig_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gigs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
        server_default=ApplicationStatus.APPLIED.value,
    )

    gig: Mapped[Gig] = relationship(Gig, lazy="joined")
    applicant: Mapped[User] = relationship(User, lazy="joined")

    __table_args__ = (
        # One application per person per gig, enforced by the database rather
        # than by a check-then-insert race.
        UniqueConstraint("gig_id", "applicant_id", name="uq_applications_gig_applicant"),
        Index("ix_applications_applicant_status", "applicant_id", "status"),
    )
