import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from katha_core import db
from katha_core.config import settings
from katha_core.models import (
    CallSession,
    ChapterStatus,
    ConsentStatus,
    Family,
    SessionStatus,
    Speaker,
    Storyteller,
    TranscriptSegment,
)
from katha_server.pipeline.chapters import ChapterDraft, SentenceDraft
from katha_server.pipeline.extraction import (
    ExtractedEntity,
    ExtractedFact,
    ExtractionResult,
)
from katha_server.scheduling import due_storytellers, finish_call, start_due_calls

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def _extraction_fixture() -> ExtractionResult:
    return ExtractionResult(
        entities=[ExtractedEntity(kind="place", name="Guntur", summary="Childhood town.")],
        facts=[
            ExtractedFact(
                statement="They grew up in Guntur near the railway station.",
                entity_names=["Guntur"],
                segment_idxs=[1],
            )
        ],
        follow_ups=[],
    )


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/sched.db")
    settings.cache_clear()
    db.reset()
    yield
    settings.cache_clear()
    db.reset()


class RecordingDispatcher:
    def __init__(self):
        self.dispatched: list[tuple[str, str]] = []

    async def dispatch(self, call, storyteller):
        self.dispatched.append((call.id, storyteller.id))


async def _mk_storyteller(
    consent=ConsentStatus.GRANTED,
    next_call_at=NOW - timedelta(hours=1),
    with_active_session=False,
) -> str:
    await db.create_all()
    async with db.session() as s:
        fam = Family(name="F")
        s.add(fam)
        await s.flush()
        st = Storyteller(
            family_id=fam.id, name="Rose", address_as="Grandma Rose",
            phone_e164="+15550001111", consent=consent, next_call_at=next_call_at,
        )
        s.add(st)
        await s.flush()
        if with_active_session:
            s.add(CallSession(storyteller_id=st.id, status=SessionStatus.IN_PROGRESS))
        await s.commit()
        return st.id


def test_due_selection_rules(fresh_db):
    async def run():
        due_id = await _mk_storyteller()
        await _mk_storyteller(consent=ConsentStatus.PENDING)          # not consented
        await _mk_storyteller(next_call_at=NOW + timedelta(days=1))   # not due yet
        await _mk_storyteller(next_call_at=None)                      # unscheduled
        await _mk_storyteller(with_active_session=True)               # already in flight
        due = await due_storytellers(NOW)
        assert [st.id for st in due] == [due_id]

    asyncio.run(run())


def test_start_due_calls_plans_and_dispatches(fresh_db):
    async def run():
        st_id = await _mk_storyteller()
        dispatcher = RecordingDispatcher()
        started = await start_due_calls(NOW, dispatcher)
        assert len(started) == 1
        call = started[0]
        assert call.planned_themes[0] == "introduction"  # first session ever
        assert dispatcher.dispatched == [(call.id, st_id)]
        # not double-started on the next tick
        assert await start_due_calls(NOW, dispatcher) == []

    asyncio.run(run())


def _fake_writer(
    theme: str, segments: list[TranscriptSegment], feedback: str = ""
) -> ChapterDraft:
    st_segments = [s for s in segments if s.speaker == Speaker.STORYTELLER]
    return ChapterDraft(
        title=theme,
        paragraphs=[[
            SentenceDraft(text="I grew up next to the railway station in Guntur.",
                          segment_ids=[st_segments[0].id]),
        ]],
    )


def test_finish_call_runs_full_chain(fresh_db):
    async def run():
        st_id = await _mk_storyteller()
        async with db.session() as s:
            call = CallSession(storyteller_id=st_id, status=SessionStatus.COMPLETED,
                               planned_themes=["Childhood home"])
            s.add(call)
            await s.flush()
            s.add_all([
                TranscriptSegment(session_id=call.id, idx=0, speaker=Speaker.BIOGRAPHER,
                                  t_start_ms=0, t_end_ms=2000, text="Where did you grow up?"),
                TranscriptSegment(session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                                  t_start_ms=2000, t_end_ms=9000,
                                  text="I grew up in Guntur, right next to the railway station."),
            ])
            await s.commit()
            call_id = call.id

        chapter = await finish_call(
            call_id,
            extractor=lambda segs: _extraction_fixture(),
            writer=_fake_writer,
            judge=lambda sent, texts, bridge: True,
        )
        assert chapter.status == ChapterStatus.VERIFIED
        assert chapter.ordinal == 1
        assert chapter.title == "Childhood home"

        async with db.session() as s:
            st = await s.get(Storyteller, st_id)
            assert st.life_brief_version == 1              # memory pipeline ran
            assert st.next_call_at is not None
            assert st.next_call_at.replace(tzinfo=UTC) > datetime.now(UTC)  # rescheduled

    asyncio.run(run())


def test_failed_fidelity_keeps_chapter_draft(fresh_db):
    async def run():
        st_id = await _mk_storyteller()
        async with db.session() as s:
            call = CallSession(storyteller_id=st_id, status=SessionStatus.COMPLETED)
            s.add(call)
            await s.flush()
            s.add_all([
                TranscriptSegment(session_id=call.id, idx=0, speaker=Speaker.BIOGRAPHER,
                                  t_start_ms=0, t_end_ms=2000, text="Tell me a memory."),
                TranscriptSegment(session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                                  t_start_ms=2000, t_end_ms=5000, text="A short memory."),
            ])
            await s.commit()
            call_id = call.id

        chapter = await finish_call(
            call_id,
            extractor=lambda segs: _extraction_fixture(),
            writer=_fake_writer,
            judge=lambda sent, texts, bridge: False,  # verifier rejects everything
        )
        assert chapter.status == ChapterStatus.DRAFT  # family will not see it

    asyncio.run(run())
