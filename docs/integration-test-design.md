# Integration Test Framework Design — Learning Space

_Version: 1.0 | Created: 2026-03-20 | Tracks: INT-000_

---

## 1. Goals

This framework validates all 48 BDD scenarios (tracked as INT-001 through INT-055 in `memory/dev-tracker.md`) with these constraints:

1. **No external network calls** — OAuth providers, LLM APIs, and third-party content fetchers are always mocked. Tests pass offline.
2. **CI-configurable** — Not all tests run in every CI pipeline. Groups are opt-in via the `INT_GROUPS` environment variable and pytest markers.
3. **UI + backend integration** — Playwright validates the full request cycle from browser to database. Jest + MSW validates frontend components against mocked APIs without running the backend.
4. **Layered execution** — Three distinct test layers with different infrastructure requirements, so fast feedback is never gated on slow infrastructure.

---

## 2. Three-Layer Architecture

```
Layer 1 — API Integration (pytest)
  ├── Real PostgreSQL + Neo4j (Docker)
  ├── External APIs → mocked via respx (httpx interceptors)
  └── Covers: INT-001–040 (health, auth, resources, worker, graph, chat)

Layer 2 — Frontend Integration (Jest + MSW)
  ├── No backend needed
  ├── API responses → mocked via Mock Service Worker (MSW)
  └── Covers: INT-041–052 (resource UI, graph UI, chat UI, settings UI)

Layer 3 — E2E (Playwright)
  ├── Full running stack (API + worker + PG + Neo4j, all via Docker)
  ├── External APIs → mocked via Playwright route interception
  └── Covers: critical path BDD scenarios from each group (subset of INT-001–055)
```

Layer 1 and Layer 2 can run independently. Layer 3 requires all services running.

---

## 3. Directory Layout

```
learning-space/
├── tests/                          # Root — E2E and shared mocks
│   ├── e2e/                        # Playwright E2E tests
│   │   ├── playwright.config.ts
│   │   ├── fixtures/               # Auth state, page objects, test helpers
│   │   │   ├── auth.ts             # Fixture: creates a logged-in browser context
│   │   │   └── pages.ts            # Page object models (ResourcesPage, GraphPage, etc.)
│   │   └── specs/                  # One spec file per BDD group
│   │       ├── auth.spec.ts
│   │       ├── resources.spec.ts
│   │       ├── worker.spec.ts
│   │       ├── graph.spec.ts
│   │       ├── chat.spec.ts
│   │       └── settings.spec.ts
│   └── mocks/                      # Shared mock definitions (Python)
│       ├── oauth_mock.py           # respx routes for OAuth /token + /userinfo
│       ├── llm_mock.py             # Deterministic LLM responses (title, summary, tags)
│       └── provider_fetch_mock.py  # Mock URL content fetch (Twitter, web pages)
│
├── apps/api/tests/
│   └── integration/                # Layer 1 — API integration tests (pytest)
│       ├── conftest.py             # INT fixtures: real DB session, mocked externals
│       ├── factories.py            # Test data factories (make_resource, make_user, etc.)
│       ├── test_int_health.py      # INT-001, INT-002
│       ├── test_int_auth.py        # INT-003–INT-012
│       ├── test_int_resources.py   # INT-013–INT-023
│       ├── test_int_worker.py      # INT-024–INT-028
│       ├── test_int_graph.py       # INT-029–INT-035
│       └── test_int_chat.py        # INT-036–INT-040
│
└── apps/web/__tests__/
    └── integration/                # Layer 2 — Frontend integration tests (Jest + MSW)
        ├── setup.ts                # MSW server lifecycle (beforeAll/afterEach/afterAll)
        ├── handlers/               # MSW request handlers per feature
        │   ├── auth.ts             # Mock /auth/me, /auth/logout, OAuth redirects
        │   ├── resources.ts        # Mock /resources CRUD endpoints
        │   ├── graph.ts            # Mock /graph, /graph/expand, /graph/nodes/{id}/resources
        │   └── chat.ts             # Mock /chat, /chat/conversations
        ├── int_resource_ui.test.tsx     # INT-041–INT-044
        ├── int_graph_ui.test.tsx        # INT-045–INT-047
        ├── int_chat_ui.test.tsx         # INT-048–INT-049
        └── int_settings_ui.test.tsx     # INT-050–INT-052
```

