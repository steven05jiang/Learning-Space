# Bugs Tracker

**Scope:** Bug reports, defects, regressions
**Task prefix:** `BUG-`
**Initialized:** 2026-03-15
**Last Updated:** 2026-03-23

---

## Progress Summary

- Total: 14 tasks
- ✅ Fixed: 13
- 🔄 Active: 0
- ⏳ Pending: 1
- ⚠️ Stuck: 0

---

## Bugs

- [x] BUG-001: Migrate JWT from python-jose to authlib — CVE-2024-23342 eliminated; migrated core/jwt.py to authlib.jose (PR #32 ✅)
- [x] BUG-002: POST /resources returns 500 — removed timezone-aware datetime args from Resource() constructor; ORM defaults handle timestamps (PR #33 ✅)
- [x] BUG-003: GET /auth/me endpoint missing — added endpoint to routers/auth.py with tests (PR #33 ✅)
- [x] BUG-004: No CORS middleware — fixed inline during demo 001 (added CORSMiddleware to main.py, cors_origins to config)
- [x] BUG-dashboard-svg: Dashboard SVG icon renders oversized without CSS — added width="20" height="20" to inline SVG in dashboard/page.tsx (PR #30 ✅)
- [x] BUG-005: ~~CORS allow_origins port 3001 blocked~~ — Invalid; web dev server runs on port 3000 which is already in allow_origins. Demo README corrected 2026-03-21.
- [x] BUG-006: Pending tag overflow in resources page — long URL title causes "Pending" badge to overflow card bounds (PR #63 ✅)
- [x] BUG-007: Settings linked accounts shows incorrect connection status — Google shown as "not connected" after OAuth login; resolved by BUG-008 (PR #65 ✅)
- [x] BUG-008: OAuth lint fix + accounts table persistence — unused mock_account variable, lint errors, OAuth callback not persisting to accounts table; added GET /auth/accounts endpoint (PR #65 ✅)
- [x] BUG-009: LLM model deprecated — default model `claude-3-5-sonnet-20241022` returns 404; updated default to `claude-haiku-4-5-20251001` in services/llm_processor.py; found during DEMO-003 run-1 (PR #114 ✅)
- [x] BUG-010: Worker never processes resources — three root causes: (1) `create_resource` called placeholder `process_resource_background_job` (just a logger.info) instead of `queue_service.enqueue_resource_processing`; (2) `process_resource` and `sync_graph` in tasks.py missing `ctx` as first arg (ARQ always passes context as arg 1, so resource_id was receiving the ctx dict); (3) jobs enqueued to arq default queue but worker listened on `learning_space_queue` (missing `_queue_name` on enqueue). Fixed routers/resources.py, workers/tasks.py, core/queue.py. ✅
- [x] BUG-012: Knowledge graph UI shows "Could not load knowledge graph" — all three fetch calls in knowledge-graph.tsx (`/graph`, `/graph/nodes/:id/resources`, `/graph/expand`) were missing the `Authorization: Bearer` header; API returns 401 which triggers the error state. Fixed by reading `localStorage.getItem("auth_token")` and attaching it to all three calls, matching the pattern used in the rest of the web app. ✅
- [ ] BUG-013: `cleanup_orphan_tags` CypherSyntaxError on resource deletion — `WITH t.name AS tag_name` projected away `t` before `DELETE t`; fixed by adding `t` to the WITH clause. Fix in `services/graph_service.py:155`. (no PR created yet — reverted to pending)
- [x] BUG-011: Neo4j graph update fails in worker — two root causes: (1) `neo4j_driver.connect()` only called in FastAPI lifespan, never in the worker process; added `on_startup`/`on_shutdown` hooks to `WorkerSettings`; (2) schema mismatch: `UNIQUE t.name` constraint conflicted with per-user `MERGE {name, owner_id}` — dropped the wrong global constraint and replaced with a composite `(name, owner_id)` index (NODE KEY not available on CE). Fixed workers/worker.py, services/neo4j_driver.py. ✅
