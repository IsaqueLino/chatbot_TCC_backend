"""This file contains the user model for the application."""

from enum import Enum
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
)

import bcrypt
from sqlmodel import (
    Field,
    Relationship,
)
import uuid
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class UserLevel(str, Enum):
    """User access levels."""

    ADMIN = "ADMIN"
    USER = "USER"

class User(BaseModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(PG_UUID(as_uuid=True), server_default=text('gen_random_uuid()'), primary_key=True))
    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(default="", max_length=150)
    hashed_password: Optional[str] = Field(default=None, max_length=255)
    level: UserLevel = Field(default=UserLevel.USER)
    # sessions relationship removed; sessions are handled as stateless JWTs

    def verify_password(self, password: str) -> bool:
        """Verify if the provided password matches the hash."""
        if not self.hashed_password:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.hashed_password.encode("utf-8"))

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

# Session model removed; sessions are stateless JWTs