---

## 4. External Dependency Mocking Strategy

### 4.1 OAuth Providers (Twitter, Google, GitHub)

**Problem:** OAuth flows redirect to third-party providers. Tests cannot use real OAuth.

**Solution:** Mock at the `httpx` transport layer using `respx`. The API's OAuth client is an `httpx.AsyncClient` injected via dependency. In tests this client is replaced with a `respx` mock that returns synthetic token and userinfo responses.

```python
# tests/mocks/oauth_mock.py
import respx
from httpx import Response

MOCK_TWITTER_USER = {
    "id": "twitter-user-123",
    "name": "Test User",
    "email": "test@example.com",
}

def setup_twitter_oauth_mock(respx_mock):
    respx_mock.post("https://api.twitter.com/2/oauth2/token").mock(
        return_value=Response(200, json={"access_token": "mock-twitter-token", "token_type": "bearer"})
    )
    respx_mock.get("https://api.twitter.com/2/users/me").mock(
        return_value=Response(200, json={"data": MOCK_TWITTER_USER})
    )
```

### 4.2 LLM API (OpenAI / Anthropic)

**Problem:** LLM calls are expensive, non-deterministic, and require API keys.

**Solution:** The `LLMProcessor` class accepts an injectable client. In tests a `MockLLMClient` returns deterministic title/summary/tags.

```python
# tests/mocks/llm_mock.py
import json

class MockLLMClient:
    """Returns predictable LLM responses for integration tests."""

    async def generate(self, prompt: str) -> str:
        return json.dumps({
            "title": "Mock Resource Title",
            "summary": "This is a mock summary for integration testing.",
            "tags": ["AI", "Testing", "Mock"],
        })
```

`MockLLMClient` is registered as the LLM dependency via pytest fixture and a `patch` on the DI function.

### 4.3 Provider URL Fetch (Twitter API, web pages)

**Problem:** The worker fetches content from external URLs, requiring network access and sometimes OAuth tokens.

**Solution:** Mock `httpx.AsyncClient` requests to external URLs with `respx`. Three scenarios covered:

```python
# tests/mocks/provider_fetch_mock.py
MOCK_PAGE_HTML = "<html><head><title>Test Page</title></head><body>Content here.</body></html>"
MOCK_TWEET_JSON = {"data": {"text": "Mock tweet content for testing."}}

def setup_fetch_success(respx_mock, url: str):
    respx_mock.get(url).mock(return_value=Response(200, text=MOCK_PAGE_HTML))

def setup_fetch_requires_auth(respx_mock, url: str):
    """Simulates a site that returns 401 on unauthenticated access."""
    respx_mock.get(url).mock(return_value=Response(401))

def setup_twitter_api_fetch(respx_mock, tweet_api_url: str):
    """Simulates a successful authenticated fetch via Twitter API."""
    respx_mock.get(tweet_api_url).mock(return_value=Response(200, json=MOCK_TWEET_JSON))
```

### 4.4 Frontend API Mocking (MSW)

**Problem:** Frontend integration tests (Layer 2) need realistic API responses without running the backend.

**Solution:** Mock Service Worker (MSW) intercepts `fetch` calls in Jest's jsdom environment. Handlers return JSON matching the actual API response schemas defined in `docs/technical-design.md`.

```typescript
// apps/web/__tests__/integration/handlers/resources.ts
import { http, HttpResponse } from 'msw'

export const resourceHandlers = [
  http.get('/api/resources', () => {
    return HttpResponse.json({
      items: [
        { id: 'uuid-1', title: 'Mock Resource', status: 'READY', tags: ['AI'] },
      ],
      total: 1,
    })
  }),
  http.post('/api/resources', () => {
    return HttpResponse.json({ id: 'uuid-new', status: 'PENDING' }, { status: 202 })
  }),
]
```

