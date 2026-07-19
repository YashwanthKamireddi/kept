"""Katha domain schema.

Design invariants:
- Provenance everywhere: every Fact and every chapter sentence must trace to
  transcript segments (and therefore to real audio spans). Nothing in a memoir
  may exist without an anchor — this is enforced by the chapter verification
  pass, and the schema makes the anchors first-class.
- The elder is a Storyteller reached by plain phone; all app-side users are
  Keepers within a Family.
- The Life Brief is a compiled artifact (from Facts/Entities), cached as the
  stable prompt prefix for the live interviewer. It is derived state: it can
  always be rebuilt from sessions.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Family(Base):
    __tablename__ = "families"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(default=_now)

    keepers: Mapped[list["Keeper"]] = relationship(back_populates="family")
    storytellers: Mapped[list["Storyteller"]] = relationship(back_populates="family")


class KeeperRole(enum.StrEnum):
    OWNER = "owner"        # pays, manages storytellers
    LISTENER = "listener"  # family member, read/listen only


class Keeper(Base):
    __tablename__ = "keepers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    family_id: Mapped[str] = mapped_column(ForeignKey("families.id"))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[KeeperRole] = mapped_column(Enum(KeeperRole), default=KeeperRole.OWNER)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    family: Mapped[Family] = relationship(back_populates="keepers")


class ApiToken(Base):
    """Bearer token for a Keeper. v0 issues it directly at signup (dev stub);
    the magic-link email flow will mint these later — same table, same shape."""

    __tablename__ = "api_tokens"

    token: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    keeper_id: Mapped[str] = mapped_column(ForeignKey("keepers.id"))
    created_at: Mapped[datetime] = mapped_column(default=_now)


class ConsentStatus(enum.StrEnum):
    PENDING = "pending"      # storyteller created, intro call not yet done
    GRANTED = "granted"      # verbal consent captured on the intro call
    DECLINED = "declined"
    REVOKED = "revoked"


class Storyteller(Base):
    __tablename__ = "storytellers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    family_id: Mapped[str] = mapped_column(ForeignKey("families.id"))
    name: Mapped[str] = mapped_column(String(120))
    # How the biographer addresses them, e.g. "Grandma Rose", "Nonna", "Dadi".
    address_as: Mapped[str] = mapped_column(String(120))
    phone_e164: Mapped[str] = mapped_column(String(20))
    # BCP 47 tag chosen by the Keeper at setup — any language, no assumed home.
    language: Mapped[str] = mapped_column(String(16), default="en")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    tts_voice: Mapped[str] = mapped_column(String(64), default="")
    consent: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus), default=ConsentStatus.PENDING
    )
    consented_at: Mapped[datetime | None] = mapped_column(default=None)
    # Context the Keeper provides at setup: relationships, birthplace, era hints.
    keeper_notes: Mapped[str] = mapped_column(Text, default="")
    # Call cadence: next due call (set by the Keeper; advanced by the scheduler
    # after each completed call). Null = not scheduled.
    next_call_at: Mapped[datetime | None] = mapped_column(default=None)
    cadence_days: Mapped[int] = mapped_column(Integer, default=7)
    # Compiled memory artifact — the interviewer's cached prompt prefix.
    life_brief: Mapped[str] = mapped_column(Text, default="")
    life_brief_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    family: Mapped[Family] = relationship(back_populates="storytellers")
    sessions: Mapped[list["CallSession"]] = relationship(back_populates="storyteller")


class SessionStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    DIALING = "dialing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_ANSWER = "no_answer"
    DROPPED = "dropped"      # line cut mid-call; resumable
    FAILED = "failed"


class CallSession(Base):
    __tablename__ = "call_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    storyteller_id: Mapped[str] = mapped_column(ForeignKey("storytellers.id"))
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.SCHEDULED
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(default=None)
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    ended_at: Mapped[datetime | None] = mapped_column(default=None)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    audio_key: Mapped[str] = mapped_column(String(512), default="")  # R2 object key
    # Themes the session planner intends to explore, with rationale.
    planned_themes: Mapped[list] = mapped_column(JSON, default=list)
    # Set when this call resumes a DROPPED one.
    resumed_from_id: Mapped[str | None] = mapped_column(
        ForeignKey("call_sessions.id"), default=None
    )
    # Life Brief version used live — for memory-recall evals & reproducibility.
    life_brief_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    storyteller: Mapped[Storyteller] = relationship(back_populates="sessions")
    segments: Mapped[list["TranscriptSegment"]] = relationship(back_populates="session")


class Speaker(enum.StrEnum):
    STORYTELLER = "storyteller"
    BIOGRAPHER = "biographer"


class TranscriptSegment(Base):
    """Immutable, diarized, time-aligned transcript — the source of truth.

    Everything downstream (facts, chapters) points back here; `t_start_ms` /
    `t_end_ms` index into the session's audio object for playback anchoring.
    """

    __tablename__ = "transcript_segments"
    __table_args__ = (UniqueConstraint("session_id", "idx"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("call_sessions.id"))
    idx: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[Speaker] = mapped_column(Enum(Speaker))
    t_start_ms: Mapped[int] = mapped_column(Integer)
    t_end_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), default="te-IN")

    session: Mapped[CallSession] = relationship(back_populates="segments")


class EntityKind(enum.StrEnum):
    PERSON = "person"
    PLACE = "place"
    EVENT = "event"
    ERA = "era"        # e.g. "childhood in Guntur", "the Bombay years"
    OBJECT = "object"  # e.g. the house, the sewing machine


class Entity(Base):
    """A node in the storyteller's life graph."""

    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    storyteller_id: Mapped[str] = mapped_column(ForeignKey("storytellers.id"))
    kind: Mapped[EntityKind] = mapped_column(Enum(EntityKind))
    canonical_name: Mapped[str] = mapped_column(String(200))
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text, default="")
    attrs: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Fact(Base):
    """One extracted statement, with provenance. Facts compile into the
    Life Brief; chapters may only assert what a Fact (or segment) supports."""

    __tablename__ = "facts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    storyteller_id: Mapped[str] = mapped_column(ForeignKey("storytellers.id"))
    entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id"), default=None)
    statement: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(default=1.0)
    session_id: Mapped[str] = mapped_column(ForeignKey("call_sessions.id"))
    segment_ids: Mapped[list] = mapped_column(JSON, default=list)  # provenance
    created_at: Mapped[datetime] = mapped_column(default=_now)


