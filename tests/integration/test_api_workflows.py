"""Integration tests (IT-01 to IT-10).

These send real HTTP requests to the API, through the routers, services and
repositories, into a fresh SQLite test database seeded with the demo data.
"""
import argparse

import pytest
from fastapi.testclient import TestClient


SOFTWARE_DEVELOPER_POSITION = 2  # department: Computer Science -> coord_compsci


@pytest.fixture
def client(resume_dir, pdf_bytes):
    """A test client on a freshly dropped, recreated and seeded database."""
    from app.cli import cmd_seed
    from app.database import create_db_and_tables, drop_all
    from app.main import app

    drop_all()
    create_db_and_tables()
    cmd_seed(argparse.Namespace())

    with TestClient(app) as test_client:
        test_client.pdf_bytes = pdf_bytes
        yield test_client


def login(client, username, password):
    response = client.post("/api/login", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def apply(client, headers, position_id=SOFTWARE_DEVELOPER_POSITION):
    return client.post(
        "/api/applications",
        headers=headers,
        data={
            "position_id": position_id,
            "first_name": "Bob",
            "last_name": "Sterling",
            "major": "Computer Science",
            "graduation_year": 2027,
            "cover_letter": "I would love to build internal tools.",
        },
        files={"resume_file": ("cv.pdf", client.pdf_bytes, "application/pdf")},
    )


def change_status(client, headers, application_id, new_status, reason):
    return client.patch(
        f"/api/review/applications/{application_id}/status",
        headers=headers,
        data={"new_status": new_status, "reason": reason},
    )


def test_it01_login(client):
    good = client.post("/api/login", data={"username": "bob", "password": "bobpass"})
    assert good.status_code == 200
    assert good.json()["access_token"]
    assert good.json()["role"] == "student"

    bad = client.post("/api/login", data={"username": "bob", "password": "wrongpass"})
    assert bad.status_code == 401


def test_it02_student_lists_open_positions(client):
    bob = login(client, "bob", "bobpass")

    response = client.get("/api/positions", headers=bob)

    assert response.status_code == 200
    positions = response.json()
    assert len(positions) == 6
    titles = {p["title"] for p in positions}
    assert "Software Developer Intern" in titles
    for field in ("position_id", "title", "company", "department"):
        assert field in positions[0]


def test_it03_student_applies(client):
    bob = login(client, "bob", "bobpass")

    created = apply(client, bob)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "pending"
    assert body["semester"] == "Summer 2027"

    mine = client.get("/api/applications", headers=bob)
    assert mine.status_code == 200
    assert [a["application_id"] for a in mine.json()] == [body["application_id"]]


def test_it04_duplicate_application_rejected(client):
    bob = login(client, "bob", "bobpass")
    assert apply(client, bob).status_code == 201

    second = apply(client, bob)

    assert second.status_code == 400
    assert second.json()["detail"] == "You have already applied for this internship."


def test_it05_application_routed_to_department_coordinator(client):
    bob = login(client, "bob", "bobpass")
    application_id = apply(client, bob).json()["application_id"]

    compsci = login(client, "coord_compsci", "coordpass")
    queue = client.get("/api/review/applications", headers=compsci)
    assert queue.status_code == 200
    assert application_id in [a["application_id"] for a in queue.json()]

    business = login(client, "coord_business", "coordpass")
    other_queue = client.get("/api/review/applications", headers=business)
    assert other_queue.status_code == 200
    assert application_id not in [a["application_id"] for a in other_queue.json()]


def test_it06_coordinator_accepts_with_reason(client):
    bob = login(client, "bob", "bobpass")
    application_id = apply(client, bob).json()["application_id"]
    compsci = login(client, "coord_compsci", "coordpass")

    changed = change_status(client, compsci, application_id, "accepted", "Strong candidate")
    assert changed.status_code == 200
    assert changed.json()["status"] == "accepted"

    detail = client.get(f"/api/review/applications/{application_id}", headers=compsci)
    assert detail.status_code == 200
    history = detail.json()["history"]
    assert len(history) == 1
    assert history[0]["previous_status"] == "pending"
    assert history[0]["new_status"] == "accepted"
    assert history[0]["reason"] == "Strong candidate"


def test_it07_revoked_is_final(client):
    bob = login(client, "bob", "bobpass")
    application_id = apply(client, bob).json()["application_id"]
    compsci = login(client, "coord_compsci", "coordpass")
    assert change_status(client, compsci, application_id, "accepted", "Strong").status_code == 200

    revoked = change_status(client, compsci, application_id, "revoked", "Failed check")
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    again = change_status(client, compsci, application_id, "accepted", "Reconsidered")
    assert again.status_code == 400
    assert again.json()["detail"] == "This status change is not allowed."


def test_it08_student_tracks_updated_status(client):
    bob = login(client, "bob", "bobpass")
    application_id = apply(client, bob).json()["application_id"]
    compsci = login(client, "coord_compsci", "coordpass")
    change_status(client, compsci, application_id, "accepted", "Strong candidate")

    mine = client.get("/api/applications", headers=bob)

    assert mine.status_code == 200
    [application] = mine.json()
    assert application["application_id"] == application_id
    assert application["status"] == "accepted"


def test_it09_student_views_details_with_reason(client):
    bob = login(client, "bob", "bobpass")
    application_id = apply(client, bob).json()["application_id"]
    compsci = login(client, "coord_compsci", "coordpass")
    change_status(client, compsci, application_id, "accepted", "Strong candidate")

    detail = client.get(f"/api/applications/{application_id}", headers=bob)
    assert detail.status_code == 200
    assert detail.json()["status"] == "accepted"
    assert detail.json()["history"][0]["reason"] == "Strong candidate"

    missing = client.get("/api/applications/999", headers=bob)
    assert missing.status_code == 404


def test_it10_authorization(client):
    bob = login(client, "bob", "bobpass")
    compsci = login(client, "coord_compsci", "coordpass")

    assert client.get("/api/review/applications", headers=bob).status_code == 403
    assert client.get("/api/applications", headers=compsci).status_code == 403
    assert client.get("/api/applications").status_code == 401
