from contextlib import asynccontextmanager

from fastapi import FastAPI
from katha_core.config import settings
from katha_core.db import create_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings().katha_env == "dev":
        await create_all()
    yield


app = FastAPI(title="Katha", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "env": settings().katha_env}
