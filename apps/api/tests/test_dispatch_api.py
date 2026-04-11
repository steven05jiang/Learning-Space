"""Tests for dispatch API functionality."""

import pytest
from fastapi.testclient import TestClient

from workers.dispatch_api import dispatch_app


class TestDispatchAPI:
    """Test dispatch API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with dispatch app."""
        return TestClient(dispatch_app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "queue_running" in data
        assert "queue_size" in data

    def test_dispatch_valid_function(self, client):
        """Test dispatching a valid function."""
        response = client.post(
            "/dispatch",
            json={
                "job_id": "test-job-123",
                "function_name": "process_resource",
                "args": ["resource-456"],
                "kwargs": {"option": "value"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "queued"
        assert "message" in data

    def test_dispatch_sync_graph(self, client):
        """Test dispatching sync_graph function."""
        response = client.post(
            "/dispatch",
            json={
                "job_id": "sync-job-789",
                "function_name": "sync_graph",
                "args": ["entity-123"],
                "kwargs": {"operation": "update"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "sync-job-789"
        assert data["status"] == "queued"

    def test_dispatch_invalid_function(self, client):
        """Test dispatching an invalid function name."""
        response = client.post(
            "/dispatch",
            json={
                "job_id": "test-job",
                "function_name": "invalid_function",
                "args": [],
                "kwargs": {},
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "Unknown function" in data["detail"]

    def test_dispatch_empty_args(self, client):
        """Test dispatching with empty args list."""
        response = client.post(
            "/dispatch",
            json={
                "job_id": "test-job",
                "function_name": "process_resource",
                "args": [],
                "kwargs": {},
            },
        )
        assert response.status_code == 200

    def test_dispatch_missing_job_id(self, client):
        """Test dispatching without job_id."""
        response = client.post(
            "/dispatch",
            json={
                "function_name": "process_resource",
                "args": [],
                "kwargs": {},
            },
        )
        assert response.status_code == 422  # Validation error

    def test_dispatch_missing_function_name(self, client):
        """Test dispatching without function_name."""
        response = client.post(
            "/dispatch",
            json={
                "job_id": "test-job",
                "args": [],
                "kwargs": {},
            },
        )
        assert response.status_code == 422  # Validation error
