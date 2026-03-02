from __future__ import annotations

from collections.abc import Sequence


def can_reuse_cached_params(
    *,
    cached_review_count: int | None,
    current_review_count: int,
    cached_params: Sequence[float] | None,
) -> bool:
    return cached_review_count == current_review_count and cached_params is not None
