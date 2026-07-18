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


class FollowUpOut(BaseModel):
    id: str
    question: str
    rationale: str
    priority: int
    status: FollowUpStatus

    model_config = {"from_attributes": True}
