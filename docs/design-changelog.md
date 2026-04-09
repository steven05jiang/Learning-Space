# Design Changelog

Tracks all changes to `docs/technical-design.md`, `docs/ux-tech-spec.md`, and related design artifacts over time.
Each entry records what changed, why, and any conflicts resolved.

---

## 2026-04-08 — Queue Enhancement: Burst Mode + Upstash Free Tier

**Type:** Design
**Trigger:** Cost optimization (Upstash per-command pricing)
**Docs Affected:** `docs/technical-design.md`, `docs/queue-enhancement-design.md` (new), `docs/design-changelog.md`
**Summary:** Enable ARQ burst mode to reduce Redis command count, leveraging Upstash's free tier (500k commands/month). With 30s timer interval, usage drops to ~250k commands/mo — within free tier limits. Keep Upstash Redis (not migrating to Railway). Production uses burst + systemd timer; local dev uses continuous polling.

### Changes

#### Design
- Added `docs/queue-enhancement-design.md`: Full spec — ARQ burst mode, configurable timer interval, Upstash free tier analysis, systemd timer setup, rollback plan, cost comparison
- Modified `docs/technical-design.md` §7.5: Updated Redis dependency description to reflect burst mode
- Modified `docs/technical-design.md` §8.5 (Environment variables): Updated `REDIS_URL` description to note burst mode

### Implementation Changes

| File | Change |
| ---- | ------ |
| `apps/api/workers/worker.py` | Add `burst = True` to `WorkerSettings` |
| `apps/api/workers/run_worker.py` | Add `--burst` CLI argument parsing via `argparse` |
| `Makefile` | dev-stack-up uses poll mode (continuous); burst only for production timer |
| `deploy/railway/arq-worker.service` | Systemd oneshot service (new) |
| `deploy/railway/arq-worker.timer` | Systemd timer with configurable `OnUnitActiveSec` (new) |
| `.env.production` | `REDIS_URL` remains Upstash (free tier) |

### Conflicts Resolved
- None

### Open Questions
- What is the current Upstash command count? (Measure before/after)
- Is 30s poll interval acceptable for job latency?
- Should a continuously-running worker be kept for low-latency needs?

---

## 2026-03-30 — X.com (Twitter) integration design

**Type:** Both
**Trigger:** New requirements
**Docs Affected:** `docs/technical-design.md`, `docs/design-resource-fetching.md`, `docs/ux-requirements.md`, `docs/design-twitter-integration.md` (new), `CLAUDE.md`
**Summary:** Introduces the full X.com integration design. A new supplement doc `docs/design-twitter-integration.md` owns the complete specification for OAuth scope management, the `twitter_posts` / `twitter_bookmarks` normalized data model, the `twitter_bookmark_sync` cron job algorithm, API contracts for `/integrations/twitter/*` and `/discover/bookmarks`, cleanup logic (30-day TTL + orphaned-post sweep), and rate limit handling. Core docs are updated with targeted changes: new tables in §2.1, `token_scopes` column on `user_accounts`, new endpoint groups §4.7–4.8, updated ER diagram, Twitter Tier 1 status promoted to Implemented in design-resource-fetching.md, and new UX sections for the Discover page and Settings integration panel.

### Changes

#### Requirements
- Added `docs/requirements.md` §8 (8 sub-requirements): X.com integration — OAuth scope grant, resource adding, Discover section, cron sync, pagination, quick-add, no-LLM preview, token scope tracking

#### Design
- Added `docs/design-twitter-integration.md`: full spec — OAuth scope flow, `twitter_posts`/`twitter_bookmarks` schemas, cron job algorithm (`sync_bookmarks_for_user`, `extract_preview`, `run_cleanup`), `has_scope()` helper, rate limit handling table, API contracts (GET status, POST authorize, DELETE disconnect, GET /discover/bookmarks, POST /discover/bookmarks/{id}/add), sequence diagrams §7–8
- Modified `docs/technical-design.md` §2.1.2: Added `token_scopes TEXT` column to `user_accounts`
- Added `docs/technical-design.md` §2.1.6: `twitter_posts` table schema
- Added `docs/technical-design.md` §2.1.7: `twitter_bookmarks` table schema
- Modified `docs/technical-design.md` §2.3: Updated ER diagram to include `twitter_posts` and `twitter_bookmarks`
- Added `docs/technical-design.md` §4.7: Twitter Integration endpoints (GET status, POST authorize, DELETE disconnect)
- Added `docs/technical-design.md` §4.8: Discover endpoints (GET /discover/bookmarks, POST /discover/bookmarks/{tweet_id}/add)
- Modified `docs/design-resource-fetching.md` §2.1: Twitter/x.com integration status changed from `Planned` → `Implemented`
- Modified `docs/ux-requirements.md` §7 Sidebar Navigation: Added "Discover" item with badge; visibility conditional on bookmark.read scope
- Added `docs/ux-requirements.md` §7.2: Discover Page — layout wireframe, bookmark card fields, [+ Add] button states, empty/loading/no-scope states
- Added `docs/ux-requirements.md` §14: Settings — X.com Integration Panel — three connection states (not connected, connected without scope, fully connected), disconnect confirmation dialog
- Modified `CLAUDE.md` On-demand Loading Index: Added `X.com/Twitter integration → docs/design-twitter-integration.md`

