# BUILD-003: Add dev-stack-up / dev-stack-down make targets

**Status:** ✅ Completed
**Priority:** Medium
**Started:** 2026-03-22
**Completed:** 2026-03-22
**Branch:** feature/build-003-dev-stack-commands
**PR:** #123 (merged)

## Goal

Add two Makefile targets for running the full local development stack without
Docker for the API or web layers:

- `make dev-stack-up` — start infra (Docker), API (uvicorn, background), and web (Next.js, background)
- `make dev-stack-down` — stop infra (Docker), and kill API/web processes by port

## Acceptance Criteria

1. `make dev-stack-up` starts all three layers in the correct order:
   - `make infra-up` (postgres, neo4j, redis via Docker)
   - API: `cd apps/api && uv run uvicorn main:app --reload --port 8000` (background, PID saved)
   - Web: `cd apps/web && npm run dev` (background, PID saved, port 3000)
   - Prints the URLs for API and web once started

2. `make dev-stack-down` tears down cleanly:
   - `docker compose down` (infra)
   - Kill process on port 8000 (API) using `lsof -ti :8000 | xargs kill -9` (no-op if not running)
   - Kill process on port 3000 (Web) using `lsof -ti :3000 | xargs kill -9` (no-op if not running)
   - Prints confirmation for each step

3. Targets are added to the `.PHONY` list in Makefile

4. No Docker container is created for API or web — they run natively

## Implementation Summary

Added `dev-stack-up` and `dev-stack-down` targets to the root Makefile. `dev-stack-up` starts infra via `make infra-up`, then launches the API (uvicorn on port 8000) and web (Next.js on port 3000) in the background with output redirected to `/tmp/api.log` and `/tmp/web.log`. `dev-stack-down` runs `docker compose down` and kills any processes on ports 8000 and 3000 using `lsof -ti` piped to `xargs kill -9 || true` (safe no-op when nothing is running). Both targets added to `.PHONY`.

## Review Rounds

1 round — APPROVED

## Progress Log

- 2026-03-22 — Task created via project-sync
- 2026-03-22 — Dispatched to implementer
- 2026-03-22 — Implementation complete: Added dev-stack-up and dev-stack-down targets to Makefile, PR #123 created
- 2026-03-22 — Review round 1: APPROVED
- 2026-03-22 — PR #123 merged ✅
