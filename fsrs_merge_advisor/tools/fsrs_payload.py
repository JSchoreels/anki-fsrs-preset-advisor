from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_FSRS_CONFIG_PARAM_KEYS = (
    "fsrsParams6",
    "fsrs_params6",
    "fsrsParams5",
    "fsrs_params5",
    "fsrsParams",
    "fsrs_params",
    "fsrsWeights",
    "fsrs_weights",
)


def set_fsrs_params_on_config_payload(
    *,
    config_payload: Mapping[str, Any],
    params: Sequence[float],
) -> dict[str, Any]:
    payload = dict(config_payload)
    params_list = [float(value) for value in params]
    updated = False

    for key in _FSRS_CONFIG_PARAM_KEYS:
        if key in payload:
            payload[key] = list(params_list)
            updated = True

    fsrs_obj = payload.get("fsrs")
    if isinstance(fsrs_obj, Mapping):
        fsrs_payload = dict(fsrs_obj)
        fsrs_updated = False
        for key in ("weights", "params", "parameters"):
            if key in fsrs_payload:
                fsrs_payload[key] = list(params_list)
                fsrs_updated = True
        if fsrs_updated:
            payload["fsrs"] = fsrs_payload
            updated = True

    if not updated:
        payload["fsrsParams6"] = list(params_list)
    return payload
