from fsrs_merge_advisor.deck_tools import (
    build_deck_search_query,
    build_multi_deck_search_query,
    can_reuse_cached_params,
    changed_target_preset_ids_from_assignments,
    count_relearning_steps_in_day,
    deck_ids_grouped_by_target_preset,
    descendant_deck_ids,
    grouped_names_by_label,
    leaf_deck_entries,
    max_distance_to_group_for_item,
    max_pairwise_distance_for_group,
    optimization_progress_message,
    preset_optimization_progress_message,
    recommended_group_preset_name,
    set_fsrs_params_on_config_payload,
    similar_items_below_threshold,
    similarity_groups_from_matrix,
    unique_name,
)


def test_leaf_deck_entries_only_returns_true_leaves():
    entries = [
        (1, "Languages"),
        (2, "Languages::French"),
        (3, "Languages::French::Vocabulary"),
        (4, "Languages::Spanish"),
        (5, "Math"),
    ]

    leaves = leaf_deck_entries(entries)

    assert leaves == [
        (3, "Languages::French::Vocabulary"),
        (4, "Languages::Spanish"),
        (5, "Math"),
    ]


def test_count_relearning_steps_in_day_stops_at_24h_limit():
    assert count_relearning_steps_in_day([10, 20, 30]) == 3
    assert count_relearning_steps_in_day([1440]) == 0
    assert count_relearning_steps_in_day([1000, 300, 200, 100]) == 2


def test_build_deck_search_query_without_children_uses_did():
    assert (
        build_deck_search_query(deck_id=42, deck_name="A::B", include_children=False)
        == "did:42 -is:suspended"
    )


def test_build_deck_search_query_with_children_uses_escaped_deck_name():
    assert (
        build_deck_search_query(
            deck_id=42,
            deck_name='A::"Quoted"\\Name',
            include_children=True,
        )
        == 'deck:"A::\\"Quoted\\"\\\\Name" -is:suspended'
    )


def test_build_multi_deck_search_query_empty_after_filtering_returns_none():
    assert build_multi_deck_search_query([0, -1]) is None


def test_build_multi_deck_search_query_single_deck_uses_did_form():
    assert build_multi_deck_search_query([42]) == "did:42 -is:suspended"


def test_build_multi_deck_search_query_multiple_decks_uses_or_and_deduplicates():
    assert (
        build_multi_deck_search_query([10, 20, 10, 30])
        == "(did:10 OR did:20 OR did:30) -is:suspended"
    )


def test_descendant_deck_ids_includes_root_and_children():
    entries = [
        (1, "A"),
        (2, "A::B"),
        (3, "A::B::C"),
        (4, "X"),
    ]
    assert descendant_deck_ids(entries, "A") == [1, 2, 3]
    assert descendant_deck_ids(entries, "A::B") == [2, 3]
    assert descendant_deck_ids(entries, "X") == [4]
    assert descendant_deck_ids(entries, "Missing") == []


def test_optimization_progress_message_with_deck_name():
    assert optimization_progress_message(done=3, total=10, deck_name="Vocabulary") == (
        'Optimizing "Vocabulary"\nCompleted: 3/10\nRemaining: 7'
    )


def test_optimization_progress_message_without_deck_name():
    assert optimization_progress_message(done=10, total=10, deck_name=None) == (
        "Preparing deck optimizations...\nCompleted: 10/10\nRemaining: 0"
    )


def test_preset_optimization_progress_message_with_preset_name():
    assert preset_optimization_progress_message(done=1, total=4, preset_name="FSRS Preset A") == (
        'Optimizing preset "FSRS Preset A"\nCompleted: 1/4\nRemaining: 3'
    )


def test_preset_optimization_progress_message_without_preset_name():
    assert preset_optimization_progress_message(done=4, total=4, preset_name=None) == (
        "Preparing preset optimizations...\nCompleted: 4/4\nRemaining: 0"
    )


def test_can_reuse_cached_params_requires_same_review_count_and_params():
    assert can_reuse_cached_params(
        cached_review_count=12,
        current_review_count=12,
        cached_params=(1.0, 2.0),
    )
    assert not can_reuse_cached_params(
        cached_review_count=12,
        current_review_count=13,
        cached_params=(1.0, 2.0),
    )
    assert not can_reuse_cached_params(
        cached_review_count=12,
        current_review_count=12,
        cached_params=None,
    )


def test_similar_items_below_threshold_filters_and_sorts():
    names = ["A", "B", "C", "D"]
    row = [0.0, 2.5, 4.2, 2.5]
    assert similar_items_below_threshold(
        names=names,
        distances_row=row,
        self_index=0,
        threshold=3.8,
    ) == ["B (2.5000)", "D (2.5000)"]


def test_similar_items_below_threshold_excludes_self_none_and_boundary():
    names = ["A", "B", "C"]
    row = [0.0, None, 3.8]
    assert similar_items_below_threshold(
        names=names,
        distances_row=row,
        self_index=0,
        threshold=3.8,
    ) == []


def test_similarity_groups_from_matrix_requires_all_pairs_below_threshold():
    names = ["A", "B", "C", "D"]
    distances = [
        [0.0, 1.0, 9.0, 9.0],
        [1.0, 0.0, 2.0, 9.0],
        [9.0, 2.0, 0.0, 9.0],
        [9.0, 9.0, 9.0, 0.0],
    ]
    assert similarity_groups_from_matrix(names=names, distances=distances, threshold=3.8) == [
        ["A", "B"]
    ]


