import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from core.config import settings
from core.errors import (
    APIError,
    api_exception_handler,
    generic_exception_handler,
    http_exception_wrapper,
)
from models.database import get_db
from routers import agent, auth, categories, chat, graph, health, jobs, resources
from services.neo4j_driver import neo4j_driver

logging.getLogger().setLevel(settings.log_level.upper())
logging.getLogger("uvicorn").setLevel(settings.log_level.upper())
logging.getLogger("uvicorn.access").setLevel(settings.log_level.upper())

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    root_level = logging.getLevelName(logging.getLogger("uvicorn").getEffectiveLevel())
    logger.info("API starting up | log_level=%s", root_level)

    from core.telemetry import setup_telemetry

    metrics_app = setup_telemetry(
        service_name=settings.otel_service_name,
        traces_endpoint=settings.otlp_traces_endpoint,
        metrics_enabled=settings.prometheus_metrics,
        app=app,
    )
    if metrics_app:
        app.mount("/metrics", metrics_app)

    await neo4j_driver.connect()
    yield
    # Shutdown
    await neo4j_driver.disconnect()


app = FastAPI(title="Learning Space API", version="0.1.0", lifespan=lifespan)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers in order of specificity
app.add_exception_handler(APIError, api_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_wrapper)
app.add_exception_handler(HTTPException, http_exception_wrapper)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(resources.router)
app.include_router(categories.router)
app.include_router(jobs.router)
app.include_router(graph.router)
app.include_router(agent.router)
app.include_router(chat.router)


@app.get("/db-health")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Database health check endpoint."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "database healthy"}
    except Exception as e:
        return {"status": "database error", "detail": str(e)}
