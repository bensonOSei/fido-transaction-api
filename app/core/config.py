from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Fido Transaction API"
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # Security
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Email
    EMAIL_SMTP_HOST: str
    EMAIL_SMTP_PORT: int
    EMAIL_SMTP_USER: str
    EMAIL_SMTP_PASSWORD: str
    EMAIL_FROM_EMAIL: str
    EMAIL_ENABLE_NOTIFICATIONS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    load_dotenv(override=True)
    return Settings()

settings = get_settings()