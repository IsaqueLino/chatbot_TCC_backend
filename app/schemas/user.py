from pydantic import BaseModel
from typing import Optional
import uuid

from app.models.user import UserLevel


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    level: UserLevel

    class Config:
        from_attributes = True