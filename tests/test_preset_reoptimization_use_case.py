from fsrs_merge_advisor.use_cases.preset_reoptimization import (
    changed_preset_deck_groups_for_reoptimization,
    preset_optimization_summary_message,
)


def test_changed_preset_deck_groups_for_reoptimization_includes_changed_reused_preset():
    groups = changed_preset_deck_groups_for_reoptimization(
        before_assignments={101: 1, 102: 2},
        after_target_assignments={101: 1, 102: 1},
        target_by_deck={101: 1, 102: 1},
        candidate_preset_ids=[1],
        all_current_assignments={101: 1, 102: 1, 103: 1},
    )
    assert groups == [(1, [101, 102, 103])]


def test_changed_preset_deck_groups_for_reoptimization_excludes_unchanged_presets():
    groups = changed_preset_deck_groups_for_reoptimization(
        before_assignments={101: 1, 102: 1},
        after_target_assignments={101: 1, 102: 1},
        target_by_deck={101: 1, 102: 1},
        candidate_preset_ids=[1],
        all_current_assignments={101: 1, 102: 1},
    )
    assert groups == []


def test_preset_optimization_summary_message_includes_all_counters_and_cancelled():
    message = preset_optimization_summary_message(
        optimized=2,
        no_data=1,
        invalid_params=3,
        failed=4,
        cancelled=True,
    )
    assert "Optimized presets: 2" in message
    assert "Skipped (no FSRS items): 1" in message
    assert "Skipped (non-FSRS6 params): 3" in message
    assert "Failed: 4" in message
    assert "Cancelled before completion." in message
