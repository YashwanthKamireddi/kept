from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from katha_core.models import (
    ApiToken,
    CallSession,
    Chapter,
    ChapterStatus,
    ConsentStatus,
    Entity,
    EntityKind,
    Fact,
    Family,
    FollowUp,
    FollowUpStatus,
    Keeper,
    Speaker,
    Storyteller,
    TranscriptSegment,
)
from sqlalchemy import func, select

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


@router.post("/auth/login", response_model=schemas.SignupOut, tags=["auth"])
async def login(body: schemas.LoginIn, db: Db) -> schemas.SignupOut:
    """Dev stub: token by email, no verification. The magic-link flow will add
    the email round-trip and mint the same ApiToken rows."""
    keeper = await db.scalar(select(Keeper).where(Keeper.email == body.email))
    if keeper is None:
        raise HTTPException(status_code=404, detail="no account with this email")
    token = ApiToken(keeper_id=keeper.id)
    db.add(token)
    await db.commit()
    return schemas.SignupOut(token=token.token, keeper_id=keeper.id, family_id=keeper.family_id)


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


@router.delete("/storytellers/{storyteller_id}", tags=["storytellers"])
async def erase(storyteller_id: str, db: Db, keeper: CurrentKeeper) -> dict:
    """Right to erasure: permanently delete a storyteller and all derived
    data (sessions, transcripts, facts, chapters, follow-ups), plus their
    call recordings from object storage. Irreversible."""
    from .. import erasure, storage  # noqa: PLC0415

    st = await _owned_storyteller(db, keeper, storyteller_id)
    result = await erasure.erase_storyteller(db, st)
    if storage.configured():
        for key in result["audio_keys"]:
            try:
                storage.delete_audio(key)
            except Exception:  # noqa: BLE001 — best-effort; DB record already gone
                pass
    return {"erased": True, "deleted": result["deleted"]}


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


@router.get(
    "/storytellers/{storyteller_id}/portrait",
    response_model=schemas.PortraitOut,
    tags=["storytellers"],
)
async def get_portrait(
    storyteller_id: str, db: Db, keeper: CurrentKeeper
) -> schemas.PortraitOut:
    st = await _owned_storyteller(db, keeper, storyteller_id)
    return schemas.PortraitOut(
        name=st.name,
        life_brief=st.life_brief or "",
        life_brief_version=st.life_brief_version,
    )


# People first — they carry the most; then the places, seasons, and things.
_LIFE_GROUPS: list[tuple[EntityKind, str]] = [
    (EntityKind.PERSON, "The people they carried"),
    (EntityKind.PLACE, "The places"),
    (EntityKind.ERA, "The seasons of a life"),
    (EntityKind.OBJECT, "The things they kept"),
    (EntityKind.EVENT, "The moments"),
]


@router.get(
    "/storytellers/{storyteller_id}/life",
    response_model=schemas.LifeOut,
    tags=["storytellers"],
)
async def get_life(storyteller_id: str, db: Db, keeper: CurrentKeeper) -> schemas.LifeOut:
    """The living portrait — the people, places, and things a life kept
    returning to, each carrying the words the storyteller actually spoke about
    them. Assembled from the life graph (entities + provenance-anchored facts),
    never invented."""
    st = await _owned_storyteller(db, keeper, storyteller_id)

    entities = list(
        await db.scalars(select(Entity).where(Entity.storyteller_id == storyteller_id))
    )
    facts = list(
        await db.scalars(
            select(Fact)
            .where(Fact.storyteller_id == storyteller_id, Fact.entity_id.is_not(None))
            .order_by(Fact.created_at)
        )
    )

    # Resolve each fact's provenance to the segment the storyteller actually spoke.
    seg_ids = {f.segment_ids[0] for f in facts if f.segment_ids}
    segs = {
        s.id: s
        for s in (
            await db.scalars(
                select(TranscriptSegment).where(TranscriptSegment.id.in_(seg_ids))
            )
        ).all()
    } if seg_ids else {}
    sessions = {
        c.id: c
        for c in (
            await db.scalars(
                select(CallSession).where(
                    CallSession.id.in_({s.session_id for s in segs.values()})
                )
            )
        ).all()
    } if segs else {}

    # Group her words by who/what they were about. Several facts can come from
    # one utterance — keep each utterance once per entity, in the order spoken.
    moments: dict[str, list[schemas.LifeMoment]] = {}
    seen: dict[str, set[str]] = {}
    for f in facts:
        if not f.segment_ids:
            continue
        seg = segs.get(f.segment_ids[0])
        if seg is None or seg.speaker != Speaker.STORYTELLER:
            continue
        if seg.id in seen.setdefault(f.entity_id, set()):
            continue
        seen[f.entity_id].add(seg.id)
        sess = sessions.get(seg.session_id)
        anchor = (
            schemas.AnchorOut(
                segment_id=seg.id,
                session_id=seg.session_id,
                audio_key=sess.audio_key,
                t_start_ms=seg.t_start_ms,
                t_end_ms=seg.t_end_ms,
            )
            if sess and sess.audio_key
            else None
        )
        moments.setdefault(f.entity_id, []).append(
            schemas.LifeMoment(quote=seg.text, anchor=anchor)
        )

    groups: list[schemas.LifeGroup] = []
    for kind, label in _LIFE_GROUPS:
        ents = [e for e in entities if e.kind == kind]
        if not ents:
            continue
        groups.append(
            schemas.LifeGroup(
                kind=kind.value,
                label=label,
                entities=[
                    schemas.LifeEntity(
                        name=e.canonical_name, summary=e.summary, moments=moments.get(e.id, [])
                    )
                    for e in ents
                ],
            )
        )

    return schemas.LifeOut(name=st.name, groups=groups)


