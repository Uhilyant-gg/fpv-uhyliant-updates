"""Guided stick mapping: derive the axis -> channel mapping from observed movement.

The operator is asked to centre the sticks (throttle down), then to hold each
stick in a named direction. The channel that moved, and whether it moved
positively, is read from the frames; nothing is guessed. A step whose movement
is too small or not clearly attributable to one channel is rejected so the
operator can repeat it.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from controller_profile import CONTROL_AXES

STEPS = ("center",) + CONTROL_AXES + ("sweep",)
MIN_SWEEP_FRAMES = 3
# A moved channel must move at least this fraction of the centre magnitude
# (RC microseconds ~1500, HID axes ~32767) and clearly more than any other.
_MIN_RELATIVE_DEFLECTION = 0.05
_DOMINANCE_RATIO = 2.0

PROMPTS = {
    "center": "Відпустіть стіки в центр, газ — повністю вниз. Потім натисніть «Далі».",
    "roll": "Утримуйте правий стік ВПРАВО (крен) і натисніть «Далі».",
    "pitch": "Утримуйте правий стік ВГОРУ (тангаж) і натисніть «Далі».",
    "yaw": "Утримуйте лівий стік ВПРАВО (рискання) і натисніть «Далі».",
    "throttle": "Підніміть газ ПОВНІСТЮ ВГОРУ і натисніть «Далі».",
    "sweep": "Покрутіть обидва стіки по колу до упору кілька разів, потім натисніть «Готово».",
}


def _finite(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def detect_moved_channel(center: Sequence[float], held: Sequence[float], exclude: Sequence[int] = ()) -> dict[str, Any]:
    """Return {"channel", "reversed"} for the single channel that clearly moved."""
    if len(center) != len(held) or not center:
        raise ValueError("controller-mapping-frame-mismatch")
    if not all(_finite(v) for v in center) or not all(_finite(v) for v in held):
        raise ValueError("controller-input-invalid")
    deltas = [float(h) - float(c) for c, h in zip(center, held)]
    order = sorted(range(len(deltas)), key=lambda i: abs(deltas[i]), reverse=True)
    best = order[0]
    second = abs(deltas[order[1]]) if len(order) > 1 else 0.0
    scale = max(abs(float(v)) for v in center) or 1.0
    if abs(deltas[best]) < _MIN_RELATIVE_DEFLECTION * scale:
        raise ValueError("controller-mapping-no-movement")
    if second and abs(deltas[best]) < _DOMINANCE_RATIO * second:
        raise ValueError("controller-mapping-ambiguous-movement")
    if best in exclude:
        raise ValueError("controller-mapping-channel-reused")
    return {"channel": best, "reversed": deltas[best] < 0}


class MappingWizard:
    """Collects frames per step and produces a validated mapping."""

    def __init__(self):
        self.step = STEPS[0]
        self.center: list[float] | None = None
        self.mapping: dict[str, dict[str, Any]] = {}
        self.sweep_frames = 0

    @property
    def done(self) -> bool:
        return self.step == "done"

    @property
    def prompt(self) -> str:
        return PROMPTS.get(self.step, "")

    def observe(self, frame: Sequence[float]) -> None:
        """Feed a live frame; during the sweep step this counts calibration movement."""
        if self.step == "sweep":
            self.sweep_frames += 1

    def advance(self, frame: Sequence[float]) -> None:
        """Confirm the current step with the frame the operator is holding now."""
        if self.step == "center":
            if not frame or not all(_finite(v) for v in frame):
                raise ValueError("controller-input-invalid")
            self.center = [float(v) for v in frame]
            self.step = CONTROL_AXES[0]
            return
        if self.step in CONTROL_AXES:
            used = [entry["channel"] for entry in self.mapping.values()]
            self.mapping[self.step] = detect_moved_channel(self.center or [], frame, used)
            index = CONTROL_AXES.index(self.step)
            self.step = CONTROL_AXES[index + 1] if index + 1 < len(CONTROL_AXES) else "sweep"
            return
        if self.step == "sweep":
            if self.sweep_frames < MIN_SWEEP_FRAMES:
                raise ValueError("controller-calibration-samples-insufficient")
            self.step = "done"
            return
        raise ValueError("controller-calibration-not-started")
