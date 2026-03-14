# Development Plan — Learning Space
_Version: v1 | Generated: 2026-03-14_

## Overview

Learning Space is a personal knowledge management app where users collect learning resources (URLs, text), which are automatically summarized and tagged by an LLM, forming a personal knowledge graph that can be explored visually and queried via an AI chatbot. The delivery philosophy is **thin vertical slices over horizontal layers** — ship a working auth-to-resource-creation loop as early as possible, then layer on graph, chat, and polish.

---

## Priority Tiers

Tasks are assigned to one of four tiers. A coding agent must complete all tasks in a tier before starting the next, unless explicitly marked `[parallel-safe]`.

---

### Tier 1 — Foundation (must exist before anything else works)

These are hard technical prerequisites: no other task can start without them.

| Priority | Task | Type | Effort | Rationale |
|----------|------|------|--------|-----------|
| 1 | DEV-001: Initialize monorepo and project structure | Infra | M | All other tasks depend on the repo layout, scaffolded apps, and CI |
| 2 | DEV-004: Set up environment variable configuration | Infra | S | All services need config before they can connect to anything |
| 3 | DEV-002: Configure PostgreSQL schema and migrations | DB | M | Users, resources, accounts — every feature needs the data layer |
| 4 | DEV-003: Configure Neo4j connection and schema setup | DB | S | Graph features depend on this; start early to surface driver issues |
| 5 | DEV-012: Implement Pydantic models for resources | Backend | S | Shared request/response models used by all resource endpoints |
| 6 | DEV-037: Implement health check endpoint | Backend | XS | Verifies the app starts and responds; used by CI and k8s probes |
| 7 | DEV-038: Implement standard error handling | Backend | S | Consistent error format needed before any endpoint returns errors |

**Tier 1 exit gate:**
- `apps/api/` starts and `GET /health` returns 200
- `alembic upgrade head` applies all migrations cleanly to a fresh PostgreSQL
- Neo4j driver connects and uniqueness constraint is created
- Pydantic models validate correctly (unit test)
- All env vars load from `.env` with clear errors for missing required vars
- CI pipeline runs linting + tests for both apps (even if test count is low)

---

### Tier 2 — MVP Core (first testable user journey end-to-end)

The thinnest vertical slice: a user can **log in, submit a URL, see it processed, and view it in their resource list.** Happy-path only.

| Priority | Task | Type | Effort | Rationale |
|----------|------|------|--------|-----------|
| 1 | DEV-005: Implement OAuth login flow (multi-provider) | Backend | L | Everything behind auth; unblocks all protected routes |
| 2 | DEV-006: Implement auth middleware / dependency | Backend | S | All protected endpoints need `get_current_user` |
| 3 | DEV-009: Implement GET /auth/me endpoint | Backend | S | Frontend needs this to show logged-in state |
| 4 | DEV-010: Implement POST /auth/logout | Backend | S | Complete the auth lifecycle |
| 5 | DEV-013: Implement POST /resources (create) | Backend | M | Core of the first user journey — submit a resource |
| 6 | DEV-014: Implement GET /resources (list) with filters | Backend | S | User needs to see their resources after submitting |
| 7 | DEV-015: Implement GET /resources/{id} (single) | Backend | S | Resource detail view |
| 8 | DEV-019: Implement task queue infrastructure | Backend | M | Resources must be processed asynchronously |
| 9 | DEV-020: Implement URL content fetcher (unauthenticated) | Backend | S | Worker needs to fetch URL content |
| 10 | DEV-022: Implement LLM processing (title, summary, tags) | Backend | M | Core value: auto-summarize and tag |
| 11 | DEV-023: Implement process_resource job (full pipeline) | Backend | M | Ties fetch + LLM + DB update together |
| 12 | DEV-039: Implement OAuth login UI (multi-provider) | Frontend | M | Users need a way to log in |
| 13 | DEV-041: Implement resource submission form | Frontend | M | Users need a way to submit resources |
| 14 | DEV-042: Implement resource list view | Frontend | L | Users need to see their resources and processing status |
| 15 | DEV-011: Unit tests — Authentication | Testing | M | Verify auth works before building on it |
| 16 | DEV-018: Unit tests — Resource API | Testing | M | Verify resource CRUD works |

**Tier 2 exit gate:**
- A user can open the app, log in with Twitter (or mocked OAuth), submit a URL, see it go to PROCESSING, and after the worker runs, see it as READY with title/summary/tags in their resource list.
- `POST /resources` returns 401 when not authenticated.
- Unit tests pass for auth and resource endpoints.

---

### Tier 3 — Feature Complete (remaining functional scope, dependency-ordered)

All remaining features, ordered by dependency then user value.

