# INT-000-a: Python Mock Modules for Integration Tests

**Type:** Integration Test Infrastructure
**Priority:** P2
**Status:** Active
**Created:** 2026-03-20
**Target:** Framework setup for offline integration tests

## Requirements

Create Python mock modules to support offline integration testing:

1. **OAuth Mock** (`tests/mocks/oauth_mock.py`):
   - Mock Twitter OAuth responses with realistic user data
   - Support successful login flows
   - Mock provider API responses (Twitter user profiles, etc.)

2. **LLM Mock** (`tests/mocks/llm_mock.py`):
   - Mock Anthropic Claude API responses
   - Deterministic responses for title/summary/tags generation
   - Support for both success and error scenarios

3. **Provider Fetch Mock** (`tests/mocks/provider_fetch_mock.py`):
   - Mock HTTP responses for URL content fetching
   - Support various content types (HTML, JSON, etc.)
   - Mock both public and authenticated provider content

4. **Dependencies**:
   - Add `respx` for HTTP mocking if not already present
   - Ensure all mock modules are importable

## Acceptance Criteria

- [ ] `tests/__init__.py` exists (empty)
- [ ] `tests/mocks/__init__.py` exists (empty)
- [ ] `tests/mocks/oauth_mock.py` provides OAuth mocking functions
- [ ] `tests/mocks/llm_mock.py` provides LLM client mocking
- [ ] `tests/mocks/provider_fetch_mock.py` provides HTTP fetch mocking
- [ ] `respx` added as dev dependency if missing
- [ ] All modules importable without errors
- [ ] Committed on branch `feature/int-000-a-python-mocks`
- [ ] PR created with title "INT-000-a: Python mock modules for integration tests"

## Progress Log

2026-03-20 13:45 — Task created, implementing Python mock modules