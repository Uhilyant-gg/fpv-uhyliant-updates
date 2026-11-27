"""Named per-vehicle settings presets: create, rename, copy, delete, import/export.

Stored as one atomic JSON file. A corrupt store is reported and never
overwritten. Exported presets are standalone files that can be imported on
another station; imports are fully validated and always get a fresh id.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping

from station_settings import validate_station_settings

STORE_SCHEMA = "fpv-uhyliant-presets"
FILE_SCHEMA = "fpv-uhyliant-preset"
VERSION = 1
MAX_PRESETS = 50
MAX_NAME_LENGTH = 60
MAX_FILE_BYTES = 256 * 1024


class PresetError(Exception):
    """Raised with a stable reason code."""


def clean_name(name: Any) -> str:
    if not isinstance(name, str):
        raise PresetError("preset-name-invalid")
    cleaned = " ".join("".join(ch for ch in name if ch.isprintable()).split())
    if not cleaned or len(cleaned) > MAX_NAME_LENGTH:
        raise PresetError("preset-name-invalid")
    return cleaned


def _unique_name(name: str, taken: set[str]) -> str:
    if name.casefold() not in taken:
        return name
    for n in range(2, MAX_PRESETS + 2):
        candidate = f"{name} ({n})"[:MAX_NAME_LENGTH]
        if candidate.casefold() not in taken:
            return candidate
    raise PresetError("preset-limit-reached")


class PresetStore:
    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)

    # -- persistence ------------------------------------------------------------
    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"active": None, "presets": []}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            raise PresetError("preset-store-invalid") from None
        if not isinstance(raw, dict) or raw.get("schema") != STORE_SCHEMA or raw.get("version") != VERSION:
            raise PresetError("preset-store-invalid")
        return validate_state(raw)

    def replace_state(self, state: Any) -> dict[str, Any]:
        """Replace every preset (backup restore); validated before anything is written."""
        try:
            valid = validate_state(state)
        except PresetError:
            raise PresetError("preset-settings-invalid") from None
        self._write(valid)
        return valid

    def _write(self, state: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema": STORE_SCHEMA, "version": VERSION, "active": state["active"], "presets": state["presets"]}
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    @staticmethod
    def _find(state: Mapping[str, Any], preset_id: str) -> dict[str, Any]:
        for preset in state["presets"]:
            if preset["id"] == preset_id:
                return preset
        raise PresetError("preset-not-found")

    def _add(self, state: dict[str, Any], name: str, settings: Any) -> dict[str, Any]:
        if len(state["presets"]) >= MAX_PRESETS:
            raise PresetError("preset-limit-reached")
        try:
            settings = validate_station_settings(settings)
        except ValueError:
            raise PresetError("preset-settings-invalid") from None
        taken = {p["name"].casefold() for p in state["presets"]}
        preset = {"id": uuid.uuid4().hex, "name": _unique_name(clean_name(name), taken), "settings": settings}
        state["presets"].append(preset)
        return preset

    # -- operations ---------------------------------------------------------------
    def create(self, name: str, settings: Any, activate: bool = True) -> dict[str, Any]:
        state = self.load()
        preset = self._add(state, name, settings)
        if activate:
            state["active"] = preset["id"]
        self._write(state)
        return preset

    def save_settings(self, preset_id: str, settings: Any) -> dict[str, Any]:
        state = self.load()
        preset = self._find(state, preset_id)
        try:
            preset["settings"] = validate_station_settings(settings)
        except ValueError:
            raise PresetError("preset-settings-invalid") from None
        self._write(state)
        return preset

    def rename(self, preset_id: str, name: str) -> dict[str, Any]:
        state = self.load()
        preset = self._find(state, preset_id)
        cleaned = clean_name(name)
        taken = {p["name"].casefold() for p in state["presets"] if p["id"] != preset_id}
        if cleaned.casefold() in taken:
            raise PresetError("preset-name-taken")
        preset["name"] = cleaned
        self._write(state)
        return preset

    def duplicate(self, preset_id: str) -> dict[str, Any]:
        state = self.load()
        source = self._find(state, preset_id)
        preset = self._add(state, f"{source['name']} (копія)"[:MAX_NAME_LENGTH], source["settings"])
        self._write(state)
        return preset

    def delete(self, preset_id: str) -> None:
        state = self.load()
        self._find(state, preset_id)
        state["presets"] = [p for p in state["presets"] if p["id"] != preset_id]
        if state["active"] == preset_id:
            state["active"] = None
        self._write(state)

    def activate(self, preset_id: str) -> dict[str, Any]:
        state = self.load()
        preset = self._find(state, preset_id)
        state["active"] = preset_id
        self._write(state)
        return preset

    def export(self, preset_id: str, path: str | os.PathLike[str]) -> None:
        preset = self._find(self.load(), preset_id)
        payload = {"schema": FILE_SCHEMA, "version": VERSION, "name": preset["name"], "settings": preset["settings"]}
        target = Path(path)
        tmp = target.with_suffix(target.suffix + ".tmp")
        try:
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, target)
        except OSError:
            raise PresetError("preset-export-failed") from None

    def import_file(self, path: str | os.PathLike[str]) -> dict[str, Any]:
        source = Path(path)
        try:
            if source.stat().st_size > MAX_FILE_BYTES:
                raise PresetError("preset-file-invalid")
            raw = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            raise PresetError("preset-file-invalid") from None
        if not isinstance(raw, dict) or raw.get("schema") != FILE_SCHEMA or raw.get("version") != VERSION:
            raise PresetError("preset-file-invalid")
        state = self.load()
        try:
            preset = self._add(state, raw.get("name"), raw.get("settings"))
        except PresetError as exc:
            raise PresetError(
                "preset-file-invalid" if str(exc) in {"preset-name-invalid", "preset-settings-invalid"} else str(exc)
            ) from None
        self._write(state)
        return preset


def validate_state(raw: Any) -> dict[str, Any]:
    """Validate {"active", "presets"} (store file or backup) or raise preset-store-invalid."""
    if not isinstance(raw, Mapping) or not isinstance(raw.get("presets"), list) or len(raw["presets"]) > MAX_PRESETS:
        raise PresetError("preset-store-invalid")
    presets, ids = [], set()
    for item in raw["presets"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or item["id"] in ids:
            raise PresetError("preset-store-invalid")
        try:
            presets.append(
                {
                    "id": item["id"],
                    "name": clean_name(item.get("name")),
                    "settings": validate_station_settings(item.get("settings")),
                }
            )
        except (PresetError, ValueError):
            raise PresetError("preset-store-invalid") from None
        ids.add(item["id"])
    active = raw.get("active")
    return {"active": active if active in ids else None, "presets": presets}