| Priority | Task | Type | Effort | Depends On | Rationale |
|----------|------|------|--------|------------|-----------|
| 1 | DEV-007: Implement account linking flow | Backend | M | DEV-006 | Unlocks multi-account and authenticated URL fetching |
| 2 | DEV-008: Implement account unlinking | Backend | S | DEV-006 | Completes account management |
| 3 | DEV-021: Implement authenticated URL fetcher (provider API) | Backend | L | DEV-020, DEV-002 | Unlocks saving from login-required sites (Twitter, etc.) |
| 4 | DEV-016: Implement PATCH /resources/{id} (update) | Backend | M | DEV-013 | Users need to edit resources |
| 5 | DEV-017: Implement DELETE /resources/{id} | Backend | S | DEV-013 | Users need to delete resources |
| 6 | DEV-025: Implement graph service (Neo4j operations) | Backend | L | DEV-003 | Foundation for all graph features |
| 7 | DEV-026: Integrate graph update into worker pipeline | Backend | S | DEV-025, DEV-023 | Resources must update the graph on processing |
| 8 | DEV-027: Implement graph sync job for resource deletion | Backend | S | DEV-025, DEV-019 | Graph must stay consistent on resource deletion |
| 9 | DEV-028: Implement GET /graph (graph view) | Backend | M | DEV-025, DEV-006 | Core graph exploration API |
| 10 | DEV-029: Implement POST /graph/expand | Backend | S | DEV-025, DEV-006 | Graph drill-down |
| 11 | DEV-030: Implement GET /graph/nodes/{node_id}/resources | Backend | S | DEV-006, DEV-012 | Resources by tag from graph |
| 12 | DEV-035: Implement conversation storage (DB schema) | DB | S | DEV-002 | Chat needs persistence |
| 13 | DEV-032: Implement LangGraph agent with tools | Backend | L | DEV-014, DEV-025, DEV-004 | Core chat intelligence |
| 14 | DEV-033: Implement POST /chat endpoint | Backend | M | DEV-032, DEV-006 | Chat API |
| 15 | DEV-034: Implement GET /chat/conversations and messages | Backend | S | DEV-033 | Chat history |
| 16 | DEV-040: Implement Settings — Account Management UI | Frontend | M | DEV-039, DEV-009 | Users manage linked accounts |
| 17 | DEV-043: Implement resource detail / edit / delete | Frontend | M | DEV-015, DEV-016, DEV-017 | Full resource management UI |
| 18 | DEV-044: Implement graph visualization component | Frontend | L | DEV-028, DEV-029 | Core graph UI |
| 19 | DEV-045: Implement resource panel on node click | Frontend | M | DEV-030, DEV-044 | Discover resources from graph |
| 20 | DEV-046: Implement chat UI | Frontend | L | DEV-033, DEV-034 | Chat interface |
| 21 | DEV-024: Unit tests — Worker / Resource Processing | Testing | M | DEV-023 | Verify worker pipeline |
| 22 | DEV-031: Unit tests — Knowledge Graph API | Testing | M | DEV-028, DEV-029, DEV-030 | Verify graph endpoints |
| 23 | DEV-036: Unit tests — Chat / Agent | Testing | M | DEV-033, DEV-034 | Verify chat |

**Tier 3 exit gate:**
- All features from the technical design are implemented and individually tested.
- User can: log in with multiple providers, link/unlink accounts, submit URL and text resources (including from login-required sites), edit/delete resources, explore their knowledge graph visually, click nodes to see resources, chat with the AI agent about their resources, and manage settings.
- All unit tests pass.

---

### Tier 4 — Hardening (non-functional requirements, polish, and coverage)

Items that improve quality, reliability, and deployment readiness.

| Priority | Task | Type | Effort | Rationale |
|----------|------|------|--------|-----------|
| 1 | DEV-047: Create Dockerfiles for frontend and backend | DevOps | M | Required for any deployment |
| 2 | DEV-048: Create Helm chart | DevOps | L | Kubernetes deployment |
| 3 | DEV-049: Configure ArgoCD application | DevOps | S | GitOps automation |
| 4 | DEV-050: Integration test — Auth end-to-end | Testing | M | Full auth flow with real DB |
| 5 | DEV-051: Integration test — Resource pipeline end-to-end | Testing | L | Full create-to-graph flow with real DB + Neo4j |

**Tier 4 exit gate:**
- Docker images build and pass health checks.
- Helm chart renders valid manifests and deploys to a test cluster.
- ArgoCD application is configured and syncs.
- Integration tests pass with real databases (test instances).
- All unit + integration tests green in CI.

---

## Milestones

### Milestone 1 — Walking Skeleton
**Completed by:** Tier 1 done
**DEV tasks included:** DEV-001, DEV-002, DEV-003, DEV-004, DEV-012, DEV-037, DEV-038

