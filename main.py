"""
AD Account Unlock via OTP - Main FastAPI Application
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from database import init_db
from auth import router as auth_router
from unlock import router as unlock_router
from admin import router as admin_router

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="AD Account Unlock via OTP",
    description="Self-service Active Directory account unlock using OTP verification",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your portal domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,   prefix="/api/auth",   tags=["Auth"])
app.include_router(unlock_router, prefix="/api/unlock", tags=["Unlock"])
app.include_router(admin_router,  prefix="/api/admin",  tags=["Admin"])

@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "AD OTP Unlock"}
