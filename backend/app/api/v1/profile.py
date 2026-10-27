from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.schemas.profile import Profile, ProfileUpdate
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=Profile)
def get_profile(current_user: CurrentUser):
    return profile_service.to_schema(current_user)


@router.patch("", response_model=Profile)
def update_profile(payload: ProfileUpdate, db: DbSession, current_user: CurrentUser):
    return profile_service.update(db, current_user, payload)


@router.post("/avatar", response_model=Profile)
def upload_avatar(
    db: DbSession, current_user: CurrentUser, file: Annotated[UploadFile, File()]
):
    return profile_service.set_avatar(db, current_user, file)


@router.post("/resume", response_model=Profile)
def upload_resume(
    db: DbSession, current_user: CurrentUser, file: Annotated[UploadFile, File()]
):
    return profile_service.set_resume(db, current_user, file)
