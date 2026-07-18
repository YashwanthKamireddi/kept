from fastapi import APIRouter, HTTPException
from katha_core.models import (
    ApiToken,
    CallSession,
    Chapter,
    ConsentStatus,
    Family,
    FollowUp,
    FollowUpStatus,
    Keeper,
    Storyteller,
    TranscriptSegment,
)
from sqlalchemy import select

from . import schemas
from .deps import CurrentKeeper, Db

router = APIRouter()

# --- Auth (dev stub: token issued at signup; magic-link flow mints the same) --


@router.post("/auth/signup", response_model=schemas.SignupOut, tags=["auth"])
async def signup(body: schemas.SignupIn, db: Db) -> schemas.SignupOut:
    existing = await db.scalar(select(Keeper).where(Keeper.email == body.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="email already registered")
    family = Family(name=body.family_name)
    db.add(family)
    await db.flush()
    keeper = Keeper(family_id=family.id, email=body.email, name=body.name)
    db.add(keeper)
    await db.flush()
    token = ApiToken(keeper_id=keeper.id)
    db.add(token)
    await db.commit()
    return schemas.SignupOut(token=token.token, keeper_id=keeper.id, family_id=family.id)


# --- Storytellers -------------------------------------------------------------

_CONSENT_TRANSITIONS: dict[ConsentStatus, set[ConsentStatus]] = {
    ConsentStatus.PENDING: {ConsentStatus.GRANTED, ConsentStatus.DECLINED},
    ConsentStatus.GRANTED: {ConsentStatus.REVOKED},
    ConsentStatus.DECLINED: {ConsentStatus.GRANTED},  # she may change her mind
    ConsentStatus.REVOKED: {ConsentStatus.GRANTED},
}


async def _owned_storyteller(db: Db, keeper: Keeper, storyteller_id: str) -> Storyteller:
    st = await db.get(Storyteller, storyteller_id)
    if st is None or st.family_id != keeper.family_id:
        raise HTTPException(status_code=404, detail="storyteller not found")
    return st


@router.post("/storytellers", response_model=schemas.StorytellerOut, tags=["storytellers"])
async def create_storyteller(
    body: schemas.StorytellerIn, db: Db, keeper: CurrentKeeper
) -> Storyteller:
    st = Storyteller(family_id=keeper.family_id, **body.model_dump())
    db.add(st)
    await db.commit()
    return st


@router.get("/storytellers", response_model=list[schemas.StorytellerOut], tags=["storytellers"])
async def list_storytellers(db: Db, keeper: CurrentKeeper) -> list[Storyteller]:
    return list(
        await db.scalars(
            select(Storyteller).where(Storyteller.family_id == keeper.family_id)
        )
    )


@router.get(
    "/storytellers/{storyteller_id}",
    response_model=schemas.StorytellerOut,
    tags=["storytellers"],
)
async def get_storyteller(storyteller_id: str, db: Db, keeper: CurrentKeeper) -> Storyteller:
    return await _owned_storyteller(db, keeper, storyteller_id)


@router.patch(
    "/storytellers/{storyteller_id}/consent",
    response_model=schemas.StorytellerOut,
    tags=["storytellers"],
)
async def set_consent(
    storyteller_id: str, body: schemas.ConsentIn, db: Db, keeper: CurrentKeeper
) -> Storyteller:
    st = await _owned_storyteller(db, keeper, storyteller_id)
    if body.consent not in _CONSENT_TRANSITIONS[st.consent]:
        raise HTTPException(
            status_code=409,
            detail=f"cannot transition consent {st.consent.value} -> {body.consent.value}",
        )
    st.consent = body.consent
    from katha_core.models import _now  # noqa: PLC0415

    st.consented_at = _now() if body.consent == ConsentStatus.GRANTED else st.consented_at
    await db.commit()
    return st


# --- Sessions -----------------------------------------------------------------


@router.get(
    "/storytellers/{storyteller_id}/sessions",
    response_model=list[schemas.SessionOut],
    tags=["sessions"],
)
async def list_sessions(storyteller_id: str, db: Db, keeper: CurrentKeeper) -> list[CallSession]:
    await _owned_storyteller(db, keeper, storyteller_id)
    return list(
        await db.scalars(
            select(CallSession)
            .where(CallSession.storyteller_id == storyteller_id)
            .order_by(CallSession.created_at.desc())
        )
    )


@router.get(
    "/sessions/{session_id}", response_model=schemas.SessionDetailOut, tags=["sessions"]
)
async def get_session(session_id: str, db: Db, keeper: CurrentKeeper) -> schemas.SessionDetailOut:
    call = await db.get(CallSession, session_id)
    if call is None:
        raise HTTPException(status_code=404, detail="session not found")
    await _owned_storyteller(db, keeper, call.storyteller_id)
    segments = (
        await db.scalars(
            select(TranscriptSegment)
            .where(TranscriptSegment.session_id == session_id)
            .order_by(TranscriptSegment.idx)
        )
    ).all()
    return schemas.SessionDetailOut(
        **schemas.SessionOut.model_validate(call).model_dump(),
        segments=[schemas.SegmentOut.model_validate(s) for s in segments],
    )


# --- Chapters -----------------------------------------------------------------


@router.get(
    "/storytellers/{storyteller_id}/chapters",
    response_model=list[schemas.ChapterOut],
    tags=["chapters"],
)
async def list_chapters(storyteller_id: str, db: Db, keeper: CurrentKeeper) -> list[Chapter]:
    await _owned_storyteller(db, keeper, storyteller_id)
    return list(
        await db.scalars(
            select(Chapter)
            .where(Chapter.storyteller_id == storyteller_id)
            .order_by(Chapter.ordinal, Chapter.version.desc())
        )
    )


@router.get("/chapters/{chapter_id}", response_model=schemas.ChapterDetailOut, tags=["chapters"])
async def get_chapter(chapter_id: str, db: Db, keeper: CurrentKeeper) -> schemas.ChapterDetailOut:
    ch = await db.get(Chapter, chapter_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="chapter not found")
    await _owned_storyteller(db, keeper, ch.storyteller_id)

    # Resolve sentence anchors to playable audio spans.
    segment_ids = {
        sid for para in ch.body for sent in para for sid in sent.get("segment_ids", [])
    }
    seg_rows = (
        await db.scalars(
            select(TranscriptSegment).where(TranscriptSegment.id.in_(segment_ids))
        )
    ).all() if segment_ids else []
    sessions = {
        c.id: c
        for c in (
            await db.scalars(
                select(CallSession).where(
                    CallSession.id.in_({s.session_id for s in seg_rows})
                )
            )
        ).all()
    } if seg_rows else {}
    by_id = {s.id: s for s in seg_rows}

    def anchors_for(sent: dict) -> list[schemas.AnchorOut]:
        out = []
        for sid in sent.get("segment_ids", []):
            seg = by_id.get(sid)
            if seg is None:
                continue
            out.append(
                schemas.AnchorOut(
                    segment_id=seg.id,
                    session_id=seg.session_id,
                    audio_key=sessions[seg.session_id].audio_key,
                    t_start_ms=seg.t_start_ms,
                    t_end_ms=seg.t_end_ms,
                )
            )
        return out

    return schemas.ChapterDetailOut(
        **schemas.ChapterOut.model_validate(ch).model_dump(),
        paragraphs=[
            [
                schemas.SentenceOut(
                    text=sent["text"], bridge=sent.get("bridge", False), anchors=anchors_for(sent)
                )
                for sent in para
            ]
            for para in ch.body
        ],
    )


# --- Audio --------------------------------------------------------------------


@router.get("/audio/{audio_key:path}", tags=["audio"])
async def resolve_audio(audio_key: str, db: Db, keeper: CurrentKeeper) -> dict:
    """Short-lived playback URL for a call recording the keeper's family owns."""
    from .. import storage  # noqa: PLC0415

    call = await db.scalar(select(CallSession).where(CallSession.audio_key == audio_key))
    if call is None:
        raise HTTPException(status_code=404, detail="recording not found")
    await _owned_storyteller(db, keeper, call.storyteller_id)
    if not storage.configured():
        raise HTTPException(status_code=503, detail="audio storage not configured")
    return {"url": storage.presigned_audio_url(audio_key), "expires_in": 600}


# --- Follow-ups ---------------------------------------------------------------


@router.get(
    "/storytellers/{storyteller_id}/follow-ups",
    response_model=list[schemas.FollowUpOut],
    tags=["follow-ups"],
)
async def list_follow_ups(storyteller_id: str, db: Db, keeper: CurrentKeeper) -> list[FollowUp]:
    await _owned_storyteller(db, keeper, storyteller_id)
    return list(
        await db.scalars(
            select(FollowUp)
            .where(FollowUp.storyteller_id == storyteller_id)
            .order_by(FollowUp.priority.desc())
        )
    )


@router.post(
    "/follow-ups/{follow_up_id}/retire", response_model=schemas.FollowUpOut, tags=["follow-ups"]
)
async def retire_follow_up(follow_up_id: str, db: Db, keeper: CurrentKeeper) -> FollowUp:
    fu = await db.get(FollowUp, follow_up_id)
    if fu is None:
        raise HTTPException(status_code=404, detail="follow-up not found")
    await _owned_storyteller(db, keeper, fu.storyteller_id)
    fu.status = FollowUpStatus.RETIRED
    await db.commit()
    return fu
