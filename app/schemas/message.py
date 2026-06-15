from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: uuid.UUID
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
