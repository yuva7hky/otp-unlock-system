"""
Notification Service — SMS, WhatsApp, Email (Gmail SMTP)
"""

import logging
import smtplib
from email.mime.text import MIMEText
from config import settings

logger = logging.getLogger(__name__)

OTP_MESSAGE_TEMPLATE = (
    "Your IT account unlock OTP is: {otp}\n"
    "Valid for {minutes} minutes. Do not share this code with anyone."
)

# ── Email via Gmail SMTP (FIXED 🔥) ───────────────────────────────────────────
async def send_email_gmail(email: str, username: str, otp: str) -> bool:
    try:
        # Check config
        if not settings.EMAIL_USER or not settings.EMAIL_PASS:
            print("❌ Email config missing in ENV")
            return False

        subject = "Your Account Unlock OTP"
        body = f"""
Hi {username},

Your OTP is: {otp}

Valid for {settings.OTP_EXPIRE_MINUTES} minutes.
Do not share this code.
"""

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_USER
        msg["To"] = email

        # ✅ Gmail SMTP config
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        server.send_message(msg)
        server.quit()

        print("✅ EMAIL SENT SUCCESSFULLY")
        logger.info(f"Email OTP sent to {email}")

        return True

    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        logger.error(f"Gmail send failed: {e}")
        return False


# ── Unified Email Handler ─────────────────────────────────────────────────────
async def send_email(email: str, username: str, otp: str) -> bool:
    return await send_email_gmail(email, username, otp)


# ── Dispatcher ───────────────────────────────────────────────────────────────
async def send_otp_notification(
    otp: str,
    mobile: str = None,
    email: str = None,
    username: str = None,
    preferred_channel: str = "email"
) -> dict:

    # 🔥 FORCE EMAIL ONLY (for demo)
    if email:
        if await send_email(email, username or "User", otp):
            return {"success": True, "channel": "email"}

    # ❌ No fallback → show failure
    print("\n❌ OTP DELIVERY FAILED — EMAIL NOT SENT\n")

    return {"success": False, "channel": "none"}