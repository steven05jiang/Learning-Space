from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import (
    APIError,
    api_exception_handler,
    generic_exception_handler,
    http_exception_wrapper,
)
from models.database import get_db
from routers import auth, health, resources
from services.neo4j_driver import neo4j_driver


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    await neo4j_driver.connect()
    yield
    # Shutdown
    await neo4j_driver.disconnect()


app = FastAPI(title="Learning Space API", version="0.1.0", lifespan=lifespan)

# Register exception handlers in order of specificity
app.add_exception_handler(APIError, api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_wrapper)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(resources.router)


@app.get("/db-health")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Database health check endpoint."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "database healthy"}
    except Exception as e:
        return {"status": "database error", "detail": str(e)}
