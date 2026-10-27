# CampusGig — Architecture

Scope of this document: Milestone 1 (authentication + read-only gig browsing).
Later milestones extend it; nothing here is designed to be thrown away.

## A. Proposed architecture

Two deployables plus a database:

```
React SPA (Vite)  --HttpOnly cookie-->  FastAPI  -->  PostgreSQL
                                            |
                                            +-->  MEDIA_ROOT (avatars, resumes)
```

Backend layering, strictly one direction:

```
api/ (routers)      HTTP only: request/response, status codes, dependencies
   |
services/           business rules: domain validation, session policy, lockout
   |
repositories/       all SQLAlchemy queries live here
   |
models/             SQLAlchemy ORM, the only place tables are declared
```

Rules:
- Routers never import SQLAlchemy models or build queries.
- Services never touch `Request`/`Response`/`HTTPException` — they raise domain
  errors that a single exception handler maps to HTTP status codes.
- Pydantic schemas are the only shapes crossing the API boundary; ORM objects
  are never serialised directly.
- `core/` holds config, security primitives, and errors; it imports nothing from
  the layers above.

### Why an opaque session token instead of a JWT

The brief requires logout to invalidate the session and requires an
"expired/invalid session" test. A stateless JWT cannot be revoked without adding
a denylist table — which is strictly more machinery than just storing the
session. So: a random 256-bit token in an HttpOnly cookie, its SHA-256 stored in
a `sessions` row. Logout deletes the row. Revocation, expiry, and "log out
everywhere" all come free, and there is no JWT library to keep patched.

## B. Folder structure

```
campusgig/
  PROJECT_PLAN.md  ARCHITECTURE.md  README.md  .gitignore  docker-compose.yml
  backend/
    app/
      main.py                  # app factory, CORS, exception handlers, router mount
      core/
        config.py              # pydantic-settings, env-driven
        security.py            # password hash, session token
        errors.py              # domain exceptions, mapped to HTTP in main.py
      db/
        base.py                # DeclarativeBase + TimestampMixin
        session.py             # engine, sessionmaker, get_db dependency
      models/
        user.py                # User, UserRole
        session.py             # UserSession
        gig.py                 # Gig, GigCategory, GigState
        application.py         # Application, ApplicationStatus
      schemas/
        auth.py  user.py  gig.py  application.py  profile.py  common.py
      repositories/
        user_repo.py  session_repo.py  gig_repo.py  application_repo.py
      services/
        auth_service.py  gig_service.py
        application_service.py  profile_service.py  storage_service.py
      api/
        deps.py                # DbSession, CurrentUser, cookie helpers
        v1/
          __init__.py          # APIRouter(prefix="/api/v1") aggregator
          auth.py  gigs.py  applications.py  profile.py  health.py
      seeds/
        seed_gigs.py           # dev data only, refuses to run in production
    alembic/versions/0001_initial_schema.py
                     0002_remove_email_verification.py
                     0003_applications_and_profile.py
    tests/
      conftest.py              # test DB, migrations, fixtures
      test_health_and_model.py  test_registration.py  test_auth_session.py
      test_gigs.py  test_applications.py  test_profile.py
    alembic.ini  pyproject.toml  .env.example
  frontend/
    src/
      main.tsx  App.tsx
      routes/AppRoutes.tsx  ProtectedRoute.tsx  GuestRoute.tsx
      context/authContext.ts  AuthProvider.tsx
              profileContext.ts  ProfileProvider.tsx
      services/apiClient.ts  authApi.ts  gigApi.ts  applicationApi.ts  profileApi.ts
      hooks/useAuth.ts  useGigs.ts  useProfile.ts
      lib/validation.ts  format.ts
      layouts/AppLayout.tsx  AuthLayout.tsx
      components/ui/{Button,TextField,SelectField,Alert,Spinner,EmptyState}.tsx
      components/gigs/{GigCard,SearchBar,FilterControls,Pagination,PostGigDialog}.tsx
      components/applications/{StatCard,StatusPill,ApplyPanel,ApplicantList}.tsx
      pages/{Login,Signup,Gigs,GigDetails,AppliedGigs,Profile,NotFound}Page.tsx
      types/auth.ts  gig.ts  application.ts  profile.ts
      styles/global.css
      __tests__/validation.test.ts  auth.test.tsx
    index.html  vite.config.ts  tsconfig.json  eslint.config.js  .env.example
```

## C. Database design — Milestone 1

