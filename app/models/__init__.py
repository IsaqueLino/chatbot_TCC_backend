"""Models package initializer.

Import models here so Alembic can import `app.models` to populate metadata.
"""
from .user import User  # noqa: F401
from .chat import Chat  # noqa: F401
from .message import Message  # noqa: F401

__all__ = ["User", "Chat", "Message"]
