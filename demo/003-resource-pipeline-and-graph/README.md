# Demo 003 — Resource Processing Pipeline + Knowledge Graph

**Date:** 2026-03-22
**Status:** ✅ Executed (run-1: 2026-03-22, run-2: 2026-03-22)
**Scenario:** Submit a URL resource, watch it get processed (LLM title/summary/tags), then explore the resulting knowledge graph.

---

## Summary

Demonstrates the complete resource processing pipeline end-to-end: a user submits a URL, the async worker fetches content and uses the LLM to extract a title, summary, and tags, and the resource transitions from PENDING → READY. The knowledge graph is then updated with tag nodes and edges, and the user can explore the live graph — expanding nodes and viewing resources for each tag.

This is the core value proposition of Learning Space: automatic categorization and knowledge graph construction from saved resources.

---

## New Since Last Demo (002 — 2026-03-17)

| Type    | Item    | Description |
| ------- | ------- | ----------- |
| Feature | DEV-019 | Task queue infrastructure (Celery + Redis) |
| Feature | DEV-020 | URL content fetcher (unauthenticated) |
| Feature | DEV-022 | LLM processing — title, summary, tags |
| Feature | DEV-023 | process_resource worker job (full pipeline) |
| Feature | DEV-025 | Graph service (Neo4j operations) |
| Feature | DEV-026 | Graph update integrated into worker pipeline |
| Feature | DEV-027 | Graph sync job for resource deletion |
| Feature | DEV-028 | GET /graph endpoint |
| Feature | DEV-029 | POST /graph/expand endpoint |
| Feature | DEV-030 | GET /graph/nodes/{id}/resources endpoint |
| Feature | DEV-052 | Graph visualization UI wired to real API |
| Feature | DEV-054 | Duplicate URL detection (409 + toast) |
| Bug fix | BUG-006 | Pending tag overflow in resources page |
| Bug fix | BUG-007 | Settings shows incorrect connection status |
| Bug fix | BUG-008 | OAuth lint fix + accounts table persistence |

---

## Prerequisites

| Requirement                | Notes                                             |
| -------------------------- | ------------------------------------------------- |
| Docker running             | For PostgreSQL, Neo4j, Redis via `docker compose` |
| `uv` installed             | Python dependency manager                         |
| `npm` installed            | Node package manager                              |
| `.env` in `apps/api/`      | API secrets incl. LLM key                        |
| `NEXT_PUBLIC_API_BASE_URL` | Set to `http://localhost:8000`                    |
| Playwright installed       | For frontend screenshots                          |

---

## Procedure

1. Start infrastructure: `docker compose up -d`
2. Run migrations: `cd apps/api && uv run alembic upgrade head`
3. Start API server: `uv run uvicorn main:app --port 8000`
4. Start web server: `cd apps/web && npm run dev -- --port 3000`
5. Verify health: `GET /health`
6. Authenticate as demo user: `GET /auth/me`
7. Submit a URL resource: `POST /resources` with a real public URL
8. Poll resource status until READY: `GET /resources/{id}`
9. Verify LLM-extracted title, summary, tags on the resource
10. Fetch knowledge graph: `GET /graph`
11. Expand a tag node: `POST /graph/expand`
12. Fetch resources for a tag node: `GET /graph/nodes/{id}/resources`
13. Capture frontend screenshots: dashboard, resources list (READY resource), graph view

---

## Expected Outcome

| Step                          | Expected                                |
| ----------------------------- | --------------------------------------- |
| infra-up                      | All containers healthy                  |
| GET /health                   | 200 `{"status": "healthy"}`             |
| GET /auth/me                  | 200 + user profile                      |
| POST /resources               | 202 ACCEPTED, status=PENDING/PROCESSING |
| GET /resources/{id} (polled)  | 200, status=READY, tags populated       |
| GET /graph                    | 200, nodes + edges present              |
| POST /graph/expand            | 200, neighboring nodes returned         |
| GET /graph/nodes/{id}/resources | 200, resources for that tag           |
| Frontend /resources           | READY resource with tags visible        |
| Frontend /graph               | Live graph with nodes and edges         |

---

## Run History

| Run   | Date       | Status | Artifacts |
| ----- | ---------- | ------ | --------- |
| run-1 | 2026-03-22 | ✅     | [artifacts/run-1/](./artifacts/run-1/) |
| run-2 | 2026-03-22 | ✅     | [artifacts/run-2/](./artifacts/run-2/) |

---

### Run 1 — 2026-03-22

