"""Normalized read-only telemetry provider boundary.

Providers expose only received telemetry. Missing source fields remain None so the UI
can render them as unavailable instead of inventing values.
"""
from PySide6.QtCore import QObject, Property, Signal

NORMALIZED_FIELDS = (
    "connected", "armed", "flightMode", "batteryVoltage", "current",
    "batteryRemaining", "gpsFix", "satellites", "hdop", "altitude",
    "groundSpeed", "heading", "homeDistance", "roll", "pitch", "yaw",
    "rssi", "health", "ages", "link",
)


class TelemetryProvider(QObject):
    """Read-only adapter from a protocol runtime to normalized vehicle telemetry."""

    changed = Signal()

    def __init__(self, name, runtime):
        super().__init__()
        self._name = name
        self._runtime = runtime
        runtime.changed.connect(self.changed)

    @Property(str, constant=True)
    def name(self):
        return self._name

    @Property(bool, constant=True)
    def readOnly(self):
        return True

    @Property("QVariantMap", notify=changed)
    def telemetry(self):
        raw = dict(self._runtime.telemetry or {})
        normalized = {key: raw.get(key) for key in NORMALIZED_FIELDS}
        normalized["provider"] = self._name
        return normalized

    @Property(str, notify=changed)
    def error(self):
        return str(self._runtime.error or "")

    @Property(bool, notify=changed)
    def available(self):
        return bool(self.telemetry.get("connected"))


class MavlinkProvider(TelemetryProvider):
    def __init__(self, runtime):
        super().__init__("MAVLink", runtime)


class MspProvider(TelemetryProvider):
    """Normalized read-only provider for Betaflight/INAV MSP telemetry."""

    def __init__(self, runtime):
        super().__init__("MSP", runtime)
