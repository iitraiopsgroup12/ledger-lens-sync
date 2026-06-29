"""Service entry point: builds the FastAPI app and runs it with uvicorn."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.router import all_routers

# Log level, e.g. DEBUG, INFO, WARNING. Configurable via the LOG_LEVEL env var.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Comma-separated list of allowed CORS origins, e.g.
# "https://app.example.com,https://admin.example.com". Defaults to "*" (any
# origin). Note: a wildcard "*" cannot be combined with credentialed requests.
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]


def configure_logging() -> None:
    """Install a root handler so application logs are emitted.

    Runs at import time so logs work both when launched via ``python main.py``
    and when uvicorn imports ``main:app`` directly (as the container does).
    Without this, loggers like ``logging.getLogger(__name__)`` in the app have
    no handler and stay silent.
    """
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )


configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting Ledger Lens Sync service")
    await init_db()
    logger.info("Database initialized; service ready")
    yield
    logger.info("Shutting down Ledger Lens Sync service")


app = FastAPI(title="Ledger Lens Sync", lifespan=lifespan)

# Allowed origins come from the CORS_ALLOW_ORIGINS env var (defaults to "*").
# Credentialed requests are only enabled when origins are explicitly listed,
# since the CORS spec forbids combining a wildcard "*" with allow_credentials.
_allow_credentials = "*" not in CORS_ALLOW_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in all_routers:
    app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness/readiness probe target; no DB dependency."""
    return {"status": "ok"}


def main() -> None:
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
        log_level=LOG_LEVEL.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()