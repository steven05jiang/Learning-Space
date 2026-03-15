from models.database import Base, engine


async def create_tables():
    """Create all database tables. Use for testing or initial setup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables. Use for testing cleanup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
