"""Demo: the live interviewer brain, on the free claude-cli backend.

Runs the EXACT turn function the live voice agent uses (`complete_turn_cli`,
called from KathaAgent.llm_node) through a short scripted conversation, and
prints the transcript. No mic, no phone, no API credits — this proves the
biographer's intelligence works at $0. In a real call the same turns would be
spoken by Sarvam TTS and the elder's replies would come from Sarvam STT.

Run: uv run --package katha-voice python scripts/demo_interviewer.py
"""

from katha_core.models import Storyteller
from katha_voice.interviewer import complete_turn_cli

# A storyteller who exists only for this demo (English, so the transcript is
# readable here). Real storytellers come from the DB in any language.
rose = Storyteller(
    name="Rose",
    address_as="Rose",
    language="en",
    life_brief_version=0,
    life_brief="",  # first session — the interviewer has nothing yet
)

PLAN = (
    "First conversation. Open with the greeting ritual and ask consent warmly. "
    "Then begin gently with her childhood home."
)

# Scripted elder replies stand in for what Sarvam STT would transcribe from a
# real phone call, so we can exercise a genuine back-and-forth.
ELDER_TURNS = [
    "Oh — hello? Yes, yes, I can hear you, dear.",
    "Yes, that's alright. You may record. What would you like to know?",
    "We grew up in a little house behind my father's bakery. The whole street "
    "smelled of bread before the sun came up.",
    "My mother. She woke before all of us and sang so softly, so as not to wake "
    "the little ones. I used to lie awake just to hear her.",
]


def main() -> None:
    dialogue: list[dict] = []
    print("=" * 70)
    print("KEPT — live interviewer brain (backend: claude-cli, $0)")
    print("=" * 70)

    # Opening: the call has just connected, she has said hello.
    dialogue.append({"role": "user", "content": "(the call connects; she greets you)"})
    for i, elder in enumerate(ELDER_TURNS):
        turn = complete_turn_cli(rose, PLAN, dialogue)
        print(f"\n  BIOGRAPHER: {turn}")
        dialogue.append({"role": "assistant", "content": turn})
        print(f"\n  ROSE:       {elder}")
        dialogue.append({"role": "user", "content": elder})

    # One last biographer turn to see how it responds to the tender memory.
    turn = complete_turn_cli(rose, PLAN, dialogue)
    print(f"\n  BIOGRAPHER: {turn}")
    print("\n" + "=" * 70)
    print(f"{len([m for m in dialogue if m['role'] == 'assistant']) + 1} biographer turns, all on the free backend.")


if __name__ == "__main__":
    main()
