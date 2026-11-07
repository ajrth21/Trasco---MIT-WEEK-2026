import os
import json
from typing import List, Union
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    class SettingsBase(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
except ImportError:
    class SettingsBase(BaseModel):
        pass


class Settings(SettingsBase):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "TRASCO AI Cybersecurity API")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "trasco-super-secret-security-key-change-in-production-2026")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trasco.db")

    # AI API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # CORS
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
