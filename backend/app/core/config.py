from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Literal
# from dotenv import 


class Settings(BaseSettings):

    APP_NAME: str = Field(...)
    APP_VERSION: str = Field(...)
    DEBUG: bool = Field(...)
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(...)

    # API
    API_V1_PREFIX: str = Field(...)
    CORS_ORIGINS: list[str] = Field(...)  # Vite dev server

    # Database
    DATABASE_URL: str = Field(...)

    # Redis
    REDIS_URL: str = Field(...)

    # JWT Auth
    JWT_SECRET_KEY: str = Field(...)
    JWT_ALGORITHM: str = Field(...)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(...)  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(...)

    # OTP
    OTP_EXPIRE_MINUTES: int = Field(...)
    OTP_LENGTH: int = Field(...)

    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str = Field(...)
    EVOLUTION_INSTANCE: str = Field(...)
    EVOLUTION_API_KEY: str = Field(...)

    # SMS Fallback (Termii)
    TERMII_API_KEY: str = Field(...)
    TERMII_SENDER_ID: str = Field(...)

    # S3 / Object Storage (for receipt images)
    S3_ENDPOINT: str = Field(...)
    S3_ACCESS_KEY: str = Field(...)
    S3_SECRET_KEY: str = Field(...)
    S3_BUCKET: str = Field(...)

    # AI / Gemini
    GEMINI_API_KEY: str = Field(...)
    AI_MODEL: str = Field(...)  # Fast and cheap, good for parsing

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
