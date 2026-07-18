"""Run a simulated interview: the real interviewer vs a synthetic elder."""

from anthropic import AsyncAnthropic
from katha_core.config import settings
from katha_voice.interviewer import stream_turn

from .personas import FIXTURE_SESSION_PLAN, Persona, storyteller_for


async def _persona_reply(client: AsyncAnthropic, persona: Persona, dialogue: list[dict]) -> str:
    """The synthetic elder answers. Dialogue is from the interviewer's POV;
    flip roles so the persona model speaks as the storyteller."""
    flipped = [
        {
            "role": "assistant" if m["role"] == "user" else "user",
            "content": m["content"],
        }
        for m in dialogue
    ]
    response = await client.messages.create(
        model=settings().utility_model,
        max_tokens=400,
        system=persona.simulator_prompt,
        messages=flipped,
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()


async def simulate(persona: Persona, turns: int = 8) -> list[dict]:
    """Returns the dialogue from the interviewer's POV:
    assistant = biographer, user = storyteller."""
    client = AsyncAnthropic(api_key=settings().anthropic_api_key)
    storyteller = storyteller_for(persona)
    plan = FIXTURE_SESSION_PLAN

    dialogue: list[dict] = [
        {"role": "user", "content": "(the phone connects; she has picked up)"}
    ]
    for _ in range(turns):
        spoken = "".join(
            [t async for t in stream_turn(client, storyteller, plan, dialogue)]
        ).strip()
        dialogue.append({"role": "assistant", "content": spoken})
        reply = await _persona_reply(client, persona, dialogue)
        dialogue.append({"role": "user", "content": reply})
    return dialogue


def render_dialogue(dialogue: list[dict]) -> str:
    lines = []
    for m in dialogue:
        who = "BIOGRAPHER" if m["role"] == "assistant" else "STORYTELLER"
        lines.append(f"{who}: {m['content']}")
    return "\n".join(lines)
