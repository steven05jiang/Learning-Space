# Demo 001 — First User Journey

**Date:** 2026-03-16
**Status:** ✅ Executed
**PRs included:** #25 (login UI), #26 (GET /resources), #28 (submit form), #29 (list view), #30 (SVG fix), #33 (BUG-001/002/003 fixes)

---

## Summary

Demonstrates the minimal end-to-end user journey through the Learning Space app:
a user can **log in via OAuth, submit a URL as a resource, and view their resource list**.

This is the first demo where the frontend and backend are integrated — covering the
full stack from the Next.js UI through the FastAPI backend to PostgreSQL.

---

## New Since Last Demo

| Type | Item | Description |
|------|------|-------------|
| Feature | DEV-039 | OAuth login UI (GitHub / Google / Twitter) |
| Feature | DEV-014 | GET /resources paginated list |
| Feature | DEV-041 | Submit URL form |
| Feature | DEV-042 | Resource list view |
| Bug fix | BUG-001 | JWT migrated to authlib (CVE-2024-23342) |
| Bug fix | BUG-002 | POST /resources datetime timezone mismatch |
| Bug fix | BUG-003 | GET /auth/me endpoint added |
| Bug fix | BUG-dashboard-svg | SVG icons proper width/height |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Docker running | For PostgreSQL, Neo4j, Redis via `docker compose` |
| `uv` installed | Python dependency manager |
| `npm` installed | Node package manager |
| `.env` in `apps/api/` | Already present with test credentials |
| `NEXT_PUBLIC_API_BASE_URL` | Set to `http://localhost:8000` |

---

## Procedure

### Step 1 — Start infrastructure

```bash
make infra-up
```

Starts PostgreSQL (5432), Neo4j (7474/7687), and Redis (6379) via Docker Compose.

### Step 2 — Run database migrations

```bash
cd apps/api && uv run alembic upgrade head
```

Applies all schema migrations to a fresh PostgreSQL database.

### Step 3 — Start the API server

```bash
cd apps/api && uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

FastAPI starts at http://localhost:8000. Swagger UI at http://localhost:8000/docs.

### Step 4 — Verify health endpoint

```
GET /health      → 200 {"status": "healthy", "message": "API is running"}
GET /db-health   → 200 {"status": "database healthy"}
```

### Step 5 — Authenticate

The login page shows GitHub / Google / Twitter buttons, but clicking them will return
**"Failed to fetch"** because `apps/api/.env` ships with placeholder OAuth credentials
(`test_github_id`, etc.). Choose one of the two options below.

---

#### Option A — JWT shortcut (no setup, recommended for demos)

Mint a token directly from the terminal — this is exactly what the backend issues after
a real OAuth callback:

```bash
cd apps/api
uv run python -c "
from core.jwt import create_access_token
token = create_access_token({'sub': '1', 'email': 'demo@learningspace.dev'})
print(token)
"
```

Then open the browser console at `http://localhost:3001` and paste:

```javascript
localStorage.setItem('auth_token', '<paste token here>')
localStorage.setItem('user_info', JSON.stringify({
  id: 1, email: 'demo@learningspace.dev', display_name: 'Demo User', avatar_url: null
}))
location.href = '/dashboard'
```

You will land directly on the dashboard as the demo user.

---

#### Option B — Real GitHub OAuth (~5 min setup)

1. Go to **GitHub → Settings → Developer settings → OAuth Apps → New OAuth App**
2. Fill in:
   - **Homepage URL:** `http://localhost:3001`
   - **Authorization callback URL:** `http://localhost:8000/auth/callback/github`
3. Copy the **Client ID** and generate a **Client Secret**
4. Update `apps/api/.env`:
   ```
   GITHUB_CLIENT_ID=<your real client id>
   GITHUB_CLIENT_SECRET=<your real client secret>
   ```
5. Restart the API server — the "Continue with GitHub" button will complete the full browser OAuth flow

