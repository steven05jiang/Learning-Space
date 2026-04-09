# Queue Enhancement Design: Burst Mode + Railway Redis

## Status

Proposed — 2026-04-08

## Executive Summary

Replace the Upstash Redis (per-command pricing) with a self-hosted Redis on Railway (flat-rate), and switch the ARQ worker to burst mode. This eliminates per-command Redis costs entirely while keeping async job processing.

## Motivation

The current Upstash Redis deployment charges per command. ARQ workers continuously poll Redis every 0.5s even when the queue is empty, generating excessive commands at ~$50-200/month. The polling architecture is the root cause.

## Proposed Changes

### 1. Switch to Railway Redis (Self-Hosted)

**Why Railway:**
- Flat-rate pricing (no per-command charges)
- Minimal configuration (Redis 7, 256MB RAM starter plan)
- managed — zero operational overhead vs self-hosting on a VPS
- Same Redis protocol — zero code changes required (just `REDIS_URL`)

**Railway Configuration (Minimum):**
- Plan: Starter (256MB RAM, shared CPU)
- Redis version: 7
- Starting price: ~$5/month (depends on usage tier)
- No persistence required (ARQ jobs are ephemeral; results stored in Redis with TTL)

**Migration:**
1. Provision Redis instance on Railway
2. Update `REDIS_URL` in environment variables
3. Verify ARQ worker connects
4. Deprovision Upstash

**Cost impact:**
| Provider | Model | Estimated Cost |
|----------|-------|---------------|
| Upstash (current) | Per command | $50-200/month |
| Railway Redis | Flat-rate (256MB) | ~$5-20/month |

### 2. Enable ARQ Burst Mode

**Change:** Add `burst = True` to `WorkerSettings` in `apps/api/workers/worker.py`.

**Effect:**
- Worker polls Redis every 0.5s (unchanged)
- When queue is empty, worker exits immediately instead of continuing to poll
- Next run is triggered by an external scheduler (cron/systemd)

**To compensate for burst exit:**
- Run worker via cron every 30 seconds: `*/30 * * * * cd /path/to/api && uv run arq workers.worker.WorkerSettings --burst`
- Or use systemd timer with OnUnitActiveSec=30s

**Redis command reduction:**
| Mode | Worker state | Commands during idle |
|------|-------------|---------------------|
| Normal (`burst=False`) | Always running | Continuous polling (every 0.5s = 7200/hr) |
| Burst (`burst=True`) + cron 30s | Ephemeral | Zero when queue empty, ~2/min from cron wake-up |

Note: With burst mode, the 30s cron interval means jobs may wait up to 30s before processing. This is acceptable for background processing. For lower latency, use a shorter interval (e.g., 10s).

### 3. Deprovision Upstash

After verifying Railway Redis is working:
1. Export any remaining data (if any)
2. Delete Upstash Redis instance
3. Remove Upstash credentials from environment

## Implementation

### Step 1: Provision Railway Redis

1. Create Railway account at railway.app
2. New Project → Add Redis → Select Redis 7 image
3. Note the connection URL: `rediss://user:pass@host:port`
4. Add `REDIS_URL` to Railway environment variables

### Step 2: Update WorkerSettings

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

### Step 3: Update run_worker.py for burst CLI argument

File: `apps/api/workers/run_worker.py`

Add `--burst` flag support (ARQ CLI already supports this natively):

```python
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ARQ Worker")
    parser.add_argument("--burst", action="store_true", help="Exit when queue is empty")
    args, _ = parser.parse_known_args()
    
    # Apply burst mode if CLI flag is set
    if args.burst:
        WorkerSettings.burst = True
```

Then run: `arq workers.worker.WorkerSettings --burst`

### Step 4: Configure Cron/Systemd Trigger

**Option A: Cron (simpler)**

```bash
# Every 30 seconds
*/30 * * * * cd /path/to/apps/api && uv run arq workers.worker.WorkerSettings --burst >> /var/log/arq-worker.log 2>&1
```

**Option B: Systemd timer (recommended for production)**

```ini
# /etc/systemd/system/arq-worker.service
[Unit]
Description=Learning Space ARQ Worker
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/apps/api
ExecStart=/path/to/venv/bin/arq workers.worker.WorkerSettings --burst
Environment=REDIS_URL=rediss://...
Environment=DATABASE_URL=...
```

```ini
# /etc/systemd/system/arq-worker.timer
[Unit]
Description=Run ARQ worker every 30s

[Timer]
OnUnitActiveSec=30s
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable arq-worker.timer
sudo systemctl start arq-worker.timer
```

### Step 5: Update Makefile dev-stack-up

File: `Makefile`

Update the worker startup command to use burst mode in development:

```makefile
dev-stack-up:
    # ... existing steps ...
    @echo "   5. Starting worker (arq, burst mode)..."
    cd apps/api && uv run python workers/run_worker.py --burst > /tmp/worker.log 2>&1 &
```

### Step 6: Update run_worker.py to handle --burst argument

File: `apps/api/workers/run_worker.py`

```python
if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Parse CLI arguments for burst mode
    parser = argparse.ArgumentParser(description="Learning Space ARQ Worker")
    parser.add_argument("--burst", action="store_true", help="Exit when queue is empty")
    args, unknown = parser.parse_known_args()

    if args.burst:
        WorkerSettings.burst = True
        logging.info("Burst mode enabled — worker will exit when queue is empty")

    log_level = logging.getLevelName(logging.getLogger().getEffectiveLevel())
    logging.info("Worker starting up | log_level=%s", log_level)
    print("Starting Learning Space task worker...")
    print("Press Ctrl+C to stop")
```

Add import: `import argparse`

## File Changes Summary

| File | Change |
|------|--------|
| `apps/api/workers/worker.py` | Add `burst = True` to `WorkerSettings` |
| `apps/api/workers/run_worker.py` | Add `--burst` CLI argument parsing |
| `Makefile` | Update worker startup to use `--burst` in dev |
| `.env.production` | Update `REDIS_URL` to Railway Redis |
| `docs/queue-enhancement-design.md` | This file (new) |

## Rollback Plan

1. Set `burst = False` in `WorkerSettings`
2. Restore previous `REDIS_URL` (Upstash)
3. Deploy — worker runs continuously again

## Cost Comparison

| Configuration | Monthly Cost |
|---------------|-------------|
| Upstash (current, per-command) | $50-200 |
| Railway Redis (256MB) + burst | ~$5-20 |
| **Savings** | **~80-90%** |

## Open Questions

- [ ] What is the current Upstash command count? (Measure before/after)
- [ ] Is 30s poll interval acceptable for job latency? (Alternative: 10s for lower latency)
- [ ] Should we keep a continuously running worker for low-latency needs, and use burst for background jobs?