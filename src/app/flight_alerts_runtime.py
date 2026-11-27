"""Qt bridge: active in-flight alerts from live telemetry and the station thresholds."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal

from flight_alerts import evaluate_alerts


class FlightAlertsRuntime(QObject):
    changed = Signal()

    def __init__(self, telemetry, station):
        super().__init__()
        self._telemetry = telemetry
        self._station = station
        self._alerts: list[dict[str, str]] = []
        telemetry.changed.connect(self.refresh)
        station.changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        alerts = evaluate_alerts(self._telemetry.telemetry, self._station.alertThresholds)
        if alerts != self._alerts:
            self._alerts = alerts
            self.changed.emit()

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
