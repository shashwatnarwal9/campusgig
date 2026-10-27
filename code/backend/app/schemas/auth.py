import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.core.security import MAX_PASSWORD_BYTES


def _normalise_email(value: str) -> str:
    return value.strip().lower()


def _validate_password(value: str) -> str:
    if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes long")
    if not any(c.isalpha() for c in value):
        raise ValueError("Password must contain at least one letter")
    if not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one digit")
    return value


NormalisedEmail = Annotated[EmailStr, AfterValidator(_normalise_email)]
NewPassword = Annotated[
    str, Field(min_length=8, max_length=MAX_PASSWORD_BYTES), AfterValidator(_validate_password)
]


class RegisterRequest(BaseModel):
    email: NormalisedEmail
    password: NewPassword
    roll_no: Annotated[
        str, Field(min_length=3, max_length=32), AfterValidator(lambda v: v.strip().upper())
    ]
    dept: Annotated[str, Field(min_length=2, max_length=100), AfterValidator(str.strip)]
    batch: int = Field(ge=1900, le=2100)


class RegisterResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    message: str


class LoginRequest(BaseModel):
    """No strength rules here: rejecting a weak password at login would leak that
    it is weak, and existing passwords must stay usable if the rules change."""

    email: NormalisedEmail
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_BYTES)
