# Sprints

Tracks each dev-cycle goal, selected tasks, and final outcome.
One entry per `/project-dispatch` invocation that reaches Phase 4.

---

## Sprint 2026-03-23-A — Feedback Implementation

**Status:** 🔄 Active
**Sprint Goal:** Implement all FB-001 through FB-005 feedback items so DEMO-006 (Feedback Verification) is runnable
**Exit Gate:** DEMO-006 — Feedback Verification demo executes successfully
**Started:** 2026-03-23
**Completed:** (pending)

### Notes

- DEV-056 (tiered fetch) is the heaviest task (L) — includes Playwright headless browser in worker Docker image
- Layer 0 tasks are independently dispatchable; Layer 1 tasks unlock after their Layer 0 prereqs merge
- DEV-061 also updates INT-029–035 integration tests (Neo4j schema change)
- max-agents: 1 (sequential dispatch per MEMORY.md feedback)

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| DEV-056 | Tiered URL fetch strategy (FB-001) | ⏳ Pending |
| DEV-057 | processing_status field + Alembic migration (FB-002) | ⏳ Pending |
| DEV-060 | Categories table, seed 10 root categories, /categories API (FB-003) | ⏳ Pending |
| DEV-065 | Fix graph node popup overflow (FB-005) | ⏳ Pending |
| DEV-058 | Worker pipeline state machine (FB-002) — needs DEV-057 | ⏳ Pending |
| DEV-059 | Re-process action in resource detail UI (FB-002) — needs DEV-057 | ⏳ Pending |
| DEV-061 | Neo4j Root/Category/Tag three-level hierarchy (FB-003) — needs DEV-060 | ⏳ Pending |
| DEV-062 | LLM prompt: tag reuse + top_level_categories (FB-003) — needs DEV-060 | ⏳ Pending |
| DEV-063 | Category management UI in Settings (FB-003) — needs DEV-060 | ⏳ Pending |
| DEV-064 | Tag editor in resource detail UI (FB-004) — needs DEV-061 | ⏳ Pending |
| DEMO-006 | Feedback Verification Demo — needs DEV-056–DEV-065 | ⏳ Pending |

---

## Sprint 2026-03-22-B — Local Dev Stack Commands

**Status:** ✅ Complete
**Sprint Goal:** Add make dev-stack-up / dev-stack-down to bring up and tear down the full local dev stack in one command
**Exit Gate:** `make dev-stack-up` starts infra + API + web; `make dev-stack-down` stops all three cleanly
**Started:** 2026-03-22
**Completed:** 2026-03-22

### Notes

- BUILD task (not DEV) — tracked in build-tracker.md
- Single task sprint — no dependencies

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| BUILD-003 | Add dev-stack-up / dev-stack-down make targets | ✅ Completed (PR #123) |

---

## Sprint 2026-03-22-A — AI Chat Backend Foundation

**Status:** ✅ Complete
**Cycle Goal:** Start AI chat backend — lay conversation storage and LangGraph agent foundation
**Started:** 2026-03-22
**Completed:** 2026-03-22

### Notes

- DEV-035 dispatches first (S, ~20min) — unblocks DEV-032
- DEV-032 dispatches after DEV-035 merges (L, ~60min) — unblocks DEV-033 → DEV-034 → DEV-053 → DEMO-005

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| DEV-035 | Conversation storage (DB schema) | ✅ Completed (PR #117) |
| DEV-032 | LangGraph agent with tools | ✅ Completed (PR #119) |

---

## Sprint 2026-03-21-A — Resource Pipeline + Graph View

**Status:** ✅ Complete
**Cycle Goal:** Complete the full resource processing pipeline (unauthenticated fetch + LLM worker) and knowledge graph backend + integration tests, then run a combined DEMO-003/004
**Started:** 2026-03-21
**Completed:** 2026-03-22

### Notes

- DEV-021 (authenticated URL fetcher) deferred — DEV-023 uses unauthenticated fetch only
- LLM calls to be mocked in unit tests and integration tests

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| DEV-025 | Graph service (Neo4j operations) | ✅ Completed (PR #90) |
| DEV-023 | process_resource job (unauthenticated fetch only) | ✅ Completed (PR #92) |
| DEV-030 | GET /graph/nodes/{id}/resources | ✅ Completed (PR #94) |
| DEV-027 | Graph sync job for resource deletion | ✅ Completed (PR #103) |
| DEV-052 | Wire graph UI to real API | ✅ Completed (PR #105) |
| DEV-028 | GET /graph | ✅ Completed (PR #99) |
| DEV-029 | POST /graph/expand | ✅ Completed (PR #101) |
| DEV-026 | Graph update in worker pipeline | ✅ Completed (PR #97) |
| DEV-024 | Unit tests — Worker | ✅ Completed (PR #108) |
| DEV-031 | Unit tests — Graph API | ✅ Completed (PR #110) |
| INT-024–028 | Worker integration tests | ✅ Completed (PR #112) |
| INT-029–035 | Graph integration tests | ✅ Completed (PR #113) |
| DEMO-003+004 | Combined pipeline + graph demo | ✅ Completed (run-1 2026-03-22) |
