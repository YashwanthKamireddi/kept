from katha_core.models import ChapterStatus, Speaker, TranscriptSegment
from katha_server.pipeline.chapters import (
    ChapterDraft,
    SentenceDraft,
    to_chapter,
    verify_chapter,
)


def _segments() -> list[TranscriptSegment]:
    return [
        TranscriptSegment(id="seg1", session_id="c1", idx=1, speaker=Speaker.STORYTELLER,
                          t_start_ms=0, t_end_ms=5000,
                          text="I grew up in Guntur, next to the railway station."),
        TranscriptSegment(id="seg2", session_id="c1", idx=3, speaker=Speaker.STORYTELLER,
                          t_start_ms=9000, t_end_ms=15000,
                          text="My brother Ravi walked me to school every day."),
    ]


def _draft(sentences: list[SentenceDraft]) -> ChapterDraft:
    return ChapterDraft(title="The Railway Town", paragraphs=[sentences])


def _permissive_judge(sentence: str, texts: list[str], bridge: bool) -> bool:
    return True


def test_verified_when_all_anchored_and_supported():
    draft = _draft([
        SentenceDraft(text="I grew up beside the railway station in Guntur.",
                      segment_ids=["seg1"]),
        SentenceDraft(text="Those mornings had a rhythm of their own.", bridge=True),
        SentenceDraft(text="Ravi walked me to school every day.", segment_ids=["seg2"]),
    ])
    report = verify_chapter(draft, _segments(), judge=_permissive_judge)
    assert report.passed
    chapter = to_chapter(draft, report, storyteller_id="st", ordinal=1)
    assert chapter.status == ChapterStatus.VERIFIED
    assert chapter.body[0][0]["segment_ids"] == ["seg1"]
    assert chapter.body[0][1]["bridge"] is True


def test_unanchored_factual_sentence_fails():
    draft = _draft([SentenceDraft(text="I was born in 1943 during the monsoon.")])
    report = verify_chapter(draft, _segments(), judge=_permissive_judge)
    assert not report.passed
    assert report.failures[0].reason == "no anchors"
    chapter = to_chapter(draft, report, "st", 1)
    assert chapter.status == ChapterStatus.DRAFT
    assert chapter.verification_notes == [
        {"text": "I was born in 1943 during the monsoon.", "reason": "no anchors"}
    ]


def test_phantom_anchor_fails_without_calling_judge():
    def exploding_judge(sentence, texts, bridge):
        raise AssertionError("judge must not run for phantom anchors")

    draft = _draft([SentenceDraft(text="I grew up in Guntur.", segment_ids=["nope"])])
    report = verify_chapter(draft, _segments(), judge=exploding_judge)
    assert not report.passed
    assert "phantom" in report.failures[0].reason


def test_bridge_with_anchors_is_malformed():
    draft = _draft([SentenceDraft(text="And so the years passed.",
                                  segment_ids=["seg1"], bridge=True)])
    report = verify_chapter(draft, _segments(), judge=_permissive_judge)
    assert not report.passed
    assert "bridge sentence carries anchors" in report.failures[0].reason


def test_regeneration_uses_verifier_feedback():
    from katha_server.pipeline.chapters import write_verified_chapter

    calls: list[str] = []

    def writer(theme, segments, feedback=""):
        calls.append(feedback)
        if not feedback:  # first attempt: an unanchored factual sentence
            return _draft([SentenceDraft(text="I was born during the monsoon.")])
        return _draft([
            SentenceDraft(text="I grew up in Guntur.", segment_ids=["seg1"]),
        ])

    draft, report = write_verified_chapter(
        "Childhood", _segments(), writer=writer, judge=_permissive_judge, max_attempts=2
    )
    assert report.passed
    assert len(calls) == 2
    assert "no anchors" in calls[1]  # the retry saw the verifier's reasons


def test_regeneration_gives_up_after_max_attempts():
    from katha_server.pipeline.chapters import write_verified_chapter

    def writer(theme, segments, feedback=""):
        return _draft([SentenceDraft(text="Always unanchored.")])

    _, report = write_verified_chapter(
        "Childhood", _segments(), writer=writer, judge=_permissive_judge, max_attempts=3
    )
    assert not report.passed  # caller keeps it DRAFT — family never sees it


def test_judge_rejection_blocks_promotion():
    def strict_judge(sentence, texts, bridge):
        return "embellished" not in sentence

    draft = _draft([
        SentenceDraft(text="I grew up in Guntur.", segment_ids=["seg1"]),
        SentenceDraft(text="An embellished claim about a golden palace.",
                      segment_ids=["seg1"]),
    ])
    report = verify_chapter(draft, _segments(), judge=strict_judge)
    assert not report.passed
    assert len(report.failures) == 1
    assert report.failures[0].reason == "not supported by anchors"
