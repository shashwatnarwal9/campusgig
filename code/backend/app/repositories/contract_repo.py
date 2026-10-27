import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.contract import Contract, ContractStatus, ContractStatusHistory
from app.models.gig import Gig
from app.models.user import User


def get_for_gig(db: Session, gig_id: uuid.UUID) -> Contract | None:
    return db.scalar(select(Contract).where(Contract.gig_id == gig_id))


def get_for_update(db: Session, contract_id: uuid.UUID) -> Contract | None:
    """Lock the contract before its current status is inspected for a transition."""
    return db.scalar(
        select(Contract)
        .where(Contract.id == contract_id)
        .with_for_update(of=Contract)
        .execution_options(populate_existing=True)
    )


def create_history(
    db: Session,
    *,
    contract_id: uuid.UUID,
    previous_status: ContractStatus,
    new_status: ContractStatus,
    actor_id: uuid.UUID,
) -> ContractStatusHistory:
    event = ContractStatusHistory(
        contract_id=contract_id,
        previous_status=previous_status,
        new_status=new_status,
        actor_id=actor_id,
    )
    db.add(event)
    db.flush()
    return event


def _participant_query(participant: User):
    return (
        select(Contract)
        .join(Gig, Contract.gig_id == Gig.id)
        .where(or_(Gig.poster_id == participant.id, Contract.worker_id == participant.id))
    )


def list_for_participant(
    db: Session, participant: User, *, page: int, page_size: int
) -> tuple[list[Contract], int]:
    conditions = or_(Gig.poster_id == participant.id, Contract.worker_id == participant.id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(Contract)
            .join(Gig, Contract.gig_id == Gig.id)
            .where(conditions)
        )
        or 0
    )
    rows = (
        db.scalars(
            _participant_query(participant)
            .order_by(Contract.created_at.desc(), Contract.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .unique()
        .all()
    )
    return list(rows), total


def get_for_participant(db: Session, contract_id: uuid.UUID, participant: User) -> Contract | None:
    return db.scalar(
        _participant_query(participant)
        .where(Contract.id == contract_id)
        .options(
            joinedload(Contract.gig),
            joinedload(Contract.worker),
            selectinload(Contract.history).joinedload(ContractStatusHistory.actor),
        )
    )
