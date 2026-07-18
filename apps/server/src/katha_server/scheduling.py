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
    FollowUp,
    SessionStatus,
    Storyteller,
    TranscriptSegment,
)
from sqlalchemy import func, select

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
    chapter = to_chapter(draft, report, storyteller.id, ordinal)

    async with db_session() as s:
        s.add(chapter)
        st = await s.get(Storyteller, storyteller.id)
        assert st is not None
        st.next_call_at = datetime.now(UTC) + timedelta(days=st.cadence_days)
        await s.commit()
    return chapter


async def run_forever(dispatcher: Dispatcher, interval_seconds: int = 60) -> None:
    while True:
        await start_due_calls(datetime.now(UTC), dispatcher)
        await asyncio.sleep(interval_seconds)
