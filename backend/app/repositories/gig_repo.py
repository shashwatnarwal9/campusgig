import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.gig import Gig, GigCategory, GigState

SORTS = {
    "newest": Gig.created_at.desc(),
    "deadline": Gig.deadline.asc(),
    "budget_asc": Gig.budget.asc(),
    "budget_desc": Gig.budget.desc(),
}


def _filtered(
    *,
    state: GigState,
    q: str | None,
    category: GigCategory | None,
    min_budget: Decimal | None,
    max_budget: Decimal | None,
    deadline_before: datetime | None,
):
    conditions = [Gig.state == state]
    if q:
        # ponytail: ILIKE scan is fine at this table size; move to a tsvector GIN
        # index once gigs pass roughly 10k rows.
        pattern = f"%{q}%"
        conditions.append(or_(Gig.title.ilike(pattern), Gig.description.ilike(pattern)))
    if category is not None:
        conditions.append(Gig.category == category)
    if min_budget is not None:
        conditions.append(Gig.budget >= min_budget)
    if max_budget is not None:
        conditions.append(Gig.budget <= max_budget)
    if deadline_before is not None:
        conditions.append(Gig.deadline <= deadline_before)
    return conditions


def list_page(
    db: Session,
    *,
    state: GigState = GigState.OPEN,
    q: str | None = None,
    category: GigCategory | None = None,
    min_budget: Decimal | None = None,
    max_budget: Decimal | None = None,
    deadline_before: datetime | None = None,
    sort: str = "newest",
    page: int = 1,
    page_size: int = 12,
) -> tuple[list[Gig], int]:
    conditions = _filtered(
        state=state,
        q=q,
        category=category,
        min_budget=min_budget,
        max_budget=max_budget,
        deadline_before=deadline_before,
    )

    total = db.scalar(select(func.count()).select_from(Gig).where(*conditions)) or 0

    rows = (
        db.scalars(
            select(Gig)
            .where(*conditions)
            .order_by(SORTS.get(sort, SORTS["newest"]), Gig.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .unique()
        .all()
    )
    return list(rows), total


def get_visible(db: Session, gig_id: uuid.UUID, *, state: GigState = GigState.OPEN) -> Gig | None:
    return db.scalar(select(Gig).where(Gig.id == gig_id, Gig.state == state))


def get(db: Session, gig_id: uuid.UUID) -> Gig | None:
    """Any state. Used by owners and by the application flow, which must see a
    closed gig in order to refuse it properly."""
    return db.get(Gig, gig_id)


def list_for_poster(db: Session, poster_id: uuid.UUID) -> list[Gig]:
    return list(
        db.scalars(
            select(Gig).where(Gig.poster_id == poster_id).order_by(Gig.created_at.desc())
        )
        .unique()
        .all()
    )


def create(
    db: Session,
    *,
    poster_id: uuid.UUID,
    title: str,
    description: str,
    category: GigCategory,
    budget: Decimal,
    deadline: datetime,
    duration_days: int | None,
) -> Gig:
    gig = Gig(
        poster_id=poster_id,
        title=title,
        description=description,
        category=category,
        budget=budget,
        deadline=deadline,
        duration_days=duration_days,
        state=GigState.OPEN,
    )
    db.add(gig)
    db.flush()
    return gig
