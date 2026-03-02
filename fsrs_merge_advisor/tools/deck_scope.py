from __future__ import annotations

from collections.abc import Sequence


def leaf_deck_entries(entries: Sequence[tuple[int, str]]) -> list[tuple[int, str]]:
    ancestor_names: set[str] = set()
    for _, name in entries:
        parts = name.split("::")
        for idx in range(1, len(parts)):
            ancestor_names.add("::".join(parts[:idx]))
    return [(deck_id, name) for deck_id, name in entries if name not in ancestor_names]


def descendant_deck_ids(
    entries: Sequence[tuple[int, str]],
    root_deck_name: str,
) -> list[int]:
    prefix = f"{root_deck_name}::"
    return [
        deck_id
        for deck_id, deck_name in entries
        if deck_name == root_deck_name or deck_name.startswith(prefix)
    ]
