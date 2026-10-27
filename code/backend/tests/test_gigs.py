from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models.gig import Gig, GigCategory, GigState
from app.models.user import User

GIGS = "/api/v1/gigs"


@pytest.fixture
def poster(db) -> User:
    user = User(
        email="poster@thapar.edu",
        password_hash=hash_password("CampusGig123"),
        roll_no="102100777",
        dept="Electronics",
        batch=2025,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def gigs(db, poster) -> list[Gig]:
    now = datetime.now(UTC)
    rows = [
        Gig(
            poster_id=poster.id,
            title="Build a React dashboard",
            description="Frontend work for a small internal tool.",
            category=GigCategory.DEVELOPMENT,
            budget=5000,
            deadline=now + timedelta(days=10),
            state=GigState.OPEN,
            created_at=now - timedelta(hours=1),
        ),
        Gig(
            poster_id=poster.id,
            title="Design a fest poster",
            description="A2 print poster with a matching social kit.",
            category=GigCategory.DESIGN,
            budget=1500,
            deadline=now + timedelta(days=3),
            state=GigState.OPEN,
            created_at=now - timedelta(hours=2),
        ),
        Gig(
            poster_id=poster.id,
            title="Proofread a long thesis",
            description="Language pass plus IEEE formatting.",
            category=GigCategory.WRITING,
            budget=3000,
            deadline=now + timedelta(days=20),
            state=GigState.OPEN,
            created_at=now - timedelta(hours=3),
        ),
        Gig(
            poster_id=poster.id,
            title="Closed archived gig",
            description="Must never be listed.",
            category=GigCategory.OTHER,
            budget=900,
            deadline=now + timedelta(days=5),
            state=GigState.CLOSED,
        ),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def test_listing_returns_only_open_gigs(client, logged_in, gigs):
    logged_in()
    body = client.get(GIGS).json()
    assert body["total"] == 3
    assert all(item["state"] == "OPEN" for item in body["items"])
    assert "Closed archived gig" not in client.get(GIGS).text


def test_listing_never_exposes_poster_email(client, logged_in, gigs):
    logged_in()
    response = client.get(GIGS)
    assert "poster@thapar.edu" not in response.text
    poster = response.json()["items"][0]["poster"]
    assert set(poster) == {"id", "roll_no", "dept", "batch"}


def test_pagination_metadata_and_slicing(client, logged_in, gigs):
    logged_in()
    body = client.get(GIGS, params={"page": 1, "page_size": 2}).json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] == 3
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2

    second = client.get(GIGS, params={"page": 2, "page_size": 2}).json()
    assert len(second["items"]) == 1
    first_ids = {item["id"] for item in body["items"]}
    assert first_ids.isdisjoint({item["id"] for item in second["items"]})


def test_page_size_is_capped(client, logged_in, gigs):
    logged_in()
    assert client.get(GIGS, params={"page_size": 500}).status_code == 422


def test_search_matches_title_and_description(client, logged_in, gigs):
    logged_in()
    by_title = client.get(GIGS, params={"q": "react"}).json()
    assert by_title["total"] == 1
    assert by_title["items"][0]["title"] == "Build a React dashboard"

    by_description = client.get(GIGS, params={"q": "IEEE"}).json()
    assert by_description["total"] == 1


def test_category_filter(client, logged_in, gigs):
    logged_in()
    body = client.get(GIGS, params={"category": "DESIGN"}).json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "DESIGN"


def test_budget_range_filter(client, logged_in, gigs):
    logged_in()
    body = client.get(GIGS, params={"min_budget": 2000, "max_budget": 4000}).json()
    assert [item["title"] for item in body["items"]] == ["Proofread a long thesis"]


def test_inverted_budget_range_is_rejected(client, logged_in, gigs):
    logged_in()
    response = client.get(GIGS, params={"min_budget": 5000, "max_budget": 100})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_query"


def test_deadline_filter(client, logged_in, gigs):
    logged_in()
    cutoff = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    body = client.get(GIGS, params={"deadline_before": cutoff}).json()
    assert [item["title"] for item in body["items"]] == ["Design a fest poster"]


def test_sorting(client, logged_in, gigs):
    logged_in()
    ascending = client.get(GIGS, params={"sort": "budget_asc"}).json()["items"]
    assert [float(item["budget"]) for item in ascending] == [1500.0, 3000.0, 5000.0]

    descending = client.get(GIGS, params={"sort": "budget_desc"}).json()["items"]
    assert [float(item["budget"]) for item in descending] == [5000.0, 3000.0, 1500.0]


def test_invalid_query_parameters_are_rejected(client, logged_in, gigs):
    logged_in()
    assert client.get(GIGS, params={"page": 0}).status_code == 422
    assert client.get(GIGS, params={"category": "NOT_A_CATEGORY"}).status_code == 422
    assert client.get(GIGS, params={"sort": "random"}).status_code == 422
    assert client.get(GIGS, params={"min_budget": -5}).status_code == 422


def test_empty_result_is_a_valid_page(client, logged_in, gigs):
    logged_in()
    body = client.get(GIGS, params={"q": "nothing matches this"}).json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["total_pages"] == 1


def test_gig_details(client, logged_in, gigs, db):
    logged_in()
    gig_id = str(db.scalar(select(Gig.id).where(Gig.title == "Build a React dashboard")))
    response = client.get(f"{GIGS}/{gig_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Build a React dashboard"
    assert body["description"].startswith("Frontend work")
    assert set(body["poster"]) == {"id", "roll_no", "dept", "batch"}
    assert "poster@thapar.edu" not in response.text


def test_missing_gig_is_404(client, logged_in, gigs):
    logged_in()
    response = client.get(f"{GIGS}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "gig_not_found"


def test_closed_gig_is_not_reachable_by_id(client, logged_in, gigs, db):
    logged_in()
    gig_id = db.scalar(select(Gig.id).where(Gig.state == GigState.CLOSED))
    assert client.get(f"{GIGS}/{gig_id}").status_code == 404


def test_malformed_gig_id_is_rejected(client, logged_in, gigs):
    logged_in()
    assert client.get(f"{GIGS}/not-a-uuid").status_code == 422
