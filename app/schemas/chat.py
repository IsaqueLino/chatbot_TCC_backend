from typing import List, Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, Field

from app.schemas.message import MessageCreate, MessageRead


class ChatCreate(BaseModel):
    user_id: uuid.UUID
    title: Optional[str] = Field(default="New Chat")


class ChatRead(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    title: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class ChatRequest(BaseModel):
    messages: List[MessageCreate]
    chat_id: Optional[uuid.UUID] = None


class ChatResponse(BaseModel):
    messages: List[MessageRead]
