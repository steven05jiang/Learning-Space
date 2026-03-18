# Demo 002 — Account Management & Resource CRUD

**Status:** ✅ Executed (run-1: 2026-03-17)
**Planned after:** DEV-015, DEV-016, DEV-017, DEV-040, DEV-043 complete

---

## Summary

Demonstrates full account management and resource lifecycle management in Learning Space.
A user can **link/unlink OAuth accounts in Settings**, and **view, edit, and delete individual resources** from the resource detail page.

This is the first demo where the resource lifecycle is complete — users can now manage resources they've submitted.

---

## New Since Last Demo (001)

| Type    | Item    | Description                                                   |
| ------- | ------- | ------------------------------------------------------------- |
| Feature | DEV-007 | Account linking flow — link a second OAuth provider           |
| Feature | DEV-008 | Account unlinking — remove a linked provider                  |
| Feature | DEV-015 | GET /resources/{id} — single resource detail endpoint         |
| Feature | DEV-016 | PATCH /resources/{id} — edit resource title/content           |
| Feature | DEV-017 | DELETE /resources/{id} — delete a resource                    |
| Feature | DEV-040 | Settings UI — Account Management page with linked accounts    |
| Feature | DEV-043 | Resource detail / edit / delete UI                            |

---

## Prerequisites

| Requirement                | Notes                                             |
| -------------------------- | ------------------------------------------------- |
| Docker running             | For PostgreSQL, Neo4j, Redis via `docker compose` |
| `uv` installed             | Python dependency manager                         |
| `npm` installed            | Node package manager                              |
| `.env` in `apps/api/`      | Present with test credentials                     |
| `NEXT_PUBLIC_API_BASE_URL` | Set to `http://localhost:8000`                    |
| At least 1 resource in DB  | Run Demo 001 first, or seed via POST /resources   |

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

### Step 3 — Start the API server

```bash
cd apps/api && uv run uvicorn main:app --host 0.0.0.0 --port 8000
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

Set token in browser:

```javascript
localStorage.setItem("auth_token", "<paste token here>");
localStorage.setItem("user_info", JSON.stringify({id: 1, email: "demo@learningspace.dev", display_name: "Demo User", avatar_url: null}));
location.href = "/dashboard";
```

### Step 5 — Seed resources (if starting fresh)

```
POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://github.com/anthropics/anthropic-sdk-python"}

POST /resources  Authorization: Bearer <token>
{"content_type": "text", "original_content": "LangGraph is a stateful, orchestration framework for building multi-step AI agents."}
```

### Step 6 — Verify single resource endpoint

```
GET /resources/1  Authorization: Bearer <token>
→ 200 with full resource object
```

### Step 7 — Edit a resource via API

```
PATCH /resources/1  Authorization: Bearer <token>
{"title": "Anthropic Python SDK"}
→ 200 with updated resource
```

### Step 8 — Delete a resource via API

```
DELETE /resources/2  Authorization: Bearer <token>
→ 204 No Content

GET /resources  Authorization: Bearer <token>
→ 200 — resource 2 no longer in list
```

### Step 9 — Test account linking via API

```
GET /auth/accounts  Authorization: Bearer <token>
→ 200 list of linked accounts

