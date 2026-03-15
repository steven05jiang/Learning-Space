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
  * **New project/service** → Ask first: "Can a platform service (Vercel/Supabase/Cloudflare) replace self-hosting?"
  * **Tech stack choices** → Prefer low-scaffolding solutions. Target: single feature ≤200 lines, single service ≤3000 lines
- **Require confirmation (Critical decision points — Stop and check in)**:
  * Tech stack choices (framework/library/architecture pattern)
  * Data model changes (schema/API contract)
  * Account/wallet/fund flow changes
  * Features outside roadmap
  * >100 line refactors
  * Trade-offs (performance vs maintainability / speed vs quality)
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

## SSOT Ownership (Single Source of Truth — modify SSOT first, never create duplicates)

| Info Type | SSOT File | Do NOT write to |
|-----------|-----------|-----------------|
| Infrastructure/Servers/Cron | `memory/infra.md` | Code comments |
| Project strategic status | Each project's `PROJECT_CONTEXT.md` | dev-tracker.md, projects.md |
| Cross-project overview | `memory/projects.md` | (summary + pointers only) |
| Technical pitfalls | Each project's `MEMORY.md` | dev-tracker.md |
| Daily progress | `memory/dev-tracker.md` | track the progress |
| In-flight task registry | `memory/active/` | (cross-session task status) |

---

## Memory Write Routing

| Layer | File | What to write |
|-------|------|---------------|
| Auto Memory | Project `memory/MEMORY.md` | Technical pitfalls, API details |
| Pattern library | `patterns.md` | Cross-project reusable patterns |
| Hot data layer | `memory/dev-tracker.md` | Centralized project tracker |
| Task registry | `memory/active/ + memory/completed/` | Cross-session in-flight tasks |

### Sub-project Memory Routes (read before operating on a project)

Routes determine write targets. Unlisted projects share the main MEMORY.md.

---

## On-demand Loading Index

| Scenario | Load file |
|----------|-----------|
| Technical design | `Read docs/technical-design.md` |
| Requirements | `Read docs/requirements.md` |
| Goals/todos | `Read memory/dev-tracker.md` |
| Project overview | `Read memory/projects.md` |

---
