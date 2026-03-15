from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from routers import health
from services.neo4j_driver import neo4j_driver


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    await neo4j_driver.connect()
    yield
    # Shutdown
    await neo4j_driver.disconnect()


app = FastAPI(
    title="Learning Space API",
    version="0.1.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health.router)


@app.get("/db-health")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Database health check endpoint."""
    try:
        # Simple query to test database connection
        await db.execute(text("SELECT 1"))
        return {"status": "database healthy"}
    except Exception:
        return {"status": "database error"}
