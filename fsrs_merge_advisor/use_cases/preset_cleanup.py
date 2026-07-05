from __future__ import annotations

from collections.abc import Iterable, Sequence

ADVISOR_PRESET_PREFIX = "FSRS Preset Advisor :"


def is_advisor_created_preset_name(name: str) -> bool:
    return str(name).startswith(ADVISOR_PRESET_PREFIX)


def empty_advisor_preset_candidates(
    *,
    presets: Sequence[tuple[int, str]],
    used_preset_ids: Iterable[int],
) -> list[tuple[int, str]]:
    used_ids = {int(preset_id) for preset_id in used_preset_ids}
    candidates = [
        (int(conf_id), str(conf_name))
        for conf_id, conf_name in presets
        if is_advisor_created_preset_name(str(conf_name)) and int(conf_id) not in used_ids
    ]
    return sorted(candidates, key=lambda item: item[1].lower())


def unused_advisor_preset_candidates_by_name(
    *,
    presets: Sequence[tuple[int, str]],
    used_preset_ids: Iterable[int],
    preset_names: Iterable[str],
) -> list[tuple[int, str]]:
    used_ids = {int(preset_id) for preset_id in used_preset_ids}
    target_names = {str(name) for name in preset_names}
    return [
        (int(conf_id), str(conf_name))
        for conf_id, conf_name in presets
        if str(conf_name) in target_names
        and is_advisor_created_preset_name(str(conf_name))
        and int(conf_id) not in used_ids
    ]
