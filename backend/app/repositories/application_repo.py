import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.gig import Gig


def create(
    db: Session, *, gig_id: uuid.UUID, applicant_id: uuid.UUID, message: str | None
) -> Application:
    application = Application(gig_id=gig_id, applicant_id=applicant_id, message=message)
    db.add(application)
    db.flush()
    return application


def get(db: Session, application_id: uuid.UUID) -> Application | None:
    return db.get(Application, application_id)


def get_for_gig_and_applicant(
    db: Session, gig_id: uuid.UUID, applicant_id: uuid.UUID
) -> Application | None:
    return db.scalar(
        select(Application).where(
            Application.gig_id == gig_id, Application.applicant_id == applicant_id
        )
    )


def list_for_applicant(
    db: Session, applicant_id: uuid.UUID, *, status: ApplicationStatus | None = None
) -> list[Application]:
    conditions = [Application.applicant_id == applicant_id]
    if status is not None:
        conditions.append(Application.status == status)
    return list(
        db.scalars(
            select(Application).where(*conditions).order_by(Application.created_at.desc())
        )
        .unique()
        .all()
    )


def list_for_gig(db: Session, gig_id: uuid.UUID) -> list[Application]:
    return list(
        db.scalars(
            select(Application)
            .where(Application.gig_id == gig_id)
            .order_by(Application.created_at.asc())
        )
        .unique()
        .all()
    )


def count_by_status(db: Session, applicant_id: uuid.UUID) -> dict[str, int]:
    rows = db.execute(
        select(Application.status, func.count())
        .where(Application.applicant_id == applicant_id)
        .group_by(Application.status)
    ).all()
    return {str(status): count for status, count in rows}


def sum_budget_by_status(
    db: Session, applicant_id: uuid.UUID, status: ApplicationStatus
) -> Decimal:
    """Total gig value for the applicant's applications in a given status.

    This is the budget of work, not money that moved - there is no payment
    system yet, and callers must label it accordingly.
    """
    total = db.scalar(
        select(func.coalesce(func.sum(Gig.budget), 0))
        .select_from(Application)
        .join(Gig, Gig.id == Application.gig_id)
        .where(Application.applicant_id == applicant_id, Application.status == status)
    )
    return Decimal(total or 0)


def reject_other_pending(
    db: Session, gig_id: uuid.UUID, keep_application_id: uuid.UUID
) -> None:
    """Accepting one applicant closes the door on the rest."""
    others = db.scalars(
        select(Application).where(
            Application.gig_id == gig_id,
            Application.id != keep_application_id,
            Application.status == ApplicationStatus.APPLIED,
        )
    ).unique()
    for application in others:
        application.status = ApplicationStatus.REJECTED
