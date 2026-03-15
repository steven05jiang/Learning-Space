"""
Neo4j driver service for Learning Space.
"""

import logging
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase

from core.config import settings

logger = logging.getLogger(__name__)


class Neo4jDriverService:
    """Async Neo4j driver service for database operations."""

    def __init__(self):
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Connect to Neo4j database and verify connectivity."""
        if self._driver is not None:
            return

        logger.info("Connecting to Neo4j database...")

        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

        # Verify connectivity
        try:
            await self._driver.verify_connectivity()
            logger.info("Neo4j connection verified successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            await self.disconnect()
            raise

        # Create uniqueness constraints on startup
        await self._create_constraints()

    async def disconnect(self) -> None:
        """Disconnect from Neo4j database."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("Disconnected from Neo4j database")

    async def _create_constraints(self) -> None:
        """Create uniqueness constraints for the graph schema."""
        constraints = [
            "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR "
            "(t:Tag) REQUIRE t.name IS UNIQUE"
        ]

        async with self._driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                    logger.info(f"Applied constraint: {constraint}")
                except Exception as e:
                    logger.warning(
                        f"Constraint may already exist or failed: {constraint} - {e}"
                    )

    def get_session(self):
        """Get a Neo4j session for database operations."""
        if self._driver is None:
            raise RuntimeError("Neo4j driver not connected. Call connect() first.")
        return self._driver.session()

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on the Neo4j connection."""
        if self._driver is None:
            return {"status": "error", "message": "Driver not connected"}

        try:
            async with self._driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record and record["test"] == 1:
                    return {
                        "status": "healthy",
                        "message": "Neo4j connection successful",
                    }
                else:
                    return {"status": "error", "message": "Invalid response from Neo4j"}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Neo4j health check failed: {str(e)}",
            }


# Global instance
neo4j_driver = Neo4jDriverService()


async def get_neo4j_driver() -> Neo4jDriverService:
    """Dependency function to get the Neo4j driver service."""
    return neo4j_driver
