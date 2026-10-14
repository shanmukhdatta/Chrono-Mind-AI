# ChronoMind deterministic evaluation suite

Run from the backend folder:

```bash
python -m v2.evaluation
```

`evals/scenarios.jsonl` provides **120 reproducible unit-sized scheduling scenarios** covering baseline feasible tasks, fixed-event conflicts, deadlines, prerequisites, infeasible deadlines, and preference-driven slots. The runner checks duration conservation, no overlaps, deadline bounds, blocked tasks, and expected completeness. It returns a category-level JSON report and exits nonzero on invariant failure; CI runs the same dataset.

**Evaluation limitations:** This evaluates the *pure deterministic proposal engine*, not user-facing LangGraph end-to-end success, natural-language tool selection accuracy, calibration, longitudinal preference learning, PostgreSQL concurrency, or LLM token/cost metrics. A passing 120-case suite is evidence of these bounded invariants only. Real AI evaluation with adversarial prompts, learned behavior, tool accuracy and LLM provider traces remains a separate release milestone.
