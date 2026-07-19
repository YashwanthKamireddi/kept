from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from katha_core.config import settings
from katha_core.db import create_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings().katha_env == "dev":
        await create_all()
    yield


app = FastAPI(title="Kept", lifespan=lifespan)

# Dev: the Expo web preview (localhost:8081) is cross-origin to this API.
# Tighten to the real app origins before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from .api.routes import router  # noqa: E402

app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "env": settings().katha_env}
