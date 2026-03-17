---
name: ui-tune
description: >
  Interactive UI tuning skill for iterative component development using Next.js dev
  server with mock data. Use this skill when the user wants to tune UI components,
  review page designs, apply visual feedback, or iterate on styling. No backend needed.
  Trigger when user says "tune UI", "update component", "show me the page",
  "apply UI feedback", "UI review", or "iterate on design".
  Modes: --setup (one-time scaffolding), --page [PageName] (build/update a page or
  component), --confirm (save approved changes to ui-tracker).
---

# UI Tune Skill

Interactive UI loop: **build page/component → run `next dev` in mock mode → review in browser → feedback → implement → repeat**.

Mock mode (`NEXT_PUBLIC_USE_MOCK=true`) makes all data-fetching hooks return data from
`apps/web/lib/mock/index.ts` so the UI works without any backend running.

| Mode | Usage | What it does |
|------|-------|--------------|
| `--setup` | `/ui-tune --setup` | One-time: install shadcn/ui + lucide-react, scaffold initial page shells, verify `next dev` starts |
| `--page [Name]` | `/ui-tune --page Dashboard` | Build or update a page/component; starts mock dev server if not running |
| `--confirm` | `/ui-tune --confirm` | Append session changes to `memory/ui-tracker.md` |

**Feedback loop** (after `--page`): user describes changes → Claude edits files → Next.js hot-reloads → repeat until confirmed.

---

## MODE A — `--setup`: One-Time Scaffolding

### A1 — Check current state

```bash
ls apps/web/components/ 2>/dev/null || echo "EMPTY"
ls apps/web/node_modules/lucide-react 2>/dev/null && echo "LUCIDE_OK" || echo "LUCIDE_MISSING"
ls apps/web/node_modules/@radix-ui 2>/dev/null && echo "RADIX_OK" || echo "RADIX_MISSING"
```

### A2 — Install UI dependencies if missing

```bash
cd apps/web && npm install lucide-react
```

For shadcn/ui primitives (install only what you need, on demand):
```bash
cd apps/web && npx shadcn@latest add button input card badge
```

### A3 — Verify mock mode works

```bash
cd apps/web && NEXT_PUBLIC_USE_MOCK=true npm run build 2>&1 | tail -5
```

### A4 — Create placeholder routes if they don't exist

Ensure these files exist (create minimal shells if missing):
- `apps/web/app/login/page.tsx`
- `apps/web/app/dashboard/page.tsx`

### A5 — Output

```
✅ UI scaffold ready
=====================
Mock mode:   NEXT_PUBLIC_USE_MOCK=true (set in .env.mock)
Dev server:  make web-dev-mock   (or: cd apps/web && npm run dev:mock)
Pages:
  /login      → apps/web/app/login/page.tsx
  /dashboard  → apps/web/app/dashboard/page.tsx

Next step: /ui-tune --page Login  (or Dashboard)
```

---

## MODE B — `--page [Name]`: Build or Update a Page / Component

### B1 — Determine target

Map the name to a file:

| Name | File |
|------|------|
| Login | `app/login/page.tsx` + `components/LoginForm.tsx` |
| Dashboard | `app/dashboard/page.tsx` |
| Sidebar | `components/Sidebar.tsx` |
| Topbar | `components/Topbar.tsx` |
| ChatPanel | `components/ChatPanel.tsx` |
| ResourceCard | `components/ResourceCard.tsx` |
| PageContainer | `components/PageContainer.tsx` |

If omitted, ask which page/component to work on.

### B2 — Read specs

Read `docs/ux-requirements.md` sections relevant to this page/component.
Use the Design System Reference at the bottom of this skill.

### B3 — Read existing files (if any)

Always read the file before editing. Never assume current state.

### B4 — Build or update the component

**Rules:**
- TailwindCSS only — no inline styles except where Tailwind can't express it (e.g. custom gradients)
- Dark mode via `dark:` prefix throughout
- Icons from `lucide-react`
- shadcn/ui primitives for inputs, buttons, cards where available
- Mock data: import from `../../lib/mock` (or `../lib/mock` from components/)
- Check mock flag: `import { useMock } from '../lib/mock/hooks'`
- Spacing: 4 / 8 / 16 / 24 / 32 / 48 px only — use `p-1/2/4/6/8/12` etc.
- No hardcoded data strings — pull from mock or props
- TypeScript: proper types for all props

**For pages** — wrap with layout shell:
```tsx
// app/dashboard/page.tsx
import { Sidebar } from '@/components/Sidebar';
import { Topbar } from '@/components/Topbar';

export default function DashboardPage() {
  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar title="Dashboard" />
        <main className="flex-1 overflow-y-auto p-6">
          {/* content */}
        </main>
      </div>
    </div>
  );
}
```

### B5 — Check mock data is wired

Data-fetching hooks should follow this pattern:

