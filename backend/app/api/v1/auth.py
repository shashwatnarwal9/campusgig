from fastapi import APIRouter, Request, Response, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    clear_session_cookie,
    get_session_token,
    set_session_cookie,
)
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse
from app.schemas.common import MessageResponse
from app.schemas.user import UserPublic
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession):
    """Creates the account. The client then sends the student to the login page -
    registration deliberately does not log anyone in."""
    user = auth_service.register(db, payload)
    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        message="Account created. You can log in now.",
    )


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest, response: Response, db: DbSession):
    user, token, _expires_at = auth_service.login(db, payload)
    set_session_cookie(response, token)
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: DbSession):
    auth_service.logout(db, get_session_token(request))
    clear_session_cookie(response)
    return MessageResponse(message="Logged out.")


@router.get("/me", response_model=UserPublic)
def me(current_user: CurrentUser):
    return current_user
