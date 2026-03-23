---
description: "Project Sync: audits stale task statuses against GitHub PR state, stages all pending memory/tracker changes, creates a chore PR, runs pr-reviewer to approve, addresses any comments, and merges to main. Usage: /project-sync"
---

You are the Project Sync operator. Your job is to reconcile the local memory
and tracker files with ground truth (GitHub PRs, git log) and ship everything
to main in one clean chore commit.

---

## Hard Rules

- **Never use `git stash`** — not for reading, not for saving state, not for any reason.
  If uncommitted changes are in the way, stop and report them to the user. The user handles stashing manually.
- **Never stage or modify `exec-plans/vN/` files.** Those folders contain the initial generated
  baseline plan and are never updated incrementally. Task progress is tracked in `dev-tracker.md`
  and the task files under `memory/`.
- **Task lifecycle:** `memory/backlog/` → `memory/active/` → `memory/completed/`.
  Detailed specs for planned but not-yet-started tasks live in `memory/backlog/`.

---

## Phase 1 — Audit Stale Task Status

Scan `memory/active/` and `memory/completed/` for any task files whose recorded
status does not match the actual GitHub PR state.

### 1a — Check active tasks

For each file in `memory/active/` and `memory/backlog/` that has a PR number recorded:

```bash
GH_TOKEN=$GH_TOKEN_REVIEWER gh pr view <PR> --json state,mergedAt,title
```

| File location   | Recorded status | Actual PR state | Action |
| --------------- | --------------- | --------------- | ------ |
| active/         | 🔄 Active       | PR merged       | Promote to completed (see Phase 2) |
| active/         | 🔄 Active       | PR closed (unmerged) | Mark ⚠️ Stuck, update tracker |
| active/         | ⏸️ Paused       | PR merged       | Promote to completed |
| active/         | ⏸️ Paused       | PR still open   | Leave as-is (will resume next /project-dispatch) |
| active/         | ⚠️ Stuck        | PR merged       | Promote to completed (override stuck) |
| backlog/        | ⏳ Pending      | No PR           | Leave as-is — task not yet started |
| backlog/        | ⏳ Pending      | PR exists       | Move to active/, update status → 🔄 Active |

### 1b — Check completed tasks

For each file in `memory/completed/` that references a PR number, verify the
PR is indeed merged. If not, move the file back to `memory/active/` and update
the tracker.

### 1c — Check tracker counts

Read all five trackers and recount from the file system:

```
memory/dev-tracker.md        → DEV- prefix
memory/bugs-tracker.md       → BUG- prefix
memory/ops-tracker.md        → OPS- prefix
memory/build-tracker.md      → BUILD- prefix
memory/tech-debt-tracker.md  → TD- prefix
```

For any task whose tracker marker (`[ ]`, `[~]`, `[x]`, `[!]`) doesn't match
its actual file location (active vs. completed) or PR state, update the marker
and Progress Summary counts.

Log what was found and corrected:

```
🔍 Audit complete
   DEV-012 — was 🔄 Active, PR #34 merged → promoted to ✅ Completed
   BUG-003 — tracker count was off by 1 → corrected
   No other discrepancies found
```

---

## Phase 2 — Promote Merged Tasks

For each task identified as merged in Phase 1:

1. Update the file content:
   - Set `**Status:** ✅ Completed`
   - Set `**Completed:** YYYY-MM-DD HH:MM`
   - Add `## Implementation Summary` section (pull from PR body if available)
   - Update `**PR:**` field to include `(merged)`

2. Move the file to completed:
   - From `memory/active/`: `mv memory/active/TASK-XXX.md memory/completed/TASK-XXX.md`
   - From `memory/backlog/` (if it was never moved to active first): `mv memory/backlog/TASK-XXX.md memory/completed/TASK-XXX.md`

3. Update the appropriate tracker:
   - Change `[~]` → `[x]` with `(PR #N ✅)`
   - Update Progress Summary

---

## Phase 3 — Collect All Pending Changes

Run `git status` to identify all modified and untracked files across the entire repo:

```bash
git status --short
```

Stage every changed file explicitly (never use `git add .` blindly — review the list first).

Categorize what you see:

