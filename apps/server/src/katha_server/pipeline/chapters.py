"""Chapter writing and fidelity verification.

A chapter is memoir prose in the storyteller's first-person voice. Its body is
structured: paragraphs of sentences, each sentence either
  - anchored: carries segment_ids whose audio spans support it, or
  - a bridge: pure narrative connective tissue that asserts NO life facts.

The verifier is the "no gimmicks" gate. A chapter is promoted DRAFT → VERIFIED
only when every anchored sentence is supported by its segments and every
bridge sentence is genuinely fact-free. Anything else stays DRAFT and is
reported for regeneration. The family never sees an unverified chapter.
"""

from collections.abc import Callable
from dataclasses import dataclass

import anthropic
from katha_core.config import settings
from katha_core.models import Chapter, ChapterStatus, TranscriptSegment
from pydantic import BaseModel, Field


class SentenceDraft(BaseModel):
    text: str
    segment_ids: list[str] = Field(default_factory=list)
    bridge: bool = False


class ChapterDraft(BaseModel):
    title: str
    paragraphs: list[list[SentenceDraft]]


_WRITER_SYSTEM = """\
You are the memoir writer for a family biographer. You write a chapter of a
living memoir in the storyteller's own first-person voice, from the transcript
segments of her recorded conversations.

Craft:
- First person, warm and concrete. Preserve her turns of phrase; keep
  original-language words where they carry weight (with gentle context, never
  footnotes).
- Scenes over summaries. Let the reader stand in the kitchen, hear the train.
- Short chapter: 4-8 paragraphs.

Fidelity rules (absolute):
- Every sentence that says anything about her life MUST carry the segment ids
  that support it, and must not go beyond what those segments say.
- Purely connective sentences (transitions with no factual content) must be
  marked bridge=true and carry no segment ids.
- Never invent details, dates, names, feelings, or weather. If the transcript
  doesn't say it, the chapter doesn't say it.
"""


def _segments_block(segments: list[TranscriptSegment]) -> str:
    return "\n".join(f"[{s.id}] {s.speaker.value}: {s.text}" for s in segments)


def draft_chapter(
    theme: str, segments: list[TranscriptSegment], feedback: str = ""
) -> ChapterDraft:
    """Blocking Claude call — run via asyncio.to_thread from async code.
    `feedback` carries the verifier's per-sentence failures on a retry."""
    content = (
        f"Chapter theme: {theme}\n\n"
        f"Transcript segments (id, speaker, text):\n{_segments_block(segments)}"
    )
    if feedback:
        content += (
            "\n\nYour previous draft FAILED fidelity verification. Rewrite the "
            "chapter fixing exactly these problems (anchor every factual sentence "
            f"to real segments; keep bridges fact-free):\n{feedback}"
        )
    client = anthropic.Anthropic(api_key=settings().anthropic_api_key or None)
    response = client.messages.parse(
        model=settings().interviewer_model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=_WRITER_SYSTEM,
        messages=[{"role": "user", "content": content}],
        output_format=ChapterDraft,
    )
    draft = response.parsed_output
    if draft is None:
        raise RuntimeError("chapter draft returned no parsable output")
    return draft


# --- Verification -----------------------------------------------------------

# judge(sentence_text, supporting_segment_texts, is_bridge) -> ok
Judge = Callable[[str, list[str], bool], bool]


@dataclass
class SentenceVerdict:
    text: str
    ok: bool
    reason: str = ""


@dataclass
class VerificationReport:
    verdicts: list[SentenceVerdict]

    @property
    def passed(self) -> bool:
        return all(v.ok for v in self.verdicts)

    @property
    def failures(self) -> list[SentenceVerdict]:
        return [v for v in self.verdicts if not v.ok]


class _JudgeVerdict(BaseModel):
    supported: bool
    reason: str = ""


