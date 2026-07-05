from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

_FSRS_VERSION_FIELDS = ("fsrsVersion", "fsrs_version")
_FSRS7_SAME_DAY_OPTIMIZE_KEY = "fsrs7IncludeSameDayOptimize"
_FSRS7_SAME_DAY_EVALUATE_KEY = "fsrs7IncludeSameDayEvaluate"
_FSRS_EVALUATION_SEARCH_KEY = "fsrsEvaluationSearch"
_FSRS_OPTIMIZE_SEARCH_FIELDS = (
    "paramSearch",
    "param_search",
    "weightSearch",
    "weight_search",
)
_FSRS_VERSION_PARAM_KEYS: dict[int, tuple[str, ...]] = {
    0: ("fsrsParams7", "fsrs_params_7", "fsrs_params7"),
    1: ("fsrsParams6", "fsrs_params_6", "fsrs_params6"),
    2: ("fsrsParams5", "fsrs_params_5", "fsrs_params5"),
    3: ("fsrsParams4", "fsrs_params_4", "fsrs_params4"),
}
FSRS7_FINAL_PARAM_COUNT = 34
FSRS7_LEGACY_PREVIEW_PARAM_COUNT = 35
FSRS7_PARAM_COUNTS = (FSRS7_FINAL_PARAM_COUNT, FSRS7_LEGACY_PREVIEW_PARAM_COUNT)

_FSRS_VERSION_BY_PARAM_COUNT: dict[int, int] = {
    FSRS7_FINAL_PARAM_COUNT: 0,
    FSRS7_LEGACY_PREVIEW_PARAM_COUNT: 0,
    21: 1,
    19: 2,
    17: 3,
}
_FSRS_CONFIG_PARAM_KEYS = (
    "fsrsParams7",
    "fsrs_params_7",
    "fsrs_params7",
    "fsrsParams6",
    "fsrs_params_6",
    "fsrs_params6",
    "fsrsParams5",
    "fsrs_params_5",
    "fsrs_params5",
    "fsrsParams4",
    "fsrs_params_4",
    "fsrs_params4",
    "fsrsParams",
    "fsrs_params",
    "fsrsWeights",
    "fsrs_weights",
)
_LEGACY_FSRS_CONFIG_PARAM_KEYS = (
    "fsrsParams",
    "fsrs_params",
    "fsrsWeights",
    "fsrs_weights",
)


def _field(obj: Any, name: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name, None)


def _config_payloads(config_payload: Any) -> tuple[Any, ...]:
    inner = _field(config_payload, "config")
    if inner is None:
        return (config_payload,)
    return (config_payload, inner)


def _to_float_tuple(values: Any) -> tuple[float, ...] | None:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        return None
    try:
        converted = tuple(float(value) for value in values)
    except (TypeError, ValueError):
        return None
    return converted if converted else None


def _normalized_fsrs_version(value: Any) -> int | None:
    if value is None:
        return None
    try:
        version = int(value)
    except (TypeError, ValueError):
        text = str(value).upper()
        if "SEVEN" in text or text.endswith("_7"):
            return 0
        if "SIX" in text or text.endswith("_6"):
            return 1
        if "FIVE" in text or text.endswith("_5"):
            return 2
        if "FOUR" in text or text.endswith("_4"):
            return 3
        return None
    return version if version in _FSRS_VERSION_PARAM_KEYS else None


def fsrs_version_for_config_payload(config_payload: Any) -> int | None:
    for payload in _config_payloads(config_payload):
        for field_name in _FSRS_VERSION_FIELDS:
            version = _normalized_fsrs_version(_field(payload, field_name))
            if version is not None:
                return version
    return None


def selected_fsrs_params_from_config_payload(config_payload: Any) -> tuple[float, ...] | None:
    selected_version = fsrs_version_for_config_payload(config_payload)
    if selected_version is not None:
        for payload in _config_payloads(config_payload):
            for key in _FSRS_VERSION_PARAM_KEYS[selected_version]:
                params = _to_float_tuple(_field(payload, key))
                if params is not None:
                    return params

    for payload in _config_payloads(config_payload):
        for key in _FSRS_CONFIG_PARAM_KEYS:
            params = _to_float_tuple(_field(payload, key))
            if params is not None:
                return params

        fsrs_obj = _field(payload, "fsrs")
        if fsrs_obj is not None:
            for key in ("weights", "params", "parameters"):
                params = _to_float_tuple(_field(fsrs_obj, key))
                if params is not None:
                    return params

    return None