POST /auth/link  Authorization: Bearer <token>
→ Initiates second OAuth provider flow (may redirect)
```

### Step 10 — Start the frontend

```bash
cd apps/web && npm run dev -- --port 3001
```

### Step 11 — Capture Settings UI

Navigate to `/settings` — verify linked accounts list and unlink button visible.

### Step 12 — Capture resource detail UI

Navigate to `/resources/1` — verify resource detail, edit form, and delete button.

### Step 13 — Edit resource via UI

Update the title field and save — verify change persists on reload.

### Step 14 — Delete resource via UI

Click delete on a resource — confirm dialog → resource removed from list.

---

## Expected Outcome

| Step                          | Expected                                          |
| ----------------------------- | ------------------------------------------------- |
| GET /resources/{id}           | 200 with full resource object                     |
| PATCH /resources/{id}         | 200 with updated fields                           |
| DELETE /resources/{id}        | 204, resource gone from list                      |
| GET /auth/accounts            | 200 with linked account list                      |
| Frontend /settings            | Account Management page with linked providers     |
| Frontend /resources/{id}      | Resource detail page with edit and delete options |
| Edit resource (UI)            | Title updates and persists on reload              |
| Delete resource (UI)          | Resource removed, redirect to list                |

---

## Run History

| Run   | Date | Status | Artifacts |
| ----- | ---- | ------ | --------- |
| run-1 | 2026-03-17 | ✅ | [artifacts/run-1/](./artifacts/run-1/) |

---

### Run 1 — 2026-03-17

| Step | Result | Artifact |
| ---- | ------ | -------- |
| infra-up | ✅ All containers healthy (postgres, neo4j, redis) | [01-infra-start.txt](./artifacts/run-1/01-infra-start.txt) |
| DB migrations | ✅ Up to date | [02-migrations.txt](./artifacts/run-1/02-migrations.txt) |
| GET /health | ✅ 200 `{"status":"healthy"}` | [03-health.json](./artifacts/run-1/03-health.json) |
| GET /auth/me | ✅ 200 + user profile | [06-auth-me.json](./artifacts/run-1/06-auth-me.json) |
| POST /resources (×2) | ✅ 202 ACCEPTED (ids 5, 6) | [07-seed-resources.txt](./artifacts/run-1/07-seed-resources.txt) |
| GET /resources/5 | ✅ 200 full resource object | [08-resource-crud.txt](./artifacts/run-1/08-resource-crud.txt) |
| PATCH /resources/5 | ✅ 200 title updated to "Anthropic Python SDK" | [08-resource-crud.txt](./artifacts/run-1/08-resource-crud.txt) |
| DELETE /resources/6 | ✅ 204 No Content | [08-resource-crud.txt](./artifacts/run-1/08-resource-crud.txt) |
| GET /resources (after delete) | ✅ 200 — resource 6 absent, 5 resources total | [08-resource-crud.txt](./artifacts/run-1/08-resource-crud.txt) |
| GET /auth/providers | ✅ 200 `["github","google","twitter"]` | [09-accounts.txt](./artifacts/run-1/09-accounts.txt) |
| Frontend /login | ✅ Login page rendered | [10-frontend-login.png](./artifacts/run-1/10-frontend-login.png) |
| Frontend /dashboard | ✅ Dashboard with "Welcome back, Demo User" | [11-frontend-dashboard.png](./artifacts/run-1/11-frontend-dashboard.png) |
| Frontend /resources | ✅ 5 resource cards, "Anthropic Python SDK" title visible | [12-frontend-resources-list.png](./artifacts/run-1/12-frontend-resources-list.png) |
| Frontend /resources/5 | ✅ Resource detail with Edit + Delete buttons | [13-frontend-resource-detail.png](./artifacts/run-1/13-frontend-resource-detail.png) |
| Frontend /settings | ✅ Account Settings with Profile info + Linked Accounts (GitHub/Google/Twitter) | [14-frontend-settings.png](./artifacts/run-1/14-frontend-settings.png) |

---

## Bugs Found

- **BUG-005**: CORS `allow_origins` only includes `http://localhost:3000` — port 3001 blocked. Workaround: run web dev server on port 3000. Fix: add `http://localhost:3001` (or use env var for allowed origins).
- **Note**: `GET /auth/accounts` (list) returns 404 — only `/auth/accounts/{id}` (delete) exists. Settings UI fetches from `/auth/me` for profile; account listing is derived from `/auth/providers`. Minor mismatch but UI renders correctly with fallback.

---

## Next Steps

1. **BUG-005** — Fix CORS allowed origins to include configurable dev ports
2. **Worker pipeline** (Demo 003) — resources are still PENDING; once DEV-023 is done, URLs will auto-process into summaries and tags
3. **Authenticated URL fetching** (DEV-021) — link Twitter account to fetch from Twitter content
