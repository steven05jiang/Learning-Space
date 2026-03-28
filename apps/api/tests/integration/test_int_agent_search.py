"""
Integration tests for agent search_resources tool functionality.

Tests:
- INT-059: Agent search_resources tool returns trimmed AgentResourceResult list

This test verifies that the search_resources LangGraph tool returns correctly
shaped AgentResourceResult objects with the proper trimmed fields, hard limit,
and URL field behavior for different resource types.
"""

import pytest

from models.resource import ResourceStatus
from models.user import User
from services.resource_search_service import (
    AgentResourceResult,
    resource_search_service,
)
from tests.integration.factories import make_resource


@pytest.mark.integration
@pytest.mark.search
async def test_agent_search_resources_returns_trimmed_results(
    db_session, test_user: User
):
    """
    INT-059: Agent search_resources tool returns trimmed AgentResourceResult list.

    Validates that AgentResourceResult conversion returns:
    - Correctly shaped dicts with fields: id, title, summary, tags,
      top_level_categories, url
    - No rank, status, created_at, updated_at fields in result
    - url = original_content for URL-type resources
    - url = None for text-type resources
    - Hard limit: at most 10 results returned even when more match
    - Results scoped to the current user only
    """
    # Create another user to test user isolation
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    # Create URL-type resources for the test user
    url_resource_1 = await make_resource(
        db_session,
        test_user.id,
        title="Python Programming Guide",
        summary="A comprehensive guide to Python development and best practices",
        tags=["python", "programming", "tutorial"],
        top_level_categories=["Technology", "Education"],
        status=ResourceStatus.READY,
        content_type="url",
        original_content="https://example.com/python-guide",
    )

    url_resource_2 = await make_resource(
        db_session,
        test_user.id,
        title="Machine Learning with Python",
        summary="Learn machine learning using Python libraries",
        tags=["machine-learning", "python", "data-science"],
        top_level_categories=["Technology", "Science"],
        status=ResourceStatus.READY,
        content_type="url",
        original_content="https://example.com/ml-python",
    )

    # Create text-type resource for the test user
    text_resource = await make_resource(
        db_session,
        test_user.id,
        title="Python Notes",
        summary="My personal Python programming notes and tips",
        tags=["python", "notes"],
        top_level_categories=["Technology"],
        status=ResourceStatus.READY,
        content_type="text",
        original_content="# Python Notes\n\nKey concepts and examples...",
    )

    # Create resources that should be excluded (non-READY status)
    pending_resource = await make_resource(
        db_session,
        test_user.id,
        title="Advanced Python Techniques",
        summary="Deep dive into advanced Python programming concepts",
        tags=["python", "advanced"],
        status=ResourceStatus.PENDING,
        content_type="url",
        original_content="https://example.com/python-advanced",
    )

    # Create resource for another user (excluded due to user isolation)
    other_user_resource = await make_resource(
        db_session,
        other_user.id,
        title="Python for Beginners",
        summary="Introduction to Python programming for newcomers",
        tags=["python", "beginner"],
        status=ResourceStatus.READY,
        content_type="url",
        original_content="https://example.com/python-intro",
    )

    # Create additional resources to test hard limit of 10
    for i in range(8):  # Adding 8 more to make 11 total matching resources
        await make_resource(
            db_session,
            test_user.id,
            title=f"Python Resource {i + 4}",
            summary=f"Additional Python resource #{i + 4} for limit testing",
            tags=["python", f"tag{i}"],
            status=ResourceStatus.READY,
            content_type="url",
            original_content=f"https://example.com/python-resource-{i + 4}",
        )

    await db_session.commit()

    # Call ResourceSearchService with hard limit (same as the tool does)
    search_result = await resource_search_service.search(
        session=db_session,
        owner_id=test_user.id,
        query="python",
        tag=None,
        limit=10,  # hard cap for agent context efficiency
        offset=0,  # no pagination in agent context
    )

    # Convert to AgentResourceResult and return as dictionaries (same as the tool does)
    results = [
        AgentResourceResult.from_item(r).__dict__ for r in search_result.resources
    ]

    # Validate basic response structure
    assert isinstance(results, list), "Should return a list"
    assert len(results) <= 10, "Hard limit: should return at most 10 results"
    assert len(results) == 10, "Should return exactly 10 results (due to hard limit)"

    # Validate result shape for each item
    for result in results:
        assert isinstance(result, dict), "Each result should be a dictionary"

        # Check required fields are present
        required_fields = {
            "id",
            "title",
            "summary",
            "tags",
            "top_level_categories",
            "url",
        }
        assert set(result.keys()) == required_fields, (
            f"Result should have exactly these fields: {required_fields}"
        )

        # Check forbidden fields are not present
        forbidden_fields = {"rank", "status", "created_at", "updated_at"}
        for forbidden_field in forbidden_fields:
            assert forbidden_field not in result, (
                f"Result should not contain {forbidden_field}"
            )

        # Validate field types and basic structure
        assert isinstance(result["id"], str), "id should be string"
        assert isinstance(result["title"], str), "title should be string"
        assert isinstance(result["summary"], str), "summary should be string"
        assert isinstance(result["tags"], list), "tags should be list"
        assert isinstance(result["top_level_categories"], list), (
            "top_level_categories should be list"
        )
        assert result["url"] is None or isinstance(result["url"], str), (
            "url should be None or string"
        )

    # Find our specific test resources in results to validate URL field behavior
    url_results = [
        r
        for r in results
        if r["id"] in [str(url_resource_1.id), str(url_resource_2.id)]
    ]
    text_results = [r for r in results if r["id"] == str(text_resource.id)]

    # Validate URL field for URL-type resources
    for url_result in url_results:
        assert url_result["url"] is not None, (
            "URL-type resources should have non-null url field"
        )
        assert url_result["url"].startswith("https://example.com/"), (
            "url should be the original_content"
        )

    # Validate URL field for text-type resources
    for text_result in text_results:
        assert text_result["url"] is None, (
            "Text-type resources should have null url field"
        )

    # Validate user isolation - no results should belong to other_user
    result_ids = {result["id"] for result in results}
    assert str(other_user_resource.id) not in result_ids, (
        "Should not return other user's resources"
    )
    assert str(pending_resource.id) not in result_ids, (
        "Should not return non-READY resources"
    )

    # Validate that we got at least our known matching resources
    expected_ids = {
        str(url_resource_1.id),
        str(url_resource_2.id),
        str(text_resource.id),
    }
    actual_ids = {result["id"] for result in results}
    assert expected_ids.issubset(actual_ids), (
        "Should include our test resources in results"
    )


