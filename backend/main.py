from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os

from scheduler import start_scheduler, stop_scheduler
from routers import tasks, assistant, profile, timetable
from middleware.auth import get_current_user, get_admin_user

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title="ChronoMind AI API",
    description="Intelligent Day Planner API for College Students",
    version="2.0.0",
    lifespan=lifespan
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"]
)

# Include routers
app.include_router(tasks.router)
app.include_router(assistant.router)
app.include_router(profile.router)
app.include_router(timetable.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "chronomind-ai"}

@app.post("/api/admin/trigger-reschedule")
async def trigger_reschedule(current_user: dict = Depends(get_admin_user)):
    """Admin endpoint to manually trigger rescheduling (for testing)"""
    from agents.rescheduler import run_for_all_users
    run_for_all_users()
    return {"success": True, "message": "Rescheduling triggered"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
