from __future__ import annotations


def optimization_progress_message(
    *,
    done: int,
    total: int,
    deck_name: str | None = None,
) -> str:
    remaining = max(total - done, 0)
    if deck_name:
        return (
            f'Optimizing "{deck_name}"\n'
            f"Completed: {done}/{total}\n"
            f"Remaining: {remaining}"
        )
    return f"Preparing deck optimizations...\nCompleted: {done}/{total}\nRemaining: {remaining}"


def preset_optimization_progress_message(
    *,
    done: int,
    total: int,
    preset_name: str | None = None,
) -> str:
    remaining = max(total - done, 0)
    if preset_name:
        return (
            f'Optimizing preset "{preset_name}"\n'
            f"Completed: {done}/{total}\n"
            f"Remaining: {remaining}"
        )
    return f"Preparing preset optimizations...\nCompleted: {done}/{total}\nRemaining: {remaining}"
