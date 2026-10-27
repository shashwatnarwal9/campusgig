from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

from sqlalchemy import select

from app.core.errors import InvalidStatusTransition
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.application import Application, ApplicationStatus
from app.models.gig import Gig, GigState
from app.models.user import User
from app.repositories import application_repo
from app.services.application_service import set_status

GIGS = "/api/v1/gigs"
APPLICATIONS = "/api/v1/applications"


def error_code(response) -> str:
    return response.json()["detail"]["code"]


def gig_payload(**overrides) -> dict:
    payload = {
        "title": "Build a small internal dashboard",
        "description": "A short brief that is comfortably past the minimum length for a gig.",
        "category": "DEVELOPMENT",
        "budget": "4500.00",
        "deadline": (datetime.now(UTC) + timedelta(days=14)).isoformat(),
        "duration_days": 5,
    }
    payload.update(overrides)
    return payload


def make_other_student(db, *, email="other@thapar.edu", roll_no="102100888") -> User:
    user = User(
        email=email,
        password_hash=hash_password("CampusGig123"),
        roll_no=roll_no,
        dept="Electronics",
        batch=2025,
    )
    db.add(user)
    db.commit()
    return user


# --- posting ---------------------------------------------------------------


def test_post_a_gig(client, logged_in, db):
    logged_in()
    response = client.post(GIGS, json=gig_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Build a small internal dashboard"
    assert body["state"] == "OPEN"
    assert body["duration_days"] == 5
    assert body["poster"]["roll_no"] == "102103999"


def test_posted_gig_appears_in_the_listing(client, logged_in):
    logged_in()
    client.post(GIGS, json=gig_payload())
    listing = client.get(GIGS).json()
    assert listing["total"] == 1


def test_poster_is_the_session_user_not_the_payload(client, logged_in, db):
    logged_in()
    intruder = make_other_student(db)
    response = client.post(GIGS, json={**gig_payload(), "poster_id": str(intruder.id)})
    assert response.status_code == 201
    gig = db.scalar(select(Gig))
    assert gig.poster_id != intruder.id


def test_state_cannot_be_set_through_the_payload(client, logged_in, db):
    logged_in()
    client.post(GIGS, json={**gig_payload(), "state": "CLOSED"})
    assert db.scalar(select(Gig.state)) is GigState.OPEN


def test_posting_requires_authentication(client):
    assert client.post(GIGS, json=gig_payload()).status_code == 401


def test_invalid_gig_payloads_are_rejected(client, logged_in):
    logged_in()
    bad = [
        {"title": "abc"},
        {"description": "too short"},
        {"budget": "0"},
        {"budget": "-10"},
        {"category": "NOT_A_CATEGORY"},
        {"deadline": (datetime.now(UTC) - timedelta(days=1)).isoformat()},
        {"duration_days": 0},
        {"duration_days": 900},
    ]
    for overrides in bad:
        assert client.post(GIGS, json=gig_payload(**overrides)).status_code == 422, overrides


def test_my_gigs_lists_only_mine(client, logged_in, db):
    logged_in()
    client.post(GIGS, json=gig_payload())

    other = make_other_student(db)
    db.add(
        Gig(
            poster_id=other.id,
            title="Someone else's gig",
            description="Not mine.",
            category="DESIGN",
            budget=100,
            deadline=datetime.now(UTC) + timedelta(days=3),
        )
    )
    db.commit()

    mine = client.get(f"{GIGS}/mine").json()
    assert [g["title"] for g in mine["items"]] == ["Build a small internal dashboard"]
    assert mine["total"] == 1
    assert mine["page"] == 1


def test_my_gigs_paginates_with_total_and_page_boundaries(client, logged_in):
    logged_in()
    for index in range(3):
        assert client.post(GIGS, json=gig_payload(title=f"Gig {index}")).status_code == 201

    first = client.get(f"{GIGS}/mine?page=1&page_size=2").json()
    second = client.get(f"{GIGS}/mine?page=2&page_size=2").json()
    beyond = client.get(f"{GIGS}/mine?page=3&page_size=2").json()

    assert first["total"] == second["total"] == beyond["total"] == 3
    assert first["total_pages"] == 2
    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert beyond["items"] == []


def test_my_gigs_rejects_page_size_above_maximum(client, logged_in):
    logged_in()
    assert client.get(f"{GIGS}/mine?page_size=51").status_code == 422


# --- applying --------------------------------------------------------------


def _gig_by_other(client, db) -> str:
    """A gig posted by someone else, so the session user may apply to it."""
    other = make_other_student(db)
    gig = Gig(
        poster_id=other.id,
        title="Proofread a long thesis",
        description="Language pass plus formatting.",
        category="WRITING",
        budget=3000,
        deadline=datetime.now(UTC) + timedelta(days=9),
    )
    db.add(gig)
    db.commit()
    return str(gig.id)


def test_apply_to_a_gig(client, logged_in, db):
    logged_in()
    gig_id = _gig_by_other(client, db)
    response = client.post(f"{GIGS}/{gig_id}/apply", json={"message": "I can start this week."})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "APPLIED"
    assert body["gig"]["id"] == gig_id


def test_cannot_apply_twice(client, logged_in, db):
    logged_in()
    gig_id = _gig_by_other(client, db)
    assert client.post(f"{GIGS}/{gig_id}/apply", json={}).status_code == 201
    second = client.post(f"{GIGS}/{gig_id}/apply", json={})
    assert second.status_code == 409
    assert error_code(second) == "already_applied"


def test_cannot_apply_to_own_gig(client, logged_in):
    logged_in()
    gig_id = client.post(GIGS, json=gig_payload()).json()["id"]
    response = client.post(f"{GIGS}/{gig_id}/apply", json={})
    assert response.status_code == 400
    assert error_code(response) == "cannot_apply_to_own_gig"


def test_cannot_apply_to_a_closed_gig(client, logged_in, db):
    logged_in()
    gig_id = _gig_by_other(client, db)
    db.execute(select(Gig))
    gig = db.get(Gig, gig_id)
    gig.state = GigState.CLOSED
    db.commit()

    response = client.post(f"{GIGS}/{gig_id}/apply", json={})
    assert response.status_code == 409
    assert error_code(response) == "gig_not_open"


def test_applying_requires_authentication(client, db):
    gig_id = _gig_by_other(client, db)
    assert client.post(f"{GIGS}/{gig_id}/apply", json={}).status_code == 401


# --- the applied-gigs report ----------------------------------------------


def test_my_applications_summary_starts_empty(client, logged_in):
    logged_in()
    body = client.get(f"{APPLICATIONS}/me").json()
    assert body["items"] == []
    assert body["summary"]["total"] == 0
    assert float(body["summary"]["earned"]) == 0.0
    assert body["total"] == 0
    assert body["total_pages"] == 1


def test_my_applications_paginates_and_filters_without_changing_summary(client, logged_in, db):
    logged_in()
    other = make_other_student(db)
    for index in range(3):
        gig = Gig(
            poster_id=other.id,
            title=f"Proofread document {index}",
            description="Language pass plus formatting.",
            category="WRITING",
            budget=3000,
            deadline=datetime.now(UTC) + timedelta(days=9),
        )
        db.add(gig)
        db.commit()
        assert client.post(
            f"{GIGS}/{gig.id}/apply", json={"message": f"app {index}"}
        ).status_code == 201

    # Keep the summary global while the listing count reflects the selected status.
    applications = list(db.scalars(select(Application).order_by(Application.created_at)))
    applications[0].status = ApplicationStatus.ACCEPTED
    db.commit()

    first = client.get(f"{APPLICATIONS}/me?page=1&page_size=1").json()
    second = client.get(f"{APPLICATIONS}/me?page=2&page_size=1").json()
    filtered = client.get(f"{APPLICATIONS}/me?page_size=1&status=APPLIED").json()
    beyond = client.get(f"{APPLICATIONS}/me?page=4&page_size=1").json()

    assert first["summary"]["total"] == 3
    assert first["total"] == second["total"] == 3
    assert first["total_pages"] == 3
    assert len(first["items"]) == len(second["items"]) == 1
    assert filtered["summary"]["total"] == 3
    assert filtered["total"] == 2
    assert all(item["status"] == "APPLIED" for item in filtered["items"])
    assert beyond["items"] == []
    assert beyond["total"] == 3


def test_my_applications_rejects_page_size_above_maximum(client, logged_in):
    logged_in()
    assert client.get(f"{APPLICATIONS}/me?page_size=51").status_code == 422


def test_my_applications_reports_totals(client, logged_in, db):
    logged_in()
    gig_id = _gig_by_other(client, db)
    client.post(f"{GIGS}/{gig_id}/apply", json={})

    body = client.get(f"{APPLICATIONS}/me").json()
    assert body["summary"]["total"] == 1
    assert body["summary"]["applied"] == 1
    assert float(body["summary"]["earned"]) == 0.0
    assert body["items"][0]["gig"]["title"] == "Proofread a long thesis"


def test_earnings_count_completed_work_only(client, logged_in, db):
    logged_in()
    gig_id = _gig_by_other(client, db)
    client.post(f"{GIGS}/{gig_id}/apply", json={})

    application = db.scalar(select(Application))
    application.status = ApplicationStatus.ACCEPTED
    db.commit()
    summary = client.get(f"{APPLICATIONS}/me").json()["summary"]
    assert float(summary["earned"]) == 0.0
    assert float(summary["in_progress_value"]) == 3000.0

    application.status = ApplicationStatus.COMPLETED
    db.commit()
    summary = client.get(f"{APPLICATIONS}/me").json()["summary"]
    assert float(summary["earned"]) == 3000.0
    assert float(summary["in_progress_value"]) == 0.0


# --- poster-side status changes -------------------------------------------


def test_poster_sees_applicants_and_can_accept(client, logged_in, db):
    logged_in()
    gig_id = client.post(GIGS, json=gig_payload()).json()["id"]

    applicant = make_other_student(db)
    db.add(Application(gig_id=gig_id, applicant_id=applicant.id))
    db.commit()

    listed = client.get(f"{GIGS}/{gig_id}/applications").json()
    assert len(listed) == 1
    assert listed[0]["applicant"]["roll_no"] == "102100888"
    assert "email" not in listed[0]["applicant"]

    application_id = listed[0]["id"]
    response = client.patch(f"{APPLICATIONS}/{application_id}", json={"status": "ACCEPTED"})
    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"


def test_accepting_closes_the_gig_and_rejects_the_rest(client, logged_in, db):
    logged_in()
    gig_id = client.post(GIGS, json=gig_payload()).json()["id"]

    first = make_other_student(db)
    second = make_other_student(db, email="second@thapar.edu", roll_no="102100999")
    db.add_all(
        [
            Application(gig_id=gig_id, applicant_id=first.id),
            Application(gig_id=gig_id, applicant_id=second.id),
        ]
    )
    db.commit()

    winner = db.scalar(select(Application).where(Application.applicant_id == first.id))
    client.patch(f"{APPLICATIONS}/{winner.id}", json={"status": "ACCEPTED"})

    db.expire_all()
    assert db.get(Gig, gig_id).state is GigState.CLOSED
    loser = db.scalar(select(Application).where(Application.applicant_id == second.id))
    assert loser.status is ApplicationStatus.REJECTED
    # and it drops off the public listing
    assert client.get(GIGS).json()["total"] == 0


def test_concurrent_acceptance_has_only_one_winner(client, logged_in, db, monkeypatch):
    logged_in()
    poster = db.scalar(select(User))
    gig_id = client.post(GIGS, json=gig_payload()).json()["id"]

    first = make_other_student(db)
    second = make_other_student(db, email="second@thapar.edu", roll_no="102100999")
    db.add_all(
        [
            Application(gig_id=gig_id, applicant_id=first.id),
            Application(gig_id=gig_id, applicant_id=second.id),
        ]
    )
    db.commit()
    application_ids = {
        str(application.id)
        for application in db.scalars(select(Application)).all()
    }

    # Ensure both requests have read APPLIED before either attempts the update.
    both_read = Barrier(2)
    original_get = application_repo.get

    def get_after_both_read(session, application_id):
        application = original_get(session, application_id)
        if str(application_id) in application_ids:
            both_read.wait(timeout=10)
        return application

    monkeypatch.setattr(application_repo, "get", get_after_both_read)

    def accept(application_id):
        with SessionLocal() as session:
            owner = session.get(User, poster.id)
            try:
                set_status(session, application_id, owner, ApplicationStatus.ACCEPTED)
                return "accepted"
            except InvalidStatusTransition:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(accept, application_ids))

    assert sorted(outcomes) == ["accepted", "conflict"]
    db.expire_all()
    statuses = db.scalars(
        select(Application.status).where(Application.gig_id == gig_id)
    ).all()
    assert statuses.count(ApplicationStatus.ACCEPTED) == 1
    assert statuses.count(ApplicationStatus.REJECTED) == 1
    assert db.get(Gig, gig_id).state is GigState.CLOSED


