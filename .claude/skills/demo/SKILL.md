---
name: demo
description: >
  Creates and executes demos for the Learning Space app. Use this skill whenever the user
  wants to run a demo, capture screenshots of the running app, document a user journey, or create
  demo artifacts. Trigger when the user says things like "create a demo", "run the demo",
  "capture screenshots", "demonstrate the app", "show me the app running", or "add a new demo".
  Supports two modes: --new (propose + define a new demo), --execute <NNN> (run an existing demo).
---

# Demo

Two modes:

| Mode | Usage | What it does |
|------|-------|-------------|
| `--new` | `/demo --new` | Reads dev-tracker.md to propose a new demo scenario. User approves goal. Writes the demo README. Does NOT execute. |
| `--execute <NNN>` | `/demo --execute 001` | Executes a demo that already has a README. Saves artifacts under a versioned run subfolder. |

If the user says "create and run a demo" or similar — run `--new` first, get approval, then
automatically proceed to `--execute` for the new demo number.

---

## MODE A — `--new`: Define a New Demo

### A1 — Find the last demo

```bash
ls demo/ 2>/dev/null | sort
```

Note the highest existing number (e.g. `001`). The new demo will be `002`, etc.

Also note the **date of the last demo** from that folder's `README.md` header.

### A2 — Identify what's changed since the last demo

Read `memory/dev-tracker.md`. Find all tasks marked `[x]` (completed) that were completed
**after** the last demo date (check their `memory/completed/DEV-XXX.md` for completion date).

Also check `memory/bugs-tracker.md` for any bugs fixed since then.

Summarize the delta:

```
New since demo 001 (2026-03-16):
  Features: DEV-039 (OAuth login UI), DEV-014 (GET /resources), DEV-041 (submit form), DEV-042 (resource list view)
  Bug fixes: BUG-001 (JWT authlib), BUG-002 (datetime fix), BUG-003 (/auth/me), BUG-dashboard-svg
```

### A3 — Propose demo goal

Based on the delta, propose a demo scenario that shows the most meaningful user-visible progress.
Prioritize end-to-end user journeys over isolated API tests. Output:

```
📋 Demo Proposal — Demo <NNN>
==============================

New features since last demo:
  • <feature 1>
  • <feature 2>

Proposed scenario: "<short title>"

Goal: <1-2 sentences describing what a user will see / do>

Pages / endpoints covered:
  • <page or endpoint 1>
  • <page or endpoint 2>

Approve this demo goal? (yes / adjust / skip)
```

**Wait for user approval before proceeding.**

- If "adjust" — ask what to change and re-propose.
- If "skip" — stop.
- If "yes" — continue to A4.

### A4 — Create the demo folder and README

Derive a short kebab-case slug from the approved goal (e.g. `resource-processing-pipeline`).

```bash
mkdir -p demo/<NNN>-<slug>/artifacts
```

Write `demo/<NNN>-<slug>/README.md`:

```markdown
# Demo <NNN> — <Title>

**Date:** YYYY-MM-DD
**Status:** 📝 Defined (not yet executed)
**Scenario:** <one-sentence description>

---

## Summary

<2-3 sentences: what this demo shows, why it matters>

---

## New Since Last Demo

| Type | Item | Description |
|------|------|-------------|
| Feature | DEV-XXX | <title> |
| Bug fix | BUG-XXX | <title> |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Docker running | For PostgreSQL, Neo4j, Redis via `docker compose` |
| `uv` installed | Python dependency manager |
| `npm` installed | Node package manager |
| `.env` in `apps/api/` | API secrets |
| `NEXT_PUBLIC_API_BASE_URL` | Set to `http://localhost:8000` |

---

## Procedure

<numbered steps for this specific scenario — derive from the goal and covered pages>

---

## Expected Outcome

| Step | Expected |
|------|----------|
| infra-up | All containers healthy |
| API health | 200 {"status": "healthy"} |
| <scenario-specific rows> | ... |

---

## Run History

| Run | Date | Status | Artifacts |
|-----|------|--------|-----------|
| (none yet) | | | |

---

## Bugs Found

(populated after execution)

---

## Next Steps

(populated after execution)
```

### A5 — Update the demo library index

Update `demo/README.md`:

```markdown
# Demo Library

| # | Slug | Date | Status | Summary |
|---|------|------|--------|---------|
| 001 | first-user-journey | 2026-03-16 | ✅ | Login → submit URL → view resource list |
| <NNN> | <slug> | <date> | 📝 Defined | <one-line summary> |
```

### A6 — Output

```
📝 Demo <NNN> — <Title> defined
================================
Folder:  demo/<NNN>-<slug>/
README:  demo/<NNN>-<slug>/README.md

