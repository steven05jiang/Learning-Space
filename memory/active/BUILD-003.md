# BUILD-003: Add dev-stack-up / dev-stack-down make targets

**Status:** ⏳ Pending
**Priority:** Medium
**Branch:** (TBD)
**PR:** (TBD)

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

## Notes

- API port: 8000 (uvicorn default)
- Web port: 3000 (Next.js default, required for Google OAuth redirect URI — see memory feedback)
- Use `run_in_background` approach with shell `&` and output redirected to logs
  e.g. `cd apps/api && uv run uvicorn main:app --reload --port 8000 > /tmp/api.log 2>&1 &`
- `lsof -ti :<port>` returns empty string if nothing is on that port; pipe to `xargs kill -9` is safe with `|| true`

## Files to Modify

- `Makefile` — add `dev-stack-up`, `dev-stack-down` targets and update `.PHONY`

## Progress Log

- 2026-03-22 — Task created via project-sync
