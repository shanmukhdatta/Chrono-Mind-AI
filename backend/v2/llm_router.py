"""Explainable, bounded assistant model routing; no LLM for simple DB summaries."""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ModelRoute:
    tier: str
    model: str | None
    reason: str


_SIMPLE_QUESTIONS = (
    "how many tasks", "how many goals", "count my tasks", "my task count",
    "how many pending tasks", "how many active goals", "show briefing",
)
_COMPLEX_MARKERS = (
    "replan", "reorganize", "optimize", "split this task", "break down",
    "decompose", "conflicting goals", "plan my week", "prioritize my",
    "compare several plans",
)


def choose_route(message: str) -> ModelRoute:
    text = message.strip().lower()
    if any(text.startswith(word) for word in _SIMPLE_QUESTIONS):
        return ModelRoute("no_llm", None, "Answerable from bounded database summary")
    if any(marker in text for marker in _COMPLEX_MARKERS):
        return ModelRoute(
            "reasoning", os.getenv("CHRONOMIND_REASONING_LLM_MODEL", "llama-3.3-70b-versatile"),
            "Complex planning or decomposition request",
        )
    return ModelRoute(
        "fast", os.getenv("CHRONOMIND_FAST_LLM_MODEL",
        os.getenv("CHRONOMIND_LLM_MODEL", "llama-3.1-8b-instant")),
        "Simple natural-language intent interpretation",
    )


def simple_answer(context: dict) -> str:
    pending = len(context["tasks"])
    goals = len(context["goals"])
    return f"You currently have {pending} pending tasks and {goals} active goals in ChronoMind V2."