MSW handlers defined here can also be reused in Playwright E2E specs (MSW supports browser service worker mode).

### 4.5 E2E Route Interception (Playwright)

**Problem:** E2E tests run a full stack but OAuth and LLM still cannot hit real endpoints.

**Solution:** Two complementary mechanisms:

1. **App-level mock flags** — The running app stack uses `LLM_MOCK=true` and `OAUTH_MOCK=true` env vars to activate mock implementations at startup (see Section 6.1).
2. **Playwright route interception** — For any external redirect that reaches the browser (e.g. the OAuth redirect), Playwright intercepts and fakes the callback:

```typescript
// tests/e2e/fixtures/auth.ts
export async function bypassOAuth(page: Page) {
  // Intercept the provider redirect and simulate a successful callback
  await page.route('**/auth/callback*', async route => {
    // Let the actual callback handler run — we injected a mock token upstream
    await route.continue()
  })
}
```

---

## 5. pytest Markers and CI Groups

### 5.1 Marker Definitions

Add to `apps/api/pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
markers = [
  "integration: requires real PostgreSQL + Neo4j (run make infra-up first)",
  "int_health:     INT-001–002: health check and error format",
  "int_auth:       INT-003–012: OAuth login, account linking, /auth/me",
  "int_resources:  INT-013–023: resource CRUD",
  "int_worker:     INT-024–028: async worker pipeline",
  "int_graph:      INT-029–035: knowledge graph update and exploration",
  "int_chat:       INT-036–040: chat agent and conversation history",
  "int_e2e:        Layer 3 Playwright E2E tests (full stack)",
  "int_deploy:     INT-053–055: Docker, Helm, ArgoCD",
]
```

Every INT test carries **two** markers — the infrastructure marker and a group marker:

```python
@pytest.mark.integration
@pytest.mark.int_auth
async def test_int_003_first_time_login(client, db_session, mock_oauth):
    ...
```

### 5.2 CI Group Selection via INT_GROUPS

The `INT_GROUPS` environment variable is a comma-separated list of group names. The Makefile translates it to a pytest marker expression:

```bash
# Default CI: auth + resources only (fast, stable)
INT_GROUPS=auth,resources make int-test-ci

# Nightly: add worker and graph
INT_GROUPS=auth,resources,worker,graph make int-test-ci

# Run everything
make int-test
```

### 5.3 Default CI Pipeline Groups

| CI Trigger           | INT_GROUPS                         | Infra Required        |
|----------------------|------------------------------------|-----------------------|
| Every PR / push      | `auth,resources`                   | PostgreSQL only       |
| Nightly scheduled    | `auth,resources,worker,graph,chat` | PostgreSQL + Neo4j    |
| Release / manual     | All + E2E + web integration        | Full stack            |
| Frontend-only PR     | Web integration (Jest + MSW)       | None                  |
| Deploy PR            | `deploy`                           | k8s cluster (manual)  |

---

## 6. Test Data and Fixtures

### 6.1 API Integration conftest (`apps/api/tests/integration/conftest.py`)

```python
import os
import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models.database import Base
from models.user import User, UserAccount
from core.jwt import create_access_token

@pytest.fixture(scope="session")
async def pg_engine():
    """Real PostgreSQL engine. Schema created once per session."""
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(pg_engine):
    """Transactional session rolled back after each test — no cleanup needed."""
    async with pg_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn)
        yield session
        await session.rollback()

@pytest.fixture
def mock_oauth(respx_mock):
    """Activates all OAuth provider mocks for the duration of a test."""
    from tests.mocks.oauth_mock import setup_twitter_oauth_mock, setup_google_oauth_mock
    setup_twitter_oauth_mock(respx_mock)
    setup_google_oauth_mock(respx_mock)
    return respx_mock

@pytest.fixture
def mock_llm():
    """Replaces the LLM client with MockLLMClient."""
    from tests.mocks.llm_mock import MockLLMClient
    with patch("services.llm_processor.get_llm_client", return_value=MockLLMClient()):
        yield

@pytest.fixture
def mock_fetch(respx_mock):
    """Default: all external URL fetches return a mock HTML page."""
    from tests.mocks.provider_fetch_mock import setup_fetch_success
    setup_fetch_success(respx_mock, url="https://example.com/article")
    return respx_mock

@pytest.fixture
async def test_user(db_session) -> User:
    user = User(display_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()
    account = UserAccount(
        user_id=user.id, provider="twitter",
        external_id="twitter-123", access_token="mock-token"
    )
    db_session.add(account)
    await db_session.flush()
    return user

@pytest.fixture
async def auth_headers(test_user) -> dict:
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

### 6.2 Factory Helpers (`apps/api/tests/integration/factories.py`)

Plain async functions — no external factory library:

```python
from models.resource import Resource

