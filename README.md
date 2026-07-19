# Kept (name pending final trademark/domain check)

A biographer for every family, in the family's own language.

Kept is a warm voice-AI biographer that calls an elder on an ordinary phone, interviews them
in their own language — any language, remembers every session, and turns a
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
