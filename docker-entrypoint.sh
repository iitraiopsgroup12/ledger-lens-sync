#!/bin/sh
set -e

# uvicorn wants a lowercase log level; LOG_LEVEL defaults to info when unset.
log_level="$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')"

# exec replaces this shell so uvicorn becomes PID 1 and receives signals
# (e.g. SIGTERM on pod shutdown) directly, allowing a graceful shutdown.
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level "$log_level"