# Demo 005 — AI Chat (LangGraph Agent)

**Status:** ⏳ Pending execution
**Planned after:** DEV-032, DEV-033, DEV-034, DEV-035, DEV-053 complete

---

## Summary

Demonstrates the AI chat assistant in Learning Space.
A user can **ask natural language questions about their saved resources**, and the LangGraph agent **searches the knowledge graph and resource database to generate grounded answers** — citing actual saved content.

This is the final Tier 3 demo and the last step before Milestone 3 (Feature Complete). After this, the full end-to-end journey is live: save → process → explore graph → chat.

---

## New Since Last Demo (004)

| Type    | Item    | Description                                                              |
| ------- | ------- | ------------------------------------------------------------------------ |
| Feature | DEV-035 | Conversation storage (DB schema) — persist chat history per user         |
| Feature | DEV-032 | LangGraph agent with tools — resource search + graph query tools         |
| Feature | DEV-033 | POST /chat endpoint — send a message, get a streamed/sync response       |
| Feature | DEV-034 | GET /chat/conversations and messages — retrieve conversation history      |
| Feature | DEV-053 | Wire chat UI to real API (replacing mock data in the Sparkles panel)     |

---

## Prerequisites

| Requirement                     | Notes                                                        |
| ------------------------------- | ------------------------------------------------------------ |
| Docker running                  | For PostgreSQL, Neo4j, Redis via `docker compose`            |
| `uv` installed                  | Python dependency manager                                    |
| `npm` installed                 | Node package manager                                         |
| `.env` in `apps/api/`           | Present with valid `ANTHROPIC_API_KEY` for LangGraph agent   |
| `NEXT_PUBLIC_API_BASE_URL`      | Set to `http://localhost:8000`                               |
| Worker running                  | Required for resource processing                             |
| ≥5 processed resources in DB    | Run Demo 003/004 first to build knowledge base               |

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

### Step 5 — Verify chat endpoint basics

```
POST /chat  Authorization: Bearer <token>
{"message": "Hello, what can you help me with?"}
→ 200 {"reply": "...", "conversation_id": "<uuid>"}
```

### Step 6 — Ask a question about saved resources

Ask a question related to URLs submitted in earlier demos:

```
POST /chat  Authorization: Bearer <token>
{"message": "What do I know about LangGraph?", "conversation_id": "<uuid>"}
→ 200 {"reply": "<answer citing saved resources>", "conversation_id": "<uuid>"}
```

Verify the reply references actual saved content (not hallucinated).

### Step 7 — Continue the conversation (multi-turn)

```
POST /chat  Authorization: Bearer <token>
{"message": "How does it compare to other agent frameworks?", "conversation_id": "<uuid>"}
→ 200 {"reply": "...", "conversation_id": "<uuid>"}
```

Verify the agent uses conversation context (references the previous LangGraph question).

### Step 8 — Ask a knowledge graph question

```
POST /chat  Authorization: Bearer <token>
{"message": "Which topics appear most frequently in my saved resources?", "conversation_id": "<uuid>"}
→ 200 {"reply": "Based on your knowledge graph, the most common topics are: ..."}
```

Verify the agent queries the graph, not just raw resource text.

### Step 9 — Retrieve conversation history

```
GET /chat/conversations  Authorization: Bearer <token>
→ 200 {"items": [{"id": "<uuid>", "created_at": "...", "message_count": N}], ...}

GET /chat/conversations/{id}/messages  Authorization: Bearer <token>
→ 200 {"items": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]}
```

### Step 10 — Start the frontend

```bash
cd apps/web && npm run dev -- --port 3001
```

### Step 11 — Open the chat panel (Sparkles toggle)

Navigate to `/dashboard` or `/graph` — click the Sparkles (✨) button to open the chat panel.
Verify the panel connects to the real API (not mock data — should show empty state or previous conversation).

### Step 12 — Chat via UI

Type a question in the chat input — verify:
1. Message appears in the panel
2. Agent response streams in (or appears after a moment)
3. Response cites relevant saved resources

### Step 13 — Reload and verify persistence

Close and reopen the chat panel — verify previous conversation is loaded from the database (not lost on page reload).

### Step 14 — Capture screenshots

Pages to capture:
- Chat panel open on `/graph` showing a multi-turn conversation with real answers
- Chat panel showing a response that references a specific saved resource

---

## Expected Outcome

| Step                              | Expected                                                               |
| --------------------------------- | ---------------------------------------------------------------------- |
| POST /chat                        | 200 with agent reply and conversation_id                               |
| Question about saved resources    | Reply cites actual saved content, not hallucination                    |
| Multi-turn conversation           | Agent maintains context across messages                                |
| Graph query question              | Agent retrieves graph data and summarizes topics                       |
| GET /chat/conversations           | 200 with conversation list                                             |
| GET /chat/conversations/{id}/msgs | 200 with full message history                                          |
| Frontend chat panel               | Connected to real API — sends messages, receives agent replies         |
| Reload persistence                | Previous conversation reloads from DB                                  |

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

1. **Milestone 3 — Feature Complete** — all Tier 3 tasks are done; exit gate passes
2. **Tier 4 — Hardening** — Dockerfiles (DEV-047), Helm chart (DEV-048), ArgoCD (DEV-049), integration tests (DEV-050, DEV-051)
3. **LangSmith tracing** — enable tracing for the LangGraph agent to observe tool call quality in production (Risk #1 in dev plan)
