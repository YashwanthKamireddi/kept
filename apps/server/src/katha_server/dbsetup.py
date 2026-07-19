"""Schema bootstrap: the database always follows the migration chain.

Rules:
- A fresh database is built by running migrations to head (never create_all).
- A legacy dev database made by create_all (tables but no alembic_version)
  is stamped at the baseline revision, then upgraded — one-time adoption.
- Idempotent: running at every boot is safe.
"""

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from katha_core.db import engine
from katha_core.log import get_logger
from sqlalchemy import inspect

log = get_logger("dbsetup")

BASELINE_REVISION = "3b50a73dae88"
_SERVER_DIR = Path(__file__).resolve().parents[2]  # apps/server


def _alembic_config() -> Config:
    cfg = Config(str(_SERVER_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_SERVER_DIR / "migrations"))
    return cfg


async def ensure_schema() -> None:
    async with engine().connect() as conn:
        def introspect(c):
            insp = inspect(c)
            tables = insp.get_table_names()
            follow_up_cols = (
                {col["name"] for col in insp.get_columns("follow_ups")}
                if "follow_ups" in tables
                else set()
            )
            return tables, follow_up_cols

        tables, follow_up_cols = await conn.run_sync(introspect)

    cfg = _alembic_config()
    if "alembic_version" not in tables and "storytellers" in tables:
        # Legacy create_all database: adopt it into the migration chain at
        # the revision its schema actually matches (marker-column detection).
        target = "head" if "asked_by_keeper_id" in follow_up_cols else BASELINE_REVISION
        log.info("adopting legacy dev database: stamping %s", target)
        await asyncio.to_thread(command.stamp, cfg, target)

    await asyncio.to_thread(command.upgrade, cfg, "head")
    log.info("schema at migration head")
