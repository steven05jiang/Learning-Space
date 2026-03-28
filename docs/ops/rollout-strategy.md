# Rollout Strategy

## Current Stage: Private Beta

For a private beta with a small allowlist, the recommended approach is:

1. **Test locally** with `make dev-stack-up` before pushing
2. **CI must pass** before merging to `main` (enforced by branch protection)
3. **Watch Railway deploy logs** after each merge — roll back via Railway dashboard if health check fails (Railway retains previous deploys, one-click rollback)
4. **Add staging** once you have real users who would be disrupted by a bad deploy

---

## Strategy by Growth Stage

| Stage | Strategy |
|---|---|
| Private beta (now) | Current approach + Railway one-click rollback |
| First real users (< 500) | Add feature flags (simple DB table) |
| Growth stage | Add staging environment (see below) |
| SLA-sensitive / high traffic | Blue-green or canary via Cloudflare Workers |

**Key diagnostic**: what is your actual failure mode?
- Bad migrations breaking the DB → staging + migration review helps most
- Bad deploys crashing the API → Railway rollback is already fast enough (30–60s)
- Risky features for a subset of users → feature flags, not infra-level routing

---

## Feature Flags (recommended next step)

For a private beta with an allowlisted user base, feature flags are strictly better than traffic splitting:

- Roll out to 2 users → check → expand — no infra changes
- Instant rollback without a redeploy
- Works with existing Railway + Supabase setup
- Target specific users by email or user ID

**Implementation**: a `feature_flags` table in Supabase + a middleware check. ~1 day to build.

```sql
create table feature_flags (
  flag    text not null,
  enabled boolean not null default false,
  -- optional: per-user override
  user_id integer references users(id),
  primary key (flag, coalesce(user_id, -1))
);
```

---

## Future: Two-Environment Setup (Staging)

When staging becomes necessary, adopt this structure:

### Environments

| | Staging | Production |
|---|---|---|
| **API** | Railway service (`SERVICE_TYPE=api`, staging env vars) | `learning-space-api-production.up.railway.app` |
| **Worker** | Railway service (`SERVICE_TYPE=worker`, staging env vars) | Production worker service |
| **Frontend** | Vercel preview deployment (automatic per branch) | Vercel production deployment |
| **Database** | Separate Supabase project (free tier allows 2) | Production Supabase project |
| **Deploy trigger** | Push to `staging` branch | Merge to `main` |

### Branch Strategy

```
feature/xxx  →  staging  →  main
                  ↓              ↓
            staging env    production env
```

- Feature branches merge to `staging` first
- After soak period (hours to days depending on risk), `staging` merges to `main`
- Railway auto-deploys on branch push; Vercel auto-creates preview URLs per branch

### Database Isolation

**Recommended: separate Supabase project for staging**
- Supabase free tier allows 2 projects — use one for staging, one for production
- Completely isolated: staging migrations and data changes cannot affect production
- Run `alembic upgrade head` against the staging DB independently

**Alternative: same DB, different schema**
- Staging uses `search_path=staging`, production uses `public`
- Simpler but risky — a bad migration command could affect both environments

### Railway Cost

One additional staging service pair (API + worker) adds ~$1–2/month to the $5 plan.
Monitor usage in the Railway dashboard and set a spending limit to avoid surprises.

### Vercel (Frontend)

Vercel automatically creates **preview deployments** for every PR and branch push.
The `staging` branch gets a stable, shareable preview URL at no extra cost.
No additional Vercel configuration is needed.

---

## Blue-Green Deployment

Railway does not natively support blue-green. Approximating it requires:

- Two Railway services (`api-blue`, `api-green`) with a load balancer or Cloudflare Worker routing between them
- Railway has no built-in traffic splitting — an external router (e.g. Cloudflare Workers) is required
- **Cost**: doubles Railway bill ($5 → $10+) and adds operational overhead

**When it makes sense**: you need zero-downtime cutover and Railway's 30–60s rollback is too slow for your SLA. Not the current bottleneck.

**Verdict**: skip until you have paying users and SLA obligations. The staging environment gets you 80% of the safety at a fraction of the complexity.

---

## Phased Rollout / Traffic Routing

### Frontend (Vercel) — already half there

Vercel gives you this for free:
- Every branch gets a preview URL — manually test before promoting to production
- **Vercel Edge Middleware** can split traffic by cookie/header (e.g. X% to new, rest to old) — requires writing middleware, but no extra cost

### Backend (Railway) — requires an external router

Railway has no built-in traffic splitting. Options:

1. **Cloudflare Workers** — intercept API calls, split by user ID or random %, forward to blue/green Railway URL. Low cost, high control.
2. **Feature flags** (see above) — ship code to all users, gate by flag. Usually better than infra-level routing because rollback is instant and targeting is flexible.

For the current use case (private beta, allowlisted users), feature flags are the right tool. Infra-level traffic routing adds complexity without meaningful benefit until you're at scale.

---

## Rollback Procedure (Production)

### API / Worker (Railway)
1. Railway dashboard → select service → Deployments tab
2. Find the last known-good deployment
3. Click **Redeploy** on that entry
4. Verify `GET /health` returns `{"status":"healthy"}` after rollback

### Frontend (Vercel)
1. Vercel dashboard → select project → Deployments
2. Find the last known-good deployment
3. Click **Promote to Production**

### Database
- Alembic migrations are applied forward-only on deploy
- For rollback: run `alembic downgrade -1` manually via Railway shell or a one-off job
- Always review migration files before merging schema changes to `main`
