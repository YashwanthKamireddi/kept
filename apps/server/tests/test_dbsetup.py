import asyncio

import pytest
from katha_core import db
from katha_core.config import settings
from katha_server.dbsetup import ensure_schema
from sqlalchemy import inspect, text


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/setup.db")
    settings.cache_clear()
    db.reset()
    yield
    settings.cache_clear()
    db.reset()


def _tables() -> list[str]:
    async def run():
        async with db.engine().connect() as conn:
            return await conn.run_sync(lambda c: inspect(c).get_table_names())

    return asyncio.run(run())


def test_fresh_database_is_built_by_migrations(fresh_db):
    asyncio.run(ensure_schema())
    tables = _tables()
    assert "alembic_version" in tables  # migration-chained, not create_all
    assert "storytellers" in tables and "follow_ups" in tables

    async def col_check():
        async with db.engine().connect() as conn:
            rows = await conn.execute(text("PRAGMA table_info(follow_ups)"))
            return [r[1] for r in rows]

    assert "asked_by_keeper_id" in asyncio.run(col_check())


def test_legacy_create_all_database_is_adopted(fresh_db):
    # Simulate the old world: tables exist, no alembic_version.
    asyncio.run(db.create_all())
    assert "alembic_version" not in _tables()

    asyncio.run(ensure_schema())
    tables = _tables()
    assert "alembic_version" in tables  # stamped + upgraded

    # Idempotent on a second boot.
    asyncio.run(ensure_schema())
