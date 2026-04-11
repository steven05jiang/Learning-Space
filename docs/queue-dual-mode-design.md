# Queue Dual-Mode Design: Redis + In-Memory Fallback

## Status

Proposed — 2026-04-10

## Executive Summary

Add in-memory queue fallback to the worker so the system continues operating when Redis is unavailable. No configuration changes are needed — the system automatically falls back when Redis fails.

## Architecture

```
Normal Mode:
  API → Redis Queue → Worker (polls Redis)

Fallback Mode (Redis unavailable):
  API → Worker /dispatch endpoint → In-Memory Queue → Worker
```

## Components

### 1. Worker In-Memory Queue (`workers/in_memory_queue.py`)

An `asyncio.Queue` that the worker monitors alongside Redis polling:

```python
import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

@dataclass
class QueuedJob:
    job_id: str
    function_name: str
    args: tuple
    kwargs: dict

class InMemoryQueue:
    def __init__(self):
        self._queue: asyncio.Queue[QueuedJob] = asyncio.Queue()
        self._job_results: dict[str, asyncio.Future] = {}
    
    async def enqueue(self, job_id: str, function_name: str, args, kwargs) -> None:
        await self._queue.put(QueuedJob(job_id, function_name, args, kwargs))
    
    async def dequeue(self) -> QueuedJob:
        return await self._queue.get()
    
    def task_done(self) -> None:
        self._queue.task_done()
```

### 2. Worker Dispatch API (`workers/dispatch_api.py`)

A lightweight FastAPI app running on the worker that receives direct task dispatches:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class DispatchRequest(BaseModel):
    job_id: str
    function_name: str
    args: list = []
    kwargs: dict = {}

class DispatchResponse(BaseModel):
    job_id: str
    status: str

@app.post("/dispatch")
async def dispatch_task(request: DispatchRequest) -> DispatchResponse:
    # Add to in-memory queue and return immediately
    await in_memory_queue.enqueue(
        request.job_id,
        request.function_name,
        tuple(request.args),
        request.kwargs
    )
    return DispatchResponse(job_id=request.job_id, status="queued")
```

### 3. Worker Dual Monitor (`workers/worker.py`)

Modified worker that monitors both Redis and in-memory queue:

```python
class WorkerSettings:
    # ... existing config ...
    
    # Additional setting for direct dispatch port
    dispatch_port: int = 8001
    
    async def run(self):
        """Main worker loop monitoring both queues."""
        while True:
            # Poll Redis for jobs (existing behavior)
            # Check in-memory queue for direct dispatches
            # Process whichever is ready
```

### 4. API Fallback Logic (`core/queue.py`)

Modified `enqueue_job` that tries Redis first, falls back to direct dispatch:

```python
import httpx

WORKER_DISPATCH_URL = "http://localhost:8001/dispatch"

async def enqueue_job(job_name: str, *args, **kwargs) -> str:
    job_id = str(uuid.uuid4())
    
    # Try Redis first
    try:
        pool = await create_queue_pool()
        try:
            job = await pool.enqueue_job(job_name, *args, _queue_name=QUEUE_NAME, **kwargs)
            return job.job_id
        finally:
            await pool.aclose()
    except Exception as redis_error:
        logger.warning(f"Redis enqueue failed, falling back to direct dispatch: {redis_error}")
    
    # Fallback: direct dispatch to worker
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            WORKER_DISPATCH_URL,
            json={
                "job_id": job_id,
                "function_name": job_name,
                "args": list(args),
                "kwargs": kwargs
            }
        )
        if response.status_code != 200:
            raise ConnectionError(f"Worker dispatch failed: {response.text}")
        return job_id
```

### 5. Graceful Degradation

Both API and worker must handle Redis failure gracefully:

**API side:**
- `enqueue_job` catches Redis exceptions and falls back to direct dispatch
- If direct dispatch also fails, raise a `ConnectionError` (never crash)

**Worker side:**
- If Redis is unavailable during startup, continue with in-memory queue only
- If Redis goes down mid-operation, log warning and continue processing in-memory queue
- When Redis comes back, resume polling Redis automatically

## API Endpoint

### POST /dispatch

Internal endpoint on worker (not exposed externally) for direct task dispatch.

**Request:**
```json
{
  "job_id": "uuid-string",
  "function_name": "process_resource",
  "args": ["resource123"],
  "kwargs": {"options": {"key": "value"}}
}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "queued"
}
```

## Implementation Plan

### Phase 1: Core Components

1. Create `workers/in_memory_queue.py` — asyncio.Queue wrapper
2. Create `workers/dispatch_api.py` — FastAPI app for dispatch
3. Modify `workers/worker.py` — add dual queue monitoring
4. Modify `core/queue.py` — add Redis-fallback logic
5. Add health check endpoint to dispatch API

### Phase 2: Integration

6. Update `run_worker.py` to start dispatch API alongside worker
7. Add `DISPATCH_PORT` env var configuration (default 8001)
8. Update Makefile to pass dispatch port to worker

### Phase 3: Testing

9. Add unit tests for in-memory queue
10. Add integration tests for fallback behavior
11. Test Redis failure scenario

## File Changes Summary

| File | Change |
|------|--------|
| `workers/in_memory_queue.py` | NEW: In-memory queue implementation |
| `workers/dispatch_api.py` | NEW: FastAPI dispatch endpoint |
| `workers/worker.py` | Add dual-queue monitoring, dispatch API |
| `core/queue.py` | Add Redis fallback to direct dispatch |
| `run_worker.py` | Start dispatch API server |
| `Makefile` | Pass DISPATCH_PORT env var |

## No Configuration Required

The system automatically detects Redis failures and switches to fallback mode. No env vars or config changes needed to enable this behavior.

Optional env vars (for advanced users):
- `DISPATCH_PORT` — Port for worker dispatch API (default: 8001)
- `REDIS_POLL_INTERVAL` — Already exists, controls Redis poll frequency

## Rollback Plan

1. Remove fallback logic from `core/queue.py`
2. Remove dispatch API from worker
3. Restart services

No data migration needed — Redis remains the primary queue.
