import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.api.v1 import health as health_router
from app.core.config import settings
from app.core.errors import DomainError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def _error(status_code: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"detail": {"code": code, "message": message, **extra}}
    )


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return _error(exc.status_code, exc.code, exc.message)


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or "body",
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return _error(422, "validation_error", "Some fields need attention.", fields=fields)


async def http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """Reshape framework errors (404, 405, ...) into the same envelope as domain
    errors so the frontend has exactly one error format to parse."""
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _error(exc.status_code, f"http_{exc.status_code}", detail)


def create_app() -> FastAPI:
    app = FastAPI(
        title="CampusGig API",
        version="0.1.0",
        description="University-only gig marketplace. Milestone 1: auth + gig browsing.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # explicit list; never "*" with credentials
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type"],
        expose_headers=["Content-Disposition"],
    )

    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)

    app.include_router(health_router.router)
    app.include_router(api_router)

    # Uploaded avatars and resumes. Filenames are random UUIDs, so the URL is
    # the capability - nothing here is enumerable from an id.
    media_root = Path(settings.media_root)
    media_root.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_root), name="media")

    return app


app = create_app()
