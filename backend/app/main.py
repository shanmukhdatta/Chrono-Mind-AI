"""
ChronoMind AI — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.database import init_db
from app.api.auth import router as auth_router
from app.api.routes import (
    user_router, dashboard_router, timetable_router,
    tasks_router, ai_router,
)

# ─── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ChronoMind AI starting up...")
    await init_db()
    logger.info("✅ Database initialized")
    yield
    logger.info("👋 ChronoMind AI shutting down")


# ─── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title="ChronoMind AI API",
    description="Intelligent AI-powered day planner for college students",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(user_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(timetable_router, prefix=API_PREFIX)
app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)


# ─── Health Check ─────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "app": settings.APP_NAME}


@app.get("/health/detailed")
async def health_detailed():
    """Debug endpoint to verify configuration."""
    import os
    groq_key = settings.GROQ_API_KEY
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "groq_configured": bool(groq_key) and len(groq_key) > 10,
        "google_oauth_configured": bool(settings.GOOGLE_CLIENT_ID),
        "database_url": settings.DATABASE_URL[:30] + "...",
        "debug_mode": settings.DEBUG,
        "allowed_origins": settings.ALLOWED_ORIGINS,
    }


@app.get("/")
async def root():
    return {
        "message": "ChronoMind AI Backend",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }
