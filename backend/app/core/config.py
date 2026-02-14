"""Application configuration using Pydantic Settings."""

from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = Field(default="ALICE", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    # Database
    postgres_host: str = Field(default="db", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="alice", alias="POSTGRES_DB")
    postgres_user: str = Field(default="alice", alias="POSTGRES_USER")
    postgres_password: str = Field(default="alice_dev_123", alias="POSTGRES_PASSWORD")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # Redis (points to FalkorDB, which is Redis-compatible)
    redis_host: str = Field(default="falkordb", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    # FalkorDB / Graphiti
    falkordb_host: str = Field(default="falkordb", alias="FALKORDB_HOST")
    falkordb_port: int = Field(default=6379, alias="FALKORDB_PORT")
    graphiti_enabled: bool = Field(default=True, alias="GRAPHITI_ENABLED")

    # JWT
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_access_token_expire_minutes: int = Field(default=15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_algorithm: str = Field(default="HS256")

    # AI
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # CORS
    cors_origins: List[str] | str = Field(
        default=["http://localhost:8081", "http://localhost:19006"],
        alias="CORS_ORIGINS"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from JSON string or list."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def async_database_url(self) -> str:
        """Get async database URL for SQLAlchemy."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Get sync database URL for Alembic."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_connection_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/0"



# Global settings instance
settings = Settings()
