from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Optional


def params_signature(params: Sequence[float]) -> str:
    canonical = ",".join(f"{float(value):.12g}" for value in params)
    return hashlib.sha1(canonical.encode("utf-8")).hexdigest()


def evaluate_logloss_cache_key(
    *,
    target_deck_id: int,
    include_children: bool,
    source_params: Sequence[float],
) -> str:
    scope = "tree" if include_children else "single"
    return f"{scope}:{int(target_deck_id)}:{params_signature(source_params)}"


def can_reuse_evaluate_cached_logloss(
    *,
    cached_review_count: int | None,
    current_review_count: int,
    cached_log_loss: float | None,
) -> bool:
    return cached_review_count == current_review_count and cached_log_loss is not None


def weighted_bidirectional_delta(
    *,
    target_self_loss: float | None,
    target_with_source_loss: float | None,
    source_self_loss: float | None,
    source_with_target_loss: float | None,
    target_reviews: int,
    source_reviews: int,
) -> float | None:
    if (
        target_self_loss is None
        or target_with_source_loss is None
        or source_self_loss is None
        or source_with_target_loss is None
    ):
        return None

    left_weight = int(target_reviews)
    right_weight = int(source_reviews)
    weight_sum = left_weight + right_weight
    if weight_sum <= 0:
        return None

    left_delta = float(target_with_source_loss) - float(target_self_loss)
    right_delta = float(source_with_target_loss) - float(source_self_loss)
    return (left_weight * left_delta + right_weight * right_delta) / float(weight_sum)


def directed_delta_matrix(
    *,
    losses: Sequence[Sequence[float | None]],
) -> list[list[float | None]]:
    total = len(losses)
    if any(len(row) != total for row in losses):
        raise ValueError("Loss matrix must be square")

    deltas: list[list[float | None]] = [[None for _ in range(total)] for _ in range(total)]
    for target_idx in range(total):
        baseline = losses[target_idx][target_idx]
        for source_idx in range(total):
            if target_idx == source_idx:
                deltas[target_idx][source_idx] = 0.0
                continue
            value = losses[target_idx][source_idx]
            if baseline is None or value is None:
                deltas[target_idx][source_idx] = None
                continue
            deltas[target_idx][source_idx] = float(value) - float(baseline)
    return deltas


def symmetric_merge_score_matrix(
    *,
    losses: Sequence[Sequence[float | None]],
    review_counts: Sequence[int],
) -> list[list[float | None]]:
    total = len(losses)
    if len(review_counts) != total:
        raise ValueError("Review count vector size must match matrix size")
    if any(len(row) != total for row in losses):
        raise ValueError("Loss matrix must be square")

    matrix: list[list[float | None]] = [[None for _ in range(total)] for _ in range(total)]
    for idx in range(total):
        matrix[idx][idx] = 0.0

    for left_idx in range(total):
        for right_idx in range(left_idx + 1, total):
            score = weighted_bidirectional_delta(
                target_self_loss=losses[left_idx][left_idx],
                target_with_source_loss=losses[left_idx][right_idx],
                source_self_loss=losses[right_idx][right_idx],
                source_with_target_loss=losses[right_idx][left_idx],
                target_reviews=review_counts[left_idx],
                source_reviews=review_counts[right_idx],
            )
            matrix[left_idx][right_idx] = score
            matrix[right_idx][left_idx] = score

    return matrix


def _cluster_weight(
    *,
    cluster: Sequence[int],
    review_counts: Sequence[int],
) -> int:
    return sum(max(int(review_counts[idx]), 0) for idx in cluster)


def _weighted_average(
    *,
    values: Sequence[tuple[float, int]],
) -> float | None:
    weighted_sum = 0.0
    total_weight = 0
    for value, weight in values:
        use_weight = max(int(weight), 0)
        if use_weight <= 0:
            continue
        weighted_sum += float(value) * use_weight
        total_weight += use_weight
    if total_weight <= 0:
        return None
    return weighted_sum / float(total_weight)


def cluster_directed_delta(
    *,
    losses: Sequence[Sequence[float | None]],
    review_counts: Sequence[int],
    target_cluster: Sequence[int],
    source_cluster: Sequence[int],
) -> float | None:
    total = len(losses)
    if len(review_counts) != total:
        raise ValueError("Review count vector size must match matrix size")
    if any(len(row) != total for row in losses):
        raise ValueError("Loss matrix must be square")

    source_weight = _cluster_weight(cluster=source_cluster, review_counts=review_counts)
    source_mix_with_weights = source_weight > 0
    target_rows: list[tuple[float, int]] = []
    baseline_rows: list[tuple[float, int]] = []

    for target_idx in target_cluster:
        if target_idx < 0 or target_idx >= total:
            continue
        baseline = losses[target_idx][target_idx]
        if baseline is None:
            continue

        source_values: list[tuple[float, int]] = []
        fallback_source_values: list[float] = []
        for source_idx in source_cluster:
            if source_idx < 0 or source_idx >= total:
                continue
            source_value = losses[target_idx][source_idx]
            if source_value is None:
                continue
            source_values.append((float(source_value), int(review_counts[source_idx])))
            fallback_source_values.append(float(source_value))

        mixed_source = _weighted_average(values=source_values) if source_mix_with_weights else None
        if mixed_source is None and fallback_source_values:
            mixed_source = sum(fallback_source_values) / float(len(fallback_source_values))
        if mixed_source is None:
            continue

        target_weight = max(int(review_counts[target_idx]), 0)
        if target_weight <= 0:
            target_weight = 1
        target_rows.append((mixed_source, target_weight))
        baseline_rows.append((float(baseline), target_weight))

    mixed_target_value = _weighted_average(values=target_rows)
    baseline_target_value = _weighted_average(values=baseline_rows)
    if mixed_target_value is None or baseline_target_value is None:
        return None
    return mixed_target_value - baseline_target_value


