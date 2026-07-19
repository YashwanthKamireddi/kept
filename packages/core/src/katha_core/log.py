"""Structured logging for Katha services.

One line per event, key=value pairs, stdout — friendly to any log collector.
Level via KATHA_LOG_LEVEL (default INFO).
"""

import logging
import os
import sys

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger("katha")
    root.addHandler(handler)
    root.setLevel(os.environ.get("KATHA_LOG_LEVEL", "INFO").upper())
    root.propagate = False
    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(f"katha.{name}")
