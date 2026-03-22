# Sprints

Tracks each dev-cycle goal, selected tasks, and final outcome.
One entry per `/project-dispatch` invocation that reaches Phase 4.

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