All primary keys are UUID (`gen_random_uuid()`, built into PostgreSQL 13+).
All timestamps are `timestamptz`, defaulted server-side.

### `users`

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | `gen_random_uuid()` |
| email | citext NOT NULL UNIQUE | stored normalised lowercase; `citext` makes uniqueness case-insensitive in the DB, not only in the app |
| email_hash | text NOT NULL, generated | `GENERATED ALWAYS AS (encode(sha256(lower(email::text)::bytea),'hex')) STORED` — satisfies the UML `emailHash` with zero application code, and it can never drift from `email` |
| password_hash | text NOT NULL | bcrypt |
| roll_no | text NOT NULL UNIQUE | |
| dept | text NOT NULL | |
| batch | integer NOT NULL | CHECK between 1900 and 2100 |
| role | user_role NOT NULL DEFAULT 'STUDENT' | enum: STUDENT, ADMIN |
| failed_login_attempts | integer NOT NULL DEFAULT 0 | |
| locked_until | timestamptz NULL | login lockout |
| bio | text NULL | short self-description |
| avatar_path | text NULL | path under MEDIA_ROOT, not a URL, so storage can change without a data migration |
| resume_path | text NULL | same, for the resume PDF |
| created_at / updated_at | timestamptz NOT NULL | `now()`; `updated_at` via ORM `onupdate` |

Indexes: unique on `email` and `roll_no`. `email_hash` gets no index of its own —
nothing in Milestone 1 looks a user up by hash, and it is derived from an already
unique column.

`role` is an enum so later milestones can extend it, but note the UML models
Poster and Worker as *capacities*, not account types: a user is a poster on gigs
they created and a worker on contracts they hold. Milestone 1 ships
`STUDENT`/`ADMIN` only. ADMIN is never assignable through registration — the
register schema has no `role` field at all and the service hardcodes `STUDENT`.

### `sessions`

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK -> users(id) ON DELETE CASCADE, indexed | |
| token_hash | text NOT NULL UNIQUE | SHA-256 of the cookie value; the raw token is never stored |
| expires_at | timestamptz NOT NULL, indexed | |
| created_at | timestamptz NOT NULL | |

### `applications`

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| gig_id | uuid FK -> gigs(id) ON DELETE CASCADE, indexed | |
| applicant_id | uuid FK -> users(id) ON DELETE CASCADE, indexed | |
| message | text NULL | optional note to the poster |
| status | application_status NOT NULL DEFAULT 'APPLIED' | enum: APPLIED, ACCEPTED, REJECTED, COMPLETED |
| created_at / updated_at | timestamptz NOT NULL | |

Constraint: `UNIQUE (gig_id, applicant_id)` — one application per person per gig,
enforced by the database rather than by a check-then-insert race in the service.
Index on `(applicant_id, status)` for the Applied page's per-status counts.

Not a bid: there is no counter-offer and no negotiated price. A student applies
at the posted budget and the poster answers. Priced bidding stays in Milestone 3.

### `gigs` (step 6)

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| poster_id | uuid FK -> users(id) ON DELETE RESTRICT, indexed | |
| title | text NOT NULL | CHECK length 5..200 |
| description | text NOT NULL | |
| category | gig_category NOT NULL | enum |
| budget | numeric(10,2) NOT NULL | CHECK > 0 — money is never a float |
| deadline | timestamptz NOT NULL | |
| duration_days | integer NULL | expected effort, CHECK 1..365. Distinct from the deadline: "two days of work, due in three weeks" |
| state | gig_state NOT NULL DEFAULT 'OPEN' | enum: OPEN, CLOSED. Milestone 1 browses OPEN only; CLOSED exists so the listing filter is provably doing something rather than passing by default |
| created_at / updated_at | timestamptz NOT NULL | |

Indexes: `(poster_id)`, `(category)`, and `(state, created_at DESC)` for the
default listing.
Search is `ILIKE '%term%'` over title and description.
`ponytail:` ILIKE scan is fine at seed-data scale; swap for a `tsvector` GIN
index when the gig table passes roughly 10k rows.

## D. Authentication design

**Registration**

```
POST /auth/register
  -> schema validation (email format, password strength, batch range)
  -> service: assert domain == thapar.edu  (case-insensitive, exact)
  -> service: assert email + roll_no unused
  -> bcrypt(password); insert user (role=STUDENT)
  -> 201 { user_id, email, message }
```

Registration deliberately does **not** create a session. The client sends the
student to `/login` with an "Account created" notice, so signing in is an
explicit act.

