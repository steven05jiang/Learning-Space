from models.account import Account
from models.resource import Resource, ResourceStatus
from models.user import User


def test_user_model():
    """Test User model creation and relationships."""
    user = User(
        email="test@example.com",
        display_name="Test User",
        avatar_url="https://example.com/avatar.jpg",
    )

    assert user.email == "test@example.com"
    assert user.display_name == "Test User"
    assert user.avatar_url == "https://example.com/avatar.jpg"


def test_account_model():
    """Test Account model creation."""
    account = Account(
        user_id=1,
        provider="google",
        provider_account_id="google_123",
        access_token="access_token_123",
        refresh_token="refresh_token_123",
    )

    assert account.user_id == 1
    assert account.provider == "google"
    assert account.provider_account_id == "google_123"
    assert account.access_token == "access_token_123"
    assert account.refresh_token == "refresh_token_123"


def test_resource_model():
    """Test Resource model creation."""
    resource = Resource(
        owner_id=1,
        content_type="url",
        original_content="https://example.com",
        title="Example Article",
        summary="Summary of the article",
        tags=["tag1", "tag2"],
        status=ResourceStatus.READY,
    )

    assert resource.owner_id == 1
    assert resource.content_type == "url"
    assert resource.original_content == "https://example.com"
    assert resource.title == "Example Article"
    assert resource.summary == "Summary of the article"
    assert resource.tags == ["tag1", "tag2"]
    assert resource.status == ResourceStatus.READY


def test_resource_status_enum():
    """Test ResourceStatus enum values."""
    assert ResourceStatus.PENDING.value == "PENDING"
    assert ResourceStatus.PROCESSING.value == "PROCESSING"
    assert ResourceStatus.READY.value == "READY"
    assert ResourceStatus.FAILED.value == "FAILED"
