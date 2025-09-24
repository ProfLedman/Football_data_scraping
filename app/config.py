import os
import yaml
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "FBref Scraper"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = False

    # Scraper settings
    SCRAPER_REQUEST_DELAY_MIN: int = 5
    SCRAPER_REQUEST_DELAY_MAX: int = 10
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_BACKOFF_FACTOR: float = 1.5
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_HEADLESS: bool = True

    # Selenium settings
    SELENIUM_WINDOW_SIZE: str = "1920,1080"
    SELENIUM_IMPLICIT_WAIT: int = 10
    SELENIUM_PAGE_LOAD_TIMEOUT: int = 30

    # Export settings
    EXPORT_DEFAULT_FORMAT: str = "xlsx"
    EXPORT_MAX_FILE_SIZE_MB: int = 50
    EXPORT_KEEP_FILES_HOURS: int = 24
    EXPORT_OUTPUT_DIR: str = "data/exports"

    # Security settings
    SECURITY_RATE_LIMIT_REQUESTS: int = 100
    SECURITY_RATE_LIMIT_PERIOD: int = 3600

    class Config:
        env_file = ".env"
        extra = "forbid"

def load_settings() -> Settings:
    """Load settings from YAML file if exists, otherwise use defaults"""
    config_path = os.getenv('CONFIG_PATH', 'config/settings.yaml')
    
    print(f"Looking for config at: {config_path}")
    print(f"Config exists: {os.path.exists(config_path)}")
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        print("Original YAML structure:")
        print(config_data)
        
        # Flatten the nested YAML structure
        flattened_config = {}
        for section, values in config_data.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    field_name = f"{section.upper()}_{key.upper()}"
                    flattened_config[field_name] = value
                    print(f"Mapping: {section}.{key} -> {field_name} = {value}")
            else:
                field_name = section.upper()
                flattened_config[field_name] = values
                print(f"Mapping: {section} -> {field_name} = {values}")
        
        print("Flattened config:")
        print(flattened_config)
        
        # Check if all required fields are present
        expected_fields = [name for name in Settings.__annotations__]
        print("Expected fields in Settings:")
        print(expected_fields)
        
        missing_fields = set(expected_fields) - set(flattened_config.keys())
        extra_fields = set(flattened_config.keys()) - set(expected_fields)
        
        print(f"Missing fields: {missing_fields}")
        print(f"Extra fields: {extra_fields}")
        
        return Settings(**flattened_config)
    
    print("Using default settings (no YAML file found)")
    return Settings()

settings = load_settings()