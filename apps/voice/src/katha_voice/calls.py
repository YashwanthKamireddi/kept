"""Call lifecycle, transcript checkpointing, and drop/resume.

Everything here is DB-backed and key-independent: the worker calls into these
seams so a dropped line never loses a word (segments are committed as they
finalize) and a resumed call re-opens mid-thought instead of starting over.
"""

from datetime import UTC, datetime

from katha_core.db import session as db_session
from katha_core.models import (
    CallSession,
    SessionStatus,
    Speaker,
    Storyteller,
    TranscriptSegment,
)
from sqlalchemy import select


class CallStateError(RuntimeError):
    pass


_BEGINNABLE = {SessionStatus.SCHEDULED, SessionStatus.DIALING}
RECONNECT_MARKER = "(the line dropped for a moment; she has picked up again)"
CONNECT_MARKER = "(the phone connects; she has picked up)"


async def begin_call(session_id: str) -> CallSession:
    async with db_session() as s:
        call = await s.get(CallSession, session_id)
        if call is None:
            raise CallStateError(f"session {session_id} not found")
        if call.status not in _BEGINNABLE:
            raise CallStateError(f"cannot begin call in status {call.status}")
        call.status = SessionStatus.IN_PROGRESS
        call.started_at = datetime.now(UTC)
        await s.commit()
        return call


async def complete_call(session_id: str, audio_key: str = "") -> CallSession:
    async with db_session() as s:
        call = await s.get(CallSession, session_id)
        if call is None or call.status != SessionStatus.IN_PROGRESS:
            raise CallStateError(f"cannot complete session {session_id}")
        call.status = SessionStatus.COMPLETED
        call.ended_at = datetime.now(UTC)
        if call.started_at is not None:
            started = call.started_at
            if started.tzinfo is None:  # SQLite round-trips naive datetimes
                started = started.replace(tzinfo=UTC)
            call.duration_seconds = int((call.ended_at - started).total_seconds())
        call.audio_key = audio_key
        await s.commit()
        return call


async def drop_call(session_id: str) -> CallSession:
    async with db_session() as s:
        call = await s.get(CallSession, session_id)
        if call is None or call.status != SessionStatus.IN_PROGRESS:
            raise CallStateError(f"cannot drop session {session_id}")
        call.status = SessionStatus.DROPPED
        call.ended_at = datetime.now(UTC)
        await s.commit()
        return call


async def start_resume(dropped_session_id: str) -> CallSession:
    """Create a new session continuing a dropped one (same plan, linked)."""
    async with db_session() as s:
        dropped = await s.get(CallSession, dropped_session_id)
        if dropped is None or dropped.status != SessionStatus.DROPPED:
            raise CallStateError(f"session {dropped_session_id} is not resumable")
        resumed = CallSession(
            storyteller_id=dropped.storyteller_id,
            status=SessionStatus.DIALING,
            planned_themes=dropped.planned_themes,
            resumed_from_id=dropped.id,
            life_brief_version=dropped.life_brief_version,
        )
        s.add(resumed)
        await s.commit()
        return resumed


class TranscriptRecorder:
    """Commits finalized utterances immediately, in order. One per live call."""

    def __init__(self, session_id: str, language: str):
        self._session_id = session_id
        self._language = language
        self._idx = 0

    async def record(self, speaker: Speaker, text: str, t_start_ms: int, t_end_ms: int) -> None:
        text = text.strip()
        if not text:
            return
        async with db_session() as s:
            s.add(
                TranscriptSegment(
                    session_id=self._session_id,
                    idx=self._idx,
                    speaker=speaker,
                    t_start_ms=t_start_ms,
                    t_end_ms=t_end_ms,
                    text=text,
                    language=self._language,
                )
            )
            await s.commit()
        self._idx += 1


async def build_dialogue_context(session_id: str) -> list[dict]:
    """Dialogue seed for the interviewer. Fresh calls open with the connect
    marker; resumed calls replay the dropped call's transcript and end with
    the reconnect marker so the biographer picks up mid-thought."""
    async with db_session() as s:
        call = await s.get(CallSession, session_id)
        if call is None:
            raise CallStateError(f"session {session_id} not found")
        if call.resumed_from_id is None:
            return [{"role": "user", "content": CONNECT_MARKER}]
        segments = (
            await s.scalars(
                select(TranscriptSegment)
                .where(TranscriptSegment.session_id == call.resumed_from_id)
                .order_by(TranscriptSegment.idx)
            )
        ).all()
    dialogue: list[dict] = [{"role": "user", "content": CONNECT_MARKER}]
    for seg in segments:
        role = "assistant" if seg.speaker == Speaker.BIOGRAPHER else "user"
        dialogue.append({"role": role, "content": seg.text})
    # Consecutive same-role messages are legal for the Claude API (combined).
    dialogue.append({"role": "user", "content": RECONNECT_MARKER})
    return dialogue


async def storyteller_for_session(session_id: str) -> Storyteller:
    async with db_session() as s:
        call = await s.get(CallSession, session_id)
        if call is None:
            raise CallStateError(f"session {session_id} not found")
        st = await s.get(Storyteller, call.storyteller_id)
        assert st is not None
        return st
