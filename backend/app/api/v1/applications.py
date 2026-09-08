import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.application import (
    ApplicationStatusUpdate,
    ApplicationSummary,
    MyApplication,
    MyApplications,
)
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/me", response_model=MyApplications)
def my_applications(db: DbSession, current_user: CurrentUser):
    """Everything the Applied Gigs page needs in one round trip: the totals and
    the list they describe, so the two can never disagree on screen."""
    items = application_service.list_mine(db, current_user)
    summary = application_service.my_summary(db, current_user)
    return MyApplications(
        summary=ApplicationSummary(**summary),
        items=[MyApplication.model_validate(item) for item in items],
    )


@router.patch("/{application_id}", response_model=MyApplication)
def update_status(
    application_id: uuid.UUID,
    payload: ApplicationStatusUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Poster-only. The applicant cannot promote their own application."""
    return application_service.set_status(db, application_id, current_user, payload.status)
