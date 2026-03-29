"""
Notification Service — SMS (Twilio), WhatsApp, Email (SendGrid / Gmail)
Falls back to next channel if one fails.
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

# ── SMS via Twilio ────────────────────────────────────────────────────────────
async def send_sms(mobile: str, otp: str) -> bool:
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=OTP_MESSAGE_TEMPLATE.format(otp=otp, minutes=settings.OTP_EXPIRE_MINUTES),
            from_=settings.TWILIO_FROM_NUMBER,
            to=mobile
        )
        logger.info(f"SMS OTP sent to {mobile[-4:].rjust(len(mobile), '*')}")
        return True
    except Exception as e:
        logger.error(f"SMS send failed: {e}")
        return False


# ── WhatsApp via Twilio ──────────────────────────────────────────────────────
async def send_whatsapp(mobile: str, otp: str) -> bool:
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        wa_to = f"whatsapp:{mobile}"
        client.messages.create(
            body=OTP_MESSAGE_TEMPLATE.format(otp=otp, minutes=settings.OTP_EXPIRE_MINUTES),
            from_=settings.WHATSAPP_FROM,
            to=wa_to
        )
        logger.info(f"WhatsApp OTP sent to {mobile[-4:].rjust(len(mobile), '*')}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
        return False


# ── Email via Gmail SMTP (NEW 🔥) ─────────────────────────────────────────────
async def send_email_gmail(email: str, username: str, otp: str) -> bool:
    try:
        if not settings.EMAIL_USER or not settings.EMAIL_PASS:
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

        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        server.send_message(msg)
        server.quit()

        logger.info(f"Gmail OTP sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Gmail send failed: {e}")
        return False


# ── Email via SendGrid (fallback) ─────────────────────────────────────────────
async def send_email_sendgrid(email: str, username: str, otp: str) -> bool:
    try:
        if not settings.SENDGRID_API_KEY:
            return False

        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        html_body = f"""
        <h2>Account Unlock OTP</h2>
        <p>Hi {username},</p>
        <h1>{otp}</h1>
        <p>Valid for {settings.OTP_EXPIRE_MINUTES} minutes.</p>
        """

        mail = Mail(
            from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
            to_emails=To(email),
            subject="Your Account Unlock OTP",
            html_content=Content("text/html", html_body)
        )

        sg.client.mail.send.post(request_body=mail.get())
        logger.info(f"SendGrid OTP sent to {email}")
        return True

    except Exception as e:
        logger.error(f"SendGrid send failed: {e}")
        return False


# ── Unified Email Handler 🔥 ─────────────────────────────────────────────────
async def send_email(email: str, username: str, otp: str) -> bool:
    # Try Gmail first
    if await send_email_gmail(email, username, otp):
        return True

    # Fallback to SendGrid
    if await send_email_sendgrid(email, username, otp):
        return True

    return False


# ── Dispatcher with fallback ──────────────────────────────────────────────────
async def send_otp_notification(
    otp: str,
    mobile: str = None,
    email: str = None,
    username: str = None,
    preferred_channel: str = "sms"
) -> dict:

    channels = _build_channel_order(preferred_channel)

    for channel in channels:
        if channel == "sms" and mobile:
            if await send_sms(mobile, otp):
                return {"success": True, "channel": "sms"}

        elif channel == "whatsapp" and mobile:
            if await send_whatsapp(mobile, otp):
                return {"success": True, "channel": "whatsapp"}

        elif channel == "email" and email:
            if await send_email(email, username or "User", otp):
                return {"success": True, "channel": "email"}

    # Demo fallback
    print(f"\n=== DEMO MODE OTP ===")
    print(f"Username: {username}")
    print(f"OTP: {otp}")
    print("=====================\n")

    return {"success": True, "channel": "console"}


def _build_channel_order(preferred: str) -> list:
    order = ["sms", "whatsapp", "email"]
    if preferred in order:
        order.insert(0, order.pop(order.index(preferred)))
    return order