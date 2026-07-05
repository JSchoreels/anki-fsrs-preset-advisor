from fsrs_merge_advisor.use_cases.first_review_split import (
    FIRST_REVIEW_PRESET_PREFIX,
    FIRST_REVIEW_RATINGS,
    FIRST_REVIEW_SPLIT_SUFFIXES,
    child_deck_name_for_first_review_split,
    is_first_review_split_deck_name,
    normalize_card_ids_from_single_column_rows,
    split_card_ids_by_first_review,
    target_deck_names_for_first_review_split,
    target_preset_names_for_first_review_split,
)


def test_target_deck_names_for_first_review_split_uses_expected_suffixes():
    names = target_deck_names_for_first_review_split("Spanish")
    assert names == {
        1: "Spanish::Spanish - Again",
        2: "Spanish::Spanish - Hard",
        3: "Spanish::Spanish - Good",
        4: "Spanish::Spanish - Easy",
    }


def test_child_deck_name_for_first_review_split_keeps_nested_decks_under_source():
    assert child_deck_name_for_first_review_split("Spanish::Verbs", "Easy") == (
        "Spanish::Verbs::Verbs - Easy"
    )


def test_target_preset_names_for_first_review_split_uses_expected_prefix():
    names = target_preset_names_for_first_review_split("Spanish")
    assert names == {
        1: f"{FIRST_REVIEW_PRESET_PREFIX} : Spanish - Again",
        2: f"{FIRST_REVIEW_PRESET_PREFIX} : Spanish - Hard",
        3: f"{FIRST_REVIEW_PRESET_PREFIX} : Spanish - Good",
        4: f"{FIRST_REVIEW_PRESET_PREFIX} : Spanish - Easy",
    }
    assert len(set(names.values())) == 4


def test_split_card_ids_by_first_review_buckets_known_ratings():
    buckets, no_first_review, unexpected = split_card_ids_by_first_review(
        card_first_ease_rows=[
            (1001, 1),
            (1002, 2),
            (1003, 3),
            (1004, 4),
        ]
    )
    assert buckets[1] == [1001]
    assert buckets[2] == [1002]
    assert buckets[3] == [1003]
    assert buckets[4] == [1004]
    assert no_first_review == 0
    assert unexpected == 0


def test_split_card_ids_by_first_review_counts_missing_and_unexpected():
    buckets, no_first_review, unexpected = split_card_ids_by_first_review(
        card_first_ease_rows=[
            (2001, None),
            (2002, 0),
            (2003, 5),
            (2004, 1),
        ]
    )
    assert buckets[1] == [2004]
    assert buckets[2] == []
    assert buckets[3] == []
    assert buckets[4] == []
    assert no_first_review == 1
    assert unexpected == 2


def test_split_card_ids_by_first_review_ignores_duplicate_card_rows():
    buckets, no_first_review, unexpected = split_card_ids_by_first_review(
        card_first_ease_rows=[
            (3001, 4),
            (3001, 1),
            (3002, None),
            (3002, 2),
        ]
    )
    assert buckets[1] == []
    assert buckets[2] == []
    assert buckets[3] == []
    assert buckets[4] == [3001]
    assert no_first_review == 1
    assert unexpected == 0
    assert len(FIRST_REVIEW_RATINGS) == 4


def test_is_first_review_split_deck_name_detects_expected_suffixes():
    assert is_first_review_split_deck_name("Spanish - Again")
    assert is_first_review_split_deck_name("Spanish::Verbs - Hard")
    assert is_first_review_split_deck_name("Foo - Good")
    assert is_first_review_split_deck_name("Foo - Easy")
    assert not is_first_review_split_deck_name("Spanish")
    assert not is_first_review_split_deck_name("Spanish - Unknown")
    assert len(FIRST_REVIEW_SPLIT_SUFFIXES) == 4


def test_normalize_card_ids_from_single_column_rows_handles_common_row_shapes():
    rows = [
        1001,
        (1002,),
        [1003],
        {"id": 1004},
        {"id": "1005"},
        {"nope": 1006},
        ("abc",),
        None,
        -5,
    ]
    assert normalize_card_ids_from_single_column_rows(rows) == [
        1001,
        1002,
        1003,
        1004,
        1005,
    ]
