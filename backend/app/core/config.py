from functools import lru_cache
from typing import List, Optional

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
    cors_origin_regex: Optional[str] = Field(
        default=r"^https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
        description="Regex for additional allowed CORS origins such as local network devices",
    )
    secret_key: str = Field(
        default="development-insecure-secret-key",
        description="Secret key used to sign access tokens",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=10080,
        description="Access token lifetime in minutes",
    )
    minimax_api_key: str = Field(
        default="",
        description="MiniMax API key for demo track generation",
    )
    minimax_api_base: str = Field(
        default="https://api.minimax.io/v1",
        description="MiniMax API base URL",
    )
    minimax_music_model: str = Field(
        default="music-2.6",
        description="MiniMax music generation model name",
    )
    minimax_request_timeout: int = Field(
        default=180,
        description="Timeout in seconds for MiniMax API requests",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance to avoid repeated environment parsing."""
    return Settings()
