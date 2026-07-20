"""Right to erasure — delete a storyteller and everything derived from them.

The product's trust promise is literal: a family can have the whole archive
removed. This performs the full cascade in dependency order and returns a
count of what was destroyed, so the deletion is auditable. Audio objects in
R2 are removed separately by the caller (keys are returned).
"""

from katha_core.log import get_logger
from katha_core.models import (
    CallSession,
    Chapter,
    Entity,
    Fact,
    FollowUp,
    Storyteller,
    TranscriptSegment,
)
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

log = get_logger("erasure")


async def erase_storyteller(db: AsyncSession, storyteller: Storyteller) -> dict:
    """Delete all data for one storyteller. Returns counts + orphaned audio
    keys (R2 objects the caller should also delete). Commits."""
    sid = storyteller.id

    session_ids = list(
        await db.scalars(select(CallSession.id).where(CallSession.storyteller_id == sid))
    )
    audio_keys = [
        k
        for k in await db.scalars(
            select(CallSession.audio_key).where(CallSession.storyteller_id == sid)
        )
        if k
    ]

    counts: dict[str, int] = {}

    async def _delete(stmt, label: str) -> None:
        result = await db.execute(stmt)
        counts[label] = result.rowcount or 0

    # Children first, then the storyteller. Segments hang off sessions.
    if session_ids:
        await _delete(
            delete(TranscriptSegment).where(
                TranscriptSegment.session_id.in_(session_ids)
            ),
            "transcript_segments",
        )
    await _delete(delete(Fact).where(Fact.storyteller_id == sid), "facts")
    await _delete(delete(FollowUp).where(FollowUp.storyteller_id == sid), "follow_ups")
    await _delete(delete(Chapter).where(Chapter.storyteller_id == sid), "chapters")
    await _delete(delete(Entity).where(Entity.storyteller_id == sid), "entities")
    await _delete(delete(CallSession).where(CallSession.storyteller_id == sid), "sessions")
    await db.delete(storyteller)
    await db.commit()

    counts["storyteller"] = 1
    log.info("erased storyteller=%s counts=%s audio_objects=%d", sid, counts, len(audio_keys))
    return {"deleted": counts, "audio_keys": audio_keys}
