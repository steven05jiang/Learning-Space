# Demo 001 — First User Journey

**Date:** 2026-03-16
**Status:** ✅ Executed (2 bugs found, CORS fixed inline)
**PRs included:** #25 (login UI), #26 (GET /resources), #28 (submit form), #29 (list view)

---

## Summary

Demonstrates the minimal end-to-end user journey through the Learning Space app:
a user can **log in via OAuth, submit a URL as a resource, and view their resource list**.

This is the first demo where the frontend and backend are integrated — covering the
full stack from the Next.js UI through the FastAPI backend to PostgreSQL.

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
cd apps/api && uv run uvicorn main:app --reload --port 8000
```

FastAPI starts at http://localhost:8000. Swagger UI at http://localhost:8000/docs.

### Step 4 — Verify health endpoint

```
GET /health      → 200 {"status": "healthy", "message": "API is running"}
GET /db-health   → 200 {"status": "database healthy"}
```

### Step 5 — Authenticate (simulate OAuth via direct JWT)

Since OAuth providers require real credentials, we simulate a logged-in user by
minting a JWT directly with the test secret key. This is exactly what the backend
does after a successful OAuth callback.

```bash
cd apps/api && uv run python3 -c "
from core.jwt import create_access_token
token = create_access_token({'sub': '1'})   # user id 1
print(token)
"
```

### Step 6 — List resources via API

```
GET /resources  Authorization: Bearer <token>
→ 200 {"items": [...], "total": N, "limit": 20, "offset": 0}
```

### Step 7 — Create a resource via API

```
POST /resources  Authorization: Bearer <token>
{"content_type": "url", "original_content": "https://..."}
```

⚠️ **BUG-002**: Returns 500 due to timezone-aware datetime passed to
`TIMESTAMP WITHOUT TIME ZONE` column. Tracked in bugs-tracker as BUG-002.

### Step 8 — Start the frontend

```bash
cd apps/web && NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Frontend starts at http://localhost:3000.

---

## Expected Outcome

| Step | Expected |
|------|----------|
| infra-up | All 3 containers healthy |
| migrations | All tables created |
| GET /health | `{"status": "healthy"}` |
| GET /db-health | `{"status": "database healthy"}` |
| GET /resources | 200 paginated list |
| POST /resources | 202 with PENDING resource |
| Frontend /login | Login page with provider buttons |
| Frontend /resources | Resource list page |
| Frontend /resources/new | Submission form |

---

## Actual Outcome

| Step | Result | Artifact |
|------|--------|----------|
| infra-up | ✅ All 3 containers healthy | [01-infra-start.txt](./artifacts/01-infra-start.txt) |
| migrations | ✅ Applied cleanly | [02-migrations.txt](./artifacts/02-migrations.txt) |
| GET /health + /db-health | ✅ 200 both | [03-health.json](./artifacts/03-health.json) |
| API schema | ✅ 9 endpoints registered | [04-api-schema.json](./artifacts/04-api-schema.json) |
| JWT generation | ✅ Token minted for demo user | [05-jwt-token.txt](./artifacts/05-jwt-token.txt) |
| POST /resources | ❌ 500 — BUG-002: datetime timezone mismatch | [06-create-resource.json](./artifacts/06-create-resource.json) |
| GET /resources | ✅ 200 — returns PENDING resource | [07-list-resources.json](./artifacts/07-list-resources.json) |
| Frontend /login | ✅ GitHub / Google / Twitter buttons visible | [08-frontend-login.png](./artifacts/08-frontend-login.png) |
| Frontend /dashboard | ✅ User info, nav, action cards | [09-frontend-dashboard.png](./artifacts/09-frontend-dashboard.png) |
| Frontend /resources/new | ✅ URL input form with submit button | [10-frontend-resources-new.png](./artifacts/10-frontend-resources-new.png) |
| Frontend /resources | ✅ Live resource row: github.com/anthropics URL, PENDING badge, date | [11-frontend-resources-list.png](./artifacts/11-frontend-resources-list.png) |
| Frontend build | ✅ 6 routes compiled (login, dashboard, resources, resources/new, callback, root) | — |

**10 of 11 steps passed. 2 bugs found, CORS fixed inline.**

---

## Bug Found: BUG-002

**Location:** `apps/api/routers/resources.py` lines 64–65

**Root cause:** `create_resource()` explicitly passes `datetime.now(timezone.utc)` (timezone-aware)
to `created_at` and `updated_at`, but the SQLAlchemy model columns are declared as
`Column(DateTime)` — which maps to `TIMESTAMP WITHOUT TIME ZONE` in PostgreSQL.
asyncpg raises `DataError: can't subtract offset-naive and offset-aware datetimes`.

**Fix:** Replace `datetime.now(timezone.utc)` with `datetime.utcnow()` in the router,
or strip tzinfo: `datetime.now(timezone.utc).replace(tzinfo=None)`.
Better long-term fix: change model columns to `DateTime(timezone=True)`.

**Logged as:** BUG-002 in `memory/bugs-tracker.md`

---

## Also Noted: Missing GET /auth/me

