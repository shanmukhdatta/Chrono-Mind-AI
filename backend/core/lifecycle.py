"""Application lifecycle boundary, separate from API route registration."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def application_lifespan(app: FastAPI):
    """Keep scheduler shutdown reliable, including exceptional application exit."""
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
