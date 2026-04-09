# Current Plan — Learning Space

_Last updated: 2026-03-28_

## Active Version

| Field             | Value                                                            |
| ----------------- | ---------------------------------------------------------------- |
| **Version**       | v2                                                               |
| **Generated**     | 2026-03-17                                                       |
| **Source**        | `docs/technical-design.md` + UI-001/UI-002 implementation review |
| **BDD scenarios** | 48 scenarios across 14 features                                  |
| **Dev tasks**     | 53 tasks across 12 modules                                       |
| **Milestones**    | 4 milestones, 4 priority tiers                                   |

---

## Version History

### v2 — UI Implementation Sync + API Wiring Tasks (2026-03-17)

**Status:** Active
**Summary:** Reflects the UI-001 and UI-002 prototype migration. Three frontend components (knowledge graph, resource panel, chat) were built ahead of schedule with mock data. DEV-044, DEV-045, DEV-046 are marked complete; two new API wiring tasks (DEV-052, DEV-053) replace them in the work queue. ESLint 8.57.1 tooling constraint documented.

#### Changes from v1

**BDD Tasks:**

- Modified: "Frontend — Graph Visualization" feature — updated scenario descriptions to use `react-force-graph-2d` terminology and note UI shell completion
- Modified: "Frontend — Chat UI" — updated chat open scenario to mention Sparkles toggle (implementation detail)
- Added: v2 implementation status note at top of file
- No scenarios added or removed — count remains 48

**Dev Tasks:**

- Added: DEV-052 — Wire graph visualization to real API (GET /graph, POST /graph/expand, GET /graph/nodes/{id}/resources)
- Added: DEV-053 — Wire chat UI to real API (POST /chat, GET /chat/conversations)
- Modified: DEV-001 — Added CI tooling constraint to acceptance criteria (ESLint 8.57.1, direct `eslint` invocation, not `next lint`)
- Modified: DEV-044 — Updated description from "React Flow or Cytoscape.js" to `react-force-graph-2d`; added implementation details (linkCanvasObject, ResizeObserver, opacity/thickness values); marked UI shell complete; noted API wiring pending (DEV-052)
- Modified: DEV-045 — Updated acceptance criteria to reflect dialog implementation; marked UI shell complete; noted API wiring pending (DEV-052)
- Modified: DEV-046 — Updated description with scroll fix details (sentinel div, min-h-0, Sparkles toggle); marked UI shell complete; noted API wiring pending (DEV-053)
- Total tasks: 51 → 53

**Dependencies:**

- New: DEV-052 depends on DEV-028, DEV-029, DEV-030, DEV-044, DEV-045
- New: DEV-053 depends on DEV-033, DEV-034, DEV-046
- Removed: DEV-044 no longer blocks other tasks (was blocking DEV-045 in v1 dep chain — now DEV-052 plays that role)
- Critical path changed: `... → DEV-028 → DEV-044 → DEV-045` → `... → DEV-028 → DEV-052` (DEV-044/045 are done)

**Priority / Tier Changes:**

- DEV-044 moved: Tier 3 pending → Tier 3 complete (UI shell done)
- DEV-045 moved: Tier 3 pending → Tier 3 complete (UI shell done)
- DEV-046 moved: Tier 3 pending → Tier 3 complete (UI shell done)
- DEV-052 added to Tier 3 (replaces DEV-044/045 in work queue, priority 23)
- DEV-053 added to Tier 3 (replaces DEV-046 in work queue, priority 24)

**Milestones:**

- M2: Marked complete (Tier 2 core journey working)
- M3 exit gate updated: now requires DEV-052 and DEV-053 (graph/chat UI wired to real APIs) in addition to all backend work
- New risk added: API response shapes in DEV-028/029/030/033/034 must match existing mock data contracts in DEV-044/045/046

#### Migration Notes

