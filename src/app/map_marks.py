"""Points the pilot marks on the map, by MGRS coordinates or by a right click.

Kept in a small JSON file, so they are there in the next flight. Each point has a short
name (1, 2, 3, ... unless the pilot gives one), its latitude/longitude and its MGRS text.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

import mgrs

MAX_MARKS = 50


class MapMarksRuntime(QObject):
    changed = Signal()

    def __init__(self, store_path: Path):
        super().__init__()
        self._path = Path(store_path)
        self._marks = self._load()
        self._message = ""

    def _load(self) -> list[dict]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        marks = []
        for item in data if isinstance(data, list) else []:
            try:
                lat, lon = float(item["lat"]), float(item["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            if -80 <= lat <= 84 and -180 <= lon <= 180:
                marks.append(
                    {"name": str(item.get("name", ""))[:20], "lat": lat, "lon": lon, "mgrs": mgrs.to_mgrs(lat, lon)}
                )
        return marks[:MAX_MARKS]

    def _save(self):
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps([{k: m[k] for k in ("name", "lat", "lon")} for m in self._marks], ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    @Property("QVariantList", notify=changed)
    def marks(self):
        return [dict(m, index=i) for i, m in enumerate(self._marks)]

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Slot(float, float, result=str)
    def mgrsOf(self, lat, lon):
        try:
            return mgrs.to_mgrs(lat, lon)
        except ValueError:
            return ""

    def _next_name(self):
        used = {m["name"] for m in self._marks}
        n = 1
        while str(n) in used:
            n += 1
        return str(n)

    def _add(self, lat, lon, name):
        if len(self._marks) >= MAX_MARKS:
            self._message = f"Можна мати до {MAX_MARKS} точок: видаліть зайві."
            self.changed.emit()
            return False
        name = (str(name or "").strip()[:20]) or self._next_name()
        self._marks.append({"name": name, "lat": lat, "lon": lon, "mgrs": mgrs.to_mgrs(lat, lon)})
        self._message = f"Точку {name} додано"
        self._save()
        self.changed.emit()
        return True

    @Slot(str, str, result=bool)
    def addMgrs(self, text, name=""):
        """A point from MGRS text the pilot typed or pasted."""
        try:
            lat, lon = mgrs.from_mgrs(text)
        except ValueError:
            self._message = "Не схоже на координати MGRS. Приклад: 36U UA 24182 91607"
            self.changed.emit()
            return False
        return self._add(lat, lon, name)

    @Slot(float, float, result=bool)
    def addAt(self, lat, lon):
        try:
            mgrs.to_mgrs(lat, lon)
        except ValueError:
            return False
        return self._add(lat, lon, "")

    @Slot(int)
    def remove(self, index):
        if 0 <= index < len(self._marks):
            del self._marks[index]
            self._message = ""
            self._save()
            self.changed.emit()
