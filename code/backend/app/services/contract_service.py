"""Contract creation and participant read operations.

Milestone 4 creates the awarded contract and audit event. Later lifecycle
triggers that require deliverables, disputes, escrow, or ledger settlement are
left for their dependent milestones and are not exposed as status-only actions.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.errors import ContractAlreadyExists, ContractNotFound, InvalidStatusTransition
from app.models.application import Application, ApplicationStatus
from app.models.contract import Contract, ContractStatus
from app.models.gig import Gig, GigState
from app.models.user import User
from app.repositories import contract_repo
from app.services.gig_service import MAX_PAGE_SIZE


def create_for_award(db: Session, gig: Gig, application: Application, poster: User) -> Contract:
    """Create the frozen agreement and record Figure 3.1 transition 1.

    The caller owns the transaction and commits it together with the accepted
    application, closed gig, and rejected competing applications.
    """
    if (
        gig.poster_id != poster.id
        or application.gig_id != gig.id
        or application.applicant_id == poster.id
        or application.status is not ApplicationStatus.ACCEPTED
        or gig.state is not GigState.OPEN
    ):
        raise InvalidStatusTransition("Only the selected applicant on an open gig can be awarded.")
    if contract_repo.get_for_gig(db, gig.id) is not None:
        raise ContractAlreadyExists()

    contract = Contract(
        gig_id=gig.id,
        application_id=application.id,
        worker_id=application.applicant_id,
        gig_title=gig.title,
        gig_description=gig.description,
        gig_category=gig.category,
        amount_paise=int(gig.budget * 100),
        deadline=gig.deadline,
        duration_days=gig.duration_days,
        status=ContractStatus.OPEN,
    )
    db.add(contract)
    db.flush()

    # Even the award edge takes and refreshes the contract row lock before
    # reading status, matching the locking rule for future lifecycle edges.
    locked = contract_repo.get_for_update(db, contract.id)
    if locked is None or locked.status is not ContractStatus.OPEN:
        raise InvalidStatusTransition("The contract is no longer open for award.")

    previous_status = locked.status
    locked.status = ContractStatus.ACCEPTED
    contract_repo.create_history(
        db,
        contract_id=locked.id,
        previous_status=previous_status,
        new_status=locked.status,
        actor_id=poster.id,
    )
    return locked


def list_for_user(
    db: Session, participant: User, *, page: int = 1, page_size: int = 12
) -> tuple[list[Contract], int, int]:
    page_size = min(page_size, MAX_PAGE_SIZE)
    items, total = contract_repo.list_for_participant(
        db, participant, page=page, page_size=page_size
    )
    return items, total, max(1, -(-total // page_size))


def get_for_user(db: Session, contract_id: uuid.UUID, participant: User) -> Contract:
    contract = contract_repo.get_for_participant(db, contract_id, participant)
    if contract is None:
        raise ContractNotFound()
    return contract
