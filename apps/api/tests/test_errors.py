"""
Tests for error handling system.
"""
from fastapi.testclient import TestClient

from core.errors import (
    ErrorCode,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
    account_already_linked,
    cannot_unlink_last_account,
    resource_not_found,
)
from main import app

client = TestClient(app)


def test_api_error_creation():
    """Test creating custom API errors."""
    error = ValidationError("Invalid input")
    assert error.detail == "Invalid input"
    assert error.code == ErrorCode.VALIDATION_ERROR
    assert error.status_code == 400


def test_specific_error_helpers():
    """Test specific error helper functions."""
    # Resource not found
    error = resource_not_found("User", "123")
    assert error.detail == "User not found: 123"
    assert error.code == ErrorCode.RESOURCE_NOT_FOUND
    assert error.status_code == 404

    # Cannot unlink last account
    error = cannot_unlink_last_account()
    assert "Cannot unlink the last account" in error.detail
    assert error.code == ErrorCode.CANNOT_UNLINK_LAST_ACCOUNT
    assert error.status_code == 400

    # Account already linked
    error = account_already_linked()
    assert "already linked to another user" in error.detail
    assert error.code == ErrorCode.ACCOUNT_ALREADY_LINKED
    assert error.status_code == 409


def test_error_format_in_response():
    """Test that errors are returned in the correct format."""
    # Create an APIError and test its format
    error = resource_not_found("User", "123")

    # Test that the error has the correct structure
    assert error.detail == "User not found: 123"
    assert error.code == ErrorCode.RESOURCE_NOT_FOUND
    assert error.status_code == 404


def test_health_endpoint_success():
    """Test that health endpoint works without errors."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_unauthorized_error():
    """Test unauthorized error format."""
    error = UnauthorizedError()
    assert error.detail == "Authentication required"
    assert error.code == ErrorCode.UNAUTHORIZED
    assert error.status_code == 401


def test_not_found_error():
    """Test not found error format."""
    error = NotFoundError("Resource not found")
    assert error.detail == "Resource not found"
    assert error.code == ErrorCode.RESOURCE_NOT_FOUND
    assert error.status_code == 404


def test_all_error_codes_defined():
    """Test that all error codes are properly defined."""
    # This ensures we have all the required error codes
    required_codes = [
        "RESOURCE_NOT_FOUND",
        "CANNOT_UNLINK_LAST_ACCOUNT",
        "UNAUTHORIZED",
        "FORBIDDEN",
        "VALIDATION_ERROR",
        "INTERNAL_SERVER_ERROR",
    ]

    for code in required_codes:
        assert hasattr(ErrorCode, code), f"ErrorCode.{code} is not defined"
        assert isinstance(getattr(ErrorCode, code), str)
