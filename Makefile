.PHONY: ci ci-check ci-lint ci-test ci-security ci-integration \
        api-lint api-test api-security api-integration \
        web-lint web-build web-security \
        infra-up infra-down

# ── Full CI (requires `make infra-up` first for integration tests) ────────

ci: ci-lint ci-test ci-security ci-integration

# Quick check — no infrastructure needed (run by implementer before every push)
ci-check: ci-lint ci-test ci-security

# ── Grouped targets ────────────────────────────────────────────────────────

ci-lint: api-lint web-lint

ci-test: api-test web-build

ci-security: api-security web-security

ci-integration: api-integration

# ── API ────────────────────────────────────────────────────────────────────

api-lint:
	@echo "── API: lint ──────────────────────────────────────────"
	cd apps/api && uv sync --frozen --extra dev -q
	cd apps/api && uv run ruff check .
	cd apps/api && uv run ruff format --check .

api-test:
	@echo "── API: unit tests ────────────────────────────────────"
	cd apps/api && uv sync --frozen --extra dev -q
	cd apps/api && uv run pytest -m "not integration" -v

api-security:
	@echo "── API: security scan ─────────────────────────────────"
	cd apps/api && uv sync --frozen --extra dev -q
	# CVE-2024-23342: ecdsa transitive dep of python-jose; unused since we use [cryptography] backend. BUG-001 tracks migration to authlib JWT.
	cd apps/api && uv run pip-audit --ignore-vuln CVE-2024-23342
	cd apps/api && uv run bandit -r . -c pyproject.toml

api-integration:
	@echo "── API: integration tests ─────────────────────────────"
	@echo "   (requires: make infra-up)"
	cd apps/api && uv sync --frozen --extra dev -q
	cd apps/api && uv run pytest -m integration -v

# ── Web ────────────────────────────────────────────────────────────────────

web-lint:
	@echo "── Web: lint ──────────────────────────────────────────"
	cd apps/web && npm run lint

web-build:
	@echo "── Web: build ─────────────────────────────────────────"
	cd apps/web && npm run build

web-security:
	@echo "── Web: security scan ─────────────────────────────────"
	# Remaining high-severity issues (GHSA-9g9p, GHSA-h25m) require Next.js 16 to fix. OPS-001 tracks the upgrade.
	cd apps/web && npm audit --audit-level=critical

# ── Infrastructure ─────────────────────────────────────────────────────────

infra-up:
	@echo "── Starting infrastructure ────────────────────────────"
	docker compose up -d
	@echo "   Waiting for PostgreSQL..."
	@until docker compose exec -T postgres pg_isready -q; do sleep 1; done
	@echo "   PostgreSQL ready."

infra-down:
	docker compose down
