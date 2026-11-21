import math
import threading
import time
from PySide6.QtCore import QObject, Property, QSettings, QThread, Signal, Slot
from pymavlink import mavutil


DEFAULT_ENDPOINT = "udpin:0.0.0.0:14550"


def _num(value, scale=1.0, invalid=None):
    if value is None or value == invalid:
        return None
    try:
        return float(value) / scale
    except (TypeError, ValueError):
        return None


def _distance_m(a, b):
    if not a or not b:
        return None
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371000.0 * 2 * math.atan2(math.sqrt(h), math.sqrt(max(0.0, 1.0 - h)))


class MavlinkWorker(QThread):
    telemetry = Signal(object)
    failed = Signal(str)

    def __init__(self, endpoint, baud):
        super().__init__()
        self.endpoint = endpoint
        self.baud = baud
        self._stop = threading.Event()
        self._master = None
        self._data = {}
        self._home = None
        self._position = None
        self._last_heartbeat = 0.0

    def stop(self):
        self._stop.set()
        master = self._master
        if master is not None:
            try:
                master.close()
            except Exception:
                pass

    def _emit(self, **values):
        self._data.update(values)
        connected = self._last_heartbeat > 0 and time.monotonic() - self._last_heartbeat < 3.0
        self._data["connected"] = connected
        self.telemetry.emit(dict(self._data))

    def _handle(self, msg):
        kind = msg.get_type()
        if kind == "BAD_DATA":
            return
        if kind == "HEARTBEAT":
            self._last_heartbeat = time.monotonic()
            armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            try:
                mode = mavutil.mode_string_v10(msg)
            except Exception:
                mode = "UNKNOWN"
            self._emit(armed=armed, flightMode=mode, heartbeat=True)
        elif kind == "SYS_STATUS":
            self._emit(
                batteryVoltage=_num(msg.voltage_battery, 1000.0, 65535),
                current=_num(msg.current_battery, 100.0, -1),
                batteryRemaining=_num(msg.battery_remaining, 1.0, -1),
            )
        elif kind == "BATTERY_STATUS":
            voltage = None
            cells = getattr(msg, "voltages", None) or []
            valid = [v for v in cells if 0 < v < 65535]
            if valid:
                voltage = sum(valid) / 1000.0
            self._emit(
                batteryVoltage=voltage if voltage is not None else self._data.get("batteryVoltage"),
                current=_num(getattr(msg, "current_battery", None), 100.0, -1),
                batteryRemaining=_num(getattr(msg, "battery_remaining", None), 1.0, -1),
            )
        elif kind == "GPS_RAW_INT":
            fix = int(getattr(msg, "fix_type", 0))
            sats = int(getattr(msg, "satellites_visible", 0))
            eph = getattr(msg, "eph", 65535)
            self._emit(gpsFix=fix, satellites=None if sats == 255 else sats, hdop=None if eph == 65535 else eph / 100.0)
        elif kind == "GLOBAL_POSITION_INT":
            lat, lon = msg.lat / 1e7, msg.lon / 1e7
            self._position = (lat, lon)
            hdg = getattr(msg, "hdg", 65535)
            self._emit(
                altitude=msg.relative_alt / 1000.0,
                heading=None if hdg == 65535 else hdg / 100.0,
                homeDistance=_distance_m(self._home, self._position),
            )
        elif kind == "VFR_HUD":
            self._emit(groundSpeed=float(msg.groundspeed), heading=float(msg.heading), altitude=float(msg.alt))
        elif kind == "ATTITUDE":
            self._emit(
                roll=math.degrees(msg.roll), pitch=math.degrees(msg.pitch), yaw=math.degrees(msg.yaw)
            )
        elif kind == "RADIO_STATUS":
            self._emit(rssi=int(msg.rssi) if getattr(msg, "rssi", 255) != 255 else None)
        elif kind == "RC_CHANNELS":
            self._emit(rssi=int(msg.rssi) if getattr(msg, "rssi", 255) != 255 else None)
        elif kind == "HOME_POSITION":
            self._home = (msg.latitude / 1e7, msg.longitude / 1e7)
            self._emit(homeDistance=_distance_m(self._home, self._position))

    def run(self):
        try:
            kwargs = {"autoreconnect": True, "robust_parsing": True}
            if not self.endpoint.startswith(("udp", "tcp")):
                kwargs["baud"] = self.baud
            self._master = mavutil.mavlink_connection(self.endpoint, **kwargs)
            self._emit(connected=False, heartbeat=False)
            while not self._stop.is_set():
                msg = self._master.recv_match(blocking=True, timeout=0.25)
                if msg is not None:
                    self._handle(msg)
                elif self._last_heartbeat and time.monotonic() - self._last_heartbeat >= 3.0:
                    self._emit(connected=False, heartbeat=False)
        except Exception as exc:
            if not self._stop.is_set():
                self.failed.emit(str(exc))
        finally:
            if self._master is not None:
                try:
                    self._master.close()
                except Exception:
                    pass
            self._master = None


class MavlinkRuntime(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        settings = QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        self._endpoint = str(settings.value("mavlink/endpoint", DEFAULT_ENDPOINT))
        self._baud = int(settings.value("mavlink/baud", 115200))
        self._enabled = str(settings.value("mavlink/enabled", "true")).lower() not in ("0", "false")
        self._worker = None
        self._error = ""
        self._telemetry = {"connected": False, "heartbeat": False}
        if self._enabled:
            self.start()

    @Property(str, notify=changed)
    def endpoint(self): return self._endpoint

    @Property(int, notify=changed)
    def baud(self): return self._baud

    @Property(bool, notify=changed)
    def enabled(self): return self._enabled

    @Property(bool, notify=changed)
    def running(self): return self._worker is not None and self._worker.isRunning()

    @Property(str, notify=changed)
    def error(self): return self._error

    @Property("QVariantMap", notify=changed)
    def telemetry(self): return self._telemetry

    @Slot(str, int, bool)
    def configure(self, endpoint, baud, enabled):
        endpoint = endpoint.strip()
        if not endpoint:
            self._error = "MAVLink endpoint не може бути порожнім"
            self.changed.emit()
            return
        self.stop()
        self._endpoint = endpoint
        self._baud = max(1200, min(int(baud), 4000000))
        self._enabled = bool(enabled)
        settings = QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        settings.setValue("mavlink/endpoint", self._endpoint)
        settings.setValue("mavlink/baud", self._baud)
        settings.setValue("mavlink/enabled", self._enabled)
        self._error = ""
        self.changed.emit()
        if self._enabled:
            self.start()

    @Slot()
    def start(self):
        if self._worker is not None and self._worker.isRunning():
            return
        self._error = ""
        self._worker = MavlinkWorker(self._endpoint, self._baud)
        self._worker.telemetry.connect(self._on_telemetry)
        self._worker.failed.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
        self.changed.emit()

    @Slot()
    def stop(self):
        worker = self._worker
        if worker is None:
            return
        worker.stop()
        worker.wait(1500)
        self._worker = None
        self._telemetry = {"connected": False, "heartbeat": False}
        self.changed.emit()

    @Slot(object)
    def _on_telemetry(self, values):
        self._telemetry = dict(values)
        self.changed.emit()

    @Slot(str)
    def _on_error(self, error):
        self._error = error
        self.changed.emit()

    @Slot()
    def _on_finished(self):
        worker = self.sender()
        if worker is self._worker:
            self._worker = None
        if worker:
            worker.deleteLater()
        self.changed.emit()

    def shutdown(self):
        self.stop()
