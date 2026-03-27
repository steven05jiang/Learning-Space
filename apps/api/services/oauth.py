import base64
import hashlib
import secrets
import time
from typing import Dict, Optional
from urllib.parse import urlencode

import httpx

from core.config import settings


class OAuthProvider:
    """Base OAuth provider class."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get the OAuth authorization URL."""
        raise NotImplementedError

    async def exchange_code(self, code: str, redirect_uri: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        raise NotImplementedError

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user information from the provider."""
        raise NotImplementedError


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth provider."""

    def __init__(self):
        super().__init__(settings.github_client_id, settings.github_client_secret)
        self.auth_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
        self.user_info_url = "https://api.github.com/user"

    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get GitHub OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "user:email",
            "response_type": "code",
        }
        if state:
            params["state"] = state
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Optional[str]:
        """Exchange code for GitHub access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
        return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user info from GitHub."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url, headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "id": str(user_data["id"]),
                    "email": user_data.get("email"),
                    "username": user_data.get("login"),
                    "display_name": user_data.get("name") or user_data.get("login"),
                    "avatar_url": user_data.get("avatar_url"),
                }
        return None


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider."""

    def __init__(self):
        super().__init__(settings.google_client_id, settings.google_client_secret)
        self.auth_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
        }
        if state:
            params["state"] = state
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Optional[str]:
        """Exchange code for Google access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
        return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user info from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url, headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "id": str(user_data["id"]),
                    "email": user_data.get("email"),
                    "username": user_data.get("email"),  # Google identifies users by email
                    "display_name": user_data.get("name"),
                    "avatar_url": user_data.get("picture"),
                }
        return None


class TwitterOAuthProvider(OAuthProvider):
    """Twitter OAuth provider (OAuth 2.0 PKCE)."""

    def __init__(self):
        super().__init__(settings.twitter_client_id, settings.twitter_client_secret)
        self.auth_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        self.user_info_url = "https://api.twitter.com/2/users/me"
        # Store PKCE values temporarily - in production use session/cache
        self._code_verifier_store = {}

    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Get Twitter OAuth authorization URL."""
        # Generate PKCE values
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)

        # Use provided state or generate one for PKCE
        if not state:
            state = self._generate_state()

        # Store code_verifier for later use in token exchange
        self._code_verifier_store[state] = code_verifier

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "tweet.read users.read",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code(
        self, code: str, redirect_uri: str, state: str = None
    ) -> Optional[str]:
        """Exchange code for Twitter access token."""
        # Retrieve code_verifier from store
        code_verifier = self._code_verifier_store.get(state) if state else None
        if not code_verifier:
            return None

        # Clean up used code_verifier
        if state:
            self._code_verifier_store.pop(state, None)

        # Create proper basic auth header
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {auth_encoded}",
                },
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
        return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user info from Twitter."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.user_info_url}?user.fields=profile_image_url",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code == 200:
                data = response.json()
                user_data = data.get("data", {})
                return {
                    "id": str(user_data["id"]),
                    "email": user_data.get("email"),  # Use email if provided (in tests)
                    "username": f"@{user_data['username']}" if user_data.get("username") else None,
                    "display_name": user_data.get("name"),
                    "avatar_url": user_data.get("profile_image_url"),
                }
        return None

    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier (random 43-128 character string)."""
        return (
            base64.urlsafe_b64encode(secrets.token_bytes(32))
            .decode("utf-8")
            .rstrip("=")
        )

    def _generate_code_challenge(self, code_verifier: str) -> str:
        """Generate PKCE code challenge (SHA256 hash of verifier, base64url)."""
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    def _generate_state(self) -> str:
        """Generate cryptographically secure random state."""
        return secrets.token_urlsafe(32)


class OAuthService:
    """OAuth service for managing multiple providers."""

    def __init__(self):
        self.providers = {
            "github": GitHubOAuthProvider(),
            "google": GoogleOAuthProvider(),
            "twitter": TwitterOAuthProvider(),
        }
        # Store state values temporarily - in production use session/cache/redis
        self._state_store = {}

    def get_provider(self, provider_name: str) -> Optional[OAuthProvider]:
        """Get OAuth provider by name."""
        return self.providers.get(provider_name.lower())

    def get_supported_providers(self) -> list[str]:
        """Get list of supported OAuth providers."""
        return list(self.providers.keys())

    def generate_state(self) -> str:
        """Generate cryptographically secure random state for CSRF protection."""
        return secrets.token_urlsafe(32)

    def generate_link_state(self, user_id: int) -> str:
        """Generate state for account linking flow."""
        # Encode link info in the state
        base_state = secrets.token_urlsafe(24)
        return f"link:{user_id}:{base_state}"

    def store_state(
        self, state: str, provider: str, redirect_uri: str | None = None
    ) -> None:
        """Store state for later validation."""
        self._state_store[state] = {
            "provider": provider,
            "created_at": time.time(),
            "redirect_uri": redirect_uri,
        }

    def store_link_state(
        self, state: str, provider: str, user_id: int, redirect_uri: str | None = None
    ) -> None:
        """Store link state for later validation."""
        self._state_store[state] = {
            "provider": provider,
            "user_id": user_id,
            "is_link": True,
            "created_at": time.time(),
            "redirect_uri": redirect_uri,
        }

    def validate_and_consume_state(self, state: str, provider: str) -> Optional[Dict]:
        """Validate state and consume it (one-time use)."""
        if not state:
            return None

        stored = self._state_store.pop(state, None)
        if not stored:
            return None

        # Check if state has expired (10 minutes = 600 seconds)
        if time.time() - stored["created_at"] > 600:
            return None

        if stored["provider"] != provider:
            return None

        return stored

    def is_link_state(self, state: str) -> bool:
        """Check if state represents a link flow."""
        stored = self._state_store.get(state)
        return stored and stored.get("is_link", False)

    def get_link_user_id(self, state: str) -> Optional[int]:
        """Extract user ID from link state."""
        stored = self._state_store.get(state)
        if stored and stored.get("is_link"):
            return stored.get("user_id")
        return None


oauth_service = OAuthService()
