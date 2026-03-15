from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_db_health_endpoint():
    """Test the database health endpoint."""
    response = client.get("/db-health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # Should be either healthy or error depending on DB availability
    assert data["status"] in ["database healthy", "database error"]
