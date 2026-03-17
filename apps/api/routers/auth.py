import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_current_user, get_current_user_optional
from core.errors import (
    ErrorCode,
    ForbiddenError,
    InternalServerError,
    UnauthorizedError,
    ValidationError,
)
from models.database import get_db
from models.user import User
from services.auth import auth_service
from services.oauth import oauth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


def _get_frontend_base_url(request: Request) -> Optional[str]:
    """
    Try to infer the frontend base URL (scheme+host) from request headers.

    This is used so the OAuth provider redirects back to the web app callback page,
    which then calls the API callback endpoint and routes the user client-side.
    """
    origin = request.headers.get("origin")
    if not origin:
        return None

    origin = origin.rstrip("/")
    if origin.startswith(("http://localhost", "http://127.0.0.1", "https://")):
        return origin

    return None


def _get_redirect_uri(request: Request, provider: str) -> str:
    """Get secure redirect URI for OAuth callback."""
    # Use configured base URL if available, otherwise use request URL
    oauth_base = getattr(settings, "oauth_redirect_base_url", None)

    if oauth_base:
        base_url = oauth_base.rstrip("/")
    else:
        inferred = _get_frontend_base_url(request)
        if inferred:
            base_url = inferred
        else:
            # Validate HTTPS in production
            base_url = str(request.base_url).rstrip("/")
            if not base_url.startswith(
                ("http://localhost", "http://127.0.0.1", "https://")
            ):
                # In production, require HTTPS
                base_url = base_url.replace("http://", "https://", 1)

    return f"{base_url}/auth/callback/{provider}"


