"""Hybrid interpreter, bounded tradeoff explainer, and owner-scoped lexical retrieval.

Strict boundaries:
- Exact reads take 0 model calls.
- Retrieved task/goal text and provider outputs are untrusted data.
- Fabricated IDs or unsupported evidence references are rejected.
- Only authenticated domain writers can commit.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import FixedEvent, Goal, Task
from .tools import _make_evidence, _user_timezone, get_consented_focus_summary, get_planning_limits

PROMPT_VERSION = "hybrid-v1.0"
SCHEMA_VERSION = "2026-11-25"
MAX_MODEL_LATENCY_MS = 15_000
MAX_INPUT_TOKENS = 6_000
MAX_OUTPUT_TOKENS = 1_200


class InterpretedIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal[
        "exact_read",
        "schedule_task",
        "replan_event",
        "draft_task",
        "draft_goal",
        "draft_task_change",
        "draft_goal_change",
        "draft_decomposition",
        "clarify",
        "answer",
    ]
    target_ids: list[str] = Field(default_factory=list, max_length=8)
    cited_evidence_ids: list[str] = Field(default_factory=list, max_length=12)
    preference_scope: Literal["request_only", "persistent", "none"] = "none"
    unresolved_question: str | None = Field(default=None, max_length=300)
    message: str = Field(min_length=1, max_length=1000)


class TradeoffExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selected_candidate_id: str | None = None
    ask_user: str | None = Field(default=None, max_length=300)
    cited_claims: list[str] = Field(default_factory=list, max_length=8)
    tradeoffs: list[str] = Field(default_factory=list, max_length=6)
    unmet_goals: list[str] = Field(default_factory=list, max_length=6)


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}", text.lower())}


def lexical_retrieve(
    db: Session,
    owner_uid: str,
    query: str,
    *,
    char_budget: int = 4500,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Owner-scoped lexical retrieval across tasks, goals, events, limits, and consented focus."""
    now = now_utc or datetime.now(timezone.utc)
    tz_name = _user_timezone(db, owner_uid)
    q_tokens = _tokenize(query)

    scored: list[tuple[int, str, dict[str, Any]]] = []
    for t in db.scalars(select(Task).where(Task.owner_uid == owner_uid)).all():
        hay = _tokenize(f"{t.title} {t.description} {' '.join(t.context_tags or [])}")
        overlap = len(q_tokens & hay)
        ev = _make_evidence(
            "task",
            t.id,
            {
                "id": t.id,
                "title": t.title,
                "description": t.description[:240],
                "status": t.status,
                "duration_minutes": t.duration_minutes,
                "version": t.version,
            },
            tz_name,
            version=t.version,
            now_utc=now,
        ).to_dict()
        scored.append((overlap * 10 + (2 if t.status == "pending" else 0), t.id, ev))

    for g in db.scalars(select(Goal).where(Goal.owner_uid == owner_uid)).all():
        hay = _tokenize(f"{g.title} {g.description}")
        overlap = len(q_tokens & hay)
        ev = _make_evidence(
            "goal",
            g.id,
            {"id": g.id, "title": g.title, "description": g.description[:240], "status": g.status, "version": g.version},
            tz_name,
            version=g.version,
            now_utc=now,
        ).to_dict()
        scored.append((overlap * 10 + (1 if g.status == "active" else 0), g.id, ev))

    for ev_row in db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == owner_uid)).all():
        hay = _tokenize(ev_row.title)
        overlap = len(q_tokens & hay)
        ev = _make_evidence(
            "fixed_event",
            ev_row.id,
            {
                "id": ev_row.id,
                "title": ev_row.title,
                "starts_at": ev_row.starts_at.isoformat(),
                "ends_at": ev_row.ends_at.isoformat(),
                "version": ev_row.version,
            },
            tz_name,
            version=ev_row.version,
            now_utc=now,
        ).to_dict()
        scored.append((overlap * 10, ev_row.id, ev))

    scored.sort(key=lambda item: (-item[0], item[1]))

    # Always include hard limits & consented focus status first (material facts before history)
    limits_ev = get_planning_limits(db, owner_uid, now_utc=now)["evidence"]
    focus_ev = get_consented_focus_summary(db, owner_uid, now_utc=now)["evidence"]
    packed: list[dict[str, Any]] = [limits_ev, focus_ev]
    used_chars = len(json.dumps(packed, default=str))
    seen_fingerprints = {limits_ev["fingerprint"], focus_ev["fingerprint"]}
    truncated = False

    for _, _, ev in scored:
        if ev["fingerprint"] in seen_fingerprints:
            continue
        encoded_len = len(json.dumps(ev, default=str))
        if used_chars + encoded_len > char_budget:
            truncated = True
            continue
        packed.append(ev)
        seen_fingerprints.add(ev["fingerprint"])
        used_chars += encoded_len

    return {
        "evidence": packed,
        "evidence_ids": [e["id"] for e in packed],
        "complete": not truncated,
        "truncated": truncated,
        "timezone": tz_name,
        "observed_at": now.isoformat(),
    }


