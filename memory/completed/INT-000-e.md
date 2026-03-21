# INT-000-e: Playwright E2E Test Skeleton

**Type:** Integration Test Framework (Layer 3)
**Priority:** P2
**Status:** Complete
**Created:** 2026-03-20
**Target:** Set up Playwright E2E test infrastructure

## Requirements

Set up Playwright E2E testing skeleton for full-stack integration tests (Layer 3 of the integration test framework). This provides the foundation for complete user journey testing with real browser automation.

### Scope
1. Create E2E test directory structure under `tests/e2e/`
2. Install and configure Playwright with `@playwright/test`
3. Set up Playwright config with proper settings for CI/local execution
4. Create auth fixture for logged-in state management
5. Create page object models for key pages:
   - ResourcesPage (resource list, detail, forms)
   - GraphPage (graph visualization)
6. Create placeholder spec files for all 5 BDD groups with test.todo() placeholders:
   - auth.spec.ts (includes one working health check smoke test)
   - resources.spec.ts
   - graph.spec.ts
   - chat.spec.ts
   - pipeline.spec.ts

### Directory Structure
```
tests/e2e/
├── package.json                    # Fresh package.json with @playwright/test
├── playwright.config.ts            # Playwright configuration
├── fixtures/
│   └── auth.ts                     # Auth fixture for logged-in state
├── pages/
│   ├── ResourcesPage.ts            # Resource pages (list, detail, forms)
│   └── GraphPage.ts                # Graph visualization page
├── auth.spec.ts                    # Auth flows (includes health check smoke test)
├── resources.spec.ts               # Resource CRUD E2E tests
├── graph.spec.ts                   # Graph visualization E2E tests
├── chat.spec.ts                    # Chat functionality E2E tests
└── pipeline.spec.ts               # End-to-end pipeline tests
```

### Implementation Requirements
- Use fresh package.json in tests/e2e/ with minimal Playwright setup
- Configure Playwright for both CI and local execution
- Auth fixture should handle login state persistence across tests
- Page objects should encapsulate UI interactions and selectors
- All spec files should use test.todo() except one health check in auth.spec.ts
- Health check test should just call /health endpoint to verify stack is running

## Acceptance Criteria

- [ ] `tests/e2e/` directory structure created
- [ ] `package.json` with @playwright/test dependency
- [ ] `playwright.config.ts` with proper configuration
- [ ] Auth fixture in `fixtures/auth.ts`
- [ ] Page objects in `pages/` (ResourcesPage, GraphPage)
- [ ] Spec files for all 5 BDD groups with test.todo() placeholders
- [ ] One working health check smoke test in auth.spec.ts
- [ ] All files pass basic import/syntax checks
- [ ] Committed on branch `feature/int-000-e-playwright-e2e`
- [ ] PR created with title "INT-000-e: Playwright E2E skeleton"

## Progress Log

2026-03-20 21:02 — Task created, implementing Playwright E2E test skeleton
2026-03-20 — Task completed and merged via PR #73