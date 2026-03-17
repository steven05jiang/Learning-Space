"""Tests for jobs API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestJobsAPI:
    """Test jobs API endpoints."""

    def test_enqueue_resource_processing_success(self):
        """Test successful resource processing job enqueueing."""
        with patch('routers.jobs.queue_service.enqueue_resource_processing') as mock_enqueue:
            mock_enqueue.return_value = "job123"

            response = client.post(
                "/jobs/process-resource",
                json={"resource_id": "resource123", "options": {"key": "value"}}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job123"
            assert "resource123" in data["message"]

    def test_enqueue_resource_processing_empty_id(self):
        """Test resource processing with empty resource_id."""
        with patch('routers.jobs.queue_service.enqueue_resource_processing') as mock_enqueue:
            mock_enqueue.side_effect = ValueError("resource_id cannot be empty")

            response = client.post(
                "/jobs/process-resource",
                json={"resource_id": "", "options": {}}
            )

            assert response.status_code == 400
            assert "resource_id cannot be empty" in response.json()["detail"]

    def test_enqueue_resource_processing_missing_resource_id(self):
        """Test resource processing with missing resource_id."""
        response = client.post(
            "/jobs/process-resource",
            json={"options": {}}
        )

        assert response.status_code == 422  # Validation error

    def test_enqueue_graph_sync_success(self):
        """Test successful graph sync job enqueueing."""
        with patch('routers.jobs.queue_service.enqueue_graph_sync') as mock_enqueue:
            mock_enqueue.return_value = "job456"

            response = client.post(
                "/jobs/sync-graph",
                json={"entity_id": "entity123", "operation": "create"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job456"
            assert "entity123" in data["message"]

    def test_enqueue_graph_sync_default_operation(self):
        """Test graph sync with default operation."""
        with patch('routers.jobs.queue_service.enqueue_graph_sync') as mock_enqueue:
            mock_enqueue.return_value = "job789"

            response = client.post(
                "/jobs/sync-graph",
                json={"entity_id": "entity123"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job789"

    def test_enqueue_graph_sync_invalid_operation(self):
        """Test graph sync with invalid operation."""
        with patch('routers.jobs.queue_service.enqueue_graph_sync') as mock_enqueue:
            mock_enqueue.side_effect = ValueError("operation must be one of")

            response = client.post(
                "/jobs/sync-graph",
                json={"entity_id": "entity123", "operation": "invalid"}
            )

            assert response.status_code == 400
            assert "operation must be one of" in response.json()["detail"]

    def test_get_job_status_success(self):
        """Test successful job status retrieval."""
        mock_status = {
            "id": "job123",
            "status": "completed",
            "result": {"success": True},
            "enqueue_time": "2026-03-17T00:00:00Z",
            "start_time": "2026-03-17T00:01:00Z",
            "finish_time": "2026-03-17T00:02:00Z",
        }

        with patch('routers.jobs.queue_service.get_job_status') as mock_get_status:
            mock_get_status.return_value = mock_status

            response = client.get("/jobs/status/job123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "job123"
            assert data["status"] == "completed"
            assert data["result"] == {"success": True}

    def test_get_job_status_not_found(self):
        """Test job status when job not found."""
        with patch('routers.jobs.queue_service.get_job_status') as mock_get_status:
            mock_get_status.return_value = None

            response = client.get("/jobs/status/nonexistent")

            assert response.status_code == 404
            assert "Job not found" in response.json()["detail"]

    def test_enqueue_internal_error(self):
        """Test handling of internal errors during job enqueueing."""
        with patch('routers.jobs.queue_service.enqueue_resource_processing') as mock_enqueue:
            mock_enqueue.side_effect = Exception("Redis connection failed")

            response = client.post(
                "/jobs/process-resource",
                json={"resource_id": "resource123"}
            )

            assert response.status_code == 500
            assert "Failed to enqueue job" in response.json()["detail"]

    def test_get_status_internal_error(self):
        """Test handling of internal errors during status retrieval."""
        with patch('routers.jobs.queue_service.get_job_status') as mock_get_status:
            mock_get_status.side_effect = Exception("Redis connection failed")

            response = client.get("/jobs/status/job123")

            assert response.status_code == 500
            assert "Failed to get job status" in response.json()["detail"]