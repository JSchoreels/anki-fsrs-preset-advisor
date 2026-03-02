from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..tools.assignment_changes import (
    changed_target_preset_ids_from_assignments,
    deck_ids_grouped_by_target_preset,
)


def changed_preset_deck_groups_for_reoptimization(
    *,
    before_assignments: Mapping[int, int],
    after_target_assignments: Mapping[int, int],
    target_by_deck: Mapping[int, int],
    candidate_preset_ids: Sequence[int],
    all_current_assignments: Mapping[int, int],
) -> list[tuple[int, list[int]]]:
    changed_preset_ids = changed_target_preset_ids_from_assignments(
        before_assignments=before_assignments,
        after_assignments=after_target_assignments,
        target_by_deck=target_by_deck,
        candidate_preset_ids=candidate_preset_ids,
    )
    return deck_ids_grouped_by_target_preset(
        target_by_deck=all_current_assignments,
        preset_ids=changed_preset_ids,
    )


def preset_optimization_summary_message(
    *,
    optimized: int,
    no_data: int,
    invalid_params: int,
    failed: int,
    cancelled: bool,
) -> str:
    lines = [
        f"Optimized presets: {optimized}",
        f"Skipped (no FSRS items): {no_data}",
        f"Skipped (non-FSRS6 params): {invalid_params}",
        f"Failed: {failed}",
    ]
    if cancelled:
        lines.append("Cancelled before completion.")
    return "Preset optimization summary:\n" + "\n".join(lines)