async def _resolve_paragraphs(db: Db, ch: Chapter) -> list[list[schemas.SentenceOut]]:
    """Resolve a chapter's sentence anchors to playable audio spans. Shared by
    the single-chapter reader and the whole-memoir view so both render the same
    gold voice-threads from one source of truth."""
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

    return [
        [
            schemas.SentenceOut(
                text=sent["text"], bridge=sent.get("bridge", False), anchors=anchors_for(sent)
            )
            for sent in para
        ]
        for para in ch.body
    ]


@router.get("/chapters/{chapter_id}", response_model=schemas.ChapterDetailOut, tags=["chapters"])
async def get_chapter(chapter_id: str, db: Db, keeper: CurrentKeeper) -> schemas.ChapterDetailOut:
    ch = await db.get(Chapter, chapter_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="chapter not found")
    await _owned_storyteller(db, keeper, ch.storyteller_id)
    return schemas.ChapterDetailOut(
        **schemas.ChapterOut.model_validate(ch).model_dump(),
        paragraphs=await _resolve_paragraphs(db, ch),
    )


async def _visible_chapters(db: Db, storyteller_id: str) -> list[Chapter]:
    """The family-visible book: verified or published chapters, latest version
    per ordinal, in reading order. The fidelity gate lives here — drafts never
    reach the family, in the book or in search."""
    rows = list(
        await db.scalars(
            select(Chapter)
            .where(
                Chapter.storyteller_id == storyteller_id,
                Chapter.status.in_((ChapterStatus.VERIFIED, ChapterStatus.PUBLISHED)),
            )
            .order_by(Chapter.ordinal, Chapter.version.desc())
        )
    )
    # Rows arrive version-desc within each ordinal; keep the first (latest) seen.
    latest: dict[int, Chapter] = {}
    for ch in rows:
        latest.setdefault(ch.ordinal, ch)
    return [latest[o] for o in sorted(latest)]


