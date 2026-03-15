"""
Dependency injection utilities for the API.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.jwt import verify_token
from models.database import get_db
from models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.

    Reads the JWT token from the Authorization header, validates it,
    and returns the authenticated user object from the database.

    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found.
    """
    # Extract token from credentials
    token = credentials.credentials

    # Verify the JWT token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up user in database
    try:
        user_id_int = int(user_id)
    except ValueError:
        # Handle case where user_id is not a valid integer
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        stmt = select(User).where(User.id == user_id_int).options(selectinload(User.accounts))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        # Re-raise HTTPExceptions (like "User not found")
        raise
    except Exception:
        # Handle any database errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
