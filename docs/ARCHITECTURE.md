# Architecture

## Runtime flow (deck-computed mode)

1. Menu action `FSRS Deck Proximity (Computed)` calls `_show_deck_computed_results()`.
2. User chooses scope (leaf only vs include middle/root).
3. `_load_computed_deck_profiles()` loops selected decks:
   - review-count-based cache check,
   - compute params via backend `compute_fsrs_params` when cache miss,
   - keep only FSRS6-valid profiles.
4. `pairwise_distance_matrix()` computes distances.
5. Similarity groups are built with `similarity_groups_from_matrix(..., min_group_size=1)`.
6. Group editor dialog `_show_similarity_groups()` opens as primary view.

## Runtime flow (preset mode)

1. Menu action `FSRS Preset Proximity` calls `_show_preset_results()`.
2. `_load_profiles()` extracts FSRS params from existing deck presets.
3. `_show_results_for_profiles()` renders table + matrix UI.

## Distance stack

- `extract_fsrs_weights()` -> `transform_params_for_distance()` ->
  `get_validated_fsrs6_inverse_covariance()` -> `mahalanobis_distance()`.
- `get_validated_fsrs6_inverse_covariance()` validates vector shape and returns the shipped matrix.

## Grouping model

- Grouping uses complete-link style merge:
  - clusters merge only if *all cross-pairs* are below threshold.
- Therefore, each final group should satisfy:
  - every pairwise distance inside group `< threshold`.

## Persistence model

- Deck param cache and preset backup each use:
  - preferred profile-folder path,
  - fallback legacy addon-folder path.
- On successful read from legacy path, data is re-saved to preferred path.
- Runtime diagnostics are written to `fsrs_preset_advisor.log` in the Anki
  profile folder, falling back to the add-on folder when the profile folder is
  unavailable. The log is rotated and records optimization API calls, parameter
  counts, skip reasons, and update failures without card IDs or card contents.

## First-review split data changes

- `FSRS Split Deck by First Review` reads cards from the selected deck and its
  descendants, then moves reviewed cards into four child decks named with Anki's
  `::` delimiter, for example `A::A - Easy`.
- Each child deck receives its own advisor-created first-review preset. After
  moving cards and assigning presets, the user is prompted to optimize those
  first-review split presets, with `Yes` selected by default.
- First-review split presets are cloned from the source preset when newly
  created, then their FSRS optimization and evaluation search filters are reset
  (`paramSearch` and auxiliary `fsrsEvaluationSearch`) so Anki falls back to the
  new preset's own default `preset:"..." -is:suspended` scope.
- Preset optimization writes FSRS params back to the matching config slot:
  FSRS6 uses `fsrsParams6`, while FSRS7-capable Anki builds use `fsrsParams7`
  when the selected preset version is FSRS7.
- On FSRS7-capable Anki builds, preset optimization reads the deck config
  auxiliary data key `fsrs7IncludeSameDayOptimize` and passes it to Anki's
  optimizer as `include_same_day_reviews`, matching the deck-options UI toggle.
  The reader accepts both legacy config dictionaries and newer nested
  `config.other` payloads. When the selected version field is absent, a
  34-parameter final `fsrsParams7` payload or legacy-preview 35-parameter
  `fsrsParams7` payload is treated as FSRS7 for this toggle. The
  field defaults to `true` when the key is absent and is omitted for FSRS6 or
  upstream builds that do not expose the newer optimizer fields.
- `FSRS Merge Back First Review Split` moves cards from those child decks back
  to the selected base deck. Empty first-review child decks are deleted with
  Anki's deck removal API, then the add-on asks Anki to reset the UI so the deck
  browser refreshes like it does after Anki's delete-deck button. The related
  first-review presets are detected when no deck uses them anymore, but deleting
  presets is offered as a separate confirmation because Anki treats deck-config
  deletion as a schema change that can require a full upload.

## Main code anchors

- UI/actions/orchestration: `fsrs_merge_advisor/addon.py`
- Distance analysis: `fsrs_merge_advisor/analyzer.py`
- Math core: `fsrs_merge_advisor/distance.py`
- Constants/matrix: `fsrs_merge_advisor/reference_covariance.py`
- Utility helpers: `fsrs_merge_advisor/deck_tools.py`
