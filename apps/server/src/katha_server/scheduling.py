"""The cycle that runs Katha end to end.

start_due_calls(now):  consented + due  ->  planned CallSession  ->  dispatch
finish_call(id):       completed call   ->  memory pipeline  ->  chapter
                       (draft -> verify -> persist)  ->  next call scheduled

Both halves take injectable collaborators so the whole cycle is testable
offline; production wiring uses the real extractor/writer/judge/dispatcher.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from katha_core.db import session as db_session
from katha_core.models import (
    CallSession,
    Chapter,
    ConsentStatus,
    Fact,
    FollowUp,
    SessionStatus,
    Storyteller,
    TranscriptSegment,
)
from sqlalchemy import func, select

from katha_core.log import get_logger

from .dispatch import Dispatcher
from .pipeline.chapters import (
    Judge,
    draft_chapter,
    llm_judge,
    to_chapter,
    write_verified_chapter,
)
from .pipeline.extraction import extract
from .pipeline.planner import plan_session
from .pipeline.runner import Extractor, process_session

log = get_logger("scheduler")

_ACTIVE = {SessionStatus.SCHEDULED, SessionStatus.DIALING, SessionStatus.IN_PROGRESS}


async def due_storytellers(now: datetime) -> list[Storyteller]:
    """Consented storytellers whose next_call_at has passed and who have no
    active or resumable call already in flight."""
    async with db_session() as s:
        active = (
            select(CallSession.storyteller_id)
            .where(CallSession.status.in_([*_ACTIVE, SessionStatus.DROPPED]))
            .subquery()
        )
        rows = await s.scalars(
            select(Storyteller).where(
                Storyteller.consent == ConsentStatus.GRANTED,
                Storyteller.next_call_at.is_not(None),
                Storyteller.next_call_at <= now,
                Storyteller.id.not_in(select(active.c.storyteller_id)),
            )
        )
        return list(rows)


async def start_due_calls(now: datetime, dispatcher: Dispatcher) -> list[CallSession]:
    started: list[CallSession] = []
    for storyteller in await due_storytellers(now):
        async with db_session() as s:
            completed = await s.scalar(
                select(func.count())
                .select_from(CallSession)
                .where(
                    CallSession.storyteller_id == storyteller.id,
                    CallSession.status == SessionStatus.COMPLETED,
                )
            )
            follow_ups = list(
                await s.scalars(
                    select(FollowUp).where(FollowUp.storyteller_id == storyteller.id)
                )
            )
            themes, _plan = plan_session(storyteller, completed or 0, follow_ups)
            call = CallSession(
                storyteller_id=storyteller.id,
                status=SessionStatus.SCHEDULED,
                scheduled_at=now,
                planned_themes=themes,
                life_brief_version=storyteller.life_brief_version,
            )
            s.add(call)
            await s.commit()
        await dispatcher.dispatch(call, storyteller)
        log.info(
            "call dispatched session=%s storyteller=%s theme=%r",
            call.id, storyteller.id, themes[0] if themes else "",
        )
        started.append(call)
    return started


async def finish_call(
    session_id: str,
    extractor: Extractor = extract,
    writer=draft_chapter,
    judge: Judge = llm_judge,
) -> Chapter:
    """Post-call chain: memory pipeline, then a chapter draft that must pass
    the fidelity gate, then schedule the next call."""
    storyteller = await process_session(session_id, extractor=extractor)

    async with db_session() as s:
        call = await s.get(CallSession, session_id)
        assert call is not None
        segments = (
            await s.scalars(
                select(TranscriptSegment)
                .where(TranscriptSegment.session_id == session_id)
                .order_by(TranscriptSegment.idx)
            )
        ).all()
        ordinal = (
            await s.scalar(
                select(func.count())
                .select_from(Chapter)
                .where(Chapter.storyteller_id == storyteller.id)
            )
            or 0
        ) + 1
        theme = str(call.planned_themes[0]) if call.planned_themes else "This conversation"

    draft, report = await asyncio.to_thread(
        write_verified_chapter, theme, list(segments), writer, judge
    )
    chapter = to_chapter(
        draft, report, storyteller.id, ordinal, source_session_id=session_id
    )

    async with db_session() as s:
        s.add(chapter)
        st = await s.get(Storyteller, storyteller.id)
        assert st is not None
        st.next_call_at = datetime.now(UTC) + timedelta(days=st.cadence_days)
        await s.commit()
    log.info(
        "call finished session=%s chapter_ordinal=%d chapter_status=%s "
        "fidelity_failures=%d brief_version=%d next_call=%s",
        session_id, chapter.ordinal, chapter.status.value,
        len(report.failures), storyteller.life_brief_version, st.next_call_at,
    )
    return chapter


async def unprocessed_completed_calls() -> list[str]:
    """COMPLETED sessions that have not yet been through the pipeline (no facts
    produced). This is how a finished call gets turned into a chapter without
    anyone invoking it by hand."""
    async with db_session() as s:
        with_facts = select(Fact.session_id).distinct().subquery()
        rows = await s.scalars(
            select(CallSession.id).where(
                CallSession.status == SessionStatus.COMPLETED,
                CallSession.id.not_in(select(with_facts.c.session_id)),
            )
        )
        return list(rows)


async def process_completed_calls(
    extractor: Extractor = extract, writer=draft_chapter, judge: Judge = llm_judge
) -> list[str]:
    """Run finish_call on every unprocessed completed session. Failures are
    logged and skipped so one bad transcript never stalls the queue."""
    done: list[str] = []
    for session_id in await unprocessed_completed_calls():
        try:
            await finish_call(session_id, extractor=extractor, writer=writer, judge=judge)
            done.append(session_id)
        except Exception:  # noqa: BLE001 — worker must survive one bad session
            log.exception("post-call processing failed session=%s", session_id)
    return done


async def run_forever(dispatcher: Dispatcher, interval_seconds: int = 60) -> None:
    """The unattended loop: place due calls, then turn finished calls into
    chapters. Both halves run every tick."""
    while True:
        await start_due_calls(datetime.now(UTC), dispatcher)
        await process_completed_calls()
        await asyncio.sleep(interval_seconds)
