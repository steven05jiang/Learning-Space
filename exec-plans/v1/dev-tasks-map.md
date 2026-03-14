# Dev Tasks Dependency Map — Learning Space
_Version: v1 | Generated: 2026-03-14_

---

## Full Dependency Tree

```
[Module: Infrastructure & Project Setup]
├── DEV-001: Initialize monorepo and project structure
│   ├── DEV-002: Configure PostgreSQL schema and migrations
│   │   ├── DEV-005: Implement OAuth login flow (multi-provider)
│   │   │   ├── DEV-006: Implement auth middleware / dependency
│   │   │   │   ├── DEV-007: Implement account linking flow
│   │   │   │   │   └── DEV-008: Implement account unlinking
│   │   │   │   ├── DEV-009: Implement GET /auth/me endpoint
│   │   │   │   ├── DEV-010: Implement POST /auth/logout
│   │   │   │   ├── DEV-013: Implement POST /resources (create)
│   │   │   │   │   ├── DEV-016: Implement PATCH /resources/{id} (update)
│   │   │   │   │   └── DEV-017: Implement DELETE /resources/{id}
│   │   │   │   ├── DEV-014: Implement GET /resources (list) with filters
│   │   │   │   ├── DEV-015: Implement GET /resources/{id} (single)
│   │   │   │   ├── DEV-028: Implement GET /graph (graph view)
│   │   │   │   ├── DEV-029: Implement POST /graph/expand
│   │   │   │   ├── DEV-030: Implement GET /graph/nodes/{node_id}/resources
│   │   │   │   └── DEV-033: Implement POST /chat endpoint
│   │   │   └── DEV-039: Implement OAuth login UI (multi-provider)
│   │   │       ├── DEV-040: Implement Settings — Account Management UI
│   │   │       └── DEV-041: Implement resource submission form
│   │   │           └── DEV-042: Implement resource list view
│   │   ├── DEV-013: Implement POST /resources (create)
│   │   ├── DEV-021: Implement authenticated URL fetcher (provider API)
│   │   └── DEV-035: Implement conversation storage (DB schema)
│   ├── DEV-003: Configure Neo4j connection and schema setup
│   │   └── DEV-025: Implement graph service (Neo4j operations)
│   │       ├── DEV-026: Integrate graph update into worker pipeline
│   │       ├── DEV-027: Implement graph sync job for resource deletion
│   │       ├── DEV-028: Implement GET /graph (graph view)
│   │       ├── DEV-029: Implement POST /graph/expand
│   │       └── DEV-032: Implement LangGraph agent with tools
│   │           └── DEV-033: Implement POST /chat endpoint
│   │               └── DEV-034: Implement GET /chat/conversations and messages
│   ├── DEV-004: Set up environment variable configuration
│   │   ├── DEV-005: Implement OAuth login flow (multi-provider)
│   │   ├── DEV-019: Implement task queue infrastructure
│   │   │   ├── DEV-023: Implement process_resource job (full pipeline)
│   │   │   │   ├── DEV-026: Integrate graph update into worker pipeline
│   │   │   │   └── DEV-024: Unit tests — Worker / Resource Processing
│   │   │   └── DEV-027: Implement graph sync job for resource deletion
│   │   ├── DEV-022: Implement LLM processing (title, summary, tags)
│   │   │   └── DEV-023: Implement process_resource job (full pipeline)
│   │   └── DEV-032: Implement LangGraph agent with tools
│   ├── DEV-012: Implement Pydantic models for resources
│   │   ├── DEV-013: Implement POST /resources (create)
│   │   ├── DEV-014: Implement GET /resources (list) with filters
│   │   ├── DEV-015: Implement GET /resources/{id} (single)
│   │   ├── DEV-016: Implement PATCH /resources/{id} (update)
│   │   ├── DEV-017: Implement DELETE /resources/{id}
│   │   └── DEV-030: Implement GET /graph/nodes/{node_id}/resources
│   ├── DEV-020: Implement URL content fetcher (unauthenticated)
│   │   └── DEV-021: Implement authenticated URL fetcher (provider API)
│   │       └── DEV-023: Implement process_resource job (full pipeline)
│   ├── DEV-037: Implement health check endpoint
│   ├── DEV-038: Implement standard error handling
│   └── DEV-047: Create Dockerfiles for frontend and backend
│       └── DEV-048: Create Helm chart
│           └── DEV-049: Configure ArgoCD application

[Module: Testing — Unit]
├── DEV-011: Unit tests — Authentication
│   └── DEV-050: Integration test — Auth end-to-end
├── DEV-018: Unit tests — Resource API
├── DEV-024: Unit tests — Worker / Resource Processing
│   └── DEV-051: Integration test — Resource pipeline end-to-end
├── DEV-031: Unit tests — Knowledge Graph API
│   └── DEV-051: Integration test — Resource pipeline end-to-end
└── DEV-036: Unit tests — Chat / Agent

[Module: Frontend — depends on backend APIs]
├── DEV-039: Implement OAuth login UI
│   ├── DEV-040: Settings — Account Management UI
│   │   └── [depends on] DEV-009: GET /auth/me
│   └── DEV-041: Resource submission form
│       └── DEV-042: Resource list view
│           └── [depends on] DEV-014: GET /resources
├── DEV-043: Resource detail / edit / delete
│   └── [depends on] DEV-015, DEV-016, DEV-017
├── DEV-044: Graph visualization component
│   └── [depends on] DEV-028, DEV-029
│   └── DEV-045: Resource panel on node click
│       └── [depends on] DEV-030
└── DEV-046: Chat UI
    └── [depends on] DEV-033, DEV-034
```

