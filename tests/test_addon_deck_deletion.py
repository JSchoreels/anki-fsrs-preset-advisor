from __future__ import annotations

import importlib
import sys
import types


class _DummyQtWidget:
    def __init__(self, *args, **kwargs) -> None:
        self._cancelled = False
        pass

    def __getattr__(self, _name: str):
        return lambda *_args, **_kwargs: None

    def wasCanceled(self) -> bool:
        return self._cancelled


class _FakeInputDialog:
    next_item: tuple[str, bool] = ("", False)

    @classmethod
    def getItem(cls, *_args, **_kwargs):
        return cls.next_item


class _FakeMessageBox:
    StandardButton = types.SimpleNamespace(Yes=1, No=2)
    next_answer = StandardButton.No
    calls: list[dict[str, object]] = []

    @classmethod
    def question(cls, *args, **_kwargs):
        cls.calls.append({"title": args[1], "text": args[2]})
        return cls.next_answer


class _FakeDeckManager:
    def __init__(self, deck_ids: set[int]) -> None:
        self.deck_ids = set(deck_ids)
        self.configs: dict[int, dict[str, object]] = {}
        self.remove_calls: list[list[int]] = []
        self.rem_called = False
        self.updated_configs: list[dict[str, object]] = []

    def get(self, did: int, default: bool = True):
        if int(did) in self.deck_ids:
            return {"id": int(did)}
        if default:
            return {"id": 1}
        return None

    def remove(self, dids: list[int]) -> None:
        self.remove_calls.append([int(did) for did in dids])
        for did in dids:
            self.deck_ids.discard(int(did))

    def rem(self, *_args, **_kwargs) -> None:
        self.rem_called = True

    def update_config(self, config: dict[str, object]) -> None:
        self.updated_configs.append(dict(config))

    def get_config(self, conf_id: int):
        return self.configs.get(int(conf_id))


class _FakeBackend:
    def __init__(
        self,
        *,
        reject_fsrs_version: bool = False,
        reject_include_same_day_reviews: bool = False,
    ) -> None:
        self.reject_fsrs_version = reject_fsrs_version
        self.reject_include_same_day_reviews = reject_include_same_day_reviews
        self.calls: list[dict[str, object]] = []

    def compute_fsrs_params(self, **kwargs):
        self.calls.append(dict(kwargs))
        if self.reject_fsrs_version and "fsrs_version" in kwargs:
            raise TypeError("unexpected keyword argument 'fsrs_version'")
        if (
            self.reject_include_same_day_reviews
            and "include_same_day_reviews" in kwargs
        ):
            raise TypeError("unexpected keyword argument 'include_same_day_reviews'")
        return types.SimpleNamespace(params=[1.0] * 35, fsrs_items=401)


class _FakeMessageBackend:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def compute_fsrs_params(self, message):
        self.calls.append(message)
        return types.SimpleNamespace(params=[4.0] * 35, fsrs_items=402)


class _FakeComputeFsrsParamsRequest:
    def __init__(self) -> None:
        self.search = ""
        self.current_params: list[float] = []
        self.ignore_revlogs_before_ms = -1
        self.num_of_relearning_steps = 0
        self.health_check = True
        self.include_same_day_reviews = True
        self.fsrs_version = 99


def _install_fake_aqt(
    monkeypatch,
    deck_manager: _FakeDeckManager,
    backend: _FakeBackend | None = None,
) -> None:
    reset_calls: list[bool] = []
    fake_mw = types.SimpleNamespace()
    fake_mw.reset_calls = reset_calls
    fake_mw.reset = lambda _unused_arg=False: reset_calls.append(True)
    fake_mw.app = types.SimpleNamespace(processEvents=lambda: None)
    fake_mw.col = types.SimpleNamespace(decks=deck_manager, _backend=backend)
    fake_aqt = types.ModuleType("aqt")
    fake_aqt.mw = fake_mw

    fake_qt = types.ModuleType("aqt.qt")
    for name in [
        "QAbstractItemView",
        "QAction",
        "QColor",
        "QComboBox",
        "QDialog",
        "QGroupBox",
        "QHBoxLayout",
        "QLabel",
        "QListWidget",
        "QListWidgetItem",
        "QProgressDialog",
        "QPushButton",
        "QScrollArea",
        "QSlider",
        "QTableWidget",
        "QTableWidgetItem",
        "QVBoxLayout",
        "QWidget",
    ]:
        setattr(fake_qt, name, _DummyQtWidget)
    fake_qt.QInputDialog = _FakeInputDialog
    fake_qt.QMessageBox = _FakeMessageBox
    fake_qt.Qt = types.SimpleNamespace()

    fake_utils = types.ModuleType("aqt.utils")
    fake_utils.showInfo = lambda *_args, **_kwargs: None
    fake_utils.showWarning = lambda *_args, **_kwargs: None

    monkeypatch.setitem(sys.modules, "aqt", fake_aqt)
    monkeypatch.setitem(sys.modules, "aqt.qt", fake_qt)
    monkeypatch.setitem(sys.modules, "aqt.utils", fake_utils)


