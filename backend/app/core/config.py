from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration pulled from environment variables where available."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="allow")

    app_name: str = "Song Master Web"
    environment: str = Field(default="development", description="Environment name")
    database_url: str = Field(
        default="sqlite:///./backend/data/song_master.db",
        description="SQLAlchemy database URL",
    )
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance to avoid repeated environment parsing."""
    return Settings()
