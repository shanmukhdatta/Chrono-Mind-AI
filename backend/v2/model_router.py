"""Allowlisted, low-cost routing: deterministic queries, fast and complex LLM tiers."""
import re

ALLOWED_MODELS = {"llama-3.1-8b-instant", "llama-3.3-70b-versatile"}


def can_answer_without_llm(message: str) -> bool:
    normalized = re.sub(r"\s+", " ", message.strip().lower())
    return normalized.rstrip("?.!") in (
        "list my pending tasks",
        "show my pending tasks",
        "how many pending tasks do i have",
        "count my pending tasks",
    )


def select_model(message: str, environment) -> str:
    text = message.lower()
    complex_request = len(message) > 320 or any(
        phrase in text for phrase in (
            "multiple goals", "conflicting deadlines", "several projects",
            "trade-offs", "prioritise across", "prioritize across",
            "complex plan", "plan my week", "replan my week",
        )
    )
    if complex_request:
        selected = environment.get(
            "CHRONOMIND_LLM_REASONING_MODEL", "llama-3.3-70b-versatile"
        )
    else:
        selected = environment.get(
            "CHRONOMIND_LLM_FAST_MODEL",
            environment.get("CHRONOMIND_LLM_MODEL", "llama-3.1-8b-instant"),
        )
    if selected not in ALLOWED_MODELS:
        raise ValueError("Configured model is not allowlisted")
    return selected
