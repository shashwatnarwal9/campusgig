import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserPublic(BaseModel):
    """What the authenticated user is allowed to see about themselves.

    Deliberately excludes password_hash, email_hash and the lockout counters.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    roll_no: str
    dept: str
    batch: int
    role: UserRole
    created_at: datetime


class PosterPublic(BaseModel):
    """What any student may see about the person who posted a gig. No email."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    roll_no: str
    dept: str
    batch: int
