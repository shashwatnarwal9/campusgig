import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.contract import ContractStatus
from app.models.gig import GigCategory
from app.schemas.user import PosterPublic


class ContractSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    gig_id: uuid.UUID
    status: ContractStatus
    gig_title: str
    amount_paise: int
    created_at: datetime
    poster: PosterPublic
    worker: PosterPublic


class ContractHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    previous_status: ContractStatus
    new_status: ContractStatus
    actor: PosterPublic
    created_at: datetime


class ContractDetail(ContractSummary):
    application_id: uuid.UUID
    gig_description: str
    gig_category: GigCategory
    deadline: datetime
    duration_days: int | None
    confirmation_deadline: datetime | None
    revisions_used: int
    updated_at: datetime
    history: list[ContractHistoryItem]