There is no email verification step, which makes the domain check the whole of
the access control. It is therefore backend-enforced, case-insensitive and
exact: normalise with `email.strip().lower()`, split on the last `@`, and
compare the **whole** domain for equality with `thapar.edu`. Suffix matching is
not used: `endswith("thapar.edu")` would accept `a@fakethapar.edu`, and no
suffix check handles `a@thapar.edu.fake.com`. Whole-domain equality rejects
every listed attack string by construction.

The trade-off this accepts: nothing proves the person controls the address they
typed. Re-adding verification is a new migration plus a service; the removed
version is in git history.

**Login**

```
POST /auth/login -> lookup by normalised email
  -> if locked_until > now: 429
  -> bcrypt verify (run a dummy verify when the user is missing, so an unknown
     account costs the same time as a wrong password)
  -> create session, Set-Cookie
  -> 200 { user }
```

Wrong password and unknown email return the identical 401 body
("Invalid email or password") with matching timing. Login failures increment
`failed_login_attempts`; 10 failures set `locked_until = now + 15 min`; a
successful login resets both.

**Session cookie**

`campusgig_session`, value = `secrets.token_urlsafe(32)`.
`HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` when `ENVIRONMENT=production`,
`Max-Age` = `SESSION_TTL_MINUTES` (default 7 days). Local dev
(`localhost:5173` -> `localhost:8000`) works with `Lax` because the SPA uses
`fetch(..., { credentials: "include" })` and CORS is configured with
`allow_credentials=True` and an explicit origin list — never `*`.

**Dependencies**

`get_current_user` reads the cookie, hashes it, loads the session, checks
expiry, and returns the user or raises 401. Routes opt in by declaring the
dependency; no per-route manual checks and no auth logic in route bodies.

## E. API endpoint plan

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | none | liveness (mounted at the root, outside the versioned API) |
| GET | `/health/db` | none | `SELECT 1` round trip |
| POST | `/api/v1/auth/register` | none | create the account; no session is issued |
| POST | `/api/v1/auth/login` | none | create session cookie |
| POST | `/api/v1/auth/logout` | session | delete session, clear cookie |
| GET | `/api/v1/auth/me` | session | safe user profile |
| GET | `/api/v1/gigs` | session | paginated list of OPEN gigs |
| POST | `/api/v1/gigs` | session | post a gig; poster is the session user |
| GET | `/api/v1/gigs/mine` | session | gigs I posted, any state |
| GET | `/api/v1/gigs/{gig_id}` | session | an OPEN gig, or any of my own |
| POST | `/api/v1/gigs/{gig_id}/apply` | session | apply to a gig |
| GET | `/api/v1/gigs/{gig_id}/applications` | poster | who applied to my gig |
| GET | `/api/v1/applications/me` | session | my applications plus summary totals |
| PATCH | `/api/v1/applications/{id}` | poster | accept / decline / complete |
| GET | `/api/v1/profile` | session | my profile |
| PATCH | `/api/v1/profile` | session | update the bio |
| POST | `/api/v1/profile/avatar` | session | upload a profile picture |
| POST | `/api/v1/profile/resume` | session | upload a resume PDF |
| GET | `/media/{path}` | none | uploaded files, served by random UUID name |

`GET /api/v1/gigs` query params, all validated server-side by Pydantic:
`page` (>=1, default 1), `page_size` (1..50, default 12), `q` (<=100 chars),
`category` (enum), `min_budget` / `max_budget` (>=0, max >= min),
`deadline_before`, `sort` (`newest` | `deadline` | `budget_asc` | `budget_desc`).

Response envelope: `{ items, page, page_size, total, total_pages }`.

Status codes: 200 ok, 201 created, 400 malformed, 401 unauthenticated,
403 not the owner, 404 not found, 409 duplicate or bad state transition,
413 file too large, 415 wrong file type, 422 schema validation, 429 locked.

`/gigs/mine` is declared before `/gigs/{gig_id}` so "mine" is not parsed as a UUID.

**Application status transitions.** Only the gig's poster drives these, and only
forwards: `APPLIED -> ACCEPTED | REJECTED`, `ACCEPTED -> COMPLETED`. Nothing
leaves `REJECTED` or `COMPLETED`. Accepting also closes the gig and rejects the
other pending applications, so one gig cannot end up with five accepted workers.

**Earnings are not payments.** `earned` is the sum of `gigs.budget` over the
applicant's COMPLETED applications. No money moves anywhere in this release; the
Applied page states this under the report cards.
Error body is always `{ "detail": { "code": "SNAKE_CASE", "message": "..." } }`.

