#!/bin/bash
set -e

if [ "$SERVICE_TYPE" = "worker" ]; then
    # Worker service: start dispatch API server + ARQ worker (via uvicorn lifespan)
    WORKER_HOST="${WORKER_HOST:-0.0.0.0}"
    WORKER_PORT="${WORKER_PORT:-8001}"
    if [ "$(id -u)" = "0" ]; then
        exec su app -c "uvicorn workers.dispatch_api:dispatch_app --host $WORKER_HOST --port $WORKER_PORT"
    else
        exec uvicorn workers.dispatch_api:dispatch_app --host $WORKER_HOST --port $WORKER_PORT
    fi
else
    # API service: run migrations then start server
    alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000
fi