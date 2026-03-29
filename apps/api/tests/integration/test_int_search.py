"""
Integration tests for resource search functionality.

Tests:
- INT-056: User searches for resources by keyword — returns ranked READY resources only

This test verifies the keyword search flow using real PostgreSQL with the GIN index
in place. It creates a set of READY resources with different titles/summaries/tags,
creates PENDING/FAILED resources (which should be excluded), and validates that
the search endpoint returns only READY resources with proper ranking.
"""

import pytest

from models.resource import ResourceStatus
from models.user import User
from tests.integration.factories import make_resource


@pytest.mark.integration
@pytest.mark.search
async def test_keyword_search_returns_ready_resources_only_with_rank(
    client, auth_headers, db_session, test_user: User
):
    """
    INT-056: User searches for resources by keyword.

    Returns ranked READY resources only. This test validates that:
    - Only READY resources are returned (PENDING/FAILED excluded)
    - Results are ordered by relevance (rank DESC)
    - Each result has a rank field > 0
    - Resources belonging to another user are excluded
    - The response format matches {resources: [...], total: N}
    """
    # Create another user to test user isolation
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    # Create READY resources for the test user with different content
    # These should match the search term "python"
    ready_resource_1 = await make_resource(
        db_session,
        test_user.id,
        title="Python Programming Guide",
        summary="A comprehensive guide to Python development and best practices",
        tags=["python", "programming", "tutorial"],
        status=ResourceStatus.READY,
        original_content="https://example.com/python-guide",
    )

    ready_resource_2 = await make_resource(
        db_session,
        test_user.id,
        title="Machine Learning with Python",
        summary="Learn machine learning using Python libraries like scikit-learn",
        tags=["machine-learning", "python", "data-science"],
        status=ResourceStatus.READY,
        original_content="https://example.com/ml-python",
    )

    # Create a READY resource that should NOT match our search
    non_matching_resource = await make_resource(
        db_session,
        test_user.id,
        title="JavaScript Fundamentals",
        summary="Learn the basics of JavaScript programming",
        tags=["javascript", "web", "frontend"],
        status=ResourceStatus.READY,
        original_content="https://example.com/js-fundamentals",
    )

    # Create resources with different statuses that should be EXCLUDED
    pending_resource = await make_resource(
        db_session,
        test_user.id,
        title="Advanced Python Techniques",
        summary="Deep dive into advanced Python programming concepts",
        tags=["python", "advanced"],
        status=ResourceStatus.PENDING,
        original_content="https://example.com/python-advanced",
    )

    failed_resource = await make_resource(
        db_session,
        test_user.id,
        title="Python Testing Guide",
        summary="Comprehensive testing strategies for Python applications",
        tags=["python", "testing"],
        status=ResourceStatus.FAILED,
        original_content="https://example.com/python-testing",
    )

    # Create a READY resource for another user (excluded due to user isolation)
    other_user_resource = await make_resource(
        db_session,
        other_user.id,
        title="Python for Beginners",
        summary="Introduction to Python programming for newcomers",
        tags=["python", "beginner"],
        status=ResourceStatus.READY,
        original_content="https://example.com/python-intro",
    )

    await db_session.commit()

    # Perform the search
    response = await client.get(
        "/resources/search",
        params={"q": "python"},
        headers=auth_headers,
    )

    # Validate response structure and status
    assert response.status_code == 200
    data = response.json()
    assert "resources" in data
    assert "total" in data

    # Validate that we got exactly 2 results (only READY resources from test_user)
    assert data["total"] == 2
    assert len(data["resources"]) == 2

    # Validate that all returned resources are READY
    for resource in data["resources"]:
        assert resource["status"] == "READY"
        assert resource["owner_id"] == str(test_user.id)

    # Validate that all results have a rank field > 0
    for resource in data["resources"]:
        assert "rank" in resource
        assert resource["rank"] > 0

    # Validate that results are ordered by relevance (rank DESC)
    ranks = [resource["rank"] for resource in data["resources"]]
    assert ranks == sorted(ranks, reverse=True), "Results should be ordered DESC"

    # Validate that the correct resources were returned (by checking IDs)
    returned_ids = {resource["id"] for resource in data["resources"]}
    expected_ids = {str(ready_resource_1.id), str(ready_resource_2.id)}
    assert returned_ids == expected_ids

    # Validate that excluded resources are not in results
    excluded_ids = {
        str(non_matching_resource.id),
        str(pending_resource.id),
        str(failed_resource.id),
        str(other_user_resource.id),
    }
    assert returned_ids.isdisjoint(excluded_ids), "Excluded resources not in results"


