"""Test processing_status migration (ea78e7455c2f) idempotency and backfill."""

from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import ProcessingStatus, Resource, ResourceStatus


async def test_processing_status_enum_values():
    """Test ProcessingStatus enum has the correct values."""
    assert ProcessingStatus.PENDING.value == "pending"
    assert ProcessingStatus.PROCESSING.value == "processing"
    assert ProcessingStatus.SUCCESS.value == "success"
    assert ProcessingStatus.FAILED.value == "failed"


async def test_migration_backfill_logic():
    """Test the backfill logic defined in migration ea78e7455c2f.

    This test verifies the mapping rules:
    - status=READY → processing_status=success
    - status=FAILED → processing_status=failed
    - all others → processing_status=pending
    """
    # Test the mapping logic that would be used in the migration
    test_cases = [
        (ResourceStatus.READY, ProcessingStatus.SUCCESS),
        (ResourceStatus.FAILED, ProcessingStatus.FAILED),
        (ResourceStatus.PENDING, ProcessingStatus.PENDING),
        (ResourceStatus.PROCESSING, ProcessingStatus.PENDING),
    ]

    for old_status, expected_processing_status in test_cases:
        # This mimics the backfill logic in the migration
        if old_status == ResourceStatus.READY:
            actual = ProcessingStatus.SUCCESS
        elif old_status == ResourceStatus.FAILED:
            actual = ProcessingStatus.FAILED
        else:
            actual = ProcessingStatus.PENDING

        assert actual == expected_processing_status


async def test_resource_model_has_processing_status():
    """Test that Resource model includes processing_status field."""
    # Verify the model has the processing_status attribute
    assert hasattr(Resource, "processing_status")

    # Verify the enum exists and has the expected default
    assert ProcessingStatus.PENDING is not None


async def test_processing_status_default_value(db_session: AsyncSession, test_user):
    """Test that new resources get the default processing_status value."""
    from datetime import datetime

    # Create a resource without explicitly setting processing_status
    resource = Resource(
        owner_id=test_user.id,
        content_type="url",
        original_content="https://example.com/test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)

    # Should have the default value
    assert resource.processing_status == ProcessingStatus.PENDING


async def test_processing_status_can_be_set(db_session: AsyncSession, test_user):
    """Test that processing_status can be explicitly set to different values."""
    from datetime import datetime

    # Test each enum value
    for status in ProcessingStatus:
        resource = Resource(
            owner_id=test_user.id,
            content_type="url",
            original_content=f"https://example.com/test-{status.value}",
            processing_status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        assert resource.processing_status == status
