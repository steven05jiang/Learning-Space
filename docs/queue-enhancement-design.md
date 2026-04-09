# Queue Enhancement Design: Burst Mode with Upstash Free Tier

## Status

Proposed — 2026-04-08

## Executive Summary

Switch the ARQ worker to burst mode to reduce Redis command count, leveraging Upstash's free tier (500k commands/month) instead of migrating to Railway Redis. This keeps Redis costs at $0/mo while eliminating idle polling overhead.

## Motivation

The current Upstash Redis deployment charges per command. ARQ workers continuously poll Redis every 0.5s even when the queue is empty, generating excessive commands at ~$50-200/month. The polling architecture is the root cause.

**New insight:** Upstash has a free tier (500k commands/month). With burst mode at 30s intervals, command usage drops to ~250k/month — well within free tier limits.

## Proposed Changes

### 1. Enable ARQ Burst Mode

**Change:** Add `burst = True` to `WorkerSettings` in `apps/api/workers/worker.py`.

**Effect:**
- Worker polls Redis every 0.5s (unchanged while active)
- When queue is empty, worker exits immediately instead of continuing to poll
- Next run is triggered by an external scheduler (cron/systemd)

**Job latency:** With 30s timer interval, jobs may wait up to 30s before processing. This is acceptable for background processing.

### 2. Configurable Timer Interval

The systemd timer interval is configurable to balance latency vs command usage:

| Interval | Commands/mo (idle) | Free Tier Coverage |
|----------|-------------------|-------------------|
| 10s | ~650k | Exceeded (~23 days) |
| **30s** | ~250k | ✅ Covers ~2 months |
| 60s | ~125k | ✅ Covers ~4 months |

**Default: 30s** — balances responsiveness with free tier limits.

To change interval, modify `OnUnitActiveSec` in `arq-worker.timer`:
```ini
OnUnitActiveSec=30s  # default
OnUnitActiveSec=10s  # lower latency, uses ~650k commands/mo
OnUnitActiveSec=60s  # higher latency, uses ~125k commands/mo
```

### 3. Keep Upstash Redis

Continue using Upstash Redis (free tier). No migration needed.

**Why not Railway Redis?**
- Railway Redis: $5-20/mo with flat-rate pricing
- Upstash Free Tier: $0/mo (500k commands)
- Burst mode keeps us well within free tier limits
- **Railway Redis would cost more** than staying with Upstash

## Implementation

### Step 1: Enable Burst Mode in WorkerSettings

File: `apps/api/workers/worker.py`

```python
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

    # Burst mode: exit when queue is empty
    burst = True

    async def on_startup(ctx):
        await neo4j_driver.connect()

    async def on_shutdown(ctx):
        await neo4j_driver.disconnect()
```

### Step 2: Add CLI Argument for Burst Mode

File: `apps/api/workers/run_worker.py`

```python
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARQ Worker")
    parser.add_argument("--burst", action="store_true", help="Exit when queue is empty")
    args, _ = parser.parse_known_args()
    
    if args.burst:
        WorkerSettings.burst = True
```

### Step 3: Configure Systemd Timer

**File:** `deploy/railway/arq-worker.timer`

```ini
[Unit]
Description=Trigger ARQ Worker every 30 seconds
Requires=arq-worker.service

[Timer]
OnUnitActiveSec=30s
Persistent=true
RandomizedDelaySec=5s

[Install]
WantedBy=timers.target
```

To change interval, edit `OnUnitActiveSec`:
```ini
OnUnitActiveSec=10s  # Lower latency, ~650k commands/mo
OnUnitActiveSec=30s  # Default, ~250k commands/mo
OnUnitActiveSec=60s  # Higher latency, ~125k commands/mo
```

### Step 4: Deploy Systemd Units (VPS/Production)

```bash
sudo cp deploy/railway/arq-worker.service /etc/systemd/system/
sudo cp deploy/railway/arq-worker.timer /etc/systemd/system/

# Edit service file with actual environment variables
sudo nano /etc/systemd/system/arq-worker.service

# Reload systemd, enable and start
sudo systemctl daemon-reload
sudo systemctl enable arq-worker.timer
sudo systemctl start arq-worker.timer

# Verify
sudo systemctl status arq-worker.timer
sudo systemctl list-timers
```

### Step 5: Railway Worker Service

For Railway deployment, set the worker to run continuously but invoke with `--burst`:

In Railway dashboard → Worker service → Variables:
```
BURST_INTERVAL=30
```

The Railway worker service itself runs always-on, but internally uses burst mode with the configured interval.

## Redis Command Analysis

### Poll Mode (Current, Always-On)

| Metric | Value |
|--------|-------|
| Poll interval | 0.5s |
| Commands per poll | ~2 |
| Idle 24/7 | 172,800 commands/day |
| Monthly | ~5.2M commands |
| Upstash Starter (500k free) | Overage: ~$10-50/mo |

### Burst Mode (30s Interval)

| Metric | Value |
|--------|-------|
| Wake-ups | 2,880/day |
| Commands per wake-up (idle) | ~2-3 |
| Idle commands | ~7,200/day |
| Active processing (~10 jobs/day) | ~1,000/day |
| Monthly total | ~250k commands |
| Upstash Free Tier (500k) | ✅ Covered |

### Burst Mode (10s Interval)

| Metric | Value |
|--------|-------|
| Wake-ups | 8,640/day |
| Commands per wake-up (idle) | ~2-3 |
| Idle commands | ~21,600/day |
| Active processing | ~1,000/day |
| Monthly total | ~680k commands |
| Upstash Free Tier (500k) | ❌ Exceeded by ~180k |

## Cost Comparison

| Configuration | Redis Cost/mo |
|---------------|---------------|
| Upstash (poll mode) | $10-50 (overage) |
| **Upstash (burst 30s)** | **$0 (free tier)** |
| Upstash (burst 10s) | ~$1-3 (slight overage) |
| Railway Redis (flat-rate) | $5-20 |

**Conclusion:** Burst mode + Upstash free tier is the lowest-cost option at $0/mo.

## File Changes Summary

| File | Change |
|------|--------|
| `apps/api/workers/worker.py` | Add `burst = True` to `WorkerSettings` |
| `apps/api/workers/run_worker.py` | Add `--burst` CLI argument parsing |
| `Makefile` | dev-stack-up uses poll mode (no `--burst`); burst for production only |
| `deploy/railway/arq-worker.service` | Systemd service unit (new) |
| `deploy/railway/arq-worker.timer` | Systemd timer with configurable `OnUnitActiveSec` (new) |
| `docs/queue-enhancement-design.md` | This file (new) |

## Environment Matrix

| Environment | Worker Mode | Redis Provider | Cost |
|-------------|-------------|----------------|------|
| Local dev | Poll (continuous) | Docker Compose | $0 |
| Production (VPS) | Burst + systemd timer | Upstash | $0 |
| Railway worker | Burst via timer | Upstash | $0 |

## Rollback Plan

1. Set `burst = False` in `WorkerSettings`
2. Stop/disable systemd timer
3. Deploy — worker runs continuously again

## Open Questions

- [x] Is 30s interval acceptable for job latency? (Yes, acceptable for background processing)
- [ ] Should we add AOF persistence for durability? (Optional, adds ~$0.50-2/mo)
- [ ] Monitor actual command usage via Upstash dashboard after deployment
