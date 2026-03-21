"""
Integration tests for resources API.

Tests:
- INT-013: Authenticated user POST /resources with a URL → 202, resource created
  with status PENDING or PROCESSING
- INT-014: Authenticated user POST /resources with text content → 202, resource
  created
- INT-015: Unauthenticated POST /resources → 401
- INT-016: POST /resources with prefer_provider hint → resource row has
  prefer_provider stored
- INT-017: GET /resources → paginated list, only own resources (not another
  user's)
- INT-018: GET /resources?tag=AI → filters by tag
- INT-019: GET /resources?status=READY → filters by status
- INT-020: GET /resources/{id} → full resource detail
- INT-021: PATCH /resources/{id} with new title → title updated, updated_at
  changes
- INT-022: PATCH /resources/{id} with new original_content → re-triggers
  PROCESSING + enqueues new job
- INT-023: DELETE /resources/{id} → resource removed, graph sync job enqueued
"""

from datetime import datetime

import pytest
from sqlalchemy import select

from models.resource import Resource, ResourceStatus
from models.user import User
from tests.integration.factories import make_resource


@pytest.mark.integration
@pytest.mark.int_resources
async def test_create_resource_with_url_returns_202_pending(client, auth_headers):
    """
    INT-013: Authenticated user POST /resources with a URL → 202, resource created
    with status PENDING or PROCESSING
    """
    payload = {"content_type": "url", "original_content": "https://example.com/article"}

    response = await client.post("/resources/", json=payload, headers=auth_headers)

    assert response.status_code == 202
    data = response.json()

    # Verify resource creation
    assert "id" in data
    assert data["content_type"] == "url"
    assert data["original_content"] == "https://example.com/article"
    assert data["status"] in ["PENDING", "PROCESSING"]
    assert data["prefer_provider"] is None
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.integration
@pytest.mark.int_resources
async def test_create_resource_with_text_returns_202(client, auth_headers):
    """
    INT-014: Authenticated user POST /resources with text content → 202,
    resource created
    """
    payload = {
        "content_type": "text",
        "original_content": "This is some text content to process",
    }

    response = await client.post("/resources/", json=payload, headers=auth_headers)

    assert response.status_code == 202
    data = response.json()

    # Verify resource creation
    assert "id" in data
    assert data["content_type"] == "text"
    assert data["original_content"] == "This is some text content to process"
    assert data["status"] in ["PENDING", "PROCESSING"]


@pytest.mark.integration
@pytest.mark.int_resources
async def test_create_resource_unauthenticated_returns_401(client):
    """
    INT-015: Unauthenticated POST /resources → 401
    """
    payload = {"content_type": "url", "original_content": "https://example.com/article"}

    response = await client.post("/resources/", json=payload)

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.int_resources
async def test_create_resource_with_prefer_provider_stores_hint(
    client, auth_headers, db_session
):
    """
    INT-016: POST /resources with prefer_provider hint → resource row has
    prefer_provider stored
    """
    payload = {
        "content_type": "url",
        "original_content": "https://example.com/article",
        "prefer_provider": "anthropic",
    }

    response = await client.post("/resources/", json=payload, headers=auth_headers)

    assert response.status_code == 202
    data = response.json()
    assert data["prefer_provider"] == "anthropic"

    # Verify in database
    resource_id = int(data["id"])
    query = select(Resource).where(Resource.id == resource_id)
    result = await db_session.execute(query)
    resource = result.scalar_one()
    assert resource.prefer_provider == "anthropic"


