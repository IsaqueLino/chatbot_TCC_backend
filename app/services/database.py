from typing import (
    List,
    Optional,
)
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import (
    SQLModel,
    select,
)

from app.core.config import settings
from app.core.logger import logger
from app.models.user import User


class DatabaseService:
    """Service class for database operations.

    This class handles all database operations for Users, Sessions, and Messages.
    It uses SQLModel for ORM operations and maintains an async connection pool.
    """

    def __init__(self):
        try:
            pool_size = settings.DATABASE_POOL_SIZE
            max_overflow = settings.DATABASE_MAX_OVERFLOW
            pool_timeout = settings.DATABASE_POOL_TIMEOUT
            pool_recycle = settings.DATABASE_POOL_RECYCLE

            try:
                self.async_engine = create_async_engine(
                    settings.database_url_async,
                    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_timeout=pool_timeout,
                    pool_recycle=pool_recycle,
                    echo=settings.DATABASE_ECHO,
                )
            except ModuleNotFoundError as e:
                # Commonly raised when the async DB driver (e.g., asyncpg) is missing.
                msg = (
                    "Database async driver not installed. Please install the required "
                    "package for your DATABASE_URL (e.g. `pip install asyncpg`)."
                )
                logger.error("missing_db_driver", extra={"error": str(e), "detail": msg})
                raise RuntimeError(msg) from e

            self.async_session = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info("async_database_initialized", extra={"environment": settings.ENVIRONMENT, "pool_size": pool_size, "max_overflow": max_overflow, "pool_timeout": pool_timeout, "pool_recycle": pool_recycle})
        except SQLAlchemyError as e:
            logger.error("database_initialization_error", extra={"error": str(e), "environment": settings.ENVIRONMENT})
            if not settings.is_production:
                raise

    async def create_tables(self):
        # Do not run migrations automatically on application startup.
        # Migrations must be applied manually by the operator using
        # `alembic upgrade head`. This avoids unexpected schema changes
        # during development and gives control to the deploy process.
        logger.info("create_tables_skipped", extra={"note": "Migrations not run automatically; run alembic manually"})
        return

    async def create_user(self, email: str, password: str, level: str = "USER") -> User:
        from app.models.user import UserLevel

        async with self.async_session() as session:
            user = User(
                email=email, 
                hashed_password=password, 
                level=UserLevel(level.upper())
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info("user_created", extra={"email": email, "level": level})
            return user

    async def create_azure_user(
        self, 
        email: str, 
        azure_id: str, 
        organization: str = "", 
        organization_user_id: str = "",
        level: str = "USER"
    ) -> User:
        from app.models.user import UserLevel

        async with self.async_session() as session:
            user = User(
                email=email,
                level=UserLevel(level.upper()),
                hashed_password=None
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info("azure_user_created", extra={"email": email, "level": level, "organization": organization})
            return user

    async def update_user_provider(
        self, 
        user_id: uuid.UUID, 
        provider: str, 
        azure_id: str, 
        organization: str = "", 
        organization_user_id: str = ""
    ) -> User:
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user.hashed_password = None
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info("user_provider_updated", extra={"user_id": user_id, "provider": provider})
            return user

    async def get_user(self, user_id: uuid.UUID) -> Optional[User]:
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with self.async_session() as session:
            statement = select(User).where(User.email == email)
            result = await session.execute(statement)
            user = result.scalar_one_or_none()
            return user

    async def delete_user_by_email(self, email: str) -> bool:
        async with self.async_session() as session:
            statement = select(User).where(User.email == email)
            result = await session.execute(statement)
            user = result.scalar_one_or_none()
            if not user:
                return False

            await session.delete(user)
            await session.commit()
            logger.info("user_deleted", extra={"email": email})
            return True

    # Session persistence removed; session-related helpers were deleted.

    def get_async_session_maker(self):
        return self.async_session

    async def health_check(self) -> bool:
        try:
            async with self.async_session() as session:
                result = await session.execute(select(1))
                result.scalar()
                return True
        except Exception as e:
            logger.error("database_health_check_failed", extra={"error": str(e)})
            return False


database_service = DatabaseService()