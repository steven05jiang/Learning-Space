# Vercel Deployment Guide

> **Note:** This project supports multiple cloud providers. See also: [Railway Deploy Guide](railway-deploy-guide.md) (API + worker), [Fly.io Deploy Guide](flyio-deploy-guide.md) (alternative backend).

This guide walks through deploying the Learning Space frontend (`apps/web`) to Vercel.

## Prerequisites

- Vercel account (free Hobby tier is sufficient)
- GitHub repository access (for auto-deploy)
- Railway API URL from OPS-003 (needed for `NEXT_PUBLIC_API_BASE_URL`)

## Step 1: Import the Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Select "Import Git Repository" and connect your GitHub account
4. Choose the Learning Space repository

## Step 2: Configure Root Directory

This is the most important step — the repo is a monorepo.

1. Under "Configure Project", expand "Root Directory"
2. Set it to `apps/web`
3. Vercel will now scope all builds and deployments to the Next.js app

## Step 3: Configure Environment Variables

Add the following under "Environment Variables":

```bash
# Backend API URL (Railway — from OPS-003)
NEXT_PUBLIC_API_BASE_URL=https://<your-railway-api-url>
```

That is the only required env var. If the Railway URL is not yet available, use a placeholder and update it after OPS-003 completes.

## Step 4: Verify Build Settings

Vercel auto-detects Next.js. Confirm the following (should be pre-filled):

| Setting | Value |
|---|---|
| Framework Preset | Next.js |
| Build Command | `next build` |
| Output Directory | `.next` |
| Install Command | `npm install` |

No `vercel.json` is needed. The `next.config.mjs` already sets `images.unoptimized: true` which is compatible with Vercel's default image handling.

## Step 5: Deploy

Click "Deploy". Vercel will:
1. Install dependencies
2. Run `next build`
3. Publish the static + server-side output

Once complete, Vercel provides a deployment URL (e.g. `https://learning-space-xxxx.vercel.app`).

## Step 6: Enable Auto-Deploy

Auto-deploy from `main` is enabled by default. Every push to `main` triggers a new production deployment. Preview deployments are created automatically for PRs.

## Step 7: Update infra.md

Record the Vercel deployment URL in `memory/infra.md` under a new `Vercel` section.

## Troubleshooting

### Build fails with TypeScript errors
`next.config.mjs` sets `typescript.ignoreBuildErrors: true` — TypeScript errors should not fail the build. If the build still fails, check for missing dependencies or import errors.

### API calls fail after deployment
- Verify `NEXT_PUBLIC_API_BASE_URL` is set correctly in Vercel → Project → Settings → Environment Variables
- Ensure the Railway API is deployed and the `/health` endpoint responds
- Check that CORS is configured on the API to allow the Vercel domain

### Wrong directory deployed
If Vercel deploys the repo root instead of `apps/web`, go to Project → Settings → General → Root Directory and correct it to `apps/web`.

## Next Steps

After successful deployment:
1. Update `NEXT_PUBLIC_API_BASE_URL` with the final Railway URL if a placeholder was used
2. Record the Vercel URL in `memory/infra.md`
3. Proceed to OPS-005 (domain + DNS) to attach a custom domain
4. Proceed to OPS-006 (Google OAuth) to configure the production OAuth redirect URIs
