"""Semantic task decomposition engine.

Decomposes large or complex tasks into meaningful, logically ordered subtasks
with dependency constraints, using LLM reasoning when configured or deterministic
structural decomposition when offline.
"""
import json
import logging
import os
from datetime import datetime
from typing import Any

from groq import Groq

logger = logging.getLogger(__name__)


def _deterministic_decomposition(
    task_title: str,
    task_desc: str,
    duration_minutes: int,
    num_subtasks: int = 3,
) -> list[dict[str, Any]]:
    """Safe, predictable breakdown into structured phases without external network."""
    num_subtasks = max(2, min(num_subtasks, 5))
    clean_title = task_title.strip()

    templates = [
        ("Research & Requirements", f"Review background, scope, and objectives for '{clean_title}'"),
        ("Architecture & Setup", f"Set up environment, outline structure, and prepare assets for '{clean_title}'"),
        ("Core Implementation", f"Execute core work and primary deliverables for '{clean_title}'"),
        ("Testing & Verification", f"Verify functionality, validate constraints, and fix issues for '{clean_title}'"),
        ("Final Polish & Review", f"Review completeness, polish details, and finalize '{clean_title}'"),
    ]

    selected_templates = templates[:num_subtasks]
    # If 2 subtasks requested
    if num_subtasks == 2:
        selected_templates = [
            (f"Draft & Preparation: {clean_title}", f"Initial research, drafting, and setup for {clean_title}"),
            (f"Finalization: {clean_title}", f"Execution, review, and completion for {clean_title}"),
        ]
    elif num_subtasks == 3:
        selected_templates = [
            (f"Phase 1: Research & Outline ({clean_title})", f"Analyze requirements and outline steps for {clean_title}"),
            (f"Phase 2: Core Execution ({clean_title})", f"Perform principal work for {clean_title}"),
            (f"Phase 3: Review & Finalize ({clean_title})", f"Review quality and finalize deliverables for {clean_title}"),
        ]
    else:
        selected_templates = [
            (f"Step {i+1}: {tmpl[0]}", tmpl[1]) for i, tmpl in enumerate(selected_templates)
        ]

    # Distribute duration_minutes proportionally (minimum 10 minutes per subtask)
    base_mins = max(10, duration_minutes // num_subtasks)
    subtasks = []
    allocated = 0
    for i, (title, desc) in enumerate(selected_templates):
        if i == len(selected_templates) - 1:
            mins = max(10, duration_minutes - allocated)
        else:
            mins = base_mins
            allocated += mins
        subtasks.append({
            "title": title[:160],
            "description": desc[:4000],
            "duration_minutes": mins,
            "splittable": mins > 45,
            "importance": "important",
        })

    return subtasks


def decompose_task_logic(
    task_title: str,
    task_desc: str = "",
    duration_minutes: int = 60,
    deadline_at: datetime | None = None,
    num_subtasks: int = 3,
    prompt_hint: str | None = None,
) -> list[dict[str, Any]]:
    """Break down a task into sequential subtasks via LLM or deterministic fallback."""
    num_subtasks = max(2, min(num_subtasks, 5))
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    if groq_key:
        try:
            client = Groq(api_key=groq_key, timeout=8.0)
            model = os.getenv("CHRONOMIND_LLM_REASONING_MODEL", "llama-3.3-70b-versatile")
            system_prompt = (
                "You are an expert productivity planning assistant in ChronoMind AI. "
                "Decompose the given task into sequential, non-overlapping subtasks that must be done in order. "
                "Output JSON with a key 'subtasks' containing an array of objects. "
                "Each object must have 'title' (string, max 120 chars), 'description' (string), "
                "and 'duration_minutes' (integer >= 10, sum of all duration_minutes should equal approximately the total minutes)."
            )
            user_msg = (
                f"Task: {task_title}\n"
                f"Description: {task_desc or 'None'}\n"
                f"Total Duration: {duration_minutes} minutes\n"
                f"Target number of subtasks: {num_subtasks}\n"
            )
            if prompt_hint:
                user_msg += f"User hint/focus: {prompt_hint}\n"

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=600,
            )
            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            candidates = parsed.get("subtasks", [])
            if isinstance(candidates, list) and len(candidates) >= 2:
                valid_subtasks = []
                for item in candidates[:num_subtasks]:
                    t_title = str(item.get("title", "")).strip()
                    if not t_title:
                        continue
                    mins = int(item.get("duration_minutes", duration_minutes // len(candidates)))
                    mins = max(10, min(mins, 480))
                    valid_subtasks.append({
                        "title": t_title[:160],
                        "description": str(item.get("description", ""))[:4000],
                        "duration_minutes": mins,
                        "splittable": mins > 45,
                        "importance": "important",
                    })
                if len(valid_subtasks) >= 2:
                    return valid_subtasks
        except Exception as exc:
            logger.warning("Groq decomposition failed or timed out: %s; using deterministic breakdown", exc)

    return _deterministic_decomposition(task_title, task_desc, duration_minutes, num_subtasks)
