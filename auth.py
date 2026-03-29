"""
Auth Router — POST /api/auth/request-otp
Step 1: User enters username → OTP is sent
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Literal

from database import get_db
from otp_service import generate_otp, create_otp_record, log_event
from notification_service import send_otp_notification
from ad_service import check_account_status, create_password_reset_token, update_password

router = APIRouter()


class OTPRequest(BaseModel):
    username: str
    preferred_channel: Literal["sms", "whatsapp", "email"] = "sms"


class OTPResponse(BaseModel):
    success: bool
    message: str
    channel: str = None
    masked_contact: str = None


class PasswordResetVerifyRequest(BaseModel):
    username: str
    otp: str


class PasswordResetVerifyResponse(BaseModel):
    success: bool
    message: str
    reset_token: str | None = None


class PasswordUpdateRequest(BaseModel):
    username: str
    reset_token: str
    new_password: str
    confirm_password: str


class PasswordUpdateResponse(BaseModel):
    success: bool
    message: str


@router.post("/request-otp", response_model=OTPResponse)
async def request_otp(
    body: OTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    username = body.username.strip().lower()
    ip = request.client.host

    # Step 1: Check if account exists and is actually locked
    account = await check_account_status(username)

    if not account.get("found"):
        # Return vague message to prevent user enumeration
        raise HTTPException(status_code=404, detail="Username not found or not eligible for self-service unlock.")

    if not account.get("locked"):
        raise HTTPException(status_code=400, detail="Account is not currently locked. Try logging in normally.")

    # Step 2: Generate OTP
    otp = generate_otp()

    # Step 3: Send via preferred channel with fallback
    result = await send_otp_notification(
        otp=otp,
        mobile=account.get("mobile"),
        email=account.get("email"),
        username=username,
        preferred_channel=body.preferred_channel
    )

    if not result["success"]:
        await log_event(db, username, "OTP_SEND_FAILED", ip_address=ip,
                        detail="All notification channels failed")
        raise HTTPException(status_code=503, detail="Could not deliver OTP. Please contact IT helpdesk.")

    # Step 4: Store hashed OTP
    await create_otp_record(db, username, otp, result["channel"])
    await log_event(db, username, "OTP_SENT", channel=result["channel"],
                    ip_address=ip, detail=f"OTP sent via {result['channel']}")

    # Mask contact for response
    contact = account.get("mobile") or account.get("email") or ""
    masked = _mask_contact(contact)

    return OTPResponse(
        success=True,
        message=f"OTP sent successfully via {result['channel']}.",
        channel=result["channel"],
        masked_contact=masked
    )


@router.post("/request-password-reset-otp", response_model=OTPResponse)
async def request_password_reset_otp(
    body: OTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    username = body.username.strip().lower()
    ip = request.client.host

    account = await check_account_status(username)
    if not account.get("found"):
        raise HTTPException(status_code=404, detail="Username not found.")

    otp = generate_otp()
    result = await send_otp_notification(
        otp=otp,
        mobile=account.get("mobile"),
        email=account.get("email"),
        username=username,
        preferred_channel=body.preferred_channel
    )

    if not result["success"]:
        await log_event(db, username, "PASSWORD_RESET_OTP_SEND_FAILED", ip_address=ip,
                        detail="All notification channels failed")
        raise HTTPException(status_code=503, detail="Could not deliver OTP. Please contact IT helpdesk.")

    await create_otp_record(db, username, otp, result["channel"])
    await log_event(db, username, "PASSWORD_RESET_OTP_SENT", channel=result["channel"],
                    ip_address=ip, detail=f"Password reset OTP sent via {result['channel']}")

    contact = account.get("mobile") or account.get("email") or ""
    masked = _mask_contact(contact)

    return OTPResponse(
        success=True,
        message=f"OTP sent successfully via {result['channel']}.",
        channel=result["channel"],
        masked_contact=masked
    )


@router.post("/verify-password-reset-otp", response_model=PasswordResetVerifyResponse)
async def verify_password_reset_otp(
    body: PasswordResetVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    from otp_service import validate_otp

    username = body.username.strip().lower()
    ip = request.client.host

    account = await check_account_status(username)
    if not account.get("found"):
        raise HTTPException(status_code=404, detail="Username not found.")

    otp_result = await validate_otp(db, username, body.otp, ip_address=ip)
    if not otp_result["success"]:
        await log_event(db, username, "PASSWORD_RESET_OTP_FAILED", ip_address=ip,
                        detail=otp_result["reason"])
        raise HTTPException(status_code=401, detail=otp_result["reason"])

    reset_token = await create_password_reset_token(username)
    await log_event(db, username, "PASSWORD_RESET_OTP_VERIFIED",
                    channel=otp_result.get("channel"), ip_address=ip,
                    detail="Password reset OTP verified")

    return PasswordResetVerifyResponse(
        success=True,
        message="OTP verified successfully. You can now update your password.",
        reset_token=reset_token
    )


@router.post("/update-password", response_model=PasswordUpdateResponse)
async def update_account_password(
    body: PasswordUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    username = body.username.strip().lower()
    ip = request.client.host

    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    account = await check_account_status(username)
    if not account.get("found"):
        raise HTTPException(status_code=404, detail="Username not found.")

    updated = await update_password(username, body.new_password, body.reset_token)
    if not updated:
        await log_event(db, username, "PASSWORD_UPDATE_FAILED", ip_address=ip,
                        detail="Invalid or expired password reset token")
        raise HTTPException(
            status_code=401,
            detail="Password reset session is invalid or expired. Please verify OTP again."
        )

    await log_event(db, username, "PASSWORD_UPDATED", ip_address=ip,
                    detail="Password updated in demo mode")
    return PasswordUpdateResponse(
        success=True,
        message="Password updated successfully. You can now sign in with the new password."
    )


def _mask_contact(contact: str) -> str:
    if "@" in contact:
        parts = contact.split("@")
        return parts[0][:2] + "****@" + parts[1]
    if len(contact) >= 4:
        return "****" + contact[-4:]
    return "****"
