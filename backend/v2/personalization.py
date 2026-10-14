"""Simple opt-in focus-hour preference inference; no training or raw-text tracking."""
def preferred_work_hour(records: list[tuple[int, int]], min_samples: int = 5) -> int | None:
    valid = [
        (hour, duration) for hour, duration in records
        if isinstance(hour, int) and 0 <= hour <= 23
        and isinstance(duration, int) and duration >= 0
    ]
    if len(valid) < min_samples:
        return None
    totals: dict[int, int] = {}
    for hour, duration in valid:
        totals[hour] = totals.get(hour, 0) + duration
    return max(totals, key=lambda hour: (totals[hour], -hour)) if totals else None
