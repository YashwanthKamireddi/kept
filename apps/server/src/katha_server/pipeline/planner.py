"""Session planner: decide what the next call should explore.

v0 is deterministic: a life-arc curriculum provides the spine, pending
follow-ups provide the threads. The live interviewer is explicitly licensed to
abandon the plan when a better thread appears — the plan is a safety net
against aimless sessions, not a script.
"""

from katha_core.models import FollowUp, FollowUpStatus, Storyteller

LIFE_ARC = [
    "Childhood home and the world she grew up in",
    "Parents, siblings, and the family she came from",
    "School years, friends, and mischief",
    "Youth, marriage, and leaving home",
    "Work, livelihood, and making a life",
    "Raising children and family life",
    "Festivals, food, and the rituals of the year",
    "Hardships weathered and how she got through them",
    "Beliefs, lessons, and what she wants remembered",
]

FIRST_SESSION_PLAN = """\
This is the very first conversation.
1. Introduce yourself warmly: you are Katha, the family asked you to help
   record her life stories so the grandchildren will always have them.
2. Confirm she is happy to talk and to be recorded (consent) — in plain,
   warm words, not legal language. If she declines, thank her gently and end.
3. Start easy and concrete: where she was born, the house she grew up in,
   who was in the family. Let her lead from there.
Keep it shorter than a regular session — this call is about trust.
"""

MAX_THREADS = 3


def plan_session(
    storyteller: Storyteller,
    completed_sessions: int,
    follow_ups: list[FollowUp],
) -> tuple[list[str], str]:
    """Returns (planned_themes, session_plan_text)."""
    if completed_sessions == 0:
        return (["introduction", LIFE_ARC[0]], FIRST_SESSION_PLAN)

    theme = LIFE_ARC[min(completed_sessions - 1, len(LIFE_ARC) - 1)]
    pending = sorted(
        (f for f in follow_ups if f.status == FollowUpStatus.PENDING),
        key=lambda f: -f.priority,
    )[:MAX_THREADS]

    lines = [f"Main theme for today: {theme}."]
    if pending:
        lines.append("Threads from earlier conversations to pull if the moment is right:")
        for fu in pending:
            why = f" ({fu.rationale})" if fu.rationale else ""
            lines.append(f"- {fu.question}{why}")
    lines.append(
        "The theme is a starting point, not a script — if she opens a door, walk through it."
    )
    themes = [theme, *[fu.question for fu in pending]]
    return themes, "\n".join(lines)
