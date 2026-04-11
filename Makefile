.PHONY: ci ci-check ci-lint ci-test ci-security ci-integration \
        api-lint api-test api-security api-integration \
        web-lint web-build web-security web-dev web-dev-mock \
        int-test-ci int-test int-test-web int-test-e2e int-test-full \
        infra-up infra-down \
        dev-stack-up dev-stack-down \
        dev-restart-api dev-restart-worker dev-restart-web dev-restart-all \
        infra-restart obs-up obs-down

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
	cd apps/api && JWT_SECRET_KEY=ci-test-secret-key-32-chars-minimum uv run pytest -m "not integration" -v

api-security:
	@echo "── API: security scan ─────────────────────────────────"
	cd apps/api && uv sync --frozen --extra dev -q
	# CVE-2024-23342: ecdsa transitive dep of python-jose; unused since we use [cryptography] backend. BUG-001 tracks migration to authlib JWT.
	cd apps/api && JWT_SECRET_KEY=ci-test-secret-key-32-chars-minimum uv run pip-audit --ignore-vuln CVE-2024-23342 --ignore-vuln CVE-2026-4539
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

obs-up:
	@echo "── Starting observability stack ───────────────────────"
	docker compose up -d phoenix prometheus grafana
	@echo "   Waiting for Phoenix..."
	@ok=0; for s in $$(seq 1 30); do if curl -sf http://localhost:6006 > /dev/null 2>&1; then ok=1; break; fi; sleep 1; done; \
	if [ $$ok -eq 0 ]; then echo "   WARNING: Phoenix not ready (check: docker compose logs phoenix)"; else echo "   Phoenix ready  → http://localhost:6006"; fi
	@echo "   Waiting for Prometheus..."
	@ok=0; for s in $$(seq 1 30); do if curl -sf http://localhost:9090/-/ready > /dev/null 2>&1; then ok=1; break; fi; sleep 1; done; \
	if [ $$ok -eq 0 ]; then echo "   WARNING: Prometheus not ready (check: docker compose logs prometheus)"; else echo "   Prometheus ready → http://localhost:9090"; fi
	@echo "   Waiting for Grafana..."
	@ok=0; for s in $$(seq 1 30); do if curl -sf http://localhost:3001/api/health > /dev/null 2>&1; then ok=1; break; fi; sleep 1; done; \
	if [ $$ok -eq 0 ]; then echo "   WARNING: Grafana not ready (check: docker compose logs grafana)"; else echo "   Grafana ready  → http://localhost:3001"; fi

obs-down:
	docker compose stop phoenix prometheus grafana

infra-up:
	@echo "── Starting infrastructure ────────────────────────────"
	docker compose up -d postgres redis neo4j
	@echo "   Waiting for PostgreSQL..."
	@until docker compose exec -T postgres pg_isready -q; do sleep 1; done
	@echo "   PostgreSQL ready."
	@echo "   Waiting for Redis..."
	@ok=0; \
	for s in $$(seq 1 30); do \
	  if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then ok=1; break; fi; \
	  sleep 1; \
	done; \
	if [ $$ok -eq 0 ]; then \
	  echo "   Redis not ready, restarting container..."; \
	  docker compose restart redis; \
	  for s in $$(seq 1 30); do \
	    if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then ok=1; break; fi; \
	    sleep 1; \
	  done; \
	fi; \
	if [ $$ok -eq 0 ]; then echo "   ERROR: Redis failed to start. Run: docker compose logs redis"; exit 1; fi; \
	echo "   Redis ready."
	@echo "   Waiting for Neo4j (may take up to 60s on first start)..."
	@ok=0; \
	for s in $$(seq 1 60); do \
	  if curl -sf http://localhost:7474 > /dev/null 2>&1; then ok=1; break; fi; \
	  sleep 1; \
	done; \
	if [ $$ok -eq 0 ]; then \
	  echo "   Neo4j not ready, restarting container..."; \
	  docker compose restart neo4j; \
	  for s in $$(seq 1 60); do \
	    if curl -sf http://localhost:7474 > /dev/null 2>&1; then ok=1; break; fi; \
	    sleep 1; \
	  done; \
	fi; \
	if [ $$ok -eq 0 ]; then echo "   ERROR: Neo4j failed to start. Run: docker compose logs neo4j"; exit 1; fi; \
	echo "   Neo4j ready."

infra-restart:
	@echo "── Restarting infrastructure ──────────────────────────"
	$(MAKE) infra-down
	$(MAKE) infra-up

infra-down:
	docker compose down

# ── Development Stack ──────────────────────────────────────────────────────

