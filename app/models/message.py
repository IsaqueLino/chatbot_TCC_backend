"""Message model."""
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship
import uuid
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.chat import Chat


class Message(BaseModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(PG_UUID(as_uuid=True), server_default=text('gen_random_uuid()'), primary_key=True))
    chat_id: Optional[uuid.UUID] = Field(default=None, foreign_key="chats.id")
    role: str = Field(max_length=32)
    content: str

    chat: "Chat" = Relationship(back_populates="messages")
