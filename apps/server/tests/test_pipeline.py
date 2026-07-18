import asyncio

import pytest
from katha_core import db
from katha_core.config import settings
from katha_core.models import (
    CallSession,
    Entity,
    EntityKind,
    Fact,
    SessionStatus,
    Speaker,
    Storyteller,
    TranscriptSegment,
)
from katha_server.pipeline.extraction import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedFollowUp,
    ExtractionResult,
    validate_provenance,
)
from katha_server.pipeline.life_brief import compile_life_brief
from katha_server.pipeline.resolution import resolve
from katha_server.pipeline.runner import PipelineError, process_session
from sqlalchemy import select


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db")
    settings.cache_clear()
    db.reset()
    yield
    settings.cache_clear()
    db.reset()


def _extraction_fixture() -> ExtractionResult:
    return ExtractionResult(
        entities=[
            ExtractedEntity(kind="person", name="Ravi", aliases=["Ravi mama"],
                            summary="Her younger brother."),
            ExtractedEntity(kind="place", name="Guntur", summary="Her childhood town."),
        ],
        facts=[
            ExtractedFact(
                statement="She grew up in Guntur near the railway station.",
                entity_names=["Guntur"],
                segment_idxs=[1],
            ),
            ExtractedFact(
                statement="Her brother Ravi walked her to school every day.",
                entity_names=["Ravi"],
                segment_idxs=[1, 3],
            ),
        ],
        follow_ups=[
            ExtractedFollowUp(question="What happened to Ravi after he moved to Bombay?",
                              rationale="Mentioned the move but the story was cut short.",
                              priority=8),
        ],
    )


async def _seed_session() -> tuple[str, str]:
    await db.create_all()
    async with db.session() as s:
        from katha_core.models import Family

        fam = Family(name="Test")
        s.add(fam)
        await s.flush()
        st = Storyteller(family_id=fam.id, name="Rajamma", address_as="Rajamma garu",
                         phone_e164="+919999999999")
        s.add(st)
        await s.flush()
        call = CallSession(storyteller_id=st.id, status=SessionStatus.COMPLETED)
        s.add(call)
        await s.flush()
        s.add_all([
            TranscriptSegment(session_id=call.id, idx=0, speaker=Speaker.BIOGRAPHER,
                              t_start_ms=0, t_end_ms=3000,
                              text="Rajamma garu, tell me about where you grew up."),
            TranscriptSegment(session_id=call.id, idx=1, speaker=Speaker.STORYTELLER,
                              t_start_ms=3000, t_end_ms=15000,
                              text="I grew up in Guntur, right next to the railway station."),
            TranscriptSegment(session_id=call.id, idx=2, speaker=Speaker.BIOGRAPHER,
                              t_start_ms=15000, t_end_ms=17000, text="Who took you to school?"),
            TranscriptSegment(session_id=call.id, idx=3, speaker=Speaker.STORYTELLER,
                              t_start_ms=17000, t_end_ms=30000,
                              text="My brother Ravi walked me every day, before he left for Bombay."),
        ])
        await s.commit()
        return call.id, st.id


def test_validate_provenance_drops_unanchored():
    result = ExtractionResult(
        entities=[],
        facts=[
            ExtractedFact(statement="anchored", entity_names=[], segment_idxs=[1]),
            ExtractedFact(statement="phantom segment", entity_names=[], segment_idxs=[99]),
            ExtractedFact(statement="no anchor at all", entity_names=[], segment_idxs=[]),
        ],
        follow_ups=[],
    )
    kept = validate_provenance(result, valid_idxs={0, 1, 2, 3})
    assert [f.statement for f in kept.facts] == ["anchored"]


def test_resolution_merges_by_alias_and_creates_new():
    existing = [Entity(id="e1", storyteller_id="st", kind=EntityKind.PERSON,
                       canonical_name="Ravi", aliases=["Ravi mama"], summary="")]
    extracted = [
        ExtractedEntity(kind="person", name="ravi mama", aliases=["Ravi anna"],
                        summary="Her brother."),
        ExtractedEntity(kind="place", name="Guntur"),
    ]
    new, by_name = resolve("st", extracted, existing)
    assert len(new) == 1 and new[0].canonical_name == "Guntur"
    assert by_name["ravi mama"].id == "e1"
    assert "Ravi anna" in existing[0].aliases
    assert existing[0].summary == "Her brother."  # filled because it was empty


def test_life_brief_compiles_sections(fresh_db):
    st = Storyteller(id="st", family_id="f", name="Rajamma", address_as="Rajamma garu",
                     phone_e164="+91", life_brief_version=0)
    entities = [Entity(id="e1", storyteller_id="st", kind=EntityKind.PERSON,
                       canonical_name="Ravi", aliases=["Ravi mama"], summary="Younger brother")]
    facts = [Fact(storyteller_id="st", entity_id="e1", statement="Ravi walked her to school.",
                  session_id="c1", segment_ids=["s1"])]
    brief = compile_life_brief(st, entities, facts, [])
    assert "# Life Brief — Rajamma" in brief
    assert "## People" in brief
    assert "**Ravi** (Ravi mama) — Younger brother" in brief
    assert "Ravi walked her to school." in brief


def test_process_session_end_to_end(fresh_db):
    async def run():
        call_id, st_id = await _seed_session()
        st = await process_session(call_id, extractor=lambda segs: _extraction_fixture())

        assert st.life_brief_version == 1
        assert "Guntur" in st.life_brief and "Ravi" in st.life_brief
        assert "What happened to Ravi after he moved to Bombay?" in st.life_brief

        async with db.session() as s:
            facts = (await s.scalars(select(Fact).where(Fact.session_id == call_id))).all()
            assert len(facts) == 2
            # provenance points at real segment row ids
            segs = (await s.scalars(
                select(TranscriptSegment).where(TranscriptSegment.session_id == call_id)
            )).all()
            seg_ids = {seg.id for seg in segs}
            for f in facts:
                assert f.segment_ids and set(f.segment_ids) <= seg_ids
            entities = (await s.scalars(
                select(Entity).where(Entity.storyteller_id == st_id)
            )).all()
            assert {e.canonical_name for e in entities} == {"Ravi", "Guntur"}

        # refuses double-processing
        with pytest.raises(PipelineError, match="already processed"):
            await process_session(call_id, extractor=lambda segs: _extraction_fixture())

    asyncio.run(run())


def test_process_session_requires_completed(fresh_db):
    async def run():
        await db.create_all()
        async with db.session() as s:
            from katha_core.models import Family

            fam = Family(name="T")
            s.add(fam)
            await s.flush()
            st = Storyteller(family_id=fam.id, name="A", address_as="A", phone_e164="+1")
            s.add(st)
            await s.flush()
            call = CallSession(storyteller_id=st.id, status=SessionStatus.IN_PROGRESS)
            s.add(call)
            await s.commit()
            call_id = call.id
        with pytest.raises(PipelineError, match="not completed"):
            await process_session(call_id, extractor=lambda segs: _extraction_fixture())

    asyncio.run(run())
