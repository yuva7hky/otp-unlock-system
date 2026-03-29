"""
OTP Service — generate, hash, verify, expire
"""
import secrets
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import OTPRecord, AuditLog
from config import settings


def generate_otp(length: int = 6) -> str:
    """Cryptographically secure 6-digit OTP."""
    return str(secrets.randbelow(10 ** length)).zfill(length)


def hash_otp(otp: str) -> str:
    return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()


def verify_otp_hash(otp: str, hashed: str) -> bool:
    return bcrypt.checkpw(otp.encode(), hashed.encode())


async def create_otp_record(
    db: AsyncSession,
    username: str,
    otp: str,
    channel: str
) -> OTPRecord:
    # Invalidate any existing OTP for this user
    result = await db.execute(
        select(OTPRecord).where(
            OTPRecord.username == username,
            OTPRecord.verified == False
        )
    )
    for old in result.scalars().all():
        await db.delete(old)

    record = OTPRecord(
        username=username,
        otp_hash=hash_otp(otp),
        channel=channel,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def validate_otp(
    db: AsyncSession,
    username: str,
    otp: str,
    ip_address: str = None
) -> dict:
    result = await db.execute(
        select(OTPRecord).where(
            OTPRecord.username == username,
            OTPRecord.verified == False
        ).order_by(OTPRecord.created_at.desc())
    )
    record = result.scalar_one_or_none()

    if not record:
        return {"success": False, "reason": "No active OTP found. Please request a new one."}

    if datetime.utcnow() > record.expires_at:
        await db.delete(record)
        await db.commit()
        return {"success": False, "reason": "OTP has expired. Please request a new one."}

    if record.attempts >= settings.OTP_MAX_ATTEMPTS:
        return {"success": False, "reason": "Too many incorrect attempts. Please request a new OTP."}

    if not verify_otp_hash(otp, record.otp_hash):
        record.attempts += 1
        await db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - record.attempts
        return {"success": False, "reason": f"Incorrect OTP. {remaining} attempt(s) remaining."}

    # Mark as verified
    record.verified = True
    await db.commit()

    # Write audit log
    log = AuditLog(
        username=username,
        event="OTP_VERIFIED",
        channel=record.channel,
        ip_address=ip_address,
        detail="OTP successfully verified"
    )
    db.add(log)
    await db.commit()

    return {"success": True, "channel": record.channel}


async def log_event(
    db: AsyncSession,
    username: str,
    event: str,
    channel: str = None,
    ip_address: str = None,
    detail: str = None
):
    entry = AuditLog(
        username=username,
        event=event,
        channel=channel,
        ip_address=ip_address,
        detail=detail
    )
    db.add(entry)
    await db.commit()