### Conflicts Resolved
- None

### Open Questions
- Twitter API Article fields (`article.title`, `article.body`) require Basic+ tier plan. If the deployment is on the Free tier, long-form Article preview will fall back to truncated tweet text. Tier requirement should be confirmed before implementation.

---

## 2026-03-28 — Unified search capability (user-facing + AI agent)

**Type:** Both
**Trigger:** New requirements + technical thoughts (phased search design session)
**Docs Affected:** `docs/technical-design.md`, `docs/ux-requirements.md`, `docs/design-search.md` (new), `CLAUDE.md`
**Summary:** Introduces the unified search design. A new supplement doc `docs/design-search.md` owns the complete specification for `ResourceSearchService` — the single shared backend called by both `GET /resources/search` (HTTP) and `search_resources` (LangGraph tool). Phase 1 uses PostgreSQL full-text search; Phase 2 upgrades to hybrid retrieval with pgvector on Supabase and RRF merge. The supplement doc includes the full retrieval strategy comparison (keyword, vector, hybrid, dedicated engines, file system). Core docs are updated with targeted edits only: new index note (§2.1.3), new endpoint row (§4.2), new event flow (§5.9), agent tool contract (§8.4), repo layout (§8.1). UX requirements gain a search page spec (§7.1).

### Changes

#### Design
- Added `docs/design-search.md`: `ResourceSearchService` interface, `SearchResult`/`ResourceSearchItem`/`AgentResourceResult` models, Phase 1 full-text (functional GIN, `plainto_tsquery`, `ts_rank`, SQLAlchemy implementation), Phase 2 hybrid (`resource_embeddings` table, pgvector IVFFlat, `text-embedding-3-small`, RRF Python implementation, worker embedding step), HTTP endpoint spec (`ResourceSearchRequest`/`ResourceSearchResponse` Pydantic schemas), agent tool `search_resources` contract + system prompt addition, event flows §8.1–8.3, sequence diagrams §9.1–9.3, retrieval strategy comparison appendix §10
- Modified `docs/technical-design.md` §2.1.3: Replaced stale "GIN on tags for search" with Phase 1 functional GIN SQL + Phase 2 `resource_embeddings` pointer
- Modified `docs/technical-design.md` §4.2: Added `GET /resources/search` endpoint row
- Added `docs/technical-design.md` §5.9: Search event flows (user Phase 1, agent Phase 1, worker Phase 2 embedding)
- Modified `docs/technical-design.md` §8.1: Added `design-search.md` to repo layout docs listing
- Modified `docs/technical-design.md` §8.4: Formalized `search_resources` tool contract (code block, return shape, limit cap)
- Added `docs/ux-requirements.md` §7.1 (Search Page): Layout wireframe, debounced input, loading/empty/blank states, tag filter dropdown, result card fields, `rank` not displayed
- Modified `CLAUDE.md` On-demand Loading Index: Added `Search capability / agent search tool → docs/design-search.md`

### Conflicts Resolved
- None

### Open Questions
- Phase 2 embedding API: if active LLM provider doesn't support embeddings, a separate key (`EMBEDDING_API_KEY`) or self-hosted model is needed. Deferred to Phase 2 sprint planning.
- `pg_trgm` fuzzy matching explicitly deferred as premature optimization — log as TD- if real user pain arises.

---

## 2026-03-14 — Initial technical design

**Type:** Design
**Trigger:** Technical thoughts (system architecture from product requirements)
**Docs Affected:** `docs/technical-design.md`
**Summary:** Established the full technical design for Learning Space, translating `docs/requirements.md` into a concrete implementation blueprint. Defined the layered architecture (UI, API, Resource Update, Resource Viewer, AI Agent, Data), data models for PostgreSQL (users, user_accounts, resources, resource_processing_log) and Neo4j (tag nodes and co-occurrence edges), REST API schemas, event flows for resource lifecycle, sequence diagrams for key operations, Kubernetes/Helm/ArgoCD deployment strategy, and implementation guidance for AI coding agents.

### Changes