> Google and Twitter require the same pattern via their respective developer consoles,
> but GitHub is the fastest to register.

### Step 6 — Verify authenticated user

```
GET /auth/me  Authorization: Bearer <token>
→ 200 {"id": ..., "email": "demo@learningspace.dev", ...}
```

### Step 7 — Create a resource via API

```
POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://github.com/anthropics/anthropic-sdk-python"}
→ 202 ACCEPTED with resource object
```

### Step 8 — List resources via API

```
GET /resources  Authorization: Bearer <token>
→ 200 {"items": [...], "total": N, "limit": 20, "offset": 0}
```

### Step 9 — Start the frontend

```bash
cd apps/web && npm run dev -- --port 3001
```

Frontend starts at http://localhost:3001.

### Step 10 — Capture frontend screenshots

Pages to capture: `/login`, `/dashboard`, `/resources/new`, `/resources`.

---

## Expected Outcome

| Step | Expected |
|------|----------|
| infra-up | All 3 containers healthy |
| migrations | All tables created |
| GET /health | `{"status": "healthy"}` |
| GET /db-health | `{"status": "database healthy"}` |
| GET /auth/me | 200 with user profile |
| POST /resources | 202 with PENDING resource |
| GET /resources | 200 paginated list |
| Frontend /login | Login page with provider buttons |
| Frontend /dashboard | Dashboard with nav and action cards |
| Frontend /resources/new | URL submission form |
| Frontend /resources | Resource list with PENDING badge |

---

## Run History

| Run | Date | Status | Artifacts |
|-----|------|--------|-----------|
| run-2 | 2026-03-16 22:13 | ✅ | [artifacts/run-2/](./artifacts/run-2/) |

---

### Run 2 — 2026-03-16

| Step | Result | Artifact |
|------|--------|----------|
| infra-up | ✅ All 3 containers healthy | [01-infra-start.txt](./artifacts/run-2/01-infra-start.txt) |
| migrations | ✅ Applied cleanly (up to date) | [02-migrations.txt](./artifacts/run-2/02-migrations.txt) |
| GET /health + /db-health | ✅ 200 both | [03-health.json](./artifacts/run-2/03-health.json) |
| JWT generation | ✅ Token minted for demo user | [05-jwt-token.txt](./artifacts/run-2/05-jwt-token.txt) |
| GET /auth/me | ✅ 200 `{"id":1,"email":"demo@learningspace.dev","display_name":"Demo User","avatar_url":null}` | [06-auth-me.json](./artifacts/run-2/06-auth-me.json) |
| POST /resources | ✅ 202 with PENDING resource (id=4) | [07-create-resource.json](./artifacts/run-2/07-create-resource.json) |
| GET /resources | ✅ 200 — 4 resources listed | [08-list-resources.json](./artifacts/run-2/08-list-resources.json) |
| Frontend /login | ✅ Login page with OAuth provider buttons | [09-frontend-login.png](./artifacts/run-2/09-frontend-login.png) |
| Frontend /dashboard | ✅ Dashboard with nav and action cards | [10-frontend-dashboard.png](./artifacts/run-2/10-frontend-dashboard.png) |
| Frontend /resources/new | ✅ URL submission form | [11-frontend-resources-new.png](./artifacts/run-2/11-frontend-resources-new.png) |
| Frontend /resources | ✅ Resource list with PENDING badges | [12-frontend-resources-list.png](./artifacts/run-2/12-frontend-resources-list.png) |

**11 of 11 steps passed. 0 bugs found.**

---

## Bugs Found

None — all steps passed.

---

## Next Steps

1. **Real OAuth** — register a GitHub OAuth app pointing to `http://localhost:8000/auth/callback/github`
   to walk through the full browser login flow
2. **Worker pipeline** (DEV-019 → 023) — resources are PENDING but never processed;
   once implemented, resources will auto-populate title/summary/tags
3. **Unit tests** (DEV-011, DEV-018) — required before Tier 2 exit gate
