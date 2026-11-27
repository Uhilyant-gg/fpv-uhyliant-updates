"""Durable local storage for non-secret RC controller profiles.

Only validated calibration/mapping profiles and a display name are persisted. A
stored record is never evidence that the controller is present: restore still
requires a fresh matching observation (see ``controller_restore``).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from controller_profile import validate_controller_profile

SCHEMA = "fpv-uhyliant-controller-profiles"
VERSION = 1
_MAX_RECORDS = 32
_MAX_NAME_LENGTH = 64


class ControllerProfileStoreInvalid(RuntimeError):
    """The stored profile file exists but cannot be trusted."""


def _validated_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, Mapping) or set(record) != {"id", "name", "profile"}:
        raise ControllerProfileStoreInvalid("controller-profile-store-invalid")
    controller_id, name = record["id"], record["name"]
    if not isinstance(controller_id, str) or not controller_id.strip():
        raise ControllerProfileStoreInvalid("controller-profile-store-invalid")
    if name is not None and (not isinstance(name, str) or len(name) > _MAX_NAME_LENGTH):
        raise ControllerProfileStoreInvalid("controller-profile-store-invalid")
    try:
        profile = validate_controller_profile(record["profile"])
    except ValueError:
        raise ControllerProfileStoreInvalid("controller-profile-store-invalid") from None
    if profile["controllerId"] != controller_id:
        raise ControllerProfileStoreInvalid("controller-profile-store-invalid")
    return {"id": controller_id, "name": name, "profile": profile}


class JsonControllerProfileStore:
    """Atomic JSON store; a corrupt file is reported and never silently overwritten."""

    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)

    def load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            raise ControllerProfileStoreInvalid("controller-profile-store-invalid") from None
        if (
            not isinstance(raw, dict)
            or set(raw) != {"schema", "version", "records"}
            or raw["schema"] != SCHEMA
            or raw["version"] != VERSION
            or not isinstance(raw["records"], list)
            or len(raw["records"]) > _MAX_RECORDS
        ):
            raise ControllerProfileStoreInvalid("controller-profile-store-invalid")
        records: dict[str, dict[str, Any]] = {}
        for item in raw["records"]:
            record = _validated_record(item)
            if record["id"] in records:
                raise ControllerProfileStoreInvalid("controller-profile-store-invalid")
            records[record["id"]] = record
        return records

    def save_profile(self, controller_id: str, name: str | None, profile: Mapping[str, Any]) -> dict[str, Any]:
        """Validate and persist one profile, replacing an earlier one for the same identity."""
        record = _validated_record({"id": controller_id, "name": name, "profile": profile})
        records = self.load()  # raises on a corrupt file: never clobber untrusted state
        records[record["id"]] = record
        if len(records) > _MAX_RECORDS:
            raise ControllerProfileStoreInvalid("controller-profile-store-full")
        self._write(records)
        return record

    def forget(self, controller_id: str) -> bool:
        records = self.load()
        if records.pop(controller_id, None) is None:
            return False
        self._write(records)
        return True

    def _write(self, records: Mapping[str, Mapping[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema": SCHEMA, "version": VERSION, "records": [dict(records[k]) for k in sorted(records)]}
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)
