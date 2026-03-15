from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db

app = FastAPI(title="Learning Space API", version="0.1.0")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/db-health")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Database health check endpoint."""
    try:
        # Simple query to test database connection
        await db.execute("SELECT 1")
        return {"status": "database healthy"}
    except Exception as e:
        return {"status": "database error", "error": str(e)}
