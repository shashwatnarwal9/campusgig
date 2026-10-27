import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from app.models.gig import GigCategory, GigState
from app.schemas.user import PosterPublic


class GigSummary(BaseModel):
    """Card-sized view used by the dashboard listing."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    category: GigCategory
    short_description: str
    budget: Decimal
    deadline: datetime
    duration_days: int | None
    state: GigState
    created_at: datetime
    poster: PosterPublic


class GigDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    category: GigCategory
    description: str
    budget: Decimal
    deadline: datetime
    duration_days: int | None
    state: GigState
    created_at: datetime
    updated_at: datetime
    poster: PosterPublic


class GigCreate(BaseModel):
    """What a student may set when posting. Poster and state are never taken
    from the request: the poster is the session user and new gigs are OPEN."""

    title: Annotated[str, Field(min_length=5, max_length=200), AfterValidator(str.strip)]
    description: Annotated[str, Field(min_length=20, max_length=5000), AfterValidator(str.strip)]
    category: GigCategory
    budget: Decimal = Field(gt=0, le=1_000_000, decimal_places=2)
    deadline: datetime
    duration_days: int | None = Field(default=None, ge=1, le=365)

    @field_validator("deadline")
    @classmethod
    def _deadline_in_future(cls, value: datetime) -> datetime:
        # Naive datetimes are treated as UTC rather than rejected: the browser
        # sends an ISO string and we care about the instant, not the notation.
        moment = value if value.tzinfo else value.replace(tzinfo=UTC)
        if moment <= datetime.now(UTC):
            raise ValueError("Deadline must be in the future")
        return moment
