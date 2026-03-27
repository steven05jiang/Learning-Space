# Railway Deployment Guide

This guide walks through deploying the Learning Space backend API and worker services to Railway.

## Prerequisites

- Railway account (free tier available)
- GitHub repository access (for auto-deploy)
- All external services provisioned (Supabase, Neo4j AuraDB, Upstash Redis)
- Environment variables from `apps/api/.env.production.example`

## Step 1: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account and select the Learning Space repository
5. Railway will create a project and attempt to detect services

## Step 2: Configure API Service

1. In the Railway dashboard, you should see a service created from your repo
2. Click on the service to open settings
3. Navigate to "Settings" tab
4. Rename the service to `api`
5. Go to "Variables" tab and add the following environment variables:

```bash
# Database
DATABASE_URL=<your-supabase-postgres-url>

# Neo4j
NEO4J_URI=<your-neo4j-aura-uri>
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-neo4j-password>

# Redis
REDIS_URL=<your-upstash-redis-url>

# Authentication
JWT_SECRET_KEY=<generate-random-32-char-string>
GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<your-google-oauth-client-secret>
OAUTH_REDIRECT_BASE_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}
# Note: RAILWAY_PUBLIC_DOMAIN is a Railway template variable automatically replaced with your service's public domain

# Authorization
ALLOWED_EMAILS=<comma-separated-list-of-allowed-emails>

# LLM Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=<your-groq-api-key>
ANTHROPIC_API_KEY=<your-anthropic-api-key>

# Service type for Docker build
SERVICE_TYPE=api
```

6. Railway will automatically detect the build configuration from `railway.toml` in the repository root
7. No manual build commands are needed - Railway will use the Dockerfile specified in the configuration
8. Ensure "Root Directory" is set to `/` (repository root)

## Step 3: Configure Worker Service

1. In the Railway project, click "New Service"
2. Select "GitHub Repo" and choose the same repository
3. Name the service `worker`
4. Go to "Variables" tab and add the same environment variables as API service, but change:

```bash
SERVICE_TYPE=worker
```

5. Railway will automatically detect the build configuration from `railway.toml` in the repository root
6. No manual build commands are needed - Railway will use the Dockerfile specified in the configuration
7. Ensure "Root Directory" is set to `/` (repository root)

## Step 4: Configure Auto-Deploy

1. In the Railway project settings, go to "Settings" → "Environment"
2. Under "Deployments", ensure "Auto-Deploy" is enabled
3. Set the branch to `main`
4. Both services will now automatically deploy when you push to the main branch

## Step 5: Verify Deployment

### API Service Health Check

1. Wait for the API service to deploy (check the "Deployments" tab)
2. Once deployed, find the public URL (should be `https://web-production-XXXX.up.railway.app`)
3. Test the health endpoint: `GET https://your-api-url/health`
4. You should receive: `{"status": "ok"}`

### Worker Service Status

1. Check the worker service in the Railway dashboard
2. Go to "Logs" tab to verify the worker is running
3. You should see logs indicating: "Starting Learning Space task worker..."

### Database Migrations

The API service automatically runs `alembic upgrade head` on startup, so your database schema should be up to date.

## Step 6: Update Configuration

1. Note the Railway API URL from the public domain
2. Update `memory/infra.md` with the Railway service URLs
3. If you have a frontend service, update its `BACKEND_URL` environment variable to point to the new Railway API URL

## Troubleshooting

### Common Issues

1. **Service won't start**: Check environment variables are correctly set
2. **Database connection issues**: Verify `DATABASE_URL` format and credentials
3. **Worker not processing tasks**: Check Redis connection and ensure worker service is running
4. **Migration errors**: Check database permissions and that `DATABASE_URL` is correct

### Checking Logs

- Go to Railway dashboard → your service → "Logs" tab
- For build issues, check "Build Logs"
- For runtime issues, check "Deploy Logs"

### Build Arguments

The Dockerfile uses a `SERVICE_TYPE` build argument to determine whether to run the API or worker:
- `SERVICE_TYPE=api`: Runs Alembic migrations then starts the FastAPI server on port 8000
- `SERVICE_TYPE=worker`: Installs Playwright dependencies and runs the ARQ worker process

## Cost Considerations

Railway free tier includes:
- $5 credit per month
- 512MB memory per service
- 1GB disk per service
- Shared CPU

Both API and worker services will consume your monthly credit. Monitor usage in the Railway dashboard.

## Security Notes

- Never commit real environment variables to the repository
- Use Railway's environment variable management for secrets
- The worker service runs as a non-root user for security
- All external services (database, Redis) should use encrypted connections (TLS/SSL)

## Next Steps

After successful deployment:
1. Test all API endpoints with your Railway URL
2. Submit a test resource processing job to verify worker functionality
3. Set up monitoring and alerting if needed
4. Configure custom domain if desired (Railway Pro feature)