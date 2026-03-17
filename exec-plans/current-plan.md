# Current Plan — Learning Space

_Last updated: 2026-03-17_

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

### v1 — Initial Plan (2026-03-14)

**Status:** Superseded by v2
**Summary:** Initial planning suite generated from technical design. Covers the full Learning Space application: OAuth multi-provider auth, resource management with async LLM processing, Neo4j knowledge graph, LangGraph chat agent, Next.js frontend, and Kubernetes deployment.

No prior version to compare against.
