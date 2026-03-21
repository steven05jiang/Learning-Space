"""
Integration tests for health endpoints.

Tests:
- INT-001: GET /health returns 200 with status ok
- INT-002: Bad request returns standard error format
"""

import pytest
from httpx import AsyncClient

from main import app


@pytest.mark.integration
@pytest.mark.int_health
async def test_get_health_returns_ok():
    """INT-001: GET /health → 200 OK; body contains {"status": "ok"} or similar"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # The health endpoint returns {"status": "healthy"} according to the router
    assert data["status"] in ["ok", "healthy"]


@pytest.mark.integration
@pytest.mark.int_health
async def test_bad_request_returns_standard_error_format():
    """
    INT-002: Any endpoint hit with a bad request returns the standard error
    response schema
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send a malformed request to trigger error handling
        response = await client.get("/health/nonexistent-endpoint")

    assert response.status_code == 404
    data = response.json()

    # Check error format matches DEV-038 pattern:
    # {"detail": ..., "code": ..., "status": ...}
    assert "detail" in data
    assert "code" in data
    assert "status" in data
    assert data["status"] == 404
    assert isinstance(data["detail"], str)
    assert isinstance(data["code"], str)
