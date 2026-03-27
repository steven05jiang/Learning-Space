# Fly.io Deployment Guide

This guide walks through deploying the Learning Space backend API and worker services to Fly.io.

## Prerequisites

- Fly.io account (free tier available)
- GitHub repository access (for auto-deploy)
- All external services provisioned (Supabase, Neo4j AuraDB, Upstash Redis)
- Environment variables from `apps/api/.env.production.example`

## Step 1: Install and Setup Fly.io CLI

1. Install flyctl:
   ```bash
   # macOS
   brew install flyctl

   # Linux/Windows
   curl -L https://fly.io/install.sh | sh
   ```

2. Login to Fly.io:
   ```bash
   fly auth login
   ```

## Step 2: Create Fly.io Applications

Create two separate applications for the API and worker services:

```bash
# Create API app
fly apps create learning-space-api

# Create worker app
fly apps create learning-space-worker
```

Note: Replace `learning-space-api` and `learning-space-worker` with your preferred app names. Update the `app` field in the corresponding `.toml` files to match.

## Step 3: Set Environment Variables

Set the required environment variables for both applications. All variables from `apps/api/.env.production.example` are required:

### For API Service:
```bash
fly secrets set \
  DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres" \
  NEO4J_URI="neo4j+s://XXXXXXXX.databases.neo4j.io" \
  NEO4J_USERNAME="neo4j" \
  NEO4J_PASSWORD="your-neo4j-password" \
  REDIS_URL="rediss://:PASSWORD@HOST:PORT" \
  JWT_SECRET_KEY="generate-random-32-char-string" \
  GOOGLE_CLIENT_ID="your-google-oauth-client-id" \
  GOOGLE_CLIENT_SECRET="your-google-oauth-client-secret" \
  OAUTH_REDIRECT_BASE_URL="https://learning-space-api.fly.dev" \
  ALLOWED_EMAILS="comma-separated-list-of-allowed-emails" \
  LLM_PROVIDER="groq" \
  GROQ_API_KEY="your-groq-api-key" \
  ANTHROPIC_API_KEY="your-anthropic-api-key" \
  --app learning-space-api
```

### For Worker Service:
```bash
fly secrets set \
  DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres" \
  NEO4J_URI="neo4j+s://XXXXXXXX.databases.neo4j.io" \
  NEO4J_USERNAME="neo4j" \
  NEO4J_PASSWORD="your-neo4j-password" \
  REDIS_URL="rediss://:PASSWORD@HOST:PORT" \
  JWT_SECRET_KEY="generate-random-32-char-string" \
  GOOGLE_CLIENT_ID="your-google-oauth-client-id" \
  GOOGLE_CLIENT_SECRET="your-google-oauth-client-secret" \
  OAUTH_REDIRECT_BASE_URL="https://learning-space-api.fly.dev" \
  ALLOWED_EMAILS="comma-separated-list-of-allowed-emails" \
  LLM_PROVIDER="groq" \
  GROQ_API_KEY="your-groq-api-key" \
  ANTHROPIC_API_KEY="your-anthropic-api-key" \
  --app learning-space-worker
```

## Step 4: First Deployment

Deploy both services for the first time:

### Deploy API Service:
```bash
fly deploy --config apps/api/fly.api.toml --remote-only
```

### Deploy Worker Service:
```bash
fly deploy --config apps/api/fly.worker.toml --remote-only
```

## Step 5: Verify Deployment

### API Service Health Check

1. Wait for the API service to deploy:
   ```bash
   fly status --app learning-space-api
   ```

2. Test the health endpoint:
   ```bash
   curl https://learning-space-api.fly.dev/health
   ```

3. You should receive: `{"status": "ok"}`

### Worker Service Status

1. Check the worker service status:
   ```bash
   fly status --app learning-space-worker
   ```

2. View worker logs to verify it's running:
   ```bash
   fly logs --app learning-space-worker
   ```

3. You should see logs indicating: "Starting Learning Space task worker..."

### Database Migrations

The API service automatically runs `alembic upgrade head` on startup, so your database schema should be up to date.

## Step 6: Setup GitHub Actions Auto-Deploy

1. Generate a Fly.io deploy token:
   ```bash
   fly tokens create deploy
   ```

2. Add the token to your GitHub repository secrets:
   - Go to your GitHub repository
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `FLY_API_TOKEN`
   - Value: The token from step 1

3. The workflow in `.github/workflows/fly-deploy.yml` will now automatically deploy both services when you push to the `main` branch.

## Step 7: Update Configuration

1. Note the Fly.io API URL: `https://learning-space-api.fly.dev`
2. Update `memory/infra.md` with the Fly.io service URLs
3. **Important**: After OPS-004 (Vercel deploy), update the `OAUTH_REDIRECT_BASE_URL` secret to point to your frontend URL instead of the API URL

## Free Tier Limits

Fly.io free tier includes:
- 3 shared-cpu-1x VMs (256MB RAM each)
- 3GB persistent volume storage
- 160GB outbound data transfer

Both API and worker services will consume your free VM allowance. The configuration sets `min_machines_running = 0` to save resources when services are idle.

## Troubleshooting

### Common Issues

1. **App creation fails**: App name might be taken, try a different name
2. **Service won't start**: Check environment variables are correctly set
3. **Database connection issues**: Verify `DATABASE_URL` format and credentials
4. **Worker not processing tasks**: Check Redis connection and ensure worker service is running
5. **Migration errors**: Check database permissions and that `DATABASE_URL` is correct

### Checking Logs

```bash
# API service logs
fly logs --app learning-space-api

# Worker service logs
fly logs --app learning-space-worker

# Real-time logs
fly logs --app learning-space-api --follow
```

### Managing Applications

```bash
# View all your apps
fly apps list

# View app details
fly status --app learning-space-api

# Scale resources (if needed beyond free tier)
fly scale memory 512 --app learning-space-api

# Stop an app
fly apps destroy learning-space-api
```

## Security Notes

- Never commit real environment variables to the repository
- Use Fly.io's secrets management for sensitive values
- The worker service runs as a non-root user for security
- All external services (database, Redis) should use encrypted connections (TLS/SSL)
- Fly.io apps get TLS certificates automatically

## Next Steps

After successful deployment:
1. Test all API endpoints with your Fly.io URL
2. Submit a test resource processing job to verify worker functionality
3. Set up monitoring if needed (Fly.io provides basic metrics)
4. Configure custom domain if desired (available on free tier)

## Provider Alternatives

This project also supports Railway deployment. See the [Railway Deploy Guide](railway-deploy-guide.md) for an alternative hosting option.