def test_similarity_groups_from_matrix_can_form_larger_all_pairs_group():
    names = ["A", "B", "C"]
    distances = [
        [0.0, 1.2, 2.0],
        [1.2, 0.0, 3.0],
        [2.0, 3.0, 0.0],
    ]
    assert similarity_groups_from_matrix(names=names, distances=distances, threshold=3.8) == [
        ["A", "B", "C"]
    ]


def test_similarity_groups_from_matrix_excludes_boundary_and_singletons():
    names = ["A", "B", "C"]
    distances = [
        [0.0, 3.8, 9.0],
        [3.8, 0.0, 9.0],
        [9.0, 9.0, 0.0],
    ]
    assert similarity_groups_from_matrix(names=names, distances=distances, threshold=3.8) == []


def test_similarity_groups_from_matrix_includes_singletons_when_requested():
    names = ["A", "B", "C"]
    distances = [
        [0.0, 9.0, 9.0],
        [9.0, 0.0, 9.0],
        [9.0, 9.0, 0.0],
    ]
    assert similarity_groups_from_matrix(
        names=names,
        distances=distances,
        threshold=3.8,
        min_group_size=1,
    ) == [["A"], ["B"], ["C"]]


def test_grouped_names_by_label_sorts_labels_and_members():
    pairs = [
        ("Preset B", "Deck 2"),
        ("Preset A", "Deck 3"),
        ("Preset B", "Deck 1"),
    ]
    assert grouped_names_by_label(pairs) == [
        ("Preset A", ["Deck 3"]),
        ("Preset B", ["Deck 1", "Deck 2"]),
    ]


def test_deck_ids_grouped_by_target_preset_filters_requested_presets():
    target_by_deck = {101: 1, 102: 2, 103: 1, 104: 3}
    assert deck_ids_grouped_by_target_preset(
        target_by_deck=target_by_deck,
        preset_ids=[1, 3, 4],
    ) == [(1, [101, 103]), (3, [104])]


def test_changed_target_preset_ids_from_assignments_detects_reused_preset_change():
    assert changed_target_preset_ids_from_assignments(
        before_assignments={101: 1, 102: 2},
        after_assignments={101: 1, 102: 1},
        target_by_deck={101: 1, 102: 1},
        candidate_preset_ids=[1],
    ) == [1]


def test_changed_target_preset_ids_from_assignments_returns_empty_when_no_change():
    assert changed_target_preset_ids_from_assignments(
        before_assignments={101: 1, 102: 1},
        after_assignments={101: 1, 102: 1},
        target_by_deck={101: 1, 102: 1},
        candidate_preset_ids=[1],
    ) == []


def test_changed_target_preset_ids_from_assignments_preserves_candidate_order():
    assert changed_target_preset_ids_from_assignments(
        before_assignments={101: 1, 102: 2, 103: 2},
        after_assignments={101: 2, 102: 2, 103: 3},
        target_by_deck={101: 2, 102: 2, 103: 3},
        candidate_preset_ids=[3, 2, 1],
    ) == [3, 2, 1]


def test_set_fsrs_params_on_config_payload_updates_existing_top_level_key():
    payload = {"id": 1, "name": "Preset A", "fsrs_weights": [1.0, 2.0]}
    updated = set_fsrs_params_on_config_payload(config_payload=payload, params=[3.0, 4.0])
    assert updated["fsrs_weights"] == [3.0, 4.0]
    assert updated["id"] == 1
    assert payload["fsrs_weights"] == [1.0, 2.0]


def test_set_fsrs_params_on_config_payload_updates_nested_fsrs_payload():
    payload = {"id": 1, "name": "Preset A", "fsrs": {"weights": [1.0], "x": 9}}
    updated = set_fsrs_params_on_config_payload(config_payload=payload, params=[7.0, 8.0])
    assert updated["fsrs"]["weights"] == [7.0, 8.0]
    assert updated["fsrs"]["x"] == 9
    assert payload["fsrs"]["weights"] == [1.0]


def test_set_fsrs_params_on_config_payload_falls_back_to_fsrs_params6():
    payload = {"id": 1, "name": "Preset A"}
    updated = set_fsrs_params_on_config_payload(config_payload=payload, params=[5.0, 6.0])
    assert updated["fsrsParams6"] == [5.0, 6.0]


def test_max_pairwise_distance_for_group():
    distances = [
        [0.0, 1.2, 3.1],
        [1.2, 0.0, 2.0],
        [3.1, 2.0, 0.0],
    ]
    assert max_pairwise_distance_for_group(group_indexes=[0, 1, 2], distances=distances) == 3.1
    assert max_pairwise_distance_for_group(group_indexes=[0], distances=distances) is None


def test_max_distance_to_group_for_item():
    distances = [
        [0.0, 1.2, 3.1],
        [1.2, 0.0, 2.0],
        [3.1, 2.0, 0.0],
    ]
    assert (
        max_distance_to_group_for_item(item_index=1, group_indexes=[0, 1, 2], distances=distances)
        == 2.0
    )
    assert (
        max_distance_to_group_for_item(item_index=0, group_indexes=[0], distances=distances)
        is None
    )


def test_recommended_group_preset_name():
    assert recommended_group_preset_name(3) == "FSRS Preset Advisor : Group 3"


def test_unique_name_appends_suffix_when_needed():
    assert unique_name("Group A", []) == "Group A"
    assert unique_name("Group A", ["Group A"]) == "Group A (2)"
    assert unique_name("Group A", ["Group A", "Group A (2)"]) == "Group A (3)"
