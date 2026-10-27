import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStatus
from app.schemas.gig import GigSummary
from app.schemas.user import PosterPublic


class ApplicationCreate(BaseModel):
    message: Annotated[str | None, Field(default=None, max_length=1000)] = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class MyApplication(BaseModel):
    """The applicant's own view: their application plus the gig it is for."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ApplicationStatus
    message: str | None
    created_at: datetime
    updated_at: datetime
    gig: GigSummary


class GigApplicant(BaseModel):
    """The poster's view of who applied. Same safe fields as a gig's poster."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ApplicationStatus
    message: str | None
    created_at: datetime
    applicant: PosterPublic


class ApplicationSummary(BaseModel):
    total: int
    applied: int
    accepted: int
    rejected: int
    completed: int
    # Budget of completed work. No money has moved: escrow and payments are a
    # later milestone, and the UI labels this accordingly.
    earned: Decimal
    in_progress_value: Decimal


class MyApplications(BaseModel):
    summary: ApplicationSummary
    items: list[MyApplication]