#### Design
- Added `docs/technical-design.md` §1 System Overview: Architecture summary table (6 layers), data store responsibility split (PostgreSQL vs Neo4j)
- Added `docs/technical-design.md` §2 Data Models: `users`, `user_accounts` (multi-provider OAuth), `resources` (PENDING/PROCESSING/READY/FAILED status lifecycle, prefer_provider for login-required URLs), `resource_processing_log` (observability)
- Added `docs/technical-design.md` §2 Data Models: Neo4j schema — `Tag` nodes and `CO_OCCURS` weighted edges
- Added `docs/technical-design.md` §3 API Schemas: Pydantic/OpenAPI shapes for resource create/update/list, auth endpoints, graph query responses
- Added `docs/technical-design.md` §4 Example Endpoints: REST endpoint definitions for resource CRUD, auth (OAuth login, logout, me, accounts), graph traversal, agent chat
- Added `docs/technical-design.md` §5 Event Flows: Resource submission → worker → LLM → graph update async flow; status state machine
- Added `docs/technical-design.md` §6 Sequence Diagrams: Resource creation, OAuth login, graph exploration, AI agent chat
- Added `docs/technical-design.md` §7 Deployment Strategy: Docker images per service, Helm chart, ArgoCD GitOps pipeline
- Added `docs/technical-design.md` §8 Implementation Guidance: Service boundaries, async worker patterns, LangGraph agent tool setup, encryption for OAuth tokens

### Conflicts Resolved
- None (initial document)

### Open Questions
- None at time of creation

---

## 2026-03-16 — UX technical spec created and UI-001 prototype design decisions captured

