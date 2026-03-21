# INT-000-b: API Integration Test Fixtures (conftest + factories)

**Type**: Integration Test Framework
**Status**: In Progress
**Branch**: feature/int-000-b-api-fixtures

## Requirements

Create API integration test fixtures for the backend integration tests. This provides Layer 1 pytest fixtures that extend beyond unit test fixtures to support real database connections, OAuth mocking, LLM service mocking, and resource factories for integration test scenarios.

### Scope
1. Create enhanced `conftest.py` with integration test fixtures:
   - `pg_engine` - Real PostgreSQL connection for integration tests
   - `db_session` - Enhanced DB session for integration tests
   - `mock_oauth` - OAuth provider mocking
   - `mock_llm` - LLM service mocking
   - `mock_fetch` - HTTP fetch mocking
   - `test_user` - Enhanced user factory
   - `auth_headers` - Auth headers for integration tests

2. Create factory helpers for test data:
   - `make_resource` - Resource creation helper with realistic data

3. All fixtures should be compatible with pytest integration markers
4. Fixtures should support offline testing (no real external APIs)
5. Mock implementations should match real service interfaces

### Files to Create
- `apps/api/tests/integration/conftest.py` - Enhanced integration fixtures
- `apps/api/tests/integration/factories.py` - Test data factory helpers

### Integration Test Requirements
- Use real PostgreSQL database (configured via test environment)
- Mock external services (OAuth providers, LLM APIs, external HTTP calls)
- Support `@pytest.mark.integration` test isolation
- Provide rich test data factories for complex integration scenarios
- Ensure all mocks are offline-safe

## Progress Log

2026-03-20 15:30 — Task created, implementing API integration test fixtures