def _aux_data_from_config_payload(config_payload: Any) -> Mapping[str, Any]:
    for payload in _config_payloads(config_payload):
        aux_data: dict[str, Any] = {}
        if isinstance(payload, Mapping):
            nested = payload.get("other")
            if isinstance(nested, Mapping):
                aux_data.update(nested)
            else:
                parsed = _json_mapping(nested)
                if parsed:
                    aux_data.update(parsed)
            for key in (
                _FSRS7_SAME_DAY_OPTIMIZE_KEY,
                _FSRS7_SAME_DAY_EVALUATE_KEY,
                _FSRS_EVALUATION_SEARCH_KEY,
            ):
                if key in payload:
                    aux_data[key] = payload[key]
            if aux_data:
                return aux_data

        other = _field(payload, "other")
        if other is not None:
            parsed = _json_mapping(other)
            if parsed:
                return parsed
    return {}


def _json_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if value is None:
        return {}
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        try:
            decoded = value.decode("utf8")
        except UnicodeDecodeError:
            return {}
        value = decoded
    elif isinstance(value, Sequence) and not isinstance(value, str):
        try:
            value = bytes(int(item) for item in value).decode("utf8")
        except (TypeError, ValueError, UnicodeDecodeError):
            return {}
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, Mapping) else {}
    return {}


def _serialized_aux_data_for_config_payload(config_payload: Any, aux_data: Mapping[str, Any]) -> Any:
    other = _field(config_payload, "other")
    if isinstance(other, (bytes, bytearray)):
        return json.dumps(dict(aux_data), separators=(",", ":")).encode("utf8")
    if isinstance(other, str):
        return json.dumps(dict(aux_data), separators=(",", ":"))
    return dict(aux_data)


def include_same_day_reviews_for_optimize_from_config_payload(
    config_payload: Any,
) -> bool | None:
    fsrs_version = fsrs_version_for_config_payload(config_payload)
    selected_params = selected_fsrs_params_from_config_payload(config_payload)
    if fsrs_version is not None and fsrs_version != 0:
        return None

    aux_data = _aux_data_from_config_payload(config_payload)
    if fsrs_version is None and len(selected_params or ()) not in FSRS7_PARAM_COUNTS:
        return None
    value = aux_data.get(_FSRS7_SAME_DAY_OPTIMIZE_KEY)
    return value if isinstance(value, bool) else False


def reset_fsrs_search_filters_on_config_payload(
    config_payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(config_payload)
    for key in _FSRS_OPTIMIZE_SEARCH_FIELDS:
        if key in payload:
            payload[key] = ""

    if _FSRS_EVALUATION_SEARCH_KEY in payload:
        payload[_FSRS_EVALUATION_SEARCH_KEY] = ""

    nested = _field(config_payload, "other")
    nested_aux_data = dict(_json_mapping(nested))
    if _FSRS_EVALUATION_SEARCH_KEY in nested_aux_data:
        nested_aux_data[_FSRS_EVALUATION_SEARCH_KEY] = ""
        payload["other"] = _serialized_aux_data_for_config_payload(
            config_payload,
            nested_aux_data,
        )

    return payload


def is_supported_fsrs_params(params: Sequence[float]) -> bool:
    return len(params) in _FSRS_VERSION_BY_PARAM_COUNT


def set_fsrs_params_on_config_payload(
    *,
    config_payload: Mapping[str, Any],
    params: Sequence[float],
) -> dict[str, Any]:
    payload = dict(config_payload)
    params_list = [float(value) for value in params]
    target_version = _FSRS_VERSION_BY_PARAM_COUNT.get(len(params_list))
    target_keys = _FSRS_VERSION_PARAM_KEYS.get(target_version, ())
    updated = False

    for key in target_keys + _LEGACY_FSRS_CONFIG_PARAM_KEYS:
        if key in payload:
            payload[key] = list(params_list)
            updated = True

    if not updated and target_keys:
        payload[target_keys[0]] = list(params_list)
        updated = True

    if target_version is not None:
        for version_field in _FSRS_VERSION_FIELDS:
            if version_field in payload:
                payload[version_field] = target_version

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
