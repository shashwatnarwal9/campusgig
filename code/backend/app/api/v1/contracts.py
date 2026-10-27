import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Page
from app.schemas.contract import ContractDetail, ContractSummary
from app.services import contract_service
from app.services.gig_service import MAX_PAGE_SIZE

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=Page[ContractSummary])
def my_contracts(
    db: DbSession,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 12,
):
    items, total, total_pages = contract_service.list_for_user(
        db, current_user, page=page, page_size=page_size
    )
    return Page[ContractSummary](
        items=[ContractSummary.model_validate(contract) for contract in items],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{contract_id}", response_model=ContractDetail)
def get_contract(contract_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    contract = contract_service.get_for_user(db, contract_id, current_user)
    return ContractDetail.model_validate(contract)
