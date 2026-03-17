# Learning Space API

FastAPI application for Learning Space with PostgreSQL support.

## Setup

1. Install dependencies:

   ```bash
   uv sync --extra dev
   ```

2. Copy the environment file:

   ```bash
   cp .env.example .env
   ```

3. Set up the database (requires PostgreSQL running):
   ```bash
   # Run migrations
   uv run alembic upgrade head
   ```

## Database Schema

- **Users**: `id`, `email`, `display_name`, `avatar_url`, `created_at`, `updated_at`
- **Accounts**: `id`, `user_id`, `provider`, `provider_account_id`, `access_token`, `refresh_token`, `created_at`
- **Resources**: `id`, `user_id`, `url`, `raw_text`, `title`, `summary`, `tags` (JSONB), `status`, `created_at`, `updated_at`

## Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run linter
uv run ruff check

# Auto-fix linting issues
uv run ruff check --fix
```

## Development

```bash
# Start the development server
uv run uvicorn main:app --reload
```

## Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Downgrade migrations
uv run alembic downgrade -1
```
