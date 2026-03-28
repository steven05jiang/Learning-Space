# Sprints

Tracks each dev-cycle goal, selected tasks, and final outcome.
One entry per `/project-dispatch` invocation that reaches Phase 4.

---

## Sprint 2026-03-27-B — Cloud Deployment to Production

**Status:** ✅ Complete
**Sprint Goal:** Ship the app to cloud so it's accessible via internet with Google login working for allowlisted users
**Exit Gate:** OPS-006 — Production Google OAuth + allowlist smoke test passes ✅
**Started:** 2026-03-27
**Completed:** 2026-03-28

### Notes

- max-agents: 1 (sequential dispatch per MEMORY.md feedback)
- All OPS tasks were completed manually by user (Vercel dashboard, Google Cloud Console, environment config)
- OPS-005 (custom domain) deferred — current vercel.app domain is acceptable for now

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| OPS-003 | Backend Railway deployment (API + worker, Alembic migrations, auto-deploy) | ✅ Completed (PR #168) |
| OPS-004 | Frontend Vercel deployment (connect GitHub, env vars, confirm build) | ✅ Completed (manual, 2026-03-27) |
| OPS-005 | Domain + DNS (Namecheap + Cloudflare + custom domains on Vercel/Railway) | 🚫 Deferred (vercel.app domain works fine) |
| OPS-006 | Production Google OAuth + allowlist smoke test | ✅ Completed (manual, 2026-03-28) |

---

## Sprint 2026-03-27-A — Deploy Hardening + Cloud Provisioning

**Status:** ✅ Complete
**Sprint Goal:** Complete deploy-hardening dev tasks and provision cloud infrastructure so the app can be shipped to production on Vercel + Railway
**Exit Gate:** All DEV-066–071 + DEV-047 merged, OPS-002 provisioned → OPS-003 (Railway deployment) fully unblocked
**Started:** 2026-03-27
**Completed:** 2026-03-27

### Notes

- max-agents: 1 (sequential dispatch per MEMORY.md feedback)
- DEV-070 depends on DEV-069; dispatch after DEV-069 merges
- DEV-066–069, DEV-071, DEV-047 are all independently unblocked — dispatch in priority order
- OPS-002 is manual user work — instructions provided directly, no implementer dispatch

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| DEV-066 | Restrict login to Google-only (remove X button + email/password form) | ✅ Completed (PR #158) |
| DEV-067 | Disable search button + "coming soon" tooltip | ✅ Completed (PR #160) |
| DEV-068 | Chat panel "coming soon" mode (disable input, inject bot message) | ✅ Completed (PR #161) |
| DEV-069 | User allowlisting backend (ALLOWED_EMAILS env var gate) | ✅ Completed (PR #162) |
| DEV-071 | Multi-LLM provider abstraction (LLM_PROVIDER env var) | ✅ Completed (PR #164) |
| DEV-047 | Backend Dockerfile (API + worker services) | ✅ Completed (PR #165) |
| DEV-070 | Coming-soon page at /coming-soon — needs DEV-069 | ✅ Completed (PR #163) |
| OPS-002 | Provision cloud services (Supabase + Neo4j AuraDB + Upstash) | ✅ Completed (manual, 2026-03-27) |

---

## Sprint 2026-03-23-A — Feedback Implementation

**Status:** ✅ Complete
**Sprint Goal:** Implement all FB-001 through FB-005 feedback items so DEMO-006 (Feedback Verification) is runnable
**Exit Gate:** DEMO-006 — Feedback Verification demo executes successfully
**Started:** 2026-03-23
**Completed:** 2026-03-27

### Notes

- DEV-056 (tiered fetch) is the heaviest task (L) — includes Playwright headless browser in worker Docker image
- Layer 0 tasks are independently dispatchable; Layer 1 tasks unlock after their Layer 0 prereqs merge
- DEV-061 also updates INT-029–035 integration tests (Neo4j schema change)
- max-agents: 1 (sequential dispatch per MEMORY.md feedback)

### Tasks

| Task | Description | Status |
|------|-------------|--------|
| DEV-056 | Tiered URL fetch strategy (FB-001) | ✅ Completed (PR #135) |
| DEV-057 | processing_status field + Alembic migration (FB-002) | ✅ Completed (PR #137) |
| DEV-060 | Categories table, seed 10 root categories, /categories API (FB-003) | ✅ Completed (PR #143) |
| DEV-065 | Fix graph node popup overflow (FB-005) | ✅ Completed (PR #145) |
| DEV-058 | Worker pipeline state machine (FB-002) — needs DEV-057 | ✅ Completed (PR #140) |
| DEV-059 | Re-process action in resource detail UI (FB-002) — needs DEV-057 | ✅ Completed (PR #141) |
| DEV-061 | Neo4j Root/Category/Tag three-level hierarchy (FB-003) — needs DEV-060 | ✅ Completed (PR #147) |
| DEV-062 | LLM prompt: tag reuse + top_level_categories (FB-003) — needs DEV-060 | ✅ Completed (PR #149) |
| DEV-063 | Category management UI in Settings (FB-003) — needs DEV-060 | ✅ Completed (PR #152) |
| DEV-064 | Tag editor in resource detail UI (FB-004) — needs DEV-061 | ✅ Completed (PR #154) |
| DEMO-006 | Feedback Verification Demo — needs DEV-056–DEV-065 | ⏳ Deferred (user verified manually 2026-03-27) |

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
