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


def test_portrait_surfaces_the_life_brief(client):
    token = _signup(client)["token"]
    sid = client.post(
        "/storytellers",
        headers=_auth(token),
        json={"name": "Rose", "address_as": "Rose", "phone_e164": "+15551230000"},
    ).json()["id"]

    # empty before the pipeline has learned anything
    p = client.get(f"/storytellers/{sid}/portrait", headers=_auth(token))
    assert p.status_code == 200
    assert p.json() == {"name": "Rose", "life_brief": "", "life_brief_version": 0}

    # once a Life Brief exists, the family sees it verbatim
    async def _set() -> None:
        from katha_core.models import Storyteller

        async with db.session() as s:
            st = await s.get(Storyteller, sid)
            st.life_brief = "# Life Brief\n\n## People\n- **Mother** — she sang"
            st.life_brief_version = 2
            await s.commit()

    asyncio.run(_set())
    got = client.get(f"/storytellers/{sid}/portrait", headers=_auth(token)).json()
    assert got["life_brief_version"] == 2
    assert "## People" in got["life_brief"]

    # a different family cannot read this storyteller's portrait
    other = client.post(
        "/auth/signup",
        json={"email": "other@example.com", "name": "O", "family_name": "Other"},
    ).json()["token"]
    assert client.get(f"/storytellers/{sid}/portrait", headers=_auth(other)).status_code == 404


def test_memoir_assembles_the_whole_book(client):
    token = _signup(client)["token"]
    sid = client.post(
        "/storytellers",
        headers=_auth(token),
        json={"name": "Rajamma", "address_as": "Rajamma garu", "phone_e164": "+919999999999"},
    ).json()["id"]

    async def seed() -> None:
        async with db.session() as s:
            call = CallSession(
                storyteller_id=sid, status=SessionStatus.COMPLETED, audio_key="audio/c.ogg"
            )
            s.add(call)
            await s.flush()
            seg = TranscriptSegment(
                session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                t_start_ms=1000, t_end_ms=9000, text="We lived by the river.",
            )
            s.add(seg)
            await s.flush()
            s.add_all([
                # chapter 2 seeded before chapter 1 to prove the memoir orders by ordinal
                Chapter(
                    storyteller_id=sid, ordinal=2, title="The Move", version=1,
                    status=ChapterStatus.VERIFIED,
                    body=[[{"text": "Then we left.", "segment_ids": [], "bridge": True}]],
                ),
                # chapter 1: a superseded v1 and the current v2 — only v2 should show
                Chapter(
                    storyteller_id=sid, ordinal=1, title="The River (old)", version=1,
                    status=ChapterStatus.VERIFIED,
                    body=[[{"text": "Stale draft prose.", "segment_ids": [], "bridge": True}]],
                ),
                Chapter(
                    storyteller_id=sid, ordinal=1, title="The River", version=2,
                    status=ChapterStatus.VERIFIED,
                    body=[[{"text": "We lived by the river.",
                            "segment_ids": [seg.id], "bridge": False}]],
                ),
                # an unverified draft must stay out of the family's hands
                Chapter(
                    storyteller_id=sid, ordinal=3, title="Unfinished", version=1,
                    status=ChapterStatus.DRAFT,
                    body=[[{"text": "Not yet checked.", "segment_ids": [], "bridge": True}]],
                ),
            ])
            await s.commit()

    asyncio.run(seed())

    book = client.get(f"/storytellers/{sid}/memoir", headers=_auth(token))
    assert book.status_code == 200, book.text
    data = book.json()
    assert data["name"] == "Rajamma"
    # draft excluded; in order by ordinal
    assert [c["ordinal"] for c in data["chapters"]] == [1, 2]
    # latest version wins for ordinal 1
    assert data["chapters"][0]["title"] == "The River"
    # anchors resolved for the memoir just like the single-chapter reader
    first = data["chapters"][0]["paragraphs"][0][0]
    assert first["anchors"][0]["audio_key"] == "audio/c.ogg"
    assert first["anchors"][0]["t_start_ms"] == 1000

    # a different family cannot read this storyteller's book
    other = client.post(
        "/auth/signup",
        json={"email": "other@example.com", "name": "O", "family_name": "Other"},
    ).json()["token"]
    assert client.get(f"/storytellers/{sid}/memoir", headers=_auth(other)).status_code == 404


