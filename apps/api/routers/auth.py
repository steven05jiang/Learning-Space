from typing import Dict

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import ErrorCode, InternalServerError, ValidationError
from models.database import get_db
from services.auth import auth_service
from services.oauth import oauth_service

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login/{provider}")
async def oauth_login(
    provider: str,
    request: Request
) -> Dict[str, str]:
    """
    Initiate OAuth login flow for the specified provider.

    Supported providers: github, google, twitter
    """
    oauth_provider = oauth_service.get_provider(provider)
    if not oauth_provider:
        raise ValidationError(
            f"Unsupported OAuth provider: {provider}",
            ErrorCode.PROVIDER_NOT_SUPPORTED
        )

    # Create redirect URI
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/auth/callback/{provider}"

    # Get authorization URL
    auth_url = await oauth_provider.get_authorization_url(redirect_uri)

    return {
        "authorization_url": auth_url,
        "provider": provider
    }


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Handle OAuth callback and complete authentication.

    Returns JWT token on successful authentication.
    """
    oauth_provider = oauth_service.get_provider(provider)
    if not oauth_provider:
        raise ValidationError(
            f"Unsupported OAuth provider: {provider}",
            ErrorCode.PROVIDER_NOT_SUPPORTED
        )

    # Create redirect URI (same as used in login)
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/auth/callback/{provider}"

    # Exchange code for access token
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
            refresh_token=None
        )

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url
            }
        }
    except Exception as e:
        raise InternalServerError(f"Authentication failed: {str(e)}")


@router.get("/providers")
async def get_supported_providers() -> Dict[str, list]:
    """Get list of supported OAuth providers."""
    return {
        "providers": oauth_service.get_supported_providers()
    }
