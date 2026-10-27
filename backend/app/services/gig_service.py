import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import GigNotFound, InvalidQuery
from app.models.gig import Gig, GigCategory, GigState
from app.models.user import User
from app.repositories import gig_repo
from app.schemas.gig import GigCreate

MAX_PAGE_SIZE = 50


def list_open_gigs(
    db: Session,
    *,
    q: str | None = None,
    category: GigCategory | None = None,
    min_budget: Decimal | None = None,
    max_budget: Decimal | None = None,
    deadline_before: datetime | None = None,
    sort: str = "newest",
    page: int = 1,
    page_size: int = 12,
) -> tuple[list[Gig], int, int]:
    if min_budget is not None and max_budget is not None and min_budget > max_budget:
        raise InvalidQuery("min_budget cannot be greater than max_budget.")
    if sort not in gig_repo.SORTS:
        raise InvalidQuery(f"sort must be one of: {', '.join(gig_repo.SORTS)}")

    page_size = min(page_size, MAX_PAGE_SIZE)
    items, total = gig_repo.list_page(
        db,
        state=GigState.OPEN,
        q=(q.strip() or None) if q else None,
        category=category,
        min_budget=min_budget,
        max_budget=max_budget,
        deadline_before=deadline_before,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, -(-total // page_size))  # ceil
    return items, total, total_pages


def get_open_gig(db: Session, gig_id: uuid.UUID) -> Gig:
    gig = gig_repo.get_visible(db, gig_id, state=GigState.OPEN)
    if gig is None:
        raise GigNotFound()
    return gig


def get_gig_for_viewer(db: Session, gig_id: uuid.UUID, viewer: User) -> Gig:
    """Open to everyone; a closed gig stays visible to the person who posted it
    so their own listing does not 404 the moment they accept someone."""
    gig = gig_repo.get(db, gig_id)
    if gig is None or (gig.state is not GigState.OPEN and gig.poster_id != viewer.id):
        raise GigNotFound()
    return gig


def create_gig(db: Session, poster: User, data: GigCreate) -> Gig:
    gig = gig_repo.create(
        db,
        poster_id=poster.id,
        title=data.title,
        description=data.description,
        category=data.category,
        budget=data.budget,
        deadline=data.deadline,
        duration_days=data.duration_days,
    )
    db.commit()
    return gig


def list_my_gigs(db: Session, poster: User) -> list[Gig]:
    return gig_repo.list_for_poster(db, poster.id)
