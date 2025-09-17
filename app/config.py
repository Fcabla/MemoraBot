"""Application configuration management."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = Field(default="development")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")

    # LLM Configuration
    LLM_PROVIDER: str = Field(default="openai")
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)

    # File Storage
    DATA_DIR: str = Field(default="./data")
    MAX_FILE_SIZE_MB: int = Field(default=10)
    ALLOWED_FILE_TYPES: str = Field(default=".txt,.md,.json,.yaml")

    # Security
    SECRET_KEY: str = Field(default="change-this-secret-key")
    CORS_ORIGINS: str = Field(default="http://localhost:8000")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def allowed_file_extensions(self) -> set[str]:
        """Parse allowed file types into a set."""
        return set(self.ALLOWED_FILE_TYPES.split(","))

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        if ',' in self.CORS_ORIGINS:
            return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
        return [self.CORS_ORIGINS]


# Create global settings instance
settings = Settings()