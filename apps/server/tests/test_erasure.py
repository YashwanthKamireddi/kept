import asyncio

import pytest
from fastapi.testclient import TestClient
from katha_core import db
from katha_core.config import settings
from katha_core.models import (
    CallSession,
    Chapter,
    ChapterStatus,
    Entity,
    EntityKind,
    Fact,
    FollowUp,
    SessionStatus,
    Speaker,
    TranscriptSegment,
)
from sqlalchemy import func, select


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/erase.db")
    settings.cache_clear()
    db.reset()
    from katha_server.main import app

    with TestClient(app) as c:
        yield c
    settings.cache_clear()
    db.reset()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _seed_full(storyteller_id: str) -> None:
    async with db.session() as s:
        call = CallSession(storyteller_id=storyteller_id, status=SessionStatus.COMPLETED,
                           audio_key="calls/x.ogg")
        s.add(call)
        await s.flush()
        s.add(TranscriptSegment(session_id=call.id, idx=0, speaker=Speaker.STORYTELLER,
                                t_start_ms=0, t_end_ms=1000, text="hello"))
        ent = Entity(storyteller_id=storyteller_id, kind=EntityKind.PERSON,
                     canonical_name="Ravi")
        s.add(ent)
        await s.flush()
        s.add(Fact(storyteller_id=storyteller_id, entity_id=ent.id, statement="x",
                   session_id=call.id, segment_ids=[]))
        s.add(FollowUp(storyteller_id=storyteller_id, question="a thread here"))
        s.add(Chapter(storyteller_id=storyteller_id, ordinal=1, title="C",
                      status=ChapterStatus.VERIFIED, body=[]))
        await s.commit()


async def _counts(storyteller_id: str) -> dict:
    async with db.session() as s:
        async def n(model, col) -> int:
            return await s.scalar(
                select(func.count()).select_from(model).where(col == storyteller_id)
            )
        return {
            "sessions": await n(CallSession, CallSession.storyteller_id),
            "facts": await n(Fact, Fact.storyteller_id),
            "entities": await n(Entity, Entity.storyteller_id),
            "follow_ups": await n(FollowUp, FollowUp.storyteller_id),
            "chapters": await n(Chapter, Chapter.storyteller_id),
        }


def test_erasure_removes_everything(client):
    token = client.post(
        "/auth/signup",
        json={"email": "y@example.com", "name": "Yash", "family_name": "Fam"},
    ).json()["token"]
    st = client.post(
        "/storytellers", headers=_auth(token),
        json={"name": "Rose", "address_as": "Grandma Rose", "phone_e164": "+15550001111"},
    ).json()
    asyncio.run(_seed_full(st["id"]))

    before = asyncio.run(_counts(st["id"]))
    assert all(v > 0 for v in before.values()), before

    r = client.delete(f"/storytellers/{st['id']}", headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["erased"] is True

    after = asyncio.run(_counts(st["id"]))
    assert all(v == 0 for v in after.values()), after
    # transcript segments gone too
    async def seg_count() -> int:
        async with db.session() as s:
            return await s.scalar(select(func.count()).select_from(TranscriptSegment))
    assert asyncio.run(seg_count()) == 0
    # storyteller itself gone
    assert client.get(f"/storytellers/{st['id']}", headers=_auth(token)).status_code == 404


def test_erasure_is_family_scoped(client):
    token_a = client.post(
        "/auth/signup", json={"email": "a@example.com", "name": "A", "family_name": "A"},
    ).json()["token"]
    st = client.post(
        "/storytellers", headers=_auth(token_a),
        json={"name": "Rose", "address_as": "Rose", "phone_e164": "+15550001111"},
    ).json()
    token_b = client.post(
        "/auth/signup", json={"email": "b@example.com", "name": "B", "family_name": "B"},
    ).json()["token"]
    # another family cannot erase this storyteller
    assert client.delete(f"/storytellers/{st['id']}", headers=_auth(token_b)).status_code == 404
    # and it still exists
    assert client.get(f"/storytellers/{st['id']}", headers=_auth(token_a)).status_code == 200
