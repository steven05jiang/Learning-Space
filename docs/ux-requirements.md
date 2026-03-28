# Web UI/UX Specification

## Project: Learning Space

---

# 1. Technology Stack

Use the following stack:

- **Framework:** Next.js 16.1.6 (App Router) with Turbopack
- **Language:** TypeScript
- **UI:** React 19.2.4
- **Styling:** TailwindCSS v4 (`@import 'tailwindcss'`, `@tailwindcss/postcss`)
- **Component Library:** shadcn/ui (New York style)
- **Icons:** lucide-react
- **Graph Visualization:** react-force-graph-2d (knowledge graph)

The UI must support **system dark/light mode automatically** using `prefers-color-scheme`.

---

# 2. Overall Design Principles

Follow these UI principles:

- Minimal and modern
- Generous whitespace
- Soft shadows
- Rounded corners (12–16px)
- Consistent spacing scale (4 / 8 / 16 / 24 / 32 px)
- Accessible components
- Responsive layout

Use **two different UI styles**:

| Page             | Style                  |
| ---------------- | ---------------------- |
| Login Page       | Modern Gradient UI     |
| Application Page | Minimal SaaS Dashboard |

---

# 3. Color System

Colors are defined via **OKLch CSS variables** in `globals.css` (not raw hex). The system auto-switches via `prefers-color-scheme`.

Reference values (approximate hex equivalents):

### Light Mode

| Token          | Value                               |
| -------------- | ----------------------------------- |
| Background     | `#f8fafc`                           |
| Card           | `#ffffff`                           |
| Primary        | `#111827` (near-black, OKLch-based) |
| Border         | `#e5e7eb`                           |
| Text primary   | `#111827`                           |
| Text secondary | `#6b7280`                           |

### Dark Mode

| Token      | Value     |
| ---------- | --------- |
| Background | `#0f172a` |
| Card       | `#1e293b` |
| Text       | `#e5e7eb` |

---

# 4. Page 1 — Login Page

## Style

Modern Gradient UI with minimal content.

Full-screen gradient background with a centered login card.

### Background

**Blur orbs** (not full-screen gradient). Three layered radial gradient blobs using `blur-3xl` create a soft ambient effect. The page background is `bg-background` (neutral).

```tsx
// Implemented in app/login/page.tsx
<div className="absolute -left-1/4 -top-1/4 h-[600px] w-[600px] rounded-full bg-gradient-to-br from-primary/10 via-primary/5 to-transparent blur-3xl" />
<div className="absolute -bottom-1/4 -right-1/4 h-[500px] w-[500px] rounded-full bg-gradient-to-tl from-muted/60 via-muted/30 to-transparent blur-3xl" />
<div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] ... blur-3xl" />
```

> **Decision:** Chose prototype's blur orbs over the original full-screen gradient spec.

---

## Layout

The login page should contain only essential elements.

```
Full screen gradient background

        App Logo / Name

        +----------------------+
        | Email                |
        | Password             |
        |                      |
        |  Sign In Button      |
        |                      |
        |  Forgot Password     |
        +----------------------+
```

---

## Login Card Design

The login form appears in a card with glass-like styling.

Properties:

- rounded corners (16px)
- soft shadow
- backdrop blur
- centered on screen
- padding: 32px

Example style concept:

```
background: rgba(255,255,255,0.9)
backdrop-filter: blur(10px)
border-radius: 16px
```

Dark mode version should use a darker translucent card.

---

## Login Components

Required components:

- App logo or name
- Email input
- Password input
- Sign In button
- Forgot Password link
- "Don't have an account? Sign up" link

Social login (2-column grid layout):

- Login with Google
- Login with X (Twitter)

---

# 5. Page 2 — Main Application Page

## Style

Minimal SaaS Dashboard.

Clean layout with sidebar navigation and large content area.

---

## Layout Structure

```
+---------------------------------------------------+
| Top Navigation Bar                                |
+------------+--------------------------------------+
| Sidebar    |                                      |
| Navigation |          Main Content Area           |
|            |                                      |
|            |                                      |
|            |                                      |
|            |                                      |
|            |                                      |
|            |                                      |
|------------|--------------------------------------|
| Chat Agent |                                      |
+------------+--------------------------------------+
```

---

