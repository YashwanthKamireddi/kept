# Katha (working codename)

A biographer for every family, in the family's own language.

A warm voice-AI biographer calls an elder on an ordinary phone, interviews them
in their native language (Telugu first), remembers every session, and turns a
life of memories into a living, audio-anchored family memoir.

## Layout

- `packages/core` — domain schema, config, DB. The memory graph lives here.
- `apps/server` — FastAPI API + post-call pipeline workers.
- `apps/voice` — LiveKit Agents worker: the live interviewer (SIP → STT → Claude → TTS).
- `apps/mobile` — Expo app for the family (Keeper surface).
- `evals` — synthetic-elder personas + interviewer quality evals.

## Dev

```sh
uv sync
uv run --package katha-server uvicorn katha_server.main:app --reload
```
