"""Models package initializer.

Import models here so Alembic can import `app.models` to populate metadata.
"""
from .user import User
from .chat import Chat
from .message import Message
from .sensor import SensorData

__all__ = ["User", "Chat", "Message", "SensorData"]
