"""Chat model."""
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship
import uuid
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.message import Message


class Chat(BaseModel, table=True):
    __tablename__ = "chats"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(PG_UUID(as_uuid=True), server_default=text('gen_random_uuid()'), primary_key=True))
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    title: str = Field(default="New Chat", max_length=255)

    messages: List["Message"] = Relationship(back_populates="chat")
