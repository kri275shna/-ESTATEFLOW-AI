import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")
    
    PROJECT_NAME: str = "EstateFlow AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    # Default to SQLite for zero-setup local dev/test, PostgreSQL for production
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./estateflow.db")
    
    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "estateflow-super-secret-jwt-key-2026-ahmedabad-core-build")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # LLM Settings (optional API key, deterministic fallback when absent)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    USE_DETERMINISTIC_FALLBACK: bool = True
    
    # Client Context
    DEVELOPER_NAME: str = "Company A"
    LOCATION: str = "Ahmedabad, Gujarat"


settings = Settings()
