"""
Database connection pool (Singleton Pattern).

This module provides database connection management using SQLAlchemy.
Follows Singleton pattern to ensure single connection pool instance.

Architecture:
- Part of Infrastructure Layer
- Implements database connection pooling
- Used by all layers for database access
"""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


# Logger will be initialized after config
def _get_logger():
    from app.core.logger import get_logger

    return get_logger(__name__)


class DatabaseManager:
    """Database connection manager (Singleton).

    Manages database connection pool and sessions.
    Follows Singleton pattern to ensure single connection pool.

    Attributes:
        engine: SQLAlchemy engine (connection pool)
        SessionLocal: Session factory
    """

    def __init__(self) -> None:
        """Initialize database manager."""
        logger = _get_logger()
        settings = get_settings()

        # Create engine with connection pooling
        db_url = settings.database_url_sync
        engine_kwargs: dict = {
            "echo": settings.DATABASE_ECHO,
        }
        # SQLite doesn't support pool_size/max_overflow/pool_recycle
        if not db_url.startswith("sqlite"):
            engine_kwargs.update(
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
                pool_recycle=3600,
            )
        else:
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        self.engine = create_engine(db_url, **engine_kwargs)

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        # Log connection pool info
        logger.info(
            "Database connection pool initialized",
            extra={"pool_size": settings.DATABASE_POOL_SIZE, "max_overflow": settings.DATABASE_MAX_OVERFLOW},
        )

    def get_session(self) -> Generator[Session, None, None]:
        """Get database session (dependency injection).

        Yields:
            Database session

        Example:
            ```python
            db = next(get_db())
            # Use db
            ```
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connections."""
        self.engine.dispose()
        logger = _get_logger()
        logger.info("Database connections closed")


@lru_cache
def get_database_manager() -> DatabaseManager:
    """Get database manager instance (Singleton).

    Uses @lru_cache to ensure single instance of DatabaseManager.
    This follows Singleton pattern for database connections.

    Returns:
        DatabaseManager instance (singleton)
    """
    return DatabaseManager()


# Export singleton instance and convenience functions
db_manager = get_database_manager()


def get_db() -> Generator[Session, None, None]:
    """Get database session (FastAPI dependency).

    This is the main function to use for dependency injection in FastAPI.

    Yields:
        Database session

    Example:
        ```python
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            # Use db
        ```
    """
    yield from db_manager.get_session()


def get_engine() -> Engine:
    """Get database engine.

    Returns:
        SQLAlchemy engine
    """
    return db_manager.engine
