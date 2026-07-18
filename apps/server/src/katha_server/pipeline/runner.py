"""Post-call pipeline orchestration.

process_session(session_id):
  1. load completed session + segments
  2. extract entities/facts/follow-ups (Claude, provenance-validated)
  3. resolve entities into the existing life graph
  4. persist facts with segment-id provenance
  5. recompile the Life Brief, bump its version

Idempotent by refusal: a session that already produced facts is not
re-processed (regeneration is an explicit maintenance operation, not a retry).
"""

import asyncio
from collections.abc import Callable

from katha_core.db import session as db_session
from katha_core.models import (
    CallSession,
    Entity,
    Fact,
    FollowUp,
    SessionStatus,
    Storyteller,
    TranscriptSegment,
)
from sqlalchemy import select

from .extraction import ExtractionResult, extract
from .life_brief import compile_life_brief
from .resolution import _norm, resolve

Extractor = Callable[[list[TranscriptSegment]], ExtractionResult]


class PipelineError(RuntimeError):
    pass


async def process_session(session_id: str, extractor: Extractor = extract) -> Storyteller:
    async with db_session() as s:
        call = await s.get(CallSession, session_id)
        if call is None:
            raise PipelineError(f"session {session_id} not found")
        if call.status != SessionStatus.COMPLETED:
            raise PipelineError(f"session {session_id} is {call.status}, not completed")

        already = await s.scalar(select(Fact).where(Fact.session_id == session_id).limit(1))
        if already is not None:
            raise PipelineError(f"session {session_id} already processed")

        segments = (
            await s.scalars(
                select(TranscriptSegment)
                .where(TranscriptSegment.session_id == session_id)
                .order_by(TranscriptSegment.idx)
            )
        ).all()
        if not segments:
            raise PipelineError(f"session {session_id} has no transcript")

        storyteller = await s.get(Storyteller, call.storyteller_id)
        assert storyteller is not None

        result = await asyncio.to_thread(extractor, list(segments))

        existing = list(
            await s.scalars(select(Entity).where(Entity.storyteller_id == storyteller.id))
        )
        new_entities, by_name = resolve(storyteller.id, result.entities, existing)
        s.add_all(new_entities)
        await s.flush()  # entity ids for fact linking

        idx_to_id = {seg.idx: seg.id for seg in segments}
        for ext in result.facts:
            entity = next(
                (by_name[_norm(n)] for n in ext.entity_names if _norm(n) in by_name), None
            )
            s.add(
                Fact(
                    storyteller_id=storyteller.id,
                    entity_id=entity.id if entity else None,
                    statement=ext.statement,
                    confidence=ext.confidence,
                    session_id=session_id,
                    segment_ids=[idx_to_id[i] for i in ext.segment_idxs],
                )
            )

        for fu in result.follow_ups:
            s.add(
                FollowUp(
                    storyteller_id=storyteller.id,
                    question=fu.question,
                    rationale=fu.rationale,
                    priority=fu.priority,
                    source_session_id=session_id,
                )
            )
        await s.flush()

        all_entities = list(
            await s.scalars(select(Entity).where(Entity.storyteller_id == storyteller.id))
        )
        all_facts = list(
            await s.scalars(select(Fact).where(Fact.storyteller_id == storyteller.id))
        )
        all_followups = list(
            await s.scalars(select(FollowUp).where(FollowUp.storyteller_id == storyteller.id))
        )
        storyteller.life_brief = compile_life_brief(
            storyteller, all_entities, all_facts, all_followups
        )
        storyteller.life_brief_version += 1

        await s.commit()
        return storyteller
