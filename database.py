"""
Database models (SQLite via SQLAlchemy async)
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from datetime import datetime
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class OTPRecord(Base):
    __tablename__ = "otp_records"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(100), index=True, nullable=False)
    otp_hash      = Column(String(256), nullable=False)   # bcrypt hash of OTP
    channel       = Column(String(20), nullable=False)    # sms / whatsapp / email
    attempts      = Column(Integer, default=0)
    verified      = Column(Boolean, default=False)
    expires_at    = Column(DateTime, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(100), index=True, nullable=False)
    event         = Column(String(50), nullable=False)    # OTP_SENT / UNLOCK_SUCCESS / UNLOCK_FAILED / ESCALATED
    channel       = Column(String(20), nullable=True)
    ip_address    = Column(String(45), nullable=True)
    detail        = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

class UnlockAttempt(Base):
    __tablename__ = "unlock_attempts"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(100), index=True, nullable=False)
    ip_address    = Column(String(45), nullable=True)
    success       = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
