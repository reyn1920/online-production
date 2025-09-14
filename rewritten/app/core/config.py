"""Application configuration settings."""

from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
import json


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    ENVIRONMENT: str = "development"
    NODE_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str
    JWT_SECRET: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    TRAE_MASTER_KEY: str

    # Lists that come as JSON arrays from .env
    ALLOWED_HOSTS: List[str] = ["localhost"]
    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("ALLOWED_HOSTS", "CORS_ORIGINS", mode="before")
    @classmethod
    def parse_json_lists(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback to comma-separated parsing
                return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # Dashboard
    DASHBOARD_PORT: int = 8081

    # Database
    DATABASE_PATH: str = "data/trae_master.db"
    DATABASE_URL: str = "sqlite:///./app.db"

    # Payment Configuration
    STRIPE_PUBLIC_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Geocoding
    NOMINATIM_USER_AGENT: str = "TraeApp/1.0"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