- **Completed tasks affected:** DEV-044, DEV-045, DEV-046 are complete from a UI perspective. No rework needed — they are valid implementations. The acceptance criteria in v2 reflect what was actually built (react-force-graph-2d, sentinel-div scroll, Sparkles toggle).

- **In-progress tasks affected:** None — no tasks were in-progress at the time of this revision.

- **New tasks:** DEV-052 and DEV-053 should be picked up in Tier 3 after their backend API dependencies are ready:
  - Start DEV-052 after DEV-028 + DEV-029 + DEV-030 are all complete
  - Start DEV-053 after DEV-033 + DEV-034 are complete

- **Dependency changes:** DEV-052 and DEV-053 are newly unblocked once their backend APIs land. No previously unblocked tasks have become blocked.

- **Breaking changes:** None. All v1 work remains valid. The only structural change is that DEV-044/045/046 are done and DEV-052/053 are the new pending frontend tasks.

- **Tooling note:** Any agent working on web CI must use direct `eslint` invocation (not `next lint`). This is locked in as of PR #40 and documented in DEV-001 acceptance criteria.

---

### v2.1 — Feedback Implementation (2026-03-22)

**Status:** Active
**Summary:** Plans implementation tasks for all five open feedback items (FB-001 through FB-005) identified during demos on 2026-03-22. Design specs were already committed in the same session (`docs/design-resource-fetching.md` for the tiered fetch strategy, `docs/design-category-taxonomy.md` for the category taxonomy). This update adds 10 new DEV tasks (DEV-056–DEV-065) covering: tiered URL fetch with Playwright fallback (FB-001), processing state machine (FB-002, 3 tasks), category taxonomy with Neo4j hierarchy and LLM prompt update (FB-003, 4 tasks), manual tag editing UI (FB-004), and graph node popup overflow fix (FB-005).

#### Changes from v2

**Dev Tasks:**

- Added: DEV-056 — Tiered URL fetch strategy (domain blocklist + HTTP + Playwright + fetch_tier/fetch_error_type tracking)
- Added: DEV-057 — Add processing_status field to resources + Alembic migration
- Added: DEV-058 — Update worker pipeline to use processing_status state machine
- Added: DEV-059 — Add manual Re-process action to resource detail UI
- Added: DEV-060 — Implement categories table, seed 10 root categories, /categories endpoints
- Added: DEV-061 — Update Neo4j schema to Root/Category/Tag three-level hierarchy
- Added: DEV-062 — Update LLM prompt for tag reuse + require top_level_categories
- Added: DEV-063 — Category management UI in Settings page
- Added: DEV-064 — Tag editor component in resource detail UI
- Added: DEV-065 — Fix graph node popup overflow (constrain size, remove summary, truncate title)
- Total tasks: 55 → 65

**Dependencies:**

- New: DEV-056 depends on DEV-020 ✅, DEV-023 ✅
- New: DEV-057 depends on DEV-002 ✅
- New: DEV-058 depends on DEV-057, DEV-023 ✅
- New: DEV-059 depends on DEV-057, DEV-043 ✅
- New: DEV-060 depends on DEV-002 ✅, DEV-006 ✅
- New: DEV-061 depends on DEV-025 ✅, DEV-060
- New: DEV-062 depends on DEV-022 ✅, DEV-060
- New: DEV-063 depends on DEV-060, DEV-040 ✅
- New: DEV-064 depends on DEV-043 ✅, DEV-061
- New: DEV-065 depends on DEV-052 ✅

**Priority / Tier Changes:**

- DEV-056 added to Tier 3 (priority 30)
- DEV-057 added to Tier 3 (priority 31)
- DEV-058 added to Tier 3 (priority 32)
- DEV-059 added to Tier 3 (priority 33)
- DEV-060 added to Tier 3 (priority 34)
- DEV-061 added to Tier 3 (priority 35)
- DEV-062 added to Tier 3 (priority 36)
- DEV-063 added to Tier 3 (priority 37)
- DEV-064 added to Tier 3 (priority 38)
- DEV-065 added to Tier 3 (priority 39)

