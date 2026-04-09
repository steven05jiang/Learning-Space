# Railway Redis Provisioning Guide

This guide walks through provisioning a self-hosted Redis instance on Railway to replace Upstash.

## Why Railway Redis?

| Provider | Pricing Model | Est. Monthly Cost |
|----------|---------------|-------------------|
| Upstash (current) | Per-command | $50-200 |
| Railway Redis | Flat-rate (256MB) | ~$5-20 |

**Savings: ~80-90%**

## Step 1: Provision Redis on Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"** → **"Add Redis"**
3. Select **Redis 7** image
4. Railway will provision a Redis instance and provide a connection URL

## Step 2: Get the Connection URL

1. Click on your Redis service in Railway dashboard
2. Go to the **"Variables"** tab
3. Copy the `REDIS_URL` variable (format: `rediss://user:password@host:port`)

If no `REDIS_URL` variable exists:
1. Go to the **"Connect"** tab
2. Copy the connection string (use `rediss://` for TLS, `redis://` for non-TLS)

## Step 3: Add Redis URL to Railway Project

### Option A: Add to API Service Variables

1. Go to your **API service** in Railway
2. Navigate to **Variables** tab
3. Add/Update: `REDIS_URL=rediss://user:password@host:port`

### Option B: Add to Worker Service Variables

1. Go to your **Worker service** in Railway
2. Navigate to **Variables** tab
3. Add/Update: `REDIS_URL=rediss://user:password@host:port`

## Step 4: Configure Worker for Burst Mode

The worker now runs in burst mode (already implemented in `redis-enhancement` branch):

- Worker exits immediately when the queue is empty
- Railway worker service should be set to **always running** (not on-demand) since the systemd timer handles job scheduling

### Worker Service Settings

In Railway dashboard for the worker service:

1. Go to **Settings** → **Scaling**
2. Set **Max Instances**: 1 (dedicated worker)
3. Set **Region**: Same as API/Redis for low latency

### Alternative: Systemd Timer (Self-Hosted)

If deploying on a VPS with systemd instead of Railway worker service:

```bash
# Copy service and timer files
sudo cp deploy/railway/arq-worker.service /etc/systemd/system/
sudo cp deploy/railway/arq-worker.timer /etc/systemd/system/

# Edit the service file with your actual environment variables
sudo nano /etc/systemd/system/arq-worker.service
# Update the Environment= lines with your actual values

# Reload systemd, enable and start the timer
sudo systemctl daemon-reload
sudo systemctl enable arq-worker.timer
sudo systemctl start arq-worker.timer

# Verify timer is active
sudo systemctl status arq-worker.timer
sudo systemctl list-timers
```

## Step 5: Update `.env.production`

Update your production environment file:

```bash
# Replace Upstash URL with Railway Redis URL
REDIS_URL=rediss://user:password@railway-redis-host:port
```

**Example:**
```bash
# Before (Upstash)
REDIS_URL=rediss://default:xxxxx@finer-ewe-86271.upstash.io:6379

# After (Railway)
REDIS_URL=rediss://default:xxxxx@persistent-redis-prod-12345-abcde.railway.app:6379
```

## Step 6: Verify the Connection

### Test Locally

```bash
cd apps/api
uv sync --frozen
REDIS_URL=rediss://user:password@host:port uv run python -c "
from core.queue import redis_settings
from arq import ArqRedis
import asyncio
async def test():
    redis = await ArqRedis.create(redis_settings)
    await redis.ping()
    print('Redis connection OK')
    await redis.aclose()
asyncio.run(test())
"
```

### Check Railway Logs

1. Go to Railway dashboard → Worker service → **Logs**
2. Look for: `Starting Learning Space task worker...`
3. If you see connection errors, verify `REDIS_URL` is correct

## Step 7: Deprovision Upstash

**After verifying Railway Redis is working:**

1. Go to [Upstash Console](https://console.upstash.com)
2. Select your Redis instance
3. Go to **Settings** → **Danger Zone**
4. Click **Delete Database**
5. Confirm deletion

## Rollback Plan

If Railway Redis has issues:

1. Update `REDIS_URL` back to Upstash in Railway variables
2. Restart the worker service
3. Re-provision Upstash if needed (data will be lost)

## Files Created

```
deploy/railway/
├── arq-worker.service   # Systemd service unit
└── arq-worker.timer    # Systemd timer (30s interval)
```

## Cost Breakdown

| Resource | Spec | Est. Monthly Cost |
|----------|------|-------------------|
| Railway Redis | 256MB RAM, shared CPU | $5-20 |
| Worker service | 512MB RAM, 1 instance | Included in Railway Pro or usage-based |

**Total Redis cost reduction: ~$45-180/month**