Run it with: /demo --execute <NNN>
```

---

## MODE B — `--execute <NNN>`: Execute a Demo

### B1 — Load the demo definition

Read `demo/<NNN>-<slug>/README.md`. Extract:
- The scenario / goal
- The procedure steps
- The expected outcome table

If no demo with that number exists, print an error and stop.

### B2 — Determine the run version

Check `demo/<NNN>-<slug>/artifacts/` for existing run subfolders:

```bash
ls demo/<NNN>-<slug>/artifacts/ 2>/dev/null
```

- **First run**: artifacts go directly in `demo/<NNN>-<slug>/artifacts/` (no subfolder)
- **Second run**: create `demo/<NNN>-<slug>/artifacts/run-2/`
- **Third run**: create `demo/<NNN>-<slug>/artifacts/run-3/`
- etc.

Detect the current run number by counting existing `run-N/` subdirectories (plus 1 for the
base artifacts dir if it already has files). Set `ARTIFACTS=demo/<NNN>-<slug>/artifacts[/run-N]`.

```bash
EXISTING_RUNS=$(ls -d demo/<NNN>-<slug>/artifacts/run-* 2>/dev/null | wc -l | tr -d ' ')
if [ "$(ls demo/<NNN>-<slug>/artifacts/*.* 2>/dev/null | wc -l)" -gt 0 ]; then
  RUN_N=$((EXISTING_RUNS + 2))
  ARTIFACTS="demo/<NNN>-<slug>/artifacts/run-${RUN_N}"
  mkdir -p "$ARTIFACTS"
else
  RUN_N=1
  ARTIFACTS="demo/<NNN>-<slug>/artifacts"
fi
echo "Run $RUN_N → $ARTIFACTS"
```

### B3 — Sync to latest main

```bash
git fetch origin && git checkout main && git reset --hard origin/main
```

### B4 — Start infrastructure

```bash
docker compose up -d
sleep 5
docker compose ps
```

### B5 — Run database migrations

```bash
cd apps/api && uv run alembic upgrade head 2>&1 | tee ../../$ARTIFACTS/02-migrations.txt
```

### B6 — Start the API server

Kill any existing process on port 8000 first:
```bash
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
cd apps/api && uv run uvicorn main:app --host 0.0.0.0 --port 8000 &
sleep 4
```

### B7 — Verify health endpoints

```bash
curl -s http://localhost:8000/health | tee $ARTIFACTS/03-health.json
curl -s http://localhost:8000/db-health >> $ARTIFACTS/03-health.json
```

### B8 — Start the web server

Kill any existing process on port 3001 first:
```bash
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
cd apps/web && npm run dev -- --port 3001 &
sleep 6
```

### B9 — Create demo user (idempotent)

```bash
POSTGRES_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i postgres | head -1)
docker exec -i "$POSTGRES_CONTAINER" psql -U postgres -d learningspace -c "
INSERT INTO users (email, display_name, hashed_password, is_active, created_at, updated_at)
VALUES ('demo@learningspace.dev', 'Demo User', 'hashed_demo_password', true, NOW(), NOW())
ON CONFLICT (email) DO NOTHING;
"
```

### B10 — Mint a JWT for the demo user

```bash
USER_ID=$(docker exec -i "$POSTGRES_CONTAINER" psql -U postgres -d learningspace -t -c \
  "SELECT id FROM users WHERE email='demo@learningspace.dev';" | tr -d ' \n')