def test_only_the_poster_can_change_status(client, logged_in, db):
    """The applicant must not be able to promote their own application."""
    logged_in()
    gig_id = _gig_by_other(client, db)
    application_id = client.post(f"{GIGS}/{gig_id}/apply", json={}).json()["id"]

    response = client.patch(f"{APPLICATIONS}/{application_id}", json={"status": "COMPLETED"})
    assert response.status_code == 403
    assert error_code(response) == "not_gig_owner"


def test_only_the_poster_can_list_applicants(client, logged_in, db):
    logged_in()
    gig_id = _gig_by_other(client, db)
    response = client.get(f"{GIGS}/{gig_id}/applications")
    assert response.status_code == 403
    assert error_code(response) == "not_gig_owner"


def test_invalid_status_transitions_are_refused(client, logged_in, db):
    logged_in()
    gig_id = client.post(GIGS, json=gig_payload()).json()["id"]
    applicant = make_other_student(db)
    db.add(Application(gig_id=gig_id, applicant_id=applicant.id))
    db.commit()
    application = db.scalar(select(Application))

    # APPLIED cannot jump straight to COMPLETED
    response = client.patch(f"{APPLICATIONS}/{application.id}", json={"status": "COMPLETED"})
    assert response.status_code == 409
    assert error_code(response) == "invalid_status_transition"

    client.patch(f"{APPLICATIONS}/{application.id}", json={"status": "ACCEPTED"})
    # and a decided application cannot be reopened
    again = client.patch(f"{APPLICATIONS}/{application.id}", json={"status": "REJECTED"})
    assert again.status_code == 409


def test_missing_application_is_404(client, logged_in):
    logged_in()
    response = client.patch(
        f"{APPLICATIONS}/00000000-0000-0000-0000-000000000000", json={"status": "ACCEPTED"}
    )
    assert response.status_code == 404
    assert error_code(response) == "application_not_found"


def test_poster_can_still_see_their_own_closed_gig(client, logged_in, db):
    logged_in()
    gig_id = client.post(GIGS, json=gig_payload()).json()["id"]
    gig = db.get(Gig, gig_id)
    gig.state = GigState.CLOSED
    db.commit()

    assert client.get(f"{GIGS}/{gig_id}").status_code == 200
