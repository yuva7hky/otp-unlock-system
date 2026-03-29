"""
Unlock Router — POST /api/unlock/verify
Step 2: User submits OTP → account unlocked if valid
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from otp_service import validate_otp, log_event
from ad_service import check_account_status, unlock_account
from risk_engine import assess_risk

router = APIRouter()


class VerifyRequest(BaseModel):
    username: str
    otp: str


class VerifyResponse(BaseModel):
    success: bool
    message: str
    escalated: bool = False


@router.post("/verify", response_model=VerifyResponse)
async def verify_and_unlock(
    body: VerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    username = body.username.strip().lower()
    ip = request.client.host

    # Step 1: Run risk assessment
    risk = await assess_risk(db, username, ip)

    if risk["require_manager_approval"]:
        await log_event(
            db, username, "ESCALATED",
            ip_address=ip,
            detail=f"High risk score {risk['score']}. Flags: {', '.join(risk['flags'])}"
        )
        return VerifyResponse(
            success=False,
            message="Your unlock request has been flagged for security review. "
                    "IT helpdesk has been notified and will contact you shortly.",
            escalated=True
        )

    # Step 2: Validate OTP
    otp_result = await validate_otp(db, username, body.otp, ip_address=ip)
    if not otp_result["success"]:
        await log_event(db, username, "OTP_FAILED", ip_address=ip,
                        detail=otp_result["reason"])
        raise HTTPException(status_code=401, detail=otp_result["reason"])

    # Step 3: Verify account is still locked before unlocking
    account = await check_account_status(username)
    if not account.get("found"):
        raise HTTPException(status_code=404, detail="Account not found.")
    if not account.get("locked"):
        return VerifyResponse(success=True, message="Account is already unlocked. You can log in now.")

    # Step 4: Unlock in Active Directory
    unlocked = await unlock_account(username, account_info=account)

    if unlocked:
        await log_event(
            db, username, "UNLOCK_SUCCESS",
            channel=otp_result.get("channel"),
            ip_address=ip,
            detail=f"Account unlocked. Risk score: {risk['score']}"
        )
        return VerifyResponse(
            success=True,
            message="Your account has been successfully unlocked. You can now log in."
        )
    else:
        await log_event(db, username, "UNLOCK_FAILED", ip_address=ip,
                        detail="AD unlock operation failed")
        raise HTTPException(
            status_code=500,
            detail="Account unlock failed. Please contact IT helpdesk."
        )