dev-stack-up:
	@echo "── Starting full development stack ───────────────────"
	@echo "   1. Starting infrastructure (Docker)..."
	$(MAKE) infra-up
	@echo "   2. Starting observability stack..."
	$(MAKE) obs-up
	@echo "   3. Running database migrations..."
	cd apps/api && uv run alembic upgrade head
	@echo "   4. Starting API (uvicorn)..."
	cd apps/api && uv run uvicorn main:app --reload --port 8000 > /tmp/api.log 2>&1 &
	@echo "   5. Starting worker (arq with dual-mode)..."
	cd apps/api && uv run python workers/run_worker.py > /tmp/worker.log 2>&1 &
	@echo "   6. Starting web (Next.js)..."
	cd apps/web && npm run dev > /tmp/web.log 2>&1 &
	@echo "   7. Waiting for API to be healthy (up to 5 attempts, 30s each)..."
	@ok=0; \
	for attempt in 1 2 3 4 5; do \
	  for s in $$(seq 1 30); do \
	    if curl -sf http://localhost:8000/health/ > /dev/null 2>&1; then ok=1; break; fi; \
	    sleep 1; \
	  done; \
	  if [ $$ok -eq 1 ]; then echo "   API healthy (attempt $$attempt/5) ✓"; break; fi; \
	  echo "   API not healthy after 30s (attempt $$attempt/5), restarting..."; \
	  lsof -ti :8000 | xargs kill -9 2>/dev/null || true; \
	  sleep 2; \
	  (cd apps/api && uv run uvicorn main:app --reload --port 8000 > /tmp/api.log 2>&1) & \
	done; \
	if [ $$ok -eq 0 ]; then echo "   ERROR: API failed to start after 5 attempts. Check /tmp/api.log"; exit 1; fi
	@echo "   8. Waiting for web to be healthy (up to 5 attempts, 30s each)..."
	@ok=0; \
	for attempt in 1 2 3 4 5; do \
	  for s in $$(seq 1 30); do \
	    if curl -sf http://localhost:3000 > /dev/null 2>&1; then ok=1; break; fi; \
	    sleep 1; \
	  done; \
	  if [ $$ok -eq 1 ]; then echo "   Web healthy (attempt $$attempt/5) ✓"; break; fi; \
	  echo "   Web not healthy after 30s (attempt $$attempt/5), restarting..."; \
	  lsof -ti :3000 | xargs kill -9 2>/dev/null || true; \
	  sleep 2; \
	  (cd apps/web && npm run dev > /tmp/web.log 2>&1) & \
	done; \
	if [ $$ok -eq 0 ]; then echo "   ERROR: Web failed to start after 5 attempts. Check /tmp/web.log"; exit 1; fi
	@echo ""
	@echo "Development stack started:"
	@echo "   API:        http://localhost:8000"
	@echo "   Web:        http://localhost:3000"
	@echo "   Phoenix:    http://localhost:6006  (agent traces)"
	@echo "   Prometheus: http://localhost:9090  (metrics)"
	@echo "   Grafana:    http://localhost:3001  (dashboards)"
	@echo "   Logs:       /tmp/api.log, /tmp/worker.log, /tmp/web.log"

dev-restart-api:
	@echo "── Restarting API ─────────────────────────────────────"
	lsof -ti :8000 | xargs kill -9 2>/dev/null || true
	cd apps/api && uv run uvicorn main:app --reload --port 8000 > /tmp/api.log 2>&1 &
	@ok=0; for s in $$(seq 1 30); do sleep 1; if curl -sf http://localhost:8000/health/ > /dev/null 2>&1; then ok=1; break; fi; done; \
	if [ $$ok -eq 1 ]; then echo "   API restarted ✓  (http://localhost:8000)"; else echo "   ERROR: API failed to start. Check /tmp/api.log"; exit 1; fi

dev-restart-worker:
	@echo "── Restarting worker ──────────────────────────────────"
	pkill -f "workers/run_worker.py" 2>/dev/null || true
	sleep 1
	cd apps/api && uv run python workers/run_worker.py > /tmp/worker.log 2>&1 &
	@sleep 2 && pgrep -f "run_worker.py" > /dev/null && echo "   Worker restarted ✓  (log: /tmp/worker.log)" || (echo "   ERROR: Worker failed to start. Check /tmp/worker.log"; exit 1)

dev-restart-web:
	@echo "── Restarting web ─────────────────────────────────────"
	lsof -ti :3000 | xargs kill -9 2>/dev/null || true
	cd apps/web && npm run dev > /tmp/web.log 2>&1 &
	@ok=0; for s in $$(seq 1 60); do sleep 1; if curl -sf http://localhost:3000 > /dev/null 2>&1; then ok=1; break; fi; done; \
	if [ $$ok -eq 1 ]; then echo "   Web restarted ✓  (http://localhost:3000)"; else echo "   ERROR: Web failed to start. Check /tmp/web.log"; exit 1; fi

dev-restart-all:
	@echo "── Restarting all services (API, worker, web) ─────────"
	$(MAKE) dev-restart-api
	$(MAKE) dev-restart-worker
	$(MAKE) dev-restart-web
	@echo "   All services restarted ✓"

dev-stack-down:
	@echo "── Stopping full development stack ───────────────────"
	@echo "   1. Stopping infrastructure (Docker)..."
	docker compose down
	@echo "   2. Stopping observability stack..."
	$(MAKE) obs-down
	@echo "   3. Killing API process on port 8000..."
	lsof -ti :8000 | xargs kill -9 || true
	@echo "   4. Killing worker (arq)..."
	pkill -f "workers/run_worker.py" || true
	@echo "   5. Killing web process on port 3000..."
	lsof -ti :3000 | xargs kill -9 || true
	@echo "   Development stack stopped."
