# BUG: Dashboard SVG icon renders oversized without CSS

**Status:** ✅ Completed
**Priority:** Medium (visual)
**Started:** 2026-03-16
**Completed:** 2026-03-16
**Branch:** fix/bug-dashboard-svg
**PR:** #30 (merged)

## Problem
`apps/web/app/dashboard/page.tsx` contains an inline `<svg>` with only Tailwind `className="h-5 w-5"` for sizing. When Tailwind CSS is not yet applied (headless browser, slow CSS load), the SVG renders at full browser default size (hundreds of px).

## Fix
Add explicit HTML `width` and `height` attributes to the inline SVG element:
```jsx
<svg
  className="h-5 w-5 text-green-400"
  width="20"
  height="20"
  viewBox="0 0 20 20"
  fill="currentColor"
>
```

## Implementation Summary
Added `width="20"` and `height="20"` HTML attributes to the inline SVG element in `apps/web/app/dashboard/page.tsx`. Minimal 2-line change; passes `web-lint` and `web-build`.

## Review Rounds
1 round before approval

## Progress Log
- 2026-03-16 — Dispatched to implementer
- 2026-03-16 — PR #30 created
- 2026-03-16 — Reviewer: APPROVED
- 2026-03-16 — PR #30 merged ✅
