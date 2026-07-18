import asyncio

import pytest
from katha_core import db
from katha_core.config import settings
from katha_core.models import (
    CallSession,
    Family,
    SessionStatus,
    Speaker,
    Storyteller,
    TranscriptSegment,
)
from katha_voice.calls import (
    CONNECT_MARKER,
    RECONNECT_MARKER,
    CallStateError,
    TranscriptRecorder,
    begin_call,
    build_dialogue_context,
    complete_call,
    drop_call,
    start_resume,
)
from sqlalchemy import select


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/voice.db")
    settings.cache_clear()
    db.reset()
    yield
    settings.cache_clear()
    db.reset()


async def _seed_call() -> str:
    await db.create_all()
    async with db.session() as s:
        fam = Family(name="T")
        s.add(fam)
        await s.flush()
        st = Storyteller(family_id=fam.id, name="Rajamma", address_as="Rajamma garu",
                         phone_e164="+91")
        s.add(st)
        await s.flush()
        call = CallSession(storyteller_id=st.id, status=SessionStatus.SCHEDULED,
                           planned_themes=["childhood"])
        s.add(call)
        await s.commit()
        return call.id


def test_lifecycle_happy_path(fresh_db):
    async def run():
        call_id = await _seed_call()
        call = await begin_call(call_id)
        assert call.status == SessionStatus.IN_PROGRESS and call.started_at is not None
        call = await complete_call(call_id, audio_key="audio/x.ogg")
        assert call.status == SessionStatus.COMPLETED
        assert call.audio_key == "audio/x.ogg"
        assert call.duration_seconds >= 0

    asyncio.run(run())


def test_invalid_transitions_refused(fresh_db):
    async def run():
        call_id = await _seed_call()
        with pytest.raises(CallStateError):
            await complete_call(call_id)  # never began
        await begin_call(call_id)
        with pytest.raises(CallStateError):
            await begin_call(call_id)  # already in progress
        await drop_call(call_id)
        with pytest.raises(CallStateError):
            await complete_call(call_id)  # dropped is terminal for this session

    asyncio.run(run())


def test_recorder_orders_and_skips_empty(fresh_db):
    async def run():
        call_id = await _seed_call()
        rec = TranscriptRecorder(call_id, "te-IN")
        await rec.record(Speaker.BIOGRAPHER, "Namaskaram Rajamma garu.", 0, 2000)
        await rec.record(Speaker.STORYTELLER, "   ", 2000, 2100)  # skipped
        await rec.record(Speaker.STORYTELLER, "Namaskaram amma.", 2100, 4000)
        async with db.session() as s:
            segs = (
                await s.scalars(
                    select(TranscriptSegment)
                    .where(TranscriptSegment.session_id == call_id)
                    .order_by(TranscriptSegment.idx)
                )
            ).all()
        assert [(x.idx, x.speaker) for x in segs] == [
            (0, Speaker.BIOGRAPHER), (1, Speaker.STORYTELLER)
        ]

    asyncio.run(run())


def test_drop_and_resume_replays_transcript(fresh_db):
    async def run():
        call_id = await _seed_call()
        await begin_call(call_id)
        rec = TranscriptRecorder(call_id, "te-IN")
        await rec.record(Speaker.BIOGRAPHER, "Tell me about the station.", 0, 2000)
        await rec.record(Speaker.STORYTELLER, "It whistled every morning...", 2000, 6000)
        await drop_call(call_id)

        resumed = await start_resume(call_id)
        assert resumed.resumed_from_id == call_id
        assert resumed.planned_themes == ["childhood"]
        assert resumed.status == SessionStatus.DIALING

        dialogue = await build_dialogue_context(resumed.id)
        assert dialogue[0]["content"] == CONNECT_MARKER
        assert dialogue[1] == {"role": "assistant", "content": "Tell me about the station."}
        assert dialogue[2]["role"] == "user"
        assert dialogue[-1]["content"] == RECONNECT_MARKER

    asyncio.run(run())


def test_fresh_call_context_is_connect_marker_only(fresh_db):
    async def run():
        call_id = await _seed_call()
        dialogue = await build_dialogue_context(call_id)
        assert dialogue == [{"role": "user", "content": CONNECT_MARKER}]

    asyncio.run(run())


def test_resume_requires_dropped_status(fresh_db):
    async def run():
        call_id = await _seed_call()
        with pytest.raises(CallStateError):
            await start_resume(call_id)

    asyncio.run(run())
