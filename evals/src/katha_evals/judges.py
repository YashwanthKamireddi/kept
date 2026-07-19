"""LLM judges: score a simulated interview transcript on the craft dimensions."""

import anthropic
from katha_core import llm
from katha_core.config import settings
from pydantic import BaseModel, Field

from .personas import FIXTURE_LIFE_BRIEF, Persona
from .scorecard import DimensionScore, Scorecard


class _DimensionJudgment(BaseModel):
    dimension: str
    score: float = Field(ge=1, le=5)
    rationale: str


class _Judgment(BaseModel):
    judgments: list[_DimensionJudgment]


_JUDGE_SYSTEM = """\
You are a demanding interview-craft reviewer for a voice biographer that calls
elders. You are given the transcript of a simulated phone interview and the
LIFE BRIEF the interviewer had (its only legitimate memory).

Score 1-5 on each dimension (5 = would make a documentary interviewer proud):
- warmth: tone, patience, rituals of care; never clinical or rushed
- follow_up_quality: pulls concrete threads, asks for scenes not summaries
- memory_usage: references brief facts naturally AND never asserts anything
  absent from brief + conversation (fabricated memories = automatic 1)
- question_discipline: one question per turn; short spoken turns; no lists
- language_mirroring: matches the storyteller's language and code-mixing
- emotional_care: slows for grief, offers choice, never probes a wound

Judge only the BIOGRAPHER's craft, not the storyteller. Be strict: a 4 means
genuinely good; a 5 means you could not improve on the turn choices.
"""


def judge_dialogue(persona: Persona, rendered_dialogue: str) -> Scorecard:
    """Blocking judge call — scores one simulated interview."""
    content = (
        f"Persona notes (what good looks like here): {persona.judge_notes}\n\n"
        f"LIFE BRIEF available to the interviewer:\n{FIXTURE_LIFE_BRIEF}\n\n"
        f"TRANSCRIPT:\n{rendered_dialogue}"
    )
    if llm.backend() == "claude-cli":
        judgment = llm.cli_structured(_JUDGE_SYSTEM, content, _Judgment)
    else:
        client = anthropic.Anthropic(api_key=settings().anthropic_api_key or None)
        response = client.messages.parse(
            model=settings().interviewer_model,
            max_tokens=4000,
            thinking={"type": "adaptive"},
            system=_JUDGE_SYSTEM,
            messages=[{"role": "user", "content": content}],
            output_format=_Judgment,
        )
        judgment = response.parsed_output
    if judgment is None:
        raise RuntimeError("judge returned no parsable output")
    card = Scorecard(persona_key=persona.key)
    for j in judgment.judgments:
        card.scores[j.dimension] = DimensionScore(score=j.score, rationale=j.rationale)
    return card
