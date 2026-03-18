from datetime import datetime
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.jwt import create_access_token
from models.account import Account
from models.user import User


class AuthService:
    """Authentication service for OAuth login."""

    async def find_user_by_provider_account(
        self, db: AsyncSession, provider: str, provider_account_id: str
    ) -> Optional[User]:
        """Find user by provider account."""
        stmt = (
            select(User)
            .join(Account)
            .where(
                Account.provider == provider,
                Account.provider_account_id == provider_account_id,
            )
            .options(selectinload(User.accounts))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Find user by email address."""
        stmt = (
            select(User)
            .where(User.email == email)
            .options(selectinload(User.accounts))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user_with_account(
        self,
        db: AsyncSession,
        provider: str,
        provider_account_id: str,
        access_token: str,
        user_info: Dict,
        refresh_token: Optional[str] = None,
    ) -> User:
        """Create a new user with associated OAuth account."""
        # Create user
        user = User(
            email=user_info.get(
                "email", f"{provider}_{provider_account_id}@example.com"
            ),
            display_name=user_info.get("display_name", "Unknown User"),
            avatar_url=user_info.get("avatar_url"),
        )
        db.add(user)
        await db.flush()  # Get the user ID

        # Create account
        account = Account(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=access_token,
            refresh_token=refresh_token,
            last_login_at=datetime.utcnow(),
        )
        db.add(account)
        await db.commit()

        # Refresh to get relationships
        await db.refresh(user, ["accounts"])
        return user

    async def update_account_tokens(
        self,
        db: AsyncSession,
        user: User,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
    ) -> None:
        """Update account tokens and last login time."""
        for account in user.accounts:
            if account.provider == provider:
                account.access_token = access_token
                if refresh_token:
                    account.refresh_token = refresh_token
                account.last_login_at = datetime.utcnow()
                break
        await db.commit()

    def generate_jwt_token(self, user: User) -> str:
        """Generate JWT token for authenticated user."""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
        }
        return create_access_token(token_data)

    async def authenticate_oauth_user(
        self,
        db: AsyncSession,
        provider: str,
        provider_account_id: str,
        access_token: str,
        user_info: Dict,
        refresh_token: Optional[str] = None,
    ) -> Tuple[User, str]:
        """
        Authenticate or create OAuth user.

        This method handles three scenarios:
        1. User has this provider account linked → update tokens
        2. User exists by email but doesn't have this provider → link the account
        3. No user exists → create new user and account

        Returns (user, jwt_token).
        """
        # First, check if this specific provider account is already linked to a user
        user = await self.find_user_by_provider_account(
            db, provider, provider_account_id
        )

        if user:
            # Scenario 1: Provider account already linked, update tokens
            await self.update_account_tokens(
                db, user, provider, access_token, refresh_token
            )
        else:
            # Check if a user exists with this email from any provider
            email = user_info.get("email")
            if email:
                user_by_email = await self.find_user_by_email(db, email)
                if user_by_email:
                    # Scenario 2: User exists but doesn't have this provider linked
                    # Link this provider account to the existing user
                    account = Account(
                        user_id=user_by_email.id,
                        provider=provider,
                        provider_account_id=provider_account_id,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        last_login_at=datetime.utcnow(),
                    )
                    db.add(account)
                    await db.commit()

                    # Refresh to get updated accounts
                    await db.refresh(user_by_email, ["accounts"])
                    user = user_by_email
                else:
                    # Scenario 3: No user exists, create new user and account
                    user = await self.create_user_with_account(
                        db,
                        provider,
                        provider_account_id,
                        access_token,
                        user_info,
                        refresh_token,
                    )
            else:
                # No email provided by OAuth provider, create user anyway
                user = await self.create_user_with_account(
                    db,
                    provider,
                    provider_account_id,
                    access_token,
                    user_info,
                    refresh_token,
                )

        # Generate JWT token
        jwt_token = self.generate_jwt_token(user)
        return user, jwt_token

    async def link_oauth_account(
        self,
        db: AsyncSession,
        current_user: User,
        provider: str,
        provider_account_id: str,
        access_token: str,
        user_info: Dict,
        refresh_token: Optional[str] = None,
    ) -> User:
        """
        Link OAuth account to existing user.

        Args:
            db: Database session
            current_user: Current authenticated user
            provider: OAuth provider name
            provider_account_id: Provider's user ID
            access_token: OAuth access token
            user_info: User info from provider
            refresh_token: Optional refresh token

        Returns:
            Updated user object

        Raises:
            HTTPException: 409 if account already belongs to another user
        """
        # Check if this provider account already exists for any user
        existing_user = await self.find_user_by_provider_account(
            db, provider, provider_account_id
        )

        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"This {provider} account is already linked to another user",
            )

        if existing_user and existing_user.id == current_user.id:
            # Account already linked to this user, just update tokens
            await self.update_account_tokens(
                db, current_user, provider, access_token, refresh_token
            )
        else:
            # Create new account link for current user
            account = Account(
                user_id=current_user.id,
                provider=provider,
                provider_account_id=provider_account_id,
                access_token=access_token,
                refresh_token=refresh_token,
                last_login_at=datetime.utcnow(),
            )
            db.add(account)
            await db.commit()

        # Refresh user to get updated accounts
        await db.refresh(current_user, ["accounts"])
        return current_user

    async def unlink_oauth_account(
        self,
        db: AsyncSession,
        current_user: User,
        account_id: int,
    ) -> None:
        """
        Unlink OAuth account from user.

        Args:
            db: Database session
            current_user: Current authenticated user
            account_id: Account ID to unlink

        Raises:
            HTTPException: 404 if account not found or doesn't belong to user
            HTTPException: 400 if trying to unlink the last account
        """
        # Find the account and verify it belongs to the user
        account = None
        for user_account in current_user.accounts:
            if user_account.id == account_id:
                account = user_account
                break

        if not account:
            from core.errors import ErrorCode, NotFoundError

            raise NotFoundError(
                detail="Account not found or does not belong to current user",
                code=ErrorCode.ACCOUNT_NOT_FOUND,
            )

        # Check if user has only one account (including the one we're trying to unlink)
        if len(current_user.accounts) <= 1:
            from core.errors import cannot_unlink_last_account

            raise cannot_unlink_last_account()

        # Delete the account
        await db.delete(account)
        await db.commit()


auth_service = AuthService()
