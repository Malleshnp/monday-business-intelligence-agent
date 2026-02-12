"""Application configuration and settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Monday.com API Configuration
    MONDAY_API_TOKEN: Optional[str] = None
    MONDAY_API_URL: str = "https://api.monday.com/v2"
    
    # OpenAI Configuration (for query understanding)
    OPENAI_API_KEY: Optional[str] = None
    
    # Application Settings
    APP_NAME: str = "Monday.com BI Agent"
    DEBUG: bool = False
    CORS_ORIGINS: list = ["*"]
    
    # Board IDs (preferred) or Board Names
    DEALS_BOARD_ID: Optional[str] = None
    WORK_ORDERS_BOARD_ID: Optional[str] = None
    
    # Fallback to board names if IDs not provided
    DEALS_BOARD_NAME: str = "Deals"
    WORK_ORDERS_BOARD_NAME: str = "Work Orders"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()