cd apps/api
TOKEN=$(uv run python -c "
from core.jwt import create_access_token
token = create_access_token({'sub': '$USER_ID', 'email': 'demo@learningspace.dev'})
print(token)
")
# Token is kept in memory only — never written to disk
echo "[JWT minted for demo user — not saved to disk]" | tee ../../$ARTIFACTS/05-jwt-minted.txt
```

### B11 — Run scenario-specific API calls

Execute the API steps from the demo's Procedure section. Save each response as a numbered artifact
under `$ARTIFACTS/`. Standard calls to always include:

```bash
# Health (always)
curl -s http://localhost:8000/health | tee $ARTIFACTS/03-health.json

# Auth check (always, if /auth/me exists)
curl -s http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  | tee $ARTIFACTS/06-auth-me.json
```

Then add scenario-specific calls per the Procedure in the README.

### B12 — Capture frontend screenshots with Playwright

Write `demo/<NNN>-<slug>/screenshot.mjs` (overwrite each run — it's a script, not an artifact):

```javascript
import { chromium } from 'playwright';

const TOKEN = process.argv[2];
const OUT   = process.argv[3];   // artifact dir passed in from shell
if (!TOKEN || !OUT) {
  console.error('Usage: node screenshot.mjs <token> <artifacts-dir>');
  process.exit(1);
}

const browser = await chromium.launch();
const base = 'http://localhost:3001';

// Login page (unauthenticated context)
const anonCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const anonPage = await anonCtx.newPage();
await anonPage.goto(`${base}/login`);
await anonPage.waitForLoadState('networkidle');
await anonPage.screenshot({ path: `${OUT}/08-frontend-login.png`, fullPage: true });
await anonCtx.close();
console.log('Saved 08-frontend-login.png');

// Authenticated context — seed localStorage
const authCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
await authCtx.addInitScript((token) => {
  localStorage.setItem('auth_token', token);
  localStorage.setItem('user_info', JSON.stringify({
    id: 1, email: 'demo@learningspace.dev', display_name: 'Demo User', avatar_url: null
  }));
}, TOKEN);

const page = await authCtx.newPage();

// Standard pages — extend this list per demo scenario
const pages = [
  { url: '/dashboard',      file: '09-frontend-dashboard.png' },
  { url: '/resources/new',  file: '10-frontend-resources-new.png' },
  { url: '/resources',      file: '11-frontend-resources-list.png' },
];

for (const { url, file } of pages) {
  await page.goto(`${base}${url}`);
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: `${OUT}/${file}`, fullPage: true });
  console.log(`Saved ${file}`);
}

await browser.close();
console.log('All screenshots saved.');
```

If Playwright is not installed:
```bash
cd apps/web && npx playwright install chromium && cd ../..
```

Run:
```bash
node demo/<NNN>-<slug>/screenshot.mjs "$TOKEN" "$ARTIFACTS"
```

### B13 — Update the README with actual outcome

Append a new run section to the demo's README under **Run History**:

```markdown
| run-<N> | YYYY-MM-DD HH:MM | ✅ / ⚠️ | [artifacts](./artifacts/run-N/) |
```

Also append an **Actual Outcome** subsection titled `### Run <N> — YYYY-MM-DD`:

```markdown
### Run <N> — YYYY-MM-DD

| Step | Result | Artifact |
|------|--------|----------|
| infra-up | ✅ All containers healthy | — |
| GET /health | ✅ 200 | [03-health.json](./artifacts[/run-N]/03-health.json) |
| GET /auth/me | ✅ 200 + user profile | [06-auth-me.json](...) |
| POST /resources | ✅ 202 ACCEPTED | [07-create-resource.json](...) |
| Frontend /dashboard | ✅ Loads correctly | [09-frontend-dashboard.png](...) |
| ... | | |
```

Update the top-level header status:
- All steps passed → `**Status:** ✅ Executed`
- Some failed → `**Status:** ⚠️ Partial`

### B14 — Log any bugs found

For each failure:

1. Assign the next `BUG-NNN` from `memory/bugs-tracker.md`.
2. Add to `memory/bugs-tracker.md`:
   ```
   - [ ] BUG-NNN: <title> — <description> — found during demo <NNN> run <N>
   ```
3. Create `memory/active/BUG-NNN.md`.
4. Update Progress Summary counts.

### B15 — Update the demo library index

Update `demo/README.md` — change the demo's status from `📝 Defined` to `✅` or `⚠️`.

### B16 — Output

```
✅ Demo <NNN> Run <N> — <Title>
================================
Artifacts: demo/<NNN>-<slug>/artifacts[/run-N]/
  01-...   02-...   03-health.json
  05-jwt-minted.txt
  06-auth-me.json   07-create-resource.json
  08-frontend-login.png
  09-frontend-dashboard.png
  10-frontend-resources-new.png
  11-frontend-resources-list.png

API Results:
  GET  /health       → 200 ✅
  GET  /auth/me      → 200 ✅
  POST /resources    → 202 ✅
  GET  /resources    → 200 ✅

Screenshots: 4 saved

Bugs found: N
  BUG-NNN: <title>   (or "none")

Next steps:
  <from README>
```

---

## Artifact Naming Convention

```
demo/
  README.md                         ← library index
  001-first-user-journey/
    README.md                       ← demo definition + run history
    screenshot.mjs                  ← reusable screenshot script (overwritten each run)
    artifacts/                      ← run 1 artifacts (flat, no subfolder)
      01-infra-start.txt
      02-migrations.txt
      03-health.json
      05-jwt-minted.txt
      06-auth-me.json
      08-frontend-login.png
      ...
    artifacts/run-2/                ← run 2 artifacts
      03-health.json
      06-auth-me.json
      ...
    artifacts/run-3/                ← run 3 artifacts
      ...
```
