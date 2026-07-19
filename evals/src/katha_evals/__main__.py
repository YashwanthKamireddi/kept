"""Run the interviewer eval suite: `uv run python -m katha_evals`.

Simulates one interview per persona, judges it, prints scorecards, writes a
JSON report, and exits nonzero on failure — usable as a CI/pre-deploy gate
for any change to the interviewer prompt.
"""

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from katha_core.config import settings

from .judges import judge_dialogue
from .personas import PERSONAS
from .scorecard import Scorecard
from .simulator import render_dialogue, simulate

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def _credentials_ok() -> bool:
    """Probe the credential chain: explicit key, env, or `ant auth login`."""
    import anthropic  # noqa: PLC0415

    try:
        client = anthropic.Anthropic(api_key=settings().anthropic_api_key or None)
        client.models.list()
        return True
    except Exception:
        return False


async def run() -> int:
    if not _credentials_ok():
        print(
            "katha-evals: no working Anthropic credentials.\n"
            "Either set ANTHROPIC_API_KEY in .env, or run `ant auth login` "
            "(the SDK picks up the profile automatically).",
            file=sys.stderr,
        )
        return 2

    cards: list[Scorecard] = []
    report: dict = {"ran_at": datetime.now(UTC).isoformat(), "personas": {}}

    for persona in PERSONAS:
        print(f"simulating: {persona.key} ...", flush=True)
        dialogue = await simulate(persona)
        rendered = render_dialogue(dialogue)
        card = await asyncio.to_thread(judge_dialogue, persona, rendered)
        cards.append(card)
        report["personas"][persona.key] = {
            "dialogue": rendered,
            "scores": {k: vars(v) for k, v in card.scores.items()},
            "passed": card.passed,
        }
        print(card.render())
        print()

    REPORTS_DIR.mkdir(exist_ok=True)
    out = REPORTS_DIR / f"eval-{datetime.now(UTC):%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"report: {out}")

    return 0 if all(c.passed for c in cards) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
