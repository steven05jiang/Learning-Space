# Web UI/UX Specification

## Project: Learning Space

---

# 1. Technology Stack

Use the following stack:

* **Framework:** Next.js (App Router)
* **Language:** TypeScript
* **UI:** React
* **Styling:** TailwindCSS
* **Component Library:** shadcn/ui
* **Icons:** lucide-react

The UI must support **system dark/light mode automatically** using `prefers-color-scheme`.

---

# 2. Overall Design Principles

Follow these UI principles:

* Minimal and modern
* Generous whitespace
* Soft shadows
* Rounded corners (12–16px)
* Consistent spacing scale (4 / 8 / 16 / 24 / 32 px)
* Accessible components
* Responsive layout

Use **two different UI styles**:

| Page             | Style                  |
| ---------------- | ---------------------- |
| Login Page       | Modern Gradient UI     |
| Application Page | Minimal SaaS Dashboard |

---

# 3. Color System

### Light Mode

Background:

```
#f8fafc
```

Card background:

```
#ffffff
```

Primary color:

```
#6366f1
```

Accent color:

```
#22c55e
```

---

### Dark Mode

Background:

```
#0f172a
```

Card background:

```
#1e293b
```

Text:

```
#e5e7eb
```

---

# 4. Page 1 — Login Page

## Style

Modern Gradient UI with minimal content.

Full-screen gradient background with a centered login card.

### Gradient Background

Use a vibrant gradient similar to:

```
linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899)
```

Dark mode should use a darker gradient variation.

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

* rounded corners (16px)
* soft shadow
* backdrop blur
* centered on screen
* padding: 32px

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

* App logo or name
* Email input
* Password input
* Sign In button
* Forgot Password link

Optional:

* Login with Google

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

* App name or logo
* Page title
* Optional user avatar / account menu

Design:

* height: ~56px
* subtle bottom border
* minimal styling

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

### Sidebar Design

* width: ~240px
* vertical navigation
* icons + labels
* highlight active item
* collapsible on smaller screens

---

# 8. AI Agent Chat Button

At the **bottom of the sidebar**, include a button:

```
🤖 Ask AI Agent
```

Clicking this button opens the **chat assistant panel**.

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

* width: ~380px
* fixed to right side
* slide-in animation
* can be closed

---

## Chat Panel Components

The panel contains:

* Chat header (AI Agent title)
* Message history
* User input box
* Send button

Optional:

* conversation reset
* suggested prompts

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

* white (or dark card in dark mode)
* rounded corners
* soft shadow
* comfortable padding

---

# 11. Responsive Behavior

Requirements:

* Sidebar collapses on small screens
* Chat panel becomes full-screen on mobile
* Cards stack vertically on narrow screens

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

* hover states for buttons and cards
* smooth transitions
* consistent spacing
* keyboard accessibility

---

# 14. Visual Style Summary

Login Page:

* gradient background
* centered login card
* minimal UI

Application Page:

* light neutral background
* sidebar navigation
* card-based content
* AI assistant panel

The design should resemble modern SaaS products like:

* Notion
* Linear
* Vercel Dashboard
* modern AI applications

---
