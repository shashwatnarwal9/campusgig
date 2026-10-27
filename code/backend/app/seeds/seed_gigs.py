"""Add repeatable fictional demonstration data to the local development database.

Run from ``backend`` with ``python -m app.seeds.seed_gigs``. New demo account
passwords are entered interactively and are never written to source or printed.
The operation only inserts missing records; it never resets or overwrites data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from getpass import getpass
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.application import Application, ApplicationStatus
from app.models.gig import Gig, GigCategory, GigState
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest
from app.services import application_service, auth_service


@dataclass(frozen=True)
class DemoAccount:
    key: str
    email: str
    roll_no: str
    department: str
    batch: int


@dataclass(frozen=True)
class DemoGig:
    title: str
    category: GigCategory
    description: str
    budget: int
    deadline_days: int
    duration_days: int | None
    closed: bool = False


ACCOUNTS = (
    DemoAccount("poster", "demo.poster@thapar.edu", "DEMO-POSTER-001", "CampusGig Demo", 2026),
    DemoAccount(
        "applicant1", "demo.applicant1@thapar.edu", "DEMO-APPLICANT-001", "CampusGig Demo", 2026
    ),
    DemoAccount(
        "applicant2", "demo.applicant2@thapar.edu", "DEMO-APPLICANT-002", "CampusGig Demo", 2026
    ),
    DemoAccount(
        "applicant3", "demo.applicant3@thapar.edu", "DEMO-APPLICANT-003", "CampusGig Demo", 2026
    ),
)

GIGS = (
    DemoGig(
        "DEMO: React landing page for the robotics club",
        GigCategory.DEVELOPMENT,
        "Build a responsive landing page for a fictional campus robotics club. The supplied brief "
        "calls for an events section, project gallery, sponsor strip and accessible contact form. "
        "Use React and document how another student can update the content.",
        6500,
        18,
        5,
    ),
    DemoGig(
        "DEMO: Python script to clean a lab survey dataset",
        GigCategory.ACADEMIC_HELP,
        "Write a small reproducible Python script that normalises column names, handles missing "
        "values and reports duplicate rows in a fictional CSV survey. Include a short README and "
        "a sample output; no real research data is involved.",
        3200,
        12,
        3,
    ),
    DemoGig(
        "DEMO: Campus event poster and social graphics",
        GigCategory.DESIGN,
        "Create an A3 poster and a matching set of square and story-sized graphics for a fictional "
        "student innovation evening. The brief includes the event details and a simple colour "
        "palette. Supply editable source files and allow two rounds of feedback.",
        2800,
        14,
        4,
    ),
    DemoGig(
        "DEMO: Annotate a small machine-learning image dataset",
        GigCategory.ACADEMIC_HELP,
        "Label a fictional set of about 450 classroom object images using the provided category "
        "guide. Flag uncertain examples instead of guessing, and return a CSV with image IDs and "
        "labels. A short calibration batch will be reviewed first.",
        4000,
        21,
        6,
    ),
    DemoGig(
        "DEMO: Edit a short promotional video for a campus club",
        GigCategory.PHOTOGRAPHY,
        "Turn supplied, fictional club footage into a 60 to 90 second promotional cut with "
        "captions, basic colour correction and royalty-free background audio. Deliver a web-ready "
        "MP4 and one revision. No external publication is required.",
        5200,
        16,
        4,
    ),
    DemoGig(
        "DEMO: Improve queries for a student society database",
        GigCategory.DEVELOPMENT,
        "Review a small sample PostgreSQL schema for a fictional society membership tool. Suggest "
        "indexes for three supplied slow queries and explain the trade-offs. Include before-and-"
        "after "
        "EXPLAIN output using generated sample data only.",
        4800,
        15,
        3,
    ),
    DemoGig(
        "DEMO: Build a portfolio website for a graduating student",
        GigCategory.DEVELOPMENT,
        "Create a clean responsive portfolio with project cards, a short profile and a contact "
        "link. The fictional student will provide approved text and illustrations; the work should "
        "include "
        "mobile layout and keyboard-friendly navigation.",
        7500,
        24,
        7,
    ),
    DemoGig(
        "DEMO: Prepare a social media graphic pack for a fest",
        GigCategory.DESIGN,
        "Design five coordinated announcement graphics for a fictional university fest, with "
        "square "
        "and story variants. Keep text readable at phone size and deliver editable files plus PNG "
        "exports in a shared folder.",
        3600,
        13,
        4,
    ),
    DemoGig(
        "DEMO: Create an Excel reporting dashboard for a club",
        GigCategory.OTHER,
        "Turn a generated sample attendance workbook into a simple Excel dashboard with monthly "
        "totals, category filters and clearly labelled charts. Include a notes tab explaining how "
        "to append future rows; no actual student data is supplied.",
        3000,
        10,
        3,
    ),
    DemoGig(
        "DEMO: Connect a club site to a public event API",
        GigCategory.DEVELOPMENT,
        "Add a small integration that reads public event records from a mock API and displays the "
        "next three events on a fictional club page. Include loading and error states, and keep "
        "any "
        "API key out of the source code.",
        5800,
        20,
        5,
    ),
    DemoGig(
        "DEMO: Write setup documentation for a student project",
        GigCategory.WRITING,
        "Document installation, local configuration and common troubleshooting steps for a "
        "fictional open-source student project. The maintainer will provide a repository and "
        "review "
        "for technical accuracy before completion.",
        2400,
        11,
        3,
    ),
    DemoGig(
        "DEMO: Photograph a mock campus entrepreneurship showcase",
        GigCategory.PHOTOGRAPHY,
        "Cover a fictional half-day showcase with room details, stage moments and posed team "
        "photos. "
        "Deliver around 60 edited images within five days. Participants will be informed that the "
        "photos are for a demonstration brief.",
        6800,
        22,
        4,
    ),
    DemoGig(
        "DEMO: Tutor first-years in SQL and relational modelling",
        GigCategory.TUTORING,
        "Plan two small-group sessions on joins, keys and normalisation using an invented library "
        "database example. Include practice questions and a short recap sheet; this is peer "
        "learning, "
        "not graded assignment completion.",
        2200,
        17,
        2,
    ),
    DemoGig(
        "DEMO: Coordinate volunteers for a mock campus workshop",
        GigCategory.EVENTS,
        "Prepare a volunteer rota and arrival checklist for a fictional one-day workshop. "
        "Coordinate four roles, confirm room setup requirements and provide a short post-event "
        "summary template.",
        2600,
        19,
        3,
    ),
    DemoGig(
        "DEMO: Archived poster design brief for a past club meetup",
        GigCategory.DESIGN,
        "This clearly fictional sample gig is closed so the poster can demonstrate closed-state "
        "display. The mock club meetup has already passed; no work or payment is pending.",
        1800,
        -7,
        2,
        closed=True,
    ),
)

# Desired states are reached through the regular application service after all
# applications have been created as APPLIED. Accepting one closes the gig and
# rejects its other pending applications in the same transaction.
APPLICATIONS = (
    ("DEMO: React landing page for the robotics club", "applicant1", ApplicationStatus.APPLIED),
    ("DEMO: React landing page for the robotics club", "applicant2", ApplicationStatus.APPLIED),
    ("DEMO: Python script to clean a lab survey dataset", "applicant3", ApplicationStatus.APPLIED),
    ("DEMO: Campus event poster and social graphics", "applicant2", ApplicationStatus.REJECTED),
    ("DEMO: Campus event poster and social graphics", "applicant3", ApplicationStatus.APPLIED),
    (
        "DEMO: Improve queries for a student society database",
        "applicant1",
        ApplicationStatus.ACCEPTED,
    ),
    (
        "DEMO: Improve queries for a student society database",
        "applicant2",
        ApplicationStatus.APPLIED,
    ),
    ("DEMO: Connect a club site to a public event API", "applicant3", ApplicationStatus.ACCEPTED),
    ("DEMO: Connect a club site to a public event API", "applicant1", ApplicationStatus.APPLIED),
)


def _assert_local_development_database() -> None:
    parsed = urlsplit(settings.database_url)
    database_name = parsed.path.lstrip("/")
    if (
        settings.environment.lower() != "development"
        or parsed.hostname not in {"localhost", "127.0.0.1"}
        or parsed.port != 5434
        or parsed.username != "campusgig"
        or database_name != "campusgig"
    ):
        raise RuntimeError(
            "Refusing to seed: DATABASE_URL must target the local development database "
            "campusgig on localhost:5434 with ENVIRONMENT=development."
        )


def _get_demo_accounts(db: Session) -> tuple[dict[str, User], int]:
    accounts: dict[str, User] = {}
    missing: list[DemoAccount] = []

    for account in ACCOUNTS:
        user = db.scalar(select(User).where(User.email == account.email))
        if user is not None:
            if (
                user.roll_no != account.roll_no
                or user.dept != account.department
                or user.batch != account.batch
                or user.role is not UserRole.STUDENT
            ):
                raise RuntimeError(
                    f"Refusing to reuse {account.email}: it is not the expected demo account."
                )
            accounts[account.key] = user
            continue

        roll_owner = db.scalar(select(User).where(User.roll_no == account.roll_no))
        if roll_owner is not None:
            raise RuntimeError(
                f"Refusing to create {account.email}: demo roll number {account.roll_no} "
                "is already in use."
            )
        missing.append(account)

    if missing:
        password = getpass("Choose a password for newly created demo accounts: ")
        confirmation = getpass("Confirm the demo account password: ")
        if password != confirmation:
            raise RuntimeError("Passwords did not match; no demo accounts were created.")

        requests = [
            RegisterRequest(
                email=account.email,
                password=password,
                roll_no=account.roll_no,
                dept=account.department,
                batch=account.batch,
            )
            for account in missing
        ]
        for account, request in zip(missing, requests, strict=True):
            accounts[account.key] = auth_service.register(db, request)

    return accounts, len(missing)


def _get_or_create_gigs(db: Session, poster: User) -> tuple[dict[str, Gig], int]:
    now = datetime.now(UTC)
    gigs: dict[str, Gig] = {}
    created = 0
    for spec in GIGS:
        gig = db.scalar(select(Gig).where(Gig.title == spec.title))
        if gig is not None:
            if gig.poster_id != poster.id:
                raise RuntimeError(f"Refusing to reuse {spec.title!r}: it belongs to another user.")
            gigs[spec.title] = gig
            continue

        gig = Gig(
            poster_id=poster.id,
            title=spec.title,
            description=spec.description,
            category=spec.category,
            budget=spec.budget,
            deadline=now + timedelta(days=spec.deadline_days),
            duration_days=spec.duration_days,
            state=GigState.CLOSED if spec.closed else GigState.OPEN,
        )
        db.add(gig)
        db.flush()
        gigs[spec.title] = gig
        created += 1
    db.commit()
    return gigs, created


def _seed_applications(
    db: Session, poster: User, users: dict[str, User], gigs: dict[str, Gig]
) -> tuple[int, int]:
    created = 0
    changed = 0
    rows: list[tuple[Application, ApplicationStatus]] = []

    for gig_title, applicant_key, target_status in APPLICATIONS:
        gig = gigs[gig_title]
        applicant = users[applicant_key]
        application = db.scalar(
            select(Application).where(
                Application.gig_id == gig.id,
                Application.applicant_id == applicant.id,
            )
        )
        if application is None:
            if gig.state is not GigState.OPEN:
                print(f"Skipped new application for already-closed gig: {gig.title}")
                continue
            application = application_service.apply_to_gig(db, gig.id, applicant, None)
            created += 1
        rows.append((application, target_status))

    for application, target_status in rows:
        if target_status is ApplicationStatus.APPLIED:
            continue
        if application.status is not ApplicationStatus.APPLIED:
            continue  # Preserve any status changed by a person after the first seed.
        if (
            application.gig.state is GigState.CLOSED
            and target_status is not ApplicationStatus.ACCEPTED
        ):
            continue
        application_service.set_status(db, application.id, poster, target_status)
        changed += 1

    return created, changed


def seed() -> None:
    _assert_local_development_database()
    with SessionLocal() as db:
        users, users_created = _get_demo_accounts(db)
        gigs, gigs_created = _get_or_create_gigs(db, users["poster"])
        applications_created, statuses_changed = _seed_applications(
            db, users["poster"], users, gigs
        )

    print(
        "Demo seed complete: "
        f"{users_created} accounts, {gigs_created} gigs, "
        f"{applications_created} applications added; "
        f"{statuses_changed} application decisions applied."
    )
    print("Demo login emails:")
    for account in ACCOUNTS:
        print(f"  {account.email}")
    if users_created:
        print("Newly created accounts use the password entered at the secure prompt.")
    else:
        print("Existing account passwords were left unchanged.")


if __name__ == "__main__":
    seed()