def test_life_portrait_groups_entities_with_their_own_words(client):
    token = _signup(client)["token"]
    sid = client.post(
        "/storytellers",
        headers=_auth(token),
        json={"name": "Rajamma", "address_as": "Rajamma garu", "phone_e164": "+919999999999"},
    ).json()["id"]

    async def seed() -> None:
        from katha_core.models import Entity, EntityKind, Fact

        async with db.session() as s:
            call = CallSession(
                storyteller_id=sid, status=SessionStatus.COMPLETED, audio_key=""
            )
            s.add(call)
            await s.flush()
            spoke = TranscriptSegment(
                session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                t_start_ms=0, t_end_ms=6000,
                text="My mother sang quietly so as not to wake us.",
            )
            s.add(spoke)
            await s.flush()
            mother = Entity(
                storyteller_id=sid, kind=EntityKind.PERSON,
                canonical_name="Mother", summary="Woke first; sang in the mornings.",
            )
            place = Entity(
                storyteller_id=sid, kind=EntityKind.PLACE,
                canonical_name="The bakery", summary="Her father's bakery.",
            )
            s.add_all([mother, place])
            await s.flush()
            # two distinct facts, same utterance -> one deduped moment for Mother
            s.add_all([
                Fact(storyteller_id=sid, entity_id=mother.id, session_id=call.id,
                     statement="Her mother sang in the mornings.", segment_ids=[spoke.id]),
                Fact(storyteller_id=sid, entity_id=mother.id, session_id=call.id,
                     statement="She sang quietly to not wake the children.", segment_ids=[spoke.id]),
            ])
            await s.commit()

    asyncio.run(seed())

    r = client.get(f"/storytellers/{sid}/life", headers=_auth(token))
    assert r.status_code == 200, r.text
    life = r.json()
    assert life["name"] == "Rajamma"
    # people group comes before places
    assert [g["kind"] for g in life["groups"]] == ["person", "place"]
    people = life["groups"][0]["entities"]
    assert people[0]["name"] == "Mother"
    # the two facts share one utterance -> exactly one moment, in her own words
    assert len(people[0]["moments"]) == 1
    assert people[0]["moments"][0]["quote"] == "My mother sang quietly so as not to wake us."
    # no recording synced (audio_key blank) -> honest null anchor, never faked
    assert people[0]["moments"][0]["anchor"] is None
    # the place has a summary but no spoken moments yet
    assert life["groups"][1]["entities"][0]["moments"] == []

    other = client.post(
        "/auth/signup",
        json={"email": "other@example.com", "name": "O", "family_name": "Other"},
    ).json()["token"]
    assert client.get(f"/storytellers/{sid}/life", headers=_auth(other)).status_code == 404


def test_search_finds_stories_and_moments_but_not_drafts_or_interviewer(client):
    token = _signup(client)["token"]
    sid = client.post(
        "/storytellers",
        headers=_auth(token),
        json={"name": "Rajamma", "address_as": "Rajamma garu", "phone_e164": "+919999999999"},
    ).json()["id"]

    async def seed() -> None:
        async with db.session() as s:
            call = CallSession(
                storyteller_id=sid, status=SessionStatus.COMPLETED, audio_key="audio/c.ogg"
            )
            s.add(call)
            await s.flush()
            s.add_all([
                # the storyteller's own words — a real "moment"
                TranscriptSegment(
                    session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                    t_start_ms=0, t_end_ms=5000,
                    text="My father ran the bakery on the corner.",
                ),
                # the interviewer said "bakery" too — must NOT surface as a moment
                TranscriptSegment(
                    session_id=call.id, idx=2, speaker=Speaker.BIOGRAPHER,
                    t_start_ms=5000, t_end_ms=8000,
                    text="What was the bakery like inside?",
                ),
            ])
            s.add_all([
                Chapter(
                    storyteller_id=sid, ordinal=1, title="The Bakery", version=1,
                    status=ChapterStatus.VERIFIED,
                    body=[[{"text": "The bakery smelled of bread each dawn.",
                            "segment_ids": [], "bridge": True}]],
                ),
                # a draft that also mentions the term — must stay out of results
                Chapter(
                    storyteller_id=sid, ordinal=2, title="Draft", version=1,
                    status=ChapterStatus.DRAFT,
                    body=[[{"text": "An unverified line about the bakery.",
                            "segment_ids": [], "bridge": True}]],
                ),
            ])
            await s.commit()

    asyncio.run(seed())

    r = client.get(f"/storytellers/{sid}/search", headers=_auth(token), params={"q": "bakery"})
    assert r.status_code == 200, r.text
    res = r.json()
    # exactly the verified chapter, not the draft
    assert [c["ordinal"] for c in res["chapters"]] == [1]
    assert "bakery" in res["chapters"][0]["snippet"].lower()
    # exactly the storyteller's line, not the interviewer's question
    assert len(res["moments"]) == 1
    assert res["moments"][0]["snippet"] == "My father ran the bakery on the corner."

    # a one-character query is a no-op, not a full-table scan
    assert client.get(
        f"/storytellers/{sid}/search", headers=_auth(token), params={"q": "b"}
    ).json() == {"query": "b", "chapters": [], "moments": []}

    # a different family cannot search this storyteller
    other = client.post(
        "/auth/signup",
        json={"email": "other@example.com", "name": "O", "family_name": "Other"},
    ).json()["token"]
    assert (
        client.get(
            f"/storytellers/{sid}/search", headers=_auth(other), params={"q": "bakery"}
        ).status_code
        == 404
    )
