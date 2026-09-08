# CampusGig — Project Plan

University-only gig marketplace for Thapar Institute. Access is restricted to
verified `@thapar.edu` accounts.

## Milestones

| # | Milestone | Contents | Status |
|---|-----------|----------|--------|
| 1 | Auth + Dashboard | Signup, login, logout, session, protected dashboard, read-only gig browsing, gig details | **Done** |
| 2 | Gig management | Gig posting, poster ownership rules, categories, profile files (avatar + resume) | **Done** (edit/delete and object storage still pending) |
| 3 | Applications | Apply to a gig, poster accept/decline/complete, applied-gigs report | **Done** as applications; priced bids and withdrawal still pending |
| 4 | Contracts | Bid acceptance, contract state machine, transitions + guards | Not started |
| 5 | Escrow + Ledger | Double-entry ledger, escrow hold/release, balances, idempotency | Not started |
| 6 | Delivery + Disputes | Deliverable upload, acceptance, dispute raise/resolve, Scheduler timeouts | Not started |
| 7 | Ratings + Reputation | Post-contract ratings, reputation aggregation | Not started |
| 8 | Admin + Reconciliation | Admin dispute resolution, ledger reconciliation reports, audit log | Not started |

Nothing from Milestones 2–8 is implemented, stubbed, faked, or shown in the UI
during Milestone 1. No payment buttons, no bid buttons except an explicitly
labelled "Coming Soon" marker on the gig details page.

## Milestone 1 scope

In scope:

1. Signup with institutional email (`@thapar.edu`, backend enforced)
2. Login
3. Logout (server-side session invalidation)
4. Authenticated session via HttpOnly cookie
5. Protected dashboard
6. Dashboard listing available (OPEN) gigs with search, filter, pagination
7. Gig details page

Added after the first pass, on request:

8. Top navbar with three destinations: Gigs, Applied, Profile
9. Gig posting from a floating + button
10. Applications: apply, poster accept/decline/complete, applied-gigs report
11. Profile: avatar upload, resume PDF upload, short description, signup details

Email OTP verification was built and then removed on request: signup creates the
account and redirects to login. Migration `0002` drops `email_verifications` and
`users.is_verified`. If verification is wanted later it comes back as its own
migration; the code is in git history.

`applications` is not the bidding milestone: there is no counter-offer, no
negotiated price and no contract. A student applies at the posted budget and the
poster says yes or no.

Out of scope: payments, escrow, ledger, contracts, bidding, bid acceptance,
deliverables, disputes, ratings, reputation, admin dispute resolution,
reconciliation, payment gateways.

Milestone 1 has **no gig-creation UI or API**. Gigs come from a development
seed script so the read-only browsing flow can be built and tested.

## Development sequence

Each step ends with tests run and reported before the next begins.

| Step | Work | Exit criteria |
|------|------|---------------|
| 0 | Planning docs (this file, ARCHITECTURE.md, README.md) | Plan reviewed |
| 1 | Backend foundation: config, DB, session, Alembic, `User` model, health endpoints, router skeleton, CORS | `pytest` green; migration applies; `/health/db` returns ok |
| 2 | Signup + `@thapar.edu` validation | domain, duplicate and password tests pass |
| 3 | Login, logout, `/auth/me`, session cookie, `get_current_user` dependency, login lockout | Session tests pass; full suite green |
| 4 | Frontend: Vite + React + TS, API client, `AuthProvider`, `/signup`, `/login`, protected route shell | `tsc --noEmit`, `eslint`, `vitest`, `vite build` all clean |
| 5 | End-to-end integration against real backend + real Postgres | Full happy path + 15 failure scenarios verified and reported |
| 6 | `Gig` model + `GET /api/v1/gigs` (paginated, searchable, filterable) + seed script + `/dashboard` UI | Backend tests green; dashboard renders live API data |
| 7 | `GET /api/v1/gigs/{id}` + `/gigs/:id` page | 404/error states handled; build green |
| 8 | Security + code audit, no new features | Audit report delivered |

## Definition of done for Milestone 1

- A new `@thapar.edu` user can sign up, land on the login page, log in, browse
  open gigs with search/filter/pagination, open a gig's detail page, and log out.
- Every rejection path in the brief is covered by an automated test.
- No secret, password, or password hash appears in any API response or log line.
- `alembic upgrade head` on an empty database produces the full schema.
