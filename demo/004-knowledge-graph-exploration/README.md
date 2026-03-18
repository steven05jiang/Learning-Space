# Demo 004 — Knowledge Graph Exploration

**Status:** ⏳ Pending execution
**Planned after:** DEV-025, DEV-026, DEV-028, DEV-029, DEV-030, DEV-052 complete
(DEV-027 recommended — graph stays consistent when resources are deleted)

---

## Summary

Demonstrates the live knowledge graph in Learning Space.
After processing several URLs, the system has automatically built a **personal knowledge graph** — tags become nodes, resources become edges. A user can **browse the force-directed graph, expand tag clusters, and click a node to see all resources associated with that tag**.

This is the first demo where the graph UI is wired to real API data (not the mock data from UI-001/UI-002).

---

## New Since Last Demo (003)

| Type    | Item    | Description                                                                |
| ------- | ------- | -------------------------------------------------------------------------- |
| Feature | DEV-025 | Graph service (Neo4j operations) — foundation for all graph features       |
| Feature | DEV-026 | Graph update integrated into worker — resources populate graph on process  |
| Feature | DEV-027 | Graph sync on deletion — removing a resource cleans up orphaned nodes      |
| Feature | DEV-028 | GET /graph — returns graph snapshot (nodes + edges)                        |
| Feature | DEV-029 | POST /graph/expand — expands a tag node to show neighbours                 |
| Feature | DEV-030 | GET /graph/nodes/{id}/resources — returns resources associated with a tag  |
| Feature | DEV-052 | Wire graph visualization UI to real API (replacing mock data)              |

---

## Prerequisites

| Requirement                     | Notes                                                    |
| ------------------------------- | -------------------------------------------------------- |
| Docker running                  | For PostgreSQL, Neo4j, Redis via `docker compose`        |
| `uv` installed                  | Python dependency manager                                |
| `npm` installed                 | Node package manager                                     |
| `.env` in `apps/api/`           | Present with valid `ANTHROPIC_API_KEY`                   |
| `NEXT_PUBLIC_API_BASE_URL`      | Set to `http://localhost:8000`                           |
| Worker running                  | Required to process resources and populate graph         |
| ≥5 processed resources in DB    | Run Demo 003 first to seed the graph with real tags      |

---

## Procedure

### Step 1 — Start infrastructure

```bash
make infra-up
```

### Step 2 — Run database migrations

```bash
cd apps/api && uv run alembic upgrade head
```

### Step 3 — Start the API server and worker

```bash
# Terminal 1
cd apps/api && uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2
cd apps/api && uv run celery -A worker.celery_app worker --loglevel=info
```

### Step 4 — Authenticate (JWT shortcut)

```bash
cd apps/api
uv run python -c "
from core.jwt import create_access_token
token = create_access_token({'sub': '1', 'email': 'demo@learningspace.dev'})
print(token)
"
```

### Step 5 — Seed processed resources (if starting fresh)

Submit at least 5 URLs covering different topics to generate diverse tags:

```
POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://anthropic.com/research/claude"}

POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://langchain.com/langgraph"}

POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://neo4j.com/docs/getting-started/"}

POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://fastapi.tiangolo.com/"}

POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://react.dev/"}
```

Wait for all resources to reach `PROCESSED` status (~10-30 seconds each).

### Step 6 — Verify graph API

```
GET /graph  Authorization: Bearer <token>
→ 200 {
    "nodes": [{"id": "...", "label": "<tag>", "resource_count": N}, ...],
    "edges": [{"source": "...", "target": "...", "weight": N}, ...]
  }
```

Confirm nodes correspond to LLM-generated tags from processed resources.

### Step 7 — Expand a graph node

```
POST /graph/expand  Authorization: Bearer <token>
{"node_id": "<tag-node-id>"}
→ 200 {
    "nodes": [...],   # neighbour nodes
    "edges": [...]    # edges to/from expanded node
  }
```

### Step 8 — Get resources for a tag node

```
GET /graph/nodes/{node_id}/resources  Authorization: Bearer <token>
→ 200 {"items": [...], "total": N}
```

Verify resources listed are actually tagged with this tag in the DB.

### Step 9 — Start the frontend

```bash
cd apps/web && npm run dev -- --port 3001
```

### Step 10 — Capture graph page (initial load)

Navigate to `/graph` — verify force-directed graph renders with real nodes (tags) and edges.
Should not show "Loading..." or mock placeholder data.

### Step 11 — Interact with the graph

Click a tag node — verify the resource panel opens on the right showing resources tagged with that concept.

### Step 12 — Expand a tag cluster

Double-click or use the expand action on a high-degree node — verify new neighbour nodes load from POST /graph/expand.

### Step 13 — Verify graph updates after new resource

Submit one more resource, wait for processing, then reload `/graph` — verify new tags appear.

### Step 14 — Verify graph sync on deletion (if DEV-027 complete)

Delete a resource from `/resources/{id}` — verify its exclusive tags are removed from the graph on reload.

---

## Expected Outcome

| Step                              | Expected                                                                |
| --------------------------------- | ----------------------------------------------------------------------- |
| GET /graph                        | 200 with real nodes (LLM tags) and edges                                |
| POST /graph/expand                | 200 with neighbour nodes                                                |
| GET /graph/nodes/{id}/resources   | 200 with matching resources                                             |
| Frontend /graph (initial load)    | Force-directed graph renders with real data, not mock                   |
| Click node                        | Resource panel opens with real resources for that tag                   |
| Expand node                       | New neighbour nodes appear dynamically                                  |
| New resource processed            | Graph updates with new tags on reload                                   |
| Resource deleted                  | Orphaned tag nodes removed from graph (if DEV-027 done)                 |

---

## Run History

| Run   | Date | Status | Artifacts |
| ----- | ---- | ------ | --------- |
| (none yet) | — | — | — |

---

## Bugs Found

None yet — not executed.

---

## Next Steps

1. **AI Chat** (Demo 005) — once DEV-053 is complete, the chat panel is wired to the LangGraph agent which can answer questions about saved resources
2. **Performance** — test graph rendering with >50 nodes; revisit react-force-graph-2d settings if needed (Risk #3 in dev plan)