async def make_resource(db, owner_id, **kwargs) -> Resource:
    defaults = {
        "content_type": "url",
        "original_content": "https://example.com/article",
        "status": "READY",
        "title": "Test Article",
        "summary": "A test summary.",
        "tags": ["AI", "Testing"],
    }
    resource = Resource(owner_id=owner_id, **{**defaults, **kwargs})
    db.add(resource)
    await db.flush()
    return resource
```

### 6.3 App-Level Mock Flags for E2E

The running app checks env flags and switches DI bindings at startup:

```python
# apps/api/main.py (additions)
if os.getenv("LLM_MOCK") == "true":
    from tests.mocks.llm_mock import MockLLMClient
    app.dependency_overrides[get_llm_client] = lambda: MockLLMClient()

if os.getenv("OAUTH_MOCK") == "true":
    from tests.mocks.oauth_mock import MockOAuthClient
    app.dependency_overrides[get_oauth_client] = lambda: MockOAuthClient()
```

These flags are only set in `docker-compose.e2e.yml` — never in production compose files.

---

## 7. Playwright E2E Setup

### 7.1 Configuration

```typescript
// tests/e2e/playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './specs',
  use: {
    baseURL: process.env.APP_URL ?? 'http://localhost:3000',
    storageState: 'fixtures/auth-state.json',  // Pre-authenticated context
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // Filter to specific INT groups via INT_GROUPS env var
  grep: process.env.INT_GROUPS
    ? new RegExp(process.env.INT_GROUPS.split(',').map(g => `@int_${g}`).join('|'))
    : undefined,
  webServer: {
    command: 'docker compose -f docker-compose.e2e.yml up',
    url: 'http://localhost:8000/health',
    reuseExistingServer: true,
  },
})
```

### 7.2 Page Object Model

```typescript
// tests/e2e/fixtures/pages.ts
export class ResourcesPage {
  constructor(private page: Page) {}

  async submitUrl(url: string) {
    await this.page.fill('[data-testid="url-input"]', url)
    await this.page.click('[data-testid="submit-resource"]')
  }

  async waitForStatus(resourceTitle: string, status: string) {
    await this.page.waitForSelector(
      `[data-testid="resource-card"]:has-text("${resourceTitle}") [data-status="${status}"]`,
      { timeout: 15000 }
    )
  }
}

export class GraphPage {
  constructor(private page: Page) {}

  async clickNode(label: string) {
    await this.page.click(`[data-node-label="${label}"]`)
  }

  async waitForPanel() {
    await this.page.waitForSelector('[data-testid="node-resource-panel"]')
  }
}
```

### 7.3 `data-testid` Contract

E2E tests rely on `data-testid` attributes. These are the required attributes implementers must add to UI components:

| Component | Required `data-testid` |
|-----------|------------------------|
| URL input field | `url-input` |
| Submit resource button | `submit-resource` |
| Resource card | `resource-card` |
| Status badge on resource card | `resource-status` (+ `data-status` attribute) |
| Graph node | `graph-node` (+ `data-node-label` attribute) |
| Node resource panel | `node-resource-panel` |
| Chat input | `chat-input` |
| Chat submit button | `chat-submit` |
| Chat message | `chat-message` |
| Settings linked account row | `linked-account-row` |
| Disconnect button | `disconnect-account` |

---

## 8. Makefile Targets

Add to the root `Makefile`:

```makefile
# ── Integration Tests ──────────────────────────────────────────────────────

