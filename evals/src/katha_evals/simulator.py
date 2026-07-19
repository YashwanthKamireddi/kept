"""Run a simulated interview: the real interviewer vs a synthetic elder."""

import asyncio

from anthropic import AsyncAnthropic
from katha_core import llm
from katha_core.config import settings
from katha_voice.interviewer import complete_turn_cli, stream_turn

from .personas import FIXTURE_SESSION_PLAN, Persona, storyteller_for


async def _persona_reply(
    client: AsyncAnthropic | None, persona: Persona, dialogue: list[dict]
) -> str:
    """The synthetic elder answers. Dialogue is from the interviewer's POV;
    flip roles so the persona model speaks as the storyteller."""
    if llm.backend() == "claude-cli":
        lines = [
            f"{'CALLER' if m['role'] == 'assistant' else 'YOU'}: {m['content']}"
            for m in dialogue
        ]
        prompt = (
            "The call so far:\n" + "\n".join(lines) +
            "\n\nReply with ONLY your next spoken turn, in character."
        )
        return await asyncio.to_thread(llm.cli_text, persona.simulator_prompt, prompt)

    assert client is not None
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


async def _interviewer_turn(
    client: AsyncAnthropic | None, storyteller, plan: str, dialogue: list[dict]
) -> str:
    if llm.backend() == "claude-cli":
        return await asyncio.to_thread(complete_turn_cli, storyteller, plan, dialogue)
    assert client is not None
    return "".join(
        [t async for t in stream_turn(client, storyteller, plan, dialogue)]
    ).strip()


async def simulate(persona: Persona, turns: int = 8) -> list[dict]:
    """Returns the dialogue from the interviewer's POV:
    assistant = biographer, user = storyteller."""
    client = (
        None
        if llm.backend() == "claude-cli"
        else AsyncAnthropic(api_key=settings().anthropic_api_key or None)
    )
    storyteller = storyteller_for(persona)
    plan = FIXTURE_SESSION_PLAN

    dialogue: list[dict] = [
        {"role": "user", "content": "(the phone connects; she has picked up)"}
    ]
    for _ in range(turns):
        spoken = await _interviewer_turn(client, storyteller, plan, dialogue)
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
