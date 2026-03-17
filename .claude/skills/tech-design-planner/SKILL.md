---
name: tech-design-planner
description: >
  Reads a technical design document and generates a full BDD + development planning suite.
  Use this skill whenever the user wants to: break down a technical spec or design doc into BDD tasks,
  create dependency maps for BDD or dev tasks, generate structured development task breakdowns,
  produce a prioritized development plan with milestones and MVP strategy, or update/version an existing
  plan. Trigger when user mentions "BDD", "behavior-driven", "dev tasks", "task breakdown",
  "dependency map", "dev plan", "milestones", "MVP", "exec-plans", or asks to plan/re-plan from a
  technical design. Also triggers when the user says things like "read this design and plan it out",
  "create tasks from this spec", "what should we build first", or "update the plan" for an existing
  technical document.
---

# Tech Design Planner

Converts a technical design document into a structured planning suite:

1. BDD tasks → `bdd-tasks.md`
2. BDD dependency map → `bdd-tasks-map.md`
3. Development tasks → `dev-tasks.md`
4. Dev dependency map → `dev-tasks-map.md`
5. Development plan → `dev-plan.md`
6. Plan changelog → `current-plan.md`

All files live under `exec-plans/`. Supports versioning when a plan already exists. `current-plan.md` tracks the active version and records what changed between versions so teams can handle migrations.

---

## Step 0 — Locate the Technical Design

Check where the design document is:

- **Path provided by user**: use that path directly
- **Pasted inline**: extract from the conversation

Read the full document before proceeding.

---

## Step 1 — Detect Existing Plan & Determine Version

Check if `exec-plans/` already exists:

```bash
ls exec-plans/ 2>/dev/null
```

**If no exec-plans/ folder**: this is `v1`. Create `exec-plans/` and `exec-plans/v1/`. Write all 5 plan files into `exec-plans/v1/` and create `exec-plans/current-plan.md`.

**If exec-plans/ exists**: detect the highest existing version folder:

```bash
ls -d exec-plans/v*/ 2>/dev/null | sort -V | tail -1
```

Increment to the next version (e.g., if `v2/` exists, new version = `v3`). Create `exec-plans/v3/` and write the 5 plan files there.

Also read `exec-plans/current-plan.md` and the previous version's files to understand the prior state — you'll need this to generate the changelog entry in Step 7.

Announce the version to the user before generating: _"Generating plan v3..."_

---

## Step 2 — Generate BDD Tasks (`bdd-tasks.md`)

Re-read the technical design carefully. Break it down into BDD scenarios using the standard format:

```markdown
# BDD Tasks — [Project/Feature Name]

_Version: vN | Generated: YYYY-MM-DD_

## Feature: [Feature Name]

### Scenario: [Scenario Title]

**Given** [initial context / preconditions]
**When** [action or event]
**Then** [expected outcome]
**Tags:** [e.g., #auth, #api, #ui]

[Repeat for each scenario]
```

**Guidelines:**

