"""Live routing and citation smoke evaluation with synthetic evidence."""
import json
from v2.workspace_agents import investigate, provider

CASES = [
    ("What prerequisite blocks my optics assignment?", "work", {"task/1":{"title":"Optics","prerequisite":"Lab"}},"lab"),
    ("When is my next fixed lecture?", "calendar", {"event/1":{"title":"Physics","starts_at":"2026-11-25T09:00:00+05:30"}},"9"),
    ("Which reminder did I receive?", "inbox", {"notification/1":{"message":"Submit optics report"}},"optics"),
    ("What is my preferred focus hour?", "focus", {"focus/1":{"preferred_hour":17}},"17"),
    ("How many tasks are overdue?", "progress", {"dashboard/today":{"overdue_count":7}},"7"),
    ("What is the first block of my proposed week?", "planning", {"preview/week":{"first":"Thermodynamics"}},"thermodynamics"),
]

def main():
    call = provider()
    results = []
    for question, role, records, keyword in CASES:
        try:
            reply = investigate(question, lambda d: records if d == role else {}, call)
            ok = (role in reply["specialists"] and bool(reply["sources"])
                  and keyword in reply["decision"]["message"].lower())
            results.append({"domain":role,"pass":ok,"latency_ms":reply["latency_ms"]})
        except Exception as exc:
            results.append({"domain":role,"pass":False,"error":type(exc).__name__})
    print(json.dumps(results, indent=2))
    return int(not all(case["pass"] for case in results))

if __name__ == "__main__":
    raise SystemExit(main())
