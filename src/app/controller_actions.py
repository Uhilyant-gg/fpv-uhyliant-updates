"""A controller switch that swaps the main and the additional video in flight.

The pilot does not pick a channel number: "Assign" waits for a switch to be
flipped and takes the channel that moved clearly while the others stayed. In
flight every change of the switch position swaps the streams, so a two- and a
three-position switch both work.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from controller_discovery import discover_controllers

POLL_MS = 50
LEARN_SECONDS = 10.0
STABLE_SAMPLES = 2  # a new position counts after it holds for this many samples


def position(value: float, low: float, high: float) -> int:
    """0, 1 or 2 along the switch's learned travel."""
    if high <= low:
        return 0
    return max(0, min(2, round((value - low) / (high - low) * 2)))


def pick_moved_channel(lows: list[float], highs: list[float]) -> int | None:
    """The channel that clearly moved while the others stayed, else None."""
    spans = [h - lo for lo, h in zip(lows, highs)]
    if not spans:
        return None
    best = max(range(len(spans)), key=lambda i: spans[i])
    scale = max(abs(lows[best]), abs(highs[best]), 1e-9)
    others = sorted(spans[:best] + spans[best + 1 :], reverse=True)
    if spans[best] < 0.25 * scale or (others and others[0] * 3 > spans[best]):
        return None
    return best


class ControllerActions(QObject):
    changed = Signal()
    swapRequested = Signal()

    def __init__(self, source, path: Path, clock=None, poll_ms=POLL_MS):
        super().__init__()
        import time

        self._source = source
        self._path = Path(path)
        self._clock = clock or time.monotonic
        self._config = self._load()
        self._active = False
        self._learning = None
        self._last = None
        self._pending = None
        self._pending_count = 0
        self._message = ""
        self._timer = QTimer(self)
        self._timer.setInterval(poll_ms)
        self._timer.timeout.connect(self.poll)

    def _load(self):
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            swap = data.get("swap")
            if isinstance(swap, dict) and isinstance(swap.get("channel"), int):
                return {"swap": {"channel": swap["channel"], "low": float(swap["low"]), "high": float(swap["high"])}}
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return {}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._config), encoding="utf-8")

    def _channels(self):
        found = discover_controllers(self._source, self._clock)
        for controller in found.get("controllers", []):
            if controller.get("connected") and controller.get("channels"):
                return controller["channels"]
        return None

    @Property(str, notify=changed)
    def swapText(self):
        swap = self._config.get("swap")
        if self._learning is not None:
            return "Перемкніть тумблер, яким міняти потоки…"
        return f"канал {swap['channel'] + 1}" if swap else "не призначено"

    @Property(bool, notify=changed)
    def learning(self):
        return self._learning is not None

    @Property(bool, notify=changed)
    def assigned(self):
        return "swap" in self._config

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Slot(bool)
    def setActive(self, active):
        """In flight the switch is watched; elsewhere only while assigning."""
        self._active = bool(active)
        self._last = None
        self._pending = None
        self._sync_timer()

    def _sync_timer(self):
        if self._active or self._learning is not None:
            self._timer.start()
        else:
            self._timer.stop()

    @Slot()
    def learnSwap(self):
        self._learning = {"started": self._clock(), "lows": None, "highs": None, "samples": 0}
        self._message = ""
        self._sync_timer()
        self.changed.emit()

    @Slot()
    def clearSwap(self):
        self._config.pop("swap", None)
        self._save()
        self._message = "Перемикання потоків пультом вимкнено"
        self.changed.emit()

    @Slot()
    def poll(self):
        channels = self._channels()
        if self._learning is not None:
            self._learn(channels)
            return
        swap = self._config.get("swap")
        if not self._active or not swap or channels is None or swap["channel"] >= len(channels):
            return
        now = position(float(channels[swap["channel"]]), swap["low"], swap["high"])
        if self._last is None:
            self._last = now
            return
        if now == self._last:
            self._pending, self._pending_count = None, 0
            return
        if now != self._pending:
            self._pending, self._pending_count = now, 1
        else:
            self._pending_count += 1
        if self._pending_count >= STABLE_SAMPLES:
            self._last, self._pending, self._pending_count = now, None, 0
            self.swapRequested.emit()

    def _learn(self, channels):
        learn = self._learning
        if self._clock() - learn["started"] > LEARN_SECONDS:
            self._learning = None
            self._message = "Тумблер не помічено. Натисніть «Призначити» і перемкніть його ще раз."
            self._sync_timer()
            self.changed.emit()
            return
        if channels is None:
            return
        values = [float(v) for v in channels]
        if learn["lows"] is None or len(learn["lows"]) != len(values):
            learn["lows"], learn["highs"] = list(values), list(values)
        learn["lows"] = [min(a, b) for a, b in zip(learn["lows"], values)]
        learn["highs"] = [max(a, b) for a, b in zip(learn["highs"], values)]
        learn["samples"] += 1
        channel = pick_moved_channel(learn["lows"], learn["highs"])
        if channel is None or learn["samples"] < 4:
            return
        self._config["swap"] = {"channel": channel, "low": learn["lows"][channel], "high": learn["highs"][channel]}
        self._save()
        self._learning = None
        self._message = f"Потоки міняє канал {channel + 1}"
        self._sync_timer()
        self.changed.emit()
