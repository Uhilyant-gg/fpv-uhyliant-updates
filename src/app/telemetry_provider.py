"""Normalized read-only telemetry provider boundary and provider selection."""
from PySide6.QtCore import QObject, Property, Signal, Slot

NORMALIZED_FIELDS = (
    "connected", "armed", "flightMode", "batteryVoltage", "current",
    "batteryRemaining", "gpsFix", "satellites", "hdop", "altitude",
    "groundSpeed", "heading", "homeDistance", "roll", "pitch", "yaw",
    "rssi", "health", "ages", "link",
)

class TelemetryProvider(QObject):
    changed=Signal()
    def __init__(self,name,runtime):
        super().__init__();self._name=name;self._runtime=runtime;runtime.changed.connect(self.changed)
    @Property(str,constant=True)
    def name(self):return self._name
    @Property(bool,constant=True)
    def readOnly(self):return True
    @Property("QVariantMap",notify=changed)
    def telemetry(self):
        raw=dict(self._runtime.telemetry or {});normalized={key:raw.get(key) for key in NORMALIZED_FIELDS};normalized["provider"]=self._name;return normalized
    @Property(str,notify=changed)
    def error(self):return str(self._runtime.error or "")
    @Property(bool,notify=changed)
    def available(self):return bool(self.telemetry.get("connected"))

class MavlinkProvider(TelemetryProvider):
    def __init__(self,runtime):super().__init__("MAVLink",runtime)
class MspProvider(TelemetryProvider):
    def __init__(self,runtime):super().__init__("MSP",runtime)
class CrsfProvider(TelemetryProvider):
    def __init__(self,runtime):super().__init__("CRSF",runtime)

class TelemetryRouter(QObject):
    """Stable QML/vehicle-facing provider that can switch read-only backends."""
    changed=Signal()
    def __init__(self,providers,active="MAVLink"):
        super().__init__();self._providers={p.name:p for p in providers};self._active=active if active in self._providers else next(iter(self._providers),"")
        for provider in self._providers.values():provider.changed.connect(self._provider_changed)
    @Property("QStringList",constant=True)
    def providerNames(self):return list(self._providers)
    @Property(str,notify=changed)
    def name(self):return self._active
    @Property(bool,constant=True)
    def readOnly(self):return True
    @Property("QVariantMap",notify=changed)
    def telemetry(self):
        provider=self._providers.get(self._active);return dict(provider.telemetry) if provider else {"provider":self._active,"connected":False,"health":"unavailable"}
    @Property(str,notify=changed)
    def error(self):
        provider=self._providers.get(self._active);return provider.error if provider else ""
    @Property(bool,notify=changed)
    def available(self):
        provider=self._providers.get(self._active);return bool(provider and provider.available)
    @Slot(str,result=bool)
    def select(self,name):
        if name not in self._providers:return False
        if name!=self._active:self._active=name;self.changed.emit()
        return True
    def _provider_changed(self):
        provider=self.sender()
        if provider and provider.name==self._active:self.changed.emit()
