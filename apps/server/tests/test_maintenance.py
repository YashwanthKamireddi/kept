import asyncio

import pytest
from katha_core import db
from katha_core.config import settings
from katha_core.models import (
    CallSession,
    Chapter,
    ChapterStatus,
    Family,
    SessionStatus,
    Speaker,
    Storyteller,
    TranscriptSegment,
)
from katha_server.maintenance import MaintenanceError, regenerate_chapter
from katha_server.pipeline.chapters import ChapterDraft, SentenceDraft


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/maint.db")
    settings.cache_clear()
    db.reset()
    yield
    settings.cache_clear()
    db.reset()


async def _seed() -> tuple[str, str]:
    await db.create_all()
    async with db.session() as s:
        fam = Family(name="F")
        s.add(fam)
        await s.flush()
        st = Storyteller(family_id=fam.id, name="Rose", address_as="Grandma Rose",
                         phone_e164="+1")
        s.add(st)
        await s.flush()
        call = CallSession(storyteller_id=st.id, status=SessionStatus.COMPLETED)
        s.add(call)
        await s.flush()
        seg = TranscriptSegment(session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                                t_start_ms=0, t_end_ms=5000,
                                text="Our house stood behind the bakery.")
        s.add(seg)
        await s.flush()
        ch = Chapter(storyteller_id=st.id, source_session_id=call.id, ordinal=1,
                     version=1, title="The Bakery", status=ChapterStatus.DRAFT,
                     body=[], verification_notes=[{"text": "x", "reason": "no anchors"}])
        s.add(ch)
        await s.commit()
        return ch.id, seg.id


def test_regenerate_creates_new_verified_version(fresh_db):
    async def run():
        chapter_id, seg_id = await _seed()

        def writer(theme, segments, feedback=""):
            return ChapterDraft(
                title=theme,
                paragraphs=[[SentenceDraft(
                    text="Our house stood behind the bakery.", segment_ids=[seg_id]
                )]],
            )

        new = await regenerate_chapter(
            chapter_id, writer=writer, judge=lambda s, t, b: True
        )
        assert new.version == 2
        assert new.status == ChapterStatus.VERIFIED
        assert new.verification_notes == []
        assert new.title == "The Bakery"  # continuity kept

    asyncio.run(run())


def test_regenerate_requires_source(fresh_db):
    async def run():
        chapter_id, _ = await _seed()
        async with db.session() as s:
            ch = await s.get(Chapter, chapter_id)
            ch.source_session_id = None
            await s.commit()
        with pytest.raises(MaintenanceError, match="no source session"):
            await regenerate_chapter(chapter_id)

    asyncio.run(run())
