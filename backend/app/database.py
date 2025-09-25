"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis.asyncio as redis

from app.config import settings

# SQLAlchemy setup with optimized connection pooling for production load
# Optimized settings for concurrent ML API requests
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,
    # Optimized connection pool settings for concurrent load
    pool_size=20,           # Base connections (increased from 5)
    max_overflow=30,        # Additional connections (increased from 10)
    pool_timeout=5,         # Connection timeout in seconds (decreased from 30)
    pool_recycle=3600,      # Recycle connections every hour
    # Additional optimizations
    connect_args={
        "connect_timeout": 10,
        "application_name": "rockettrainer_ml_api"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Redis setup
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_db():
    """
    Dependency to get database session with improved error handling.

    Provides proper session lifecycle management with connection pool monitoring
    and automatic cleanup on exceptions.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Rollback any pending transaction on error
        db.rollback()
        # Log database session error for monitoring
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("Database session error",
                    error=str(e),
                    pool_status=get_db_pool_status())
        raise
    finally:
        # Always close the session to return connection to pool
        db.close()


async def get_redis():
    """Dependency to get Redis client."""
    return redis_client


async def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db_pool_status():
    """Get database connection pool status for monitoring."""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in_connections": pool.checkedin(),
        "checked_out_connections": pool.checkedout(),
        "overflow_connections": pool.overflow(),
        "invalid_connections": 0,  # QueuePool doesn't have invalid() method
        "total_connections": pool.size() + pool.overflow(),
        "utilization_percent": round((pool.checkedout() / (pool.size() + pool.overflow())) * 100, 2) if (pool.size() + pool.overflow()) > 0 else 0
    }


async def close_db():
    """Close database connections."""
    await redis_client.close()
