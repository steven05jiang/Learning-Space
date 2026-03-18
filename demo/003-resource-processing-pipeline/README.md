# Demo 003 — Automated Resource Processing Pipeline

**Status:** ⏳ Pending execution
**Planned after:** DEV-019, DEV-020, DEV-022, DEV-023 complete
(DEV-021 optional — authenticated URL fetching for Twitter content)

---

## Summary

Demonstrates the async resource processing pipeline in Learning Space.
A user submits a URL, and within seconds the system **auto-fetches the page content, generates a title, summary, and tags via LLM**, and updates the resource status from `PENDING` to `PROCESSED`.

This is the first demo where resources become genuinely useful — the AI enrichment loop is live.

---

## New Since Last Demo (002)

| Type    | Item    | Description                                                        |
| ------- | ------- | ------------------------------------------------------------------ |
| Feature | DEV-019 | Task queue infrastructure — async job dispatch via Celery/ARQ      |
| Feature | DEV-020 | URL content fetcher (unauthenticated) — fetch raw page text        |
| Feature | DEV-022 | LLM processing — generate title, summary, and tags via Claude API  |
| Feature | DEV-023 | process_resource job — ties fetch + LLM + DB update into one task  |
| Feature | DEV-021 | (optional) Authenticated URL fetcher — fetch Twitter/X content     |

---

## Prerequisites

| Requirement                | Notes                                                   |
| -------------------------- | ------------------------------------------------------- |
| Docker running             | For PostgreSQL, Neo4j, Redis via `docker compose`       |
| `uv` installed             | Python dependency manager                               |
| `npm` installed            | Node package manager                                    |
| `.env` in `apps/api/`      | Present with valid `ANTHROPIC_API_KEY` for LLM calls    |
| `NEXT_PUBLIC_API_BASE_URL` | Set to `http://localhost:8000`                          |
| Worker process running     | See Step 4 — worker must be running to process jobs     |

---

## Procedure

### Step 1 — Start infrastructure

```bash
make infra-up
```

Redis is required for the task queue broker.

### Step 2 — Run database migrations

```bash
cd apps/api && uv run alembic upgrade head
```

### Step 3 — Start the API server

```bash
cd apps/api && uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 4 — Start the worker process

```bash
cd apps/api && uv run celery -A worker.celery_app worker --loglevel=info
```

(Command may vary depending on task queue implementation — adjust to match DEV-019 worker entrypoint.)

### Step 5 — Authenticate (JWT shortcut)

```bash
cd apps/api
uv run python -c "
from core.jwt import create_access_token
token = create_access_token({'sub': '1', 'email': 'demo@learningspace.dev'})
print(token)
"
```

### Step 6 — Submit a URL resource

```
POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://anthropic.com/research/claude"}
→ 202 ACCEPTED — status: PENDING
```

### Step 7 — Observe processing (API polling)

Poll every 2 seconds until status transitions:

```
GET /resources/{id}  Authorization: Bearer <token>
→ status: PENDING  (initial)
→ status: FETCHING (fetching page content)
→ status: PROCESSING (LLM generating summary)
→ status: PROCESSED (done — title, summary, tags populated)
```

### Step 8 — Inspect enriched resource

```
GET /resources/{id}  Authorization: Bearer <token>
→ 200 {
    "title": "<LLM-generated title>",
    "summary": "<LLM-generated summary>",
    "tags": ["<tag1>", "<tag2>", ...],
    "status": "PROCESSED"
  }
```

### Step 9 — Submit a text resource

```
POST /resources  Authorization: Bearer <token>
{"content_type": "text", "original_content": "LangGraph is a stateful orchestration framework for multi-step LLM agents..."}
→ 202 ACCEPTED — status: PENDING
```

Verify text resources also get summarized and tagged (no fetch step needed — content already present).

### Step 10 — (Optional) Authenticated URL fetching

If DEV-021 is complete and a Twitter account is linked:

```
POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://x.com/AnthropicAI/status/<tweet_id>"}
→ 202 ACCEPTED
```

Verify the tweet content is fetched using the linked Twitter credentials.

### Step 11 — Start the frontend and capture resource list

```bash
cd apps/web && npm run dev -- --port 3001
```

Navigate to `/resources` — verify resources show `PROCESSED` status with auto-generated title/summary/tags visible.

### Step 12 — Capture resource detail with enriched content

Navigate to `/resources/{id}` — verify title, summary, and tags are displayed.

---

## Expected Outcome

| Step                              | Expected                                                       |
| --------------------------------- | -------------------------------------------------------------- |
| POST /resources (URL)             | 202, status: PENDING                                           |
| Worker logs                       | Fetch + LLM pipeline logged                                    |
| GET /resources/{id} (after ~5s)   | status: PROCESSED, title/summary/tags populated                |
| POST /resources (text)            | 202 → PROCESSED without fetch step                             |
| Frontend /resources               | Resources show PROCESSED badge with auto-generated content     |
| Frontend /resources/{id}          | Full enriched resource detail visible                          |

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

1. **Knowledge graph** (Demo 004) — processed resources generate tags which populate the graph; once DEV-052 is wired, the graph UI will show real data
2. **Graph sync on deletion** (DEV-027) — deleting a resource should clean up its graph nodes
