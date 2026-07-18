"""Structured extraction from a completed call's transcript.

One Claude call per session turns diarized segments into entities, facts, and
follow-up threads. Provenance discipline is enforced twice: the prompt demands
segment indices for every fact, and `validate_provenance` drops anything whose
indices don't exist in the transcript.
"""

from typing import Literal

import anthropic
from katha_core.config import settings
from katha_core.models import Speaker, TranscriptSegment
from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    kind: Literal["person", "place", "event", "era", "object"]
    name: str
    aliases: list[str] = Field(default_factory=list)
    summary: str = ""


class ExtractedFact(BaseModel):
    statement: str = Field(description="One factual statement in English, third person.")
    entity_names: list[str] = Field(default_factory=list)
    segment_idxs: list[int] = Field(description="Transcript segment indices supporting this.")
    confidence: float = 1.0


class ExtractedFollowUp(BaseModel):
    question: str
    rationale: str = ""
    priority: int = Field(ge=0, le=10, default=5)


class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity]
    facts: list[ExtractedFact]
    follow_ups: list[ExtractedFollowUp]


_SYSTEM = """\
You are the memory engine of a family biographer. You are given the diarized
transcript of one phone conversation between a warm AI biographer and an elder
storyteller, as numbered segments.

Extract, faithfully and only from what the storyteller actually said:
- entities: people, places, events, eras, and meaningful objects in their life.
  Use the storyteller's own names for them (keep original-language names as
  spoken, transliterated; put variants in aliases).
- facts: discrete statements about the storyteller's life, written in English,
  third person ("She moved to Vijayawada in 1968 after her marriage").
  Every fact MUST list the segment indices that support it. Never infer beyond
  what was said; if uncertain, lower confidence rather than embellish.
- follow_ups: specific threads a loving interviewer should pull next time —
  mentioned-but-unexplored people, interrupted stories, emotionally significant
  moments passed over quickly. Priority 0-10.

The biographer's own words are context only — extract nothing from them except
to resolve what the storyteller was answering.
"""


def transcript_block(segments: list[TranscriptSegment]) -> str:
    lines = []
    for seg in segments:
        who = "STORYTELLER" if seg.speaker == Speaker.STORYTELLER else "BIOGRAPHER"
        lines.append(f"[{seg.idx}] {who}: {seg.text}")
    return "\n".join(lines)


def validate_provenance(result: ExtractionResult, valid_idxs: set[int]) -> ExtractionResult:
    """Drop facts whose claimed provenance doesn't exist. No anchor, no fact."""
    kept = [f for f in result.facts if f.segment_idxs and set(f.segment_idxs) <= valid_idxs]
    return result.model_copy(update={"facts": kept})


def extract(segments: list[TranscriptSegment]) -> ExtractionResult:
    """Blocking Claude call — run via asyncio.to_thread from async code."""
    client = anthropic.Anthropic(api_key=settings().anthropic_api_key)
    response = client.messages.parse(
        model=settings().interviewer_model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=_SYSTEM,
        messages=[{"role": "user", "content": transcript_block(segments)}],
        output_format=ExtractionResult,
    )
    result = response.parsed_output
    if result is None:
        raise RuntimeError("extraction returned no parsable output")
    return validate_provenance(result, {s.idx for s in segments})