**Type:** Design
**Trigger:** Technical thoughts (UI-001 prototype implementation, PR #38 + commit `e5054599`)
**Docs Affected:** `docs/ux-tech-spec.md`
**Summary:** Added `docs/ux-tech-spec.md` — an AI-optimized UI specification intended for single-generation production UI output. Captured all key design decisions made during the UI-001 prototype implementation including technology choices, design system, color system, layout structure, and component specifications. A second pass during the full UI-001 prototype migration updated the spec to reflect the final implemented decisions (blur orbs background, icon-only Sparkles toggle, react-force-graph-2d for knowledge graph).

### Changes

#### Design
- Added `docs/ux-tech-spec.md` §1 Tech Stack: Next.js 16.1.6, React 19.2.4, TailwindCSS v4 (no tailwind.config.js — inline @theme in globals.css), shadcn/ui New York style, lucide-react, react-force-graph-2d, React state/hooks (no global state yet)
- Added `docs/ux-tech-spec.md` §2 Design System: Spacing scale (4/8/16/24/32/48px), border radius (cards 12–16px, buttons 10–12px), subtle shadows only
- Added `docs/ux-tech-spec.md` §3 Color System: OKLch CSS variables in globals.css — light and dark mode token tables
- Added `docs/ux-tech-spec.md` §4–16: Login page (blur orbs bg, centered card, glass effect, social login grid), dashboard layout (topbar 56px, sidebar 240px, main content flex-grow), sidebar navigation (5 items + Sparkles icon-only footer toggle), AI chat panel (right slide-out, 360–400px), resource card spec, responsive behavior (desktop/tablet/mobile), component list, file structure

### Conflicts Resolved
- Background style: full-screen gradient replaced by blur orbs from prototype
- AI agent button: labeled "Ask AI Agent" replaced by icon-only Sparkles toggle from prototype PR #2

### Open Questions
- State management: React hooks only for now; global state (Zustand, Jotai, etc.) deferred until needed

---

## 2026-03-20 — Integration test design added

**Type:** Design
**Trigger:** Technical thoughts (BDD integration test framework design)
**Docs Affected:** `docs/integration-test-design.md`
**Summary:** Added `docs/integration-test-design.md` to define the three-layer integration test strategy for Learning Space: Layer 1 (API integration tests using pytest + real PostgreSQL/Neo4j), Layer 2 (frontend integration tests using Jest + MSW), Layer 3 (E2E tests using Playwright). Defined BDD scenarios for all major functional areas, INT task prefixes, and the test execution pipeline (CI-default groups vs full suite). This design drives the INT-001 through INT-055 task set tracked in `memory/dev-tracker.md`.

### Changes

#### Design
- Added `docs/integration-test-design.md`: Three-layer test strategy (API integration, frontend, E2E)
- Added `docs/integration-test-design.md`: BDD scenario definitions covering auth, resources, knowledge graph, AI agent, settings
- Added `docs/integration-test-design.md`: CI execution model — Layer 1 runs on every PR, Layers 2–3 on demand
- Added `docs/integration-test-design.md`: INT task numbering scheme (INT-000 = framework, INT-001–055 = BDD scenarios)

### Conflicts Resolved
- None

### Open Questions
- INT tasks blocked on DEV dependencies are deferred; see `memory/dev-tracker.md` for per-task dependency status

---

## 2026-03-22 — Resource fetching and category taxonomy design; supplement doc strategy adopted

**Type:** Design
**Trigger:** Technical thoughts (feedback review — FB-001, FB-003, FB-004) + doc organization strategy
**Docs Affected:** `docs/technical-design.md`, `docs/design-resource-fetching.md` (new), `docs/design-category-taxonomy.md` (new)
**Summary:** Two new supplement design documents created to hold domain-specific specs without bloating `technical-design.md` (which was already hitting context limits at 12k+ tokens). `docs/design-resource-fetching.md` specifies the tiered URL fetch strategy (domain blocklist, HTTP fetch, Playwright fallback, error classification). `docs/design-category-taxonomy.md` specifies the category taxonomy (10 seeded categories, user-created categories, Neo4j three-level hierarchy, LLM prompt changes, /categories endpoints, tag editing validation). `technical-design.md` is updated with new schema fields, the updated Neo4j model, new endpoints, and pointers to the supplement docs, replacing all stale inline fetch descriptions. The supplement doc strategy is now documented in `CLAUDE.md` On-demand Loading Index and `.claude/commands/project-design.md`.

### Changes

#### Design
- Added `docs/design-resource-fetching.md`: Full spec for tiered URL fetch strategy — domain blocklist, Tier 1 (API), Tier 2a (HTTP), Tier 2b (Playwright), error classification, data model additions (`fetch_tier`, `fetch_error_type`), updated event flow, sequence diagram, implementation guidance (Playwright Docker image, domain config format)
- Added `docs/design-category-taxonomy.md`: Full spec for category taxonomy — `categories` PostgreSQL table, `top_level_categories` JSONB field on resources, Neo4j `Root` + `Category` nodes + `CHILD_OF` + `BELONGS_TO` relationships, LLM output schema update, /categories endpoints, validation rules (CATEGORY_REQUIRED, INVALID_CATEGORY), seeding/migration notes
- Modified `docs/technical-design.md` §2.1.3 (resources): Added `fetch_tier`, `fetch_error_type`, `top_level_categories` fields; updated `prefer_provider` description
- Added `docs/technical-design.md` §2.1.5 (categories): New PostgreSQL `categories` table definition
- Modified `docs/technical-design.md` §2.2 (Neo4j): Replaced flat Tag schema with three-node schema (Root, Category, Tag); added CHILD_OF and BELONGS_TO relationships; updated resource-tag linkage note
- Modified `docs/technical-design.md` §3.1.2 (Update resource): Added `tags` and `top_level_categories` as editable fields; added validation rules
- Modified `docs/technical-design.md` §3.2.1 (Graph node schema): Added `node_type` field (`root` | `category` | `topic`)
- Added `docs/technical-design.md` §4.3 (Categories endpoints): GET/POST/DELETE /categories
- Modified `docs/technical-design.md` §5.1.1 (Fetch flow): Replaced stale inline description with pointer to `docs/design-resource-fetching.md`
- Modified `docs/technical-design.md` §5.1 step 5–6: Updated to reference `top_level_categories`, category-aware Neo4j update
- Modified `docs/technical-design.md` §6.1 (Sequence diagram): Updated worker fetch and LLM/Neo4j steps
- Modified `docs/technical-design.md` §6.2 (Graph update sequence): Updated to include Root/Category merge and CHILD_OF/BELONGS_TO edges
- Modified `docs/technical-design.md` §8.1 (Repo layout): Updated docs/ listing to include new supplement docs
- Modified `docs/technical-design.md` §8.2 (Worker checklist): Replaced stale fetch logic with pointers to supplement docs
- Modified `docs/technical-design.md` §8.3 (Frontend checklist): Added category management UI and tag editor constraint note
- Modified `CLAUDE.md` On-demand Loading Index: Added rows for new supplement docs
- Modified `.claude/commands/project-design.md`: Documented supplement doc strategy (when to create, how to load, how to stage/commit)

### Conflicts Resolved
- `docs/technical-design.md` §5.1.1 contained a full inline fetch flow that conflicted with the new tiered strategy. Replaced with a compact pointer to `docs/design-resource-fetching.md`.
- `docs/technical-design.md` §2.2 contained a flat `Tag`-only Neo4j schema. Replaced with the three-node hierarchy.

### Open Questions
- Playwright worker as separate Kubernetes Deployment vs single worker image: deferred to OPS task. Single image acceptable for early development.
- Existing resource backfill (assign top_level_categories) deferred to OPS task.
