# Learning Space

A personal knowledge management app where you collect learning resources (URLs, text snippets), which are automatically summarized and tagged by an LLM, forming a personal knowledge graph you can explore visually and query via an AI chatbot.

## Local Dev

**Prerequisites:** Docker, Node 20+, Python 3.12+, `uv`

```bash
# Start infrastructure
docker compose up -d

# Run backend
cd apps/api
uv sync
uv run uvicorn main:app --reload

# Run frontend (new terminal)
cd apps/web
npm install
npm run dev
```

## CI

The CI pipeline runs lint, unit tests, security scans, and integration tests. Use `make` to run it locally.

**Prerequisites:** `make`, Docker (for integration tests)

```bash
# Quick check — lint + unit tests + security (no Docker needed)
make ci-check

# Full CI — includes integration tests (requires running infrastructure)
make infra-up   # starts PostgreSQL, Neo4j, Redis via docker compose
make ci

# Individual stages
make api-lint         # ruff check + format
make api-test         # pytest unit tests
make api-security     # pip-audit + bandit
make api-integration  # pytest -m integration (needs infra)
make web-lint         # next lint
make web-build        # next build
make web-security     # npm audit
```

**Integration tests** require real services and are marked with `@pytest.mark.integration`. They are excluded from `api-test` and only run via `api-integration`.

The same pipeline runs automatically on GitHub Actions for every push and pull request (see `.github/workflows/ci.yml`).