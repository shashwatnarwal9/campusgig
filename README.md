# CampusGig

A university-only gig marketplace for Thapar Institute. Only verified
`@thapar.edu` accounts can register and use the platform.

**Status: Milestone 1 implemented.**
See [PROJECT_PLAN.md](PROJECT_PLAN.md) for milestones and
[ARCHITECTURE.md](ARCHITECTURE.md) for the design.

## What Milestone 1 does

Signup with an institutional `@thapar.edu` email, login, logout, and an
authenticated session in an HttpOnly cookie. Signup creates the account and sends
the student straight to the login page; there is no email verification step, so
the backend `@thapar.edu` domain check is the access control.

Behind the login there are three pages, reachable from the top navbar:

| Page | What it does |
|---|---|
| **Gigs** (`/gigs`) | Browse open gigs with search, category, budget and deadline filters, sorting and pagination. A floating **+** button posts a gig: title, scope, category, pay, expected duration and deadline. |
| **Applied** (`/applied`) | Every gig you applied for, filterable by status, with report cards for earned value, work in progress, total applications and replies pending. |
| **Profile** (`/profile`) | Profile picture, resume (PDF), a short description, and the read-only details captured at signup. |

A gig's detail page lets you apply with a message. If the gig is yours, you see
the applicants instead and can accept, decline or mark the work complete;
accepting closes the gig and declines the others.

**Earnings are not payments.** The "earned" figure is the budget of gigs a poster
marked complete. There is no escrow, ledger or payment gateway in this release and
no money moves; the UI says so on the Applied page.

Not included yet: bidding and counter-offers, contracts, escrow, ledger,
deliverable uploads, disputes, ratings, reputation, admin tooling, payments.

## Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, pytest |
| Database | PostgreSQL 15+ |
| Frontend | React 18, TypeScript, Vite, React Router |
| Auth | Server-side sessions in an HttpOnly cookie, bcrypt passwords |
| UI | Framer Motion for page, list and dialog animation |

## Getting started

Prerequisites: Python 3.12+, Node 20+, and PostgreSQL 15+ (or Docker).

### Database

Either point `DATABASE_URL` at an existing PostgreSQL 15+ instance, or start the
bundled development one:

```bash
docker compose up -d db          # postgres on localhost:5434, user/password campusgig
```

With the container, use:

```
DATABASE_URL=postgresql+psycopg://campusgig:campusgig@localhost:5434/campusgig
```

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate           # Windows;  source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
cp .env.example .env             # then fill in real values
alembic upgrade head
python -m app.seeds.seed_gigs    # development gig data, optional
uvicorn app.main:app --reload --port 8000
```

API docs at http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev                      # http://localhost:5173
```

### Tests

```bash
# backend - creates and migrates a separate <db>_test database on first run
cd backend
.venv/Scripts/python.exe -m pytest -q

# frontend
cd frontend
npm run typecheck && npm run lint && npm test && npm run build
```

`tests/conftest.py` creates the `<db>_test` database if missing and applies the
real Alembic migrations, so schema drift is caught by the suite.

## Environment variables

Full list with placeholder values lives in `backend/.env.example` and
`frontend/.env.example`. Never commit a real `.env`.

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | PostgreSQL connection string |
| `AUTH_SECRET` | backend | Signs session material |
| `ENVIRONMENT` | backend | `development` / `production`; controls the `Secure` cookie flag |
| `FRONTEND_URL` | backend | CORS allowlist origin |
| `SESSION_TTL_MINUTES` | backend | Session lifetime |
| `MEDIA_ROOT` | backend | Directory for uploaded avatars and resumes (default `media`) |
| `MAX_AVATAR_BYTES`, `MAX_RESUME_BYTES` | backend | Upload size caps (2 MB / 5 MB) |
| `LOGIN_MAX_FAILURES`, `LOGIN_LOCKOUT_MINUTES` | backend | Login lockout policy |
| `VITE_API_BASE_URL` | frontend | Backend base URL, no trailing slash |
| `TEST_DATABASE_URL` | backend | Optional. Overrides the `<db>_test` default used by pytest |

## Repository layout

```
backend/    FastAPI app (api -> services -> repositories -> models), Alembic, tests
frontend/   React + TypeScript SPA
```

Detailed layout in [ARCHITECTURE.md](ARCHITECTURE.md#b-folder-structure).
