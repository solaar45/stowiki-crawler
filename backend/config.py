"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Flask settings
    flask_env: str = "production"
    flask_debug: bool = False

    # API settings
    host: str = "0.0.0.0"
    port: int = 5000

    # Scraper settings
    base_url: str = "https://stowiki.net"
    max_concurrent_requests: int = 10
    request_delay: float = 0.2
    request_timeout: int = 30
    max_retries: int = 3

    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    cache_dir: str = "cache"

    # Storage settings
    storage_type: str = "json"
    database_url: Optional[str] = "sqlite:///ships.db"

    # Logging
    log_level: str = "INFO"
    
    # Auto-refresh settings
    auto_refresh_enabled: bool = True
    auto_refresh_max_age_hours: int = 24  # Refresh if older than 24h

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()