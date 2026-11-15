from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.logging import logger


class Base(DeclarativeBase):
    """Base declarative model class for SQLAlchemy."""
    pass


# Global engine and session factory references
engine = None
async_session_maker = None

if settings.DATABASE_URL:
    try:
        # Convert postgres:// or postgresql:// to postgresql+asyncpg:// if needed
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

        engine = create_async_engine(
            db_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            echo=settings.DEBUG,
        )
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("Database engine initialized for configured connection.")
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {e}")
        engine = None
        async_session_maker = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions."""
    if async_session_maker is None:
        raise RuntimeError("Database connection is not configured yet (prepared for Supabase PostgreSQL in Phase 2).")
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> Dict[str, Any]:
    """
    Truthfully check database connectivity.
    Never reports connected unless verified by an actual database query.
    """
    if not settings.DATABASE_URL or engine is None:
        return {
            "status": "not_configured",
            "connected": False,
            "provider": "Supabase PostgreSQL (prepared for Phase 2)",
            "message": "DATABASE_URL is not set. Awaiting Phase 2 Supabase PostgreSQL configuration.",
        }

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            if val == 1:
                return {
                    "status": "connected",
                    "connected": True,
                    "provider": "Supabase PostgreSQL",
                    "message": "Connection verified via live query.",
                }
            return {
                "status": "degraded",
                "connected": False,
                "provider": "Supabase PostgreSQL",
                "message": f"Unexpected ping response: {val}",
            }
    except Exception as e:
        logger.warning(f"Database connectivity check failed: {e}")
        return {
            "status": "disconnected",
            "connected": False,
            "provider": "Supabase PostgreSQL",
            "error": str(e),
            "message": "Database server unreachable or credentials invalid.",
        }
