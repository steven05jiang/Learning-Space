# Ops Tracker

**Scope:** Infrastructure, deployments, Kubernetes, ArgoCD, monitoring, on-call
**Task prefix:** `OPS-`
**Initialized:** 2026-03-15
**Last Updated:** 2026-03-28 (sprint 2026-03-27-B complete — OPS-004 + OPS-006 done manually; OPS-005 deferred)

---

## Progress Summary

- Total: 6 tasks
- ✅ Completed: 5
- 🔄 Active: 0
- ⏳ Pending: 0
- ⚠️ Stuck: 0
- 🚫 Deferred: 1

---

## Tasks

- [ ] OPS-001: Upgrade Next.js to 16.x — GHSA-9g9p-9gw9-jx7f (Image Optimizer DoS) and GHSA-h25m-26qc-wcjf (RSC HTTP deserialization) are only patched in Next.js 16; web-security scan currently set to `--audit-level=critical` as workaround

## 🚀 Deployment (v2.2 — 2026-03-27)

_Target stack: Vercel (frontend) + Railway (API + worker) + Supabase (Postgres) + Neo4j AuraDB Free + Upstash (Redis) + Namecheap/Cloudflare (domain/DNS)_

- [x] OPS-002: Provision cloud data services — Supabase PostgreSQL + Neo4j AuraDB Free + Upstash Redis; document in memory/infra.md (✅ manual, 2026-03-27)
- [x] OPS-003: Backend Dockerfile + Railway deployment — API + worker services, Alembic migrations, auto-deploy from main (PR #168 ✅)
- [x] OPS-004: Frontend Vercel deployment — https://learning-space-app.vercel.app (✅ manual, 2026-03-27)
- [~] OPS-005: Domain + DNS — Namecheap domain + Cloudflare DNS + custom domains on Vercel/Railway (🚫 DEFERRED — current vercel.app domain works for now)
- [x] OPS-006: Production Google OAuth + allowlist smoke test — configure OAuth app, set ALLOWED_EMAILS, end-to-end login test (✅ manual, 2026-03-28)
