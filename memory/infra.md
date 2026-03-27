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

### Fly.io (Primary)
- **Services:** API, Worker
- **API URL:** https://learning-space-api.fly.dev (to be updated after deployment)
- **Worker:** Background service for resource processing
- **Dockerfile:** `apps/api/Dockerfile` with `SERVICE_TYPE` build arg (api/worker)
- **Auto-deploy:** GitHub Actions workflow from `main` branch
- **Migrations:** API service runs `alembic upgrade head` on startup
- **Config:** `apps/api/fly.api.toml`, `apps/api/fly.worker.toml`
- **GitHub Actions:** `.github/workflows/fly-deploy.yml`
- **Environment variables:**
  - `DATABASE_URL` (Supabase PostgreSQL)
  - `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` (Neo4j AuraDB)
  - `REDIS_URL` (Upstash Redis)
  - `JWT_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  - `OAUTH_REDIRECT_BASE_URL`, `ALLOWED_EMAILS`
  - `LLM_PROVIDER`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`
  - `FLY_API_TOKEN` (for GitHub Actions deployment)
- **Free tier limits:** 3 shared VMs (256MB each), 3GB storage, 160GB transfer

### Railway (Alternative)
- **Services:** API, Worker
- **API URL:** https://web-production-XXXX.up.railway.app (if deployed)
- **Worker:** Background service for resource processing
- **Dockerfile:** `apps/api/Dockerfile` with `SERVICE_TYPE` build arg (api/worker)
- **Auto-deploy:** Enabled from `main` branch
- **Migrations:** API service runs `alembic upgrade head` on startup
- **Config:** `railway.toml` at repository root
- **Environment variables:** Same as Fly.io (minus `FLY_API_TOKEN`)
- **Free tier limits:** $5/month credit, 512MB memory per service, 1GB disk per service

---

## Change Log

- 2026-03-27 — Supabase, Neo4j AuraDB, Upstash provisioned (US East 1); Railway template created; Fly.io deployment added as primary provider
