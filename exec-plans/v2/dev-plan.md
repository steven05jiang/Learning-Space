# Development Plan — Learning Space

_Version: v2 | Generated: 2026-03-17_

## Overview

Learning Space is a personal knowledge management tool that lets users save URLs and text, auto-summarizes them via LLM, and visualises their personal knowledge graph. The delivery philosophy is thin vertical slices over horizontal layers — ship a working loop as early as possible.

**v2 context:** Three frontend UI shells (knowledge graph, resource panel, chat) were built ahead of schedule via UI-001/UI-002 using `react-force-graph-2d` and mock data. The plan reflects this reality — DEV-044, DEV-045, DEV-046 are marked complete. Two new API wiring tasks (DEV-052, DEV-053) replace them in the work queue.

**Tooling constraint:** Web CI uses direct `eslint` invocation rather than `next lint` (Next.js 16 incompatibility with ESLint 9 — ESLint downgraded to 8.57.1 in PR #40).

---

## Priority Tiers

### 🔴 Tier 1 — Foundation ✅ COMPLETE

All prerequisites are in place.

| Priority | Task                                                 | Type    | Effort | Status    |
| -------- | ---------------------------------------------------- | ------- | ------ | --------- |
| 1        | DEV-001: Initialize monorepo and project structure   | Infra   | M      | ✅ PR #1  |
| 2        | DEV-004: Set up environment variable configuration   | Infra   | S      | ✅ PR #2  |
| 3        | DEV-002: Configure PostgreSQL schema and migrations  | DB      | M      | ✅ PR #7  |
| 4        | DEV-003: Configure Neo4j connection and schema setup | DB      | S      | ✅ PR #8  |
| 5        | DEV-012: Implement Pydantic models for resources     | Backend | S      | ✅ PR #10 |
| 6        | DEV-037: Implement health check endpoint             | Backend | XS     | ✅ PR #11 |
| 7        | DEV-038: Implement standard error handling           | Backend | S      | ✅ PR #12 |

**Tier 1 exit gate:** ✅ Health check returns 200, DB migrations apply cleanly, all env vars load, CI passes.

---

### 🟠 Tier 2 — MVP Core ✅ COMPLETE

First user journey is working end-to-end.

| Priority | Task                                                  | Type     | Effort | Status                           |
| -------- | ----------------------------------------------------- | -------- | ------ | -------------------------------- |
| 1        | DEV-005: Implement OAuth login flow (multi-provider)  | Backend  | L      | ✅ PR #13                        |
| 2        | DEV-006: Implement auth middleware / dependency       | Backend  | S      | ✅ PR #16                        |
| 3        | DEV-009: Implement GET /auth/me endpoint              | Backend  | S      | ✅ PR #17                        |
| 4        | DEV-010: Implement POST /auth/logout                  | Backend  | S      | ✅ PR #18                        |
| 5        | DEV-013: Implement POST /resources (create)           | Backend  | M      | ✅ PR #20                        |
| 6        | DEV-014: Implement GET /resources (list) with filters | Backend  | S      | ✅ PR #26                        |
| 7        | DEV-039: Implement OAuth login UI (multi-provider)    | Frontend | M      | ✅ PR #25 + #40                  |
| 8        | DEV-041: Implement resource submission form           | Frontend | M      | ✅ PR #28                        |
| 9        | DEV-042: Implement resource list view                 | Frontend | L      | ✅ PR #29                        |
| 10       | DEV-011: Unit tests — Authentication                  | Testing  | M      | ⏳ (blocked by DEV-007, DEV-008) |
| 11       | DEV-018: Unit tests — Resource API                    | Testing  | M      | ⏳ (blocked by DEV-015–017)      |

**Tier 2 exit gate:** ✅ Core journey working — user can log in (Google or X), submit a URL, and see it appear in the resource list. Auth and resource list fully functional with real data.

> **Note:** DEV-011 and DEV-018 remain pending because they depend on account linking (DEV-007/008) and full resource CRUD (DEV-015–017) which are Tier 3 tasks. They are listed here as aspirational Tier 2 completions.

---

### 🟡 Tier 3 — Feature Complete

All remaining functional scope, ordered by dependency then value then risk.

#### Pre-built Frontend Components (completed ahead of schedule via UI-001/UI-002)

These components were built with mock data before their backend APIs existed. They are **complete** from a UI perspective; the remaining work is API wiring (DEV-052, DEV-053).

| Task                                                | Type     | Status       | Remaining            |
| --------------------------------------------------- | -------- | ------------ | -------------------- |
| DEV-044: Graph visualization (react-force-graph-2d) | Frontend | ✅ PR #40+41 | API wiring → DEV-052 |
| DEV-045: Resource panel on node click               | Frontend | ✅ PR #40    | API wiring → DEV-052 |
| DEV-046: Chat UI (Sparkles toggle, scroll fixes)    | Frontend | ✅ PR #40+41 | API wiring → DEV-053 |

#### Active Tier 3 Tasks

| Priority | Task                                                | Type     | Effort | Depends On                                        | Rationale                                        |
| -------- | --------------------------------------------------- | -------- | ------ | ------------------------------------------------- | ------------------------------------------------ |
| 1        | DEV-007: Implement account linking flow             | Backend  | M      | DEV-005 ✅, DEV-006 ✅                            | Unlocks authenticated URL fetching + Settings UI |
| 2        | DEV-008: Implement account unlinking                | Backend  | S      | DEV-006 ✅                                        | Completes account management                     |
| 3        | DEV-015: Implement GET /resources/{id}              | Backend  | S      | DEV-006 ✅, DEV-012 ✅                            | Unblocks resource detail UI                      |
| 4        | DEV-019: Implement task queue infrastructure        | Backend  | M      | DEV-001 ✅, DEV-004 ✅                            | Prerequisite for all worker tasks                |
| 5        | DEV-020: Implement URL content fetcher              | Backend  | S      | DEV-001 ✅                                        | Worker fetch foundation                          |
| 6        | DEV-022: Implement LLM processing                   | Backend  | M      | DEV-004 ✅                                        | Core value: auto-summarize and tag               |
| 7        | DEV-016: Implement PATCH /resources/{id}            | Backend  | M      | DEV-006 ✅, DEV-012 ✅                            | Resource editing                                 |
| 8        | DEV-017: Implement DELETE /resources/{id}           | Backend  | S      | DEV-006 ✅, DEV-012 ✅                            | Resource deletion                                |
| 9        | DEV-021: Implement authenticated URL fetcher        | Backend  | L      | DEV-020, DEV-002 ✅                               | Twitter/X content fetching                       |
| 10       | DEV-023: Implement process_resource job             | Backend  | M      | DEV-019, DEV-020, DEV-021, DEV-022                | Full processing pipeline                         |
| 11       | DEV-025: Implement graph service (Neo4j ops)        | Backend  | L      | DEV-003 ✅                                        | Foundation for all graph features                |
| 12       | DEV-026: Integrate graph update into worker         | Backend  | S      | DEV-025, DEV-023                                  | Resources update graph on processing             |
| 13       | DEV-027: Graph sync job for resource deletion       | Backend  | S      | DEV-025, DEV-019                                  | Graph consistency on deletion                    |
| 14       | DEV-028: Implement GET /graph                       | Backend  | M      | DEV-025, DEV-006 ✅                               | Core graph exploration API                       |
| 15       | DEV-029: Implement POST /graph/expand               | Backend  | S      | DEV-025, DEV-006 ✅                               | Graph drill-down                                 |
| 16       | DEV-030: Implement GET /graph/nodes/{id}/resources  | Backend  | S      | DEV-006 ✅, DEV-012 ✅                            | Resources by tag from graph                      |
| 17       | DEV-035: Implement conversation storage (DB schema) | DB       | S      | DEV-002 ✅                                        | Chat persistence prerequisite                    |
| 18       | DEV-032: Implement LangGraph agent with tools       | Backend  | L      | DEV-014 ✅, DEV-025, DEV-004 ✅                   | Core chat intelligence                           |
| 19       | DEV-033: Implement POST /chat endpoint              | Backend  | M      | DEV-032, DEV-006 ✅                               | Chat API                                         |
| 20       | DEV-034: GET /chat/conversations and messages       | Backend  | S      | DEV-033                                           | Chat history                                     |
| 21       | DEV-040: Settings — Account Management UI           | Frontend | M      | DEV-039 ✅, DEV-009 ✅                            | Manage linked accounts                           |
| 22       | DEV-043: Resource detail / edit / delete UI         | Frontend | M      | DEV-015, DEV-016, DEV-017                         | Full resource management UI                      |
| 23       | DEV-052: Wire graph visualization to real API       | Frontend | M      | DEV-028, DEV-029, DEV-030, DEV-044 ✅, DEV-045 ✅ | Connect existing graph UI to backend             |
| 24       | DEV-053: Wire chat UI to real API                   | Frontend | S      | DEV-033, DEV-034, DEV-046 ✅                      | Connect existing chat UI to backend              |
| 25       | DEV-024: Unit tests — Worker / Resource Processing  | Testing  | M      | DEV-023                                           | Verify worker pipeline                           |
| 26       | DEV-031: Unit tests — Knowledge Graph API           | Testing  | M      | DEV-028, DEV-029, DEV-030                         | Verify graph endpoints                           |
| 27       | DEV-036: Unit tests — Chat / Agent                  | Testing  | M      | DEV-033, DEV-034                                  | Verify chat                                      |
| 28       | DEV-011: Unit tests — Authentication                | Testing  | M      | DEV-007, DEV-008                                  | Verify full auth                                 |
| 29       | DEV-018: Unit tests — Resource API                  | Testing  | M      | DEV-015, DEV-016, DEV-017                         | Verify resource CRUD                             |

#### Feedback Implementation (FB-001 – FB-005, 2026-03-22)

_Addresses all open feedback items. Design specs: `docs/design-resource-fetching.md`, `docs/design-category-taxonomy.md`._

| Priority | Task                                                         | Type     | Effort | Depends On                    | Feedback |
| -------- | ------------------------------------------------------------ | -------- | ------ | ----------------------------- | -------- |
| 30       | DEV-056: Implement tiered URL fetch strategy                 | Backend  | L      | DEV-020 ✅, DEV-023 ✅        | FB-001   |
| 31       | DEV-057: Add processing_status field + migration             | Backend  | S      | DEV-002 ✅                    | FB-002   |
| 32       | DEV-058: Update worker to use processing_status state machine | Backend  | S      | DEV-057, DEV-023 ✅           | FB-002   |
| 33       | DEV-059: Add manual Re-process action to resource detail UI  | Frontend | S      | DEV-057, DEV-043 ✅           | FB-002   |
| 34       | DEV-060: Implement categories table + seed + /categories API | Backend  | M      | DEV-002 ✅, DEV-006 ✅        | FB-003   |
| 35       | DEV-061: Update Neo4j schema to Root/Category/Tag hierarchy  | Backend  | M      | DEV-025 ✅, DEV-060           | FB-003   |
| 36       | DEV-062: Update LLM prompt for tag reuse + top_level_categories | Backend | S     | DEV-022 ✅, DEV-060           | FB-003   |
| 37       | DEV-063: Category management UI in Settings                  | Frontend | M      | DEV-060, DEV-040 ✅           | FB-003   |
| 38       | DEV-064: Tag editor component in resource detail UI          | Frontend | S      | DEV-043 ✅, DEV-061           | FB-004   |
| 39       | DEV-065: Fix graph node popup overflow                       | Frontend | XS     | DEV-052 ✅                    | FB-005   |

**Dependency graph (feedback tasks):**
- DEV-056 (independent)
- DEV-057 → DEV-058
- DEV-057 → DEV-059
- DEV-060 → DEV-061 → DEV-064
- DEV-060 → DEV-062
- DEV-060 → DEV-063
- DEV-065 (independent)

**Tier 3 exit gate:** All features working end-to-end with real data: account linking, authenticated URL fetching, resource processing pipeline, knowledge graph exploration, LangGraph chat agent responding to real questions. Graph UI and chat UI wired to live APIs (not mock data). All five open feedback items resolved.

---

### 🟢 Tier 4 — Hardening

| Priority | Task                                          | Type    | Effort | Rationale                   |
| -------- | --------------------------------------------- | ------- | ------ | --------------------------- |
| 1        | DEV-047: Create Dockerfiles                   | DevOps  | M      | Required for any deployment |
| 2        | DEV-048: Create Helm chart                    | DevOps  | L      | Kubernetes deployment       |
| 3        | DEV-049: Configure ArgoCD application         | DevOps  | S      | GitOps automation           |
| 4        | DEV-050: Integration test — Auth end-to-end   | Testing | M      | Full auth flow with real DB |
| 5        | DEV-051: Integration test — Resource pipeline | Testing | L      | Full create-to-graph flow   |

**Tier 4 exit gate:** Docker images build and run, Helm chart deploys to k8s, ArgoCD syncs from Git, integration tests green. Ready for beta users.

---

## Milestones

### Milestone 1 — Walking Skeleton ✅

**Completed by:** Tier 1 done
**DEV tasks:** DEV-001, DEV-002, DEV-003, DEV-004, DEV-012, DEV-037, DEV-038

**What a tester can do at this milestone:**

> I can clone the repo, run the backend locally, hit `GET /health` and get 200, and confirm the PostgreSQL schema and Neo4j constraints are applied. The CI pipeline runs lint and tests for both apps.

**What is NOT yet possible:** Any user-facing functionality (login, resources, chat).

---

### Milestone 2 — First User Journey ✅

**Completed by:** Tier 2 core tasks done (note: unit tests DEV-011 and DEV-018 will complete in Tier 3)
**DEV tasks:** DEV-005, DEV-006, DEV-009, DEV-010, DEV-013, DEV-014, DEV-039, DEV-041, DEV-042

**What a tester can do at this milestone:**

> I can open the app in a browser, log in with Google or X (Twitter), submit a URL or paste text, and see my resource appear in the list. The full auth-to-create-to-list loop works with real data persisted to the database.

**What is NOT yet possible:** Resource processing (no LLM summaries or tags yet), knowledge graph, chat, account linking, resource editing/deleting.

---

### Milestone 3 — Feature Complete

**Completed by:** Tier 3 done
**DEV tasks:** DEV-007, DEV-008, DEV-011, DEV-015–023, DEV-024–036, DEV-040, DEV-043, DEV-052, DEV-053

**What a tester can do at this milestone:**

> I can use all features: link my Twitter account in Settings to save Twitter content, submit URLs which auto-process into summaries and tags within seconds, browse my knowledge graph (real tags and edges from processed resources), click a graph node to see associated resources, chat with the AI assistant and ask it about my saved content. The graph and chat panels are live — not mock data.

**What is NOT yet possible:** Kubernetes deployment, ArgoCD GitOps, integration test suite.

---

### Milestone 4 — Production Ready

**Completed by:** Tier 4 done
**DEV tasks:** DEV-047, DEV-048, DEV-049, DEV-050, DEV-051

**What a tester can do at this milestone:**

> I can run `helm install` to deploy the full stack to Kubernetes. ArgoCD watches the repo and auto-syncs on image tag changes. The integration test suite verifies auth and resource pipeline end-to-end with real services. The system is ready for beta users.

---

## Coding Agent Execution Rules

1. **Never start a task before its dependencies are complete.** Check `dev-tasks-map.md` before each task.
2. **Complete each Tier's exit gate before advancing.** Exit gates are not optional.
3. **Within a tier, follow the priority order** unless a task is marked `[parallel-safe]`.
4. **`[parallel-safe]` tasks** within the same tier may be started concurrently if separate agents are available.
5. **When a task is unexpectedly blocked**, escalate immediately rather than skipping ahead.
6. **Test tasks belong to the same tier as the feature they test** — do not defer testing to a later tier.
7. **DEV-052 and DEV-053 must not start until their backend API dependencies are complete.** The UI shells exist; connecting them to broken or missing APIs will produce confusing failures.
8. **ESLint CI constraint:** Do not change the web lint CI step to use `next lint` — it is incompatible with Next.js 16. Use direct `eslint` invocation as established in PR #40.

---

## Risk & Assumptions Log

| #   | Risk / Assumption                                                                 | Tier Affected | Mitigation                                                                             |
| --- | --------------------------------------------------------------------------------- | ------------- | -------------------------------------------------------------------------------------- |
| 1   | LangGraph agent tool reliability — agent may hallucinate tool calls               | T3            | Comprehensive mocked unit tests; LangSmith tracing from day 1                          |
| 2   | Twitter/X API auth-required fetching may require OAuth 1.0a vs 2.0 handling       | T3            | DEV-021 should probe API requirements early; design for both                           |
| 3   | react-force-graph-2d canvas performance with large graphs                         | T3            | Confirmed working for prototype scale; revisit if >500 nodes                           |
| 4   | ESLint 8.57.1 pinned — may diverge from eslint-config-next over time              | T1            | Track Next.js ESLint 9 compatibility; upgrade when stable                              |
| 5   | DEV-044/045/046 built with mock data — API response shapes must match mock shapes | T3            | Define API response shapes in DEV-028/029/030/033/034 to match existing mock contracts |
| 6   | Graph data model (Neo4j) may need adjustment once real LLM tags are generated     | T3            | DEV-025 graph service should handle arbitrary tag strings; avoid hard-coded structures |