@router.get("/login/{provider}")
async def oauth_login(provider: str, request: Request) -> Dict[str, str]:
    """
    Initiate OAuth login flow for the specified provider.

    Supported providers: github, google, twitter
    """
    oauth_provider = oauth_service.get_provider(provider)
    if not oauth_provider:
        raise ValidationError(
            f"Unsupported OAuth provider: {provider}", ErrorCode.PROVIDER_NOT_SUPPORTED
        )

    # Create secure redirect URI
    redirect_uri = _get_redirect_uri(request, provider)

    # Generate and store CSRF state parameter
    state = oauth_service.generate_state()
    oauth_service.store_state(state, provider, redirect_uri=redirect_uri)

    # Get authorization URL with state parameter
    auth_url = await oauth_provider.get_authorization_url(redirect_uri, state)

    return {"authorization_url": auth_url, "provider": provider, "state": state}


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),  # State is now required for CSRF protection
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> Dict:
    """
    Handle OAuth callback and complete authentication.

    Returns JWT token on successful authentication.
    """
    oauth_provider = oauth_service.get_provider(provider)
    if not oauth_provider:
        raise ValidationError(
            f"Unsupported OAuth provider: {provider}", ErrorCode.PROVIDER_NOT_SUPPORTED
        )

    # Check if this is a link flow before validating and consuming state
    is_link_flow = oauth_service.is_link_state(state)
    link_user_id = oauth_service.get_link_user_id(state) if is_link_flow else None

    # Validate state parameter to prevent CSRF attacks
    consumed = oauth_service.validate_and_consume_state(state, provider)
    if not consumed:
        raise ValidationError("Invalid or expired state parameter")

    # Create redirect URI (must match what was used in /login)
    redirect_uri = consumed.get("redirect_uri") or _get_redirect_uri(request, provider)

    # Exchange code for access token (pass state for PKCE providers)
    if provider == "twitter":
        access_token = await oauth_provider.exchange_code(code, redirect_uri, state)
    else:
        access_token = await oauth_provider.exchange_code(code, redirect_uri)
    if not access_token:
        raise ValidationError("Failed to exchange authorization code for access token")

    # Get user information from provider
    user_info = await oauth_provider.get_user_info(access_token)
    if not user_info:
        raise ValidationError("Failed to retrieve user information from OAuth provider")

    # Handle link flow vs regular login flow
    try:
        if is_link_flow:
            # Account linking flow - SECURITY: Verify user matches link state
            if not link_user_id:
                raise ValidationError("Invalid link state")

            if not current_user:
                raise UnauthorizedError(
                    "Authentication required for account linking",
                    ErrorCode.AUTHENTICATION_REQUIRED,
                )

            if current_user.id != link_user_id:
                raise ForbiddenError(
                    "Link state does not match authenticated user", ErrorCode.FORBIDDEN
                )

            # Use the authenticated user directly (no need to query again)
            # Note: current_user is already loaded from the database via dependency

            # Link the account to the authenticated user
            user = await auth_service.link_oauth_account(
                db=db,
                current_user=current_user,
                provider=provider,
                provider_account_id=user_info["id"],
                access_token=access_token,
                user_info=user_info,
                refresh_token=None,
            )

            return {
                "message": f"{provider.title()} account linked successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "display_name": user.display_name,
                    "avatar_url": user.avatar_url,
                },
            }
        else:
            # Regular login flow
            user, jwt_token = await auth_service.authenticate_oauth_user(
                db=db,
                provider=provider,
                provider_account_id=user_info["id"],
                access_token=access_token,
                user_info=user_info,
                # Most providers don't provide refresh tokens in basic flow
                refresh_token=None,
            )

            return {
                "access_token": jwt_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "display_name": user.display_name,
                    "avatar_url": user.avatar_url,
                },
            }
    except (UnauthorizedError, ForbiddenError, ValidationError) as e:
        # Re-raise authentication/authorization errors as-is
        raise e
    except Exception as e:
        # Log the actual error server-side for debugging
        logger.error(
            f"OAuth authentication failed for {provider}: {str(e)}", exc_info=True
        )
        # Return generic error to client without exposing details
        raise InternalServerError("Authentication failed. Please try again.")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(current_user: User = Depends(get_current_user)) -> Response:
    """
    Log out the current authenticated user.

    Invalidates the current session. In this JWT-based implementation,
    the client should delete the token from local storage.

    Returns HTTP 204 No Content on success.
    Requires valid JWT authentication.

    Note: For production use, consider implementing a token blacklist
    for immediate token invalidation server-side.
    """
    # Log the logout event
    logger.info(f"User {current_user.id} ({current_user.email}) logged out")

    # In a JWT-based auth system, logout is primarily client-side
    # The client should delete the token from storage
    # For enhanced security, you could:
    # 1. Add the token to a blacklist (requires token storage/caching)
    # 2. Use shorter-lived tokens with refresh tokens
    # 3. Store session data server-side instead of pure JWT

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/providers")
async def get_supported_providers() -> Dict[str, list]:
    """Get list of supported OAuth providers."""
    return {"providers": oauth_service.get_supported_providers()}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> Dict:
    """Return the currently authenticated user's profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
    }


@router.get("/link/{provider}")
async def oauth_link(
    provider: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Initiate OAuth link flow for the specified provider.

    Links an additional social account to the current authenticated user.
    Requires authentication.

    Supported providers: github, google, twitter
    """
    oauth_provider = oauth_service.get_provider(provider)
    if not oauth_provider:
        raise ValidationError(
            f"Unsupported OAuth provider: {provider}", ErrorCode.PROVIDER_NOT_SUPPORTED
        )

    # Create secure redirect URI
    redirect_uri = _get_redirect_uri(request, provider)

    # Generate link state with user ID encoded
    state = oauth_service.generate_link_state(current_user.id)
    oauth_service.store_link_state(
        state, provider, current_user.id, redirect_uri=redirect_uri
    )

    # Get authorization URL with link state parameter
    auth_url = await oauth_provider.get_authorization_url(redirect_uri, state)

    return {"authorization_url": auth_url, "provider": provider, "state": state}


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Unlink an OAuth account from the current user.

    Removes the specified account from the user's linked accounts.
    Returns HTTP 404 if the account doesn't exist or doesn't belong to the user.
    Returns HTTP 400 if trying to unlink the user's last account.

    Args:
        account_id: ID of the account to unlink
        current_user: Current authenticated user
        db: Database session

    Returns:
        HTTP 204 No Content on success
    """
    await auth_service.unlink_oauth_account(
        db=db, current_user=current_user, account_id=account_id
    )

    logger.info(
        f"User {current_user.id} ({current_user.email}) unlinked account {account_id}"
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
