"""LLM backend seam.

Two backends:
- "api"        — the Anthropic SDK (prompt caching, streaming, structured
                 outputs). Needs API credits. Required for live voice turns.
- "claude-cli" — Claude Code in headless mode (`claude -p`), billed to the
                 developer's Claude subscription. Free for development; slower
                 per call, so it powers the pipeline/evals, never live calls.

Selected via KATHA_LLM_BACKEND ("api" default; "claude-cli" for the free dev
path). Structured output on the CLI backend is schema-instructed JSON,
validated with the same Pydantic models and retried once on mismatch.
"""

import json
import subprocess

from pydantic import BaseModel, ValidationError

from .config import settings
from .log import get_logger

log = get_logger("llm")

CLI_TIMEOUT_S = 300


def backend() -> str:
    return settings().llm_backend or "api"


def _run_cli(system: str, prompt: str) -> str:
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--model", settings().cli_model,
    ]
    if system:
        cmd += ["--append-system-prompt", system]
    proc = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, timeout=CLI_TIMEOUT_S
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed: {proc.stderr[:300]}")
    envelope = json.loads(proc.stdout)
    result = envelope.get("result")
    if not isinstance(result, str) or not result.strip():
        raise RuntimeError("claude -p returned no result text")
    return result.strip()


def cli_text(system: str, prompt: str) -> str:
    """One completion, plain text."""
    return _run_cli(system, prompt)


def _extract_json(text: str) -> str:
    """Models sometimes wrap JSON in a code fence; unwrap defensively."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("```", 2)[1]
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped
    start, end = stripped.find("{"), stripped.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in reply")
    return stripped[start : end + 1]


def cli_structured[T: BaseModel](system: str, prompt: str, schema: type[T]) -> T:
    """One completion validated against a Pydantic model; one retry with the
    validation error fed back."""
    instruction = (
        f"{prompt}\n\n"
        "Respond with ONLY a JSON object (no prose, no code fence) matching "
        f"this JSON schema:\n{json.dumps(schema.model_json_schema())}"
    )
    last_error = ""
    for attempt in range(2):
        ask = instruction if not last_error else (
            f"{instruction}\n\nYour previous reply was invalid: {last_error}\n"
            "Reply again with ONLY valid JSON."
        )
        reply = _run_cli(system, ask)
        try:
            return schema.model_validate_json(_extract_json(reply))
        except (ValidationError, ValueError) as e:
            last_error = str(e)[:400]
            log.warning("cli_structured attempt=%d invalid: %s", attempt, last_error)
    raise RuntimeError(f"claude-cli structured output failed: {last_error}")
