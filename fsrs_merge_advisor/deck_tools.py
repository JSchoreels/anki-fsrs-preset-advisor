from __future__ import annotations

from .tools.assignment_changes import (
    changed_target_preset_ids_from_assignments,
    deck_ids_grouped_by_target_preset,
)
from .tools.cache import can_reuse_cached_params
from .tools.deck_scope import descendant_deck_ids, leaf_deck_entries
from .tools.fsrs_payload import (
    fsrs_version_for_config_payload,
    include_same_day_reviews_for_optimize_from_config_payload,
    is_supported_fsrs_params,
    reset_fsrs_search_filters_on_config_payload,
    selected_fsrs_params_from_config_payload,
    set_fsrs_params_on_config_payload,
)
from .tools.grouping import (
    grouped_names_by_label,
    max_distance_to_group_for_item,
    max_pairwise_distance_for_group,
    recommended_group_preset_name,
    similar_items_below_threshold,
    similarity_groups_from_matrix,
    unique_name,
)
from .tools.progress_messages import (
    optimization_progress_message,
    preset_optimization_progress_message,
)
from .tools.relearning import count_relearning_steps_in_day
from .tools.search_queries import build_deck_search_query, build_multi_deck_search_query

__all__ = [
    "build_deck_search_query",
    "build_multi_deck_search_query",
    "can_reuse_cached_params",
    "changed_target_preset_ids_from_assignments",
    "count_relearning_steps_in_day",
    "deck_ids_grouped_by_target_preset",
    "descendant_deck_ids",
    "fsrs_version_for_config_payload",
    "grouped_names_by_label",
    "include_same_day_reviews_for_optimize_from_config_payload",
    "is_supported_fsrs_params",
    "leaf_deck_entries",
    "max_distance_to_group_for_item",
    "max_pairwise_distance_for_group",
    "optimization_progress_message",
    "preset_optimization_progress_message",
    "recommended_group_preset_name",
    "reset_fsrs_search_filters_on_config_payload",
    "selected_fsrs_params_from_config_payload",
    "set_fsrs_params_on_config_payload",
    "similar_items_below_threshold",
    "similarity_groups_from_matrix",
    "unique_name",
]