@pytest.mark.integration
@pytest.mark.search
async def test_agent_search_resources_with_tag_filter(db_session, test_user: User):
    """
    INT-059: Test search with tag filtering.

    Validates that the tag parameter works correctly to narrow results.
    """
    # Create resources with different tags
    tutorial_resource = await make_resource(
        db_session,
        test_user.id,
        title="Python Tutorial",
        summary="Learn Python programming step by step",
        tags=["python", "tutorial", "beginner"],
        status=ResourceStatus.READY,
    )

    await make_resource(
        db_session,
        test_user.id,
        title="Advanced Python",
        summary="Advanced Python programming techniques",
        tags=["python", "advanced"],
        status=ResourceStatus.READY,
    )

    await db_session.commit()

    # Test search with tag filter
    search_result = await resource_search_service.search(
        session=db_session,
        owner_id=test_user.id,
        query="python",
        tag="tutorial",
        limit=10,
        offset=0,
    )

    results = [
        AgentResourceResult.from_item(r).__dict__ for r in search_result.resources
    ]

    # Should only return the tutorial resource
    assert len(results) == 1, "Tag filter should narrow results"
    assert results[0]["id"] == str(tutorial_resource.id)
    assert "tutorial" in results[0]["tags"]

    # Validate result structure (should be same as previous test)
    result = results[0]
    required_fields = {"id", "title", "summary", "tags", "top_level_categories", "url"}
    assert set(result.keys()) == required_fields


@pytest.mark.integration
@pytest.mark.search
async def test_agent_search_resources_no_results(db_session, test_user: User):
    """
    INT-059: Test search when no resources match.

    Validates that the search returns empty list gracefully.
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
    search_result = await resource_search_service.search(
        session=db_session,
        owner_id=test_user.id,
        query="nonexistent term",
        tag=None,
        limit=10,
        offset=0,
    )

    results = [
        AgentResourceResult.from_item(r).__dict__ for r in search_result.resources
    ]

    assert results == [], "Should return empty list when no matches"


@pytest.mark.integration
@pytest.mark.search
async def test_agent_resource_result_url_field_behavior(db_session, test_user: User):
    """
    INT-059: Test AgentResourceResult URL field behavior.

    Validates that:
    - URL-type resources have url = original_content
    - Text-type resources have url = None
    """
    # Create URL-type resource
    url_resource = await make_resource(
        db_session,
        test_user.id,
        title="Web Article",
        summary="A web article about technology",
        tags=["technology"],
        status=ResourceStatus.READY,
        content_type="url",
        original_content="https://example.com/tech-article",
    )

    # Create text-type resource
    text_resource = await make_resource(
        db_session,
        test_user.id,
        title="My Notes",
        summary="My personal notes on technology",
        tags=["technology"],
        status=ResourceStatus.READY,
        content_type="text",
        original_content="# Tech Notes\n\nSome important notes...",
    )

    await db_session.commit()

    # Search for both resources
    search_result = await resource_search_service.search(
        session=db_session,
        owner_id=test_user.id,
        query="technology",
        tag=None,
        limit=10,
        offset=0,
    )

    results = [
        AgentResourceResult.from_item(r).__dict__ for r in search_result.resources
    ]

    assert len(results) == 2, "Should find both resources"

    # Find each resource in results
    url_result = next(r for r in results if r["id"] == str(url_resource.id))
    text_result = next(r for r in results if r["id"] == str(text_resource.id))

    # Validate URL field behavior
    assert url_result["url"] == "https://example.com/tech-article", (
        "URL-type resource should have url = original_content"
    )
    assert text_result["url"] is None, "Text-type resource should have url = None"
