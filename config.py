"""
Configuration — load from environment variables / .env file
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────
    APP_SECRET_KEY: str = "change-me"
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_COOLDOWN_MINUTES: int = 15

    # ── Email (Gmail SMTP) ────────────────────────────
    EMAIL_USER: str = ""
    EMAIL_PASS: str = ""

    # ── Database ──────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./ad_unlock.db"

    # ── Risk Engine ───────────────────────────────────
    ENABLE_IP_CHECK: bool = False
    HIGH_RISK_UNLOCK_REQUIRES_MANAGER: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"   # 🔥 Prevent crash from unknown env vars


# Create settings instance
settings = Settings()