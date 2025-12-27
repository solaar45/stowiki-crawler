"""Configuration management using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Flask Configuration
    flask_env: str = "production"
    flask_debug: bool = False
    
    # Scraper Configuration
    base_url: str = "https://stowiki.net"  # Updated from sto.fandom.com
    max_concurrent_requests: int = 10  # Increased from 5 for faster scraping
    request_delay: float = 0.2  # Reduced from 0.5 for faster scraping
    request_timeout: int = 30
    max_retries: int = 3
    
    # Cache Configuration
    enable_cache: bool = True
    cache_ttl: int = 3600  # Cache for 1 hour (in seconds)
    cache_dir: str = "cache"
    
    # Storage Configuration
    storage_type: str = "json"  # "json" or "database"
    database_url: str = "sqlite:///ships.db"  # Can be PostgreSQL, MySQL, etc.
    
    # Logging
    log_level: str = "INFO"
    
    # API Configuration
    host: str = "0.0.0.0"
    port: int = 5000


# Global settings instance
settings = Settings()