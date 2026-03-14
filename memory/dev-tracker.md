# Dev Tracker

**Plan:** exec-plans/v1/dev-plan.md
**Sprint:** Tier 1 — Foundation
**Goal:** Stand up the walking skeleton: monorepo structure, PostgreSQL + Neo4j schemas, health endpoint, error handling, and Pydantic models
**Initialized:** 2026-03-14
**Last Updated:** 2026-03-14

---

## Progress Summary
- Total: 51 tasks
- ✅ Completed: 0
- 🔄 Active: 1
- ⏳ Pending: 50
- ⚠️ Stuck: 0

---

## 🔴 Tier 1 — Foundation

- [~] DEV-001: Initialize monorepo and project structure — Scaffold monorepo, apps (api + web), CI pipeline
- [ ] DEV-004: Set up environment variable configuration — All services need config before connecting to anything
- [ ] DEV-002: Configure PostgreSQL schema and migrations — Users, resources, accounts data layer via Alembic
- [ ] DEV-003: Configure Neo4j connection and schema setup — Graph driver connection + uniqueness constraints
- [ ] DEV-012: Implement Pydantic models for resources — Shared request/response models for resource endpoints
- [ ] DEV-037: Implement health check endpoint — GET /health returns 200; used by CI and k8s probes
- [ ] DEV-038: Implement standard error handling — Consistent error format before any endpoint returns errors

## 🔴 Tier 2 — MVP Core

- [ ] DEV-005: Implement OAuth login flow (multi-provider) — Unblocks all protected routes
- [ ] DEV-006: Implement auth middleware / dependency — get_current_user for protected endpoints
- [ ] DEV-009: Implement GET /auth/me endpoint — Frontend needs logged-in state
- [ ] DEV-010: Implement POST /auth/logout — Complete auth lifecycle
- [ ] DEV-013: Implement POST /resources (create) — Core first user journey: submit a resource
- [ ] DEV-014: Implement GET /resources (list) with filters — View resources after submitting
- [ ] DEV-015: Implement GET /resources/{id} (single) — Resource detail view
- [ ] DEV-019: Implement task queue infrastructure — Async resource processing
- [ ] DEV-020: Implement URL content fetcher (unauthenticated) — Worker fetch URL content
- [ ] DEV-022: Implement LLM processing (title, summary, tags) — Core value: auto-summarize and tag
- [ ] DEV-023: Implement process_resource job (full pipeline) — Ties fetch + LLM + DB update
- [ ] DEV-039: Implement OAuth login UI (multi-provider) — User-facing login page
- [ ] DEV-041: Implement resource submission form — User-facing resource submit UI
- [ ] DEV-042: Implement resource list view — View resources and processing status
- [ ] DEV-011: Unit tests — Authentication — Verify auth works before building on it
- [ ] DEV-018: Unit tests — Resource API — Verify resource CRUD works

## 🟡 Tier 3 — Feature Complete

- [ ] DEV-007: Implement account linking flow — Unlocks multi-account + authenticated URL fetching
- [ ] DEV-008: Implement account unlinking — Completes account management
- [ ] DEV-021: Implement authenticated URL fetcher (provider API) — Fetch from login-required sites
- [ ] DEV-016: Implement PATCH /resources/{id} (update) — Users edit resources
- [ ] DEV-017: Implement DELETE /resources/{id} — Users delete resources
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
- [ ] DEV-044: Implement graph visualization component — Core graph UI
- [ ] DEV-045: Implement resource panel on node click — Discover resources from graph
- [ ] DEV-046: Implement chat UI — Chat interface
- [ ] DEV-024: Unit tests — Worker / Resource Processing — Verify worker pipeline
- [ ] DEV-031: Unit tests — Knowledge Graph API — Verify graph endpoints
- [ ] DEV-036: Unit tests — Chat / Agent — Verify chat

## 🟢 Tier 4 — Hardening

- [ ] DEV-047: Create Dockerfiles for frontend and backend — Required for any deployment
- [ ] DEV-048: Create Helm chart — Kubernetes deployment
- [ ] DEV-049: Configure ArgoCD application — GitOps automation
- [ ] DEV-050: Integration test — Auth end-to-end — Full auth flow with real DB
- [ ] DEV-051: Integration test — Resource pipeline end-to-end — Full create-to-graph flow
