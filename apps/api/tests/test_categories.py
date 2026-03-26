"""Tests for category management endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.category import Category
from models.user import User


@pytest.fixture
async def test_user_2(db_session: AsyncSession) -> User:
    """Create a second test user in the database."""
    user = User(
        email="test2@example.com",
        display_name="Test User 2",
        avatar_url="https://example.com/avatar2.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_category(db_session: AsyncSession, test_user: User) -> Category:
    """Create a test user category in the database."""
    category = Category(
        name="Test Category",
        is_system=False,
        owner_id=test_user.id
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


class TestListCategories:
    """Test cases for GET /categories."""

    @pytest.mark.asyncio
    async def test_list_categories_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test listing categories without authentication returns only system categories."""
        response = await client.get("/categories")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # 10 system categories seeded

        # All categories should be system categories
        for category in data:
            assert category["is_system"] is True
            assert category["user_id"] is None
            assert "id" in category
            assert "name" in category
            assert "created_at" in category

        # Check that all expected system categories are present
        category_names = {cat["name"] for cat in data}
        expected_names = {
            "Technology", "Science", "Business", "Arts", "Health",
            "Education", "Politics", "Entertainment", "Sports", "Philosophy"
        }
        assert category_names == expected_names

    @pytest.mark.asyncio
    async def test_list_categories_authenticated_no_user_categories(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing categories with authentication but no user categories."""
        response = await client.get("/categories", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 10  # Only system categories

        # All categories should be system categories
        for category in data:
            assert category["is_system"] is True
            assert category["user_id"] is None

    @pytest.mark.asyncio
    async def test_list_categories_authenticated_with_user_categories(
        self, client: AsyncClient, auth_headers: dict, test_category: Category
    ):
        """Test listing categories with authentication includes user categories."""
        response = await client.get("/categories", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 11  # 10 system + 1 user category

        # Check that user category is included
        user_categories = [cat for cat in data if not cat["is_system"]]
        assert len(user_categories) == 1
        assert user_categories[0]["name"] == "Test Category"
        assert user_categories[0]["user_id"] == test_category.owner_id

    @pytest.mark.asyncio
    async def test_list_categories_user_isolation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_user_2: User,
        auth_headers: dict
    ):
        """Test that users only see their own categories, not other users'."""
        # Create categories for both users
        user1_category = Category(
            name="User 1 Category",
            is_system=False,
            owner_id=test_user.id
        )
        user2_category = Category(
            name="User 2 Category",
            is_system=False,
            owner_id=test_user_2.id
        )
        db_session.add(user1_category)
        db_session.add(user2_category)
        await db_session.commit()

        # Get categories for user 1
        response = await client.get("/categories", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        user_categories = [cat for cat in data if not cat["is_system"]]
        assert len(user_categories) == 1
        assert user_categories[0]["name"] == "User 1 Category"


class TestCreateCategory:
    """Test cases for POST /categories."""

    @pytest.mark.asyncio
    async def test_create_category_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a category successfully."""
        category_data = {"name": "My Research"}

        response = await client.post("/categories", json=category_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "My Research"
        assert data["is_system"] is False
        assert data["user_id"] is not None
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_category_unauthenticated(self, client: AsyncClient):
        """Test creating a category without authentication fails."""
        category_data = {"name": "My Research"}

        response = await client.post("/categories", json=category_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_category_empty_name(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a category with empty name fails."""
        category_data = {"name": ""}

        response = await client.post("/categories", json=category_data, headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_category_whitespace_name(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a category with whitespace-only name fails."""
        category_data = {"name": "   "}

        response = await client.post("/categories", json=category_data, headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_category_duplicate_user_category(
        self, client: AsyncClient, auth_headers: dict, test_category: Category
    ):
        """Test creating a category with duplicate name for same user fails."""
        category_data = {"name": "Test Category"}

        response = await client.post("/categories", json=category_data, headers=auth_headers)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_category_duplicate_system_category(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a category with duplicate system category name fails."""
        category_data = {"name": "Technology"}

        response = await client.post("/categories", json=category_data, headers=auth_headers)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_category_case_insensitive_duplicate(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a category with case variation of system category fails."""
        category_data = {"name": "technology"}  # lowercase

        response = await client.post("/categories", json=category_data, headers=auth_headers)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_category_same_name_different_users(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_2: User,
        auth_headers: dict
    ):
        """Test that different users can create categories with same name."""
        # Create category for user 1
        category_data = {"name": "My Research"}
        response = await client.post("/categories", json=category_data, headers=auth_headers)
        assert response.status_code == 201

        # Create JWT for user 2
        from core.jwt import create_access_token
        token_data = {
            "sub": str(test_user_2.id),
            "email": test_user_2.email,
            "display_name": test_user_2.display_name,
        }
        token = create_access_token(token_data)
        user2_headers = {"Authorization": f"Bearer {token}"}

        # Create same-named category for user 2 - should succeed
        response = await client.post("/categories", json=category_data, headers=user2_headers)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_category_name_trimming(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that category names are trimmed of whitespace."""
        category_data = {"name": "  My Research  "}

        response = await client.post("/categories", json=category_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "My Research"


class TestDeleteCategory:
    """Test cases for DELETE /categories/{id}."""

    @pytest.mark.asyncio
    async def test_delete_category_success(
        self, client: AsyncClient, auth_headers: dict, test_category: Category
    ):
        """Test deleting a category successfully."""
        response = await client.delete(f"/categories/{test_category.id}", headers=auth_headers)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_category_unauthenticated(
        self, client: AsyncClient, test_category: Category
    ):
        """Test deleting a category without authentication fails."""
        response = await client.delete(f"/categories/{test_category.id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_category_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent category fails."""
        response = await client.delete("/categories/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category_not_owner(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_2: User,
        auth_headers: dict
    ):
        """Test deleting category not owned by user fails."""
        # Create category for user 2
        other_category = Category(
            name="Other User Category",
            is_system=False,
            owner_id=test_user_2.id
        )
        db_session.add(other_category)
        await db_session.commit()
        await db_session.refresh(other_category)

        # Try to delete with user 1's auth
        response = await client.delete(f"/categories/{other_category.id}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_system_category(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict
    ):
        """Test deleting a system category fails."""
        # Get a system category
        stmt = select(Category).where(Category.is_system == True)
        result = await db_session.execute(stmt)
        system_category = result.scalars().first()
        assert system_category is not None

        response = await client.delete(f"/categories/{system_category.id}", headers=auth_headers)
        assert response.status_code == 403
        assert "system category" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_category_persistence(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_category: Category
    ):
        """Test that category is actually removed from database."""
        category_id = test_category.id

        # Delete the category
        response = await client.delete(f"/categories/{category_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone from database
        stmt = select(Category).where(Category.id == category_id)
        result = await db_session.execute(stmt)
        deleted_category = result.scalar_one_or_none()
        assert deleted_category is None