# 6. Top Navigation Bar

The top bar should include:

- App name or logo
- Page title
- Optional user avatar / account menu

Design:

- height: ~56px
- subtle bottom border
- minimal styling

---

# 7. Sidebar Navigation

The sidebar is used for application navigation.

### Sidebar Structure

```
Logo

Navigation
• Dashboard
• Resources
• Knowledge Graph
• Search
• Settings

---------------------

AI Agent

[ Ask AI Agent ]
```

---

# 7.1 Search Page

The Search page is the target of the "Search" sidebar nav item.

### Layout

```
+----------------------------------+
| Search                           |
|                                  |
| [ 🔍  Search your resources... ] |
|                              [x] | ← clear button, shown when query is non-empty
|                                  |
| Filters: tag dropdown (optional) |
|                                  |
| Results (N found)                |
| ┌──────────────────────────────┐ |
| │ Resource Card (ranked)       │ |
| │ Title · summary · tags · url │ |
| └──────────────────────────────┘ |
| ...                              |
+----------------------------------+
```

### Behavior

- Search input is auto-focused on page load.
- Search triggers on each keystroke with a 300 ms debounce (no submit button required; hitting Enter also triggers immediately).
- Results replace the list below in real time as user types.
- **Loading state**: show a spinner inside the input while request is in flight.
- **Empty state** (query entered, no results): show "No resources found for '...'. Try a broader search." message.
- **Blank state** (no query yet): show a prompt, e.g. "Start typing to search your resources."
- Optional tag filter renders as a dropdown populated from `GET /categories`; clears when query is cleared.
- Each result card links to the resource detail page on click.
- Results show: title, summary (truncated to 2 lines), tags (as chips), and the URL/source if applicable.
- `rank` score is not displayed to the user.

---

### Sidebar Design

- width: ~240px
- vertical navigation
- icons + labels
- highlight active item
- collapsible on smaller screens

---

# 8. AI Agent Chat Button

At the **bottom of the sidebar**, include an icon-only toggle button:

- Icon: `Sparkles` (lucide-react)
- No text label — icon only
- **Toggles** the chat panel open/closed (not just open)
- Active state: `bg-primary/20 text-primary ring-2 ring-primary/50`
- Inactive state: `bg-primary text-primary-foreground`

> **Decision:** Changed from labeled "Ask AI Agent" button to icon-only Sparkles toggle per prototype PR #2.

---

# 9. Chat Assistant Panel

The AI assistant appears as a **slide-out panel on the right side of the screen**.

Layout:

```
+---------------------------+
| Main Content              |
|                           |
|                           |
|                 +---------+
|                 | Chat UI |
|                 |         |
+-----------------+---------+
```

Panel properties:

- width: ~380px
- fixed to right side
- slide-in animation
- can be closed

---

## Chat Panel Components

The panel contains:

- Chat header (AI Agent title)
- Message history
- User input box
- Send button

Optional:

- conversation reset
- suggested prompts

---

# 10. Main Content Area

The content area will display application pages.

Example layout pattern:

```
Page Title

Cards Grid

+----------------------------+
| Resource Title             |
| Summary text               |
|                            |
| Tags                       |
|                    Open →  |
+----------------------------+
```

---

## Card Design

Cards should follow minimal SaaS style:

- white (or dark card in dark mode)
- rounded corners
- soft shadow
- comfortable padding

---

# 11. Responsive Behavior

Requirements:

- Sidebar collapses on small screens
- Chat panel becomes full-screen on mobile
- Cards stack vertically on narrow screens

---

# 12. Folder Structure

Suggested structure:

```
/app
  /login
    page.tsx

  /dashboard
    page.tsx

/components
  Sidebar.tsx
  Topbar.tsx
  ChatPanel.tsx
  LoginForm.tsx
  ResourceCard.tsx
```

---

# 13. Interaction Requirements

The UI should include:

- hover states for buttons and cards
- smooth transitions
- consistent spacing
- keyboard accessibility

---

# 14. Visual Style Summary

Login Page:

- gradient background
- centered login card
- minimal UI

Application Page:

- light neutral background
- sidebar navigation
- card-based content
- AI assistant panel

The design should resemble modern SaaS products like:

- Notion
- Linear
- Vercel Dashboard
- modern AI applications

---
