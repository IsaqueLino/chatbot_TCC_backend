from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = Field(
        validation_alias=AliasChoices("PROJECT_NAME", "APP_NAME"),
        description="Application name"
    )
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
        description="Environment name",
    )
    VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(description="Debug mode")
    API_V1_PREFIX: str = Field(
        validation_alias=AliasChoices("API_V1_STR", "API_V1_PREFIX"),
        description="API version prefix"
    )
    CORS_ORIGINS: str = Field(
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "CORS_ORIGINS"),
        description="Comma-separated CORS origins",
    )

    DATABASE_URL: str = Field(
        description="PostgreSQL database URL",
        examples=["postgresql://user:password@localhost:5432/dbname"],
    )
    DATABASE_POOL_SIZE: int = Field(
        validation_alias=AliasChoices("POSTGRES_POOL_SIZE", "DATABASE_POOL_SIZE"),
        description="Database connection pool size",
        ge=1,
        le=50,
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        validation_alias=AliasChoices("POSTGRES_MAX_OVERFLOW", "DATABASE_MAX_OVERFLOW"),
        description="Database connection pool max overflow",
        ge=0,
    )
    DATABASE_POOL_PRE_PING: bool = Field(
        default=True,
        description="Enable connection pool pre-ping",
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        validation_alias=AliasChoices("POSTGRES_POOL_TIMEOUT", "DATABASE_POOL_TIMEOUT"),
        default=30,
        description="Database pool timeout",
    )
    DATABASE_POOL_RECYCLE: int = Field(
        validation_alias=AliasChoices("POSTGRES_POOL_RECYCLE", "DATABASE_POOL_RECYCLE"),
        default=1800,
        description="Database pool recycle timeout",
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries (for debugging)",
    )

    JWT_SECRET_KEY: str = Field(
        description="Secret key for JWT tokens",
    )
    JWT_ALGORITHM: str = Field(
        description="JWT algorithm",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration in minutes",
        ge=1,
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        validation_alias=AliasChoices("JWT_ACCESS_TOKEN_EXPIRE_DAYS", "REFRESH_TOKEN_EXPIRE_DAYS"),
        description="Refresh token expiration in days (MANDATORY: 30 days)",
        ge=1,
    )

    OAUTH2_MICROSOFT_CLIENT_ID: str | None = Field(
        default=None,
        description="Microsoft OAuth2 client ID",
    )
    OAUTH2_MICROSOFT_CLIENT_SECRET: str | None = Field(
        default=None,
        description="Microsoft OAuth2 client secret",
    )
    OAUTH2_GOOGLE_CLIENT_ID: str | None = Field(
        default=None,
        description="Google OAuth2 client ID",
    )
    OAUTH2_GOOGLE_CLIENT_SECRET: str | None = Field(
        default=None,
        description="Google OAuth2 client secret",
    )
    OAUTH2_GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/v1/auth/oauth/google/callback",
        description="Google OAuth2 redirect URI",
    )
    OAUTH2_MICROSOFT_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/v1/auth/oauth/microsoft/callback",
        description="Microsoft OAuth2 redirect URI",
    )
    OAUTH2_GITHUB_CLIENT_ID: str | None = Field(
        default=None,
        description="GitHub OAuth2 client ID",
    )
    OAUTH2_GITHUB_CLIENT_SECRET: str | None = Field(
        default=None,
        description="GitHub OAuth2 client secret",
    )

    CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable caching",
    )
    CACHE_TTL_SECONDS: int = Field(
        default=3600,
        description="Default cache TTL in seconds",
        ge=1,
    )
    REDIS_URL: str | None = Field(
        default=None,
        description="Redis URL for distributed cache",
        examples=["redis://localhost:6379/0"],
    )

    GOOGLE_APP: str | None = Field(default=None, description="Google email address")
    GOOGLE_SENHA_APP: str | None = Field(default=None, description="Google app password")
    SMTP_HOST: str | None = Field(default=None, description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    SMTP_USER: str | None = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: str | None = Field(default=None, description="SMTP password")
    SMTP_FROM_EMAIL: str = Field(
        default="noreply@oiko.com.br",
        description="From email address",
    )
    SMTP_FROM_NAME: str = Field(default="Atlas - OiKO", description="From name")
    FRONTEND_URL: str = Field(
        default="http://localhost:3001",
        description="Frontend URL for links in emails",
    )

    GEMINI_API_KEY: str | None = Field(default=None, description="Gemini API key")
    GEMINI_API_VERSION: str | None = Field(default=None, description="Gemini API version")
    GEMINI_ENDPOINT: str | None = Field(default=None, description="Gemini endpoint")
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API key",
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4",
        description="OpenAI model to use",
    )
    ANTHROPIC_API_KEY: str | None = Field(
        default=None,
        description="Anthropic API key",
    )
    ANTHROPIC_MODEL: str = Field(
        default="claude-3-opus-20240229",
        description="Anthropic model to use",
    )
    LLM_PROVIDER: Literal["openai", "anthropic", "gemini"] = Field(
        default="gemini",
        description="Default LLM provider",
    )
    LLM_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="LLM model name from env",
    )
    LLM_TEMPERATURE: float = Field(
        validation_alias=AliasChoices("DEFAULT_LLM_TEMPERATURE", "LLM_TEMPERATURE"),
        description="LLM temperature",
        ge=0.0,
        le=2.0,
    )
    LLM_MAX_TOKENS: int = Field(
        default=2000,
        description="LLM max tokens",
        ge=1,
    )

    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Embedding model to use",
    )
    EMBEDDING_DIMENSIONS: int = Field(
        default=1536,
        description="Embedding dimensions",
        ge=1,
    )

    RATE_LIMIT_DEFAULT: str = Field(default="1000 per day,200 per hour")
    RATE_LIMIT_CHAT: str = Field(default="100 per minute")
    RATE_LIMIT_CHAT_STREAM: str = Field(default="100 per minute")
    RATE_LIMIT_MESSAGES: str = Field(default="200 per minute")
    RATE_LIMIT_LOGIN: str = Field(default="100 per minute")

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        description="Logging level",
    )
    LOG_FORMAT: str = Field(
        description="Log format (json or text)",
    )

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @field_validator("REFRESH_TOKEN_EXPIRE_DAYS")
    @classmethod
    def validate_refresh_token_expiry(cls, v: int) -> int:
        if v != 30:
            raise ValueError("Refresh token expiration MUST be 30 days")
        return v

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def database_url_sync(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")

    @property
    def database_url_async(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        """Legacy property name kept for backwards compatibility with existing code."""
        return self.cors_origins_list

    @property
    def RATE_LIMIT_ENDPOINTS(self) -> dict:
        """Map named endpoints to their rate limit strings.

        Returns a dict similar to the previous config shape used by the app,
        where each value is a tuple and the first element is the rate string.
        """
        return {
            "root": (self.RATE_LIMIT_DEFAULT,),
            "health": (self.RATE_LIMIT_DEFAULT,),
            "chat": (self.RATE_LIMIT_CHAT,),
            "chat_stream": (self.RATE_LIMIT_CHAT_STREAM,),
            "messages": (self.RATE_LIMIT_MESSAGES,),
            "login": (self.RATE_LIMIT_LOGIN,),
        }

    @property
    def API_V1_STR(self) -> str:
        """Backward-compatible name for API prefix used elsewhere in the codebase."""
        return getattr(self, "API_V1_PREFIX")

    @property
    def DESCRIPTION(self) -> str:
        """Simple description field kept for backward compatibility."""
        return getattr(self, "APP_NAME")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Backwards compatibility: expose common legacy names on the Settings class
# so existing code that imports `Settings` (the class) and uses e.g. `Settings.SECRET_KEY`
# will continue to work. We copy values from the instantiated `settings` object.
legacy_aliases = {
    "PROJECT_NAME": settings.APP_NAME,
    "API_V1_STR": settings.API_V1_PREFIX,
    "DESCRIPTION": settings.APP_NAME,
    "SECRET_KEY": settings.JWT_SECRET_KEY,
    "ALGORITHM": settings.JWT_ALGORITHM,
}

for k, v in legacy_aliases.items():
    setattr(Settings, k, v)

# Also set the common legacy names on the instantiated settings object so
# code that accesses `settings.ALLOWED_ORIGINS` or `settings.SECRET_KEY`
# will work at runtime.
instance_aliases = {
    "API_V1_STR": settings.API_V1_PREFIX,
    "DESCRIPTION": settings.APP_NAME,
    "SECRET_KEY": settings.JWT_SECRET_KEY,
    "ALGORITHM": settings.JWT_ALGORITHM,
    "ALLOWED_ORIGINS": settings.cors_origins_list,
}

for k, v in instance_aliases.items():
    try:
        setattr(settings, k, v)
    except Exception:
        # Be defensive during app startup; don't crash on attribute set
        pass