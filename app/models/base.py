"""Base models and common imports for all models."""

from datetime import (
    UTC,
    datetime,
)
from typing import (
    List,
    Optional,
)

from sqlmodel import (
    Field,
    Relationship,
    SQLModel,
)


class BaseModel(SQLModel):
    """Base model with common fields."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None), sa_column_kwargs={"server_default": "NOW()"}
    )
    update_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None), sa_column_kwargs={"server_default": "NOW()", "onupdate": "NOW()"}
    ) 
    deleted_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"index": True})