**What a tester can do at this milestone:**
> I can clone the repo, run `docker compose up` (or equivalent local setup), hit `GET /health` and get a 200 response. I can run `alembic upgrade head` and see all tables created in PostgreSQL. The Neo4j connection is verified. The project structure is clean, CI is green, and the codebase is ready for feature development.

**What is NOT yet possible:** No authentication, no resource submission, no graph, no chat, no frontend.

---

### Milestone 2 — First User Journey
**Completed by:** Tier 2 done
**DEV tasks included:** DEV-005, DEV-006, DEV-009, DEV-010, DEV-011, DEV-013, DEV-014, DEV-015, DEV-018, DEV-019, DEV-020, DEV-022, DEV-023, DEV-039, DEV-041, DEV-042

**What a tester can do at this milestone:**
> I can open the app in a browser, log in with Twitter (or another OAuth provider), see my profile, submit a URL, and watch it go from "Processing..." to showing a title, summary, and tags. I can view my list of resources and click into any one. If I'm not logged in, I'm prompted to log in before I can submit anything. The full loop — auth to resource to AI-processed result — works end-to-end.

**What is NOT yet possible:** Account linking/unlinking, authenticated URL fetching, resource editing/deletion, knowledge graph, chat, deployment to Kubernetes.

---

### Milestone 3 — Feature Complete
**Completed by:** Tier 3 done
**DEV tasks included:** DEV-007, DEV-008, DEV-016, DEV-017, DEV-021, DEV-024, DEV-025, DEV-026, DEV-027, DEV-028, DEV-029, DEV-030, DEV-031, DEV-032, DEV-033, DEV-034, DEV-035, DEV-036, DEV-040, DEV-043, DEV-044, DEV-045, DEV-046

**What a tester can do at this milestone:**
> I can use all features described in the technical design. I manage multiple linked social accounts from Settings. I submit resources including from login-required sites like Twitter. I edit and delete resources. I explore my personal knowledge graph visually — nodes are tags, edges show relationships, and I can click to expand and drill down. Clicking a tag node shows me all resources with that tag. I can chat with the AI agent: "What resources do I have about AI coding?" and get an accurate, context-aware answer that references my actual resources and graph. All unit tests pass.

**What is NOT yet possible:** Dockerized deployment, Kubernetes/Helm, ArgoCD, integration tests with real infrastructure.

---

### Milestone 4 — Production Ready
**Completed by:** Tier 4 done
**DEV tasks included:** DEV-047, DEV-048, DEV-049, DEV-050, DEV-051

**What a tester can do at this milestone:**
> I can build Docker images for frontend and backend, deploy them to a Kubernetes cluster using the Helm chart, and have ArgoCD manage the deployment from Git. Integration tests with real databases confirm the auth flow and resource processing pipeline work end-to-end. The system is ready for beta users.

---

## Coding Agent Execution Rules

1. **Never start a task before its dependencies are complete.** Check `dev-tasks-map.md` before each task.
2. **Complete each Tier's exit gate before advancing.** Exit gates are not optional.
3. **Within a tier, follow the priority order** unless a task is marked `[parallel-safe]`.
4. **`[parallel-safe]` tasks** within the same tier may be started concurrently if separate agents are available.
5. **When a task is unexpectedly blocked**, escalate immediately rather than skipping ahead.
6. **Test tasks belong to the same tier as the feature they test** — do not defer testing to a later tier.

---

## Risk & Assumptions Log

| # | Risk / Assumption | Tier Affected | Mitigation |
|---|-------------------|---------------|------------|
| 1 | OAuth providers (Twitter/X, Google, GitHub) may have rate limits or API changes | T2 | Pin SDK versions; mock providers in tests; test with real providers in a staging env |
| 2 | Twitter/X API authentication for content fetching may require elevated access | T3 | Research Twitter API tiers early; have fallback to basic scraping if API access is limited |
| 3 | LLM quality for summarization and tag extraction may vary | T2 | Design prompts carefully; add a manual override mechanism (user can edit title/tags) |
| 4 | Neo4j schema may need revision as graph complexity grows | T3 | Keep graph schema simple (Tag + RELATED_TO only); use migrations or versioned Cypher scripts |
| 5 | LangGraph agent tool quality depends on well-indexed resources | T3 | Ensure PostgreSQL GIN indexes perform well; consider adding full-text search if JSONB tag matching is insufficient |
| 6 | Frontend graph visualization library choice (React Flow vs Cytoscape.js) affects UX significantly | T3 | Evaluate both libraries with a small prototype before committing; React Flow is simpler, Cytoscape.js is more powerful for graph layouts |
| 7 | WebSocket or polling for real-time status updates may add complexity | T2, T3 | Start with polling (simpler); upgrade to WebSocket in a later iteration if needed |
| 8 | Single callback URL for all OAuth providers requires careful state management | T2 | Encode provider info in OAuth state parameter; test all three providers thoroughly |