DEV-009 (PR #17) was supposed to implement `GET /auth/me` but it does not appear
in the registered routes. The endpoint may have been omitted from the router registration.
Not blocking for this demo but should be verified — logged as BUG-003.

---

## Post-Fix Run — 2026-03-16 17:33

**Context:** Re-ran demo after all 4 bugs were claimed fixed on main:
- BUG-001: JWT migrated to authlib (PR #32)
- BUG-002: POST /resources no longer returns 500 (PR #32)
- BUG-003: GET /auth/me now exists (PR #32)
- BUG-dashboard-svg: SVG has proper width/height (PR #30)

### Verification Results

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Health Check | 200 | ✅ 200 | PASS |
| Database Health | 200 | ✅ 200 | PASS |
| JWT Generation (BUG-001) | Valid authlib token | ✅ Working | **FIXED** |
| GET /auth/me (BUG-003) | 200 with user profile | ❌ 404 Not Found | **NOT FIXED** |
| POST /resources (BUG-002) | 200/201 with resource | ❌ 500 Internal Error | **NOT FIXED** |
| GET /resources | 200 with list | ✅ 200 | PASS |

### Code Analysis

**BUG-001 ✅ ACTUALLY FIXED**
- `core/jwt.py` properly migrated to `authlib.jose`
- JWT tokens generate and validate correctly
- CVE-2024-23342 eliminated

**BUG-002 ❌ NOT ACTUALLY FIXED**
- `routers/resources.py` lines 65-66 still explicitly set `created_at=datetime.now(timezone.utc)`
- Resource model has `default=datetime.utcnow` for both timestamp columns
- The fix (removing explicit datetime args) was reverted in the same commit
- Still causes timezone mismatch error

**BUG-003 ❌ NOT ACTUALLY FIXED**
- No `/auth/me` endpoint exists in `routers/auth.py`
- Returns 404 Not Found
- Was added and then removed in the same commit per commit message

**BUG-dashboard-svg ✅ VERIFIED FIXED**
- Dashboard screenshot shows properly sized SVG icons
- Visual comparison: [original](./artifacts/09-frontend-dashboard.png) vs [fixed](./artifacts/09-frontend-dashboard-fixed.png)

### Updated Screenshots

All frontend pages captured with fixed dashboard SVG:
- [Dashboard (fixed)](./artifacts/09-frontend-dashboard-fixed.png) — SVG icons properly sized
- [Resources New (fixed)](./artifacts/10-frontend-resources-new-fixed.png) — Form renders correctly
- [Resources List (fixed)](./artifacts/11-frontend-resources-list-fixed.png) — List view working

### Test Artifacts

- [Endpoint Test Report](./artifacts/endpoint-test-report-fixed.json) — Detailed API test results
- All screenshots with `-fixed` suffix — Visual proof of current state

**Conclusion:** Only 2 of 4 claimed bug fixes were actually implemented. BUG-002 and BUG-003 require re-opening.

---

## Post-Fix Run (2026-03-16 17:42) — ALL BUGS FIXED

**Context:** Re-ran demo after final fixes merged to main (PR #33).

### Final Verification Results

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Health Check | 200 | ✅ 200 | PASS |
| Database Health | 200 | ✅ 200 | PASS |
| JWT Generation (BUG-001) | Valid authlib token | ✅ Working | **FIXED** |
| GET /auth/me (BUG-003) | 200 with user profile | ✅ 200 `{"id":1,"email":"demo@learningspace.dev","display_name":"Demo User","avatar_url":null}` | **FIXED** |
| POST /resources/ (BUG-002) | 200/202 with resource | ✅ 202 with full resource object | **FIXED** |
| GET /resources/ | 200 with list | ✅ 200 with 2 resources | PASS |

### Final Test Artifacts (All Bugs Fixed)

- [06-create-resource-fixed.json](./artifacts/06-create-resource-fixed.json) — POST /resources/ returns 202 with resource ID
- [auth-me-response.json](./artifacts/auth-me-response.json) — GET /auth/me returns 200 with user profile
- [07-list-resources-fixed.json](./artifacts/07-list-resources-fixed.json) — GET /resources/ returns 200 with resource list
- [09-frontend-dashboard-fixed.png](./artifacts/09-frontend-dashboard-fixed.png) — Dashboard with properly sized SVG icons
- [10-frontend-resources-new-fixed.png](./artifacts/10-frontend-resources-new-fixed.png) — Resources creation form
- [11-frontend-resources-list-fixed.png](./artifacts/11-frontend-resources-list-fixed.png) — Resources list view

**Conclusion:** All 4 bugs have been successfully fixed. The first user journey now works end-to-end.

---

## Next Steps

1. **Real OAuth** — register a GitHub OAuth app pointing to `http://localhost:8000/auth/callback/github`
   to walk through the full browser login flow
2. **Worker pipeline** (DEV-019 → 023) — resources are PENDING but never processed;
   once implemented, resources will auto-populate title/summary/tags
3. **Unit tests** (DEV-011, DEV-018) — required before Tier 2 exit gate
