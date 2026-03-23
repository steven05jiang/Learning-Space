# Requirement Changelog

Tracks all changes to `docs/requirements.md` over time.
Each entry records what changed, why, and any conflicts resolved.

---

## 2026-03-14 — Initial product requirements

**Type:** Requirements
**Trigger:** New requirements
**Docs Affected:** `docs/requirements.md`
**Summary:** Established the full product requirements for Learning Space. Defined the core product vision (collect, organize, and explore learning resources via an automatically generated knowledge graph), six functional requirement areas, the technology stack choices, asynchronous processing architecture, and deployment strategy. This forms the foundational contract for all implementation work.

### Changes

#### Requirements
- Added `docs/requirements.md` §Overview: Product vision — knowledge graph from user-submitted learning resources
- Added `docs/requirements.md` §1 Resource Management: CRUD operations for resources (URL and text), required fields (ID, content, title, summary, tags, timestamps, owner, preferred provider), auth gate on add
- Added `docs/requirements.md` §2 Automatic Resource Processing: URL fetching (including login-required content via linked accounts), LLM summarization and tag generation, linked account fallback messaging
- Added `docs/requirements.md` §3 Knowledge Graph Generation: Per-user graph, tag nodes, co-occurrence edges, async updates
- Added `docs/requirements.md` §4 Knowledge Graph Exploration: Multi-level navigation (parent / current / child), click-to-expand, breadcrumb context
- Added `docs/requirements.md` §5 Resource Discovery from Graph Nodes: Node click shows associated resources (title, summary, link)
- Added `docs/requirements.md` §6 AI Chatbot for Resource Discovery: Agent capabilities (search, summarize, graph traversal, suggestions), LangGraph + LangSmith
- Added `docs/requirements.md` §Technical Choices: Next.js frontend, Python/FastAPI backend, LangGraph agent, Neo4j graph DB, PostgreSQL relational DB, OAuth multi-provider auth (Twitter, Google, GitHub), multi-account linking
- Added `docs/requirements.md` §Asynchronous Processing: PENDING → PROCESSING → READY status lifecycle, background worker pattern
- Added `docs/requirements.md` §Deployment: Docker images, Helm chart, ArgoCD

### Conflicts Resolved
- None (initial document)

### Open Questions
- None at time of creation

---

## 2026-03-16 — UX requirements specification added

**Type:** Requirements
**Trigger:** New requirements (UI/UX design session — ui-tune skill setup, PR #38, then UI-001 prototype migration)
**Docs Affected:** `docs/ux-requirements.md`
**Summary:** Added `docs/ux-requirements.md` to capture the web UI/UX specification for Learning Space. Defined the technology stack (Next.js 16.1.6, React 19.2.4, TailwindCSS v4, shadcn/ui New York style, lucide-react, react-force-graph-2d), design principles (minimal SaaS, dual-mode dark/light), color system using OKLch CSS variables, and the full layout and component specifications for the login page and main application dashboard. A second pass during UI-001 prototype migration (`e5054599`) refined key design decisions from prototype implementation.

### Changes

#### Requirements
- Added `docs/ux-requirements.md` §1 Technology Stack: Next.js 16.1.6, React 19.2.4, TailwindCSS v4, shadcn/ui New York style, lucide-react, react-force-graph-2d
- Added `docs/ux-requirements.md` §2 Design Principles: Minimal/modern, generous whitespace, rounded corners, dual page styles (Login = Modern Gradient UI; App = Minimal SaaS Dashboard)
- Added `docs/ux-requirements.md` §3 Color System: OKLch CSS variables, light/dark auto-switch
- Added `docs/ux-requirements.md` §4 Login Page: Blur orbs background, centered glass card, email/password form, social login 2-column grid (Google + X/Twitter)
- Added `docs/ux-requirements.md` §5 Main Application Page: Top nav bar, sidebar (240px) with 5 nav items, AI chat toggle at sidebar bottom, slide-out chat panel (right, 380px)
- Added `docs/ux-requirements.md` §6–14: Top navigation, sidebar, AI agent chat button (Sparkles icon-only toggle), chat assistant panel, main content area, responsive behavior, folder structure, interaction requirements

### Conflicts Resolved
- Login page background: original spec called for full-screen gradient; prototype implementation used blur orbs — blur orbs chosen and captured as the canonical spec.
- AI agent button: original spec called for labeled "Ask AI Agent" button; prototype PR #2 changed to icon-only Sparkles toggle — icon-only adopted and captured.

### Open Questions
- None
