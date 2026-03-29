"""
Admin Router — audit log viewer and stats (internal use only)
Protect this with VPN/IP restriction or JWT in production.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import get_db, AuditLog, UnlockAttempt

router = APIRouter()


class AuditEntry(BaseModel):
    id: int
    username: str
    event: str
    channel: Optional[str]
    ip_address: Optional[str]
    detail: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class Stats(BaseModel):
    total_unlocks_today: int
    total_failures_today: int
    total_escalations_today: int
    top_users: List[dict]


@router.get("/logs", response_model=List[AuditEntry])
async def get_audit_logs(
    username: Optional[str] = Query(None),
    event: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve audit logs with optional filters."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
    if username:
        query = query.where(AuditLog.username == username.lower())
    if event:
        query = query.where(AuditLog.event == event.upper())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats", response_model=Stats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Daily summary stats for IT dashboard."""
    cutoff = datetime.utcnow() - timedelta(hours=24)

    async def count_event(event_name: str) -> int:
        r = await db.execute(
            select(func.count()).where(
                AuditLog.event == event_name,
                AuditLog.created_at >= cutoff
            )
        )
        return r.scalar() or 0

    unlocks    = await count_event("UNLOCK_SUCCESS")
    failures   = await count_event("UNLOCK_FAILED")
    escalated  = await count_event("ESCALATED")

    # Top 5 users with most unlock attempts today
    result = await db.execute(
        select(AuditLog.username, func.count().label("cnt"))
        .where(AuditLog.created_at >= cutoff)
        .group_by(AuditLog.username)
        .order_by(desc("cnt"))
        .limit(5)
    )
    top_users = [{"username": row.username, "attempts": row.cnt} for row in result]

    return Stats(
        total_unlocks_today=unlocks,
        total_failures_today=failures,
        total_escalations_today=escalated,
        top_users=top_users
    )
