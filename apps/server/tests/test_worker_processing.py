import asyncio

import pytest
from katha_core import db
from katha_core.config import settings
from katha_core.models import (
    CallSession,
    ChapterStatus,
    Family,
    SessionStatus,
    Speaker,
    Storyteller,
    TranscriptSegment,
)
from katha_server.pipeline.chapters import ChapterDraft, SentenceDraft
from katha_server.pipeline.extraction import ExtractedFact, ExtractionResult
from katha_server.scheduling import process_completed_calls, unprocessed_completed_calls
from sqlalchemy import select


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/worker.db")
    settings.cache_clear()
    db.reset()
    yield
    settings.cache_clear()
    db.reset()


async def _seed_completed(text: str = "I grew up beside the river.") -> tuple[str, str]:
    await db.create_all()
    async with db.session() as s:
        fam = Family(name="F")
        s.add(fam)
        await s.flush()
        st = Storyteller(family_id=fam.id, name="Rose", address_as="Rose", phone_e164="+1")
        s.add(st)
        await s.flush()
        call = CallSession(storyteller_id=st.id, status=SessionStatus.COMPLETED,
                           planned_themes=["Childhood"])
        s.add(call)
        await s.flush()
        s.add_all([
            TranscriptSegment(session_id=call.id, idx=0, speaker=Speaker.BIOGRAPHER,
                              t_start_ms=0, t_end_ms=1000, text="Where did you grow up?"),
            TranscriptSegment(session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                              t_start_ms=1000, t_end_ms=5000, text=text),
        ])
        await s.commit()
        return call.id, st.id


def _fixture_extractor(segs) -> ExtractionResult:
    return ExtractionResult(
        entities=[],
        facts=[ExtractedFact(statement="They grew up beside the river.",
                             entity_names=[], segment_idxs=[1])],
        follow_ups=[],
    )


def _fixture_writer(theme, segments, feedback="") -> ChapterDraft:
    story = [s for s in segments if s.speaker == Speaker.STORYTELLER][0]
    return ChapterDraft(title=theme, paragraphs=[[
        SentenceDraft(text="I grew up beside the river.", segment_ids=[story.id]),
    ]])


def test_finds_only_unprocessed_completed(fresh_db):
    async def run():
        call_id, _ = await _seed_completed()
        assert await unprocessed_completed_calls() == [call_id]
        # after processing, it's no longer pending
        done = await process_completed_calls(
            extractor=_fixture_extractor, writer=_fixture_writer, judge=lambda *a: True
        )
        assert done == [call_id]
        assert await unprocessed_completed_calls() == []

    asyncio.run(run())


def test_one_bad_session_does_not_stall_the_queue(fresh_db):
    async def run():
        good_id, _ = await _seed_completed("A good clear memory by the river.")
        # a completed session with NO transcript will raise inside finish_call
        async with db.session() as s:
            st = (await s.scalars(select(Storyteller))).first()
            bad = CallSession(storyteller_id=st.id, status=SessionStatus.COMPLETED)
            s.add(bad)
            await s.commit()

        done = await process_completed_calls(
            extractor=_fixture_extractor, writer=_fixture_writer, judge=lambda *a: True
        )
        # the good one still got processed despite the bad one erroring
        assert good_id in done

        async with db.session() as s:
            from katha_core.models import Chapter

            chapters = (await s.scalars(select(Chapter))).all()
            assert len(chapters) == 1
            assert chapters[0].status == ChapterStatus.VERIFIED

    asyncio.run(run())
