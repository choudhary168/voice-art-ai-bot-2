import asyncio
import logging
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from backend.config import settings

logger = logging.getLogger(__name__)
engine = create_async_engine(settings.database_url, pool_size=settings.database_pool_size,
                             max_overflow=settings.database_max_overflow, pool_pre_ping=True,
                             connect_args={"timeout": 2})
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)
database_ready = False


async def check_database() -> bool:
    global database_ready
    if not settings.database_enabled:
        database_ready = False
        return False
    try:
        from sqlalchemy import text

        async def _ping():
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_ping(), timeout=2.0)
        database_ready = True
    except Exception:
        database_ready = False
        logger.warning("Database readiness check failed or timed out; degraded mode active")
    return database_ready


async def close_database() -> None:
    global database_ready
    database_ready = False
    await engine.dispose()
