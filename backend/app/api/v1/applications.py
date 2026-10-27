import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.models.application import ApplicationStatus
from app.schemas.application import (
    ApplicationStatusUpdate,
    ApplicationSummary,
    MyApplication,
    MyApplications,
)
from app.services import application_service
from app.services.gig_service import MAX_PAGE_SIZE

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/me", response_model=MyApplications)
def my_applications(
    db: DbSession,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 12,
    status: ApplicationStatus | None = None,
):
    """Everything the Applied Gigs page needs in one round trip: the totals and
    the list they describe, so the two can never disagree on screen."""
    items, total, total_pages = application_service.list_mine(
        db, current_user, status=status, page=page, page_size=page_size
    )
    summary = application_service.my_summary(db, current_user)
    return MyApplications(
        summary=ApplicationSummary(**summary),
        items=[MyApplication.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
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
