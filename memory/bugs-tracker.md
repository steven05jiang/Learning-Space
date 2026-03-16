# Bugs Tracker

**Scope:** Bug reports, defects, regressions
**Task prefix:** `BUG-`
**Initialized:** 2026-03-15
**Last Updated:** 2026-03-16

---

## Progress Summary
- Total: 5 tasks
- ✅ Fixed: 5
- 🔄 Active: 0
- ⏳ Pending: 0
- ⚠️ Stuck: 0

---

## Bugs

- [x] BUG-001: Migrate JWT from python-jose to authlib — CVE-2024-23342 eliminated; migrated core/jwt.py to authlib.jose (PR #32 ✅)
- [x] BUG-002: POST /resources returns 500 — removed timezone-aware datetime args from Resource() constructor; ORM defaults handle timestamps (PR #33 ✅)
- [x] BUG-003: GET /auth/me endpoint missing — added endpoint to routers/auth.py with tests (PR #33 ✅)
- [x] BUG-004: No CORS middleware — fixed inline during demo 001 (added CORSMiddleware to main.py, cors_origins to config)
- [x] BUG-dashboard-svg: Dashboard SVG icon renders oversized without CSS — added width="20" height="20" to inline SVG in dashboard/page.tsx (PR #30 ✅)
