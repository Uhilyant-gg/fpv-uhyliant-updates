"""Additional video windows over the flight video: up to three, opened by the pilot.

The pilot presses "+" on a stream to see it in a window and "−" to close it; a
closed stream is stopped, so it spends no bitrate. The station never opens or
moves windows by itself; it only remembers the pilot's last arrangement for the
"open as last time" button. Places and sizes are kept as fractions of the
flight area, so they survive a window resize.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from video import VideoRuntime

MAX_WINDOWS = 3
DEFAULT_WIDTH = 0.3
MIN_WIDTH, MAX_WIDTH = 0.12, 0.7


def _clamp(value, low, high):
    return max(low, min(high, float(value)))


class ExtraWindowsRuntime(QObject):
    changed = Signal()

    def __init__(self, devices, workspace, store_path: Path, host_resolver=None, runtime_factory=None):
        super().__init__()
        self._devices = devices
        self._workspace = workspace
        self._path = Path(store_path)
        factory = runtime_factory or (lambda: VideoRuntime(devices))
        self._runtimes = [factory() for _ in range(MAX_WINDOWS)]
        for runtime in self._runtimes:
            if host_resolver is not None:
                runtime.host_resolver = host_resolver
            runtime.changed.connect(self.changed)
        self._slots = [self._empty() for _ in range(MAX_WINDOWS)]
        self._last_used = -1
        for signal_name in ("changed", "streamsChanged"):
            signal = getattr(devices, signal_name, None)
            if signal is not None:
                signal.connect(self._camera_changed)
        if hasattr(workspace, "changed"):
            workspace.changed.connect(self.changed)
        self._camera = getattr(devices, "activeId", "")

    @staticmethod
    def _empty():
        return {
            "open": False,
            "streamId": "",
            "x": 0.0,
            "y": 0.0,
            "w": DEFAULT_WIDTH,
            "fullscreen": False,
            "detached": False,
        }

    # --- what QML shows -------------------------------------------------------
    def _streams(self):
        return [s for s in getattr(self._devices, "activeStreams", []) if s.get("enabled", True)]

    def _primary_id(self):
        return (getattr(self._workspace, "state", {}) or {}).get("primaryId", "")

    @Property("QVariantList", notify=changed)
    def windows(self):
        names = {s.get("id"): s.get("name", "") for s in self._streams()}
        out = []
        for index, (slot, runtime) in enumerate(zip(self._slots, self._runtimes)):
            out.append(
                {
                    **slot,
                    "index": index,
                    "name": names.get(slot["streamId"], ""),
                    "url": runtime.url if slot["open"] else "",
                    "state": runtime.state if slot["open"] else "stopped",
                }
            )
        return out

    @Property("QVariantList", notify=changed)
    def sources(self):
        """Streams of the camera in flight that can go into a window (not the main one)."""
        primary = self._primary_id()
        open_by_stream = {s["streamId"]: i for i, s in enumerate(self._slots) if s["open"]}
        return [
            {
                "id": s.get("id"),
                "name": s.get("name", ""),
                "kind": s.get("kind", ""),
                "slot": open_by_stream.get(s.get("id"), -1),
            }
            for s in self._streams()
            if s.get("id") != primary
        ]

    @Property(int, notify=changed)
    def openCount(self):
        return sum(1 for s in self._slots if s["open"])

    @Property(int, notify=changed)
    def lastUsed(self):
        return self._last_used if 0 <= self._last_used < MAX_WINDOWS and self._slots[self._last_used]["open"] else -1

    @Property(bool, notify=changed)
    def canRestore(self):
        return bool(self._saved()) and self.openCount == 0

    # --- actions ----------------------------------------------------------------
    @Slot(str, result=int)
    def open(self, stream_id):
        return self._open(stream_id, None)

    def _open(self, stream_id, place):
        if not stream_id or stream_id == self._primary_id():
            return -1
        for index, slot in enumerate(self._slots):
            if slot["open"] and slot["streamId"] == stream_id:
                return index
        free = next((i for i, s in enumerate(self._slots) if not s["open"]), -1)
        if free < 0:
            return -1
        if not self._runtimes[free].prepare(stream_id):
            self.changed.emit()
            return -1
        count = self.openCount
        x, y, w = place if place else (1 - DEFAULT_WIDTH - 0.01 - 0.03 * count, 0.02 + 0.06 * count, DEFAULT_WIDTH)
        self._slots[free] = {**self._empty(), "open": True, "streamId": stream_id}
        self._place(free, x, y, w)
        self._last_used = free
        self._save()
        self.changed.emit()
        return free

    @Slot(int)
    def close(self, index):
        if not 0 <= index < MAX_WINDOWS or not self._slots[index]["open"]:
            return
        self._save()  # the arrangement before closing is what "as last time" brings back
        self._runtimes[index].stop()
        self._slots[index] = self._empty()
        if self._last_used == index:
            self._last_used = next((i for i, s in enumerate(self._slots) if s["open"]), -1)
        self.changed.emit()

    @Slot()
    def closeAll(self):
        if self.openCount:
            self._save()
        for index in range(MAX_WINDOWS):
            if self._slots[index]["open"]:
                self._runtimes[index].stop()
                self._slots[index] = self._empty()
        self._last_used = -1
        self.changed.emit()

    def _place(self, index, x, y, w):
        w = _clamp(w, MIN_WIDTH, MAX_WIDTH)
        slot = self._slots[index]
        slot["w"] = w
        slot["x"] = _clamp(x, 0.0, 1.0 - w)
        slot["y"] = _clamp(y, 0.0, 0.98)

    @Slot(int, float, float, float)
    def place(self, index, x, y, w):
        """Where the pilot put the window (fractions of the flight area)."""
        if 0 <= index < MAX_WINDOWS and self._slots[index]["open"]:
            self._place(index, x, y, w)
            self._last_used = index
            self._save()
            self.changed.emit()

    @Slot(int, bool)
    def setFullscreen(self, index, on):
        if 0 <= index < MAX_WINDOWS and self._slots[index]["open"]:
            self._slots[index]["fullscreen"] = bool(on)
            self._last_used = index
            self.changed.emit()

    @Slot(int, bool)
    def setDetached(self, index, on):
        if 0 <= index < MAX_WINDOWS and self._slots[index]["open"]:
            self._slots[index]["detached"] = bool(on)
            self._slots[index]["fullscreen"] = False
            self.changed.emit()

    @Slot(int)
    def touch(self, index):
        """The pilot used this window: Tab and the controller switch go to it."""
        if 0 <= index < MAX_WINDOWS and self._slots[index]["open"]:
            self._last_used = index
            self.changed.emit()

    # --- playback bookkeeping for QML ---------------------------------------------
    @Slot(int, result=bool)
    def reconnect(self, index):
        return 0 <= index < MAX_WINDOWS and self._slots[index]["open"] and self._runtimes[index].reconnect()

    @Slot(int)
    def markPlaying(self, index):
        if 0 <= index < MAX_WINDOWS:
            self._runtimes[index].markPlaying()

    @Slot(int, str)
    def playbackError(self, index, message):
        if 0 <= index < MAX_WINDOWS:
            self._runtimes[index].playbackError(message)

    # --- "open as last time" and saved layouts -----------------------------------
    def _load(self) -> dict:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _camera_data(self, data=None) -> dict:
        data = self._load() if data is None else data
        entry = data.get(getattr(self._devices, "activeId", ""))
        if isinstance(entry, list):  # older files kept only the last arrangement
            entry = {"last": entry}
        return entry if isinstance(entry, dict) else {}

    def _write_camera(self, entry: dict):
        data = self._load()
        data[getattr(self._devices, "activeId", "")] = entry
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def _current(self):
        return [{"streamId": s["streamId"], "x": s["x"], "y": s["y"], "w": s["w"]} for s in self._slots if s["open"]]

    def _saved(self):
        last = self._camera_data().get("last")
        return last if isinstance(last, list) else []

    def _save(self):
        current = self._current()
        if not current:
            return
        entry = self._camera_data()
        entry["last"] = current
        self._write_camera(entry)

    def _open_all(self, windows) -> int:
        opened = 0
        for item in windows[:MAX_WINDOWS]:
            try:
                place = (float(item["x"]), float(item["y"]), float(item["w"]))
            except (KeyError, TypeError, ValueError):
                continue
            if self._open(str(item.get("streamId", "")), place) >= 0:
                opened += 1
        return opened

    @Slot(result=int)
    def restoreLast(self):
        """Only on the pilot's press: open the windows of the last arrangement again."""
        return self._open_all(self._saved())

    @Property("QVariantList", notify=changed)
    def layouts(self):
        """The pilot's saved arrangements of windows for this camera."""
        items = self._camera_data().get("layouts")
        if not isinstance(items, list):
            return []
        return [
            {"name": str(i.get("name", "")), "count": len(i.get("windows") or [])} for i in items if isinstance(i, dict)
        ]

    @Slot(result=int)
    def saveLayout(self):
        current = self._current()
        if not current:
            return -1
        entry = self._camera_data()
        items = entry.get("layouts") if isinstance(entry.get("layouts"), list) else []
        used = {i.get("name") for i in items if isinstance(i, dict)}
        number = 1
        while f"Розташування {number}" in used:
            number += 1
        items.append({"name": f"Розташування {number}", "windows": current})
        entry["layouts"] = items[-9:]
        self._write_camera(entry)
        self.changed.emit()
        return len(entry["layouts"]) - 1

    @Slot(int, result=int)
    def applyLayout(self, index):
        items = self._camera_data().get("layouts") or []
        if not 0 <= index < len(items):
            return 0
        self.closeAll()
        return self._open_all(items[index].get("windows") or [])

    @Slot(int)
    def deleteLayout(self, index):
        entry = self._camera_data()
        items = entry.get("layouts") or []
        if 0 <= index < len(items):
            items.pop(index)
            entry["layouts"] = items
            self._write_camera(entry)
            self.changed.emit()

    def _camera_changed(self):
        camera = getattr(self._devices, "activeId", "")
        if camera != self._camera:
            self._camera = camera
            self.closeAll()
        else:
            known = {s.get("id") for s in self._streams()}
            for index, slot in enumerate(self._slots):
                if slot["open"] and slot["streamId"] not in known:
                    self.close(index)
            self.changed.emit()
