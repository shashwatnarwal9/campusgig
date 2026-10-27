from fastapi import APIRouter

from app.api.v1 import applications, auth, gigs, profile
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(auth.router)
api_router.include_router(gigs.router)
api_router.include_router(applications.router)
api_router.include_router(profile.router)

__all__ = ["api_router"]
