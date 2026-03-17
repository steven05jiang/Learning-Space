# Dev Tasks Dependency Map — Learning Space

_Version: v2 | Generated: 2026-03-17_

> **v2 Changes:**
>
> - DEV-044, DEV-045, DEV-046 are complete (UI shell, mock data) — their downstream wiring
>   tasks are now DEV-052 and DEV-053
> - DEV-052 added: Wire graph UI → depends on DEV-028, DEV-029, DEV-030
> - DEV-053 added: Wire chat UI → depends on DEV-033, DEV-034
> - Critical path updated to reflect completed tasks

---

## Full Dependency Tree

```
[Module: Infrastructure & Project Setup]
├── DEV-001: Initialize monorepo and project structure ✅
│   ├── DEV-002: Configure PostgreSQL schema and migrations ✅
│   │   ├── DEV-005: Implement OAuth login flow (multi-provider) ✅
│   │   │   ├── DEV-006: Implement auth middleware / dependency ✅
│   │   │   │   ├── DEV-007: Implement account linking flow
│   │   │   │   │   └── DEV-008: Implement account unlinking
│   │   │   │   ├── DEV-009: Implement GET /auth/me endpoint ✅
│   │   │   │   ├── DEV-010: Implement POST /auth/logout ✅
│   │   │   │   ├── DEV-013: Implement POST /resources (create) ✅
│   │   │   │   │   ├── DEV-016: Implement PATCH /resources/{id} (update)
│   │   │   │   │   └── DEV-017: Implement DELETE /resources/{id}
│   │   │   │   ├── DEV-014: Implement GET /resources (list) with filters ✅
│   │   │   │   ├── DEV-015: Implement GET /resources/{id} (single)
│   │   │   │   ├── DEV-028: Implement GET /graph (graph view)
│   │   │   │   │   └── DEV-052: Wire graph visualization to real API
│   │   │   │   ├── DEV-029: Implement POST /graph/expand
│   │   │   │   │   └── DEV-052: Wire graph visualization to real API
│   │   │   │   ├── DEV-030: Implement GET /graph/nodes/{node_id}/resources
│   │   │   │   │   └── DEV-052: Wire graph visualization to real API
│   │   │   │   └── DEV-033: Implement POST /chat endpoint
│   │   │   │       └── DEV-034: GET /chat/conversations and messages
│   │   │   │           ├── DEV-053: Wire chat UI to real API
│   │   │   │           └── DEV-036: Unit tests — Chat / Agent
│   │   │   └── DEV-039: Implement OAuth login UI (multi-provider) ✅
│   │   │       ├── DEV-040: Implement Settings — Account Management UI
│   │   │       │   └── [depends on] DEV-009: GET /auth/me ✅
│   │   │       └── DEV-041: Implement resource submission form ✅
│   │   │           └── DEV-042: Implement resource list view ✅
│   │   │               └── [depends on] DEV-014: GET /resources ✅
│   │   ├── DEV-013: Implement POST /resources (create) ✅
│   │   ├── DEV-021: Implement authenticated URL fetcher (provider API)
│   │   └── DEV-035: Implement conversation storage (DB schema)
│   │       └── DEV-032: Implement LangGraph agent with tools
│   │           └── DEV-033: Implement POST /chat endpoint
│   ├── DEV-003: Configure Neo4j connection and schema setup ✅
│   │   └── DEV-025: Implement graph service (Neo4j operations)
│   │       ├── DEV-026: Integrate graph update into worker pipeline
│   │       ├── DEV-027: Implement graph sync job for resource deletion
│   │       ├── DEV-028: Implement GET /graph (graph view)
│   │       ├── DEV-029: Implement POST /graph/expand
│   │       └── DEV-032: Implement LangGraph agent with tools
│   ├── DEV-004: Set up environment variable configuration ✅
│   │   ├── DEV-005: Implement OAuth login flow (multi-provider) ✅
│   │   ├── DEV-019: Implement task queue infrastructure
│   │   │   ├── DEV-023: Implement process_resource job (full pipeline)
│   │   │   │   ├── DEV-026: Integrate graph update into worker pipeline
│   │   │   │   └── DEV-024: Unit tests — Worker / Resource Processing
│   │   │   └── DEV-027: Implement graph sync job for resource deletion
│   │   ├── DEV-022: Implement LLM processing (title, summary, tags)
│   │   │   └── DEV-023: Implement process_resource job (full pipeline)
│   │   └── DEV-032: Implement LangGraph agent with tools
│   ├── DEV-012: Implement Pydantic models for resources ✅
│   │   ├── DEV-013: Implement POST /resources (create) ✅
│   │   ├── DEV-014: Implement GET /resources (list) with filters ✅
│   │   ├── DEV-015: Implement GET /resources/{id} (single)
│   │   ├── DEV-016: Implement PATCH /resources/{id} (update)
│   │   ├── DEV-017: Implement DELETE /resources/{id}
│   │   └── DEV-030: Implement GET /graph/nodes/{node_id}/resources
│   ├── DEV-020: Implement URL content fetcher (unauthenticated)
│   │   └── DEV-021: Implement authenticated URL fetcher (provider API)
│   │       └── DEV-023: Implement process_resource job (full pipeline)
│   ├── DEV-037: Implement health check endpoint ✅
│   ├── DEV-038: Implement standard error handling ✅
│   └── DEV-047: Create Dockerfiles for frontend and backend
│       └── DEV-048: Create Helm chart
│           └── DEV-049: Configure ArgoCD application

[Module: Frontend — API Wiring (new in v2)]
├── DEV-052: Wire graph visualization to real API
│   └── [requires] DEV-028, DEV-029, DEV-030, DEV-044 ✅, DEV-045 ✅
└── DEV-053: Wire chat UI to real API
    └── [requires] DEV-033, DEV-034, DEV-046 ✅

[Module: Frontend — Completed Shells (v2)]
├── DEV-044: Graph visualization component ✅ (mock data — UI-001, UI-002)
├── DEV-045: Resource panel on node click ✅ (mock data — UI-001)
└── DEV-046: Chat UI ✅ (mock data — UI-001, UI-002)

[Module: Testing — Unit]
├── DEV-011: Unit tests — Authentication
│   └── DEV-050: Integration test — Auth end-to-end
├── DEV-018: Unit tests — Resource API
├── DEV-024: Unit tests — Worker / Resource Processing
│   └── DEV-051: Integration test — Resource pipeline end-to-end
├── DEV-031: Unit tests — Knowledge Graph API
│   └── DEV-051: Integration test — Resource pipeline end-to-end
└── DEV-036: Unit tests — Chat / Agent

[Module: Frontend — Auth/Resources (completed)]
├── DEV-039: Implement OAuth login UI ✅
│   ├── DEV-040: Settings — Account Management UI
│   └── DEV-041: Resource submission form ✅
│       └── DEV-042: Resource list view ✅
└── DEV-043: Resource detail / edit / delete
    └── [depends on] DEV-015, DEV-016, DEV-017
```

