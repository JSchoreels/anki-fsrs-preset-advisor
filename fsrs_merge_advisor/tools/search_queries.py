from __future__ import annotations

from collections.abc import Sequence


def build_deck_search_query(
    *,
    deck_id: int,
    deck_name: str,
    include_children: bool,
) -> str:
    if not include_children:
        return f"did:{deck_id} -is:suspended"

    escaped_name = deck_name.replace("\\", "\\\\").replace('"', '\\"')
    return f'deck:"{escaped_name}" -is:suspended'


def build_multi_deck_search_query(deck_ids: Sequence[int]) -> str | None:
    unique_ids: list[int] = []
    seen: set[int] = set()
    for deck_id in deck_ids:
        value = int(deck_id)
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        unique_ids.append(value)

    if not unique_ids:
        return None
    if len(unique_ids) == 1:
        return f"did:{unique_ids[0]} -is:suspended"

    joined = " OR ".join(f"did:{deck_id}" for deck_id in unique_ids)
    return f"({joined}) -is:suspended"
