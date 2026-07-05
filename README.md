# FSRS Preset Advisor

**Always make a recent Anki backup before using this add-on. Some features can change deck assignments, create or delete presets, move cards between decks, and update FSRS preset parameters.**

FSRS Preset Advisor is an Anki add-on that helps you inspect, compare, and reorganize FSRS presets across your decks.

It is intended for users who maintain several decks or subdecks and want help deciding which decks can share an FSRS preset, which presets look different enough to keep separate, and which advisor-created presets can be cleaned up later.

## What it does

The add-on adds several actions to Anki's `Tools` menu:

- `FSRS Preset Proximity`
  - Compares the FSRS parameters already saved on your existing presets.
  - Shows pairwise distances between presets.
  - Marks presets whose parameters are close enough to be considered similar.

- `FSRS Deck Proximity (Computed)`
  - Computes FSRS parameters per deck scope, then compares decks by those computed parameters.
  - Defaults to leaf decks only.
  - Can optionally include middle and root decks.
  - Opens a grouping editor where you can compare current preset assignments with recommended similarity groups.

- `FSRS Mergeability (Evaluate)`
  - Computes deck parameters and evaluates whether decks can share parameters using log loss comparisons.
  - Shows current preset groups, Mahalanobis-distance groups, and log-loss-based groups side by side.
  - Lets you apply one of the suggested splits to new or reused advisor presets.

- `FSRS Split Deck by First Review`
  - Splits cards from a selected deck into `Again`, `Hard`, `Good`, and `Easy` target decks based on the card's first review rating.
  - Creates or reuses matching advisor presets for those target decks.
  - Leaves cards without a first review, or with an unexpected first rating, unchanged.

- `FSRS Merge Back First Review Split`
  - Moves cards from the `Again`, `Hard`, `Good`, and `Easy` split decks back into the selected base deck.
  - Deletes empty split decks when possible.

- `FSRS Cleanup Empty Advisor Presets`
  - Finds presets created by this add-on that are no longer assigned to any deck.
  - Asks for confirmation before deleting them.

## How recommendations work

The main proximity workflow compares FSRS6 parameter vectors with a Mahalanobis distance model.

Only FSRS6-style parameter sets with 21 values are compared. Presets or computed deck parameters with a different shape are treated as not valid for the FSRS6 comparison.

The default shared-preset threshold is `3.8`. In the deck-computed grouping editor, you can adjust the threshold with a slider and see the recommended groups update.

Recommended groups use a conservative complete-link style rule: a group is only recommended when every pair inside the group is below the selected threshold.

## Changing presets and decks

Some screens are read-only comparison tools, while others can change your collection.

The add-on may:

- assign decks to existing presets,
- create advisor presets named like `FSRS Preset Advisor : Group X`,
- create first-review split decks,
- move cards between decks,
- delete empty advisor-created presets after confirmation,
- optimize FSRS parameters for advisor presets when you confirm that action.

Before using actions that move cards or reassign presets, make sure you have a recent Anki backup.

## Stored files

The add-on stores small helper files in the active Anki profile folder when possible:

- `deck_params_cache.json`
  - caches computed deck parameters and reuses them when the review count has not changed.

- `evaluate_logloss_cache.json`
  - caches mergeability log-loss evaluations when the relevant review count has not changed.

- `deck_preset_backup.json`
  - stores preset assignments so advisor-driven preset changes can be reverted from inside the add-on.

Older versions may have stored these files in the add-on folder. When legacy files are read successfully, the add-on migrates the data to the preferred profile-folder location.

## Installation

If you have a packaged release, install the `.ankiaddon` file through Anki:

1. Open Anki.
2. Go to `Tools` -> `Add-ons`.
3. Choose `Install from file...`.
4. Select `dist/anki-fsrs-preset-advisor.ankiaddon`.
5. Restart Anki.

This add-on expects an Anki version with FSRS support and the optimizer APIs used by current Anki releases.

## Development

Useful commands:

```bash
pytest -q
./copy_to_anki.sh
./package_ankiaddon.sh
```

Additional technical notes are in `docs/README.md`, `docs/ARCHITECTURE.md`, and `docs/HANDOFF.md`.

## License

MIT License. See `LICENSE`.
