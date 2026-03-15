"""
Health check endpoints for the API.
"""
from fastapi import APIRouter, Depends

from services.neo4j_driver import Neo4jDriverService, get_neo4j_driver

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health():
    """Basic API health check."""
    return {"status": "healthy", "message": "API is running"}


@router.get("/neo4j")
async def neo4j_health(
    neo4j: Neo4jDriverService = Depends(get_neo4j_driver)
):
    """Neo4j database health check."""
    return await neo4j.health_check()
