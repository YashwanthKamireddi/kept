"""LiveKit Agents worker: the live interviewer.

Pipeline per call:
  SIP -> LiveKit room -> AgentSession(Sarvam STT -> KathaAgent -> Sarvam TTS)
with Silero VAD + semantic turn detection (barge-in handled by AgentSession).

KathaAgent overrides `llm_node` — the documented extension point — so the
brain is our own `stream_turn` (Opus 4.8 with cached Life Brief prefix),
not a generic LLM adapter. Transcripts checkpoint to the DB as turns finalize
(user turns via the session's conversation events, biographer turns as they
are spoken), so a dropped line never loses a word.

THE WIRING POINT (single place that needs real credentials to go live):
  1. Fill .env — LIVEKIT_URL/KEY/SECRET, SARVAM_API_KEY, ANTHROPIC_API_KEY.
  2. Point a SIP trunk at LiveKit (dispatch rule -> agent name "katha").
  3. Run: uv run --package katha-voice python -m katha_voice.worker dev
The job's room metadata must carry {"session_id": "..."} (set by the caller
that creates the outbound SIP participant).
"""

import asyncio
import json
import sys
import time

from anthropic import AsyncAnthropic
from katha_core import llm
from katha_core.config import settings
from katha_core.db import create_all
from katha_core.models import Speaker, Storyteller
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions
from livekit.agents import llm as lk_llm
from livekit.plugins import sarvam, silero

from .calls import (
    CallStateError,
    TranscriptRecorder,
    begin_call,
    build_dialogue_context,
    complete_call,
    drop_call,
    storyteller_for_session,
)
from .interviewer import complete_turn_cli, stream_turn

AGENT_NAME = "katha"


class _BrainPlaceholder(lk_llm.LLM):
    """A non-None LLM so AgentSession routes generation into our llm_node.

    This livekit-agents version skips ALL replies when session.llm is None
    (agent_activity: `elif self.llm is None: return`) and only reaches the
    agent's llm_node when an LLM is set. Generation actually runs through
    KathaAgent.llm_node (see generation.py `node(chat_ctx, ...)`), so this
    object's chat() is never called — it exists purely to pass that guard and
    to let session.generate_reply() work for the opening greeting."""

    def chat(self, *, chat_ctx, tools=None, **kwargs):  # noqa: ANN001, ANN201
        raise RuntimeError("KathaAgent.llm_node handles generation; chat() is unused")


def preflight() -> list[str]:
    # ANTHROPIC_API_KEY is intentionally not required here: with it unset, the
    # SDK falls through to the ambient credential chain (`ant auth login`).
    s = settings()
    return [
        name
        for name, value in {
            "LIVEKIT_URL": s.livekit_url,
            "LIVEKIT_API_KEY": s.livekit_api_key,
            "LIVEKIT_API_SECRET": s.livekit_api_secret,
            "SARVAM_API_KEY": s.sarvam_api_key,
        }.items()
        if not value
    ]


class KathaAgent(Agent):
    def __init__(self, *, storyteller, session_plan: str, seed_dialogue: list[dict]):
        # Craft prompt + Life Brief live in our own system blocks (interviewer.py);
        # instructions here are minimal because llm_node bypasses them.
        super().__init__(instructions="You are Kept, a warm voice biographer.")
        self._storyteller = storyteller
        self._session_plan = session_plan
        self._seed = seed_dialogue
        # Two brains behind one seam. "api" streams token-by-token (natural
        # latency). "claude-cli" runs on the developer's subscription for $0:
        # each turn is a blocking one-shot, so it's slower and non-streamed —
        # usable for a demo, not a production call. No API client is created
        # (and no credits needed) on the CLI path.
        self._use_cli = llm.backend() == "claude-cli"
        self._client = None if self._use_cli else AsyncAnthropic(
            api_key=settings().anthropic_api_key or None
        )

    def _dialogue(self, chat_ctx) -> list[dict]:
        dialogue = list(self._seed)
        for item in chat_ctx.items:
            if getattr(item, "type", "message") != "message":
                continue
            text = (item.text_content or "").strip()
            if not text or item.role == "system":
                continue
            role = "assistant" if item.role == "assistant" else "user"
            dialogue.append({"role": role, "content": text})
        if not dialogue or dialogue[-1]["role"] != "user":
            dialogue.append({"role": "user", "content": "(silence — she is waiting)"})
        return dialogue

    async def llm_node(self, chat_ctx, tools, model_settings):
        dialogue = self._dialogue(chat_ctx)
        if self._use_cli:
            # Blocking subprocess (claude -p): run off the event loop so the
            # audio pipeline keeps breathing, then speak the whole turn at once.
            text = await asyncio.to_thread(
                complete_turn_cli, self._storyteller, self._session_plan, dialogue
            )
            yield text
            return
        async for delta in stream_turn(
            self._client, self._storyteller, self._session_plan, dialogue
        ):
            yield delta


