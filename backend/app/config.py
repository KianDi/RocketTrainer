"""
Configuration settings for RocketTrainer application.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "RocketTrainer"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # External APIs
    ballchasing_api_key: Optional[str] = None
    steam_api_key: Optional[str] = None
    epic_client_id: Optional[str] = None
    epic_client_secret: Optional[str] = None
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # File uploads
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    upload_dir: str = "/tmp/uploads"
    
    # ML Models
    ml_model_dir: str = "/app/ml/models"
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Fix pydantic namespace warning
        protected_namespaces = ('settings_',)


# Global settings instance
settings = Settings()
