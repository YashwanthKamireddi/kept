"""STT/TTS provider seam.

Target providers (per architecture): Sarvam Saaras (STT, 22 Indic languages,
code-mixing) and Sarvam Bulbul v3 (TTS, Telugu voices, streaming).

Integration order of preference:
1. LiveKit Agents plugin for Sarvam, if the installed livekit-agents version
   ships one (verify at wiring time — do not assume).
2. Direct Sarvam WebSocket streaming APIs behind these interfaces.

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
