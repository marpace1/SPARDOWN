from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional






class Settings(BaseSettings):
    
    ADMIN_API_KEY: str = "super-secret-admin-key"
    # Project Settings
    APP_NAME: str = "SPARDOWN"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Storage Settings
    BASE_DOWNLOAD_PATH: Path = Path("./downloads")
    METADATA_CACHE_PATH: Path = Path("./cache/metadata")
    
    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./spardown.db"
    
    # Download Engine Settings
    MAX_CONCURRENT_DOWNLOADS: int = 3
    DOWNLOAD_RETRIES: int = 3
    DEFAULT_AUDIO_FORMAT: str = "mp3"
    AUDIO_QUALITY: str = "best"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    
    )

settings = Settings()
