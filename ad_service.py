"""
Active Directory Service - DEMO MODE
Fake in-memory user database for demonstration purposes
"""
import logging
import secrets
from datetime import datetime, timedelta

from config import settings

logger = logging.getLogger(__name__)
PASSWORD_RESET_TOKEN_TTL_MINUTES = 10
PASSWORD_RESET_TOKENS = {}

# Demo user database
DEMO_USERS = {
    "john": {
        "username": "john",
        "locked": True,
        "email": "ajayarun177@gmail.com",
        "mobile": "+911234567890",
        "display_name": "John Doe",
        "password": "Welcome@123"
    },
    "yuva": {
        "username": "yuva",
        "locked": False,
        "email": "your-email@gmail.com",
        "mobile": "+911234567891",
        "display_name": "Yuva Kumar",
        "password": "Welcome@123"
    },
    "rajasekar": {
        "username": "rajasekar",
        "locked": True,
        "email": "rajasekar.r@prodapt.com",
        "mobile": "+918072210473",
        "display_name": "Rajasekar",
        "password": "Welcome@123"
    }
}


async def check_account_status(username: str) -> dict:
    """Check account status from demo user database."""
    user = DEMO_USERS.get(username.lower())
    if not user:
        return {"found": False, "locked": False}

    return {
        "found": True,
        "locked": user["locked"],
        "display_name": user["display_name"],
        "email": user["email"],
        "mobile": user["mobile"]
    }


async def unlock_account(username: str, account_info: dict = None) -> bool:
    """Unlock account in demo user database."""
    user = DEMO_USERS.get(username.lower())
    if not user:
        logger.warning(f"User {username} not found in demo database")
        return False

    user["locked"] = False
    logger.info(f"Account {username} unlocked in demo mode")
    return True


async def create_password_reset_token(username: str) -> str | None:
    """Create a short-lived reset token after OTP verification."""
    user = DEMO_USERS.get(username.lower())
    if not user:
        return None

    token = secrets.token_urlsafe(24)
    PASSWORD_RESET_TOKENS[username.lower()] = {
        "token": token,
        "expires_at": datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_TOKEN_TTL_MINUTES)
    }
    return token


async def update_password(username: str, new_password: str, reset_token: str) -> bool:
    """Update the demo user's password if the reset token is valid."""
    user = DEMO_USERS.get(username.lower())
    if not user:
        logger.warning(f"Password reset failed. User {username} not found in demo database")
        return False

    session = PASSWORD_RESET_TOKENS.get(username.lower())
    if not session:
        return False

    if datetime.utcnow() > session["expires_at"] or session["token"] != reset_token:
        PASSWORD_RESET_TOKENS.pop(username.lower(), None)
        return False

    user["password"] = new_password
    PASSWORD_RESET_TOKENS.pop(username.lower(), None)
    logger.info(f"Password updated for {username} in demo mode")
    return True