def _import_addon_with_fake_aqt(
    monkeypatch,
    deck_manager: _FakeDeckManager,
    backend: _FakeBackend | None = None,
):
    _install_fake_aqt(monkeypatch, deck_manager, backend)
    _FakeInputDialog.next_item = ("", False)
    _FakeMessageBox.next_answer = _FakeMessageBox.StandardButton.No
    _FakeMessageBox.calls.clear()
    sys.modules.pop("fsrs_merge_advisor.addon", None)
    sys.modules.pop("fsrs_merge_advisor.infra.decks_gateway", None)
    return importlib.import_module("fsrs_merge_advisor.addon")


def test_deck_exists_does_not_treat_default_deck_as_requested_deck(monkeypatch):
    addon = _import_addon_with_fake_aqt(monkeypatch, _FakeDeckManager({123}))

    assert addon._deck_exists(123) is True
    assert addon._deck_exists(999) is False


def test_delete_deck_uses_current_remove_api_without_deprecated_rem(monkeypatch):
    deck_manager = _FakeDeckManager({123})
    addon = _import_addon_with_fake_aqt(monkeypatch, deck_manager)

    assert addon._delete_deck_by_id(123) is True
    assert deck_manager.remove_calls == [[123]]
    assert deck_manager.rem_called is False
    assert addon._deck_exists(123) is False


def test_compute_fsrs_params_passes_fsrs_version_when_backend_accepts_it(monkeypatch):
    backend = _FakeBackend()
    addon = _import_addon_with_fake_aqt(monkeypatch, _FakeDeckManager(set()), backend)

    params, fsrs_items = addon._compute_fsrs_params_for_deck(
        search="deck:Example",
        current_params=tuple([2.0] * 35),
        num_of_relearning_steps=1,
        fsrs_version=0,
        include_same_day_reviews=False,
    )

    assert params == tuple([1.0] * 35)
    assert fsrs_items == 401
    assert backend.calls[0]["fsrs_version"] == 0
    assert backend.calls[0]["include_same_day_reviews"] is False


def test_compute_fsrs_params_falls_back_for_upstream_backend_without_fsrs7_fields(
    monkeypatch,
):
    backend = _FakeBackend(
        reject_fsrs_version=True,
        reject_include_same_day_reviews=True,
    )
    addon = _import_addon_with_fake_aqt(monkeypatch, _FakeDeckManager(set()), backend)

    params, fsrs_items = addon._compute_fsrs_params_for_deck(
        search="deck:Example",
        current_params=tuple([2.0] * 21),
        num_of_relearning_steps=1,
        fsrs_version=0,
        include_same_day_reviews=False,
    )

    assert params == tuple([1.0] * 35)
    assert fsrs_items == 401
    assert "fsrs_version" in backend.calls[0]
    assert "include_same_day_reviews" in backend.calls[0]
    assert "include_same_day_reviews" not in backend.calls[1]
    assert "fsrs_version" in backend.calls[1]
    assert "fsrs_version" not in backend.calls[2]


def test_compute_fsrs_params_supports_message_style_generated_backend(monkeypatch):
    fake_anki = types.ModuleType("anki")
    fake_scheduler_pb2 = types.ModuleType("anki.scheduler_pb2")
    fake_scheduler_pb2.ComputeFsrsParamsRequest = _FakeComputeFsrsParamsRequest
    fake_anki.scheduler_pb2 = fake_scheduler_pb2
    monkeypatch.setitem(sys.modules, "anki", fake_anki)
    monkeypatch.setitem(sys.modules, "anki.scheduler_pb2", fake_scheduler_pb2)
    backend = _FakeMessageBackend()
    addon = _import_addon_with_fake_aqt(monkeypatch, _FakeDeckManager(set()), backend)

    params, fsrs_items = addon._compute_fsrs_params_for_deck(
        search="deck:Example",
        current_params=tuple([2.0] * 35),
        num_of_relearning_steps=1,
        fsrs_version=0,
        include_same_day_reviews=False,
    )

    assert params == tuple([4.0] * 35)
    assert fsrs_items == 402
    request = backend.calls[0]
    assert request.search == "deck:Example"
    assert request.current_params == [2.0] * 35
    assert request.ignore_revlogs_before_ms == 0
    assert request.num_of_relearning_steps == 1
    assert request.health_check is False
    assert request.include_same_day_reviews is False
    assert request.fsrs_version == 0


def test_optimize_preset_configs_logs_unsupported_params(monkeypatch):
    deck_manager = _FakeDeckManager(set())
    addon = _import_addon_with_fake_aqt(monkeypatch, deck_manager)
    warnings: list[str] = []
    monkeypatch.setattr(addon, "_log_info", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        addon,
        "_log_warning",
        lambda message, *args: warnings.append(message % args),
    )
    monkeypatch.setattr(addon, "_config_from_conf_id", lambda _conf_id: {"id": 10, "name": "Preset"})
    monkeypatch.setattr(addon, "_config_name", lambda _conf_id, _config: "Preset")
    monkeypatch.setattr(addon, "build_multi_deck_search_query", lambda _deck_ids: "deck:Preset")
    monkeypatch.setattr(
        addon,
        "_compute_fsrs_params_for_deck",
        lambda **_kwargs: (tuple([1.0] * 20), 401),
    )

    optimized, no_data, invalid_params, failed, cancelled = addon._optimize_preset_configs(
        [(10, [123])]
    )

    assert (optimized, no_data, invalid_params, failed, cancelled) == (0, 0, 1, 0, False)
    assert deck_manager.updated_configs == []
    assert any("unsupported params" in warning for warning in warnings)


def test_optimize_preset_configs_passes_fsrs7_same_day_toggle(monkeypatch):
    deck_manager = _FakeDeckManager(set())
    addon = _import_addon_with_fake_aqt(monkeypatch, deck_manager)
    compute_calls: list[dict[str, object]] = []
    monkeypatch.setattr(addon, "_log_info", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(addon, "_config_from_conf_id", lambda _conf_id: {
        "id": 10,
        "name": "Preset",
        "fsrsVersion": 0,
        "fsrsParams7": [2.0] * 35,
        "other": {"fsrs7IncludeSameDayOptimize": False},
    })
    monkeypatch.setattr(addon, "_config_name", lambda _conf_id, _config: "Preset")
    monkeypatch.setattr(addon, "build_multi_deck_search_query", lambda _deck_ids: "deck:Preset")

    def compute(**kwargs):
        compute_calls.append(dict(kwargs))
        return tuple([3.0] * 35), 401

    monkeypatch.setattr(addon, "_compute_fsrs_params_for_deck", compute)

    optimized, no_data, invalid_params, failed, cancelled = addon._optimize_preset_configs(
        [(10, [123])]
    )

    assert (optimized, no_data, invalid_params, failed, cancelled) == (1, 0, 0, 0, False)
    assert compute_calls[0]["fsrs_version"] == 0
    assert compute_calls[0]["include_same_day_reviews"] is False
    assert deck_manager.updated_configs[0]["fsrsParams7"] == [3.0] * 35


def test_reset_preset_search_filters_resets_new_split_preset_scope(monkeypatch):
    deck_manager = _FakeDeckManager(set())
    deck_manager.configs[10] = {
        "id": 10,
        "name": "Parent Clone",
        "paramSearch": 'preset:"Parent"',
        "other": {"fsrsEvaluationSearch": 'preset:"Parent" is:review'},
    }
    addon = _import_addon_with_fake_aqt(monkeypatch, deck_manager)

    assert addon._reset_preset_search_filters(10, "Split Preset") is True

    assert deck_manager.updated_configs == [
        {
            "id": 10,
            "name": "Split Preset",
            "paramSearch": "",
            "other": {"fsrsEvaluationSearch": ""},
        }
    ]


def test_merge_back_does_not_delete_unused_presets_without_full_sync_confirmation(
    monkeypatch,
):
    addon = _import_addon_with_fake_aqt(monkeypatch, _FakeDeckManager(set()))
    base_name = "Base"
    split_names = addon.target_deck_names_for_first_review_split(base_name)
    split_preset_names = addon.target_preset_names_for_first_review_split(base_name)
    entries = [(1, base_name)] + [
        (deck_id, split_names[rating])
        for deck_id, (rating, _label) in enumerate(addon.FIRST_REVIEW_RATINGS, start=2)
    ]
    deleted_decks: list[int] = []
    deleted_presets: list[int] = []
    infos: list[str] = []

    _FakeInputDialog.next_item = (base_name, True)
    _FakeMessageBox.next_answer = _FakeMessageBox.StandardButton.No
    monkeypatch.setattr(addon, "_deck_entries", lambda: list(entries))
    monkeypatch.setattr(addon, "_card_ids_for_decks", lambda _deck_ids: [])
    monkeypatch.setattr(addon, "_delete_deck_by_id", lambda deck_id: deleted_decks.append(deck_id) or True)
    monkeypatch.setattr(
        addon,
        "_all_preset_configs",
        lambda: [
            (preset_id, split_preset_names[rating], {})
            for preset_id, (rating, _label) in enumerate(addon.FIRST_REVIEW_RATINGS, start=20)
        ],
    )
    monkeypatch.setattr(addon, "_current_preset_assignments", lambda _deck_ids: {})
    monkeypatch.setattr(addon, "_delete_preset_by_id", lambda preset_id: deleted_presets.append(preset_id) or True)
    monkeypatch.setattr(addon, "showInfo", lambda message: infos.append(message))

    addon._merge_back_first_review_split()

    assert deleted_decks == [2, 3, 4, 5]
    assert deleted_presets == []
    assert len(addon.mw.reset_calls) == 1
    assert _FakeMessageBox.calls == [
        {
            "title": "Delete Unused Split Presets?",
            "text": (
                "Found 4 unused first-review split preset(s).\n\n"
                "Deleting deck presets is treated by Anki as a schema change and can "
                "require a full upload on next sync.\n\n"
                "Delete these unused presets now?"
            ),
        }
    ]
    assert "Kept unused split presets: 4" in infos[0]