- **Modified tracker files** (dev-tracker.md, bugs-tracker.md, etc.)
- **New or modified backlog/ files** — task specs added or updated during planning
- **New or modified active/ files** — task files updated during audit
- **New completed/ files** — tasks just promoted
- **Any other memory/ files** (MEMORY.md, infra.md, etc.)
- **Code changes** — modified or untracked source files outside memory/
- **Config / tooling changes** — Makefile, CI config, etc.

**Never stage `exec-plans/vN/` files** — those are the baseline plan, generated once and not updated incrementally. If you see changes there, do not include them in the sync commit; flag them to the user.

If there are **no changes** (nothing to stage), output:

```
✅ Nothing to sync — working tree is clean and up to date with main.
```

And stop.

---

## Phase 4 — Create Sync Branch and Commit

```bash
git checkout main && git pull origin main
git checkout -b chore/project-sync-YYYY-MM-DD
```

Stage files explicitly by name — list every file you intend to commit:

```bash
git add memory/dev-tracker.md memory/completed/DEV-012.md ...
```

Commit with a descriptive message summarising what changed:

```bash
git commit -m "chore: project sync YYYY-MM-DD — <brief summary of changes>"
```

Example summaries:
- `promote DEV-012 to completed, fix tracker counts`
- `sync 3 completed tasks, update all tracker Progress Summaries`
- `audit pass — no status changes, update Last Updated dates`

---

## Phase 5 — Push and Create PR

```bash
GH_TOKEN=$GH_TOKEN_IMPLEMENTER git push -u origin chore/project-sync-YYYY-MM-DD
GH_TOKEN=$GH_TOKEN_IMPLEMENTER gh pr create \
  --title "chore: project sync YYYY-MM-DD" \
  --body "$(cat <<'EOF'
## Project Sync

Automated reconciliation of memory/ and tracker files against GitHub PR state.

### Changes

<bullet list of what was changed: tasks promoted, counts corrected, etc.>

### Verification

- [ ] All promoted tasks have merged PRs confirmed
- [ ] Tracker Progress Summary counts match file system
- [ ] No active task files reference closed/unmerged PRs
EOF
)"
```

---

## Phase 6 — Review Loop

Spawn the `pr-reviewer` subagent. Tell it:

- This is a **chore/sync PR** — there is no active task context file
- The PR number
- Review scope: **accuracy only** — verify tracker counts match the committed
  files, status markers are correct, and PR references are valid
- **Do NOT write to any memory files** — post findings as a PR comment only

**If APPROVED:**
- Merge directly: `GH_TOKEN=$GH_TOKEN_IMPLEMENTER gh pr merge <PR> --squash`
- Pull main: `git checkout main && git pull origin main`

**If CHANGES REQUESTED:**
- Read the reviewer's PR comment
- Fix the specific issues in the committed files (re-edit, re-stage, re-commit)
- Push: `GH_TOKEN=$GH_TOKEN_IMPLEMENTER git push`
- Loop back — dispatch `pr-reviewer` again

Stop after 3 consecutive CHANGES REQUESTED rounds on the same issue and report
the blocker.

---

## Phase 7 — Final Sync Report

```
╔══════════════════════════════════════════════════╗
║           Project Sync Report                    ║
╠══════════════════════════════════════════════════╣
║ Date:   YYYY-MM-DD                               ║
║ Branch: chore/project-sync-YYYY-MM-DD            ║
║ PR:     #N (merged)                              ║
╠══════════════════════════════════════════════════╣
║ CHANGES COMMITTED                                ║
║  ✅ Promoted: DEV-012 (PR #34)                   ║
║  📝 Updated:  dev-tracker.md (counts corrected)  ║
╠══════════════════════════════════════════════════╣
║ TRACKER STATE AFTER SYNC                         ║
║  dev-tracker:       ✅ 12  |  🔄 0  |  ⏳ 8     ║
║  bugs-tracker:      ✅ 2   |  🔄 0  |  ⏳ 1     ║
║  build-tracker:     ✅ 3   |  🔄 0  |  ⏳ 0     ║
║  ops-tracker:       ✅ 1   |  🔄 0  |  ⏳ 2     ║
║  tech-debt-tracker: ✅ 0   |  🔄 0  |  ⏳ 3     ║
╚══════════════════════════════════════════════════╝
```
