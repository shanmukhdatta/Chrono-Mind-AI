import logging
from fastapi import FastAPI, Depends, Request

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from core.config import get_cors_origins
from core.lifecycle import application_lifespan
from routers import tasks, assistant, profile, timetable
from v2.api import router as v2_router
from v2.planning_api import router as planning_preview_router
from v2.calendar_api import router as v2_calendar_router
from v2.proposals_api import router as proposals_router
from v2.agent_api import router as agent_router
from v2.assistant import router as assistant_v2_router
from v2.dashboard_api import router as dashboard_v2_router
from v2.recurrence import router as recurrence_v2_router
from v2.focus_api import router as focus_v2_router
from v2.notifications_api import router as notifications_v2_router
from v2.account_data import router as account_v2_router
from v2.dependencies_api import router as dependency_v2_router
from middleware.auth import get_current_user, get_admin_user

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ChronoMind AI API",
    description="Intelligent Day Planner API for College Students",
    version="2.0.0",
    lifespan=application_lifespan
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"]
)

# Include routers
app.include_router(tasks.router)
app.include_router(assistant.router)
app.include_router(profile.router)
app.include_router(timetable.router)
app.include_router(v2_router)
app.include_router(planning_preview_router)
app.include_router(v2_calendar_router)
app.include_router(proposals_router)
app.include_router(agent_router)
app.include_router(assistant_v2_router)
app.include_router(dashboard_v2_router)
app.include_router(recurrence_v2_router)
app.include_router(focus_v2_router)
app.include_router(notifications_v2_router)
app.include_router(account_v2_router)
app.include_router(dependency_v2_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "chronomind-ai"}

@app.post("/api/admin/trigger-reschedule")
async def trigger_reschedule(current_user: dict = Depends(get_admin_user)):
    """Admin endpoint to manually trigger rescheduling (for testing)"""
    from scheduler import run_nightly_once
    outcome = run_nightly_once()
    return {"success": True, "data": outcome}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
