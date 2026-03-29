"""
Configuration — load from environment variables / .env file
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ─────────────────────────────────────────────
    APP_SECRET_KEY: str = "change-me-in-production"
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_COOLDOWN_MINUTES: int = 15

    # ── Active Directory ────────────────────────────────
    AD_SERVER: str = "ldap://your-dc.company.com"
    AD_DOMAIN: str = "company.com"
    AD_BIND_USER: str = "CN=svc-account,OU=ServiceAccounts,DC=company,DC=com"
    AD_BIND_PASSWORD: str = "your-service-account-password"
    AD_BASE_DN: str = "DC=company,DC=com"

    # ── Microsoft Graph API ─────────────────────────────
    GRAPH_TENANT_ID: str = ""
    GRAPH_CLIENT_ID: str = ""
    GRAPH_CLIENT_SECRET: str = ""

    # ── Twilio (SMS) ────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # ── WhatsApp ────────────────────────────────────────
    WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # ── Email (SendGrid - optional) ─────────────────────
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@company.com"
    EMAIL_FROM_NAME: str = "IT Helpdesk"

    # ── Gmail SMTP (NEW 🔥) ─────────────────────────────
    EMAIL_USER: str = ""
    EMAIL_PASS: str = ""
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    # ── Database ────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./ad_unlock.db"

    # ── Risk Engine ─────────────────────────────────────
    ENABLE_IP_CHECK: bool = True
    HIGH_RISK_UNLOCK_REQUIRES_MANAGER: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"   # 🔥 IMPORTANT: prevents crash for extra env vars


# Global settings instance
settings = Settings()