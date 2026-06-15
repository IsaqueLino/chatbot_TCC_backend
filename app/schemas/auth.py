import re
import uuid
from datetime import datetime
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
)
from app.models.user import UserLevel


class Token(BaseModel):
    access_token: str = Field(..., description="The JWT access token")
    token_type: str = Field(default="bearer", description="The type of token")
    expires_at: datetime = Field(..., description="The token expiration timestamp")

    class Config:
        populate_by_name = True


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="The JWT access token")
    token_type: str = Field(default="bearer", description="The type of token")
    expires_at: datetime = Field(..., description="When the token expires")


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: SecretStr = Field(..., description="User's password", min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: SecretStr) -> SecretStr:
        password = v.get_secret_value()

        if len(password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")

        if not re.search(r"[A-Z]", password):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula")

        if not re.search(r"[a-z]", password):
            raise ValueError("A senha deve conter pelo menos uma letra minúscula")

        if not re.search(r"[0-9]", password):
            raise ValueError("A senha deve conter pelo menos um número")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("A senha deve conter pelo menos um caractere especial")

        return v

class ProviderMismatchError(BaseModel):
    detail: str = Field(..., description="Error message")
    current_provider: str = Field(..., description="Current authentication provider")
    suggested_action: str = Field(..., description="Suggested action for the user")


class UserResponse(BaseModel):
    id: uuid.UUID = Field(..., description="User's ID")
    email: str = Field(..., description="User's email address")
    level: UserLevel = Field(..., description="User access level")
    token: Token = Field(..., description="Authentication token")

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    session_id: str = Field(..., description="The unique identifier for the chat session")
    name: str = Field(default="", description="Name of the session", max_length=100)
    token: Token = Field(..., description="The authentication token for the session")

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        sanitized = re.sub(r'[<>{}[\]()\'"`]', "", v)
        return sanitized