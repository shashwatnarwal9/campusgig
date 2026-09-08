from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@router.get("/health/db")
def health_db(db: DbSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
