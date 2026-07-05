from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any

FIRST_REVIEW_RATINGS: tuple[tuple[int, str], ...] = (
    (1, "Again"),
    (2, "Hard"),
    (3, "Good"),
    (4, "Easy"),
)
FIRST_REVIEW_PRESET_PREFIX = "FSRS Preset Advisor : First Review"
FIRST_REVIEW_SPLIT_SUFFIXES: tuple[str, ...] = tuple(
    f" - {label}" for _rating, label in FIRST_REVIEW_RATINGS
)


def child_deck_name_for_first_review_split(source_deck_name: str, label: str) -> str:
    source_leaf_name = source_deck_name.split("::")[-1]
    return f"{source_deck_name}::{source_leaf_name} - {label}"


def target_deck_names_for_first_review_split(source_deck_name: str) -> dict[int, str]:
    return {
        rating: child_deck_name_for_first_review_split(source_deck_name, label)
        for rating, label in FIRST_REVIEW_RATINGS
    }


def target_preset_names_for_first_review_split(source_deck_name: str) -> dict[int, str]:
    return {
        rating: f"{FIRST_REVIEW_PRESET_PREFIX} : {source_deck_name} - {label}"
        for rating, label in FIRST_REVIEW_RATINGS
    }


def is_first_review_split_deck_name(deck_name: str) -> bool:
    return any(deck_name.endswith(suffix) for suffix in FIRST_REVIEW_SPLIT_SUFFIXES)


def normalize_card_ids_from_single_column_rows(rows: Sequence[Any]) -> list[int]:
    normalized: list[int] = []
    for row in rows:
        raw_value: Any
        if isinstance(row, Mapping):
            raw_value = row.get("id")
        elif isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)):
            raw_value = row[0] if row else None
        else:
            raw_value = row

        try:
            card_id = int(raw_value)
        except (TypeError, ValueError):
            continue
        if card_id > 0:
            normalized.append(card_id)
    return normalized


def split_card_ids_by_first_review(
    *,
    card_first_ease_rows: Sequence[tuple[int, int | None]],
) -> tuple[dict[int, list[int]], int, int]:
    buckets: dict[int, list[int]] = {rating: [] for rating, _ in FIRST_REVIEW_RATINGS}
    allowed_ratings = set(buckets.keys())
    seen: set[int] = set()
    no_first_review_count = 0
    unexpected_rating_count = 0

    for card_id, first_ease in card_first_ease_rows:
        cid = int(card_id)
        if cid in seen:
            continue
        seen.add(cid)

        if first_ease is None:
            no_first_review_count += 1
            continue

        ease = int(first_ease)
        if ease in allowed_ratings:
            buckets[ease].append(cid)
            continue

        unexpected_rating_count += 1

    return buckets, no_first_review_count, unexpected_rating_count
