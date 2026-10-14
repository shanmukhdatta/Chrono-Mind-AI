"""Protect the integrated V2 API contract and migration revision chain."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from main import app
from v2.models import Base


def test_every_v2_product_slice_is_registered():
    registered = {
        (path.path, method)
        for path in app.routes
        for method in getattr(path, "methods", set())
    }
    expected = {
        ("/api/v2/goals", "POST"),
        ("/api/v2/tasks", "POST"),
        ("/api/v2/tasks/{task_id}", "PATCH"),
        ("/api/v2/tasks/{task_id}/dependencies", "POST"),
        ("/api/v2/preferences", "PUT"),
        ("/api/v2/fixed-events", "POST"),
        ("/api/v2/calendar", "GET"),
        ("/api/v2/planning/preview", "GET"),
        ("/api/v2/plans", "POST"),
        ("/api/v2/plans/{plan_id}/approve", "POST"),
        ("/api/v2/plans/{plan_id}/undo", "POST"),
        ("/api/v2/agent/runs", "POST"),
        ("/api/v2/agent/runs/{run_id}/resume", "POST"),
        ("/api/v2/assistant/chat", "POST"),
        ("/api/v2/assistant/briefing", "GET"),
        ("/api/v2/dashboard", "GET"),
        ("/api/v2/recurrence", "POST"),
        ("/api/v2/focus/sessions", "POST"),
        ("/api/v2/focus/consent", "PUT"),
        ("/api/v2/notifications", "GET"),
        ("/api/v2/notifications/unread-count", "GET"),
        ("/api/v2/account/export", "GET"),
    }
    assert not (expected - registered), f"Missing endpoints: {expected - registered}"


def test_migration_history_is_linear_and_matches_schema():
    path = Path(__file__).resolve().parents[1] / "v2" / "alembic" / "versions"
    stems = [
        "0001_initial", "0002_proposals", "0003_legacy_archive",
        "0004_recurrence", "0005_focus", "0006_notifications",
        "0007_dependencies", "0008_release_hardening",
    ]
    previous = None
    for stem in stems:
        filename = path / (stem + ".py")
        assert filename.is_file()
        spec = spec_from_file_location("migration_" + stem, filename)
        assert spec is not None and spec.loader is not None
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == stem
        assert module.down_revision == previous
        previous = stem
    required = {
        "v2_users", "v2_goals", "v2_tasks", "v2_schedule_blocks",
        "v2_fixed_events", "v2_preferences", "v2_plan_proposals",
        "v2_legacy_task_archive", "v2_recurrence_series",
        "v2_recurrence_occurrences", "v2_recurrence_skips",
        "v2_focus_sessions", "v2_behavior_consent", "v2_behavior_events",
        "v2_inapp_notifications", "v2_task_dependencies",
    }
    assert required.issubset(Base.metadata.tables)