def validate_interpreted_intent(intent: InterpretedIntent, allowed_ids: set[str]) -> InterpretedIntent:
    """Reject any fabricated or cross-owner entity/evidence IDs."""
    for tid in intent.target_ids:
        if tid not in allowed_ids:
            raise ValueError(f"Unsupported target_id '{tid}' not in owner evidence packet")
    for eid in intent.cited_evidence_ids:
        if eid not in allowed_ids:
            raise ValueError(f"Unsupported cited_evidence_id '{eid}' not in owner evidence packet")
    return intent


def deterministic_tradeoff_comparison(candidates: list[dict[str, Any]]) -> TradeoffExplanation:
    """Fallback deterministic comparison when tradeoff model is disabled or fails."""
    if not candidates:
        return TradeoffExplanation(
            ask_user="No feasible candidate plans were generated.",
            cited_claims=[],
            tradeoffs=[],
            unmet_goals=[],
        )
    best = max(
        candidates,
        key=lambda c: (c.get("quality_score", 0.0), c.get("planned_minutes", 0), -c.get("unscheduled_minutes", 0)),
    )
    tradeoffs = [
        f"Candidate {c['candidate_id']}: {c.get('planned_minutes', 0)}m planned, "
        f"{c.get('unscheduled_minutes', 0)}m unscheduled, score {c.get('quality_score', 0):.2f}"
        for c in candidates[:3]
    ]
    return TradeoffExplanation(
        selected_candidate_id=best["candidate_id"],
        cited_claims=[best["candidate_id"]],
        tradeoffs=tradeoffs,
        unmet_goals=[],
    )


def explain_tradeoffs(
    candidates: list[dict[str, Any]],
    call_model=None,
) -> dict[str, Any]:
    """Select/explain candidate differences; falls back cleanly to deterministic comparison."""
    if not candidates or call_model is None:
        exp = deterministic_tradeoff_comparison(candidates)
        return {"mode": "deterministic", "explanation": exp.model_dump()}

    allowed_cand_ids = {c["candidate_id"] for c in candidates}
    try:
        raw = call_model(
            "Compare these validated schedule candidates. Cite only provided candidate_ids. "
            "Do not invent slots or alter constraints.",
            {"candidates": candidates},
            TradeoffExplanation,
        )
        exp = TradeoffExplanation.model_validate(raw)
        if exp.selected_candidate_id and exp.selected_candidate_id not in allowed_cand_ids:
            raise ValueError("Selected unknown candidate_id")
        if any(cid not in allowed_cand_ids for cid in exp.cited_claims):
            raise ValueError("Cited unknown candidate_id")
        return {"mode": "llm", "explanation": exp.model_dump()}
    except Exception:
        exp = deterministic_tradeoff_comparison(candidates)
        return {"mode": "deterministic_fallback", "explanation": exp.model_dump()}
