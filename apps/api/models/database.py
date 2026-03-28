from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings

# Create declarative base
Base = declarative_base()

# Create async engine
# statement_cache_size=0 required when using Supabase transaction pooler (pgbouncer)
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
    connect_args={"statement_cache_size": 0},
)

# Create async session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Dependency to get database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
