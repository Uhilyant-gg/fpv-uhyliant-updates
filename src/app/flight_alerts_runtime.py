"""Qt bridge: active in-flight alerts from live telemetry and the station thresholds."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from flight_alerts import evaluate_alerts


class FlightAlertsRuntime(QObject):
    changed = Signal()

    def __init__(self, telemetry, station):
        super().__init__()
        self._telemetry = telemetry
        self._station = station
        self._alerts: list[dict[str, str]] = []
        # "Telemetry lost" only after it was there: a drone without a flight-controller link
        # is not an emergency, and a red banner for it would hide the real ones.
        self._seen_connected = False
        telemetry.changed.connect(self.refresh)
        station.changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        telemetry = self._telemetry.telemetry or {}
        if telemetry.get("connected") is True:
            self._seen_connected = True
        alerts = evaluate_alerts(telemetry, self._station.alertThresholds)
        if not self._seen_connected:
            alerts = [a for a in alerts if a["code"] != "telemetry-lost"]
        if alerts != self._alerts:
            self._alerts = alerts
            self.changed.emit()

    @Slot()
    def resetSession(self):
        """A new flight: telemetry has to show up again before its loss is an alert."""
        self._seen_connected = False
        self.refresh()

    @Property("QVariantList", notify=changed)
    def alerts(self):
        return [dict(alert) for alert in self._alerts]

    @Property(bool, notify=changed)
    def active(self):
        return bool(self._alerts)

    @Property(str, notify=changed)
    def level(self):
        return self._alerts[0]["level"] if self._alerts else ""

    @Property(str, notify=changed)
    def text(self):
        return " · ".join(alert["text"] for alert in self._alerts)