def cluster_symmetric_merge_score(
    *,
    losses: Sequence[Sequence[float | None]],
    review_counts: Sequence[int],
    left_cluster: Sequence[int],
    right_cluster: Sequence[int],
) -> float | None:
    left_delta = cluster_directed_delta(
        losses=losses,
        review_counts=review_counts,
        target_cluster=left_cluster,
        source_cluster=right_cluster,
    )
    right_delta = cluster_directed_delta(
        losses=losses,
        review_counts=review_counts,
        target_cluster=right_cluster,
        source_cluster=left_cluster,
    )
    if left_delta is None or right_delta is None:
        return None

    left_weight = _cluster_weight(cluster=left_cluster, review_counts=review_counts)
    right_weight = _cluster_weight(cluster=right_cluster, review_counts=review_counts)
    if left_weight <= 0 and right_weight <= 0:
        left_weight = len(left_cluster)
        right_weight = len(right_cluster)
    total_weight = left_weight + right_weight
    if total_weight <= 0:
        return None
    return (
        float(left_delta) * left_weight + float(right_delta) * right_weight
    ) / float(total_weight)


def cluster_logloss_groups_agglomerative(
    *,
    losses: Sequence[Sequence[float | None]],
    review_counts: Sequence[int],
    threshold: float,
) -> list[list[int]]:
    total = len(losses)
    if len(review_counts) != total:
        raise ValueError("Review count vector size must match matrix size")
    if any(len(row) != total for row in losses):
        raise ValueError("Loss matrix must be square")

    clusters: list[list[int]] = [[idx] for idx in range(total)]

    while len(clusters) > 1:
        best_pair: tuple[int, int] | None = None
        best_score: float | None = None
        for left_idx in range(len(clusters)):
            for right_idx in range(left_idx + 1, len(clusters)):
                score = cluster_symmetric_merge_score(
                    losses=losses,
                    review_counts=review_counts,
                    left_cluster=clusters[left_idx],
                    right_cluster=clusters[right_idx],
                )
                if score is None or float(score) > float(threshold):
                    continue
                if best_score is None or float(score) < float(best_score):
                    best_score = float(score)
                    best_pair = (left_idx, right_idx)
                    continue
                if float(score) == float(best_score):
                    left_key = tuple(sorted(clusters[left_idx]))
                    right_key = tuple(sorted(clusters[right_idx]))
                    current_key = (left_key, right_key)
                    assert best_pair is not None
                    best_left_key = tuple(sorted(clusters[best_pair[0]]))
                    best_right_key = tuple(sorted(clusters[best_pair[1]]))
                    best_key = (best_left_key, best_right_key)
                    if current_key < best_key:
                        best_pair = (left_idx, right_idx)

        if best_pair is None:
            break

        left_idx, right_idx = best_pair
        merged = sorted(set(clusters[left_idx]) | set(clusters[right_idx]))
        clusters[left_idx] = merged
        del clusters[right_idx]

    clusters.sort(key=lambda group: (group[0], len(group)))
    return clusters


def mergeable_pair_count(
    *,
    score_matrix: Sequence[Sequence[float | None]],
    threshold: float,
) -> int:
    total = len(score_matrix)
    if any(len(row) != total for row in score_matrix):
        raise ValueError("Score matrix must be square")

    count = 0
    for left_idx in range(total):
        for right_idx in range(left_idx + 1, total):
            value: Optional[float] = score_matrix[left_idx][right_idx]
            if value is not None and float(value) <= float(threshold):
                count += 1
    return count


def align_group_indexes_by_overlap(
    *,
    left_groups: Sequence[Sequence[int]],
    right_groups: Sequence[Sequence[int]],
) -> list[tuple[int | None, int | None]]:
    left_sets = [set(int(v) for v in group) for group in left_groups]
    right_sets = [set(int(v) for v in group) for group in right_groups]

    candidates: list[tuple[int, int, int, int, int]] = []
    for left_idx, left_set in enumerate(left_sets):
        for right_idx, right_set in enumerate(right_sets):
            overlap = len(left_set & right_set)
            min_size = min(len(left_set), len(right_set))
            size_gap = abs(len(left_set) - len(right_set))
            candidates.append((overlap, min_size, -size_gap, left_idx, right_idx))

    candidates.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3], item[4]))

    aligned: list[tuple[int | None, int | None]] = []
    used_left: set[int] = set()
    used_right: set[int] = set()
    for overlap, _min_size, _neg_gap, left_idx, right_idx in candidates:
        if overlap <= 0:
            continue
        if left_idx in used_left or right_idx in used_right:
            continue
        aligned.append((left_idx, right_idx))
        used_left.add(left_idx)
        used_right.add(right_idx)

    for left_idx in range(len(left_groups)):
        if left_idx not in used_left:
            aligned.append((left_idx, None))
    for right_idx in range(len(right_groups)):
        if right_idx not in used_right:
            aligned.append((None, right_idx))

    return aligned
