"""Category management endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_current_user_optional
from models.category import Category
from models.database import get_db
from models.resource import Resource
from models.user import User
from schemas.category import CategoryCreate, CategoryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> list[CategoryResponse]:
    """
    List all categories visible to the user.

    Returns:
    - All system categories + user's own categories if authenticated
    - System categories only if unauthenticated
    """
    if current_user:
        # Return system categories + user's own categories
        stmt = (
            select(Category)
            .where(or_(Category.is_system, Category.owner_id == current_user.id))
            .order_by(Category.is_system.desc(), Category.name)
        )
    else:
        # Return only system categories
        stmt = select(Category).where(Category.is_system).order_by(Category.name)

    result = await db.execute(stmt)
    categories = result.scalars().all()

    # Convert to response objects, renaming owner_id to user_id
    response_categories = []
    for category in categories:
        response_categories.append(
            CategoryResponse(
                id=category.id,
                name=category.name,
                is_system=category.is_system,
                user_id=category.owner_id,
                created_at=category.created_at,
            )
        )

    return response_categories


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """
    Create a new user-owned category.

    Returns:
    - 409 if name already exists for this user (case-insensitive)
    """
    # Check for duplicate name (case-insensitive) for this user
    # Check both system categories and user's own categories
    stmt = select(Category).where(
        func.lower(Category.name) == func.lower(category_data.name),
        or_(Category.is_system, Category.owner_id == current_user.id),
    )
    result = await db.execute(stmt)
    existing_category = result.scalar_one_or_none()

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{category_data.name}' already exists",
        )

    # Create new category
    new_category = Category(
        name=category_data.name, is_system=False, owner_id=current_user.id
    )

    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)

    logger.info(f"Created category '{category_data.name}' for user {current_user.id}")

    return CategoryResponse(
        id=new_category.id,
        name=new_category.name,
        is_system=new_category.is_system,
        user_id=new_category.owner_id,
        created_at=new_category.created_at,
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a user-owned category.

    Returns:
    - 403 if trying to delete a system category
    - 404 if category not found or not owned by user
    """
    # Find the category
    stmt = select(Category).where(Category.id == category_id)
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Check if it's a system category
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system category",
        )

    # Check if user owns the category
    if category.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Block deletion if any resources still reference this category.
    # Fetch category arrays for the user's resources and check in Python —
    # avoids JSONB-specific SQL so this works on both PostgreSQL and SQLite (tests).
    cats_result = await db.execute(
        select(Resource.top_level_categories).where(
            Resource.owner_id == current_user.id
        )
    )
    resource_count = sum(
        1
        for (cats,) in cats_result
        if cats and category.name in cats
    )
    if resource_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Category is used by {resource_count} resource(s). "
                "Remove it from all resources before deleting."
            ),
        )

    await db.delete(category)
    await db.commit()

    logger.info(
        f"Deleted category '{category.name}' (id={category_id}) "
        f"for user {current_user.id}"
    )
