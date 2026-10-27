from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.application import Application
from app.models.gig import Gig, GigCategory
from app.models.user import User


class ContractStatus(enum.StrEnum):
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    DELIVERED = "DELIVERED"
    REVISION = "REVISION"
    DISPUTED = "DISPUTED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    SPLIT = "SPLIT"


class Contract(Base, TimestampMixin):
    """Frozen agreement created as part of a poster's award transaction.

    Poster identity is derived from the gig; the selected application and worker
    are retained explicitly so the agreement can be audited independently.
    """

    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    gig_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gigs.id", ondelete="RESTRICT"), nullable=False
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="RESTRICT"), nullable=False
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    gig_title: Mapped[str] = mapped_column(Text, nullable=False)
    gig_description: Mapped[str] = mapped_column(Text, nullable=False)
    gig_category: Mapped[GigCategory] = mapped_column(
        Enum(GigCategory, name="gig_category", create_type=False), nullable=False
    )
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus, name="contract_status"), nullable=False
    )
    confirmation_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revisions_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    gig: Mapped[Gig] = relationship(Gig, foreign_keys=[gig_id], lazy="joined")
    application: Mapped[Application] = relationship(
        Application, foreign_keys=[application_id], lazy="joined"
    )
    worker: Mapped[User] = relationship(User, foreign_keys=[worker_id], lazy="joined")
    history: Mapped[list[ContractStatusHistory]] = relationship(
        back_populates="contract",
        order_by="(ContractStatusHistory.created_at, ContractStatusHistory.id)",
        lazy="selectin",
    )

    @property
    def poster(self) -> User:
        return self.gig.poster

    @property
    def budget(self) -> Decimal:
        """Snapshot amount represented in rupees for conventional formatters."""
        return Decimal(self.amount_paise) / 100

    __table_args__ = (
        UniqueConstraint("gig_id", name="uq_contracts_gig_id"),
        UniqueConstraint("application_id", name="uq_contracts_application_id"),
        ForeignKeyConstraint(
            ["application_id", "gig_id", "worker_id"],
            ["applications.id", "applications.gig_id", "applications.applicant_id"],
            name="fk_contracts_selected_application",
            ondelete="RESTRICT",
        ),
        CheckConstraint("amount_paise > 0", name="ck_contracts_amount_positive"),
        CheckConstraint("revisions_used >= 0", name="ck_contracts_revisions_nonnegative"),
        CheckConstraint(
            "duration_days IS NULL OR duration_days BETWEEN 1 AND 365",
            name="ck_contracts_duration_range",
        ),
        Index("ix_contracts_worker_created_at", "worker_id", text("created_at DESC")),
    )


class ContractStatusHistory(Base):
    __tablename__ = "contract_status_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus, name="contract_status", create_type=False), nullable=False
    )
    new_status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus, name="contract_status", create_type=False), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    contract: Mapped[Contract] = relationship(back_populates="history")
    actor: Mapped[User] = relationship(User, lazy="joined")

    __table_args__ = (Index("ix_contract_history_contract_created", "contract_id", "created_at"),)
