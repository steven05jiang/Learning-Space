# Development Tasks — Learning Space
_Version: v2 | Generated: 2026-03-17_

> **v2 Changes:**
> - DEV-044, DEV-045, DEV-046: UI shell implementations completed ahead of schedule via UI-001/UI-002 (mock data)
> - DEV-001: Added CI tooling constraint (ESLint 8.57.1, direct eslint invocation)
> - DEV-044: Updated library reference (react-force-graph-2d, not React Flow/Cytoscape.js)
> - DEV-052 (new): Wire graph visualization to real GET /graph API
> - DEV-053 (new): Wire chat UI to real POST /chat API

---

## Module: Infrastructure & Project Setup

### DEV-001: Initialize monorepo and project structure
**Type:** Infra
**BDD Reference:** (prerequisite for all scenarios)
**Description:** Create the repository layout per the technical design: `apps/web/` (Next.js), `apps/api/` (FastAPI), `deploy/`, `docs/`. Initialize package.json, requirements.txt, pyproject.toml, .gitignore, and basic CI config.
**Acceptance Criteria:**
- [x] Repository matches the suggested layout in section 8.1
- [x] `apps/web/` is a scaffolded Next.js project
- [x] `apps/api/` is a scaffolded FastAPI project with `main.py` returning health check
- [x] CI runs linting and tests for both apps
- [x] **CI tooling constraint (v2):** Web CI uses direct `eslint` invocation (not `next lint` — incompatible with Next.js 16 / ESLint 9 was downgraded to 8.57.1)
**Estimated Effort:** M
**Dependencies:** None
**Status:** ✅ Complete (PR #1)

### DEV-002: Configure PostgreSQL schema and migrations
**Type:** DB
**BDD Reference:** (prerequisite for all data-dependent scenarios)
**Description:** Set up Alembic (or similar) for migrations. Create initial migration for `users`, `user_accounts`, `resources`, and `resource_processing_log` tables per section 2.1.
**Acceptance Criteria:**
- [x] Migration creates all 4 tables with correct columns, types, constraints, and indexes
- [x] `(provider, external_id)` unique constraint on `user_accounts`
- [x] GIN index on `resources.tags`
- [x] Migrations can be applied and rolled back cleanly
**Estimated Effort:** M
**Dependencies:** DEV-001
**Status:** ✅ Complete (PR #7)

### DEV-003: Configure Neo4j connection and schema setup
**Type:** DB
**BDD Reference:** (prerequisite for graph scenarios)
**Description:** Set up Neo4j driver connection in the backend. Create initialization script for constraints (unique Tag `id` per `owner_id`). Provide connection pooling config.
**Acceptance Criteria:**
- [x] Neo4j driver connects and health-checks successfully
- [x] Uniqueness constraint on `(Tag.id, Tag.owner_id)` is created
- [x] Connection config is driven by environment variables
**Estimated Effort:** S
**Dependencies:** DEV-001
**Status:** ✅ Complete (PR #8)

### DEV-004: Set up environment variable configuration
**Type:** Infra
**BDD Reference:** (prerequisite for all services)
**Description:** Implement a settings/config module using Pydantic Settings (or similar) that loads all env vars per section 8.5: DATABASE_URL, NEO4J_URI, REDIS_URL, OAuth secrets, LangChain keys, etc.
**Acceptance Criteria:**
- [x] All env vars from section 8.5 are defined with types and defaults
- [x] Missing required vars cause a clear startup error
- [x] `.env.example` file documents all variables
**Estimated Effort:** S
**Dependencies:** DEV-001
**Status:** ✅ Complete (PR #2)

---

## Module: Authentication

### DEV-005: Implement OAuth login flow (multi-provider)
**Type:** Backend
**BDD Reference:** Scenario: User logs in with Twitter for the first time; Scenario: User logs in with an existing linked account
**Description:** Implement `GET /auth/login/{provider}`, `GET /auth/callback` for Twitter, Google, and GitHub. On callback: exchange code for tokens, fetch user info, look up `user_accounts` by `(provider, external_id)`. If not found, create `users` + `user_accounts`. If found, update `last_login_at` and tokens. Issue JWT or set session cookie.
**Acceptance Criteria:**
- [x] Login flow works for Twitter, Google, and GitHub
- [x] New users get a `users` row and `user_accounts` row created
- [x] Returning users are authenticated to their existing `users` row
- [x] JWT or session cookie is issued on successful auth
- [x] `last_login_at` is updated on each login
**Estimated Effort:** L
**Dependencies:** DEV-002, DEV-004
**Status:** ✅ Complete (PR #13)

### DEV-006: Implement auth middleware / dependency
**Type:** Backend
**BDD Reference:** Scenario: Session/JWT is validated on each request; Scenario: Unauthenticated user is redirected to login
**Description:** Create a FastAPI dependency (`get_current_user`) that extracts and validates JWT/session from request. Returns `users.id` or raises 401.
**Acceptance Criteria:**
- [x] Valid tokens resolve to the correct `user_id`
- [x] Expired or invalid tokens return 401
- [x] Dependency is reusable across all protected routes
**Estimated Effort:** S
**Dependencies:** DEV-005
**Status:** ✅ Complete (PR #16)

### DEV-007: Implement account linking flow
**Type:** Backend
**BDD Reference:** Scenario: User links an additional social account; Scenario: User attempts to link an account already linked to another user
**Description:** Implement `GET /auth/link/{provider}` (requires auth). Encodes `link:<user_id>` in OAuth state. On callback, if state indicates link flow, create new `user_accounts` row for current user. If `(provider, external_id)` exists for another user, return 409.
**Acceptance Criteria:**
- [ ] Authenticated user can start link flow for any supported provider
- [ ] New `user_accounts` row is created under the current user
- [ ] 409 returned if account already belongs to another user
- [ ] Tokens are stored for the linked account
**Estimated Effort:** M
**Dependencies:** DEV-005, DEV-006

### DEV-008: Implement account unlinking
**Type:** Backend
**BDD Reference:** Scenario: User unlinks a social account; Scenario: User cannot unlink their last account
**Description:** Implement `DELETE /auth/accounts/{account_id}`. Verify account belongs to current user. If user has only one account, return 400 `CANNOT_UNLINK_LAST_ACCOUNT`. Otherwise delete the row.
**Acceptance Criteria:**
- [ ] Account is deleted if user has 2+ accounts
- [ ] 400 with `CANNOT_UNLINK_LAST_ACCOUNT` if it's the last account
- [ ] 404 if account doesn't exist or doesn't belong to user
**Estimated Effort:** S
**Dependencies:** DEV-006

### DEV-009: Implement GET /auth/me endpoint
**Type:** Backend
**BDD Reference:** Scenario: User retrieves their profile and linked accounts
**Description:** Return current user with all linked accounts (no tokens exposed). Response matches section 3.4.1.
**Acceptance Criteria:**
- [x] Returns user `id`, `display_name`, `email`, and `accounts` array
- [x] `access_token` and `refresh_token` are never included in response
- [x] Each account includes `provider`, `display_name`, `email`, `last_login_at`, `created_at`
**Estimated Effort:** S
**Dependencies:** DEV-006
**Status:** ✅ Complete (PR #17)

### DEV-010: Implement POST /auth/logout
**Type:** Backend
**BDD Reference:** (implicit from auth design)
**Description:** Invalidate session or JWT. If using stateless JWT, implement a token denylist or simply clear the cookie.
**Acceptance Criteria:**
- [x] After logout, the token/session is no longer valid
- [x] Subsequent requests with the old token return 401
**Estimated Effort:** S
**Dependencies:** DEV-006
**Status:** ✅ Complete (PR #18)

### DEV-011: Unit tests — Authentication
**Type:** Testing
**BDD Reference:** All auth scenarios
**Description:** Write pytest tests for: login flow (new user, existing user), link flow (success, 409 conflict), unlink (success, last account), /auth/me, logout. Mock OAuth providers.
**Acceptance Criteria:**
- [ ] Tests cover all auth BDD scenarios
- [ ] OAuth providers are mocked (no real network calls)
- [ ] All tests pass
**Estimated Effort:** M
**Dependencies:** DEV-005, DEV-006, DEV-007, DEV-008, DEV-009, DEV-010

---

## Module: Resources — API

### DEV-012: Implement Pydantic models for resources
**Type:** Backend
**BDD Reference:** (prerequisite for resource endpoints)
**Description:** Create Pydantic request/response models per section 3.1: `ResourceCreate`, `ResourceUpdate`, `ResourceResponse`. Validate `content_type` is `url` or `text`.
**Acceptance Criteria:**
- [x] `ResourceCreate` validates `content_type` and `original_content` required, `prefer_provider` optional
- [x] `ResourceUpdate` has all fields optional
- [x] `ResourceResponse` matches section 3.1.3
**Estimated Effort:** S
**Dependencies:** DEV-001
**Status:** ✅ Complete (PR #10)

### DEV-013: Implement POST /resources (create)
**Type:** Backend
**BDD Reference:** Scenario: Authenticated user submits a URL resource; Scenario: Authenticated user submits a text resource; Scenario: User submits a URL with prefer_provider hint
**Description:** Create resource in PostgreSQL with `status=PENDING`, enqueue background processing job. Requires auth (return 401 if not). Return 202 with resource.
**Acceptance Criteria:**
- [x] Resource row created with correct `owner_id`, `content_type`, `original_content`, `prefer_provider`
- [x] Status is PENDING or PROCESSING
- [x] Background job is enqueued
- [x] Returns 202 with full resource response
- [x] Returns 401 if not authenticated
**Estimated Effort:** M
**Dependencies:** DEV-006, DEV-012, DEV-002
**Status:** ✅ Complete (PR #20)

### DEV-014: Implement GET /resources (list) with filters
**Type:** Backend
**BDD Reference:** Scenario: User lists their resources; Scenario: User filters resources by tag; Scenario: User filters resources by status
**Description:** List resources for `current_user`. Support query params: `tag`, `status`, `limit`, `offset`. Filter by `owner_id` always.
**Acceptance Criteria:**
- [x] Only returns resources owned by the current user
- [x] `?tag=AI` filters using JSONB contains
- [x] `?status=READY` filters by status
- [x] Pagination with `limit` and `offset`
**Estimated Effort:** S
**Dependencies:** DEV-006, DEV-012
**Status:** ✅ Complete (PR #26)

### DEV-015: Implement GET /resources/{id} (single)
**Type:** Backend
**BDD Reference:** Scenario: User views a single resource
**Description:** Return a single resource by ID. Verify ownership (return 404 if not found or not owned by user).
**Acceptance Criteria:**
- [ ] Returns full resource response
- [ ] 404 if resource doesn't exist or belongs to another user
**Estimated Effort:** S
**Dependencies:** DEV-006, DEV-012

### DEV-016: Implement PATCH /resources/{id} (update)
**Type:** Backend
**BDD Reference:** Scenario: User updates a resource title; Scenario: User updates original_content triggering reprocessing
**Description:** Update user-editable fields. If `original_content` changes, set `status=PROCESSING` and enqueue re-processing job.
**Acceptance Criteria:**
- [ ] Only provided fields are updated
- [ ] `updated_at` is refreshed
- [ ] Changing `original_content` triggers re-processing
- [ ] 404 if not found or not owned
**Estimated Effort:** M
**Dependencies:** DEV-006, DEV-012

### DEV-017: Implement DELETE /resources/{id}
**Type:** Backend
**BDD Reference:** Scenario: User deletes a resource
**Description:** Delete resource (soft or hard delete) and enqueue a graph sync job to update Neo4j.
**Acceptance Criteria:**
- [ ] Resource is removed or marked deleted
- [ ] Graph sync job is enqueued
- [ ] 404 if not found or not owned
**Estimated Effort:** S
**Dependencies:** DEV-006, DEV-012

### DEV-018: Unit tests — Resource API
**Type:** Testing
**BDD Reference:** All resource management scenarios
**Description:** Write pytest tests for: create (url, text, prefer_provider, unauth), list (filters), get, update (with re-process), delete. Use TestClient and mock DB.
**Acceptance Criteria:**
- [ ] Tests cover all resource BDD scenarios
- [ ] All tests pass
**Estimated Effort:** M
**Dependencies:** DEV-013, DEV-014, DEV-015, DEV-016, DEV-017

---

## Module: Resource Processing — Worker

### DEV-019: Implement task queue infrastructure
**Type:** Backend
**BDD Reference:** (prerequisite for all worker scenarios)
**Description:** Set up the async job queue. Options: Celery + Redis, or `asyncio` background tasks, or ARQ. Define `process_resource` and `sync_graph` job signatures.
**Acceptance Criteria:**
- [ ] Jobs can be enqueued from the API
- [ ] Worker process picks up and executes jobs
- [ ] Failed jobs are logged
**Estimated Effort:** M
**Dependencies:** DEV-001, DEV-004

### DEV-020: Implement URL content fetcher (unauthenticated)
**Type:** Backend
**BDD Reference:** Scenario: Worker processes a URL resource successfully
**Description:** Fetch URL content via HTTP GET. Handle success, redirects, and common failure modes (timeout, 404, etc.).
**Acceptance Criteria:**
- [ ] Fetches HTML/text content from URLs
- [ ] Handles timeouts and HTTP errors gracefully
- [ ] Returns fetched content or error info
**Estimated Effort:** S
**Dependencies:** DEV-001

### DEV-021: Implement authenticated URL fetcher (provider API)
**Type:** Backend
**BDD Reference:** Scenario: URL requires login and user has linked account; Scenario: URL requires login and user has no linked account
**Description:** When unauthenticated fetch fails or domain is in the auth-required list (twitter.com, x.com, etc.), look up owner's `user_accounts` for that provider. Use `access_token` to fetch via provider API. If no linked account, set `status=FAILED` with user-facing message.
**Acceptance Criteria:**
- [ ] Domain→provider mapping works (twitter.com → twitter, etc.)
- [ ] `prefer_provider` hint is respected
- [ ] Access token is used for authenticated fetch
- [ ] Token refresh is attempted if expired
- [ ] FAILED status with clear message if no linked account
**Estimated Effort:** L
**Dependencies:** DEV-020, DEV-002

### DEV-022: Implement LLM processing (title, summary, tags)
**Type:** Backend
**BDD Reference:** Scenario: Worker processes a URL resource successfully; Scenario: Worker processes a text resource successfully; Scenario: LLM processing fails
**Description:** Send fetched content (or pasted text) to the LLM. Extract title, summary, and tags array. Handle LLM failures gracefully (set `status=FAILED`).
**Acceptance Criteria:**
- [ ] LLM returns structured output: title, summary, tags
- [ ] Tags are an array of strings
- [ ] LLM timeout/error sets status=FAILED with message
**Estimated Effort:** M
**Dependencies:** DEV-004

### DEV-023: Implement process_resource job (full pipeline)
**Type:** Backend
**BDD Reference:** All worker scenarios
**Description:** Orchestrate the full pipeline: set status PROCESSING → fetch content (DEV-020/021) → LLM (DEV-022) → update resource in DB → trigger graph update (DEV-026). Handle errors at each step.
**Acceptance Criteria:**
- [ ] Pipeline runs end-to-end for URL and text resources
- [ ] Status transitions: PENDING → PROCESSING → READY or FAILED
- [ ] Processing log entries are created (optional)
- [ ] Graph update is triggered on success
**Estimated Effort:** M
**Dependencies:** DEV-019, DEV-020, DEV-021, DEV-022

### DEV-024: Unit tests — Worker / Resource Processing
**Type:** Testing
**BDD Reference:** All worker scenarios
**Description:** Test the full pipeline with mocked HTTP, LLM, and Neo4j. Cover: URL success, text success, auth-required URL with linked account, auth-required URL without linked account, LLM failure.
**Acceptance Criteria:**
- [ ] All worker BDD scenarios covered
- [ ] External services are mocked
- [ ] All tests pass
**Estimated Effort:** M
**Dependencies:** DEV-023

---

## Module: Knowledge Graph — Backend

### DEV-025: Implement graph service (Neo4j operations)
**Type:** Backend
**BDD Reference:** Scenario: Graph is updated after resource is processed; Scenario: Graph is updated after resource deletion; Scenario: Graph is updated after resource re-processing
**Description:** Create a graph service with methods: `update_from_resource(owner_id, tags[])` — merge Tag nodes and RELATED_TO edges; `remove_resource_tags(owner_id, old_tags[])` — decrement/remove edges; `cleanup_orphan_tags(owner_id)`.
**Acceptance Criteria:**
- [ ] Tag nodes are created with `owner_id` scoping
- [ ] `RELATED_TO` edges are created for each tag pair with weight
- [ ] Weights are incremented on new resources and decremented on removal
- [ ] Orphan tags (no resources) can be cleaned up
**Estimated Effort:** L
**Dependencies:** DEV-003

### DEV-026: Integrate graph update into worker pipeline
**Type:** Backend
**BDD Reference:** Scenario: Graph is updated after resource is processed
**Description:** After LLM processing succeeds in the worker, call graph service to update Neo4j with the resource's tags.
**Acceptance Criteria:**
- [ ] Graph is updated after each successful resource processing
- [ ] Old tags are removed and new tags applied on re-processing
**Estimated Effort:** S
**Dependencies:** DEV-025, DEV-023

### DEV-027: Implement graph sync job for resource deletion
**Type:** Backend
**BDD Reference:** Scenario: Graph is updated after resource deletion
**Description:** When a resource is deleted, enqueue a job that calls graph service to decrement RELATED_TO weights for the resource's tags and clean up orphan tags.
**Acceptance Criteria:**
- [ ] Edge weights are decremented correctly
- [ ] Zero-weight edges are removed
- [ ] Orphan tags are cleaned up
**Estimated Effort:** S
**Dependencies:** DEV-025, DEV-019

---

## Module: Knowledge Graph — API

### DEV-028: Implement GET /graph (graph view)
**Type:** Backend
**BDD Reference:** Scenario: User views the root graph; Scenario: User views graph centered on a specific tag
**Description:** Query Neo4j for the user's graph. Support optional `?root=TagName`. Return nodes (with `level`: parent/current/child) and edges per section 3.2.3.
**Acceptance Criteria:**
- [ ] Returns nodes and edges scoped to `owner_id`
- [ ] Nodes include `id`, `label`, `level`, `resource_count`
- [ ] `?root=` parameter centers the view on a specific tag
- [ ] Three-level display (parent/current/child)
**Estimated Effort:** M
**Dependencies:** DEV-025, DEV-006

### DEV-029: Implement POST /graph/expand
**Type:** Backend
**BDD Reference:** Scenario: User expands a graph node
**Description:** Expand graph from a specific node. Accept `node_id` and optional `direction`. Return next level of nodes and edges.
**Acceptance Criteria:**
- [ ] Returns neighbors of the specified node
- [ ] Supports `direction` parameter (children/parents)
- [ ] Scoped to `owner_id`
**Estimated Effort:** S
**Dependencies:** DEV-025, DEV-006

### DEV-030: Implement GET /graph/nodes/{node_id}/resources
**Type:** Backend
**BDD Reference:** Scenario: User views resources for a graph node
**Description:** Query PostgreSQL for resources where `tags` contains the given tag name and `owner_id` matches. Return list of resources.
**Acceptance Criteria:**
- [ ] Returns resources matching the tag for the current user
- [ ] Uses GIN index on `tags` JSONB column
- [ ] Response includes `id`, `title`, `summary`, `original_content`, `content_type`
**Estimated Effort:** S
**Dependencies:** DEV-006, DEV-012

### DEV-031: Unit tests — Knowledge Graph API
**Type:** Testing
**BDD Reference:** All graph exploration scenarios
**Description:** Test graph endpoints with mocked Neo4j and PostgreSQL.
**Acceptance Criteria:**
- [ ] Tests cover all graph exploration BDD scenarios
- [ ] All tests pass
**Estimated Effort:** M
**Dependencies:** DEV-028, DEV-029, DEV-030

---

## Module: Chat — AI Agent

### DEV-032: Implement LangGraph agent with tools
**Type:** Backend
**BDD Reference:** Scenario: User sends a chat message; Scenario: Agent uses graph traversal tool
**Description:** Create a LangGraph agent with tools: `search_resources(query, tag)`, `get_resources_for_tag(tag)`, `get_graph_neighbors(node_id)`, `get_resource_summary(resource_id)`. Tools call internal services (not public API). Set system prompt per section 8.4.
**Acceptance Criteria:**
- [ ] Agent is configured with LangGraph
- [ ] All 4+ tools are implemented and callable
- [ ] Tools use internal service layer (not HTTP)
- [ ] LangSmith tracing is configured
- [ ] System prompt guides the agent appropriately
**Estimated Effort:** L
**Dependencies:** DEV-014, DEV-025, DEV-004

### DEV-033: Implement POST /chat endpoint
**Type:** Backend
**BDD Reference:** Scenario: User sends a chat message; Scenario: User continues a conversation
**Description:** Accept message and optional `conversation_id`. Create or load conversation. Run LangGraph agent. Store messages and return response.
**Acceptance Criteria:**
- [ ] New conversation created if no `conversation_id`
- [ ] Existing conversation continued if `conversation_id` provided
- [ ] Agent response is stored and returned
- [ ] Response matches section 3.3.2
**Estimated Effort:** M
**Dependencies:** DEV-032, DEV-006

### DEV-034: Implement GET /chat/conversations and GET /chat/conversations/{id}/messages
**Type:** Backend
**BDD Reference:** Scenario: User lists their conversations; Scenario: User retrieves messages in a conversation
**Description:** List conversations for current user; get messages in a specific conversation ordered by created_at.
**Acceptance Criteria:**
- [ ] Conversations scoped to `owner_id`
- [ ] Messages returned in chronological order
- [ ] 404 if conversation not found or not owned
**Estimated Effort:** S
**Dependencies:** DEV-033

### DEV-035: Implement conversation storage (DB schema)
**Type:** DB
**BDD Reference:** (prerequisite for chat persistence)
**Description:** Create migration for `conversations` and `messages` tables. Conversations: `id`, `user_id`, `created_at`, `updated_at`. Messages: `id`, `conversation_id`, `role`, `content`, `created_at`.
**Acceptance Criteria:**
- [ ] Tables created with correct schema
- [ ] FK constraints and indexes in place
**Estimated Effort:** S
**Dependencies:** DEV-002

### DEV-036: Unit tests — Chat / Agent
**Type:** Testing
**BDD Reference:** All chat scenarios
**Description:** Test chat endpoints and agent tool invocations with mocked LLM and services.
**Acceptance Criteria:**
- [ ] Tests cover all chat BDD scenarios
- [ ] LLM is mocked
- [ ] All tests pass
**Estimated Effort:** M
**Dependencies:** DEV-033, DEV-034

---

## Module: API — Common

### DEV-037: Implement health check endpoint
**Type:** Backend
**BDD Reference:** Scenario: Health check returns OK
**Description:** Implement `GET /health` that returns 200 with service status. Optionally check DB and Neo4j connectivity.
**Acceptance Criteria:**
- [x] Returns 200 when service is healthy
- [x] No authentication required
**Estimated Effort:** XS
**Dependencies:** DEV-001
**Status:** ✅ Complete (PR #11)

### DEV-038: Implement standard error handling
**Type:** Backend
**BDD Reference:** Scenario: API returns standard error format
**Description:** Create exception handlers that return errors in the standard format: `{ "detail": "...", "code": "...", "status": N }` per section 3.5.
**Acceptance Criteria:**
- [x] All errors follow the standard format
- [x] HTTP status codes used correctly (400, 401, 403, 404, 429, 500)
- [x] Custom error codes like `RESOURCE_NOT_FOUND`, `CANNOT_UNLINK_LAST_ACCOUNT` are defined
**Estimated Effort:** S
**Dependencies:** DEV-001
**Status:** ✅ Complete (PR #12)

---

## Module: Frontend — Auth

### DEV-039: Implement OAuth login UI (multi-provider)
**Type:** Frontend
**BDD Reference:** Scenario: User logs in with Twitter for the first time; Scenario: Unauthenticated user is redirected to login
**Description:** Login page with Google and X (Twitter) buttons in a 2-col grid. "Don't have an account? Sign up" link. Blur-orbs gradient background. Redirect to backend `/auth/login/{provider}`. Handle callback and store session/JWT.
**Acceptance Criteria:**
- [x] Login buttons for Google and X (Twitter)
- [x] Successful auth stores session and redirects to app
- [x] Unauthenticated users are redirected to login page
- [x] OKLch color system, blur-orbs background per ux-requirements.md
**Estimated Effort:** M
**Dependencies:** DEV-005
**Status:** ✅ Complete (PR #25, enhanced via UI-001 PR #40)

### DEV-040: Implement Settings — Account Management UI
**Type:** Frontend
**BDD Reference:** Scenario: User views linked accounts in settings; Scenario: User adds a new linked account from settings; Scenario: User sees error when unlinking last account
**Description:** Settings page showing linked accounts from `GET /auth/me`. "Add" buttons for each provider. "Disconnect" button per account. Handle `CANNOT_UNLINK_LAST_ACCOUNT` error.
**Acceptance Criteria:**
- [ ] Lists all linked accounts
- [ ] "Add" initiates `/auth/link/{provider}` flow
- [ ] "Disconnect" calls `DELETE /auth/accounts/{id}`
- [ ] Error shown when trying to unlink last account
**Estimated Effort:** M
**Dependencies:** DEV-039, DEV-009

---

## Module: Frontend — Resources

### DEV-041: Implement resource submission form
**Type:** Frontend
**BDD Reference:** Scenario: User sees resource submission form; Scenario: Unauthenticated user attempts to create a resource
**Description:** Form with URL/text toggle. Submit calls `POST /resources`. If 401, show login prompt.
**Acceptance Criteria:**
- [x] URL and text input modes
- [x] Submits to `POST /resources`
- [x] Shows login prompt on 401
- [x] Shows success/processing state after submission
**Estimated Effort:** M
**Dependencies:** DEV-013, DEV-039
**Status:** ✅ Complete (PR #28)

### DEV-042: Implement resource list view
**Type:** Frontend
**BDD Reference:** Scenario: User browses their resource list; Scenario: Resource shows processing status; Scenario: Resource shows FAILED status with actionable message
**Description:** List page showing all user resources. Display title, summary, tags, status. Show processing indicator for PROCESSING. Show error message and Settings link for FAILED resources. Support tag/status filtering.
**Acceptance Criteria:**
- [x] Lists all resources with title, summary, tags, status
- [x] Processing indicator for PROCESSING status
- [x] FAILED status shows `status_message` and link to Settings
- [x] Filter by tag and status
- [x] Pagination
**Estimated Effort:** L
**Dependencies:** DEV-014, DEV-041
**Status:** ✅ Complete (PR #29)

### DEV-043: Implement resource detail / edit / delete
**Type:** Frontend
**BDD Reference:** Scenario: User views a single resource (implicit edit/delete from resource management)
**Description:** Resource detail page with edit and delete functionality. Edit form calls `PATCH /resources/{id}`. Delete button calls `DELETE /resources/{id}` with confirmation.
**Acceptance Criteria:**
- [ ] Detail view shows full resource info
- [ ] Edit form for user-editable fields
- [ ] Delete with confirmation dialog
- [ ] Navigates back to list after delete
**Estimated Effort:** M
**Dependencies:** DEV-015, DEV-016, DEV-017

---

## Module: Frontend — Knowledge Graph

### DEV-044: Implement graph visualization component
**Type:** Frontend
**BDD Reference:** Scenario: User views the knowledge graph; Scenario: User clicks a node to expand
**Description:** Force-directed graph visualization using `react-force-graph-2d` (dynamic import, SSR disabled). Renders nodes (tag labels) and edges. Custom `linkCanvasObject` for edges that stop at node boundary. Node click expands the graph. Runs on mock data until DEV-052 wires it to the real API.
**Acceptance Criteria:**
- [x] Graph renders with force-directed layout, nodes and edges
- [x] Edges stop at node boundary (custom linkCanvasObject with 'replace' mode)
- [x] Node opacity: 0.45 normal, 0.08 dimmed; edge thickness: 1 normal, 2 highlighted
- [x] Clicking a node triggers expand (currently mock; real API wiring in DEV-052)
- [x] Graph re-centers via ResizeObserver when chat panel opens/closes
- [x] Dynamic import (SSR disabled) — avoids Next.js canvas SSR issues
**Estimated Effort:** L
**Dependencies:** DEV-028, DEV-029 (for real data; UI shell independent)
**Status:** ✅ UI Shell Complete (PR #40 via UI-001 + PR #41 via UI-002) — API wiring pending (DEV-052)

### DEV-045: Implement resource panel on node click
**Type:** Frontend
**BDD Reference:** Scenario: User clicks a node to see resources
**Description:** When a node is clicked, display associated resources in a detail dialog. Show connected topics and resources. Dismissible. Runs on mock data until DEV-052 wires it to `GET /graph/nodes/{node_id}/resources`.
**Acceptance Criteria:**
- [x] Clicking a node shows associated resources in a dialog
- [x] Dialog shows connected topics and resources (mock data)
- [x] Dialog is dismissible
- [ ] Wired to real `GET /graph/nodes/{node_id}/resources` API (DEV-052)
**Estimated Effort:** M
**Dependencies:** DEV-030, DEV-044
**Status:** ✅ UI Shell Complete (PR #40 via UI-001) — API wiring pending (DEV-052)

---

## Module: Frontend — Chat

### DEV-046: Implement chat UI
**Type:** Frontend
**BDD Reference:** Scenario: User opens the chat interface; Scenario: User sends a message and receives a response
**Description:** Slide-out chat panel (360–400px wide) triggered by Sparkles icon toggle in sidebar. Scrollable message history with sentinel-div auto-scroll (Radix UI ScrollArea compatible). User input with send button. Multi-turn support via `conversation_id`. Runs on mock data until DEV-053 wires it to the real API.
**Acceptance Criteria:**
- [x] Chat panel slides open/closed via Sparkles toggle with active ring state
- [x] Scrollable message area with correct auto-scroll (sentinel div + scrollIntoView)
- [x] `min-h-0` on ScrollArea prevents layout overflow bug
- [x] Message input and send button
- [x] Multi-turn conversations work with `conversation_id` (mock)
- [ ] Wired to real `POST /chat` and `GET /chat/conversations` APIs (DEV-053)
**Estimated Effort:** L
**Dependencies:** DEV-033, DEV-034
**Status:** ✅ UI Shell Complete (PR #40 via UI-001 + PR #41 via UI-002) — API wiring pending (DEV-053)

---

## Module: Frontend — API Wiring (new in v2)

### DEV-052: Wire graph visualization to real API
**Type:** Frontend
**BDD Reference:** Scenario: User views the knowledge graph; Scenario: User clicks a node to expand; Scenario: User clicks a node to see resources
**Description:** Connect the existing `knowledge-graph.tsx` component (built with mock data in DEV-044/045) to the real backend APIs. Replace mock graph data with `GET /graph` response. Replace mock expand with `POST /graph/expand`. Replace mock node resources with `GET /graph/nodes/{node_id}/resources`. Add auth token passing, loading states, and error handling.
**Acceptance Criteria:**
- [ ] Graph renders real data from `GET /graph` for the authenticated user
- [ ] Node click expand calls `POST /graph/expand` and appends new nodes/edges
- [ ] Node click resources panel loads from `GET /graph/nodes/{node_id}/resources`
- [ ] Auth token is passed correctly (uses existing session)
- [ ] Loading skeleton shown while fetching
- [ ] Error state shown if API fails
- [ ] Empty state shown if user has no graph data yet
**Estimated Effort:** M
**Dependencies:** DEV-028, DEV-029, DEV-030, DEV-044, DEV-045

### DEV-053: Wire chat UI to real API
**Type:** Frontend
**BDD Reference:** Scenario: User opens the chat interface; Scenario: User sends a message and receives a response; Scenario: User continues a conversation
**Description:** Connect the existing `chat-panel.tsx` component (built with mock data in DEV-046) to the real backend API. Replace mock send with `POST /chat`. Support `conversation_id` for multi-turn. Optionally load history from `GET /chat/conversations`. Add streaming if supported, or poll for response.
**Acceptance Criteria:**
- [ ] Sending a message calls `POST /chat` and displays the real assistant response
- [ ] `conversation_id` is persisted across messages in the same session
- [ ] Auth token is passed correctly
- [ ] Loading indicator shown while waiting for response
- [ ] Error state shown if API fails
- [ ] Previous conversation selectable from history (GET /chat/conversations)
**Estimated Effort:** S
**Dependencies:** DEV-033, DEV-034, DEV-046

---

## Module: Deployment

### DEV-047: Create Dockerfiles for frontend and backend
**Type:** DevOps
**BDD Reference:** Scenario: Docker images build successfully
**Description:** Create Dockerfile for `apps/web/` (Next.js: build + serve on port 3000) and `apps/api/` (Python: FastAPI + worker). Multi-stage builds for smaller images.
**Acceptance Criteria:**
- [ ] `learning-space-frontend` image builds and runs
- [ ] `learning-space-backend` image builds and runs
- [ ] Multi-stage builds minimize image size
- [ ] Health check passes in containerized mode
**Estimated Effort:** M
**Dependencies:** DEV-001

### DEV-048: Create Helm chart
**Type:** DevOps
**BDD Reference:** Scenario: Helm chart deploys to Kubernetes
**Description:** Create Helm chart under `deploy/helm/learning-space/` with: Chart.yaml, values.yaml, templates for Deployments (frontend, api, worker), Services, Ingress, Secrets, ConfigMaps.
**Acceptance Criteria:**
- [ ] `helm template` renders valid Kubernetes manifests
- [ ] All components (frontend, api, worker) have Deployments and Services
- [ ] Ingress with TLS and path-based routing
- [ ] Secrets for DB, Neo4j, OAuth, LangSmith credentials
- [ ] Configurable replicas and image tags via values
**Estimated Effort:** L
**Dependencies:** DEV-047

### DEV-049: Configure ArgoCD application
**Type:** DevOps
**BDD Reference:** Scenario: ArgoCD syncs from Git
**Description:** Create ArgoCD Application manifest under `deploy/argocd/application.yaml`. Point to Helm chart in the repo. Configure auto-sync or manual sync policy.
**Acceptance Criteria:**
- [ ] ArgoCD Application YAML is valid
- [ ] Points to correct Helm chart path
- [ ] Sync policy configured
- [ ] Namespace is set (e.g. `learning-space`)
**Estimated Effort:** S
**Dependencies:** DEV-048

---

## Module: Integration Tests

### DEV-050: Integration test — Auth end-to-end
**Type:** Testing
**BDD Reference:** All auth scenarios
**Description:** Integration tests with a test database: full login flow (mocked OAuth provider), link, unlink, /me endpoint.
**Acceptance Criteria:**
- [ ] Tests use a real test database
- [ ] OAuth provider is mocked at HTTP level
- [ ] Full flow: register → login → link → unlink → /me
**Estimated Effort:** M
**Dependencies:** DEV-011

### DEV-051: Integration test — Resource pipeline end-to-end
**Type:** Testing
**BDD Reference:** Resource creation through graph update
**Description:** Integration test: create resource → worker processes → LLM generates tags → graph updated. Use test DB and test Neo4j (or TestContainers). Mock LLM.
**Acceptance Criteria:**
- [ ] Full pipeline tested end-to-end
- [ ] Resource goes from PENDING to READY
- [ ] Tags appear on resource and in Neo4j graph
- [ ] LLM is mocked but pipeline is real
**Estimated Effort:** L
**Dependencies:** DEV-024, DEV-031
