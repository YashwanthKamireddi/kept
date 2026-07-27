from datetime import datetime

from katha_core.models import ChapterStatus, ConsentStatus, FollowUpStatus, SessionStatus
from pydantic import BaseModel, EmailStr, Field


class SignupIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    family_name: str = Field(min_length=1, max_length=120)


class SignupOut(BaseModel):
    token: str
    keeper_id: str
    family_id: str


class LoginIn(BaseModel):
    email: EmailStr


class StorytellerIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address_as: str = Field(min_length=1, max_length=120)
    phone_e164: str = Field(pattern=r"^\+\d{7,15}$")
    language: str = "en"
    timezone: str = "UTC"
    keeper_notes: str = ""
    next_call_at: datetime | None = None
    cadence_days: int = Field(default=7, ge=1, le=30)


class StorytellerOut(BaseModel):
    id: str
    name: str
    address_as: str
    phone_e164: str
    language: str
    timezone: str
    consent: ConsentStatus
    life_brief_version: int
    next_call_at: datetime | None
    cadence_days: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PortraitOut(BaseModel):
    """A warm profile of the storyteller, assembled from their own stories —
    the Life Brief the pipeline maintains, surfaced to the family."""

    name: str
    life_brief: str
    life_brief_version: int


class ConsentIn(BaseModel):
    consent: ConsentStatus


class SessionOut(BaseModel):
    id: str
    status: SessionStatus
    scheduled_at: datetime | None
    started_at: datetime | None
    duration_seconds: int
    audio_key: str

    model_config = {"from_attributes": True}


class SegmentOut(BaseModel):
    id: str
    idx: int
    speaker: str
    t_start_ms: int
    t_end_ms: int
    text: str

    model_config = {"from_attributes": True}


class SessionDetailOut(SessionOut):
    segments: list[SegmentOut]


class AnchorOut(BaseModel):
    segment_id: str
    session_id: str
    audio_key: str
    t_start_ms: int
    t_end_ms: int


class SentenceOut(BaseModel):
    text: str
    bridge: bool
    anchors: list[AnchorOut]


class ChapterOut(BaseModel):
    id: str
    ordinal: int
    version: int
    title: str
    status: ChapterStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ChapterDetailOut(ChapterOut):
    paragraphs: list[list[SentenceOut]]


class MemoirChapterOut(BaseModel):
    ordinal: int
    title: str
    paragraphs: list[list[SentenceOut]]


class MemoirOut(BaseModel):
    """The whole book: every family-visible chapter, in order, assembled into
    one continuous read — the keepsake the product exists to produce."""

    name: str
    chapters: list[MemoirChapterOut]


class SearchChapterHit(BaseModel):
    chapter_id: str
    ordinal: int
    title: str
    snippet: str


class SearchMomentHit(BaseModel):
    session_id: str
    started_at: datetime | None
    snippet: str


class SearchOut(BaseModel):
    """Finding a story or a moment across a storyteller's memoir. `chapters`
    are matches in the written book; `moments` are matches in the storyteller's
    own recorded words."""

    query: str
    chapters: list[SearchChapterHit]
    moments: list[SearchMomentHit]


class LifeMoment(BaseModel):
    """Something the storyteller actually said about a person or place. `anchor`
    is present only when the recording exists — so it plays in their real voice
    where we have it, and reads as their words where we don't. Never faked."""

    quote: str
    anchor: AnchorOut | None = None


class LifeEntity(BaseModel):
    name: str
    summary: str
    moments: list[LifeMoment]


class LifeGroup(BaseModel):
    kind: str
    label: str
    entities: list[LifeEntity]


class LifeOut(BaseModel):
    """The living portrait: the people, places, and things a life kept coming
    back to — each carrying the words the storyteller spoke about them. Built
    from the life graph the pipeline maintains, with real provenance."""

    name: str
    groups: list[LifeGroup]


class FollowUpIn(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    rationale: str = Field(default="", max_length=500)


class FollowUpOut(BaseModel):
    id: str
    question: str
    rationale: str
    priority: int
    status: FollowUpStatus
    asked_by_name: str | None = None

    model_config = {"from_attributes": True}
