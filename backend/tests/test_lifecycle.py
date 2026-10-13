"""Lifecycle tests never start background threads or touch Firebase."""
import asyncio

import pytest
from core import lifecycle


def test_lifespan_starts_and_stops_scheduler(monkeypatch):
    events = []
    monkeypatch.setattr(lifecycle, "start_scheduler", lambda: events.append("start"))
    monkeypatch.setattr(lifecycle, "stop_scheduler", lambda: events.append("stop"))

    async def verify():
        async with lifecycle.application_lifespan(None):
            assert events == ["start"]

    asyncio.run(verify())
    assert events == ["start", "stop"]


def test_lifespan_stops_scheduler_on_error(monkeypatch):
    events = []
    monkeypatch.setattr(lifecycle, "start_scheduler", lambda: events.append("start"))
    monkeypatch.setattr(lifecycle, "stop_scheduler", lambda: events.append("stop"))

    async def fail():
        async with lifecycle.application_lifespan(None):
            raise RuntimeError("test interruption")

    with pytest.raises(RuntimeError, match="test interruption"):
        asyncio.run(fail())
    assert events == ["start", "stop"]