INT_GROUPS ?= auth,resources

# Layer 1: API integration tests — CI-configurable groups
int-test-ci:
	@echo "── API integration tests (CI groups: $(INT_GROUPS)) ────"
	$(eval MARKERS := $(shell echo "$(INT_GROUPS)" | tr ',' '\n' | sed 's/^/int_/' | paste -sd ' or '))
	cd apps/api && uv run pytest -m "integration and ($(MARKERS))" -v

# Layer 1: All API integration tests
int-test:
	@echo "── API integration tests (all groups) ─────────────────"
	@echo "   (requires: make infra-up)"
	cd apps/api && uv run pytest -m "integration" -v

# Layer 2: Frontend integration tests (Jest + MSW, no infra needed)
int-test-web:
	@echo "── Frontend integration tests (Jest + MSW) ────────────"
	cd apps/web && npm test -- --testPathPattern="integration" --watchAll=false

# Layer 3: E2E tests (Playwright, full stack)
int-test-e2e:
	@echo "── E2E tests (Playwright) ──────────────────────────────"
	@echo "   (requires: full stack via docker-compose.e2e.yml)"
	cd tests/e2e && npx playwright test

# All layers
int-test-full: int-test int-test-web int-test-e2e
```

---

## 9. Key Design Decisions

### Decision 1: `respx` over `unittest.mock` for external HTTP

**Why:** `respx` intercepts at the `httpx` transport layer — the actual HTTP plumbing the app uses. Tests exercise real serialization and error handling, not mocked function return values.

**Rejected:** `unittest.mock.patch` on individual functions — couples tests to internal implementation details.

### Decision 2: App-level env flags for E2E mock injection

**Why:** Playwright E2E tests cannot inject Python dependencies mid-flight. Env flags (`LLM_MOCK=true`) switch the DI container at startup, keeping test code clean and production code unchanged.

**Rejected:** A separate parallel "test app" — drifts from production behavior over time.

### Decision 3: MSW for frontend integration (not Cypress component tests)

**Why:** MSW runs in Jest's jsdom alongside existing unit tests — no new runner. MSW handlers are reusable between Jest and Playwright (browser service worker mode).

**Rejected:** Cypress component testing — adds a third test framework.

### Decision 4: Transactional rollback for API integration tests

**Why:** Each test gets a session that rolls back after the test — no manual cleanup or truncation. Faster and order-independent.

**Trade-off:** Cannot test behavior that spans transaction boundaries. Those cases go in Layer 3 E2E.

### Decision 5: No `factory_boy`

**Why:** Plain async helper functions in `factories.py` are sufficient and have zero extra dependencies. `factory_boy`'s async support is experimental.

---

## 10. Implementation Plan (INT-000 subtasks)

INT-000 is delivered in five sequential subtasks:

| Subtask | Deliverable | Effort |
|---------|-------------|--------|
| INT-000-a | `tests/mocks/` — oauth_mock.py, llm_mock.py, provider_fetch_mock.py | S |
| INT-000-b | `apps/api/tests/integration/conftest.py` + `factories.py` | S |
| INT-000-c | `apps/web/__tests__/integration/` — MSW setup + handler stubs for all features | S |
| INT-000-d | Makefile targets + pyproject.toml markers + `docker-compose.e2e.yml` | XS |
| INT-000-e | `tests/e2e/` — playwright.config.ts + login fixture + one smoke spec per group | M |

Once INT-000 is complete, individual INT-001 through INT-055 tests are written as their DEV dependencies land.

---

## 11. What This Framework Does NOT Cover

- **Load / performance testing** — out of scope for INT tasks.
- **Visual regression** — not represented in BDD scenarios.
- **Contract testing (Pact)** — considered for API mocking; rejected in favor of simpler respx + MSW given single-team ownership of both API and frontend.
- **Deployment INT tests (INT-053–055)** — these are smoke tests against a real k8s cluster, not in-process integration tests. They run in a separate CI job triggered on release, outside this framework.
