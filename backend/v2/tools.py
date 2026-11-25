"""Typed, owner-bound domain read tools with structured evidence metadata.

Every query in this module binds `owner_uid` from server-side authentication.
Model-supplied or client-supplied owner IDs are never accepted.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from .focus_api import focus_insights
from .models import (
    BehaviorConsent,
    FixedEvent,
    Goal,
    InAppNotification,
    PlanProposal,
    PlanningDecisionLog,
    Preference,
    ScheduleBlock,
    Task,
    TaskDependency,
)


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is not None and (dt.tzinfo is None or dt.utcoffset() is None):
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _user_timezone(db: Session, owner_uid: str) -> str:
    pref = db.get(Preference, owner_uid)
    return pref.timezone if pref else "Asia/Kolkata"


@dataclass
class EvidenceItem:
    source_type: str
    id: str
    fields: dict[str, Any]
    version: int | None
    fingerprint: str
    observed_at: str
    timezone: str
    filters: dict[str, Any] = field(default_factory=dict)
    complete: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "id": self.id,
            "fields": self.fields,
            "version": self.version,
            "fingerprint": self.fingerprint,
            "observed_at": self.observed_at,
            "timezone": self.timezone,
            "filters": self.filters,
            "complete": self.complete,
        }


def _make_evidence(
    source_type: str,
    record_id: str,
    fields: dict[str, Any],
    tz_name: str,
    *,
    version: int | None = None,
    filters: dict[str, Any] | None = None,
    complete: bool = True,
    now_utc: datetime | None = None,
) -> EvidenceItem:
    observed = (now_utc or datetime.now(timezone.utc)).isoformat()
    return EvidenceItem(
        source_type=source_type,
        id=record_id,
        fields=fields,
        version=version,
        fingerprint=_fingerprint(fields),
        observed_at=observed,
        timezone=tz_name,
        filters=filters or {},
        complete=complete,
    )


def count_tasks(
    db: Session,
    owner_uid: str,
    *,
    status: str = "pending",
    exclude_containers: bool = False,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    tz_name = _user_timezone(db, owner_uid)
    filters_meta = {"status": status, "exclude_containers": exclude_containers}
    stmt = select(func.count()).select_from(Task).where(
        Task.owner_uid == owner_uid,
        Task.status == status,
    )
    if exclude_containers:
        container_subq = select(Task.parent_task_id).where(
            Task.owner_uid == owner_uid,
            Task.parent_task_id.is_not(None),
        )
        stmt = stmt.where(Task.id.not_in(container_subq))
    total = int(db.scalar(stmt) or 0)
    ev = _make_evidence(
        "task_count",
        f"tasks:count:{status}",
        {"status": status, "count": total, "exclude_containers": exclude_containers},
        tz_name,
        filters=filters_meta,
        complete=True,
        now_utc=now_utc,
    )
    return {"count": total, "evidence": ev.to_dict()}


def list_tasks(
    db: Session,
    owner_uid: str,
    *,
    status: str = "pending",
    limit: int = 20,
    offset: int = 0,
    exclude_containers: bool = False,
    query: str | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    tz_name = _user_timezone(db, owner_uid)
    base_filters = [Task.owner_uid == owner_uid, Task.status == status]
    if exclude_containers:
        container_subq = select(Task.parent_task_id).where(
            Task.owner_uid == owner_uid,
            Task.parent_task_id.is_not(None),
        )
        base_filters.append(Task.id.not_in(container_subq))
    if query and query.strip():
        q = query.strip()
        base_filters.append(
            Task.title.icontains(q, autoescape=True)
            | Task.description.icontains(q, autoescape=True)
        )

    total = int(db.scalar(select(func.count()).select_from(Task).where(*base_filters)) or 0)
    rows = db.scalars(
        select(Task)
        .where(*base_filters)
        .order_by(Task.deadline_at, Task.created_at, Task.id)
        .offset(offset)
        .limit(limit)
    ).all()
    has_more = (offset + len(rows)) < total
    complete = (offset == 0 and not has_more)
    filters_meta = {
        "status": status,
        "exclude_containers": exclude_containers,
        "query": query,
        "limit": limit,
        "offset": offset,
    }
    items = []
    evidence = []
    for row in rows:
        fields = {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "status": row.status,
            "duration_minutes": row.duration_minutes,
            "importance": row.importance,
            "splittable": row.splittable,
            "goal_id": row.goal_id,
            "parent_task_id": row.parent_task_id,
            "context_tags": row.context_tags or [],
            "deadline_at": _ensure_aware(row.deadline_at).isoformat() if row.deadline_at else None,
            "version": row.version,
        }
        items.append(fields)
        evidence.append(
            _make_evidence(
                "task",
                row.id,
                fields,
                tz_name,
                version=row.version,
                filters=filters_meta,
                complete=complete,
                now_utc=now_utc,
            ).to_dict()
        )
    return {
        "items": items,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "returned": len(items),
            "has_more": has_more,
        },
        "complete": complete,
        "evidence": evidence,
    }


def count_goals(
    db: Session,
    owner_uid: str,
    *,
    status: str = "active",
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    tz_name = _user_timezone(db, owner_uid)
    total = int(
        db.scalar(
            select(func.count())
            .select_from(Goal)
            .where(Goal.owner_uid == owner_uid, Goal.status == status)
        )
        or 0
    )
    ev = _make_evidence(
        "goal_count",
        f"goals:count:{status}",
        {"status": status, "count": total},
        tz_name,
        filters={"status": status},
        complete=True,
        now_utc=now_utc,
    )
    return {"count": total, "evidence": ev.to_dict()}


def list_goals(
    db: Session,
    owner_uid: str,
    *,
    status: str = "active",
    limit: int = 20,
    offset: int = 0,
    query: str | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    tz_name = _user_timezone(db, owner_uid)
    filters = [Goal.owner_uid == owner_uid, Goal.status == status]
    if query and query.strip():
        q = query.strip()
        filters.append(
            Goal.title.icontains(q, autoescape=True)
            | Goal.description.icontains(q, autoescape=True)
        )
    total = int(db.scalar(select(func.count()).select_from(Goal).where(*filters)) or 0)
    rows = db.scalars(
        select(Goal).where(*filters).order_by(Goal.created_at, Goal.id).offset(offset).limit(limit)
    ).all()
    has_more = (offset + len(rows)) < total
    complete = (offset == 0 and not has_more)
    items = []
    evidence = []
    for row in rows:
        fields = {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "status": row.status,
            "target_date": row.target_date.isoformat() if row.target_date else None,
        }
        items.append(fields)
        evidence.append(
            _make_evidence(
                "goal",
                row.id,
                fields,
                tz_name,
                filters={"status": status, "limit": limit, "offset": offset},
                complete=complete,
                now_utc=now_utc,
            ).to_dict()
        )
    return {
        "items": items,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "returned": len(items),
            "has_more": has_more,
        },
        "complete": complete,
        "evidence": evidence,
    }


def get_task_dependencies(
    db: Session,
    owner_uid: str,
    task_id: str | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    tz_name = _user_timezone(db, owner_uid)
    stmt = select(TaskDependency).where(TaskDependency.owner_uid == owner_uid)
    if task_id:
        stmt = stmt.where((TaskDependency.task_id == task_id) | (TaskDependency.depends_on_id == task_id))
    edges = db.scalars(stmt.order_by(TaskDependency.id)).all()
    task_ids = {e.task_id for e in edges} | {e.depends_on_id for e in edges}
    task_map = {
        t.id: t
        for t in db.scalars(select(Task).where(Task.owner_uid == owner_uid, Task.id.in_(task_ids))).all()
    } if task_ids else {}
    items = []
    evidence = []
    for edge in edges:
        prereq = task_map.get(edge.depends_on_id)
        succ = task_map.get(edge.task_id)
        fields = {
            "id": edge.id,
            "task_id": edge.task_id,
            "task_title": succ.title if succ else None,
            "depends_on_id": edge.depends_on_id,
            "depends_on_title": prereq.title if prereq else None,
            "depends_on_status": prereq.status if prereq else None,
            "blocking": (prereq.status != "completed") if prereq else True,
        }
        items.append(fields)
        evidence.append(
            _make_evidence("dependency", edge.id, fields, tz_name, filters={"task_id": task_id}, now_utc=now_utc).to_dict()
        )
    return {"items": items, "complete": True, "evidence": evidence}


def get_calendar_range(
    db: Session,
    owner_uid: str,
    start_at: datetime,
    end_at: datetime,
    *,
    limit: int = 100,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Read overlapping fixed events and schedule blocks in [start_at, end_at).

    Sets `complete=False` if either query hits `limit`, preventing callers from
    claiming an entire day or range is free when coverage is truncated.
    """
    start_utc = _ensure_aware(start_at).astimezone(timezone.utc)
    end_utc = _ensure_aware(end_at).astimezone(timezone.utc)
    tz_name = _user_timezone(db, owner_uid)
    limit = max(1, min(limit, 500))

    event_rows = db.scalars(
        select(FixedEvent)
        .where(
            FixedEvent.owner_uid == owner_uid,
            FixedEvent.starts_at < end_utc,
            FixedEvent.ends_at > start_utc,
        )
        .order_by(FixedEvent.starts_at, FixedEvent.id)
        .limit(limit + 1)
    ).all()
    events_truncated = len(event_rows) > limit
    event_rows = event_rows[:limit]

    block_rows = db.scalars(
        select(ScheduleBlock)
        .where(
            ScheduleBlock.owner_uid == owner_uid,
            ScheduleBlock.starts_at < end_utc,
            ScheduleBlock.ends_at > start_utc,
        )
        .order_by(ScheduleBlock.starts_at, ScheduleBlock.id)
        .limit(limit + 1)
    ).all()
    blocks_truncated = len(block_rows) > limit
    block_rows = block_rows[:limit]

    task_ids = {b.task_id for b in block_rows}
    task_titles = {
        t.id: t.title
        for t in db.scalars(select(Task).where(Task.owner_uid == owner_uid, Task.id.in_(task_ids))).all()
    } if task_ids else {}

    complete = not (events_truncated or blocks_truncated)
    filters_meta = {"start_at": start_utc.isoformat(), "end_at": end_utc.isoformat(), "limit": limit}

    events = []
    blocks = []
    evidence = []
    for ev_row in event_rows:
        fields = {
            "id": ev_row.id,
            "title": ev_row.title,
            "starts_at": _ensure_aware(ev_row.starts_at).isoformat(),
            "ends_at": _ensure_aware(ev_row.ends_at).isoformat(),
            "fixed": True,
        }
        events.append(fields)
        evidence.append(
            _make_evidence("fixed_event", ev_row.id, fields, tz_name, filters=filters_meta, complete=complete, now_utc=now_utc).to_dict()
        )
    for blk in block_rows:
        fields = {
            "id": blk.id,
            "task_id": blk.task_id,
            "task_title": task_titles.get(blk.task_id),
            "starts_at": _ensure_aware(blk.starts_at).isoformat(),
            "ends_at": _ensure_aware(blk.ends_at).isoformat(),
            "source": blk.source,
            "fixed": False,
        }
        blocks.append(fields)
        evidence.append(
            _make_evidence("schedule_block", blk.id, fields, tz_name, filters=filters_meta, complete=complete, now_utc=now_utc).to_dict()
        )
    return {
        "range_start": start_utc.isoformat(),
        "range_end": end_utc.isoformat(),
        "timezone": tz_name,
        "fixed_events": events,
        "schedule_blocks": blocks,
        "complete": complete,
        "truncated": not complete,
        "evidence": evidence,
    }


def get_planning_limits(
    db: Session,
    owner_uid: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    pref = db.get(Preference, owner_uid)
    tz_name = pref.timezone if pref else "Asia/Kolkata"
    fields = {
        "timezone": tz_name,
        "work_start": pref.work_start.strftime("%H:%M") if pref else "08:00",
        "work_end": pref.work_end.strftime("%H:%M") if pref else "22:00",
        "max_daily_minutes": pref.max_daily_minutes if pref else 480,
        "min_break_minutes": pref.min_break_minutes if pref else 10,
        "focus_context": pref.focus_context if pref else None,
        "configured": pref is not None,
    }
    ev = _make_evidence("preference", f"preferences:{owner_uid}", fields, tz_name, now_utc=now_utc)
    return {"limits": fields, "evidence": ev.to_dict()}


def get_consented_focus_summary(
    db: Session,
    owner_uid: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    tz_name = _user_timezone(db, owner_uid)
    consent = db.get(BehaviorConsent, owner_uid)
    if consent is None or not consent.enabled:
        fields = {"consented": False, "preferred_hour": None, "sample_size": 0}
        ev = _make_evidence("focus_summary", "focus:consent", fields, tz_name, now_utc=now_utc)
        return {"consented": False, "summary": fields, "evidence": ev.to_dict()}
    insights = focus_insights(user={"uid": owner_uid}, db=db)
    fields = {
        "consented": True,
        "preferred_hour": insights.get("preferred_hour"),
        "sample_size": insights.get("sample_size", 0),
        "window_days": 90,
        "insights": insights,
    }
    ev = _make_evidence("focus_summary", "focus:insights", fields, tz_name, now_utc=now_utc)
    return {"consented": True, "summary": fields, "evidence": ev.to_dict()}


def list_proposal_history(
    db: Session,
    owner_uid: str,
    *,
    limit: int = 20,
    offset: int = 0,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    tz_name = _user_timezone(db, owner_uid)
    total = int(
        db.scalar(
            select(func.count()).select_from(PlanProposal).where(PlanProposal.owner_uid == owner_uid)
        )
        or 0
    )
    proposals = db.scalars(
        select(PlanProposal)
        .where(PlanProposal.owner_uid == owner_uid)
        .order_by(PlanProposal.created_at.desc(), PlanProposal.id)
        .offset(offset)
        .limit(limit)
    ).all()
    has_more = (offset + len(proposals)) < total
    complete = (offset == 0 and not has_more)
    items = []
    evidence = []
    for p in proposals:
        fields = {
            "id": p.id,
            "status": p.status,
            "block_count": len(p.proposed_blocks or []),
            "unscheduled_count": len(p.unscheduled or []),
            "created_at": _ensure_aware(p.created_at).isoformat(),
            "approved_at": _ensure_aware(p.approved_at).isoformat() if p.approved_at else None,
        }
        items.append(fields)
        evidence.append(
            _make_evidence("proposal", p.id, fields, tz_name, complete=complete, now_utc=now_utc).to_dict()
        )
    return {
        "items": items,
        "pagination": {"limit": limit, "offset": offset, "total": total, "returned": len(items), "has_more": has_more},
        "complete": complete,
        "evidence": evidence,
    }


def get_inbox_state(
    db: Session,
    owner_uid: str,
    *,
    limit: int = 20,
    offset: int = 0,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    tz_name = _user_timezone(db, owner_uid)
    unread_count = int(
        db.scalar(
            select(func.count())
            .select_from(InAppNotification)
            .where(InAppNotification.owner_uid == owner_uid, InAppNotification.read_at.is_(None))
        )
        or 0
    )
    total = int(
        db.scalar(
            select(func.count())
            .select_from(InAppNotification)
            .where(InAppNotification.owner_uid == owner_uid)
        )
        or 0
    )
    rows = db.scalars(
        select(InAppNotification)
        .where(InAppNotification.owner_uid == owner_uid)
        .order_by(InAppNotification.created_at.desc(), InAppNotification.id)
        .offset(offset)
        .limit(limit)
    ).all()
    has_more = (offset + len(rows)) < total
    complete = (offset == 0 and not has_more)
    items = []
    evidence = []
    for row in rows:
        fields = {
            "id": row.id,
            "kind": row.kind,
            "message": row.message,
            "read_at": _ensure_aware(row.read_at).isoformat() if row.read_at else None,
            "created_at": _ensure_aware(row.created_at).isoformat(),
        }
        items.append(fields)
        evidence.append(
            _make_evidence("notification", row.id, fields, tz_name, complete=complete, now_utc=now_utc).to_dict()
        )
    return {
        "unread_count": unread_count,
        "items": items,
        "pagination": {"limit": limit, "offset": offset, "total": total, "returned": len(items), "has_more": has_more},
        "complete": complete,
        "evidence": evidence,
    }


_WEEKDAYS = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}


def resolve_local_date(
    phrase: str,
    tz_name: str,
    now_utc: datetime | None = None,
) -> date | None:
    """Resolve a local date phrase ('today', 'tomorrow', weekday, or YYYY-MM-DD) in user's zone."""
    zone = ZoneInfo(tz_name)
    local_now = (now_utc or datetime.now(timezone.utc)).astimezone(zone)
    today = local_now.date()
    text = phrase.lower().strip()

    iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if iso_match:
        try:
            return date.fromisoformat(iso_match.group(1))
        except ValueError:
            pass
    if "day after tomorrow" in text:
        return today + timedelta(days=2)
    if "tomorrow" in text:
        return today + timedelta(days=1)
    if "today" in text or "tonight" in text:
        return today

    for name, weekday_num in _WEEKDAYS.items():
        if re.search(rf"\bnext\s+{name}\b", text):
            delta = (weekday_num - today.weekday()) % 7
            delta = delta + 7 if delta == 0 else delta
            return today + timedelta(days=delta)
        if re.search(rf"\b{name}\b", text):
            delta = (weekday_num - today.weekday()) % 7
            return today + timedelta(days=delta)
    return None


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{2,}", text.lower()) if t not in {
        "the", "and", "for", "with", "this", "that", "from", "into", "find",
        "minutes", "minute", "mins", "min", "hour", "hours", "today", "tomorrow",
        "task", "goal", "event", "exam", "existing", "moved", "reorganize", "week",
    }}


def search_entities(
    db: Session,
    owner_uid: str,
    query_text: str,
    *,
    entity_types: tuple[str, ...] = ("task", "goal", "fixed_event"),
    selected_id: str | None = None,
    selected_type: str | None = None,
    limit: int = 10,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Owner-bound entity resolution across ID, active selection, titles, descriptions, tags, dates, and type.

    Explicitly preserves `fixed_event` vs `task` distinction (e.g. an exam event vs its prep task).
    """
    tz_name = _user_timezone(db, owner_uid)
    q_norm = query_text.strip().lower()
    q_tokens = _tokens(query_text)
    target_date = resolve_local_date(query_text, tz_name, now_utc)
    zone = ZoneInfo(tz_name)
    candidates: list[tuple[float, dict[str, Any], EvidenceItem]] = []

    def score_record(
        etype: str,
        rec_id: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        rec_date: datetime | date | None = None,
        extra: dict[str, Any] | None = None,
        version: int | None = None,
    ):
        score = 0.0
        if rec_id.lower() in q_norm:
            score += 100.0
        if selected_id and rec_id == selected_id and (not selected_type or selected_type == etype):
            score += 60.0
        title_low = title.lower()
        if title_low in q_norm or q_norm in title_low:
            score += 40.0
        title_tokens = _tokens(title)
        desc_tokens = _tokens(description)
        tag_tokens = _tokens(" ".join(tags or []))
        if q_tokens:
            overlap_title = len(q_tokens & title_tokens)
            overlap_desc = len(q_tokens & desc_tokens)
            overlap_tags = len(q_tokens & tag_tokens)
            score += overlap_title * 12.0 + overlap_tags * 6.0 + overlap_desc * 3.0
        if target_date and rec_date is not None:
            d = rec_date.astimezone(zone).date() if isinstance(rec_date, datetime) else rec_date
            if d == target_date:
                score += 8.0
        # Type affinity hints
        if etype == "fixed_event" and any(w in q_norm for w in ("exam", "lecture", "class", "meeting", "event", "appointment")):
            if "exam" in title_low or "exam" in q_norm:
                score += 10.0
        if etype == "task" and any(w in q_norm for w in ("task", "revision", "study", "homework", "assignment", "prep")):
            score += 5.0

        if score <= 0 and selected_id != rec_id:
            return
        fields = {"id": rec_id, "entity_type": etype, "title": title, **(extra or {})}
        ev = _make_evidence(etype, rec_id, fields, tz_name, version=version, now_utc=now_utc)
        candidates.append((score, {"entity_type": etype, "id": rec_id, "title": title, "score": score, "fields": fields}, ev))

    if "task" in entity_types:
        for row in db.scalars(select(Task).where(Task.owner_uid == owner_uid, Task.status == "pending")).all():
            score_record(
                "task", row.id, row.title, row.description, row.context_tags,
                _ensure_aware(row.deadline_at),
                extra={
                    "duration_minutes": row.duration_minutes,
                    "importance": row.importance,
                    "splittable": row.splittable,
                    "status": row.status,
                    "version": row.version,
                    "parent_task_id": row.parent_task_id,
                    "deadline_at": _ensure_aware(row.deadline_at).isoformat() if row.deadline_at else None,
                },
                version=row.version,
            )
    if "goal" in entity_types:
        for row in db.scalars(select(Goal).where(Goal.owner_uid == owner_uid, Goal.status == "active")).all():
            score_record("goal", row.id, row.title, row.description, None, row.target_date, extra={"status": row.status})
    if "fixed_event" in entity_types:
        for row in db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == owner_uid)).all():
            score_record(
                "fixed_event", row.id, row.title, "", None, _ensure_aware(row.starts_at),
                extra={
                    "starts_at": _ensure_aware(row.starts_at).isoformat(),
                    "ends_at": _ensure_aware(row.ends_at).isoformat(),
                },
            )

    candidates.sort(key=lambda item: (-item[0], item[1]["title"], item[1]["id"]))
    top = candidates[:limit]
    return {
        "matches": [item[1] for item in top],
        "evidence": [item[2].to_dict() for item in top],
    }


def resolve_target_entity(
    db: Session,
    owner_uid: str,
    phrase: str,
    *,
    expected_type: str | None = None,
    selected_id: str | None = None,
    selected_type: str | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Resolve a user phrase to a single entity, or return a targeted disambiguation question."""
    types = (expected_type,) if expected_type else ("task", "fixed_event", "goal")
    res = search_entities(
        db, owner_uid, phrase,
        entity_types=types,
        selected_id=selected_id,
        selected_type=selected_type,
        limit=5,
        now_utc=now_utc,
    )
    matches = res["matches"]
    if not matches:
        return {"status": "not_found", "entity": None, "candidates": [], "question": None, "evidence": []}
    if len(matches) == 1:
        return {"status": "resolved", "entity": matches[0], "candidates": matches, "question": None, "evidence": res["evidence"][:1]}

    top, second = matches[0], matches[1]
    # Clear winner (e.g. exact ID/selection or significantly higher score)
    if top["score"] >= second["score"] + 15.0:
        return {"status": "resolved", "entity": top, "candidates": matches, "question": None, "evidence": res["evidence"][:1]}

    # Ambiguous: build a targeted question distinguishing the top candidates
    options_desc = ", ".join(
        f'"{m["title"]}" ({m["entity_type"].replace("_", " ")}, id {m["id"][:8]})'
        for m in matches[:3]
    )
    return {
        "status": "ambiguous",
        "entity": None,
        "candidates": matches[:3],
        "question": f"I found multiple matching items: {options_desc}. Which one do you mean?",
        "evidence": res["evidence"][:3],
    }
