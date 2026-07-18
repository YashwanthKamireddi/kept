from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .models import Base

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings().database_url)
    return _engine


def session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(engine(), expire_on_commit=False)
    return _session_factory


@asynccontextmanager
async def session() -> AsyncIterator[AsyncSession]:
    async with session_factory()() as s:
        yield s


async def create_all() -> None:
    # Dev convenience. Prod schema changes go through Alembic migrations.
    async with engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def reset() -> None:
    """Drop cached engine/session factory (tests re-point DATABASE_URL)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
