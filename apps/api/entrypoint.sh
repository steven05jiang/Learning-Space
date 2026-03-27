#!/bin/bash
set -e

if [ "$SERVICE_TYPE" = "worker" ]; then
    # Check if running as root and switch to app user if needed
    if [ "$(id -u)" = "0" ]; then
        exec su app -c "python -m workers.run_worker"
    else
        exec python -m workers.run_worker
    fi
else
    # API service: run migrations then start server
    alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000
fi