`UserPublic` (returned by `/me`): `id, email, roll_no, dept, batch, role,
created_at`. `PosterPublic` (embedded in gigs): `id, dept, batch,
roll_no` — no email, no hash, no internal fields.

## F. Frontend route plan

| Route | Guard | Page |
|---|---|---|
| `/` | — | redirect to `/dashboard` or `/login` |
| `/signup` | guest-only | Signup, then redirect to `/login` (email passed via router state, not the URL) |
| `/login` | guest-only | Login |
| `/gigs` | protected | Gigs board: search, filters, pagination, and the + button that posts a gig |
| `/gigs/:gigId` | protected | Gig details; apply, or manage applicants if it is yours |
| `/applied` | protected | Applied gigs: report cards and the application list |
| `/profile` | protected | Avatar, resume, bio, signup details |
| `/dashboard` | — | redirect to `/gigs`, the page's former name |
| `*` | — | NotFound |

`AuthProvider` calls `GET /auth/me` once on mount to rehydrate the session after
a refresh, exposing `{ user, status: 'loading' | 'authenticated' | 'anonymous',
login, logout, refresh }`. `ProtectedRoute` renders a spinner while
`status === 'loading'` — otherwise a refresh flashes the login page — then
redirects to `/login` carrying the attempted path. The API client is a single
`request()` wrapper over native `fetch` with `credentials: 'include'`,
`VITE_API_BASE_URL` from env, and a 401 handler that clears auth state. No
`axios`; no URLs scattered through components.

## G. Security considerations

| Risk | Control |
|---|---|
| Non-Thapar signup | Backend exact-domain check, the only access control now that verification is gone; the frontend check is UX only |
| Unproven email ownership | **Accepted risk.** Nothing confirms the signer-up controls the address. Re-add verification if that matters |
| Password disclosure | bcrypt (cost 12); `password_hash` absent from every response schema; no password in any log or exception |
| Session theft via XSS | HttpOnly cookie; the token never reaches JS; nothing auth-related in localStorage |
| CSRF | `SameSite=Lax` + explicit CORS allowlist + no state-changing GETs. A double-submit token is deferred; `Lax` already blocks cross-site POSTs. `ponytail:` add a CSRF token if a future flow ever needs `SameSite=None` |
| Session fixation / replay | Token generated server-side per login, stored hashed, deleted on logout |
| Login brute force | Per-account lockout after 10 failures for 15 minutes |
| Account enumeration | Identical 401 body and timing for unknown email and wrong password |
| Privilege escalation | `role` is not part of any request schema; register hardcodes STUDENT |
| IDOR / data leakage | Gig responses use `PosterPublic`; ORM objects never serialised directly |
| Injection | SQLAlchemy parameter binding only; no string-built SQL |
| Unbounded queries | `page_size` capped at 50; every list endpoint paginated |
| Malicious uploads | File type decided by magic bytes, never the client's Content-Type; size capped while streaming, not after; stored under a random UUID name so a client filename can never carry a path or a second extension |
| Uploaded file exposure | Served from `/media` under unguessable UUID names - a capability URL, not an access check. Good enough for an avatar; move behind an authenticated endpoint before anything private lives here |
| Privilege escalation on gigs | `poster_id` and `state` are absent from `GigCreate`; the poster is the session user and new gigs are always OPEN |
| Acting on someone else's gig | Status changes and the applicant list check `gig.poster_id` against the session user, so an applicant cannot promote their own application |
| Secret leakage | All secrets from env; `.env.example` holds placeholders only; `.env` gitignored; the app refuses to boot in production with a default `AUTH_SECRET` |
| Transport | `Secure` cookie plus HTTPS assumed in production |

Explicitly deferred to later milestones: per-IP rate limiting (needs a shared
store), refresh-token rotation, audit logging, 2FA, virus scanning of uploads.

`ponytail:` uploads live on local disk. That is correct for one process and wrong
the moment a second app instance exists, because the two would not share files.
`storage_service` is the only module that touches the filesystem, so swapping in
S3 or MinIO is a change to that file alone.

## H. Development sequence

See the table in [PROJECT_PLAN.md](PROJECT_PLAN.md). Order: foundation ->
signup -> login/session -> frontend auth -> end-to-end integration ->
gig list + dashboard -> gig details -> audit. Each step runs its tests and
reports failures honestly before the next step starts.
