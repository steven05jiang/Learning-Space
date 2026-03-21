"""
Integration tests for auth endpoints.

Tests:
- INT-003: POST to `/auth/callback/twitter` with mock OAuth → creates new User +
          Account row; returns JWT/session
- INT-004: Same Twitter login again (existing user) → returns existing user
          (no new row)
- INT-005: Login with Google (different provider, same email) → links to
          existing user
- INT-006: Request to a protected endpoint without a token → 401
- INT-007: Request with an expired/invalid JWT → 401
- INT-008: Authenticated user hits GET /auth/link/twitter → links new Account row to
          existing user
- INT-009: Link attempt when that provider account is already linked to a different
          user → 409
- INT-010: DELETE /auth/accounts/{account_id} → account row removed
- INT-011: DELETE /auth/accounts/{account_id} when it's the user's last account →
          400 CANNOT_UNLINK_LAST_ACCOUNT
- INT-012: GET /auth/me → returns user profile + linked accounts list
"""

from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from main import app
from models.account import Account
from models.user import User


@pytest.mark.integration
@pytest.mark.int_auth
async def test_oauth_callback_twitter_creates_new_user(db_session, mock_oauth):
    """
    INT-003: POST to /auth/callback/twitter with mock OAuth → creates new User +
    Account row; returns JWT/session
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First, initiate OAuth to get a valid state
        login_response = await client.get("/auth/login/twitter")
        assert login_response.status_code == 200
        state = login_response.json()["state"]

        # Now call the callback with the state
        response = await client.get(
            f"/auth/callback/twitter?code=mock-code&state={state}"
        )

    assert response.status_code == 200
    data = response.json()

    # Check JWT token is returned
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data

    # Check user data
    user_data = data["user"]
    assert "id" in user_data
    assert user_data["email"] == "test@example.com"
    assert user_data["display_name"] == "Test User"

    # Verify user was created in database
    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    user = result.scalar_one()
    assert user is not None
    assert user.display_name == "Test User"

    # Verify account was created
    result = await db_session.execute(select(Account).where(Account.user_id == user.id))
    account = result.scalar_one()
    assert account is not None
    assert account.provider == "twitter"
    assert account.provider_account_id == "twitter-user-123"


@pytest.mark.integration
@pytest.mark.int_auth
async def test_oauth_callback_existing_user_returns_same_user(db_session, mock_oauth):
    """
    INT-004: Same Twitter login again (existing user) → returns existing user
    (no new row)
    """
    # Create existing user and account
    user = User(display_name="Existing User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        provider="twitter",
        provider_account_id="twitter-user-123",
        access_token="existing-token",
    )
    db_session.add(account)
    await db_session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Initiate OAuth to get a valid state
        login_response = await client.get("/auth/login/twitter")
        state = login_response.json()["state"]

        # Call callback
        response = await client.get(
            f"/auth/callback/twitter?code=mock-code&state={state}"
        )

    assert response.status_code == 200
    data = response.json()

    # Should return the existing user
    assert data["user"]["id"] == user.id
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["display_name"] == "Existing User"

    # Verify no duplicate user was created
    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    users = result.scalars().all()
    assert len(users) == 1


@pytest.mark.integration
@pytest.mark.int_auth
async def test_oauth_callback_google_links_to_existing_user(db_session, mock_oauth):
    """
    INT-005: Login with Google (different provider, same email) → links to
    existing user
    """
    # Create existing user with Twitter account
    user = User(display_name="Existing User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        provider="twitter",
        provider_account_id="twitter-user-123",
        access_token="twitter-token",
    )
    db_session.add(account)
    await db_session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Initiate Google OAuth
        login_response = await client.get("/auth/login/google")
        state = login_response.json()["state"]

        # Call Google callback
        response = await client.get(
            f"/auth/callback/google?code=mock-code&state={state}"
        )

    assert response.status_code == 200
    data = response.json()

    # Should return the existing user
    assert data["user"]["id"] == user.id
    assert data["user"]["email"] == "test@example.com"

    # Verify Google account was linked to existing user
    result = await db_session.execute(
        select(Account).where(Account.user_id == user.id, Account.provider == "google")
    )
    google_account = result.scalar_one()
    assert google_account is not None
    assert google_account.provider_account_id == "google-user-456"

    # Verify no new user was created
    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    users = result.scalars().all()
    assert len(users) == 1


@pytest.mark.integration
@pytest.mark.int_auth
async def test_protected_endpoint_without_token_returns_401():
    """
    INT-006: Request to a protected endpoint (e.g. GET /auth/me) without a token → 401
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/auth/me")

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "code" in data
    assert data["code"] == "UNAUTHORIZED"


@pytest.mark.integration
@pytest.mark.int_auth
async def test_protected_endpoint_with_invalid_jwt_returns_401():
    """INT-007: Request with an expired/invalid JWT → 401"""
    # Create an invalid/expired token
    invalid_token = "invalid.jwt.token"

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {invalid_token}"}
        )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "code" in data
    assert data["code"] == "UNAUTHORIZED"


