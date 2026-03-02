from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aqt import mw


def as_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def field(obj: Any, name: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name, None)


def field_any(obj: Any, names: Sequence[str]) -> Any:
    for name in names:
        value = field(obj, name)
        if value is not None:
            return value
    return None


def config_name(conf_id: int, config: Any) -> str:
    name = field(config, "name")
    return str(name) if isinstance(name, str) and name else f"Preset {conf_id}"


def deck_entries() -> list[tuple[int, str]]:
    entries = []
    for item in mw.col.decks.all_names_and_ids():
        if isinstance(item, Mapping):
            deck_id = int(item["id"])
            name = str(item["name"])
        else:
            deck_id = int(getattr(item, "id"))
            name = str(getattr(item, "name"))
        entries.append((deck_id, name))
    return entries


def config_from_conf_id(conf_id: int) -> Any:
    getter_names = ["get_config", "get_config_dict", "dconf_for_update_dict", "getconf"]
    for getter_name in getter_names:
        getter = getattr(mw.col.decks, getter_name, None)
        if getter is None:
            continue
        try:
            value = getter(conf_id)
        except Exception:
            continue
        if value is not None:
            return value
    return None


def config_for_deck(deck_id: int) -> Any:
    by_deck = getattr(mw.col.decks, "config_dict_for_deck_id", None)
    if by_deck is not None:
        try:
            value = by_deck(deck_id)
            if value is not None:
                return value
        except Exception:
            pass

    deck = mw.col.decks.get(deck_id)
    conf_id = field_any(deck, ("conf", "config_id"))
    if isinstance(conf_id, int):
        return config_from_conf_id(conf_id)

    return None


def _normalize_config(config: Any, fallback_id: Any = None) -> tuple[int, str, Any] | None:
    conf_id = as_int(field(config, "id"))
    if conf_id is None:
        conf_id = as_int(fallback_id)
    if conf_id is None:
        return None
    conf_name = config_name(conf_id, config)
    return conf_id, conf_name, config


def all_preset_configs() -> list[tuple[int, str, Any]]:
    seen: dict[int, tuple[str, Any]] = {}

    getter_names = (
        "all_config",
        "all_configs",
        "all_config_dict",
        "all_config_dicts",
        "all_confs",
    )
    for getter_name in getter_names:
        getter = getattr(mw.col.decks, getter_name, None)
        if getter is None:
            continue
        try:
            raw = getter()
        except Exception:
            continue

        if isinstance(raw, Mapping):
            entries = list(raw.items())
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
            entries = [(None, config) for config in raw]
        else:
            continue

        for key, config in entries:
            normalized = _normalize_config(config, fallback_id=key)
            if normalized is None:
                continue
            conf_id, conf_name, conf_obj = normalized
            seen[conf_id] = (conf_name, conf_obj)

    if seen:
        return sorted((conf_id, item[0], item[1]) for conf_id, item in seen.items())

    # Fallback for older API shapes: gather presets referenced by decks.
    for deck_id, _ in deck_entries():
        deck = mw.col.decks.get(deck_id)
        conf_id = as_int(field_any(deck, ("conf", "config_id")))
        if conf_id is None:
            continue
        if conf_id in seen:
            continue

        config = config_from_conf_id(conf_id)
        if config is None:
            continue
        name = config_name(conf_id, config)
        seen[conf_id] = (name, config)

    return sorted((conf_id, item[0], item[1]) for conf_id, item in seen.items())


def current_preset_assignments(deck_ids: Sequence[int]) -> dict[int, int]:
    assignments: dict[int, int] = {}
    for deck_id in deck_ids:
        try:
            deck = mw.col.decks.get(deck_id)
        except Exception:
            continue
        conf_id = as_int(field_any(deck, ("conf", "config_id")))
        if conf_id is not None:
            assignments[int(deck_id)] = conf_id
    return assignments


def apply_preset_assignments(assignments: Mapping[int, int]) -> tuple[int, int]:
    changed = 0
    failed = 0
    setter = getattr(mw.col.decks, "set_config_id_for_deck_dict", None)
    for deck_id, preset_id in assignments.items():
        try:
            deck = mw.col.decks.get(deck_id)
            if not deck:
                failed += 1
                continue

            current_preset = as_int(field_any(deck, ("conf", "config_id")))
            if current_preset == preset_id:
                continue

            if setter is not None:
                setter(deck, preset_id)
            else:
                if isinstance(deck, Mapping):
                    deck["conf"] = preset_id
                else:
                    setattr(deck, "conf", preset_id)
                mw.col.decks.save(deck)
            changed += 1
        except Exception:
            failed += 1

    try:
        mw.reset()
    except Exception:
        pass
    return changed, failed
