"""
Notification Service — Email via SendGrid API (FIXED 🔥)
"""

import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

# ── SendGrid Email ─────────────────────────────────────────────
async def send_email_sendgrid(email: str, username: str, otp: str) -> bool:
    try:
        if not settings.SENDGRID_API_KEY:
            print("❌ SendGrid API key missing")
            return False

        url = "https://api.sendgrid.com/v3/mail/send"

        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        }

        body = {
            "personalizations": [
                {
                    "to": [{"email": email}],
                    "subject": "Your Account Unlock OTP",
                }
            ],
            "from": {
                "email": settings.EMAIL_FROM,
                "name": settings.EMAIL_FROM_NAME,
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": f"""
Hi {username},

Your OTP is: {otp}

Valid for {settings.OTP_EXPIRE_MINUTES} minutes.
Do not share this code with anyone.
""",
                }
            ],
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=body)

        if response.status_code in [200, 202]:
            print("✅ EMAIL SENT VIA SENDGRID")
            return True
        else:
            print("❌ SENDGRID ERROR:", response.text)
            return False

    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        return False


# ── Unified Email Handler ─────────────────────────────────────
async def send_email(email: str, username: str, otp: str) -> bool:
    return await send_email_sendgrid(email, username, otp)


# ── Dispatcher ───────────────────────────────────────────────
async def send_otp_notification(
    otp: str,
    mobile: str = None,
    email: str = None,
    username: str = None,
    preferred_channel: str = "email"
) -> dict:

    if email:
        if await send_email(email, username or "User", otp):
            return {"success": True, "channel": "email"}

    print("\n❌ OTP DELIVERY FAILED — EMAIL NOT SENT\n")
    return {"success": False, "channel": "none"}