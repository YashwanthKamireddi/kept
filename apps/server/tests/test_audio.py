import asyncio

import pytest
from fastapi.testclient import TestClient
from katha_core import db
from katha_core.config import settings
from katha_core.models import CallSession, SessionStatus
from katha_server import storage


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/audio.db")
    monkeypatch.setenv("R2_ENDPOINT", "https://dummy.r2.cloudflarestorage.com")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "dummy-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "dummy-secret")
    settings.cache_clear()
    db.reset()
    storage.reset()
    from katha_server.main import app

    with TestClient(app) as c:
        yield c
    settings.cache_clear()
    db.reset()
    storage.reset()


def _setup(client: TestClient) -> tuple[str, str]:
    token = client.post(
        "/auth/signup",
        json={"email": "a@example.com", "name": "A", "family_name": "Fam"},
    ).json()["token"]
    st = client.post(
        "/storytellers",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Rose", "address_as": "Grandma Rose", "phone_e164": "+15550001111"},
    ).json()

    async def seed() -> None:
        async with db.session() as s:
            s.add(
                CallSession(
                    storyteller_id=st["id"],
                    status=SessionStatus.COMPLETED,
                    audio_key="calls/rose/1.ogg",
                )
            )
            await s.commit()

    asyncio.run(seed())
    return token, st["id"]


def test_presigned_url_for_owned_recording(client):
    token, _ = _setup(client)
    r = client.get("/audio/calls/rose/1.ogg", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    url = r.json()["url"]
    assert "calls/rose/1.ogg" in url
    assert "X-Amz-Signature" in url  # actually presigned, not a bare path


def test_unknown_recording_404(client):
    token, _ = _setup(client)
    r = client.get("/audio/calls/nope.ogg", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_other_family_cannot_resolve(client):
    _setup(client)
    other = client.post(
        "/auth/signup",
        json={"email": "b@example.com", "name": "B", "family_name": "Other"},
    ).json()["token"]
    r = client.get("/audio/calls/rose/1.ogg", headers={"Authorization": f"Bearer {other}"})
    assert r.status_code == 404


def test_unconfigured_storage_is_honest(client, monkeypatch):
    token, _ = _setup(client)
    monkeypatch.delenv("R2_ENDPOINT")
    settings.cache_clear()
    storage.reset()
    r = client.get("/audio/calls/rose/1.ogg", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"]
