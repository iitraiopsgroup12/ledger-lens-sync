# syntax=docker/dockerfile:1

FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY app/ app/
COPY nse_data_storage/ nse_data_storage/
COPY nse_web_source/ nse_web_source/
COPY main.py ./
RUN uv sync --locked --no-dev


FROM python:3.14-slim AS runtime

RUN groupadd --system --gid 1000 app && useradd --system --uid 1000 --gid app --no-create-home app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/nse_data_storage /app/nse_data_storage
COPY --from=builder /app/nse_web_source /app/nse_web_source
COPY --from=builder /app/main.py /app/main.py
COPY --chmod=755 docker-entrypoint.sh /app/docker-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN mkdir -p /home/data /home/storage \
    && chown -R app:app /home/data /home/storage \
    && chmod -R 777 /home/data /home/storage

USER app

EXPOSE 8000

# Entrypoint script uses `exec` so uvicorn becomes PID 1 and receives signals
# (SIGTERM on pod shutdown) directly for a graceful shutdown.
ENTRYPOINT ["/app/docker-entrypoint.sh"]