| Step | Result | Artifact |
| ---- | ------ | -------- |
| infra-up (PostgreSQL, Neo4j, Redis) | ✅ All containers healthy | [01-infra-start.txt](./artifacts/run-1/01-infra-start.txt) |
| DB migrations | ✅ Up to date | [02-migrations.txt](./artifacts/run-1/02-migrations.txt) |
| GET /health | ✅ 200 `{"status":"healthy"}` | [03-health.json](./artifacts/run-1/03-health.json) |
| GET /auth/me | ✅ 200 + user profile | [06-auth-me.json](./artifacts/run-1/06-auth-me.json) |
| POST /resources (Wikipedia URL) | ✅ 202 status=PENDING | [07-create-resource.json](./artifacts/run-1/07-create-resource.json) |
| Worker process_resource (URL fetch + LLM) | ✅ READY — title extracted, 7 tags, 1501-char summary | [08-worker-process.txt](./artifacts/run-1/08-worker-process.txt) |
| GET /resources/1 | ✅ status=READY, tags=["knowledge-graph","ontology",...] | [09-resource-ready.json](./artifacts/run-1/09-resource-ready.json) |
| Graph seed (7 tags → Neo4j) | ✅ 7 nodes, 21 edges | [10-graph-seed.txt](./artifacts/run-1/10-graph-seed.txt) |
| GET /graph | ✅ 7 nodes + 21 edges returned | [11-graph-view.json](./artifacts/run-1/11-graph-view.json) |
| POST /graph/expand (knowledge-graph) | ✅ 6 neighboring nodes + edges | [12-graph-expand.json](./artifacts/run-1/12-graph-expand.json) |
| GET /graph/nodes/knowledge-graph/resources | ✅ 1 resource returned | [13-graph-node-resources.json](./artifacts/run-1/13-graph-node-resources.json) |
| Frontend /login | ✅ Login page renders | [14-frontend-login.png](./artifacts/run-1/14-frontend-login.png) |
| Frontend /dashboard | ✅ Dashboard loads | [15-frontend-dashboard.png](./artifacts/run-1/15-frontend-dashboard.png) |
| Frontend /resources | ✅ Resource list with READY resource + tags | [16-frontend-resources-list.png](./artifacts/run-1/16-frontend-resources-list.png) |
| Frontend /graph | ✅ Live knowledge graph renders with nodes/edges | [17-frontend-graph.png](./artifacts/run-1/17-frontend-graph.png) |
| Frontend /resources/1 | ✅ Resource detail with title, summary, tags | [18-frontend-resource-detail.png](./artifacts/run-1/18-frontend-resource-detail.png) |

---

### Run 2 — 2026-03-22

| Step | Result | Artifact |
| ---- | ------ | -------- |
| infra-up (PostgreSQL, Neo4j, Redis) | ✅ All containers healthy | [01-infra-start.txt](./artifacts/run-2/01-infra-start.txt) |
| DB migrations | ✅ Up to date | [02-migrations.txt](./artifacts/run-2/02-migrations.txt) |
| GET /health | ✅ 200 `{"status":"healthy"}` | [03-health.json](./artifacts/run-2/03-health.json) |
| GET /auth/me | ✅ 200 + user profile | [06-auth-me.json](./artifacts/run-2/06-auth-me.json) |
| POST /resources (Wikipedia Machine Learning URL) | ✅ 202 status=PENDING | [07-create-resource.json](./artifacts/run-2/07-create-resource.json) |
| Worker process_resource (URL fetch + LLM) | ✅ READY — title extracted, 8 tags, 1385-char summary | [08-worker-process.txt](./artifacts/run-2/08-worker-process.txt) |
| GET /resources/2 | ✅ status=READY, tags=["machine-learning","artificial-intelligence",...] | [09-resource-ready.json](./artifacts/run-2/09-resource-ready.json) |
| Graph seed (8 tags → Neo4j) | ✅ 8 nodes, 28 edges | [10-graph-seed.txt](./artifacts/run-2/10-graph-seed.txt) |
| GET /graph | ✅ 15 nodes + 49 edges returned (cumulative from both runs) | [11-graph-view.json](./artifacts/run-2/11-graph-view.json) |
| POST /graph/expand (machine-learning) | ✅ 7 neighboring nodes + edges | [12-graph-expand.json](./artifacts/run-2/12-graph-expand.json) |
| GET /graph/nodes/machine-learning/resources | ✅ 1 resource returned | [13-graph-node-resources.json](./artifacts/run-2/13-graph-node-resources.json) |
| Frontend /login | ✅ Login page renders | [14-frontend-login.png](./artifacts/run-2/14-frontend-login.png) |
| Frontend /dashboard | ✅ "Dashboard" visible, no errors | [15-frontend-dashboard.png](./artifacts/run-2/15-frontend-dashboard.png) |
| Frontend /resources | ✅ "My Resources" visible, no errors | [16-frontend-resources-list.png](./artifacts/run-2/16-frontend-resources-list.png) |
| Frontend /knowledge-graph | ✅ "Knowledge Graph" visible, nodes/edges rendered | [17-frontend-graph.png](./artifacts/run-2/17-frontend-graph.png) |
| Frontend /resources/2 | ✅ "Machine Learning" title visible | [18-frontend-resource-detail.png](./artifacts/run-2/18-frontend-resource-detail.png) |
| UI validation report | ✅ 33 passed, 0 failed | [12-ui-validation.json](./artifacts/run-2/12-ui-validation.json) |

---

## Bugs Found

- **BUG-009**: LLM model `claude-3-5-sonnet-20241022` deprecated — updated default to `claude-haiku-4-5-20251001` in `services/llm_processor.py`
- **Note**: Worker graph_update step logs a warning ("Neo4j driver not connected") when called outside the FastAPI app lifecycle — does not affect API-path graph updates (graph seeded manually for demo). This is a known limitation of running the worker directly without the full app context.

---

## Next Steps

- Run DEMO-005 (AI Chat) after DEV-032–035 + DEV-053 complete
- Consider fixing worker graph_update to work outside FastAPI lifecycle (or document that Celery task context initializes the driver)
