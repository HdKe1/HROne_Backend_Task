"""
Application configuration settings.
Handles environment variables and application-wide settings.
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = Field(default="Ecommerce API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_description: str = Field(
        default="A FastAPI-based ecommerce application similar to Flipkart/Amazon",
        env="APP_DESCRIPTION"
    )
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = Field(default="Ecommerce API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_description: str = Field(
        default="A FastAPI-based ecommerce application similar to Flipkart/Amazon",
        env="APP_DESCRIPTION"
    )
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    
    # Database settings
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    database_name: str = Field(default="ecommerce_db", env="DATABASE_NAME")
    
    # MongoDB connection settings
    server_selection_timeout_ms: int = Field(default=30000, env="MONGODB_SERVER_SELECTION_TIMEOUT_MS")
    connect_timeout_ms: int = Field(default=30000, env="MONGODB_CONNECT_TIMEOUT_MS")
    socket_timeout_ms: int = Field(default=30000, env="MONGODB_SOCKET_TIMEOUT_MS")
    max_pool_size: int = Field(default=10, env="MONGODB_MAX_POOL_SIZE")
    min_pool_size: int = Field(default=1, env="MONGODB_MIN_POOL_SIZE")
    retry_writes: bool = Field(default=True, env="MONGODB_RETRY_WRITES")
    direct_connection: bool = Field(default=False, env="MONGODB_DIRECT_CONNECTION")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    
    # Pagination defaults
    default_page_size: int = Field(default=10, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    # Business logic settings
    max_order_items: int = Field(default=50, env="MAX_ORDER_ITEMS")
    max_item_quantity: int = Field(default=100, env="MAX_ITEM_QUANTITY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings