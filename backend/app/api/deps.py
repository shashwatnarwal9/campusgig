from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotAuthenticated
from app.db.session import get_db
from app.models.user import User
from app.services import auth_service

DbSession = Annotated[Session, Depends(get_db)]


def get_session_token(request: Request) -> str | None:
    return request.cookies.get(settings.session_cookie_name)


def get_current_user(request: Request, db: DbSession) -> User:
    """The single authentication gate. Routes require auth by declaring
    `CurrentUser`; no route ever checks the cookie itself."""
    user = auth_service.user_for_token(db, get_session_token(request))
    if user is None:
        raise NotAuthenticated()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )
