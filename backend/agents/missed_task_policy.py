"""Non-destructive selection policy for the legacy nightly rollover agent.

Unfinished optional tasks remain persisted on their original date; the legacy
rollover only attempts to move unfinished explicitly important tasks. V2 will
introduce a dedicated backlog and proposal/approval workflow.
"""

from typing import Any, Iterable, Mapping


def select_rollover_candidates(tasks: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return copies of unfinished important tasks without changing any input."""
    return [
        dict(task)
        for task in tasks
        if task.get("importance") == "important" and not task.get("completed", False)
    ]
