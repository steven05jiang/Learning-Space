# Learning Space API

FastAPI backend for the Learning Space application.

## Features

- Environment-based configuration
- PostgreSQL database integration
- Neo4j graph database support
- Redis caching
- OAuth authentication (Twitter, Google, GitHub)
- OpenAI integration

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Start development server
uv run uvicorn main:app --reload
```