**Structural notes:**

- Schema changes: `resources` table gains `fetch_tier`, `fetch_error_type`, `processing_status` columns; new `categories` table added
- Neo4j model changes: flat `Tag` schema replaced with three-node hierarchy (`Root`, `Category`, `Tag`) + `CHILD_OF` and `BELONGS_TO` relationships
- Integration tests INT-029–035 (graph group) will require updates after DEV-061 lands

---

### v2.2 — Deploy Prioritization: Auth Hardening + Multi-LLM + Cheap Cloud Stack (2026-03-27)

**Status:** Active
**Summary:** Adds 11 new tasks (DEV-066–DEV-071, OPS-002–OPS-006) to support an immediate production deployment focused on gathering user feedback. Changes cover: Google-only login (UI restriction + allowlisting security gate), coming-soon UX for disabled features (search button, chat), a multi-LLM provider abstraction supporting Groq/SiliconFlow/Fireworks AI, and a full cheap-cloud deployment stack (Vercel + Railway + Supabase + Neo4j AuraDB Free + Upstash + Namecheap/Cloudflare). DEV-048 and DEV-049 (Helm/ArgoCD) are deprioritized — the k8s deployment strategy is replaced by the low-cost managed cloud approach.

#### Changes from v2.1

**Dev Tasks:**

- Added: DEV-066 — Restrict login UI to Google-only (remove X button + credential form)
- Added: DEV-067 — Disable search button with "coming soon" tooltip
- Added: DEV-068 — Chat panel "coming soon" mode (disable input, inject bot welcome message)
- Added: DEV-069 — User allowlisting backend (ALLOWED_EMAILS env var gate on OAuth callback)
- Added: DEV-070 — Coming-soon page at /coming-soon (redirect target for non-allowlisted users)
- Added: DEV-071 — Multi-LLM provider abstraction (Anthropic/Groq/SiliconFlow/Fireworks via LLM_PROVIDER env var)
- Deprioritized: DEV-048 (Helm chart) — not needed for Vercel+Railway stack
- Deprioritized: DEV-049 (ArgoCD) — not needed for Vercel+Railway stack
- Total DEV tasks: 65 → 71

**Ops Tasks:**

- Added: OPS-002 — Provision Supabase (PostgreSQL) + Neo4j AuraDB Free + Upstash Redis
- Added: OPS-003 — Backend Dockerfile + Railway deployment (API + worker)
- Added: OPS-004 — Frontend Vercel deployment
- Added: OPS-005 — Domain + DNS (Namecheap + Cloudflare)
- Added: OPS-006 — Production Google OAuth + allowlist smoke test
- Total OPS tasks: 1 → 6

**Total tasks: 127 → 138**

**Dependencies:**

- New: DEV-066 depends on DEV-039 ✅
- New: DEV-067 depends on DEV-044 ✅
- New: DEV-068 depends on DEV-046 ✅
- New: DEV-069 depends on DEV-005 ✅
- New: DEV-070 depends on DEV-039 ✅, DEV-069
- New: DEV-071 depends on DEV-022 ✅, DEV-032 ✅
- New: OPS-002 (no dependencies)
- New: OPS-003 depends on DEV-047, OPS-002
- New: OPS-004 depends on OPS-003
- New: OPS-005 depends on OPS-003, OPS-004
- New: OPS-006 depends on DEV-069, OPS-004, OPS-005

**Deployment strategy change:**

