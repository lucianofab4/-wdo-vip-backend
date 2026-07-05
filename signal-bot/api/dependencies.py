from database.connection import AsyncSessionFactory
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session
