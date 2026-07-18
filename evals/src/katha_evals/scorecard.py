"""Scorecard: dimension scores + pass/fail gate for the interviewer."""

from dataclasses import dataclass, field

DIMENSIONS = [
    "warmth",
    "follow_up_quality",
    "memory_usage",
    "question_discipline",  # one question at a time, short spoken turns
    "language_mirroring",
    "emotional_care",
]

PASS_THRESHOLD = 3.5  # per-dimension floor on a 1-5 scale


@dataclass
class DimensionScore:
    score: float
    rationale: str = ""


@dataclass
class Scorecard:
    persona_key: str
    scores: dict[str, DimensionScore] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return bool(self.scores) and all(
            s.score >= PASS_THRESHOLD for s in self.scores.values()
        )

    @property
    def weakest(self) -> tuple[str, DimensionScore] | None:
        if not self.scores:
            return None
        name = min(self.scores, key=lambda k: self.scores[k].score)
        return name, self.scores[name]

    def render(self) -> str:
        lines = [f"── {self.persona_key} {'PASS' if self.passed else 'FAIL'} ──"]
        for name in DIMENSIONS:
            if name in self.scores:
                s = self.scores[name]
                flag = "  " if s.score >= PASS_THRESHOLD else "✗ "
                lines.append(f"{flag}{name:<20} {s.score:.1f}  {s.rationale}")
        return "\n".join(lines)
