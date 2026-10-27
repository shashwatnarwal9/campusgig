"""Profile reads and updates, including avatar and resume files."""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.profile import Profile, ProfileUpdate
from app.services import storage_service


def to_schema(user: User) -> Profile:
    return Profile(
        id=user.id,
        email=user.email,
        roll_no=user.roll_no,
        dept=user.dept,
        batch=user.batch,
        role=user.role,
        created_at=user.created_at,
        bio=user.bio,
        avatar_url=storage_service.public_url(user.avatar_path),
        resume_url=storage_service.public_url(user.resume_path),
    )


def update(db: Session, user: User, data: ProfileUpdate) -> Profile:
    bio = (data.bio or "").strip()
    user.bio = bio or None
    db.commit()
    return to_schema(user)


def _replace_file(db: Session, user: User, field: str, new_path: str) -> Profile:
    """Point the user at the new file, then delete the old one.

    Order matters: if the delete fails we are left with a stray file, which is
    harmless. Deleting first would risk a profile pointing at nothing.
    """
    previous = getattr(user, field)
    setattr(user, field, new_path)
    db.commit()
    storage_service.delete(previous)
    return to_schema(user)


def set_avatar(db: Session, user: User, upload: UploadFile) -> Profile:
    return _replace_file(db, user, "avatar_path", storage_service.save_avatar(upload))


def set_resume(db: Session, user: User, upload: UploadFile) -> Profile:
    return _replace_file(db, user, "resume_path", storage_service.save_resume(upload))
