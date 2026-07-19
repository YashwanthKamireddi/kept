"""Synthetic storytellers for interviewer evals.

Each persona is a simulated elder with a fixed inner world. The FIXTURE brief
plants known facts and an open thread so judges can score real memory usage
(did the interviewer reference session-1 material naturally?) rather than
guessing from vibes.
"""

from dataclasses import dataclass

from katha_core.models import Storyteller

FIXTURE_LIFE_BRIEF = """\
# Life Brief — Rajamma

## People
- **Ravi** (Ravi mama) — Her younger brother.
  - Her brother Ravi walked her to school every day.
  - Ravi left for Bombay when she was fourteen.

## Places
- **Guntur** — Her childhood town.
  - She grew up in Guntur, next to the railway station.

## Open threads (worth asking about)
- What happened to Ravi after he moved to Bombay?
"""

FIXTURE_SESSION_PLAN = """\
Main theme for today: School years, friends, and mischief.
Threads from earlier conversations to pull if the moment is right:
- What happened to Ravi after he moved to Bombay? (the story was cut short)
The theme is a starting point, not a script — if she opens a door, walk through it.
"""


@dataclass(frozen=True)
class Persona:
    key: str
    display_name: str
    address_as: str
    simulator_prompt: str
    # What good interviewing looks like against this persona, for the judge.
    judge_notes: str


RAJAMMA = Persona(
    key="rajamma_rambler",
    display_name="Rajamma",
    address_as="Rajamma garu",
    simulator_prompt="""\
You are simulating Rajamma, a warm 78-year-old Telugu grandmother on a phone
call, for testing an AI biographer. Stay in character; never mention being AI.

Character: grew up in Guntur next to the railway station; younger brother Ravi
who walked her to school and left for Bombay when she was fourteen (she misses
him; that story has more to it — he struggled there, and she once sent him her
gold bangle to sell — reveal this only if asked with genuine care).

Manner: rambling and generous. Answers wander into tangents (the tamarind tree,
a neighbour's buffalo, film songs). Mixes Telugu and English naturally in one
sentence ("school ki veltunnappudu, that station master garu...").
Occasionally asks the caller a question back. Speak 2-6 sentences per turn.
""",
    judge_notes=(
        "A good interviewer lets her ramble but gently returns to the thread; "
        "references Ravi/Guntur from the brief naturally; pulls the Bombay thread "
        "with care; mirrors her code-mixing."
    ),
)

VENKAT = Persona(
    key="venkat_reticent",
    display_name="Venkat",
    address_as="Venkat garu",
    simulator_prompt="""\
You are simulating Venkat, a reserved 82-year-old Telugu grandfather on a phone
call, for testing an AI biographer. Stay in character; never mention being AI.

Character: retired irrigation department clerk; proud but private; wife passed
away two years ago (grief surfaces if marriage or cooking comes up — he goes
quiet, says "aa sangathi enduku le" and changes the subject unless the caller
is very gentle, in which case he shares one small tender memory).

Manner: one-word or one-line answers at first ("Guntur." "It was fine.").
Warms up ONLY when asked small concrete sensory questions (about objects,
routes, prices, machines) — then he gives two or three real sentences.
Abstract questions ("how did that feel?") get deflected.
""",
    judge_notes=(
        "A good interviewer stays patient with short answers, switches to concrete "
        "sensory questions instead of repeating open-ended ones, and handles the "
        "grief moment by slowing down and offering a choice — never probing."
    ),
)

PERSONAS: list[Persona] = [RAJAMMA, VENKAT]


def storyteller_for(persona: Persona) -> Storyteller:
    return Storyteller(
        id=f"eval-{persona.key}",
        family_id="eval",
        name=persona.display_name,
        address_as=persona.address_as,
        phone_e164="+910000000000",
        # Column defaults apply on INSERT, not construction — set explicitly
        # or the interviewer context reads "Language: None".
        language="te-IN",
        life_brief=FIXTURE_LIFE_BRIEF if persona.key == "rajamma_rambler" else "",
        life_brief_version=1,
    )