@pytest.mark.integration
@pytest.mark.search
async def test_search_with_tag_filter(
    client, auth_headers, db_session, test_user: User
):
    """
    INT-057: User filters search results by tag — results narrowed to matching tag.

    Validates that the tag parameter works correctly and narrows results
    to resources containing the specified tag. Tests both valid and nonexistent tags.
    """
    # Create resources with different tags
    python_tutorial = await make_resource(
        db_session,
        test_user.id,
        title="Python Tutorial",
        summary="Learn Python programming step by step",
        tags=["python", "tutorial", "beginner"],
        status=ResourceStatus.READY,
    )

    python_advanced = await make_resource(
        db_session,
        test_user.id,
        title="Advanced Python",
        summary="Advanced Python programming techniques",
        tags=["python", "advanced"],
        status=ResourceStatus.READY,
    )

    await db_session.commit()

    # Test 1: Search for "python" with tag filter for "tutorial"
    # Should only return the tutorial resource
    response = await client.get(
        "/resources/search",
        params={"q": "python", "tag": "tutorial"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Should only return the tutorial resource
    assert data["total"] == 1
    assert len(data["resources"]) == 1
    assert data["resources"][0]["id"] == str(python_tutorial.id)
    assert "tutorial" in data["resources"][0]["tags"]

    # Test 2: Search for "python" with tag filter for "advanced"
    # Should only return the advanced resource
    response = await client.get(
        "/resources/search",
        params={"q": "python", "tag": "advanced"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["resources"]) == 1
    assert data["resources"][0]["id"] == str(python_advanced.id)
    assert "advanced" in data["resources"][0]["tags"]

    # Test 3: Search with a nonexistent tag
    # Should return empty list (total=0), not an error
    response = await client.get(
        "/resources/search",
        params={"q": "python", "tag": "nonexistent"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["resources"]) == 0


@pytest.mark.integration
@pytest.mark.search
async def test_search_no_results(client, auth_headers, db_session, test_user: User):
    """
    INT-056: Test search with no matching results.

    Validates that the endpoint returns empty results gracefully
    when no resources match the search query.
    """
    # Create a resource that won't match our search
    await make_resource(
        db_session,
        test_user.id,
        title="JavaScript Guide",
        summary="Complete guide to JavaScript programming",
        tags=["javascript", "web"],
        status=ResourceStatus.READY,
    )

    await db_session.commit()

    # Search for something that doesn't match
    response = await client.get(
        "/resources/search",
        params={"q": "nonexistent term"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["resources"]) == 0


@pytest.mark.integration
@pytest.mark.search
async def test_search_unauthenticated_returns_401(client, db_session):
    """
    INT-056: Test that unauthenticated search requests are rejected.

    Validates that search requires authentication.
    """
    response = await client.get(
        "/resources/search",
        params={"q": "python"},
        # No auth headers
    )

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.search
async def test_search_empty_query_returns_400(client, auth_headers, db_session):
    """
    INT-058: Empty query returns 400 validation error.

    Validates that empty queries are rejected with SEARCH_QUERY_EMPTY error.
    """
    # Test with empty string
    response = await client.get(
        "/resources/search",
        params={"q": ""},
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "SEARCH_QUERY_EMPTY"
    assert "empty" in data["detail"]["message"].lower()

    # Test with whitespace-only string
    response = await client.get(
        "/resources/search",
        params={"q": "   "},
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "SEARCH_QUERY_EMPTY"
    assert "empty" in data["detail"]["message"].lower()


@pytest.mark.integration
@pytest.mark.search
async def test_search_overlong_query_returns_400(client, auth_headers, db_session):
    """
    INT-058: Overlong query returns 400 validation error.

    Validates that queries exceeding 500 characters are rejected with
    SEARCH_QUERY_TOO_LONG error.
    """
    # Create a query that's exactly 501 characters
    long_query = "a" * 501

    response = await client.get(
        "/resources/search",
        params={"q": long_query},
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "SEARCH_QUERY_TOO_LONG"
    assert "exceeds" in data["detail"]["message"].lower()
    assert "500" in data["detail"]["message"]


@pytest.mark.integration
@pytest.mark.search
async def test_search_missing_query_param_returns_422(client, auth_headers, db_session):
    """
    INT-058: Missing q parameter returns 422 validation error.

    Validates that FastAPI's required field validation works correctly
    when the q parameter is completely omitted.
    """
    response = await client.get(
        "/resources/search",
        # No params at all - missing required q parameter
        headers=auth_headers,
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

    # FastAPI validation error format
    errors = data["detail"]
    assert isinstance(errors, list)
    assert len(errors) >= 1

    # Find the error for the 'q' field
    q_error = next(
        (err for err in errors if err.get("loc") and "q" in err["loc"]), None
    )
    assert q_error is not None
    assert q_error["type"] == "missing"
