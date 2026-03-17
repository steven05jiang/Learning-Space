# Dev Tracker

**Plan:** exec-plans/v2/dev-plan.md
**Sprint:** Tier 3 — Feature Complete
**Goal:** Complete remaining backend APIs (resource CRUD, worker pipeline, graph, chat), wire graph/chat UI to live APIs
**Initialized:** 2026-03-14
**Last Updated:** 2026-03-17

---

## Progress Summary

- Total: 58 tasks (53 DEV + 5 DEMO)
- ✅ Completed: 27
- 🔄 Active: 0
- ⏳ Pending: 31
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
- [ ] DEV-022: Implement LLM processing (title, summary, tags) — Core value: auto-summarize and tag
- [x] DEV-016: Implement PATCH /resources/{id} (update) — Users edit resources (PR #50 ✅)
- [x] DEV-017: Implement DELETE /resources/{id} — Users delete resources (PR #50 ✅)
- [ ] DEV-021: Implement authenticated URL fetcher (provider API) — Fetch from login-required sites
- [ ] DEV-023: Implement process_resource job (full pipeline) — Ties fetch + LLM + DB update
- [ ] DEV-025: Implement graph service (Neo4j operations) — Foundation for all graph features
- [ ] DEV-026: Integrate graph update into worker pipeline — Resources update graph on processing
- [ ] DEV-027: Implement graph sync job for resource deletion — Graph consistency on deletion
- [ ] DEV-028: Implement GET /graph (graph view) — Core graph exploration API
- [ ] DEV-029: Implement POST /graph/expand — Graph drill-down
- [ ] DEV-030: Implement GET /graph/nodes/{node_id}/resources — Resources by tag from graph
- [ ] DEV-035: Implement conversation storage (DB schema) — Chat persistence
- [ ] DEV-032: Implement LangGraph agent with tools — Core chat intelligence
- [ ] DEV-033: Implement POST /chat endpoint — Chat API
- [ ] DEV-034: Implement GET /chat/conversations and messages — Chat history
- [ ] DEV-040: Implement Settings — Account Management UI — Manage linked accounts UI
- [ ] DEV-043: Implement resource detail / edit / delete — Full resource management UI
- [x] DEV-044: Implement graph visualization component — react-force-graph-2d UI shell (PR #40, #41 ✅)
- [x] DEV-045: Implement resource panel on node click — node detail dialog UI shell (PR #40 ✅)
- [x] DEV-046: Implement chat UI — chat panel UI shell with scroll fixes (PR #40, #41 ✅)
- [ ] DEV-052: Wire graph visualization to real API — connect existing UI to GET /graph, POST /graph/expand, GET /graph/nodes/{id}/resources
- [ ] DEV-053: Wire chat UI to real API — connect existing chat panel to POST /chat, GET /chat/conversations
- [ ] DEV-024: Unit tests — Worker / Resource Processing — Verify worker pipeline
- [ ] DEV-031: Unit tests — Knowledge Graph API — Verify graph endpoints
- [ ] DEV-036: Unit tests — Chat / Agent — Verify chat
- [ ] DEV-011: Unit tests — Authentication — Verify full auth (blocked by DEV-007, DEV-008)
- [ ] DEV-018: Unit tests — Resource API — Verify resource CRUD (blocked by DEV-015, DEV-016, DEV-017)

## 🟢 Tier 4 — Hardening

- [ ] DEV-047: Create Dockerfiles for frontend and backend — Required for any deployment
- [ ] DEV-048: Create Helm chart — Kubernetes deployment
- [ ] DEV-049: Configure ArgoCD application — GitOps automation
- [ ] DEV-050: Integration test — Auth end-to-end — Full auth flow with real DB
- [ ] DEV-051: Integration test — Resource pipeline end-to-end — Full create-to-graph flow

## 🎬 Demos

- [x] DEMO-001: First User Journey — login → submit resource → see list (run-2 ✅)
- [ ] DEMO-002: Account Management & Resource CRUD — settings, detail, edit, delete (blocked: DEV-040, DEV-043 pending)
- [ ] DEMO-003: Resource Processing Pipeline — submit URL → LLM summary + tags (blocked: DEV-022, DEV-023 pending)
- [ ] DEMO-004: Knowledge Graph Exploration — live graph, expand nodes, resource panel (blocked: DEV-025, DEV-026, DEV-028, DEV-029, DEV-030, DEV-052 pending)
- [ ] DEMO-005: AI Chat — LangGraph agent answers questions about saved resources (blocked: DEV-032, DEV-033, DEV-034, DEV-035, DEV-053 pending)
