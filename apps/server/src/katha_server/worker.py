"""The unattended background worker.

Runs the full automation loop: place due calls (via the LiveKit dispatcher)
and turn finished calls into verified chapters. This is the process that makes
Kept run without anyone touching it.

    uv run --package katha-server python -m katha_server.worker

Requires the pipeline brain (API key or LLM_BACKEND=claude-cli) and, to place
calls, the LiveKit + SIP dispatcher config. Post-call processing runs even
without telephony configured — useful for reprocessing after a manual import.
"""

import asyncio
import sys

from katha_core.log import get_logger

from .dbsetup import ensure_schema
from .dispatch import DispatchError, LiveKitDispatcher
from .scheduling import process_completed_calls, run_forever

log = get_logger("worker")


async def main() -> None:
    await ensure_schema()
    try:
        dispatcher = LiveKitDispatcher()
        log.info("worker starting: dialing + post-call processing")
        await run_forever(dispatcher)
    except DispatchError as e:
        # No telephony configured — still do the useful half (chapters) so a
        # dev without LiveKit can process imported transcripts on a loop.
        log.warning("telephony unconfigured (%s); running post-call processing only", e)
        while True:
            await process_completed_calls()
            await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("worker stopped", file=sys.stderr)
