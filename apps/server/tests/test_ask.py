import pytest
from fastapi.testclient import TestClient
from katha_core import db
from katha_core.config import settings


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/ask.db")
    settings.cache_clear()
    db.reset()
    from katha_server.main import app

    with TestClient(app) as c:
        yield c
    settings.cache_clear()
    db.reset()


def _setup(client: TestClient) -> tuple[str, str]:
    token = client.post(
        "/auth/signup",
        json={"email": "y@example.com", "name": "Yash", "family_name": "Fam"},
    ).json()["token"]
    st = client.post(
        "/storytellers",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Rose", "address_as": "Grandma Rose", "phone_e164": "+15550001111"},
    ).json()
    return token, st["id"]


def test_ask_something_is_attributed_and_listed(client):
    token, st_id = _setup(client)
    r = client.post(
        f"/storytellers/{st_id}/follow-ups",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "Ask about the wedding sari story"},
    )
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["asked_by_name"] == "Yash"
    assert created["priority"] == 6
    assert created["status"] == "pending"

    listed = client.get(
        f"/storytellers/{st_id}/follow-ups", headers={"Authorization": f"Bearer {token}"}
    ).json()
    assert len(listed) == 1
    assert listed[0]["asked_by_name"] == "Yash"

    # pipeline-generated threads (no asker) keep a null attribution
    # and family questions flow into the planner's pending pool untouched.


def test_ask_validation_and_isolation(client):
    token, st_id = _setup(client)
    r = client.post(
        f"/storytellers/{st_id}/follow-ups",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "hm"},
    )
    assert r.status_code == 422  # too short

    other = client.post(
        "/auth/signup",
        json={"email": "o@example.com", "name": "O", "family_name": "Other"},
    ).json()["token"]
    r = client.post(
        f"/storytellers/{st_id}/follow-ups",
        headers={"Authorization": f"Bearer {other}"},
        json={"question": "Should not be allowed here"},
    )
    assert r.status_code == 404  # family isolation
