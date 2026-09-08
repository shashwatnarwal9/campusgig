import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class ProfileUpdate(BaseModel):
    bio: Annotated[str | None, Field(default=None, max_length=1000)] = None


class Profile(BaseModel):
    """Everything the signed-in student may see about themselves: the details
    captured at signup plus what they have added since."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    roll_no: str
    dept: str
    batch: int
    role: UserRole
    created_at: datetime
    bio: str | None
    avatar_url: str | None
    resume_url: str | None