```typescript
// lib/hooks/useResources.ts
import { useMock } from '../mock/hooks';
import { mockResources } from '../mock';

export function useResources() {
  if (useMock()) {
    return { data: mockResources, isLoading: false, error: null };
  }
  // real fetch logic here
}
```

### B6 — Start dev server in mock mode (if not running)

```bash
lsof -ti:3000 | head -1 && echo "RUNNING" || echo "STOPPED"
```

If stopped:
```bash
cd apps/web && npm run dev:mock &
sleep 5
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

### B7 — Lint check

```bash
cd apps/web && npm run lint 2>&1 | tail -8
```

Fix any errors before reporting done.

### B8 — Output

```
📐 <PageName> ready
====================
File(s): apps/web/app/<route>/page.tsx
         apps/web/components/<Name>.tsx

Dev server: http://localhost:3000/<route>
Mock mode:  ✅ active (no backend needed)

Open http://localhost:3000/<route> to review.
Provide feedback and I'll implement it immediately.
```

---

## Feedback Loop (after `--page`)

User types feedback in the conversation. Claude implements it immediately.

**Rules:**
1. Read the file before editing — never guess current state
2. Make targeted edits — only change what was asked
3. Preserve dark mode — always add `dark:` when touching colors/bg
4. Run lint after changes
5. List exactly what changed (class names, structure)
6. Remind user Next.js hot-reloads — no server restart needed

**Track changes for `--confirm`:**
```
Session changes so far:
  1. LoginForm: card bg rgba(255,255,255,0.9) + backdrop-blur-md
  2. Sidebar: active item highlight indigo-100 dark:indigo-900/30
  3. ResourceCard: hover shadow-md transition
```

---

## MODE C — `--confirm`: Save to UI Tracker

### C1 — Collect session changes

List all files edited and what changed.

### C2 — Get next ID

Read `memory/ui-tracker.md`. Increment highest `UI-NNN`.

### C3 — Append to `memory/ui-tracker.md`

```markdown
## UI-NNN: <Session Title> — YYYY-MM-DD

**Pages/Components:** <list>
**Status:** ✅ Confirmed

### Changes

| File | Change | Rationale |
|------|--------|-----------|
| LoginForm.tsx | glass card bg + blur | spec: backdrop blur login card |
| Sidebar.tsx | active highlight indigo | clearer nav state |

### Routes

| Page | URL |
|------|-----|
| Login | /login |
| Dashboard | /dashboard |
```

### C4 — Output

```
✅ UI-NNN recorded in memory/ui-tracker.md
==========================================
Files changed: N
Tracker: memory/ui-tracker.md

Commit: git add apps/web/app/ apps/web/components/ apps/web/lib/ memory/ui-tracker.md
        git commit -m "UI-NNN: <title>"
```

---

## Mock Data Reference

Import from `apps/web/lib/mock/index.ts`:

| Export | Type | Use for |
|--------|------|---------|
| `mockResources` | `Resource[]` | Resource list, dashboard grid |
| `mockResource` | `Resource` | Single resource detail |
| `mockUser` | `User` | Topbar avatar, profile |
| `mockNavItems` | `NavItem[]` | Sidebar navigation |
| `mockMessages` | `ChatMessage[]` | Chat panel history |
| `mockEmptyMessages` | `ChatMessage[]` | Empty chat state |

Check mock mode: `import { useMock } from '../lib/mock/hooks'`

---

## Design System Reference

**Colors — Light:**
- Page bg: `bg-slate-50` (#f8fafc)
- Card: `bg-white`
- Primary: `bg-indigo-500` (#6366f1)
- Accent: `bg-green-500` (#22c55e)
- Border: `border-gray-200` (#e5e7eb)
- Text primary: `text-gray-900` (#111827)
- Text secondary: `text-gray-500` (#6b7280)

**Colors — Dark:**
- Page bg: `dark:bg-slate-900` (#0f172a)
- Card: `dark:bg-slate-800` (#1e293b)
- Border: `dark:border-slate-700` (#334155)
- Text primary: `dark:text-gray-200` (#e5e7eb)
- Text secondary: `dark:text-slate-400` (#94a3b8)

**Spacing:** `p-1`(4px) `p-2`(8px) `p-4`(16px) `p-6`(24px) `p-8`(32px) `p-12`(48px)
**Radius:** Cards/inputs: `rounded-xl` | Buttons: `rounded-lg`
**Shadow:** `shadow-sm` or `shadow-md` only. Hover: `hover:shadow-md transition-shadow`

**Login gradient** (inline style — Tailwind can't express three-stop gradients):
```tsx
style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899)' }}
```
Dark mode gradient variation:
```tsx
style={{ background: 'linear-gradient(135deg, #312e81, #4c1d95, #831843)' }}
```

**Login card:**
```tsx
className="bg-white/90 backdrop-blur-md rounded-2xl shadow-md dark:bg-slate-900/80"
```

**Sidebar:** `w-60 shrink-0 border-r border-gray-200 dark:border-slate-700`
**Topbar:** `h-14 border-b border-gray-200 dark:border-slate-700 flex items-center px-6`
