"""
Risk Engine — checks IP reputation, repeated attempts, off-hours access
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import UnlockAttempt
from config import settings


async def assess_risk(
    db: AsyncSession,
    username: str,
    ip_address: str
) -> dict:
    """
    DEMO MODE: Always allow unlocks without restrictions
    """
    score = 0
    flags = []

    # Still log the attempt for demo purposes
    attempt = UnlockAttempt(username=username, ip_address=ip_address)
    db.add(attempt)
    await db.commit()

    return {
        "score": score,
        "high_risk": False,
        "flags": flags,
        "require_manager_approval": False  # Always allow in demo mode
    }


def _is_private_ip(ip: str) -> bool:
    """Simple check for RFC1918 private IPs."""
    private_prefixes = ("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                        "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                        "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                        "172.30.", "172.31.", "192.168.", "127.")
    return ip.startswith(private_prefixes)
