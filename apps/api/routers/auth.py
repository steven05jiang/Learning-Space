import logging
from typing import Dict

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_current_user
from core.errors import ErrorCode, InternalServerError, ValidationError
from models.database import get_db
from models.user import User
from services.auth import auth_service
from services.oauth import oauth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


def _get_redirect_uri(request: Request, provider: str) -> str:
    """Get secure redirect URI for OAuth callback."""
    # Use configured base URL if available, otherwise use request URL
    oauth_base = getattr(settings, "oauth_redirect_base_url", None)

    if oauth_base:
        base_url = oauth_base.rstrip("/")
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
    oauth_service.store_state(state, provider)

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

    # Validate state parameter to prevent CSRF attacks
    if not oauth_service.validate_and_consume_state(state, provider):
        raise ValidationError("Invalid or expired state parameter")

    # Create redirect URI (same as used in login)
    redirect_uri = _get_redirect_uri(request, provider)

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

    # Authenticate or create user
    try:
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
