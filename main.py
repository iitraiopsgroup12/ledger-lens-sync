"""Service entry point: builds the FastAPI app and runs it with uvicorn."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.database import init_db
from app.router import all_routers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


app = FastAPI(title="Ledger Lens Sync", lifespan=lifespan)

for router in all_routers:
    app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness/readiness probe target; no DB dependency."""
    return {"status": "ok"}


def main() -> None:
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload)


if __name__ == "__main__":
    main()