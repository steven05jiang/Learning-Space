from contextlib import asynccontextmanager

from fastapi import FastAPI

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
