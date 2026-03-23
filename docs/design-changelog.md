# Design Changelog

Tracks all changes to `docs/technical-design.md`, `docs/ux-tech-spec.md`, and related design artifacts over time.
Each entry records what changed, why, and any conflicts resolved.

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
