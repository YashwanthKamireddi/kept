from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from katha_core.db import session_factory
from katha_core.models import ApiToken, Keeper
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncIterator[AsyncSession]:
    async with session_factory()() as s:
        yield s


Db = Annotated[AsyncSession, Depends(get_db)]


async def current_keeper(db: Db, authorization: str = Header(default="")) -> Keeper:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    row = await db.get(ApiToken, token)
    if row is None:
        raise HTTPException(status_code=401, detail="invalid token")
    keeper = await db.get(Keeper, row.keeper_id)
    if keeper is None:
        raise HTTPException(status_code=401, detail="keeper not found")
    return keeper


CurrentKeeper = Annotated[Keeper, Depends(current_keeper)]
