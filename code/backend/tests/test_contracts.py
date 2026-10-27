import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError

from app.core.errors import InvalidStatusTransition
from app.core.security import hash_password
from app.models.application import Application, ApplicationStatus
from app.models.contract import Contract, ContractStatus, ContractStatusHistory
from app.models.gig import Gig, GigState
from app.models.user import User
from app.services import application_service, contract_service

GIGS = "/api/v1/gigs"
CONTRACTS = "/api/v1/contracts"
PASSWORD = "CampusGig123"


def make_student(db, email: str, roll_no: str) -> User:
    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        roll_no=roll_no,
        dept="Computer Science",
        batch=2026,
    )
    db.add(user)
    db.commit()
    return user


def make_gig(client, *, title: str = "Create a campus event website") -> dict:
    response = client.post(
        GIGS,
        json={
            "title": title,
            "description": "Build a responsive event page and document how to update it.",
            "category": "DEVELOPMENT",
            "budget": "1234.56",
            "deadline": (datetime.now(UTC) + timedelta(days=18)).isoformat(),
            "duration_days": 4,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def make_application(db, gig_id, applicant: User) -> Application:
    application = Application(
        gig_id=gig_id,
        applicant_id=applicant.id,
        message="I can complete this within the stated schedule.",
    )
    db.add(application)
    db.commit()
    return application


def test_award_creates_frozen_contract_history_and_rejects_pending(client, logged_in, db):
    poster_data = logged_in()
    poster = db.scalar(select(User).where(User.email == poster_data["email"]))
    gig_data = make_gig(client)
    gig = db.get(Gig, uuid.UUID(gig_data["id"]))
    worker = make_student(db, "worker@thapar.edu", "102100801")
    other = make_student(db, "other-worker@thapar.edu", "102100802")
    selected = make_application(db, gig.id, worker)
    pending = make_application(db, gig.id, other)

    accepted = client.patch(f"/api/v1/applications/{selected.id}", json={"status": "ACCEPTED"})
    assert accepted.status_code == 200

    contract = db.scalar(select(Contract))
    history = db.scalars(select(ContractStatusHistory)).all()
    db.refresh(gig)
    db.refresh(pending)
    assert contract is not None
    assert contract.gig_id == gig.id
    assert contract.application_id == selected.id
    assert contract.worker_id == worker.id
    assert contract.poster.id == poster.id
    assert contract.amount_paise == 123456
    assert contract.gig_title == gig_data["title"]
    assert contract.gig_description == gig_data["description"]
    assert contract.deadline == gig.deadline
    assert contract.status is ContractStatus.ACCEPTED
    assert gig.state is GigState.CLOSED
    assert pending.status is ApplicationStatus.REJECTED
    assert len(history) == 1
    assert history[0].previous_status is ContractStatus.OPEN
    assert history[0].new_status is ContractStatus.ACCEPTED
    assert history[0].actor_id == poster.id

    repeated = client.patch(f"/api/v1/applications/{selected.id}", json={"status": "ACCEPTED"})
    assert repeated.status_code == 409
    assert db.scalar(select(func.count()).select_from(Contract)) == 1

    # Later edits to the source gig cannot change the contract's recorded terms.
    gig.title = "Edited after award"
    gig.description = "A different description after award."
    gig.budget = Decimal("9999.00")
    db.commit()
    detail = client.get(f"{CONTRACTS}/{contract.id}")
    assert detail.status_code == 200
    assert detail.json()["gig_title"] == "Create a campus event website"
    assert detail.json()["amount_paise"] == 123456
    assert detail.json()["history"][0]["new_status"] == "ACCEPTED"


def test_contract_creation_failure_rolls_back_the_award(client, logged_in, db, monkeypatch):
    poster_data = logged_in()
    poster = db.scalar(select(User).where(User.email == poster_data["email"]))
    gig_data = make_gig(client)
    worker = make_student(db, "worker@thapar.edu", "102100801")
    application = make_application(db, gig_data["id"], worker)

    def fail_creation(*_args, **_kwargs):
        raise RuntimeError("contract write failed")

    monkeypatch.setattr(contract_service, "create_for_award", fail_creation)
    with pytest.raises(RuntimeError, match="contract write failed"):
        application_service.set_status(db, application.id, poster, ApplicationStatus.ACCEPTED)

    db.expire_all()
    assert db.get(Application, application.id).status is ApplicationStatus.APPLIED
    assert db.get(Gig, uuid.UUID(gig_data["id"])).state is GigState.OPEN
    assert db.scalar(select(func.count()).select_from(Contract)) == 0
    assert db.scalar(select(func.count()).select_from(ContractStatusHistory)) == 0


def test_contract_access_is_limited_to_poster_and_selected_worker(client, logged_in, db):
    logged_in()
    gig_data = make_gig(client)
    worker = make_student(db, "worker@thapar.edu", "102100801")
    application = make_application(db, gig_data["id"], worker)
    assert (
        client.patch(
            f"/api/v1/applications/{application.id}", json={"status": "ACCEPTED"}
        ).status_code
        == 200
    )
    contract = db.scalar(select(Contract))

    poster_list = client.get(CONTRACTS)
    assert poster_list.status_code == 200
    assert poster_list.json()["total"] == 1
    assert poster_list.json()["items"][0]["id"] == str(contract.id)
    assert client.get(f"{CONTRACTS}/{contract.id}").status_code == 200
    assert client.get(f"{CONTRACTS}?page=2&page_size=1").json()["items"] == []
    assert client.get(f"{CONTRACTS}?page_size=51").status_code == 422

    client.post("/api/v1/auth/logout")
    assert client.get(CONTRACTS).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": worker.email, "password": PASSWORD}
        ).status_code
        == 200
    )
    assert client.get(CONTRACTS).json()["total"] == 1
    assert client.get(f"{CONTRACTS}/{contract.id}").status_code == 200

    client.post("/api/v1/auth/logout")
    make_student(db, "unrelated@thapar.edu", "102100803")
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "unrelated@thapar.edu", "password": PASSWORD},
        ).status_code
        == 200
    )
    assert client.get(CONTRACTS).json()["total"] == 0
    assert client.get(f"{CONTRACTS}/{contract.id}").status_code == 404


def test_contract_history_rejects_updates_and_deletes(client, logged_in, db):
    logged_in()
    gig_data = make_gig(client)
    worker = make_student(db, "worker@thapar.edu", "102100801")
    application = make_application(db, gig_data["id"], worker)
    assert (
        client.patch(
            f"/api/v1/applications/{application.id}", json={"status": "ACCEPTED"}
        ).status_code
        == 200
    )
    history = db.scalar(select(ContractStatusHistory))

    history.new_status = ContractStatus.RELEASED
    with pytest.raises(DBAPIError, match="append-only"):
        db.commit()
    db.rollback()

    db.delete(history)
    with pytest.raises(DBAPIError, match="append-only"):
        db.commit()
    db.rollback()
    assert db.scalar(select(func.count()).select_from(ContractStatusHistory)) == 1


def test_contract_cannot_be_created_for_an_unaccepted_application(client, logged_in, db):
    poster_data = logged_in()
    poster = db.scalar(select(User).where(User.email == poster_data["email"]))
    gig_data = make_gig(client)
    gig = db.get(Gig, uuid.UUID(gig_data["id"]))
    worker = make_student(db, "worker@thapar.edu", "102100801")
    application = make_application(db, gig.id, worker)

    with pytest.raises(InvalidStatusTransition):
        contract_service.create_for_award(db, gig, application, poster)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Contract)) == 0