@pytest.mark.integration
@pytest.mark.int_resources
async def test_list_resources_returns_paginated_own_resources_only(
    client, auth_headers, db_session, test_user
):
    """
    INT-017: GET /resources → paginated list, only own resources (not another
    user's)
    """
    # Create a second user and their resource
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    # Create resources for both users
    await make_resource(db_session, test_user.id, title="Own Resource")
    await make_resource(db_session, other_user.id, title="Other's Resource")
    await db_session.commit()

    response = await client.get("/resources/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify pagination structure
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    # Should only see own resource
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Own Resource"

    # Verify other user's resource is not included
    returned_titles = [item["title"] for item in data["items"]]
    assert "Other's Resource" not in returned_titles


@pytest.mark.integration
@pytest.mark.int_resources
@pytest.mark.skip(reason="Tag filtering not yet implemented in resources router")
async def test_list_resources_filter_by_tag(
    client, auth_headers, db_session, test_user
):
    """
    INT-018: GET /resources?tag=AI → filters by tag

    Currently skipped because tag filtering is not implemented in the router.
    This test will be enabled when the DEV task adds tag query parameter support.
    """
    # Create resources with different tags
    await make_resource(db_session, test_user.id, title="AI Article", tags=["AI", "ML"])
    await make_resource(
        db_session, test_user.id, title="Tech Article", tags=["Technology"]
    )
    await make_resource(
        db_session,
        test_user.id,
        title="Mixed Article",
        tags=["AI", "Technology"],
    )
    await db_session.commit()

    # Test tag filter for "AI"
    response = await client.get("/resources/?tag=AI", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Expected behavior when tag filtering is implemented:
    assert data["total"] == 2
    returned_titles = [item["title"] for item in data["items"]]
    assert "AI Article" in returned_titles
    assert "Mixed Article" in returned_titles
    assert "Tech Article" not in returned_titles


@pytest.mark.integration
@pytest.mark.int_resources
async def test_list_resources_filter_by_status(
    client, auth_headers, db_session, test_user
):
    """
    INT-019: GET /resources?status=READY → filters by status
    """
    # Create resources with different statuses
    await make_resource(
        db_session,
        test_user.id,
        title="Ready Resource",
        status=ResourceStatus.READY,
    )
    await make_resource(
        db_session,
        test_user.id,
        title="Pending Resource",
        status=ResourceStatus.PENDING,
    )
    await make_resource(
        db_session,
        test_user.id,
        title="Failed Resource",
        status=ResourceStatus.FAILED,
    )
    await db_session.commit()

    # Test status filter for "READY"
    response = await client.get("/resources/?status=READY", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should only return READY resources
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Ready Resource"
    assert data["items"][0]["status"] == "READY"


@pytest.mark.integration
@pytest.mark.int_resources
async def test_get_resource_by_id_returns_full_detail(
    client, auth_headers, db_session, test_user
):
    """
    INT-020: GET /resources/{id} → full resource detail
    """
    resource = await make_resource(
        db_session,
        test_user.id,
        title="Test Resource",
        summary="A test summary",
        tags=["AI", "Testing"],
        prefer_provider="anthropic",
    )
    await db_session.commit()

    response = await client.get(f"/resources/{resource.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify full resource detail
    assert data["id"] == str(resource.id)
    assert data["owner_id"] == str(test_user.id)
    assert data["content_type"] == "url"
    assert data["original_content"] == "https://example.com/article"
    assert data["title"] == "Test Resource"
    assert data["summary"] == "A test summary"
    assert data["tags"] == ["AI", "Testing"]
    assert data["prefer_provider"] == "anthropic"
    assert data["status"] == "READY"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.integration
@pytest.mark.int_resources
async def test_get_resource_not_found_returns_404(client, auth_headers):
    """
    INT-020 variant: GET /resources/{nonexistent_id} → 404
    """
    response = await client.get("/resources/99999", headers=auth_headers)

    assert response.status_code == 404
    data = response.json()
    assert "Resource not found" in data["detail"]


@pytest.mark.integration
@pytest.mark.int_resources
async def test_get_resource_not_owned_returns_404(client, auth_headers, db_session):
    """
    INT-020 variant: GET /resources/{other_user_resource_id} → 404
    """
    # Create a second user and their resource
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    other_resource = await make_resource(
        db_session, other_user.id, title="Other's Resource"
    )
    await db_session.commit()

    response = await client.get(f"/resources/{other_resource.id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.int_resources
async def test_patch_resource_title_updates_title_and_timestamp(
    client, auth_headers, db_session, test_user
):
    """
    INT-021: PATCH /resources/{id} with new title → title updated, updated_at changes
    """
    resource = await make_resource(db_session, test_user.id, title="Original Title")
    await db_session.commit()

    # Set updated_at to a known past timestamp to ensure reliable comparison
    past_time = datetime(2020, 1, 1, 0, 0, 0)
    resource.updated_at = past_time
    await db_session.commit()
    original_updated_at = resource.updated_at

    patch_data = {"title": "Updated Title"}
    response = await client.patch(
        f"/resources/{resource.id}", json=patch_data, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify title updated
    assert data["title"] == "Updated Title"

    # Verify updated_at changed
    updated_updated_at = datetime.fromisoformat(
        data["updated_at"].replace("Z", "+00:00")
    )
    assert updated_updated_at > original_updated_at


@pytest.mark.integration
@pytest.mark.int_resources
async def test_patch_resource_original_content_triggers_reprocessing(
    client, auth_headers, db_session, test_user
):
    """
    INT-022: PATCH /resources/{id} with new original_content → re-triggers
    PROCESSING + enqueues new job

    Note: Job enqueuing verification is deferred to INT-024+ worker tests
    (pending DEV-019 queue integration).
    """
    resource = await make_resource(
        db_session,
        test_user.id,
        original_content="https://example.com/old-article",
        status=ResourceStatus.READY,
    )
    await db_session.commit()

    patch_data = {"original_content": "https://example.com/new-article"}
    response = await client.patch(
        f"/resources/{resource.id}", json=patch_data, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify content updated and status reset
    assert data["original_content"] == "https://example.com/new-article"
    assert data["status"] == "PENDING"  # Should be reset to PENDING for reprocessing


@pytest.mark.integration
@pytest.mark.int_resources
async def test_patch_resource_not_found_returns_404(client, auth_headers):
    """
    INT-021/022 variant: PATCH /resources/{nonexistent_id} → 404
    """
    patch_data = {"title": "New Title"}
    response = await client.patch(
        "/resources/99999", json=patch_data, headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.int_resources
async def test_patch_resource_not_owned_returns_404(client, auth_headers, db_session):
    """
    INT-021/022 variant: PATCH /resources/{other_user_resource_id} → 404
    """
    # Create a second user and their resource
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    other_resource = await make_resource(db_session, other_user.id)
    await db_session.commit()

    patch_data = {"title": "New Title"}
    response = await client.patch(
        f"/resources/{other_resource.id}", json=patch_data, headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.int_resources
async def test_delete_resource_removes_resource(
    client, auth_headers, db_session, test_user
):
    """
    INT-023: DELETE /resources/{id} → resource removed, graph sync job enqueued

    Note: Graph sync job verification is deferred to INT-029+ graph tests
    (pending DEV-019 queue integration).
    """
    resource = await make_resource(db_session, test_user.id, title="To Delete")
    await db_session.commit()
    resource_id = resource.id

    response = await client.delete(f"/resources/{resource_id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify resource is deleted from database
    query = select(Resource).where(Resource.id == resource_id)
    result = await db_session.execute(query)
    deleted_resource = result.scalar_one_or_none()
    assert deleted_resource is None


@pytest.mark.integration
@pytest.mark.int_resources
async def test_delete_resource_not_found_returns_404(client, auth_headers):
    """
    INT-023 variant: DELETE /resources/{nonexistent_id} → 404
    """
    response = await client.delete("/resources/99999", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.int_resources
async def test_delete_resource_not_owned_returns_404(client, auth_headers, db_session):
    """
    INT-023 variant: DELETE /resources/{other_user_resource_id} → 404
    """
    # Create a second user and their resource
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    other_resource = await make_resource(db_session, other_user.id)
    await db_session.commit()

    response = await client.delete(
        f"/resources/{other_resource.id}", headers=auth_headers
    )

    assert response.status_code == 404
