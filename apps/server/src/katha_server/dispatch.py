"""Call dispatch: control-plane side of placing a call.

The scheduler decides WHO to call and WHEN; a Dispatcher makes it happen —
creating a LiveKit room carrying {"session_id"} metadata (which the voice
worker reads) and dialing the storyteller out via the SIP trunk. Tests inject
a fake; production uses LiveKitDispatcher, which fails fast without keys.
"""

from typing import Protocol

from katha_core.config import settings
from katha_core.models import CallSession, Storyteller


class Dispatcher(Protocol):
    async def dispatch(self, call: CallSession, storyteller: Storyteller) -> None: ...


class DispatchError(RuntimeError):
    pass


class LiveKitDispatcher:
    """Creates the room and SIP participant for one call."""

    def __init__(self) -> None:
        s = settings()
        missing = [
            k
            for k, v in {
                "LIVEKIT_URL": s.livekit_url,
                "LIVEKIT_API_KEY": s.livekit_api_key,
                "LIVEKIT_API_SECRET": s.livekit_api_secret,
                "SIP_TRUNK_ID": s.sip_trunk_id,
            }.items()
            if not v
        ]
        if missing:
            raise DispatchError(f"LiveKit dispatch unconfigured: {', '.join(missing)}")

    async def dispatch(self, call: CallSession, storyteller: Storyteller) -> None:
        import json  # noqa: PLC0415

        from livekit import api  # noqa: PLC0415  (ships with livekit-api)

        s = settings()
        lk = api.LiveKitAPI(url=s.livekit_url, api_key=s.livekit_api_key,
                            api_secret=s.livekit_api_secret)
        try:
            room_name = f"call-{call.id}"
            await lk.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    metadata=json.dumps({"session_id": call.id}),
                )
            )
            await lk.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=s.sip_trunk_id,
                    sip_call_to=storyteller.phone_e164,
                    room_name=room_name,
                    participant_identity=f"storyteller-{storyteller.id}",
                )
            )
        finally:
            await lk.aclose()
