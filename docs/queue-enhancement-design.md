# Queue Enhancement Design: Upstash Poll Interval Configuration

## Status

Proposed — 2026-04-08

## Executive Summary

Reduce Redis command count on Upstash by configuring the worker poll interval to 30s instead of the default 0.5s. This keeps command usage within the free tier (500k/month) without code or deployment changes.

**Note:** This approach is designed for Railway deployment where the worker runs as an always-on service. The poll interval is configured via `REDIS_POLL_INTERVAL` environment variable.

## Motivation

The current Upstash Redis deployment charges per command. With default 0.5s poll interval, ARQ workers generate ~5.2M commands/month — well beyond the free tier limit.

**New insight:** With 30s poll interval, command usage drops to ~250k/month — within free tier limits, costing $0/mo.

## Proposed Changes

### 1. Add Poll Interval Configuration

**Change:** Add configurable `poll_interval` to `WorkerSettings` in `apps/api/workers/worker.py`, defaulting to 30s.

**Effect:**
- Worker polls Redis at configured interval instead of default 0.5s
- Lower command count = stays within Upstash free tier
- No code changes needed in production — just set env var

### 2. Environment Variable Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_POLL_INTERVAL` | `30` | Poll interval in seconds for ARQ worker |

Set `REDIS_POLL_INTERVAL=30` in Railway environment variables to reduce command count.

## Redis Command Analysis

### Current (0.5s Poll Interval)

| Metric | Value |
|--------|-------|
| Poll interval | 0.5s |
| Commands per poll | ~2 |
| Idle 24/7 | 172,800 commands/day |
| Monthly | ~5.2M commands |
| Upstash Free Tier (500k) | **Exceeded by ~4.7M** |

### With 30s Poll Interval

| Metric | Value |
|--------|-------|
| Poll interval | 30s |
| Commands per poll | ~2 |
| Idle 24/7 | 5,760 commands/day |
| Monthly | ~173k commands |
| Upstash Free Tier (500k) | ✅ Covered (~3 months) |

### With 10s Poll Interval

| Metric | Value |
|--------|-------|
| Poll interval | 10s |
| Commands per poll | ~2 |
| Idle 24/7 | 17,280 commands/day |
| Monthly | ~518k commands |
| Upstash Free Tier (500k) | ⚠️ Slightly exceeded |

**Recommended:** `REDIS_POLL_INTERVAL=30` (default)

## Implementation

### Step 1: Add Poll Interval to WorkerSettings

File: `apps/api/workers/worker.py`

```python
import os

class WorkerSettings:
    """ARQ worker configuration."""

    redis_settings = redis_settings

    functions = [process_resource, sync_graph]

    max_jobs = 10
    job_timeout = 600
    keep_result = 3600
    max_tries = 3
    on_job_failure = job_failed
    queue_name = QUEUE_NAME

    # Poll interval in seconds (default 30s to reduce Upstash commands)
    poll_interval = int(os.environ.get("REDIS_POLL_INTERVAL", 30))

    async def on_startup(ctx):
        await neo4j_driver.connect()

    async def on_shutdown(ctx):
        await neo4j_driver.disconnect()
```

### Step 2: Update run_worker.py

File: `apps/api/workers/run_worker.py`

Read `BURST_MODE` env var (for VPS/self-hosted use case):

```python
import os

if os.environ.get("BURST_MODE", "").lower() == "true":
    WorkerSettings.burst = True
```

### Step 3: Configure Railway Environment

In Railway dashboard → Worker service → Variables:

```
REDIS_POLL_INTERVAL=30
```

**For local development:** No changes needed. Default 30s poll interval works fine with local Docker Redis (no cost concern).

## Why Not Burst Mode with Systemd Timer?

Burst mode (worker exits when queue empty, triggered by systemd timer) works well for **self-hosted VPS deployments** where you control the scheduler.

For **Railway deployment**, this doesn't apply because:
- Railway worker service runs as an always-on managed service
- You can't install systemd timers on Railway
- Setting `burst=True` would cause the worker to exit and Railway would immediately restart it, creating a spin loop

**Therefore:** Use `REDIS_POLL_INTERVAL` instead — same command reduction without deployment model changes.

## Cost Comparison

| Configuration | Commands/mo | Upstash Cost |
|---------------|-------------|-------------|
| Default (0.5s) | 5.2M | $10-50/mo |
| **Poll interval 30s** | ~173k | **$0 (free tier)** |
| Poll interval 10s | ~518k | $0 (free tier, tight) |

**Conclusion:** `REDIS_POLL_INTERVAL=30` is the lowest-risk configuration.

## File Changes Summary

| File | Change |
|------|--------|
| `apps/api/workers/worker.py` | Add `poll_interval` with `REDIS_POLL_INTERVAL` env var support |
| `apps/api/workers/run_worker.py` | Replace `--burst` argparse with `BURST_MODE` env var |
| `Makefile` | dev-stack-up uses default poll interval (continuous) |
| `docs/queue-enhancement-design.md` | Updated with poll interval approach |

## Rollback Plan

1. Remove or increase `REDIS_POLL_INTERVAL` in Railway variables
2. Restart worker service

## Open Questions

- [x] Is 30s poll interval acceptable for job latency? (Yes, acceptable for background processing)
- [ ] Monitor actual command usage via Upstash dashboard after deployment
- [ ] Consider AOF persistence for durability? (Optional, adds ~$0.50-2/mo)
