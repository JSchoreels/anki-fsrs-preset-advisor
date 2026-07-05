import pytest

from fsrs_merge_advisor.use_cases.evaluate_mergeability import (
    align_group_indexes_by_overlap,
    can_reuse_evaluate_cached_logloss,
    cluster_directed_delta,
    cluster_logloss_groups_agglomerative,
    cluster_symmetric_merge_score,
    directed_delta_matrix,
    evaluate_logloss_cache_key,
    mergeable_pair_count,
    params_signature,
    symmetric_merge_score_matrix,
    weighted_bidirectional_delta,
)


def test_weighted_bidirectional_delta_returns_weighted_average_difference():
    value = weighted_bidirectional_delta(
        target_self_loss=0.100,
        target_with_source_loss=0.103,
        source_self_loss=0.090,
        source_with_target_loss=0.094,
        target_reviews=300,
        source_reviews=100,
    )
    assert value == pytest.approx(0.00325)


def test_params_signature_stable_for_equivalent_float_representations():
    assert params_signature([1.0, 2.5]) == params_signature([1, 2.5000000000])


def test_evaluate_logloss_cache_key_varies_by_scope_deck_and_params():
    key_a = evaluate_logloss_cache_key(
        target_deck_id=10,
        include_children=False,
        source_params=[1.0, 2.0],
    )
    key_b = evaluate_logloss_cache_key(
        target_deck_id=10,
        include_children=True,
        source_params=[1.0, 2.0],
    )
    key_c = evaluate_logloss_cache_key(
        target_deck_id=11,
        include_children=False,
        source_params=[1.0, 2.0],
    )
    key_d = evaluate_logloss_cache_key(
        target_deck_id=10,
        include_children=False,
        source_params=[1.0, 3.0],
    )
    assert key_a != key_b
    assert key_a != key_c
    assert key_a != key_d


def test_can_reuse_evaluate_cached_logloss_requires_same_review_count_and_value():
    assert can_reuse_evaluate_cached_logloss(
        cached_review_count=100,
        current_review_count=100,
        cached_log_loss=0.123,
    )
    assert not can_reuse_evaluate_cached_logloss(
        cached_review_count=100,
        current_review_count=101,
        cached_log_loss=0.123,
    )
    assert not can_reuse_evaluate_cached_logloss(
        cached_review_count=100,
        current_review_count=100,
        cached_log_loss=None,
    )


def test_weighted_bidirectional_delta_requires_inputs_and_non_zero_weight():
    assert (
        weighted_bidirectional_delta(
            target_self_loss=None,
            target_with_source_loss=0.2,
            source_self_loss=0.1,
            source_with_target_loss=0.2,
            target_reviews=1,
            source_reviews=1,
        )
        is None
    )
    assert (
        weighted_bidirectional_delta(
            target_self_loss=0.1,
            target_with_source_loss=0.2,
            source_self_loss=0.1,
            source_with_target_loss=0.2,
            target_reviews=0,
            source_reviews=0,
        )
        is None
    )


def test_directed_delta_matrix_computes_cross_minus_self():
    losses = [
        [0.10, 0.11, None],
        [0.12, 0.09, 0.10],
        [0.15, None, 0.14],
    ]
    matrix = directed_delta_matrix(losses=losses)
    assert matrix[0][0] == 0.0
    assert matrix[0][1] == pytest.approx(0.01)
    assert matrix[0][2] is None
    assert matrix[1][0] == pytest.approx(0.03)
    assert matrix[1][1] == 0.0
    assert matrix[1][2] == pytest.approx(0.01)
    assert matrix[2][0] == pytest.approx(0.01)
    assert matrix[2][1] is None
    assert matrix[2][2] == 0.0


def test_symmetric_merge_score_matrix_uses_bidirectional_weighted_delta():
    losses = [
        [0.100, 0.103, 0.110],
        [0.094, 0.090, 0.100],
        [0.120, 0.110, 0.105],
    ]
    reviews = [300, 100, 200]

    matrix = symmetric_merge_score_matrix(losses=losses, review_counts=reviews)

    assert matrix[0][0] == 0.0
    assert matrix[1][1] == 0.0
    assert matrix[2][2] == 0.0
    assert matrix[0][1] == pytest.approx(0.00325)
    assert matrix[1][0] == pytest.approx(0.00325)
    assert matrix[0][2] == pytest.approx(0.012)
    assert matrix[2][0] == pytest.approx(0.012)


def test_symmetric_merge_score_matrix_validates_shape():
    with pytest.raises(ValueError, match="Review count vector size"):
        symmetric_merge_score_matrix(losses=[[0.1]], review_counts=[])
    with pytest.raises(ValueError, match="square"):
        symmetric_merge_score_matrix(losses=[[0.1, 0.2]], review_counts=[1])


def test_cluster_directed_delta_uses_weighted_target_average_for_merged_cluster():
    losses = [
        [0.100, 0.1002, 0.1060],
        [0.1002, 0.100, 0.1010],
        [0.1040, 0.1010, 0.100],
    ]
    reviews = [100, 900, 100]

    delta = cluster_directed_delta(
        losses=losses,
        review_counts=reviews,
        target_cluster=[0, 1],
        source_cluster=[2],
    )

    # (100 * (0.1060 - 0.100) + 900 * (0.1010 - 0.100)) / 1000
    assert delta == pytest.approx(0.0015)


def test_cluster_symmetric_merge_score_matches_weighted_bidirectional_cluster_delta():
    losses = [
        [0.100, 0.1002, 0.1060],
        [0.1002, 0.100, 0.1010],
        [0.1040, 0.1010, 0.100],
    ]
    reviews = [100, 900, 100]

    score = cluster_symmetric_merge_score(
        losses=losses,
        review_counts=reviews,
        left_cluster=[0, 1],
        right_cluster=[2],
    )

    assert score == pytest.approx(0.0014818181818)


def test_cluster_logloss_groups_agglomerative_merges_using_cluster_scores():
    losses = [
        [0.100, 0.1002, 0.1060],
        [0.1002, 0.100, 0.1010],
        [0.1040, 0.1010, 0.100],
    ]
    reviews = [100, 900, 100]

    groups = cluster_logloss_groups_agglomerative(
        losses=losses,
        review_counts=reviews,
        threshold=0.002,
    )

    assert groups == [[0, 1, 2]]


def test_mergeable_pair_count_counts_values_under_or_equal_threshold():
    matrix = [
        [0.0, 0.003, 0.004],
        [0.003, 0.0, None],
        [0.004, None, 0.0],
    ]
    assert mergeable_pair_count(score_matrix=matrix, threshold=0.003) == 1


def test_align_group_indexes_by_overlap_prefers_largest_shared_groups():
    aligned = align_group_indexes_by_overlap(
        left_groups=[[0, 1, 2], [3, 4], [5]],
        right_groups=[[3, 4, 6], [0, 1], [7]],
    )
    assert aligned[0] == (0, 1)
    assert aligned[1] == (1, 0)


def test_align_group_indexes_by_overlap_keeps_unmatched_groups():
    aligned = align_group_indexes_by_overlap(
        left_groups=[[0], [1]],
        right_groups=[[2]],
    )
    assert (0, None) in aligned
    assert (1, None) in aligned
    assert (None, 0) in aligned