- Group scenarios under Features (map to major modules/components in the design)
- Each scenario should be independently testable
- Use tags to indicate domain (#backend, #frontend, #db, #api, #auth, #infra, etc.)
- Cover: happy paths, error/edge cases, integration points, and performance/security requirements where specified
- Aim for exhaustive but non-redundant coverage

---

## Step 3 — Generate BDD Dependency Map (`bdd-tasks-map.md`)

Analyze which BDD scenarios depend on others (e.g., auth must pass before user profile scenarios can run).

```markdown
# BDD Tasks Dependency Map — [Project/Feature Name]

_Version: vN_

## Dependency Tree

[Feature: Auth]
├── Scenario: User registers successfully
│ └── Scenario: User logs in with valid credentials
│ ├── Scenario: User accesses protected resource
│ └── Scenario: User refreshes token

[Feature: Profile]
├── [depends on] Scenario: User logs in with valid credentials
│ └── Scenario: User updates profile
│ └── Scenario: User uploads avatar

## Dependency Notes

- [Note any circular dependencies or special ordering requirements]
- [Note scenarios that can run in parallel]
```

**Guidelines:**

- Use ASCII tree (`├──`, `└──`, `│`) for hierarchy
- Mark cross-feature dependencies clearly with `[depends on]`
- Group independent scenario clusters together
- Add a "Parallel Execution Groups" section listing scenarios with no interdependencies

---

## Step 4 — Generate Dev Tasks (`dev-tasks.md`)

Based on `bdd-tasks.md`, decompose each BDD scenario into concrete developer tasks:

```markdown
# Development Tasks — [Project/Feature Name]

_Version: vN_

## Module: [Module Name]

### DEV-001: [Task Title]

**Type:** [Backend | Frontend | DB | Infra | Testing | DevOps]
**BDD Reference:** Scenario: [scenario title]
**Description:** [What needs to be built/changed]
**Acceptance Criteria:**

- [ ] Criterion 1
- [ ] Criterion 2
      **Estimated Effort:** [XS | S | M | L | XL]
      **Dependencies:** [DEV-XXX, DEV-YYY or "None"]

[Repeat for each task]
```

**Guidelines:**

- Number tasks sequentially: DEV-001, DEV-002, …
- One dev task per BDD scenario minimum; split complex scenarios into multiple tasks
- Include tasks for: data models/migrations, API endpoints, business logic, UI components, unit tests, integration tests, documentation
- List dependencies between dev tasks explicitly
- Include infra/DevOps tasks (CI setup, env configs, deployments) as separate tasks

---

## Step 5 — Generate Dev Tasks Dependency Map (`dev-tasks-map.md`)

Combine BDD-level dependencies (from `bdd-tasks-map.md`) with task-level dependencies (from `dev-tasks.md`) into a unified map:

```markdown
# Dev Tasks Dependency Map — [Project/Feature Name]

_Version: vN_

## Full Dependency Tree

[Module: Infrastructure & Setup]
├── DEV-001: Initialize project & CI pipeline
│ └── DEV-002: Configure database migrations
│ └── DEV-003: Create User model

[Module: Auth]
├── [requires] DEV-003: Create User model
│ ├── DEV-004: Implement registration endpoint
│ │ └── DEV-008: Unit tests — registration
│ └── DEV-005: Implement login endpoint
│ ├── DEV-009: Unit tests — login
│ └── DEV-010: Integration test — auth flow

[Module: Profile]
├── [requires] DEV-005: Implement login endpoint
│ └── DEV-011: Profile GET endpoint
│ └── DEV-012: Profile PUT endpoint
│ └── DEV-015: Integration test — profile CRUD

## Critical Path

[List the longest dependency chain — this determines minimum delivery time]
DEV-001 → DEV-002 → DEV-003 → DEV-005 → DEV-010 → ...

## Parallel Work Streams

**Stream A (can start immediately):** DEV-001, DEV-020, DEV-025
**Stream B (after DEV-003):** DEV-004, DEV-005, DEV-006
**Stream C (after DEV-005):** DEV-011, DEV-016

## Milestone Gates

| Milestone          | Blocked tasks unlocked | Required DEV tasks |
| ------------------ | ---------------------- | ------------------ |
| M1: Auth complete  | Profile, Settings, …   | DEV-001–010        |
| M2: Core API ready | Frontend integration   | DEV-001–020        |
```

---

## Step 6 — Generate Development Plan (`dev-plan.md`)

Synthesize `dev-tasks-map.md` and `bdd-tasks-map.md` into an actionable, prioritized development plan for a coding agent. The plan must answer two questions simultaneously: **what order does correctness require?** (dependency constraints) and **what order does value delivery prefer?** (MVP strategy).

```markdown
# Development Plan — [Project/Feature Name]

_Version: vN | Generated: YYYY-MM-DD_

## Overview

[2–3 sentences: what this system does, who it serves, and the core delivery philosophy
e.g. "thin vertical slices over horizontal layers — ship a working loop as early as possible."]

---

## Priority Tiers

Tasks are assigned to one of four tiers. A coding agent must complete all tasks in a tier
before starting the next, unless explicitly marked `[parallel-safe]`.

### 🔴 Tier 1 — Foundation (must exist before anything else works)

These are hard technical prerequisites: no other task can start without them.

| Priority | Task                             | Type    | Effort | Rationale                                        |
| -------- | -------------------------------- | ------- | ------ | ------------------------------------------------ |
| 1        | DEV-001: Initialize project & CI | Infra   | S      | All other tasks depend on this                   |
| 2        | DEV-002: DB schema & migrations  | DB      | M      | Data layer required by every model               |
| 3        | DEV-003: User model              | Backend | S      | Auth and all user-scoped features depend on this |

**Tier 1 exit gate:** [What must be true / passing before moving to Tier 2]

---

### 🟠 Tier 2 — MVP Core (delivers the first testable user journey end-to-end)

Pick the single thinnest vertical slice that produces real user value. Prioritize:

1. Tasks unblocked after Tier 1
2. Tasks on the critical path to the first user-facing feature
3. Happy-path only — defer error handling, edge cases, and polish

| Priority | Task                             | Type     | Effort | Rationale                             |
| -------- | -------------------------------- | -------- | ------ | ------------------------------------- |
| 1        | DEV-004: Registration endpoint   | Backend  | M      | Core of first user journey            |
| 2        | DEV-005: Login endpoint          | Backend  | M      | Required for all authenticated flows  |
| 3        | DEV-010: Registration + login UI | Frontend | L      | Makes the journey testable by a human |
| …        | …                                | …        | …      | …                                     |

**Tier 2 exit gate:** [Describe the minimal end-to-end user action that should now work]

---

### 🟡 Tier 3 — Feature Complete (remaining functional scope, dependency-ordered)

All other in-scope features, ordered by:

1. Dependency order (tasks that unlock other tasks come first)
2. User-facing value (features visible to users before internal tooling)
3. Risk (higher-risk tasks earlier, so issues surface with more time to fix)

| Priority | Task                 | Type    | Effort | Depends On | Rationale               |
| -------- | -------------------- | ------- | ------ | ---------- | ----------------------- |
| 1        | DEV-011: Profile GET | Backend | S      | DEV-005    | Unlocks profile UI      |
| 2        | DEV-012: Profile PUT | Backend | M      | DEV-011    | Unlocks profile editing |
| …        | …                    | …       | …      | …          | …                       |

**Tier 3 exit gate:** [Full feature scope complete and integration-tested]

---

### 🟢 Tier 4 — Hardening (non-functional requirements, polish, and coverage)

Items that improve quality, reliability, and observability but don't add new user capabilities.
Can be interleaved with Tier 3 where bandwidth allows.

| Priority | Task                            | Type    | Effort | Rationale                      |
| -------- | ------------------------------- | ------- | ------ | ------------------------------ |
| 1        | DEV-030: Rate limiting          | Backend | S      | Security prerequisite for prod |
| 2        | DEV-031: Error monitoring setup | Infra   | S      | Needed before any real traffic |
| …        | …                               | …       | …      | …                              |

---

## Milestones

### Milestone 1 — [Name, e.g. "Walking Skeleton"]

**Completed by:** Tier 1 done  
**DEV tasks included:** DEV-001, DEV-002, DEV-003

**What a tester can do at this milestone:**

> [Write this as a concrete user or developer action, first-person present tense]
> e.g. "I can run the project locally, hit the health-check endpoint, and confirm the
> database schema is applied."

**What is NOT yet possible:** [Be explicit — sets expectations for the coding agent]

---

### Milestone 2 — [Name, e.g. "First User Journey"]

**Completed by:** Tier 2 done  
**DEV tasks included:** DEV-004–DEV-010

**What a tester can do at this milestone:**

> e.g. "I can open the app in a browser, create an account, log in, and see my dashboard.
> The full auth loop works end-to-end with real data persisted to the database."

**What is NOT yet possible:** Profile editing, settings, notifications, …

---

### Milestone 3 — [Name, e.g. "Feature Complete"]

**Completed by:** Tier 3 done  
**DEV tasks included:** DEV-011–DEV-029

**What a tester can do at this milestone:**

> e.g. "I can use all features described in the technical design: manage my profile,
> invite team members, receive notifications, and export data."

**What is NOT yet possible:** Production hardening (rate limiting, monitoring, …)

---

### Milestone 4 — [Name, e.g. "Production Ready"]

**Completed by:** Tier 4 done  
**DEV tasks included:** DEV-030–DEV-0XX

**What a tester can do at this milestone:**

> e.g. "The system handles malformed requests gracefully, surfaces errors in the monitoring
> dashboard, and is protected against basic abuse vectors. Ready for beta users."

---

## Coding Agent Execution Rules

1. **Never start a task before its dependencies are complete.** Check `dev-tasks-map.md` before each task.
2. **Complete each Tier's exit gate before advancing.** Exit gates are not optional.
3. **Within a tier, follow the priority order** unless a task is marked `[parallel-safe]`.
4. **`[parallel-safe]` tasks** within the same tier may be started concurrently if separate agents are available.
5. **When a task is unexpectedly blocked**, escalate immediately rather than skipping ahead.
6. **Test tasks belong to the same tier as the feature they test** — do not defer testing to a later tier.

---

## Risk & Assumptions Log

| #   | Risk / Assumption                                              | Tier Affected | Mitigation                             |
| --- | -------------------------------------------------------------- | ------------- | -------------------------------------- |
| 1   | [e.g. Third-party auth provider API may have breaking changes] | T2            | Pin SDK version; add integration test  |
| 2   | [e.g. Schema design may need revision after Tier 1 testing]    | T2, T3        | Design schema to be migration-friendly |
```

**Guidelines for generating the plan:**

- **Tier 1** = pure prerequisites (no user value alone, but everything else is blocked without them). Typically: project setup, DB schema, core models, auth primitives.
- **Tier 2** = the thinnest possible vertical slice. Ask: _"What is the smallest set of tasks that produces a working user journey a human can click through?"_ Include only happy-path tasks. Resist adding "while we're here" items.
- **Tier 3** = all remaining functional scope, ordered by dependency first, then value, then risk. Within dependency-equal tasks, prefer those that unblock more downstream tasks.
- **Tier 4** = non-blocking quality items. These rarely need to block feature work but should not be skipped before production.
- **Milestones** must describe user experience in first-person, present-tense prose — not task lists. A coding agent reading this should know exactly what to demo.
- **Exit gates** should be automatable checks where possible (e.g., "all Tier 1 tests passing, migrations applied cleanly").

---

## Step 7 — Generate or Update Plan Changelog (`current-plan.md`)

`current-plan.md` lives at the root of `exec-plans/` (never inside a version folder). It is the single source of truth for which version is active and what changed between versions.

### For v1 (initial plan)

Create `current-plan.md` with the initial state:

```markdown
# Current Plan — [Project/Feature Name]

_Last updated: YYYY-MM-DD_

## Active Version

| Field             | Value                           |
| ----------------- | ------------------------------- |
| **Version**       | v1                              |
| **Generated**     | YYYY-MM-DD                      |
| **Source**        | `[path/to/technical-design.md]` |
| **BDD scenarios** | X scenarios across Y features   |
| **Dev tasks**     | X tasks across Y modules        |
| **Milestones**    | N milestones, 4 priority tiers  |

---

## Version History

### v1 — Initial Plan (YYYY-MM-DD)

**Status:** Active
**Summary:** Initial planning suite generated from technical design.

No prior version to compare against.
```

### For v2+ (updates)

Read the existing `current-plan.md` and the previous version's files. Compare the new plan against the previous version and **append** a new entry to the Version History. Update the Active Version table to point to the new version.

Each version entry must include these sections:

```markdown
### vN — [Short Change Title] (YYYY-MM-DD)

**Status:** Active
**Summary:** [1–2 sentences: what triggered this revision and the high-level impact]

#### Changes from v(N-1)

**BDD Tasks:**

- Added: [list new scenarios with feature group]
- Removed: [list removed scenarios]
- Modified: [list changed scenarios with what changed]

**Dev Tasks:**

- Added: [DEV-XXX: title — reason]
- Removed: [DEV-XXX: title — reason]
- Modified: [DEV-XXX: what changed (e.g. updated acceptance criteria, effort, dependencies)]

**Dependencies:**

- New: [DEV-XXX now depends on DEV-YYY]
- Removed: [DEV-XXX no longer depends on DEV-YYY]
- Critical path changed: [old chain] → [new chain] (or "unchanged")

**Priority / Tier Changes:**

- [DEV-XXX moved from Tier 2 → Tier 3]
- [DEV-XXX added to Tier 2]

**Milestones:**

- [M2 updated: added DEV-XXX, removed DEV-YYY]
- [M3: exit gate revised]

#### Migration Notes

[Actionable guidance for a coding agent or team that has already started work on v(N-1).
Address each of these questions where applicable:]

- **Completed tasks affected:** If any removed or modified task was already completed, explain
  whether the work is still valid or needs revision.
- **In-progress tasks affected:** If a task's acceptance criteria, dependencies, or tier changed,
  explain what the implementer should do (e.g. "review updated criteria before marking complete").
- **New tasks:** Where in the current progress they should be picked up
  (e.g. "start after DEV-010 is complete").
- **Dependency changes:** Any tasks that are now unblocked or newly blocked.
- **Breaking changes:** Anything that invalidates prior work (e.g. schema changes, renamed
  endpoints, removed features).
```

Also mark the previous version's status as a past version:

- Change previous entry's `**Status:**` from `Active` to `Superseded by vN`

**Guidelines:**

- Be specific — reference task IDs, scenario names, and tier numbers
- Migration Notes should be actionable, not just informational
- If nothing changed in a section (e.g. no milestone changes), write "No changes" instead of omitting the section
- Keep the full history — never delete previous version entries

---

## Step 8 — Write All Files

All plan files live inside versioned `exec-plans/vN/` subfolders. `current-plan.md` is the only file at the `exec-plans/` root — it tracks which version is active and records the changelog.

For a **new plan** (v1):

```
exec-plans/
├── current-plan.md       ← changelog & active version tracker
└── v1/
    ├── bdd-tasks.md
    ├── bdd-tasks-map.md
    ├── dev-tasks.md
    ├── dev-tasks-map.md
    └── dev-plan.md
```

For an **update** (v2, v3, …), add a new version folder and update `current-plan.md`:

```
exec-plans/
├── current-plan.md       ← updated: new version entry appended, active version changed
├── v1/
│   └── ...
└── v2/
    ├── bdd-tasks.md
    ├── bdd-tasks-map.md
    ├── dev-tasks.md
    ├── dev-tasks-map.md
    └── dev-plan.md
```

---

## Step 9 — Summary Report

After writing all files, print a summary in the conversation:

```
✅ Plan vN generated successfully!

📁 exec-plans/
   current-plan.md      — changelog & active version (vN)
   vN/
     bdd-tasks.md       — X scenarios across Y features
     bdd-tasks-map.md   — dependency tree for BDD scenarios
     dev-tasks.md       — X dev tasks across Y modules
     dev-tasks-map.md   — full dependency tree + critical path
     dev-plan.md        — N milestones, 4 priority tiers, X tasks

🏁 Milestones:
   M1 [Tier 1]: [Name] — [one-line user experience]
   M2 [Tier 2]: [Name] — [one-line user experience]
   M3 [Tier 3]: [Name] — [one-line user experience]
   M4 [Tier 4]: [Name] — [one-line user experience]

🔑 Critical path: DEV-001 → DEV-00X → ... → DEV-0XX (N tasks)
⚡ Parallel-safe tasks: N tasks can run concurrently across tiers
```

For v2+ updates, also include a brief summary of what changed:

```
📝 Changes from v(N-1):
   BDD: +X added, -Y removed, ~Z modified
   DEV: +X added, -Y removed, ~Z modified
   See current-plan.md for full changelog and migration notes.
```

---

## Quality Checklist

Before finalizing, verify:

- [ ] Every feature in the design has at least one BDD scenario
- [ ] Every BDD scenario maps to at least one dev task
- [ ] No orphaned dev tasks (all reference a BDD scenario)
- [ ] All dependency references (DEV-XXX) exist in dev-tasks.md
- [ ] Critical path is plausible (no missing links)
- [ ] Every dev task appears in exactly one priority tier in dev-plan.md
- [ ] Tier 2 is genuinely minimal — no task in Tier 2 that could be deferred to Tier 3 without breaking the first user journey
- [ ] Each milestone's user experience description is concrete and first-person (not a task list)
- [ ] Exit gates are defined for all four tiers
- [ ] Version numbers are consistent across all 6 files
- [ ] `current-plan.md` exists at `exec-plans/` root and Active Version matches the generated version
- [ ] For v2+: `current-plan.md` has a changelog entry with Changes and Migration Notes for the new version
- [ ] For v2+: previous version entry is marked `Superseded by vN`