- New target: Vercel (frontend) + Railway (API + worker) + Supabase (Postgres) + Neo4j AuraDB Free + Upstash (Redis)
- Replaces: Kubernetes / Helm / ArgoCD (DEV-047 scope narrowed to backend-only Dockerfile)
- Services NOT adopted (from user's candidate list): Clerk (custom OAuth kept), Pinecone (Neo4j used instead), Stripe/Resend (no payment/email features), PostHog/Sentry (deferred to post-MVP)

**Priority / Tier Changes:**

- DEV-066–DEV-071 added to Tier 3 (feature complete), all HIGH priority
- OPS-002–OPS-006 added as new deployment sequence, all HIGH priority
- DEV-048, DEV-049 marked DEFERRED (deprioritized, not blocked)

---

### v2.4 — X.com (Twitter) Integration (2026-03-30)

**Status:** Active
**Summary:** Translates the `docs/design-twitter-integration.md` spec (merged PR #245 on 2026-03-30) into 7 DEV tasks and 7 INT tests. Backend tasks cover: DB migration (token_scopes + twitter_posts + twitter_bookmarks), Twitter integration endpoints + has_scope() helper, Twitter API content fetcher (supersedes DEV-021), bookmark sync cron task, and Discover API endpoints. Frontend tasks cover the Settings X.com Integration Panel and the Discover page with bookmark cards, pagination, and quick-add flow. 7 new INT tests added to a new `twitter` CI group.

#### Changes from v2.3

**Dev Tasks:**

- Added: DEV-081 — DB migration: token_scopes column + twitter_posts + twitter_bookmarks tables
- Added: DEV-082 — Twitter integration endpoints (status / authorize / disconnect) + has_scope() helper
- Added: DEV-083 — Twitter API content fetcher (Tier 1); supersedes DEV-021
- Added: DEV-084 — twitter_bookmark_sync cron task (startup + hourly; 7-day window; cleanup)
- Added: DEV-085 — Discover endpoints (GET /discover/bookmarks + POST /discover/bookmarks/{tweet_id}/add)
- Added: DEV-086 — Settings — X.com Integration Panel UI
- Added: DEV-087 — Discover page UI (bookmark cards, pagination, [+ Add] states)
- Superseded: DEV-021 — superseded by DEV-083 (which provides the full Twitter API fetcher spec)
- Total DEV tasks: 80 → 87

**INT Tasks:**

- Added: INT-060 — Twitter status endpoint reflects all connection variants (group: twitter)
- Added: INT-061 — Authorize returns redirect_url; callback updates token_scopes (group: twitter)
- Added: INT-062 — Disconnect clears token_scopes and deletes bookmarks (group: twitter)
- Added: INT-063 — Bookmark sync creates twitter_posts + twitter_bookmarks (group: twitter)
- Added: INT-064 — Sync skips already-cached posts (group: twitter)
- Added: INT-065 — Discover list returns unprocessed bookmarks sorted by bookmarked_at DESC (group: twitter)
- Added: INT-066 — Quick-add creates resource, sets is_added=true; post cleaned up if fully added (group: twitter)
- Total INT tasks: 59 → 66

**Total tasks: 151 → 165**

**Dependencies:**

- New: DEV-081 depends on DEV-002 ✅
- New: DEV-082 depends on DEV-081, DEV-007 ✅
- New: DEV-083 depends on DEV-056 ✅, DEV-082
- New: DEV-084 depends on DEV-081, DEV-082
- New: DEV-085 depends on DEV-081, DEV-083
- New: DEV-086 depends on DEV-082, DEV-040 ✅
- New: DEV-087 depends on DEV-085, DEV-086
- New: INT-060–062 blocked on DEV-082
- New: INT-063–064 blocked on DEV-084
- New: INT-065 blocked on DEV-085
- New: INT-066 blocked on DEV-085, DEV-083

**Dependency graph:**
```
DEV-081 → DEV-082 → DEV-083 → DEV-085 → DEV-087
                 ↘ DEV-084
                 ↘ DEV-086 → DEV-087
```

**Priority / Tier Changes:**

- DEV-081–DEV-087 added to Tier 3 (HIGH priority)
- INT-060, INT-063, INT-065, INT-066 HIGH priority
- INT-061, INT-062, INT-064 MEDIUM priority
- New CI group `twitter` added (Layer 1 API integration, nightly)

**Structural notes:**

- Schema changes: `user_accounts` gains `token_scopes TEXT`; new `twitter_posts` + `twitter_bookmarks` tables
- New API groups: `/integrations/twitter/*` (§4.7) and `/discover/bookmarks` (§4.8)
- New background worker cron: `twitter_bookmark_sync` (startup + hourly)
- DEV-021 formally superseded by DEV-083

---

### v2.3 — Search Design Breakdown (2026-03-28)

**Status:** Active
**Summary:** Translates the `docs/design-search.md` unified search spec (committed 2026-03-28) into 9 DEV tasks and 4 INT tests. Phase 1 (DEV-072–077) uses PostgreSQL full-text search (functional GIN index, `ResourceSearchService`, `GET /resources/search` endpoint, `search_resources` LangGraph tool, Search page UI, unit tests) and requires no new infrastructure. Phase 2 (DEV-078–080) adds pgvector hybrid retrieval with RRF merge, selectable via `SEARCH_MODE` env var. 4 new INT tests (INT-056–059) added to a new `search` CI group.

#### Changes from v2.2

**Dev Tasks:**

- Added: DEV-072 — Alembic migration: functional GIN index on resources (tsvector)
- Added: DEV-073 — ResourceSearchService Phase 1 (full-text search, SearchResult/ResourceSearchItem/AgentResourceResult models)
- Added: DEV-074 — GET /resources/search endpoint (ResourceSearchRequest/ResourceSearchResponse schemas)
- Added: DEV-075 — search_resources LangGraph tool + AgentResourceResult shape + system prompt update
- Added: DEV-076 — Search page UI (Next.js) + re-enable search navigation (replaces DEV-067 coming-soon tooltip)
- Added: DEV-077 — Unit tests for ResourceSearchService and search endpoint
- Added: DEV-078 — Alembic migration: resource_embeddings table + pgvector IVFFlat index (Phase 2)
- Added: DEV-079 — Worker embedding step: build_embedding_text + upsert resource_embeddings (Phase 2)
- Added: DEV-080 — ResourceSearchService hybrid retrieval: _vector_search + _hybrid_search RRF k=60 (Phase 2)
- Total DEV tasks: 71 → 80

**INT Tasks:**

- Added: INT-056 — User keyword search returns ranked READY results (group: search)
- Added: INT-057 — Tag filter narrows search results (group: search)
- Added: INT-058 — Empty/overlong query → 400 validation error (group: search)
- Added: INT-059 — Agent search_resources returns trimmed AgentResourceResult list (group: search)
- Total INT-BDD tasks: 55 → 59

**Total tasks: 138 → 151**

**Dependencies:**

- New: DEV-072 → DEV-073 → DEV-074 → DEV-076
- New: DEV-073 → DEV-075 (also needs DEV-032 ✅)
- New: DEV-073, DEV-074 → DEV-077
- New: DEV-072 → DEV-078 → DEV-079 → DEV-080 (also needs DEV-073)
- New: INT-056, INT-057 blocked on DEV-073 + DEV-074
- New: INT-058 blocked on DEV-074
- New: INT-059 blocked on DEV-075

**Priority / Tier Changes:**

- DEV-072–076 added to Tier 3 (HIGH priority, Phase 1)
- DEV-077 added to Tier 3 (MEDIUM, unit tests)
- DEV-078–080 added as Phase 2 follow-up (MEDIUM priority)
- INT-056–059 added to new `search` CI group (every PR, Layer 1)

**Structural notes:**

- Phase 1: purely additive — functional GIN index on existing `resources` table, no column changes
- Phase 2: new `resource_embeddings` table + pgvector extension (pre-enabled on Supabase)
- No changes to existing API contracts, auth model, or deployment architecture

---

### v1 — Initial Plan (2026-03-14)

**Status:** Superseded by v2
**Summary:** Initial planning suite generated from technical design. Covers the full Learning Space application: OAuth multi-provider auth, resource management with async LLM processing, Neo4j knowledge graph, LangGraph chat agent, Next.js frontend, and Kubernetes deployment.

No prior version to compare against.
