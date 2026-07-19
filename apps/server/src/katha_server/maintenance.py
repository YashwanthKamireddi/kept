"""Maintenance operations — explicit, never automatic.

regenerate_chapter: re-write a chapter from its source transcript (e.g. after
a writer-prompt improvement, or when a held draft deserves another attempt).
Creates a NEW version row; history is never overwritten.
"""

import asyncio

from katha_core.db import session as db_session
from katha_core.log import get_logger
from katha_core.models import Chapter, TranscriptSegment
from sqlalchemy import select

from .pipeline.chapters import (
    Judge,
    draft_chapter,
    llm_judge,
    to_chapter,
    write_verified_chapter,
)

log = get_logger("maintenance")


class MaintenanceError(RuntimeError):
    pass


async def regenerate_chapter(
    chapter_id: str,
    session_id: str | None = None,
    writer=draft_chapter,
    judge: Judge = llm_judge,
) -> Chapter:
    async with db_session() as s:
        chapter = await s.get(Chapter, chapter_id)
        if chapter is None:
            raise MaintenanceError(f"chapter {chapter_id} not found")
        source = session_id or chapter.source_session_id
        if source is None:
            raise MaintenanceError(
                f"chapter {chapter_id} has no source session; pass session_id"
            )
        segments = (
            await s.scalars(
                select(TranscriptSegment)
                .where(TranscriptSegment.session_id == source)
                .order_by(TranscriptSegment.idx)
            )
        ).all()
        if not segments:
            raise MaintenanceError(f"session {source} has no transcript")
        latest_version = (
            await s.scalar(
                select(Chapter.version)
                .where(
                    Chapter.storyteller_id == chapter.storyteller_id,
                    Chapter.ordinal == chapter.ordinal,
                )
                .order_by(Chapter.version.desc())
                .limit(1)
            )
        ) or chapter.version

    draft, report = await asyncio.to_thread(
        write_verified_chapter, chapter.title, list(segments), writer, judge
    )
    regenerated = to_chapter(
        draft,
        report,
        chapter.storyteller_id,
        chapter.ordinal,
        version=latest_version + 1,
        source_session_id=source,
    )
    async with db_session() as s:
        s.add(regenerated)
        await s.commit()
    log.info(
        "chapter regenerated ordinal=%d version=%d status=%s failures=%d",
        regenerated.ordinal, regenerated.version,
        regenerated.status.value, len(report.failures),
    )
    return regenerated