class FollowUpStatus(enum.StrEnum):
    PENDING = "pending"
    ASKED = "asked"
    RETIRED = "retired"


class FollowUp(Base):
    """A thread worth pulling in a future session, generated post-call."""

    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    storyteller_id: Mapped[str] = mapped_column(ForeignKey("storytellers.id"))
    question: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, default="")
    source_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("call_sessions.id"), default=None
    )
    # Set when a family member suggested this question ("Ask her something").
    asked_by_keeper_id: Mapped[str | None] = mapped_column(
        ForeignKey("keepers.id"), default=None
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[FollowUpStatus] = mapped_column(
        Enum(FollowUpStatus), default=FollowUpStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(default=_now)


class ChapterStatus(enum.StrEnum):
    DRAFT = "draft"          # generated, not yet verified
    VERIFIED = "verified"    # every sentence anchor-checked
    PUBLISHED = "published"  # visible to the family


class Chapter(Base):
    """A living memoir chapter.

    `body` is structured JSON: a list of paragraphs, each a list of sentences:
      {"text": str, "anchors": [{"segment_id": str}, ...]}
    The verification pass refuses to promote DRAFT → VERIFIED if any sentence
    lacks anchors that actually support it.
    """

    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("storyteller_id", "ordinal", "version"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    storyteller_id: Mapped[str] = mapped_column(ForeignKey("storytellers.id"))
    ordinal: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[ChapterStatus] = mapped_column(
        Enum(ChapterStatus), default=ChapterStatus.DRAFT
    )
    # Why a DRAFT was held: [{"text": ..., "reason": ...}] from the verifier.
    verification_notes: Mapped[list] = mapped_column(JSON, default=list)
    published_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=_now)
