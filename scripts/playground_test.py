"""Hear Kept for free — dispatch the agent into a room and print a join link.

No phone, no Twilio, no API credits: you talk to Kept over the browser with
your own mic (Sarvam STT -> claude-cli brain -> Sarvam TTS).

How to use (two terminals):
  Terminal A — start the worker and leave it running:
    uv run --package katha-voice python -m katha_voice.worker dev
  Terminal B — run this, then follow the printed steps:
    uv run --package katha-voice python scripts/playground_test.py
"""

import asyncio

from katha_core.config import settings
from livekit import api

ROOM = "kept-test"


async def main() -> None:
    s = settings()
    if not (s.livekit_url and s.livekit_api_key and s.livekit_api_secret):
        raise SystemExit("LiveKit keys missing in .env (LIVEKIT_URL/KEY/SECRET).")

    lk = api.LiveKitAPI(
        url=s.livekit_url, api_key=s.livekit_api_key, api_secret=s.livekit_api_secret
    )
    try:
        try:
            await lk.room.create_room(api.CreateRoomRequest(name=ROOM, metadata="{}"))
        except Exception:
            pass  # already exists — fine
        # Dispatch our named agent into the room. No session_id in metadata ->
        # the worker runs its test path (see _run_test_agent).
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(agent_name="katha", room=ROOM, metadata="{}")
        )
    finally:
        await lk.aclose()

    token = (
        api.AccessToken(s.livekit_api_key, s.livekit_api_secret)
        .with_identity("keeper")
        .with_name("You")
        .with_grants(api.VideoGrants(room_join=True, room=ROOM))
        .to_jwt()
    )

    line = "=" * 68
    print(f"\n{line}\nTALK TO KEPT — free browser test\n{line}")
    print("The 'katha' agent has been dispatched into the room 'kept-test'.")
    print("(Make sure the worker is running in another terminal first.)\n")
    print("1. Open:  https://agents-playground.livekit.io")
    print("2. Top-right, switch to  Manual  (connect with a token).")
    print("3. Paste these, then Connect:")
    print(f"     Server URL:  {s.livekit_url}")
    print(f"     Token:       {token}")
    print("4. Allow your microphone and say hello. Kept will greet you.")
    print("   On the free (claude-cli) brain, expect a few seconds between turns.\n")


if __name__ == "__main__":
    asyncio.run(main())
