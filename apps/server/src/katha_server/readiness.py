"""Capability readiness — what is wired, and what each unwired piece blocks.

Pure function of configuration (no network calls), so it's safe to expose and
cheap to poll. It's the honest single source of "how far can this deployment
actually go right now" — used by the readiness endpoint and useful for a
launch dashboard.
"""

from katha_core.config import settings


def capabilities() -> dict:
    s = settings()

    brain_cli = (s.llm_backend or "api") == "claude-cli"
    brain_api = bool(s.anthropic_api_key)
    brain_ready = brain_cli or brain_api

    voice = {"sarvam": bool(s.sarvam_api_key)}
    livekit = bool(s.livekit_url and s.livekit_api_key and s.livekit_api_secret)
    sip = bool(s.sip_trunk_id)
    storage = bool(s.r2_endpoint and s.r2_access_key_id and s.r2_secret_access_key)

    caps = {
        "brain": {
            "ready": brain_ready,
            "backend": s.llm_backend or "api",
            "note": (
                "claude-cli (subscription; dev/pipeline only)"
                if brain_cli
                else "anthropic api key present" if brain_api
                else "no Anthropic credentials — set ANTHROPIC_API_KEY or LLM_BACKEND=claude-cli"
            ),
        },
        "voice_stt_tts": {
            "ready": voice["sarvam"],
            "note": "sarvam configured" if voice["sarvam"] else "SARVAM_API_KEY missing",
        },
        "telephony": {
            "ready": livekit and sip,
            "note": _telephony_note(livekit, sip),
        },
        "audio_storage": {
            "ready": storage,
            "note": "r2 configured" if storage else "R2_* missing — audio playback disabled",
        },
    }

    # What the whole product can actually do, given the above.
    can_run_pipeline = brain_ready
    can_place_live_call = brain_api and voice["sarvam"] and livekit and sip
    caps["_summary"] = {
        "pipeline": can_run_pipeline,  # extraction, chapters, evals
        "live_call": can_place_live_call,  # the real phone conversation
    }
    return caps


def _telephony_note(livekit: bool, sip: bool) -> str:
    missing = []
    if not livekit:
        missing.append("LIVEKIT_*")
    if not sip:
        missing.append("SIP_TRUNK_ID")
    return "livekit + sip configured" if not missing else f"missing: {', '.join(missing)}"
