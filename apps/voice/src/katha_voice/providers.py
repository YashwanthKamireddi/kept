"""STT/TTS provider routing.

The product is language-universal; providers are per-language market choices.
Routing policy (config, not identity):
- Indic languages (launch wedge): Sarvam — saarika STT with code-mixing,
  bulbul TTS — via the official LiveKit plugins (wired in worker.py).
- Other languages: pluggable per deployment (e.g. ElevenLabs/Deepgram LiveKit
  plugins) behind the same seam; add routes as markets open.

Nothing here fakes audio: until keys are configured and the wiring is verified
against a real call, the worker refuses to start rather than simulating.
"""

from typing import Protocol


class StreamingSTT(Protocol):
    async def start(self, language: str) -> None: ...
    async def push_audio(self, pcm16: bytes) -> None: ...
    async def partials(self):  # yields (text, is_final, t_start_ms, t_end_ms)
        ...


class StreamingTTS(Protocol):
    async def synthesize(self, text_stream, voice: str, language: str):
        """Consume a text-delta stream, yield PCM16 audio frames."""
        ...
