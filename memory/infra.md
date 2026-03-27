# Infrastructure — Learning Space

> Credentials are stored in `apps/api/.env.production` (not committed). This file documents service metadata only.

---

## Data Services

### Supabase (PostgreSQL)
- **Region:** US East 1
- **Free tier limits:** 500 MB database, 2 GB bandwidth, 50k monthly active users
- **Dashboard:** https://supabase.com/dashboard
- **Env vars:** `DATABASE_URL`

### Neo4j AuraDB Free
- **Region:** US East 1
- **Free tier limits:** 1 instance, 200k nodes, 400k relationships, 200 MB storage
- **Dashboard:** https://console.neo4j.io
- **Env vars:** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`

### Upstash Redis
- **Region:** US East 1
- **Free tier limits:** 10k commands/day, 256 MB storage, 1 database
- **Dashboard:** https://console.upstash.com
- **Env vars:** `REDIS_URL`

---

## Hosting

### Railway
- **Services:** API, Worker (see `apps/api/Dockerfile`)
- **Template:** created (OPS-002 Step 5)
- **Env vars:** all vars from `apps/api/.env.production.example` set in Railway dashboard

---

## Change Log

- 2026-03-27 — Supabase, Neo4j AuraDB, Upstash provisioned (US East 1); Railway template created
