import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_db_health_endpoint_without_db():
    """Test the database health endpoint (will fail without actual DB)."""
    response = client.get("/db-health")
    # This will fail due to no database connection, but the endpoint works
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # Should be a database error since we don't have a real DB running
    assert data["status"] == "database error"
    assert "error" in data