---

## Critical Path

The longest dependency chain (determines minimum delivery time):

```
DEV-001 → DEV-004 → DEV-019 → DEV-023 → DEV-026 → (graph populated)
    ↓              ↓
DEV-002 → DEV-005 → DEV-006 → DEV-014 → DEV-032 → DEV-033 → DEV-034 → DEV-046
    ↓
DEV-003 → DEV-025 → DEV-028 → DEV-044 → DEV-045
```

**Longest single chain (13 tasks):**
DEV-001 → DEV-002 → DEV-005 → DEV-006 → DEV-013 → DEV-014 → DEV-032 → DEV-033 → DEV-034 → DEV-036 → DEV-046

---

## Parallel Work Streams

### Stream A — Infrastructure (can start immediately)
DEV-001

### Stream B — Backend Foundation (after DEV-001, parallel within stream)
DEV-002, DEV-003, DEV-004, DEV-012, DEV-020, DEV-037, DEV-038, DEV-047

### Stream C — Auth Backend (after DEV-002 + DEV-004)
DEV-005 → DEV-006 → DEV-007, DEV-008, DEV-009, DEV-010 (parallel after DEV-006)

### Stream D — Resource API (after DEV-006 + DEV-012)
DEV-013, DEV-014, DEV-015 (parallel) → DEV-016, DEV-017 (after DEV-013)

### Stream E — Worker Pipeline (after DEV-004, parallel with Stream D)
DEV-019, DEV-022 (parallel) → DEV-021 (after DEV-020 + DEV-002) → DEV-023 (after DEV-019 + DEV-020 + DEV-021 + DEV-022)

### Stream F — Graph Backend (after DEV-003)
DEV-025 → DEV-026 (after DEV-025 + DEV-023), DEV-027 (after DEV-025 + DEV-019), DEV-028, DEV-029 (after DEV-025 + DEV-006)

### Stream G — Chat Backend (after DEV-014 + DEV-025 + DEV-004)
DEV-035 (after DEV-002) → DEV-032 → DEV-033 → DEV-034

### Stream H — Frontend Auth (after DEV-005)
DEV-039 → DEV-040 (after DEV-039 + DEV-009), DEV-041 (after DEV-039 + DEV-013)

### Stream I — Frontend Features (after respective APIs)
DEV-042 (after DEV-041 + DEV-014), DEV-043 (after DEV-015 + DEV-016 + DEV-017)
DEV-044 (after DEV-028 + DEV-029), DEV-045 (after DEV-044 + DEV-030)
DEV-046 (after DEV-033 + DEV-034)

### Stream J — Testing (after respective implementations)
DEV-011, DEV-018, DEV-024, DEV-031, DEV-036 (parallel, each after its module)
DEV-050, DEV-051 (integration, after unit tests)

### Stream K — Deployment (after DEV-047)
DEV-048 → DEV-049

---

## Milestone Gates

| Milestone | Blocked Tasks Unlocked | Required DEV Tasks |
|-----------|------------------------|-------------------|
| **M1: Foundation** | All backend modules | DEV-001, DEV-002, DEV-003, DEV-004, DEV-012, DEV-037, DEV-038 |
| **M2: Auth + First Resource** | Resource UI, Settings, Graph API, Chat | DEV-005, DEV-006, DEV-007, DEV-008, DEV-009, DEV-010, DEV-013, DEV-014, DEV-015, DEV-019, DEV-020, DEV-022, DEV-039 |
| **M3: Processing Pipeline** | Graph updates, FAILED status UI | DEV-021, DEV-023, DEV-025, DEV-026, DEV-027 |
| **M4: Graph + Chat** | Graph UI, Chat UI, all frontend | DEV-028, DEV-029, DEV-030, DEV-032, DEV-033, DEV-034, DEV-035 |
| **M5: Full Frontend** | Integration tests | DEV-040, DEV-041, DEV-042, DEV-043, DEV-044, DEV-045, DEV-046 |
| **M6: Tested & Deployed** | Production readiness | DEV-011, DEV-016, DEV-017, DEV-018, DEV-024, DEV-031, DEV-036, DEV-047, DEV-048, DEV-049, DEV-050, DEV-051 |
