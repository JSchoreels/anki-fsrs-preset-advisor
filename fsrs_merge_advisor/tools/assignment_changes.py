from __future__ import annotations

from collections.abc import Mapping, Sequence


def deck_ids_grouped_by_target_preset(
    *,
    target_by_deck: Mapping[int, int],
    preset_ids: Sequence[int],
) -> list[tuple[int, list[int]]]:
    grouped: list[tuple[int, list[int]]] = []
    for preset_id in preset_ids:
        deck_ids = [
            int(deck_id)
            for deck_id, assigned_preset in target_by_deck.items()
            if int(assigned_preset) == int(preset_id)
        ]
        if deck_ids:
            grouped.append((int(preset_id), deck_ids))
    return grouped


def changed_target_preset_ids_from_assignments(
    *,
    before_assignments: Mapping[int, int],
    after_assignments: Mapping[int, int],
    target_by_deck: Mapping[int, int],
    candidate_preset_ids: Sequence[int],
) -> list[int]:
    candidate_set = {int(preset_id) for preset_id in candidate_preset_ids}
    changed_set: set[int] = set()

    for raw_deck_id in target_by_deck:
        deck_id = int(raw_deck_id)
        before_preset = before_assignments.get(deck_id)
        after_preset = after_assignments.get(deck_id)
        if before_preset == after_preset:
            continue
        if before_preset is not None and int(before_preset) in candidate_set:
            changed_set.add(int(before_preset))
        if after_preset is not None and int(after_preset) in candidate_set:
            changed_set.add(int(after_preset))

    return [int(preset_id) for preset_id in candidate_preset_ids if int(preset_id) in changed_set]