def _snippet(text: str, needle: str, width: int = 120) -> str:
    """A readable window around the first match, with ellipses where clipped."""
    lo = text.lower().find(needle)
    if lo < 0:
        return text[:width].strip()
    start = max(0, lo - width // 3)
    end = min(len(text), lo + len(needle) + (2 * width) // 3)
    return ("…" if start > 0 else "") + text[start:end].strip() + ("…" if end < len(text) else "")


@router.get(
    "/storytellers/{storyteller_id}/memoir",
    response_model=schemas.MemoirOut,
    tags=["chapters"],
)
async def get_memoir(
    storyteller_id: str, db: Db, keeper: CurrentKeeper
) -> schemas.MemoirOut:
    """The whole book. Every family-visible chapter (verified or published),
    latest version per ordinal, assembled in order into one continuous read."""
    st = await _owned_storyteller(db, keeper, storyteller_id)
    chapters = [
        schemas.MemoirChapterOut(
            ordinal=ch.ordinal,
            title=ch.title,
            paragraphs=await _resolve_paragraphs(db, ch),
        )
        for ch in await _visible_chapters(db, storyteller_id)
    ]
    return schemas.MemoirOut(name=st.name, chapters=chapters)


@router.get(
    "/storytellers/{storyteller_id}/search",
    response_model=schemas.SearchOut,
    tags=["chapters"],
)
async def search_storyteller(
    storyteller_id: str, db: Db, keeper: CurrentKeeper, q: str = ""
) -> schemas.SearchOut:
    """Find a story or a moment. Searches the written book (family-visible
    chapters) and the storyteller's own recorded words (their transcript
    turns) — never the interviewer's lines, never unverified drafts."""
    await _owned_storyteller(db, keeper, storyteller_id)
    needle = q.strip().lower()
    if len(needle) < 2:
        return schemas.SearchOut(query=q, chapters=[], moments=[])

    # The book: the first matching sentence (or the title) becomes the snippet.
    chapter_hits: list[schemas.SearchChapterHit] = []
    for ch in await _visible_chapters(db, storyteller_id):
        match = next(
            (sent["text"] for para in ch.body for sent in para if needle in sent["text"].lower()),
            None,
        )
        if match is None and needle in ch.title.lower():
            match = ch.title
        if match is not None:
            chapter_hits.append(
                schemas.SearchChapterHit(
                    chapter_id=ch.id,
                    ordinal=ch.ordinal,
                    title=ch.title,
                    snippet=_snippet(match, needle),
                )
            )

    # Their own words: transcript turns the storyteller actually spoke.
    escaped = needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    seg_rows = (
        await db.execute(
            select(TranscriptSegment, CallSession.started_at)
            .join(CallSession, TranscriptSegment.session_id == CallSession.id)
            .where(
                CallSession.storyteller_id == storyteller_id,
                TranscriptSegment.speaker == Speaker.STORYTELLER,
                func.lower(TranscriptSegment.text).like(f"%{escaped}%", escape="\\"),
            )
            .order_by(CallSession.created_at.desc(), TranscriptSegment.idx)
            .limit(20)
        )
    ).all()
    moment_hits = [
        schemas.SearchMomentHit(
            session_id=seg.session_id, started_at=started, snippet=_snippet(seg.text, needle)
        )
        for seg, started in seg_rows
    ]

    return schemas.SearchOut(query=q, chapters=chapter_hits, moments=moment_hits)


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


@router.get("/audio-file/{audio_key:path}", tags=["audio"])
async def stream_local_audio(audio_key: str, exp: int = 0, sig: str = "") -> FileResponse:
    """Stream a recording from the local dev audio dir. Authorised by the
    short-lived HMAC signature minted in /audio (not the bearer token), so the
    audio player can fetch it directly — exactly as it would a presigned R2 URL."""
    from .. import storage  # noqa: PLC0415

    if not storage.verify_local(audio_key, exp, sig):
        raise HTTPException(status_code=403, detail="invalid or expired link")
    path = storage.local_audio_path(audio_key)
    if path is None:
        raise HTTPException(status_code=404, detail="recording not found")
    return FileResponse(str(path))


# --- Follow-ups ---------------------------------------------------------------


@router.get(
    "/storytellers/{storyteller_id}/follow-ups",
    response_model=list[schemas.FollowUpOut],
    tags=["follow-ups"],
)
async def list_follow_ups(
    storyteller_id: str, db: Db, keeper: CurrentKeeper
) -> list[schemas.FollowUpOut]:
    await _owned_storyteller(db, keeper, storyteller_id)
    rows = (
        await db.execute(
            select(FollowUp, Keeper.name)
            .outerjoin(Keeper, FollowUp.asked_by_keeper_id == Keeper.id)
            .where(FollowUp.storyteller_id == storyteller_id)
            .order_by(FollowUp.priority.desc())
        )
    ).all()
    return [
        schemas.FollowUpOut(
            **schemas.FollowUpOut.model_validate(fu).model_dump(exclude={"asked_by_name"}),
            asked_by_name=name,
        )
        for fu, name in rows
    ]


@router.post(
    "/storytellers/{storyteller_id}/follow-ups",
    response_model=schemas.FollowUpOut,
    tags=["follow-ups"],
)
async def ask_something(
    storyteller_id: str, body: schemas.FollowUpIn, db: Db, keeper: CurrentKeeper
) -> schemas.FollowUpOut:
    """'Ask her something' — a family-suggested question. It joins the open
    threads the session planner already draws from, so it reaches a real call."""
    await _owned_storyteller(db, keeper, storyteller_id)
    fu = FollowUp(
        storyteller_id=storyteller_id,
        question=body.question.strip(),
        rationale=body.rationale.strip(),
        priority=6,  # family asks rank above routine threads, below urgent ones
        asked_by_keeper_id=keeper.id,
    )
    db.add(fu)
    await db.commit()
    return schemas.FollowUpOut(
        **schemas.FollowUpOut.model_validate(fu).model_dump(exclude={"asked_by_name"}),
        asked_by_name=keeper.name,
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