---

## Critical Path

The longest dependency chain (determines minimum delivery time). Completed tasks marked ✅.

```
DEV-001 ✅ → DEV-004 ✅ → DEV-019 → DEV-023 → DEV-026 → (graph populated)
    ↓               ↓
DEV-002 ✅ → DEV-005 ✅ → DEV-006 ✅ → DEV-014 ✅ → DEV-032 → DEV-033 → DEV-034 → DEV-053
    ↓
DEV-003 ✅ → DEV-025 → DEV-028 → DEV-052
```

**Longest remaining chain (from current state):**
DEV-019 → DEV-023 → DEV-026 → DEV-025 → DEV-028 → DEV-052 (graph wiring)
DEV-032 → DEV-033 → DEV-034 → DEV-053 (chat wiring)

Both chains can proceed in parallel after their respective prerequisites.

---

## Parallel Work Streams

### Stream A — Already complete ✅

DEV-001, DEV-002, DEV-003, DEV-004, DEV-005, DEV-006, DEV-009, DEV-010,
DEV-012, DEV-013, DEV-014, DEV-037, DEV-038, DEV-039, DEV-041, DEV-042,
DEV-044, DEV-045, DEV-046

### Stream B — Auth remaining (can start now, parallel)

DEV-007 → DEV-008 (account linking/unlinking)
DEV-011 (unit tests, after DEV-007 + DEV-008)