def llm_judge(sentence: str, segment_texts: list[str], bridge: bool) -> bool:
    """Haiku fidelity check for one sentence. Blocking."""
    client = anthropic.Anthropic(api_key=settings().anthropic_api_key or None)
    if bridge:
        question = (
            "Is this memoir sentence pure narrative transition, asserting NO specific "
            "fact about the storyteller's life (no events, people, places, dates, "
            f"possessions, or feelings attributed to her)?\n\nSentence: {sentence}"
        )
    else:
        joined = "\n".join(f"- {t}" for t in segment_texts)
        question = (
            "Does the transcript below FULLY support this memoir sentence? The sentence "
            "may rephrase and translate, but must not add facts, intensify claims, or "
            f"attribute anything not present.\n\nSentence: {sentence}\n\nTranscript:\n{joined}"
        )
    response = client.messages.parse(
        model=settings().utility_model,
        max_tokens=300,
        system="You are a strict fidelity checker for a memoir. Judge only support, not style.",
        messages=[{"role": "user", "content": question}],
        output_format=_JudgeVerdict,
    )
    verdict = response.parsed_output
    return bool(verdict and verdict.supported)


def verify_chapter(
    draft: ChapterDraft,
    segments: list[TranscriptSegment],
    judge: Judge = llm_judge,
) -> VerificationReport:
    by_id = {s.id: s for s in segments}
    verdicts: list[SentenceVerdict] = []

    for paragraph in draft.paragraphs:
        for sent in paragraph:
            if sent.bridge:
                if sent.segment_ids:
                    verdicts.append(
                        SentenceVerdict(sent.text, False, "bridge sentence carries anchors")
                    )
                    continue
                ok = judge(sent.text, [], True)
                verdicts.append(
                    SentenceVerdict(sent.text, ok, "" if ok else "bridge asserts facts")
                )
                continue

            if not sent.segment_ids:
                verdicts.append(SentenceVerdict(sent.text, False, "no anchors"))
                continue
            missing = [i for i in sent.segment_ids if i not in by_id]
            if missing:
                verdicts.append(
                    SentenceVerdict(sent.text, False, f"phantom segment ids: {missing}")
                )
                continue
            texts = [by_id[i].text for i in sent.segment_ids]
            ok = judge(sent.text, texts, False)
            verdicts.append(
                SentenceVerdict(sent.text, ok, "" if ok else "not supported by anchors")
            )

    return VerificationReport(verdicts)


def write_verified_chapter(
    theme: str,
    segments: list[TranscriptSegment],
    writer=draft_chapter,
    judge: Judge = llm_judge,
    max_attempts: int = 2,
) -> tuple[ChapterDraft, VerificationReport]:
    """Draft → verify → on failure, re-draft with the verifier's feedback.
    Returns the last (draft, report); the caller decides what a failed final
    report means (it stays DRAFT and invisible to the family)."""
    feedback = ""
    draft = writer(theme, segments)
    report = verify_chapter(draft, segments, judge)
    for _ in range(max_attempts - 1):
        if report.passed:
            break
        feedback = "\n".join(f"- {v.text!r}: {v.reason}" for v in report.failures)
        draft = writer(theme, segments, feedback)
        report = verify_chapter(draft, segments, judge)
    return draft, report


def to_chapter(
    draft: ChapterDraft,
    report: VerificationReport,
    storyteller_id: str,
    ordinal: int,
    version: int = 1,
) -> Chapter:
    """Materialize a Chapter row; VERIFIED only if the report passed."""
    body = [
        [
            {"text": s.text, "segment_ids": s.segment_ids, "bridge": s.bridge}
            for s in paragraph
        ]
        for paragraph in draft.paragraphs
    ]
    return Chapter(
        storyteller_id=storyteller_id,
        ordinal=ordinal,
        version=version,
        title=draft.title,
        body=body,
        status=ChapterStatus.VERIFIED if report.passed else ChapterStatus.DRAFT,
    )
