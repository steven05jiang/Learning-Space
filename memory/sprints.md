# Sprints

Tracks each dev-cycle goal, selected tasks, and final outcome.
One entry per `/project-dispatch` invocation that reaches Phase 4.

---

## Sprint 2026-03-21-A — Resource Pipeline + Graph View

**Status:** 🔄 Active
**Cycle Goal:** Complete the full resource processing pipeline (unauthenticated fetch + LLM worker) and knowledge graph backend + integration tests, then run a combined DEMO-003/004
**Started:** 2026-03-21
**Completed:** (pending)

### Notes

- DEV-021 (authenticated URL fetcher) deferred — DEV-023 uses unauthenticated fetch only
- LLM calls to be mocked in unit tests and integration tests

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| DEV-025 | Graph service (Neo4j operations) | ✅ Completed (PR #90) |
| DEV-023 | process_resource job (unauthenticated fetch only) | ✅ Completed (PR #92) |
| DEV-030 | GET /graph/nodes/{id}/resources | 🔄 Active |
| DEV-027 | Graph sync job for resource deletion | ⏳ Pending (needs DEV-025) |
| DEV-028 | GET /graph | ⏳ Pending (needs DEV-025) |
| DEV-029 | POST /graph/expand | ⏳ Pending (needs DEV-025) |
| DEV-026 | Graph update in worker pipeline | ⏳ Pending (needs DEV-023 + DEV-025) |
| DEV-024 | Unit tests — Worker | ⏳ Pending (needs DEV-023) |
| DEV-031 | Unit tests — Graph API | ⏳ Pending (needs DEV-028+029+030) |
| INT-024–028 | Worker integration tests | ⏳ Pending (needs DEV-023) |
| INT-029–035 | Graph integration tests | ⏳ Pending (needs DEV-025–030) |
| DEMO-003+004 | Combined pipeline + graph demo | ⏳ Pending (all above) |
