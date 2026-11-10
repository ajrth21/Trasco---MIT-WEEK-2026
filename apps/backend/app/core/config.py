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
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "trasco-super-secret-security-key-change-in-production-2026")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trasco.db")

    # AI API Keys & Models
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_IMAGE_TIMEOUT_SECONDS: float = float(os.getenv("GEMINI_IMAGE_TIMEOUT_SECONDS", "15.0"))

    # CORS
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()


_INSECURE_DEFAULT_SECRET = "trasco-super-secret-security-key-change-in-production-2026"


def validate_startup_security(current_settings: Settings = None) -> None:
    """Validates runtime security configuration at server startup.

    Enforces that:
    1. Empty or whitespace-only SECRET_KEY is rejected on all modes (both DEBUG=True and DEBUG=False).
    2. SECRET_KEY shorter than 32 characters is rejected on all modes (both DEBUG=True and DEBUG=False).
    3. In explicit DEBUG mode (development/demo), only the known insecure default secret
       is tolerated with a non-fatal warning emitted to sys.stderr for local evaluation.
    4. In non-debug mode (production), the known insecure default secret triggers an immediate hard stop.
    5. A SECRET_KEY meeting minimum length requirements satisfies structural length validation,
       but is not assumed to possess cryptographic entropy unless generated via a CSPRNG.
    6. SECRET_KEY values are never printed to logs, warnings, or exceptions.
    """
    target = current_settings or settings
    secret = target.SECRET_KEY or ""

    # Universal Rule 1: Empty or whitespace-only check across all modes
    if not secret.strip():
        raise SystemExit(
            "[CRITICAL SECURITY BLOCKER] SECRET_KEY is empty or contains only whitespace. "
            "A valid SECRET_KEY must be provided in the environment or .env file."
        )

    # Universal Rule 2: Exception for the known insecure default ONLY in explicit DEBUG mode
    if target.DEBUG and secret == _INSECURE_DEFAULT_SECRET:
        import sys
        sys.stderr.write(
            "[TRASCO SECURITY WARNING] Running in DEVELOPMENT mode with default insecure SECRET_KEY. "
            "This configuration is permitted solely for local demo/hackathon evaluations and is unsafe for production!\n"
        )
        sys.stderr.flush()
        return

    # Universal Rule 3: Rejection of the known insecure default in non-debug / production mode
    if secret == _INSECURE_DEFAULT_SECRET:
        raise SystemExit(
            "[CRITICAL SECURITY BLOCKER] Insecure default SECRET_KEY detected in production mode (DEBUG=False). "
            "You must configure a strong, unique SECRET_KEY in the environment or .env file. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Universal Rule 4: Minimum length check across all modes
    if len(secret) < 32:
        raise SystemExit(
            f"[CRITICAL SECURITY BLOCKER] SECRET_KEY length is insufficient ({len(secret)} chars). "
            "A minimum of 32 characters is required for structural length validation."
        )
