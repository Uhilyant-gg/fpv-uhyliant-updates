"""Qt bridge for vehicle settings presets."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from settings_presets import PresetError, PresetStore

_MESSAGES = {
    "preset-name-invalid": "Введіть назву (до 60 символів).",
    "preset-name-taken": "Пресет з такою назвою вже є.",
    "preset-limit-reached": "Досягнуто максимуму пресетів. Видаліть непотрібні.",
    "preset-not-found": "Пресет не знайдено.",
    "preset-store-invalid": "Файл пресетів пошкоджено. Зверніться до діагностики, дані не змінено.",
    "preset-file-invalid": "Файл не є коректним пресетом FPV Uhyliant.",
    "preset-export-failed": "Не вдалося зберегти файл. Перевірте доступ до вибраної папки.",
    "preset-settings-invalid": "Налаштування пресета некоректні.",
    "settings-apply-failed": "Не вдалося застосувати налаштування. Перевірте доступ до папки даних.",
}


def human_message(reason: str) -> str:
    return _MESSAGES.get(reason, "Операцію не виконано.")


def _local_path(value: str) -> str:
    url = QUrl(value)
    return url.toLocalFile() if url.isLocalFile() else value


class PresetsRuntime(QObject):
    changed = Signal()

    def __init__(self, store: PresetStore, station):
        super().__init__()
        self._store = store
        self._station = station
        self._state: dict[str, Any] = {"active": None, "presets": []}
        self._message = ""
        self._message_ok = True
        station.changed.connect(self.changed)
        self._reload()

    def _reload(self) -> bool:
        try:
            self._state = self._store.load()
            return True
        except PresetError as exc:
            self._state = {"active": None, "presets": []}
            self._set_message(str(exc), False)
            return False

    def _set_message(self, reason_or_text: str, ok: bool):
        self._message = reason_or_text if ok else human_message(reason_or_text)
        self._message_ok = ok

    def _run(self, action, success: str) -> bool:
        try:
            action()
        except PresetError as exc:
            self._set_message(str(exc), False)
            self._reload()
            self.changed.emit()
            return False
        self._reload()
        self._set_message(success, True)
        self.changed.emit()
        return True

    def _active(self) -> dict[str, Any] | None:
        return next((p for p in self._state["presets"] if p["id"] == self._state["active"]), None)

    # -- actions --------------------------------------------------------------
    @Slot(str, result=bool)
    def createPreset(self, name):
        return self._run(lambda: self._store.create(name, self._station.exportSettings()), "Пресет створено.")

    @Slot(str, result=bool)
    def selectPreset(self, preset_id):
        preset = next((p for p in self._state["presets"] if p["id"] == preset_id), None)
        if preset is None:
            self._set_message("preset-not-found", False)
            self.changed.emit()
            return False
        if not self._station.applySettings(preset["settings"]):
            self._set_message("settings-apply-failed", False)
            self.changed.emit()
            return False
        return self._run(lambda: self._store.activate(preset_id), f"Застосовано пресет «{preset['name']}».")

    @Slot(result=bool)
    def saveToActive(self):
        active = self._active()
        if active is None:
            self._set_message("preset-not-found", False)
            self.changed.emit()
            return False
        return self._run(
            lambda: self._store.save_settings(active["id"], self._station.exportSettings()),
            "Налаштування збережено в пресет.",
        )

    @Slot(str, str, result=bool)
    def renamePreset(self, preset_id, name):
        return self._run(lambda: self._store.rename(preset_id, name), "Пресет перейменовано.")

    @Slot(str, result=bool)
    def duplicatePreset(self, preset_id):
        return self._run(lambda: self._store.duplicate(preset_id), "Копію пресета створено.")

    @Slot(str, result=bool)
    def deletePreset(self, preset_id):
        return self._run(lambda: self._store.delete(preset_id), "Пресет видалено.")

    @Slot(str, str, result=bool)
    def exportPreset(self, preset_id, target):
        return self._run(lambda: self._store.export(preset_id, _local_path(target)), "Пресет експортовано у файл.")

    @Slot(str, result=bool)
    def importPreset(self, source):
        return self._run(
            lambda: self._store.import_file(_local_path(source)), "Пресет імпортовано. Виберіть його, щоб застосувати."
        )

    # -- properties -----------------------------------------------------------
    @Property("QVariantList", notify=changed)
    def presets(self):
        active = self._state["active"]
        return [{"id": p["id"], "name": p["name"], "active": p["id"] == active} for p in self._state["presets"]]

    @Property(str, notify=changed)
    def activeName(self):
        active = self._active()
        return active["name"] if active else ""

    @Property(bool, notify=changed)
    def dirty(self):
        active = self._active()
        return active is not None and active["settings"] != self._station.exportSettings()

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Property(bool, notify=changed)
    def messageOk(self):
        return self._message_ok
