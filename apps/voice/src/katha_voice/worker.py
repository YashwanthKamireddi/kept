"""LiveKit Agents worker entrypoint (skeleton).

Wiring plan (Day 1-4 gate: Telugu echo over a real SIP call):
  SIP trunk -> LiveKit room -> this worker
  audio -> Sarvam STT -> interviewer.stream_turn (Claude) -> Sarvam TTS -> room

This file intentionally fails fast when credentials are missing instead of
pretending: the first milestone is a REAL call, not a demo.
"""

import sys

from katha_core.config import settings


def preflight() -> list[str]:
    s = settings()
    missing = [
        name
        for name, value in {
            "LIVEKIT_URL": s.livekit_url,
            "LIVEKIT_API_KEY": s.livekit_api_key,
            "LIVEKIT_API_SECRET": s.livekit_api_secret,
            "ANTHROPIC_API_KEY": s.anthropic_api_key,
            "SARVAM_API_KEY": s.sarvam_api_key,
        }.items()
        if not value
    ]
    return missing


def main() -> None:
    missing = preflight()
    if missing:
        print(f"katha-voice: missing credentials: {', '.join(missing)}", file=sys.stderr)
        print("Fill .env (see .env.example) before starting the voice worker.", file=sys.stderr)
        raise SystemExit(2)
    # LiveKit AgentSession wiring lands here once credentials exist and the
    # Sarvam plugin availability is verified against the installed version.
    raise SystemExit("katha-voice: wiring not implemented yet (next milestone)")


if __name__ == "__main__":
    main()
