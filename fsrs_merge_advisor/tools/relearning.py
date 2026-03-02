from __future__ import annotations

from collections.abc import Sequence


def count_relearning_steps_in_day(steps: Sequence[float]) -> int:
    count = 0
    accumulated_minutes = 0.0
    for raw_value in steps:
        value = float(raw_value)
        accumulated_minutes += value
        if accumulated_minutes >= 1440:
            break
        count += 1
    return count
