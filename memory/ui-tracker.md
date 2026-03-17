# UI Tracker

Tracks UI/UX component development sessions. Each entry records what changed, why, and which Storybook stories were created or updated.

**Prefix:** `UI-` | **Workflow:** `/ui-tune` skill | **Stories:** `apps/web/stories/`

---

## Progress Summary

| Status         | Count |
| -------------- | ----- |
| ✅ Confirmed   | 0     |
| 🔄 In Progress | 1     |
| 📝 Planned     | 0     |

---

## Log

## UI-001: Prototype Migration + Session Enhancements — 2026-03-16

**Pages/Components:** Login, Dashboard, Resources, Resources/New, KnowledgeGraph, AppSidebar, AppLayout, ChatPanel
**Status:** 🔄 In Progress
**Task file:** `memory/active/UI-001.md`

### Changes

| File                             | Change                                                        | Rationale                           |
| -------------------------------- | ------------------------------------------------------------- | ----------------------------------- |
| `app/globals.css`                | OKLch CSS variable color system                               | Prototype uses Tailwind v4 + OKLch  |
| `app/layout.tsx`                 | Added ThemeProvider (next-themes)                             | System dark/light mode support      |
| `components/LoginForm.tsx`       | Google + X OAuth in 2-col grid; sign up link                  | Prototype PR + user request         |
| `app/login/page.tsx`             | Blur orbs background (not full-screen gradient)               | Prototype decision                  |
| `components/app-sidebar.tsx`     | Sparkles icon-only toggle; active ring state                  | Prototype PR #2                     |
| `components/app-layout.tsx`      | Toggle chat (not open-only); overflow fixes; truncate title   | Prototype PR #2                     |
| `components/knowledge-graph.tsx` | react-force-graph-2d canvas graph; click → dialog             | Prototype knowledge-graph component |
| `app/knowledge-graph/page.tsx`   | Dynamic import (SSR disabled)                                 | Canvas requires window              |
| `components/ui/` (57 files)      | Full shadcn/ui New York style component set                   | Prototype design system             |
| `docs/ux-requirements.md`        | Updated: versions, OKLch, blur orbs, X login, Sparkles toggle | Align docs with decisions           |
| `docs/ux-tech-spec.md`           | Same updates as ux-requirements                               | Align docs with decisions           |

### Routes

| Page            | URL              |
| --------------- | ---------------- |
| Login           | /login           |
| Dashboard       | /dashboard       |
| Resources       | /resources       |
| Add Resource    | /resources/new   |
| Knowledge Graph | /knowledge-graph |
