import os
import yaml
from typing import List, Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "FBref Scraper"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Scraper settings
    REQUEST_DELAY_MIN: int = 5
    REQUEST_DELAY_MAX: int = 10
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 1.5
    TIMEOUT: int = 30
    SCRAPER_HEADLESS: bool = True
    
    # Selenium settings
    SELENIUM_WINDOW_SIZE: str = "1920,1080"
    SELENIUM_IMPLICIT_WAIT: int = 10
    SELENIUM_PAGE_LOAD_TIMEOUT: int = 30
    
    # Export settings
    DEFAULT_FORMAT: str = "xlsx"
    MAX_FILE_SIZE_MB: int = 50
    KEEP_FILES_HOURS: int = 24
    
    # Security settings
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour
    ENABLE_PROXY: bool = False
    
    class Config:
        env_file = ".env"

def load_settings() -> Settings:
    """Load settings from YAML file if exists, otherwise use defaults"""
    config_path = os.getenv('CONFIG_PATH', 'config/settings.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return Settings(**config_data)
    return Settings()

settings = load_settings()