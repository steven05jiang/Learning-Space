# Builder Workflow Template — Claude Code Global Memory

> On-demand = docs/ (technical-design.md, requirements.md) + exec-plans/ for plan related information
> Hot data layer → memory/dev-tracker.md + memory/ (active/, completed/)

---

## Delivery Standards

- **Truth > Speed**: Never claim completion without verification evidence
- **Small Batch**: ≤15 files or ≤400 lines net change per commit
- **No Secrets**: Never commit API keys/tokens
- **Reversible**: Must have rollback path
- **Self-verify**: Run lint/build/test before declaring done, read output to confirm PASS
- **Banned phrases**: "I fixed it, you try" / "Should be fine" / "Probably passes" / "Theoretically correct" / "I think it's fixed"

Multi-model cross-check (for critical logic): Claude analysis → Codex verification → label `✅ reviewed / ⚠️ unverified`

### Task Completion Gate (before starting the NEXT prefixed task)

> **Every prefixed task (DEV-, INT-, BUG-, OPS-, BUILD-, TD-, DEMO-, etc.) MUST be fully merged to `main` via PR before the next task begins. No exceptions.**

- [ ] All code changes committed and lint/build/test PASS
- [ ] PR created, reviewed, and merged to `main`
- [ ] Tracker updated (task marked complete with PR number)
- [ ] Confirm `main` is up to date locally before starting next task

This rule exists to prevent work-in-progress loss across sessions and ensure every task is independently recoverable from git history.

### Handoff Checklist (before session-end)

- [ ] Code committed and passes lint/build/test
- [ ] dev-tracker.md updated with progress and key decisions
- [ ] MEMORY.md / patterns.md updated with lessons learned
- [ ] Deploy docs updated (if VPS/config changes involved)
- [ ] Remaining issues and v2 improvements noted

---

## Work Preferences

- **Language**: English | **Code**: Follow project lint rules | **Commits**: Atomic, one commit = one change
- **Verification**: Claude runs it | **Tests**: Must work offline, use mock/fixtures
- **Python**: Use `uv` for all project/dependency management. `uv init` to scaffold, `uv add` to add dependencies, `uv run` to execute scripts/tests. Never use raw `pip install` or `python -m venv`.
- **GitHub tokens**: Always use `GH_TOKEN=<value of GH_TOKEN_IMPLEMENTER>` when pushing code/branches or creating PRs with `gh`. Always use `GH_TOKEN=<value of GH_TOKEN_REVIEWER>` when reviewing, requesting changes, or approving PRs with `gh`. Example: `GH_TOKEN=$GH_TOKEN_IMPLEMENTER gh pr create ...` / `GH_TOKEN=$GH_TOKEN_REVIEWER gh pr review ...`

---

## Collaboration Preferences

- Act as advisor, devil's advocate, mirror — proactively point out blind spots, never be a yes-man
- **Auto-execute**: P0/P1 bugs, bug fixes, ≤100 line refactors
- **Auto-intercept**:
  - **New project/service** → Ask first: "Can a platform service (Vercel/Supabase/Cloudflare) replace self-hosting?"
  - **Tech stack choices** → Prefer low-scaffolding solutions. Target: single feature ≤200 lines, single service ≤3000 lines
- **Require confirmation (Critical decision points — Stop and check in)**:
  - Tech stack choices (framework/library/architecture pattern)
  - Data model changes (schema/API contract)
  - Account/wallet/fund flow changes
  - Features outside roadmap
  - > 100 line refactors
  - Trade-offs (performance vs maintainability / speed vs quality)
- **Never self-decide**: Delete projects, production deploys, fund operations
- **Banned**: "Is this OK?" / "Should I pick A or B?" / "Should I continue?"
- **No filler intros**: Don't say "OK let me help" / "Let me take a look" / "Sure!" — go straight to the answer or start working

---

## Experience Recall & Evolution

**Mandatory triggers (check every conversation turn)**:

- 🔍 **Encountering Bug/Error/Stuck** → First step: `memory_search "<problem keywords>"`
- 📝 **Corrected by user** → Immediately: `memory_add` to record lesson
- 🆕 **Starting new task** → Check: patterns.md for related pitfalls

---

- **Recall First**: Encountering Bug/Error → First step: query memory. No recall before debugging = process violation.
- **Self-Evolution**: If executed >8 tools on a complex task, REFLECT: "Which system should capture this learning?" and record it.

---

## CI — Running Locally

```bash
# Quick check (lint + unit tests + security scan — no infrastructure needed)
make ci-check

# Full CI (requires running infrastructure first)
make infra-up
make ci

# Individual targets
make api-lint        # ruff check + format check
make api-test        # pytest unit tests (no real DB)
make api-integration # pytest -m integration (needs postgres + neo4j)
make api-security    # pip-audit + bandit
make web-lint        # next lint
make web-build       # next build
make web-security    # npm audit
```

