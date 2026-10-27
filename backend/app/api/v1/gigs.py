import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.gig import GigCategory
from app.schemas.application import ApplicationCreate, GigApplicant, MyApplication
from app.schemas.common import Page
from app.schemas.gig import GigCreate, GigDetail, GigSummary
from app.services import application_service, gig_service

router = APIRouter(prefix="/gigs", tags=["gigs"])


@router.get("", response_model=Page[GigSummary])
def list_gigs(
    db: DbSession,
    _current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=gig_service.MAX_PAGE_SIZE)] = 12,
    q: Annotated[str | None, Query(max_length=100)] = None,
    category: GigCategory | None = None,
    min_budget: Annotated[Decimal | None, Query(ge=0)] = None,
    max_budget: Annotated[Decimal | None, Query(ge=0)] = None,
    deadline_before: datetime | None = None,
    sort: Literal["newest", "deadline", "budget_asc", "budget_desc"] = "newest",
):
    items, total, total_pages = gig_service.list_open_gigs(
        db,
        q=q,
        category=category,
        min_budget=min_budget,
        max_budget=max_budget,
        deadline_before=deadline_before,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return Page[GigSummary](
        items=[GigSummary.model_validate(gig) for gig in items],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=GigDetail, status_code=status.HTTP_201_CREATED)
def create_gig(payload: GigCreate, db: DbSession, current_user: CurrentUser):
    return gig_service.create_gig(db, current_user, payload)


@router.get("/mine", response_model=list[GigDetail])
def my_gigs(db: DbSession, current_user: CurrentUser):
    """Declared before /{gig_id} so "mine" is not parsed as a UUID."""
    return gig_service.list_my_gigs(db, current_user)


@router.get("/{gig_id}", response_model=GigDetail)
def get_gig(gig_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return gig_service.get_gig_for_viewer(db, gig_id, current_user)


@router.post(
    "/{gig_id}/apply", response_model=MyApplication, status_code=status.HTTP_201_CREATED
)
def apply_to_gig(
    gig_id: uuid.UUID, payload: ApplicationCreate, db: DbSession, current_user: CurrentUser
):
    return application_service.apply_to_gig(db, gig_id, current_user, payload.message)


@router.get("/{gig_id}/applications", response_model=list[GigApplicant])
def gig_applications(gig_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    """Poster-only: who applied to my gig."""
    return application_service.list_for_my_gig(db, gig_id, current_user)