@pytest.mark.integration
@pytest.mark.int_auth
async def test_authenticated_user_can_link_additional_account(
    db_session, auth_headers, mock_oauth, test_user
):
    """
    INT-008: Authenticated user hits GET /auth/link/google → links new Account row
    to existing user
    """
    # Use the test_user fixture which creates a user with a twitter account already
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get link URL for Google (since test_user already has Twitter)
        link_response = await client.get("/auth/link/google", headers=auth_headers)

        assert link_response.status_code == 200
        link_data = link_response.json()
        assert "authorization_url" in link_data
        assert "state" in link_data
        assert link_data["provider"] == "google"

        # Extract state from the authorization_url to complete the link flow
        parsed_url = urlparse(link_data["authorization_url"])
        query_params = parse_qs(parsed_url.query)
        state = query_params["state"][0]

        # Complete the link flow by calling the callback
        callback_response = await client.get(
            f"/auth/callback/google?code=mock-code&state={state}", headers=auth_headers
        )

    assert callback_response.status_code == 200
    callback_data = callback_response.json()
    assert "message" in callback_data
    assert "Google account linked successfully" in callback_data["message"]
    assert "user" in callback_data

    # Verify that a new Google account was created in the database
    result = await db_session.execute(
        select(Account).where(
            Account.user_id == test_user.id, Account.provider == "google"
        )
    )
    google_account = result.scalar_one()
    assert google_account is not None
    assert google_account.provider == "google"
    # Mock OAuth returns "google-user-456"
    assert google_account.provider_account_id == "google-user-456"


@pytest.mark.integration
@pytest.mark.int_auth
async def test_link_attempt_existing_account_different_user_returns_409(
    db_session, auth_headers, mock_oauth
):
    """
    INT-009: Link attempt when that provider account is already linked to a
    different user → 409
    """
    # Create another user with the Google account that our test user will try to link
    other_user = User(display_name="Other User", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    other_account = Account(
        user_id=other_user.id,
        provider="google",
        provider_account_id="google-user-456",  # This is what the mock returns
        access_token="other-token",
    )
    db_session.add(other_account)
    await db_session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Initiate link flow
        link_response = await client.get("/auth/link/google", headers=auth_headers)
        state = link_response.json()["state"]

        # Try to complete the link callback
        response = await client.get(
            f"/auth/callback/google?code=mock-code&state={state}", headers=auth_headers
        )

    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "code" in data
    assert data["code"] == "ACCOUNT_ALREADY_LINKED"


@pytest.mark.integration
@pytest.mark.int_auth
async def test_delete_account_removes_account_row(db_session, test_user, auth_headers):
    """INT-010: DELETE /auth/accounts/{account_id} → account row removed"""
    # Create a second account for test_user so we can safely delete one
    additional_account = Account(
        user_id=test_user.id,
        provider="google",
        provider_account_id="google-123",
        access_token="google-token",
    )
    db_session.add(additional_account)
    await db_session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"/auth/accounts/{additional_account.id}", headers=auth_headers
        )

    assert response.status_code == 204

    # Verify account was deleted
    result = await db_session.execute(
        select(Account).where(Account.id == additional_account.id)
    )
    deleted_account = result.scalar_one_or_none()
    assert deleted_account is None

    # Verify user still exists and has their original account
    result = await db_session.execute(
        select(Account).where(
            Account.user_id == test_user.id, Account.provider == "twitter"
        )
    )
    remaining_account = result.scalar_one_or_none()
    assert remaining_account is not None


@pytest.mark.integration
@pytest.mark.int_auth
async def test_delete_last_account_returns_400_cannot_unlink(
    db_session, test_user, auth_headers
):
    """
    INT-011: DELETE /auth/accounts/{account_id} when it's the user's last account →
    400 CANNOT_UNLINK_LAST_ACCOUNT
    """
    # Get the test_user's only account
    result = await db_session.execute(
        select(Account).where(Account.user_id == test_user.id)
    )
    account = result.scalar_one()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"/auth/accounts/{account.id}", headers=auth_headers
        )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "code" in data
    assert data["code"] == "CANNOT_UNLINK_LAST_ACCOUNT"

    # Verify account was NOT deleted
    result = await db_session.execute(select(Account).where(Account.id == account.id))
    existing_account = result.scalar_one_or_none()
    assert existing_account is not None


@pytest.mark.integration
@pytest.mark.int_auth
async def test_get_auth_me_returns_user_profile_and_accounts(test_user, auth_headers):
    """INT-012: GET /auth/me → returns user profile + linked accounts list"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test /auth/me endpoint for user profile
        me_response = await client.get("/auth/me", headers=auth_headers)

        # Test /auth/accounts endpoint for linked accounts
        accounts_response = await client.get("/auth/accounts", headers=auth_headers)

    # Verify user profile from /auth/me
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert "id" in me_data
    assert "email" in me_data
    assert "display_name" in me_data
    assert "avatar_url" in me_data
    assert me_data["id"] == test_user.id
    assert me_data["email"] == test_user.email
    assert me_data["display_name"] == test_user.display_name

    # Verify linked accounts from /auth/accounts
    assert accounts_response.status_code == 200
    accounts_data = accounts_response.json()
    assert "accounts" in accounts_data
    accounts = accounts_data["accounts"]
    assert len(accounts) == 1  # test_user has one twitter account

    account = accounts[0]
    assert "id" in account
    assert "provider" in account
    assert "provider_account_id" in account
    assert "created_at" in account
    assert account["provider"] == "twitter"
    assert account["provider_account_id"] == "twitter-123"


@pytest.mark.integration
@pytest.mark.int_auth
async def test_get_auth_accounts_returns_linked_accounts_list(test_user, auth_headers):
    """Additional test for GET /auth/accounts endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/auth/accounts", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "accounts" in data
    accounts = data["accounts"]
    assert len(accounts) == 1  # test_user has one twitter account

    account = accounts[0]
    assert "id" in account
    assert "provider" in account
    assert "provider_account_id" in account
    assert "created_at" in account
    assert account["provider"] == "twitter"
    assert account["provider_account_id"] == "twitter-123"
