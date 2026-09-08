"""Development seed data.

Run with:  python -m app.seeds.seed_gigs

Refuses to run against a production environment. Never imported by the app.
"""

import random
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.gig import Gig, GigCategory, GigState
from app.models.user import User

SEED_PASSWORD = "SeedPass123"

POSTERS = [
    ("aarav.mehta@thapar.edu", "102103001", "Computer Science", 2025),
    ("isha.kapoor@thapar.edu", "102103002", "Electronics", 2024),
    ("rohan.gill@thapar.edu", "102103003", "Mechanical", 2026),
    ("neha.sharma@thapar.edu", "102103004", "Chemical", 2025),
]

GIGS = [
    (
        "Build a React landing page for our robotics club",
        GigCategory.DEVELOPMENT,
        "We need a single-page site for the robotics club with a hero section, an events "
        "timeline, a sponsors strip and a contact form. Design is already done in Figma; "
        "we need it built responsively and deployed. React or plain HTML/CSS both fine.",
        4500,
        12,
    ),
    (
        "Poster and social media kit for Saturnalia",
        GigCategory.DESIGN,
        "Looking for a designer to produce one A2 print poster plus a matching set of six "
        "Instagram posts and three story templates for our cultural fest. Brand colours and "
        "the logo will be shared. Two revision rounds included.",
        2500,
        9,
    ),
    (
        "Weekly Data Structures tutoring - second year",
        GigCategory.TUTORING,
        "Need help getting through trees, graphs and dynamic programming before end-sems. "
        "Two sessions a week, one hour each, in the library or over a call. Looking for "
        "someone who has already cleared the course with a good grade.",
        3000,
        20,
    ),
    (
        "Proofread and format an 80-page thesis",
        GigCategory.WRITING,
        "Mechanical engineering thesis needs a careful language pass plus consistent IEEE "
        "formatting for citations, figure captions and the table of contents. Document is "
        "in Word. Track changes please.",
        3500,
        7,
    ),
    (
        "Event photography for the inter-hostel sports meet",
        GigCategory.PHOTOGRAPHY,
        "Two-day sports meet, roughly six hours of shooting per day across the ground and "
        "the indoor court. Need around 150 edited photos delivered within a week. You must "
        "have your own camera body and a telephoto lens.",
        6000,
        15,
    ),
    (
        "Help setting up a MATLAB simulation for control systems",
        GigCategory.ACADEMIC_HELP,
        "Stuck on a Simulink model for a PID controller assignment. Need someone to sit with "
        "me for a couple of sessions, walk through the block diagram and help debug why the "
        "step response is oscillating.",
        1200,
        5,
    ),
    (
        "Volunteer coordination app for the NSS chapter",
        GigCategory.DEVELOPMENT,
        "Small internal tool: volunteers sign up for drives, coordinators mark attendance, "
        "and we export a monthly report. Any stack is fine as long as it is easy to hand "
        "over. Hosting will be handled by us.",
        8000,
        30,
    ),
    (
        "Compere and run the schedule for a departmental tech talk",
        GigCategory.EVENTS,
        "Half-day event with four speakers. Need someone confident on stage to introduce "
        "speakers, keep the schedule tight, and run the Q and A. Script will be provided a "
        "week in advance.",
        1500,
        11,
    ),
    (
        "Illustrate ten spot drawings for the campus magazine",
        GigCategory.DESIGN,
        "Black and white line illustrations, roughly postcard sized, to sit alongside student "
        "essays. We will share the essays and a rough brief for each. Consistent style across "
        "all ten matters more than complexity.",
        4000,
        18,
    ),
    (
        "Transcribe and summarise twelve recorded lectures",
        GigCategory.WRITING,
        "Twelve recordings, about fifty minutes each. Need a clean transcript plus a one-page "
        "summary of each lecture with the key formulas pulled out. Accuracy on technical terms "
        "is the main thing.",
        5000,
        14,
    ),
    (
        "Fix the CSS on our hostel mess feedback form",
        GigCategory.DEVELOPMENT,
        "The form works but looks broken on phones - overlapping labels, buttons off screen. "
        "Small job, should be an evening's work for someone who knows flexbox. Codebase is "
        "plain HTML and Bootstrap.",
        900,
        4,
    ),
    (
        "Statistics doubt-clearing before the mid-semester",
        GigCategory.ACADEMIC_HELP,
        "Hypothesis testing and regression are not clicking. Looking for two or three focused "
        "sessions with worked examples from previous years' papers.",
        1800,
        6,
    ),
    (
        "Shoot and edit a two-minute club recruitment video",
        GigCategory.PHOTOGRAPHY,
        "Need a short recruitment film for the entrepreneurship cell: some b-roll around "
        "campus, three short interviews, background music and subtitles. Script and shot list "
        "will be ready before the shoot.",
        7000,
        21,
    ),
    (
        "Design a pitch deck for our student startup",
        GigCategory.DESIGN,
        "Fifteen slides, content is written already. Need a clean visual system, simple charts "
        "and consistent typography. Google Slides or PowerPoint, editable file handed over at "
        "the end.",
        3200,
        10,
    ),
    (
        "Run a two-session Git and GitHub workshop for first years",
        GigCategory.EVENTS,
        "Practical introduction to version control for about forty first-year students. Two "
        "sessions of ninety minutes. Slides and exercises will need to be prepared; we can "
        "provide the lab.",
        2800,
        16,
    ),
    (
        "Miscellaneous help moving lab equipment",
        GigCategory.OTHER,
        "One afternoon of careful work moving instruments between two labs, packing and "
        "labelling as we go. Two people needed, so apply with a partner if you have one.",
        1000,
        3,
    ),
]


def _get_or_create_poster(db, email: str, roll_no: str, dept: str, batch: int) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user
    user = User(
        email=email,
        password_hash=hash_password(SEED_PASSWORD),
        roll_no=roll_no,
        dept=dept,
        batch=batch,
    )
    db.add(user)
    db.flush()
    return user


def seed() -> None:
    if settings.is_production:
        sys.exit("Refusing to seed development data into a production environment.")

    random.seed(20260908)  # stable output across runs
    now = datetime.now(UTC)

    with SessionLocal() as db:
        posters = [_get_or_create_poster(db, *poster) for poster in POSTERS]

        existing = {title for title in db.scalars(select(Gig.title))}
        created = 0
        for index, (title, category, description, budget, deadline_days) in enumerate(GIGS):
            if title in existing:
                continue
            db.add(
                Gig(
                    poster_id=posters[index % len(posters)].id,
                    title=title,
                    description=description,
                    category=category,
                    budget=budget,
                    deadline=now + timedelta(days=deadline_days),
                    state=GigState.OPEN,
                    created_at=now - timedelta(hours=index * 7 + 1),
                )
            )
            created += 1

        # One closed gig so the "only OPEN gigs are listed" filter is observably
        # doing something rather than passing by default.
        closed_title = "Archived: help wiring the old lab display"
        if closed_title not in existing:
            db.add(
                Gig(
                    poster_id=posters[0].id,
                    title=closed_title,
                    description="This gig is closed and must never appear in the dashboard.",
                    category=GigCategory.OTHER,
                    budget=500,
                    deadline=now + timedelta(days=2),
                    state=GigState.CLOSED,
                )
            )
            created += 1

        db.commit()

    print(f"Seeded {len(posters)} posters and {created} gigs.")
    print(f"Seed accounts use the password: {SEED_PASSWORD}")


if __name__ == "__main__":
    seed()
