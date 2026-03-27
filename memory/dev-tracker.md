# Dev Tracker

**Plan:** exec-plans/v2/dev-plan.md
**Sprint:** Tier 3 — Feature Complete
**Goal:** Complete remaining backend APIs (resource CRUD, worker pipeline, graph, chat), wire graph/chat UI to live APIs
**Initialized:** 2026-03-14
**Last Updated:** 2026-03-27 (v2.2 plan update — DEV-066–071 added)

---

## Progress Summary

- Total: 138 tasks (71 DEV + 6 DEMO + 1 INT-framework + 55 INT-BDD + 5 OPS [tracked separately])
- ✅ Completed: 92
- 🔄 Active: 0
- ⏳ Pending: 46
- ⚠️ Stuck: 0

---

## 🔴 Tier 1 — Foundation

- [x] DEV-001: Initialize monorepo and project structure — Scaffold monorepo, apps (api + web) (PR #1 ✅)
- [x] DEV-004: Set up environment variable configuration — Pydantic Settings, .env.example, production validator (PR #2 ✅)
- [x] DEV-002: Configure PostgreSQL schema and migrations — Users, resources, accounts data layer via Alembic (PR #7 ✅)
- [x] DEV-003: Configure Neo4j connection and schema setup — Graph driver connection + uniqueness constraints (PR #8 ✅)
- [x] DEV-012: Implement Pydantic models for resources — Shared request/response models for resource endpoints (PR #10 ✅)
- [x] DEV-037: Implement health check endpoint — GET /health returns 200; used by CI and k8s probes (PR #11 ✅)
- [x] DEV-038: Implement standard error handling — Consistent error format before any endpoint returns errors (PR #12 ✅)

## 🔴 Tier 2 — MVP Core

- [x] DEV-005: Implement OAuth login flow (multi-provider) — Unblocks all protected routes (PR #13 ✅)
- [x] DEV-006: Implement auth middleware / dependency — get_current_user for protected endpoints (PR #16 ✅)
- [x] DEV-009: Implement GET /auth/me endpoint — Frontend needs logged-in state (PR #17 ✅)
- [x] DEV-010: Implement POST /auth/logout — Complete auth lifecycle (PR #18 ✅)
- [x] DEV-013: Implement POST /resources (create) — Core first user journey: submit a resource (PR #20 ✅)
- [x] DEV-014: Implement GET /resources (list) with filters — View resources after submitting (PR #26 ✅)
- [x] DEV-039: Implement OAuth login UI (multi-provider) — User-facing login page (PR #25 ✅)
- [x] DEV-041: Implement resource submission form — User-facing resource submit UI (PR #28 ✅)
- [x] DEV-042: Implement resource list view — View resources and processing status (PR #29 ✅)

## 🟡 Tier 3 — Feature Complete

- [x] DEV-007: Implement account linking flow — Unlocks multi-account + authenticated URL fetching (PR #45 ✅)
- [x] DEV-008: Implement account unlinking — Completes account management (PR #47 ✅)
- [x] DEV-015: Implement GET /resources/{id} (single) — Resource detail view (PR #50 ✅)
- [x] DEV-019: Implement task queue infrastructure — Async resource processing (PR #52 ✅)
- [x] DEV-020: Implement URL content fetcher (unauthenticated) — Worker fetch URL content (PR #54 ✅)
- [x] DEV-022: Implement LLM processing (title, summary, tags) — Core value: auto-summarize and tag (PR #56 ✅)
- [x] DEV-016: Implement PATCH /resources/{id} (update) — Users edit resources (PR #50 ✅)
- [x] DEV-017: Implement DELETE /resources/{id} — Users delete resources (PR #50 ✅)
- [ ] DEV-021: Implement authenticated URL fetcher (provider API) — Fetch from login-required sites
- [x] DEV-023: Implement process_resource job (full pipeline) — Ties fetch + LLM + DB update (PR #92 ✅)
- [x] DEV-025: Implement graph service (Neo4j operations) — Foundation for all graph features (PR #90 ✅)
- [x] DEV-026: Integrate graph update into worker pipeline — Resources update graph on processing (PR #97 ✅)
- [x] DEV-027: Implement graph sync job for resource deletion — Graph consistency on deletion (PR #103 ✅)
- [x] DEV-028: Implement GET /graph (graph view) — Core graph exploration API (PR #99 ✅)
- [x] DEV-029: Implement POST /graph/expand — Graph drill-down (PR #101 ✅)
- [x] DEV-030: Implement GET /graph/nodes/{node_id}/resources — Resources by tag from graph (PR #94 ✅)
- [x] DEV-035: Implement conversation storage (DB schema) — Chat persistence (PR #117 ✅)
- [x] DEV-032: Implement LangGraph agent with tools — Core chat intelligence (PR #119 ✅)
- [ ] DEV-033: Implement POST /chat endpoint — Chat API
- [ ] DEV-034: Implement GET /chat/conversations and messages — Chat history
- [x] DEV-040: Implement Settings — Account Management UI — Manage linked accounts UI (PR #59 ✅)
- [x] DEV-043: Implement resource detail / edit / delete — Full resource management UI (PR #58 ✅)
- [x] DEV-044: Implement graph visualization component — react-force-graph-2d UI shell (PR #40, #41 ✅)
- [x] DEV-045: Implement resource panel on node click — node detail dialog UI shell (PR #40 ✅)
- [x] DEV-046: Implement chat UI — chat panel UI shell with scroll fixes (PR #40, #41 ✅)
- [x] DEV-052: Wire graph visualization to real API — connect existing UI to GET /graph, POST /graph/expand, GET /graph/nodes/{id}/resources (PR #105 ✅)
- [ ] DEV-053: Wire chat UI to real API — connect existing chat panel to POST /chat, GET /chat/conversations
- [x] DEV-024: Unit tests — Worker / Resource Processing — Verify worker pipeline (PR #108 ✅)
- [x] DEV-031: Unit tests — Knowledge Graph API — Verify graph endpoints (PR #110 ✅)
- [ ] DEV-036: Unit tests — Chat / Agent — Verify chat
- [ ] DEV-011: Unit tests — Authentication — Verify full auth (blocked by DEV-007, DEV-008)
- [ ] DEV-018: Unit tests — Resource API — Verify resource CRUD (blocked by DEV-015, DEV-016, DEV-017)
- [x] DEV-054: Duplicate URL detection with user-facing notification — 409 on duplicate submit + "already added" toast (PR #64 ✅)
- [ ] DEV-055: Dashboard statistics panel — in-processing count, total added, categories identified, category rankings

## Feedback Implementation (FB-001 – FB-005)

_Design specs: `docs/design-resource-fetching.md` (FB-001), `docs/design-category-taxonomy.md` (FB-003/004)_

- [x] DEV-056: Tiered URL fetch strategy (PR #135 ✅) — domain blocklist + HTTP + Playwright fallback + fetch_tier/fetch_error_type tracking (FB-001)
- [x] DEV-057: Add processing_status field to resources + Alembic migration (pending/processing/success/failed) (FB-002) (PR #137 ✅)
- [x] DEV-058: Update worker pipeline to use processing_status state machine — skip success/failed, set state on start/complete (FB-002) (PR #140 ✅)
- [x] DEV-059: Add manual Re-process action to resource detail UI — POST /resources/{id}/reprocess endpoint + button (FB-002) (PR #141 ✅)
- [x] DEV-060: Implement categories table, seed 10 root categories, GET/POST/DELETE /categories endpoints (FB-003) (PR #143 ✅)
- [x] DEV-061: Update Neo4j schema to Root/Category/Tag three-level hierarchy + CHILD_OF/BELONGS_TO relationships + graph service update (FB-003) (PR #147 ✅)
- [x] DEV-062: Update LLM prompt to include existing tags + require top_level_categories in output; add CATEGORY_REQUIRED/INVALID_CATEGORY validation (FB-003) (PR #149 ✅)
- [x] DEV-063: Category management UI in Settings — list system + user categories, add/delete user categories (FB-003) (PR #152 ✅)
- [x] DEV-064: Tag editor component in resource detail UI — add/remove tag chips, save triggers graph resync (FB-004) (PR #154 ✅)
- [x] DEV-065: Fix graph node popup overflow — max-width/height, remove summary, truncate title, URL link + tag chips only (FB-005) (PR #145 ✅)

## 🟢 Tier 4 — Hardening

- [ ] DEV-047: Create backend Dockerfile — Required for Railway deployment (scope narrowed: frontend uses Vercel native build, no Dockerfile needed)
- [ ] ~~DEV-048~~: ~~Create Helm chart~~ — DEFERRED: k8s deployment replaced by Vercel+Railway cheap cloud stack (v2.2)
- [ ] ~~DEV-049~~: ~~Configure ArgoCD application~~ — DEFERRED: k8s deployment replaced by Vercel+Railway cheap cloud stack (v2.2)
- [ ] DEV-050: Integration test — Auth end-to-end — Full auth flow with real DB
- [ ] DEV-051: Integration test — Resource pipeline end-to-end — Full create-to-graph flow

## 🛠️ Integration Test Framework

- [x] INT-000: Build integration test framework — Python mocks, pytest fixtures, MSW frontend mocks, CI infra, Playwright E2E (PRs #67 #68 #69 #73 #74 ✅)

## 🧪 Integration Tests (INT-001 – INT-055)

_One test per BDD scenario. Design: `docs/integration-test-design.md`. Framework: INT-000 ✅_

> **CI groups**: `auth,resources` — every PR | `worker,graph,chat` — nightly | `web` — frontend PRs | `deploy` — release only

### Layer 1 — API Integration (pytest + real DB, mocked externals)

**Group: health** — CI: every PR
- [x] INT-001: Health check returns OK — GET /health → 200 (BDD: API Health) (PR #79 ✅)
- [x] INT-002: API returns standard error format — error response schema (BDD: API Errors) (PR #79 ✅)

**Group: auth** — CI: every PR
- [x] INT-003: User logs in with Twitter for the first time — creates user + account row (BDD: OAuth Login) (PR #79 ✅)
- [x] INT-004: User logs in with an existing linked account — returns existing user (BDD: OAuth Login) (PR #79 ✅)
- [x] INT-005: User logs in with Google (second provider, same user) (BDD: OAuth Login) (PR #79 ✅)
- [x] INT-006: Unauthenticated user is redirected to login — 401 on protected endpoint (BDD: OAuth Login) (PR #79 ✅)
- [x] INT-007: Session/JWT validated on each request — expired token returns 401 (BDD: OAuth Login) (PR #79 ✅)
- [x] INT-008: User links an additional social account — new user_accounts row (BDD: Account Linking) (PR #79 ✅)
- [x] INT-009: Link attempt when account already linked to another user — 409 (BDD: Account Linking) (PR #79 ✅)
- [x] INT-010: User unlinks a social account — account row deleted (BDD: Account Linking) (PR #79 ✅)
- [x] INT-011: User cannot unlink their last account — 400 CANNOT_UNLINK_LAST_ACCOUNT (BDD: Account Linking) (PR #79 ✅)
- [x] INT-012: GET /auth/me returns profile + linked accounts (BDD: Current User) (PR #79 ✅)

**Group: resources** — CI: every PR
- [x] INT-013: Authenticated user submits a URL resource — 202 + PENDING/PROCESSING (BDD: Resource Create) (PR #84 ✅)
- [x] INT-014: Authenticated user submits a text resource — 202 (BDD: Resource Create) (PR #84 ✅)
- [x] INT-015: Unauthenticated user cannot create resource — 401 (BDD: Resource Create) (PR #84 ✅)
- [x] INT-016: User submits URL with prefer_provider hint — stored on resource (BDD: Resource Create) (PR #84 ✅)
- [x] INT-017: User lists their resources — paginated, own resources only (BDD: Resource Read) (PR #84 ✅)
- [x] INT-018: User filters resources by tag (BDD: Resource Read) (PR #84 ✅)
- [x] INT-019: User filters resources by status (BDD: Resource Read) (PR #84 ✅)
- [x] INT-020: User views a single resource — full details (BDD: Resource Read) (PR #84 ✅)
- [x] INT-021: User updates a resource title — updated_at changes (BDD: Resource Update) (PR #84 ✅)
- [x] INT-022: User updates original_content — triggers PROCESSING + new job (BDD: Resource Update) (PR #84 ✅)
- [x] INT-023: User deletes a resource — removed + graph sync enqueued (BDD: Resource Delete) (PR #84 ✅)

**Group: worker** — CI: nightly
- [x] INT-024: Worker processes URL resource successfully — READY + graph updated (BDD: Async Worker) (PR #112 ✅)
- [x] INT-025: Worker processes text resource successfully — LLM title/summary/tags (BDD: Async Worker) (PR #112 ✅)
- [x] INT-026: URL requires login, user has linked account — provider fetch succeeds (BDD: Async Worker) (PR #112 ✅)
- [x] INT-027: URL requires login, user has no linked account — FAILED + status_message (BDD: Async Worker) (PR #112 ✅)
- [x] INT-028: LLM processing fails — FAILED + status_message (BDD: Async Worker) (PR #112 ✅)

**Group: graph** — CI: nightly
- [x] INT-029: Graph updated after resource processed — Tag nodes + RELATED_TO edges created (BDD: Graph Update) (PR #113 ✅)
- [x] INT-030: Graph updated after resource deletion — edge weights decremented (BDD: Graph Update) (PR #113 ✅)
- [x] INT-031: Graph updated after resource re-processing — old tags removed, new applied (BDD: Graph Update) (PR #113 ✅)
- [x] INT-032: User views root graph — nodes + edges for personal graph (BDD: Graph Exploration) (PR #113 ✅)
- [x] INT-033: User views graph centered on specific tag (BDD: Graph Exploration) (PR #113 ✅)
- [x] INT-034: User expands a graph node (BDD: Graph Exploration) (PR #113 ✅)
- [x] INT-035: User views resources for a graph node (BDD: Graph Exploration) (PR #113 ✅)

**Group: chat** — CI: nightly (blocked: DEV-032–035)
- [ ] INT-036: User sends a chat message — agent returns answer + conversation_id (BDD: Chat Agent) (blocked: DEV-032, DEV-033, DEV-035)
- [ ] INT-037: User continues a conversation with context (BDD: Chat Agent) (blocked: DEV-032, DEV-033, DEV-035)
- [ ] INT-038: Agent uses graph traversal tool (BDD: Chat Agent) (blocked: DEV-032)
- [ ] INT-039: User lists their conversations (BDD: Chat Agent) (blocked: DEV-034)
- [ ] INT-040: User retrieves messages in a conversation (BDD: Chat Agent) (blocked: DEV-034)

### Layer 2 — Frontend Integration (Jest + MSW, no backend)

**Group: web** — CI: frontend PRs
- [ ] INT-041: User sees resource submission form (BDD: Frontend Resource UI) (ready ✅)
- [ ] INT-042: Resource shows processing status indicator (BDD: Frontend Resource UI) (ready ✅)
- [ ] INT-043: Resource shows FAILED status with actionable message (BDD: Frontend Resource UI) (ready ✅)
- [ ] INT-044: User browses resource list (BDD: Frontend Resource UI) (ready ✅)
- [ ] INT-045: User views the knowledge graph — force-directed render (BDD: Frontend Graph) (blocked: DEV-052)
- [ ] INT-046: User clicks a node to expand — graph expands (BDD: Frontend Graph) (blocked: DEV-052)
- [ ] INT-047: User clicks a node to see resources — panel shown (BDD: Frontend Graph) (blocked: DEV-052)
- [ ] INT-048: User opens the chat interface — panel slides open (BDD: Frontend Chat) (blocked: DEV-053)
- [ ] INT-049: User sends a message and receives a response (BDD: Frontend Chat) (blocked: DEV-053)
- [ ] INT-050: User views linked accounts in settings (BDD: Frontend Settings) (ready ✅)
- [ ] INT-051: User adds a new linked account from settings (BDD: Frontend Settings) (ready ✅)
- [ ] INT-052: User sees error when unlinking last account (BDD: Frontend Settings) (ready ✅)

### Layer 3 — E2E Deployment (k8s smoke tests)

**Group: deploy** — CI: release only (blocked: DEV-047–049)
- [ ] INT-053: Docker images build successfully (BDD: Deployment) (blocked: DEV-047)
- [ ] INT-054: Helm chart deploys to Kubernetes (BDD: Deployment) (blocked: DEV-048)
- [ ] INT-055: ArgoCD syncs from Git (BDD: Deployment) (blocked: DEV-049)

## 🚀 Deploy Prioritization (v2.2 — 2026-03-27)

_Goal: ship to production for feedback. Auth hardening + feature gates + multi-LLM + cheap cloud stack._

- [ ] DEV-066: Restrict login UI to Google-only — remove X/Twitter button + username/password form from login page
- [ ] DEV-067: Disable search button — add disabled state + "Search coming soon" tooltip
- [ ] DEV-068: Chat panel "coming soon" mode — disable input/send, inject initial bot message
- [ ] DEV-069: User allowlisting backend — ALLOWED_EMAILS env var gate on OAuth callback → redirect /coming-soon
- [ ] DEV-070: Coming-soon page — static /coming-soon page for non-allowlisted users
- [ ] DEV-071: Multi-LLM provider abstraction — LLM_PROVIDER env var; support Groq/SiliconFlow/Fireworks + Anthropic

## 🎬 Demos

- [x] DEMO-001: First User Journey — login → submit resource → see list (run-2 ✅)
- [x] DEMO-002: Account Management & Resource CRUD — settings, detail, edit, delete (run-1 ✅)
- [x] DEMO-003: Resource Processing Pipeline — submit URL → LLM summary + tags (run-1 ✅)
- [x] DEMO-004: Knowledge Graph Exploration — live graph, expand nodes, resource panel (run-1 ✅)
- [ ] DEMO-005: AI Chat — LangGraph agent answers questions about saved resources (blocked: DEV-032, DEV-033, DEV-034, DEV-035, DEV-053 pending)
- [ ] DEMO-006: Feedback Verification — verify FB-001 to FB-005: tiered fetch, processing_status, category taxonomy, tag editor, node popup fix (blocked: DEV-056–DEV-065)
