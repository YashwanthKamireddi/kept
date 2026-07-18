import pytest
from fastapi.testclient import TestClient
from katha_core import db
from katha_core.config import settings


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/login.db")
    settings.cache_clear()
    db.reset()
    from katha_server.main import app

    with TestClient(app) as c:
        yield c
    settings.cache_clear()
    db.reset()


def test_login_returns_fresh_token_for_existing_account(client):
    client.post(
        "/auth/signup",
        json={"email": "d@example.com", "name": "D", "family_name": "Demo"},
    )
    r = client.post("/auth/login", json={"email": "d@example.com"})
    assert r.status_code == 200
    token = r.json()["token"]
    assert client.get(
        "/storytellers", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 200


def test_login_unknown_email_404(client):
    assert client.post("/auth/login", json={"email": "who@example.com"}).status_code == 404
