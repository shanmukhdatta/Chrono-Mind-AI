"""Transparent deterministic priority scoring, independent of an LLM.

Combines user importance, deadline urgency, active goals, repeated delays,
dependency unblocking value, and permitted behavioral focus alignments.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class PrioritySignal:
    score: int
    reasons: tuple[str, ...]


def normalize_context(value: str | None) -> str:
    """Canonical form used to compare a user's focus context with task tags."""
    return " ".join((value or "").casefold().split())


def context_matches(focus_context: str | None, context_tags: list[str] | None) -> bool:
    """Deterministic match between the active focus context and a task's tags.

    Comparison is case-insensitive and whitespace-normalized. Two phrases match
    when they share at least one meaningful token (3+ characters), or when one
    normalized phrase contains the other, so "Placement Season" matches the tag
    "Placement Prep" through the shared "placement" token without relying on
    fuzzy or substring-of-word heuristics.
    """
    focus = normalize_context(focus_context)
    if len(focus) < 3 or not context_tags:
        return False
    focus_tokens = {token for token in focus.split() if len(token) >= 3}
    if not focus_tokens:
        return False
    for raw_tag in context_tags:
        tag = normalize_context(raw_tag if isinstance(raw_tag, str) else str(raw_tag))
        if len(tag) < 3:
            continue
        tag_tokens = {token for token in tag.split() if len(token) >= 3}
        if focus_tokens & tag_tokens:
            return True
        if focus == tag or focus in tag or tag in focus:
            return True
    return False


def score_task(
    importance: str,
    deadline_at: datetime | None,
    goal_is_active: bool,
    now: datetime,
    postponements: int = 0,
    dependent_count: int = 0,
    is_blocked: bool = False,
    preferred_hour_alignment: bool = False,
    duration_minutes: int | None = None,
    context_match: bool = False,
    splittable: bool = True,
) -> PrioritySignal:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    score = 15
    reasons = ["Pending work"]
    if importance == "important":
        score += 35
        reasons.append("Marked important")
    if goal_is_active:
        score += 15
        reasons.append("Supports an active goal")
    if deadline_at is not None:
        if deadline_at.tzinfo is None or deadline_at.utcoffset() is None:
            raise ValueError("deadline_at must be timezone-aware")
        remaining = deadline_at - now
        if remaining.total_seconds() < 0:
            score += 40
            reasons.append("Deadline passed")
        elif remaining <= timedelta(hours=24):
            score += 30
            reasons.append("Due within 24 hours")
        elif remaining <= timedelta(days=3):
            score += 20
            reasons.append("Due within 3 days")
        elif remaining <= timedelta(days=7):
            score += 10
            reasons.append("Due this week")

    if postponements > 0:
        boost = min(15, postponements * 5)
        score += boost
        reasons.append(f"Postponed {postponements} time(s)")

    if dependent_count > 0:
        boost = min(15, dependent_count * 5)
        score += boost
        reasons.append(f"Unblocks {dependent_count} dependent task(s)")

    if preferred_hour_alignment:
        score += 10
        reasons.append("Matches preferred focus window")

    if duration_minutes is not None and duration_minutes <= 15:
        score += 5
        reasons.append("Quick win (<=15 min)")

    if context_match:
        score += 15
        reasons.append("Matches your current focus context")

    if not splittable:
        score += 5
        reasons.append("Needs one continuous block (cannot be split)")

    if is_blocked:
        score = max(5, score - 25)
        reasons.append("Blocked by unfinished prerequisite")

    return PrioritySignal(score=max(1, min(score, 100)), reasons=tuple(reasons))
