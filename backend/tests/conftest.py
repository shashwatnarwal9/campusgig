"""Test harness.

Points the app at a dedicated test database, applies the real Alembic migrations
(so schema drift is caught by the suite) and truncates between tests.
"""

import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest

# Must run before any app module reads configuration.
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("AUTH_SECRET", "test-secret-not-used-anywhere-else")
# Uploads land in a scratch directory, never the development media folder.
os.environ.setdefault("MEDIA_ROOT", str(Path(__file__).parent / "_media"))


def _from_env_file(key: str) -> str | None:
    """Read one key out of backend/.env.

    Settings normally does this, but the test database URL has to be decided
    before any app module imports configuration, so it is read directly here.
    """
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return None
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() == key:
            return value.strip()
    return None


def _test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL") or _from_env_file("TEST_DATABASE_URL")
    if explicit:
        return explicit
    base = (
        os.environ.get("DATABASE_URL")
        or _from_env_file("DATABASE_URL")
        or "postgresql+psycopg://postgres:postgres@localhost:5432/campusgig"
    )
    parts = urlsplit(base)
    return urlunsplit(parts._replace(path=parts.path.rstrip("/") + "_test"))


os.environ["DATABASE_URL"] = _test_database_url()

from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

TABLES = ("applications", "sessions", "gigs", "users")


def _ensure_database_exists(url: str) -> None:
    parts = urlsplit(url)
    db_name = parts.path.lstrip("/")
    admin_url = urlunsplit(parts._replace(path="/postgres"))
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _database() -> Iterator[None]:
    url = settings.database_url
    _ensure_database_exists(url)

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
    shutil.rmtree(settings.media_root, ignore_errors=True)
    yield


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


# --- helpers ---------------------------------------------------------------

VALID_PASSWORD = "CampusGig123"


def registration_payload(**overrides) -> dict:
    payload = {
        "email": "student@thapar.edu",
        "password": VALID_PASSWORD,
        "roll_no": "102103999",
        "dept": "Computer Science",
        "batch": 2026,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def register_user(client: TestClient):
    def _register(**overrides) -> dict:
        payload = registration_payload(**overrides)
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201, response.text
        return payload

    return _register


@pytest.fixture
def logged_in(client: TestClient, register_user):
    def _logged_in(**overrides) -> dict:
        payload = register_user(**overrides)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
        assert response.status_code == 200, response.text
        return payload

    return _logged_in