def _plan_text(planned_themes: list) -> str:
    return "\n".join(str(t) for t in planned_themes) or "First conversation — introduce, ask consent, start with childhood."


async def _run_test_agent(ctx: JobContext) -> None:
    """Playground/echo mode: talk to Kept over the browser with no phone, no
    call record, no DB. Same STT/brain/TTS as a real call, English so it's
    easy to try. Runs on whatever LLM_BACKEND is set (claude-cli = free)."""
    storyteller = Storyteller(
        name="a storyteller",
        address_as="friend",
        language="en-IN",  # Sarvam Indian-English STT + TTS
        life_brief_version=0,
        life_brief="",
    )
    session = AgentSession(
        llm=_BrainPlaceholder(),
        stt=sarvam.STT(language=storyteller.language, api_key=settings().sarvam_api_key),
        tts=sarvam.TTS(
            target_language_code=storyteller.language,
            model="bulbul:v3",
            api_key=settings().sarvam_api_key,
        ),
        vad=silero.VAD.load(),
    )
    agent = KathaAgent(
        storyteller=storyteller,
        session_plan=_plan_text([]),
        seed_dialogue=[],
    )
    await ctx.connect()
    await session.start(agent, room=ctx.room)
    await ctx.wait_for_participant()
    # Kept opens the conversation so you hear it the moment you join.
    session.generate_reply()


async def entrypoint(ctx: JobContext) -> None:
    await create_all()
    meta = json.loads(ctx.room.metadata or "{}")
    session_id = meta.get("session_id")
    if not session_id:
        # No call to attach to (e.g. the LiveKit playground) — run a throwaway
        # interviewer so you can hear STT -> brain -> TTS with your own mic.
        # No DB writes, no call record, no telephony.
        await _run_test_agent(ctx)
        return

    call = await begin_call(session_id)
    storyteller = await storyteller_for_session(session_id)
    seed = await build_dialogue_context(session_id)
    recorder = TranscriptRecorder(session_id, storyteller.language)
    t0 = time.monotonic()

    def now_ms() -> int:
        return int((time.monotonic() - t0) * 1000)

    session = AgentSession(
        llm=_BrainPlaceholder(),
        stt=sarvam.STT(
            language=storyteller.language,
            api_key=settings().sarvam_api_key,
        ),
        tts=sarvam.TTS(
            target_language_code=storyteller.language,
            model="bulbul:v3",
            speaker=storyteller.tts_voice or None,
            api_key=settings().sarvam_api_key,
        ),
        vad=silero.VAD.load(),
    )

    @session.on("conversation_item_added")
    def _on_item(ev) -> None:
        item = ev.item
        text = (getattr(item, "text_content", None) or "").strip()
        if not text:
            return
        speaker = Speaker.BIOGRAPHER if item.role == "assistant" else Speaker.STORYTELLER
        # Fired synchronously; persist without blocking the audio loop.
        import asyncio  # noqa: PLC0415

        asyncio.create_task(recorder.record(speaker, text, now_ms(), now_ms()))

    agent = KathaAgent(
        storyteller=storyteller,
        session_plan=_plan_text(call.planned_themes),
        seed_dialogue=seed,
    )

    async def on_shutdown() -> None:
        # Clean hangup -> COMPLETED. If the error path already marked the call
        # DROPPED, complete_call refuses (CallStateError) and we leave it be —
        # the scheduler resumes dropped calls.
        try:
            await complete_call(session_id)
        except CallStateError:
            pass

    ctx.add_shutdown_callback(on_shutdown)

    try:
        await ctx.connect()
        await session.start(agent, room=ctx.room)
        await ctx.wait_for_participant()
    except Exception:
        await drop_call(session_id)
        raise


def main() -> None:
    missing = preflight()
    if missing:
        print(f"katha-voice: missing credentials: {', '.join(missing)}", file=sys.stderr)
        print("Fill .env (see .env.example) before starting the voice worker.", file=sys.stderr)
        raise SystemExit(2)
    # Thread LiveKit creds from our .env-backed settings straight into the
    # worker. The agents framework otherwise only reads them from os.environ,
    # which pydantic-settings doesn't populate — so without this the worker
    # fails with "ws_url is required" even though preflight sees the keys.
    s = settings()
    agents.cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name=AGENT_NAME,
            ws_url=s.livekit_url,
            api_key=s.livekit_api_key,
            api_secret=s.livekit_api_secret,
        )
    )


if __name__ == "__main__":
    main()
