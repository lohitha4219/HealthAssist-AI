from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "HealthAssist AI"
    APP_ENV: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/healthcare_assistant"
    )

    JWT_SECRET_KEY: str = "dev-only-insecure-change-me-before-production-32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    EXPOSE_DEV_RESET_TOKEN: bool = False

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    UPLOAD_DIR: str = "storage/reports"
    MAX_UPLOAD_SIZE_MB: int = 10

    # AI Provider: auto | gemini | openai_compatible | llamacpp | ollama
    AI_PROVIDER: str = "auto"
    AI_TIMEOUT_SECONDS: int = 90
    AI_MAX_CONTEXT_MESSAGES: int = 14

    # Google Gemini API (Recommended Cloud Provider - official google-genai SDK)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # llama.cpp local server
    LLAMACPP_BASE_URL: str = "http://127.0.0.1:8080"
    LLAMACPP_MODEL: str = "qwen2.5-1.5b-instruct-q4_k_m"

    # Ollama local server
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"

    # Optional generic OpenAI-compatible endpoint (OpenAI, Groq, DeepSeek, etc.)
    AI_BASE_URL: Optional[str] = None
    AI_API_KEY: Optional[str] = None
    AI_MODEL: Optional[str] = None

    # Optional SMTP email delivery
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: str = "HealthAssist AI"
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # Optional public support details (never invented if unset)
    SUPPORT_EMAIL: str = "nslohitha2924@gmail.com"
    SUPPORT_PHONE: Optional[str] = None
    SUPPORT_ADDRESS: Optional[str] = None

    # Secure operational keys for doctor onboarding & hospital data maintenance (no Admin UI)
    DOCTOR_ONBOARDING_KEY: Optional[str] = None
    HOSPITAL_MAINTENANCE_KEY: Optional[str] = None

    @field_validator("GEMINI_MODEL")
    @classmethod
    def normalize_gemini_model(cls, value: Optional[str]) -> str:
        val = (value or "").strip().lower()
        if not val or val in ("gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5", "gemini-2.0"):
            return "gemini-3.5-flash"
        return val

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        raw = self.CORS_ORIGINS.strip()
        if not raw:
            return []
        if raw.startswith("["):
            import json

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(o).strip() for o in parsed if str(o).strip()]
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute():
            p = BASE_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p.resolve()

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def smtp_configured(self) -> bool:
        user = self.SMTP_USERNAME or self.SMTP_USER
        return bool(self.SMTP_HOST and (self.SMTP_FROM_EMAIL or user))


@lru_cache
def get_settings() -> Settings:
    return Settings()
