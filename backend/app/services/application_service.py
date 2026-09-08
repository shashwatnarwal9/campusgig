"""Applying to gigs and moving applications through their statuses."""

import uuid
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import (
    AlreadyApplied,
    ApplicationNotFound,
    CannotApplyToOwnGig,
    GigNotFound,
    GigNotOpen,
    InvalidStatusTransition,
    NotGigOwner,
)
from app.models.application import Application, ApplicationStatus
from app.models.gig import GigState
from app.models.user import User
from app.repositories import application_repo, gig_repo

# Only the gig owner drives these, and only forwards.
ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.APPLIED: {ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED},
    ApplicationStatus.ACCEPTED: {ApplicationStatus.COMPLETED},
    ApplicationStatus.REJECTED: set(),
    ApplicationStatus.COMPLETED: set(),
}


def apply_to_gig(
    db: Session, gig_id: uuid.UUID, applicant: User, message: str | None
) -> Application:
    gig = gig_repo.get(db, gig_id)
    if gig is None:
        raise GigNotFound()
    if gig.poster_id == applicant.id:
        raise CannotApplyToOwnGig()
    if gig.state is not GigState.OPEN:
        raise GigNotOpen()

    try:
        application = application_repo.create(
            db, gig_id=gig.id, applicant_id=applicant.id, message=message
        )
        db.commit()
    except IntegrityError as exc:  # unique(gig_id, applicant_id)
        db.rollback()
        raise AlreadyApplied() from exc

    return application


def list_mine(db: Session, applicant: User) -> list[Application]:
    return application_repo.list_for_applicant(db, applicant.id)


def my_summary(db: Session, applicant: User) -> dict[str, Decimal | int]:
    counts = application_repo.count_by_status(db, applicant.id)
    return {
        "total": sum(counts.values()),
        "applied": counts.get(ApplicationStatus.APPLIED, 0),
        "accepted": counts.get(ApplicationStatus.ACCEPTED, 0),
        "rejected": counts.get(ApplicationStatus.REJECTED, 0),
        "completed": counts.get(ApplicationStatus.COMPLETED, 0),
        # Budget of completed work. No payment has actually moved: there is no
        # escrow or ledger in this release, and the UI says so.
        "earned": application_repo.sum_budget_by_status(
            db, applicant.id, ApplicationStatus.COMPLETED
        ),
        "in_progress_value": application_repo.sum_budget_by_status(
            db, applicant.id, ApplicationStatus.ACCEPTED
        ),
    }


def list_for_my_gig(db: Session, gig_id: uuid.UUID, owner: User) -> list[Application]:
    gig = gig_repo.get(db, gig_id)
    if gig is None:
        raise GigNotFound()
    if gig.poster_id != owner.id:
        raise NotGigOwner()
    return application_repo.list_for_gig(db, gig.id)


def set_status(
    db: Session, application_id: uuid.UUID, owner: User, new_status: ApplicationStatus
) -> Application:
    application = application_repo.get(db, application_id)
    if application is None:
        raise ApplicationNotFound()

    if application.gig.poster_id != owner.id:
        raise NotGigOwner()

    if new_status not in ALLOWED_TRANSITIONS[application.status]:
        raise InvalidStatusTransition(
            f"An application cannot go from {application.status} to {new_status}."
        )

    application.status = new_status

    if new_status is ApplicationStatus.ACCEPTED:
        # The gig is spoken for: stop listing it and turn away everyone else.
        application.gig.state = GigState.CLOSED
        application_repo.reject_other_pending(db, application.gig_id, application.id)

    db.commit()
    return application
