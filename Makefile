.PHONY: ci ci-check ci-lint ci-test ci-security ci-integration \
        api-lint api-test api-security api-integration \
        web-lint web-build web-security web-dev web-dev-mock \
        int-test-ci int-test int-test-web int-test-e2e int-test-full \
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

web-dev:
	@echo "── Web: dev server ────────────────────────────────────"
	cd apps/web && npm run dev

web-dev-mock:
	@echo "── Web: dev server (mock data, no backend needed) ─────"
	cd apps/web && npm run dev:mock

# ── Integration Tests ──────────────────────────────────────────────────────

INT_GROUPS ?= auth,resources

int-test-ci:
	@echo "-- API integration tests (CI groups: $(INT_GROUPS)) ----"
	$(eval MARKERS := $(shell echo "$(INT_GROUPS)" | tr ',' '\n' | sed 's/^/int_/' | tr '\n' ' ' | sed 's/ / or /g' | sed 's/ or $$//'))
	cd apps/api && uv run pytest -m "integration and ($(MARKERS))" -v

int-test:
	@echo "── Integration: all backend tests ─────────────────────"
	@echo "   (requires: make infra-up)"
	cd apps/api && uv sync --frozen --extra dev -q
	cd apps/api && uv run pytest -m "integration" -v

int-test-web:
	@echo "── Integration: web component tests ───────────────────"
	cd apps/web && npm test -- --testPathPattern="integration" --watchAll=false

int-test-e2e:
	@echo "── Integration: end-to-end tests ──────────────────────"
	@echo "   (requires: docker-compose -f docker-compose.e2e.yml up -d)"
	cd tests/e2e && npx playwright test

int-test-full: int-test int-test-web int-test-e2e

# ── Infrastructure ─────────────────────────────────────────────────────────

infra-up:
	@echo "── Starting infrastructure ────────────────────────────"
	docker compose up -d
	@echo "   Waiting for PostgreSQL..."
	@until docker compose exec -T postgres pg_isready -q; do sleep 1; done
	@echo "   PostgreSQL ready."

infra-down:
	docker compose down
