import asyncio

import pytest
from fastapi.testclient import TestClient
from katha_core import db
from katha_core.config import settings
from katha_core.models import (
    CallSession,
    Chapter,
    ChapterStatus,
    SessionStatus,
    Speaker,
    TranscriptSegment,
)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/api.db")
    monkeypatch.setenv("KATHA_ENV", "dev")
    settings.cache_clear()
    db.reset()
    from katha_server.main import app

    with TestClient(app) as c:
        yield c
    settings.cache_clear()
    db.reset()


def _signup(client: TestClient) -> dict:
    r = client.post(
        "/auth/signup",
        json={"email": "yk@example.com", "name": "Yash", "family_name": "Kamireddi"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_auth_required(client):
    assert client.get("/storytellers").status_code == 401
    assert client.get("/storytellers", headers=_auth("bogus")).status_code == 401


def test_signup_rejects_duplicate_email(client):
    _signup(client)
    r = client.post(
        "/auth/signup",
        json={"email": "yk@example.com", "name": "Y", "family_name": "K"},
    )
    assert r.status_code == 409


def test_storyteller_lifecycle_and_consent_machine(client):
    token = _signup(client)["token"]
    r = client.post(
        "/storytellers",
        headers=_auth(token),
        json={"name": "Rajamma", "address_as": "Rajamma garu", "phone_e164": "+919999999999"},
    )
    assert r.status_code == 200, r.text
    st = r.json()
    assert st["consent"] == "pending"

    # invalid transition: pending -> revoked
    r = client.patch(
        f"/storytellers/{st['id']}/consent", headers=_auth(token), json={"consent": "revoked"}
    )
    assert r.status_code == 409

    # valid: pending -> granted
    r = client.patch(
        f"/storytellers/{st['id']}/consent", headers=_auth(token), json={"consent": "granted"}
    )
    assert r.status_code == 200
    assert r.json()["consent"] == "granted"

    # granted -> revoked -> granted (she may change her mind)
    assert (
        client.patch(
            f"/storytellers/{st['id']}/consent",
            headers=_auth(token),
            json={"consent": "revoked"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/storytellers/{st['id']}/consent",
            headers=_auth(token),
            json={"consent": "granted"},
        ).status_code
        == 200
    )


def test_family_isolation(client):
    token_a = _signup(client)["token"]
    r = client.post(
        "/auth/signup",
        json={"email": "other@example.com", "name": "O", "family_name": "Other"},
    )
    token_b = r.json()["token"]

    st = client.post(
        "/storytellers",
        headers=_auth(token_a),
        json={"name": "Rajamma", "address_as": "Rajamma garu", "phone_e164": "+919999999999"},
    ).json()

    # family B cannot see family A's storyteller
    assert (
        client.get(f"/storytellers/{st['id']}", headers=_auth(token_b)).status_code == 404
    )


def test_chapter_detail_resolves_audio_anchors(client):
    token = _signup(client)["token"]
    st = client.post(
        "/storytellers",
        headers=_auth(token),
        json={"name": "Rajamma", "address_as": "Rajamma garu", "phone_e164": "+919999999999"},
    ).json()

    async def seed() -> str:
        async with db.session() as s:
            call = CallSession(
                storyteller_id=st["id"],
                status=SessionStatus.COMPLETED,
                audio_key="audio/call1.ogg",
            )
            s.add(call)
            await s.flush()
            seg = TranscriptSegment(
                session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                t_start_ms=3000, t_end_ms=15000,
                text="I grew up in Guntur, next to the railway station.",
            )
            s.add(seg)
            await s.flush()
            ch = Chapter(
                storyteller_id=st["id"], ordinal=1, title="The Railway Town",
                status=ChapterStatus.VERIFIED,
                body=[[
                    {"text": "I grew up beside the railway station.",
                     "segment_ids": [seg.id], "bridge": False},
                    {"text": "Mornings had their own rhythm.",
                     "segment_ids": [], "bridge": True},
                ]],
            )
            s.add(ch)
            await s.commit()
            return ch.id

    chapter_id = asyncio.run(seed())

    r = client.get(f"/chapters/{chapter_id}", headers=_auth(token))
    assert r.status_code == 200, r.text
    detail = r.json()
    first = detail["paragraphs"][0][0]
    assert first["anchors"][0]["audio_key"] == "audio/call1.ogg"
    assert first["anchors"][0]["t_start_ms"] == 3000
    assert detail["paragraphs"][0][1]["bridge"] is True
    assert detail["paragraphs"][0][1]["anchors"] == []

    sessions = client.get(
        f"/storytellers/{st['id']}/sessions", headers=_auth(token)
    ).json()
    assert len(sessions) == 1 and sessions[0]["audio_key"] == "audio/call1.ogg"
