# INT-000-c: MSW Frontend Integration Test Scaffold

**Type**: Integration Test Framework
**Status**: Complete
**Branch**: feature/int-000-c-msw-frontend
**PR**: #69 (merged)

## Requirements

Set up frontend integration testing scaffold for the web application using simple fetch mocking. This provides the foundation for testing frontend components with mocked backend APIs.

### Scope
1. Create integration test directory structure under `apps/web/__tests__/integration/`
2. Set up fetch mock handlers for core API endpoints:
   - Auth endpoints (login, logout, user profile)
   - Resources endpoints (CRUD operations)
   - Graph endpoints (Neo4j graph data)
   - Chat endpoints (LLM interactions)
3. Create placeholder test files for integration scenarios
4. Verify test runner works with fetch mocking setup

### Directory Structure
```
apps/web/__tests__/integration/
├── setup.ts                   # Test setup and fetch mocking configuration
├── mocks/
│   ├── auth.ts                # Auth API mock data and handlers
│   ├── resources.ts           # Resources API mock data and handlers
│   ├── graph.ts               # Graph API mock data and handlers
│   └── chat.ts                # Chat API mock data and handlers
├── auth.integration.test.ts   # Auth flow integration tests
├── resources.integration.test.ts # Resources CRUD integration tests
├── graph.integration.test.ts  # Graph visualization integration tests
└── chat.integration.test.ts   # Chat functionality integration tests
```

### Test Framework Requirements
- Use simple fetch mocking for API responses (offline-safe)
- Tests should use React Testing Library
- Each mock file should export handlers and mock data
- Setup file should configure global fetch mock for Jest environment
- All test files should have it.todo() placeholders initially

## Progress Log

2026-03-20 13:45 — Task created, implementing integration test scaffold
2026-03-20 14:20 — Switched from MSW to simple fetch mocking due to Jest ESM compatibility issues
2026-03-20 14:30 — Successfully implemented fetch mock handlers and test structure, all tests passing
2026-03-20 16:15 — PR #69 merged, task complete