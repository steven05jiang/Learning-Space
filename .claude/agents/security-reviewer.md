---
name: security-reviewer
description: DEPRECATED — security checks are now handled by pr-reviewer. Do not dispatch this agent.
tools: Read
model: claude-haiku-4-5-20251001
---

This agent has been consolidated into `pr-reviewer`.
All security checks (OWASP Top 10, injection, auth, sensitive data exposure, security misconfiguration)
are now performed as part of every `pr-reviewer` run.

Do not dispatch this agent. Use `pr-reviewer` instead.