### Stream C — Resource API remaining (can start now, parallel within stream)

DEV-015, DEV-016, DEV-017 (parallel) → DEV-018 (unit tests)
DEV-043 (frontend, after DEV-015 + DEV-016 + DEV-017)

### Stream D — Worker Pipeline (after DEV-004 ✅ — can start now)

DEV-019, DEV-020, DEV-022 (parallel) →
DEV-021 (after DEV-020 + DEV-002 ✅) →
DEV-023 (after DEV-019 + DEV-020 + DEV-021 + DEV-022) →
DEV-024 (unit tests)

### Stream E — Graph Backend (after DEV-003 ✅ — can start now)

DEV-025 →
DEV-026 (after DEV-025 + DEV-023), DEV-027 (after DEV-025 + DEV-019),
DEV-028, DEV-029 (after DEV-025 + DEV-006 ✅) →
DEV-030 (after DEV-006 ✅ + DEV-012 ✅) →
DEV-031 (unit tests, after DEV-028 + DEV-029 + DEV-030) →
DEV-052 (graph UI wiring, after DEV-028 + DEV-029 + DEV-030)

### Stream F — Chat Backend (after DEV-014 ✅ + DEV-025)

DEV-035 (after DEV-002 ✅) →
DEV-032 (after DEV-035 + DEV-014 ✅ + DEV-025 + DEV-004 ✅) →
DEV-033 →
DEV-034 →
DEV-036 (unit tests) +
DEV-053 (chat UI wiring, after DEV-033 + DEV-034)

### Stream G — Frontend Settings (after DEV-039 ✅ + DEV-007)

DEV-040 (Settings UI, after DEV-007 + DEV-009 ✅)

### Stream H — Deployment (parallel with all feature work)

DEV-047 → DEV-048 → DEV-049

### Stream I — Integration Tests (after unit tests)

DEV-050 (after DEV-011) + DEV-051 (after DEV-024 + DEV-031)

---

## Milestone Gates

| Milestone                        | Blocked Tasks Unlocked                 | Required DEV Tasks                                                                                         |
| -------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **M1: Foundation** ✅            | All backend modules                    | DEV-001, DEV-002, DEV-003, DEV-004, DEV-012, DEV-037, DEV-038                                              |
| **M2: Auth + First Resource** ✅ | Resource UI, Settings, Graph API, Chat | DEV-005, DEV-006, DEV-009, DEV-010, DEV-013, DEV-014, DEV-039, DEV-041, DEV-042                            |
| **M3: Processing Pipeline**      | Graph updates, FAILED status UI        | DEV-007, DEV-008, DEV-015, DEV-019, DEV-020, DEV-021, DEV-022, DEV-023, DEV-025, DEV-026, DEV-027          |
| **M4: Graph + Chat Backend**     | Graph UI wiring, Chat UI wiring        | DEV-028, DEV-029, DEV-030, DEV-032, DEV-033, DEV-034, DEV-035                                              |
| **M5: Full Frontend**            | Integration tests                      | DEV-040, DEV-043, DEV-052, DEV-053                                                                         |
| **M6: Tested & Deployed**        | Production readiness                   | DEV-011, DEV-016, DEV-017, DEV-018, DEV-024, DEV-031, DEV-036, DEV-047, DEV-048, DEV-049, DEV-050, DEV-051 |