**Integration tests** are marked `@pytest.mark.integration` and require real services.
Run `make infra-up` to start PostgreSQL, Neo4j, and Redis via Docker before `make api-integration`.

```bash
# Integration test targets (from docs/integration-test-design.md)
INT_GROUPS=auth,resources make int-test-ci   # Layer 1: CI-default groups (every PR)
make int-test                                 # Layer 1: all API integration groups
make int-test-web                             # Layer 2: frontend (Jest + MSW, no infra)
make int-test-e2e                             # Layer 3: Playwright E2E (full stack)
make int-test-full                            # All three layers
```

INT tasks that are **ready to write** (DEV dependencies complete): INT-001–023 (health, auth, resources), INT-041–044, INT-050–052 (frontend settings/resource UI).
Remaining INT tasks are blocked pending their DEV dependency — see `memory/dev-tracker.md` for per-task status.

---

## Task Tracker Files

| Tracker                 | File                          | Prefix   | Scope                                           |
| ----------------------- | ----------------------------- | -------- | ----------------------------------------------- |
| Feature development     | `memory/dev-tracker.md`       | `DEV-`   | Product features per exec-plan                  |
| Integration tests (BDD) | `memory/dev-tracker.md`       | `INT-`   | One test per BDD scenario; INT-000 = framework, INT-001–055 = BDD coverage |
| Bug fixes               | `memory/bugs-tracker.md`      | `BUG-`   | Defects and regressions                         |
| DevOps / Infrastructure | `memory/ops-tracker.md`       | `OPS-`   | Deploy, k8s, ArgoCD, monitoring                 |
| Build / CI / Tooling    | `memory/build-tracker.md`     | `BUILD-` | CI pipelines, test frameworks, tooling          |
| Tech debt               | `memory/tech-debt-tracker.md` | `TD-`    | Refactors, cleanups, architectural improvements |

All task files (regardless of tracker) live in `memory/active/` and `memory/completed/`.
Use the prefix (e.g. `BUG-001.md`, `OPS-001.md`) to avoid name collisions.

---

## SSOT Ownership (Single Source of Truth — modify SSOT first, never create duplicates)

| Info Type                   | SSOT File                           | Do NOT write to              |
| --------------------------- | ----------------------------------- | ---------------------------- |
| Infrastructure/Servers/Cron | `memory/infra.md`                   | Code comments                |
| Project strategic status    | Each project's `PROJECT_CONTEXT.md` | dev-tracker.md, projects.md  |
| Cross-project overview      | `memory/projects.md`                | (summary + pointers only)    |
| Technical pitfalls          | Each project's `MEMORY.md`          | dev-tracker.md               |
| Feature progress            | `memory/dev-tracker.md`             | track the progress           |
| Bug progress                | `memory/bugs-tracker.md`            | track bug fixes              |
| Ops progress                | `memory/ops-tracker.md`             | track ops work               |
| Build/CI progress           | `memory/build-tracker.md`           | track build work             |
| Tech debt progress          | `memory/tech-debt-tracker.md`       | track refactors and cleanups |
| In-flight task registry     | `memory/active/`                    | (cross-session task status)  |
| Backlog task specs          | `memory/backlog/`                   | (detailed specs for planned but not yet started tasks) |

---

## Memory Write Routing

| Layer             | File                                 | What to write                   |
| ----------------- | ------------------------------------ | ------------------------------- |
| Auto Memory       | Project `memory/MEMORY.md`           | Technical pitfalls, API details |
| Pattern library   | `patterns.md`                        | Cross-project reusable patterns |
| Feature tracker   | `memory/dev-tracker.md`              | DEV task progress               |
| Bug tracker       | `memory/bugs-tracker.md`             | BUG task progress               |
| Ops tracker       | `memory/ops-tracker.md`              | OPS task progress               |
| Build tracker     | `memory/build-tracker.md`            | BUILD task progress             |
| Tech debt tracker | `memory/tech-debt-tracker.md`        | TD task progress                |
| Task registry     | `memory/active/ + memory/completed/` | Cross-session in-flight tasks   |

### Sub-project Memory Routes (read before operating on a project)

Routes determine write targets. Unlisted projects share the main MEMORY.md.

---

## On-demand Loading Index

| Scenario                      | Load file                                     |
| ----------------------------- | --------------------------------------------- |
| Technical design              | `Read docs/technical-design.md`               |
| Requirements                  | `Read docs/requirements.md`                   |
| Resource fetching strategy    | `Read docs/design-resource-fetching.md`        |
| Category taxonomy / graph     | `Read docs/design-category-taxonomy.md`        |
| Feature goals/todos           | `Read memory/dev-tracker.md`                  |
| Bug status                    | `Read memory/bugs-tracker.md`                 |
| Ops status                    | `Read memory/ops-tracker.md`                  |
| Build/CI status               | `Read memory/build-tracker.md`                |
| Tech debt status              | `Read memory/tech-debt-tracker.md`            |
| Project overview              | `Read memory/projects.md`                     |

---
