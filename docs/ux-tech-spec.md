# AI-Optimized UI Specification

## Project: Learning Resource Management Web App

This specification is designed for **AI coding agents to generate a near-production UI in a single generation**.

The implementation should follow **modern SaaS UI patterns** similar to Notion, Linear, or Vercel dashboards.

---

# 1. Tech Stack (Strict)

The UI must use the following stack:

Framework

* Next.js (App Router)

Language

* TypeScript

UI Framework

* React

Styling

* TailwindCSS

Component Library

* shadcn/ui

Icons

* lucide-react

State management

* React state/hooks (no global state required yet)

Dark mode

* Must support **system dark/light mode automatically** using `prefers-color-scheme`.

---

# 2. Design System

The design should follow **minimal SaaS design principles**.

## Spacing Scale

Use only these spacing units:

4px
8px
16px
24px
32px
48px

---

## Border Radius

Cards and inputs:

12px – 16px

Buttons:

10px – 12px

---

## Shadow

Use subtle shadows only.

Example Tailwind:

shadow-sm
shadow-md

Avoid heavy shadows.

---

# 3. Color System

## Light Mode

Background

#f8fafc

Card Background

#ffffff

Primary

#6366f1

Accent

#22c55e

Border

#e5e7eb

Text Primary

#111827

Text Secondary

#6b7280

---

## Dark Mode

Background

#0f172a

Card

#1e293b

Border

#334155

Text Primary

#e5e7eb

Text Secondary

#94a3b8

---

# 4. Application Layout

The application consists of **two pages**:

1. Login Page
2. Main Application Dashboard

---

# 5. Login Page (Modern Gradient UI)

## Page Purpose

Authenticate users.

The page must remain **extremely minimal and visually appealing**.

---

## Background

Use a full screen gradient.

Example:

linear-gradient(135deg,#6366f1,#8b5cf6,#ec4899)

Dark mode should use a darker gradient variation.

---

## Layout

Centered layout.

Structure:

Logo
Login Card

---

## Login Card

Centered card containing the login form.

Design:

rounded-xl
shadow-md
backdrop blur effect

Example styling concept:

background: rgba(255,255,255,0.9)
backdrop-filter: blur(10px)

Dark mode version:

rgba(30,30,30,0.8)

---

## Login Components

The card contains:

App Logo / Name

Email input

Password input

Sign In button

Forgot Password link

Optional:

Login with Google button

---

## Login Layout

Vertical stack layout.

Spacing between elements:

16px – 24px.

---

# 6. Main Application Dashboard

The dashboard uses a **Minimal SaaS layout**.

Structure:

Top Bar
Left Sidebar
Main Content Area

---

## Dashboard Layout Grid

Layout structure:

Topbar (height ~56px)

Below:

Left Sidebar (240px width)
Main Content Area (flex grow)

---

# 7. Sidebar Navigation

The sidebar is the **primary navigation system**.

---

## Sidebar Sections

Top Section

Logo
App name

---

Navigation Section

Dashboard
Resources
Knowledge Graph
Search
Settings

Each item contains:

icon
label

---

## Sidebar Footer

At the **bottom of the sidebar**, include an AI assistant button.

Button label:

Ask AI Agent

Icon:

robot or sparkles icon.

---

## Sidebar Behavior

Active item should be highlighted.

Sidebar collapses to icon-only mode on smaller screens.

---

# 8. AI Chat Assistant

Clicking **Ask AI Agent** opens a **chat panel on the right side of the screen**.

---

## Chat Panel Layout

Right slide-out panel.

Width:

360px – 400px.

Height:

Full height.

Animation:

Slide in from right.

---

## Chat Panel Components

Header

AI Agent title
Close button

---

Message Area

Scrollable message history.

---

Input Area

Text input
Send button

Optional:

Suggested prompts.

---

# 9. Top Bar

The top bar contains:

Page title
Optional user avatar

Design:

Height: ~56px
Bottom border
Minimal styling.

---

# 10. Main Content Area

The main area displays application content.

Example initial page:

Resource dashboard.

---

## Content Layout

Page title

Grid of cards.

---

## Resource Card

Each resource is displayed as a card.

Card content:

Title

Short summary text

Tags

Open link button

---

## Card Design

Card style:

rounded-lg
shadow-sm
padding

Hover state:

slight elevation.

---

## Card Layout Example

Title

Summary text

Tags row

Open action

---

# 11. Responsiveness

Requirements:

Desktop

Sidebar visible
Chat panel side-by-side.

---

Tablet

Sidebar collapsible.

---

Mobile

Sidebar becomes drawer.

Chat panel becomes full screen modal.

---

# 12. Component List

The implementation should create reusable components.

Components:

Sidebar
Topbar
ChatPanel
LoginForm
ResourceCard
PageContainer

---

# 13. File Structure

Suggested Next.js structure.

app

/login/page.tsx

/dashboard/page.tsx

---

components

Sidebar.tsx
Topbar.tsx
ChatPanel.tsx
LoginForm.tsx
ResourceCard.tsx

---

# 14. Interaction Behavior

Buttons must have hover states.

Cards should have hover elevation.

Transitions should be smooth.

Focus states must be visible for accessibility.

---

# 15. Visual Style Goal

The UI should resemble modern SaaS and AI products such as:

Notion
Linear
Vercel Dashboard
OpenAI dashboards

The final result should feel:

clean
modern
minimal
professional

---

# 16. Implementation Goal

Generate a **fully functional UI skeleton** including:

Login page

Dashboard layout

Sidebar navigation

AI chat panel

Resource card example

Dark/light mode support

Responsive behavior

The output should be **production-quality UI structure ready for backend integration**.
