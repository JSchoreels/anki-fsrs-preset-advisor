from fsrs_merge_advisor.use_cases.preset_cleanup import (
    ADVISOR_PRESET_PREFIX,
    empty_advisor_preset_candidates,
    is_advisor_created_preset_name,
    unused_advisor_preset_candidates_by_name,
)


def test_is_advisor_created_preset_name_matches_expected_prefix():
    assert is_advisor_created_preset_name(f"{ADVISOR_PRESET_PREFIX} Mahalanobis Group 1")
    assert is_advisor_created_preset_name(f"{ADVISOR_PRESET_PREFIX} First Review : Foo - Again")
    assert not is_advisor_created_preset_name("Default")


def test_empty_advisor_preset_candidates_returns_only_unused_advisor_presets():
    presets = [
        (1, "Default"),
        (2, f"{ADVISOR_PRESET_PREFIX} Mahalanobis Group 1"),
        (3, f"{ADVISOR_PRESET_PREFIX} LogLoss Group 1"),
        (4, "Custom"),
        (5, f"{ADVISOR_PRESET_PREFIX} First Review : Deck - Easy"),
    ]
    candidates = empty_advisor_preset_candidates(
        presets=presets,
        used_preset_ids=[2, 4],
    )
    assert candidates == [
        (5, f"{ADVISOR_PRESET_PREFIX} First Review : Deck - Easy"),
        (3, f"{ADVISOR_PRESET_PREFIX} LogLoss Group 1"),
    ]


def test_unused_advisor_preset_candidates_by_name_limits_cleanup_to_named_unused_presets():
    presets = [
        (1, "Default"),
        (2, f"{ADVISOR_PRESET_PREFIX} First Review : Deck - Again"),
        (3, f"{ADVISOR_PRESET_PREFIX} First Review : Deck - Easy"),
        (4, f"{ADVISOR_PRESET_PREFIX} First Review : Other - Easy"),
    ]
    candidates = unused_advisor_preset_candidates_by_name(
        presets=presets,
        used_preset_ids=[2],
        preset_names=[
            f"{ADVISOR_PRESET_PREFIX} First Review : Deck - Again",
            f"{ADVISOR_PRESET_PREFIX} First Review : Deck - Easy",
        ],
    )
    assert candidates == [(3, f"{ADVISOR_PRESET_PREFIX} First Review : Deck - Easy")]
