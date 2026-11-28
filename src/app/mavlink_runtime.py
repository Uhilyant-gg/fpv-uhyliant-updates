import json
import math
import os
import threading
import time
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from PySide6.QtCore import QObject, Property, QSettings, QThread, Signal, Slot
from pymavlink import mavutil

DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FPV-Uhyliant"
DEFAULT_ENDPOINT = "udpin:0.0.0.0:14550"
HEARTBEAT_TIMEOUT = 3.0
PRESETS = {"UDP Listen": "udpin:0.0.0.0:14550", "UDP Out": "udpout:127.0.0.1:14550", "TCP": "tcp:127.0.0.1:5760"}
STALE_AFTER = {
    "heartbeat": 3.0,
    "battery": 5.0,
    "gps": 5.0,
    "position": 3.0,
    "attitude": 2.0,
    "radio": 5.0,
    "home": 30.0,
}
GROUP_FIELDS = {
    "heartbeat": ("armed", "flightMode"),
    "battery": ("batteryVoltage", "current", "batteryRemaining"),
    "gps": ("gpsFix", "satellites", "hdop"),
    "position": ("altitude", "groundSpeed", "heading", "homeDistance", "homeBearing", "latitude", "longitude"),
    "attitude": ("roll", "pitch", "yaw"),
    "radio": ("rssi", "rssiSource"),
    "home": (),
}


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


def _bearing_deg(frm, to):
    """Initial great-circle bearing from `frm` to `to` in degrees (0 = north), or None."""
    if not frm or not to or (frm[0] == to[0] and frm[1] == to[1]):
        return None
    lat1, lon1 = map(math.radians, frm)
    lat2, lon2 = map(math.radians, to)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def _enum_name(prefix, value):
    for name in dir(mavutil.mavlink):
        if name.startswith(prefix) and getattr(mavutil.mavlink, name) == value:
            return name[len(prefix) :]
    return str(value)


def _version(value):
    if value in (None, 0):
        return ""
    return f"{(value >> 24) & 255}.{(value >> 16) & 255}.{(value >> 8) & 255}"


class MavlinkWorker(QThread):
    telemetry = Signal(object)
    failed = Signal(str)

    def __init__(self, endpoint, baud, target_system=0, target_component=0):
        super().__init__()
        self.endpoint = endpoint
        self.baud = baud
        self.target_system = target_system
        self.target_component = target_component
        self._stop = threading.Event()
        self._master = None
        self._data = {}
        self._seen = {}
        self._field_seen = {}
        self._home = None
        self._position = None
        self._last_heartbeat = 0.0
        self._started = time.monotonic()
        self._received = 0
        self._bad = 0
        self._lost = 0
        self._last_seq = {}
        self._types = Counter()
        self._window = deque()
        self._last_packet = 0.0
        self._vehicle = None

    def stop(self):
        self._stop.set()
        if self._master is not None:
            try:
                self._master.close()
            except Exception:
                pass

    def _touch(self, group):
        self._seen[group] = time.monotonic()

    def _link(self, now):
        while self._window and now - self._window[0] > 5.0:
            self._window.popleft()
        total = self._received + self._lost
        loss = (100.0 * self._lost / total) if total else 0.0
        return {
            "messagesReceived": self._received,
            "packetsLost": self._lost,
            "packetLossPercent": loss,
            "badData": self._bad,
            "messageRate": len(self._window) / 5.0,
            "lastPacketAge": None if not self._last_packet else now - self._last_packet,
            "uptime": now - self._started,
            "messageTypes": dict(self._types.most_common(12)),
            "rxErrors": self._data.get("rxErrors"),
            "fixedErrors": self._data.get("fixedErrors"),
            "txBuffer": self._data.get("txBuffer"),
            "localNoise": self._data.get("localNoise"),
            "remoteNoise": self._data.get("remoteNoise"),
            "remoteRssi": self._data.get("remoteRssi"),
        }

    def _snapshot(self):
        now = time.monotonic()
        out = dict(self._data)
        ages = {}
        freshness = {}
        for group, limit in STALE_AFTER.items():
            seen = self._seen.get(group)
            age = None if seen is None else max(0.0, now - seen)
            ages[group] = age
            fresh = age is not None and age < limit
            out[group + "Fresh"] = fresh
            for field in GROUP_FIELDS[group]:
                field_seen = self._field_seen.get(field)
                field_fresh = field_seen is not None and now - field_seen < limit
                freshness[field] = field_fresh if field_seen is not None else None
                if not field_fresh:
                    out[field] = None
        connected = self._last_heartbeat > 0 and now - self._last_heartbeat < HEARTBEAT_TIMEOUT
        out["connected"] = connected
        out["heartbeat"] = connected
        out["ages"] = ages
        out["freshness"] = freshness
        out["link"] = self._link(now)
        out["health"] = (
            "connected"
            if connected
            else ("traffic-no-heartbeat" if self._last_packet and now - self._last_packet < 3 else "disconnected")
        )
        return out

    def _emit(self, group=None, **values):
        if group:
            self._touch(group)
            for field in GROUP_FIELDS[group]:
                if field in values:
                    self._field_seen[field] = self._seen[group]
        self._data.update(values)
        self.telemetry.emit(self._snapshot())

    def _candidate(self, msg):
        sysid, compid = msg.get_srcSystem(), msg.get_srcComponent()
        if self.target_system and sysid != self.target_system:
            return False
        if self.target_component and compid != self.target_component:
            return False
        return True

    def _accept_identity(self, msg):
        if not self._candidate(msg):
            return False
        sysid, compid = msg.get_srcSystem(), msg.get_srcComponent()
        autopilot = getattr(msg, "autopilot", mavutil.mavlink.MAV_AUTOPILOT_INVALID)
        if self._vehicle is None and autopilot != mavutil.mavlink.MAV_AUTOPILOT_INVALID:
            self._vehicle = (sysid, compid)
        return self._vehicle == (sysid, compid)

    def _account(self, msg):
        now = time.monotonic()
        kind = msg.get_type()
        self._last_packet = now
        self._window.append(now)
        if kind == "BAD_DATA":
            self._bad += 1
            return False
        self._received += 1
        self._types[kind] += 1
        key = (msg.get_srcSystem(), msg.get_srcComponent())
        seq = msg.get_seq()
        previous = self._last_seq.get(key)
        if previous is not None:
            gap = (seq - previous - 1) & 255
            if gap < 128:
                self._lost += gap
        self._last_seq[key] = seq
        return True

    def _handle(self, msg):
        if not self._account(msg):
            self.telemetry.emit(self._snapshot())
            return
        kind = msg.get_type()
        if kind == "HEARTBEAT" and self._accept_identity(msg):
            self._last_heartbeat = time.monotonic()
            armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            try:
                mode = mavutil.mode_string_v10(msg)
            except Exception:
                mode = "UNKNOWN"
            self._emit(
                "heartbeat",
                armed=armed,
                flightMode=mode,
                systemId=msg.get_srcSystem(),
                componentId=msg.get_srcComponent(),
                vehicleType=_enum_name("MAV_TYPE_", msg.type),
                autopilotType=_enum_name("MAV_AUTOPILOT_", msg.autopilot),
                systemStatus=_enum_name("MAV_STATE_", msg.system_status),
                mavlinkVersion=int(msg.mavlink_version),
            )
            return
        if self._vehicle and (msg.get_srcSystem(), msg.get_srcComponent()) != self._vehicle and kind != "RADIO_STATUS":
            self.telemetry.emit(self._snapshot())
            return
        if kind == "AUTOPILOT_VERSION":
            self._emit(
                flightSoftwareVersion=_version(getattr(msg, "flight_sw_version", 0)),
                middlewareVersion=_version(getattr(msg, "middleware_sw_version", 0)),
                osVersion=_version(getattr(msg, "os_sw_version", 0)),
                boardVersion=int(getattr(msg, "board_version", 0)),
                vendorId=int(getattr(msg, "vendor_id", 0)),
                productId=int(getattr(msg, "product_id", 0)),
                vehicleUid=str(int(getattr(msg, "uid", 0))) if getattr(msg, "uid", 0) else "",
                capabilities=int(getattr(msg, "capabilities", 0)),
            )
        elif kind == "SYS_STATUS":
            self._emit(
                "battery",
                batteryVoltage=_num(msg.voltage_battery, 1000.0, 65535),
                current=_num(msg.current_battery, 100.0, -1),
                batteryRemaining=_num(msg.battery_remaining, 1.0, -1),
                controllerLoad=_num(getattr(msg, "load", None), 10.0, 65535),
                communicationErrors=int(getattr(msg, "errors_comm", 0)),
            )
        elif kind == "BATTERY_STATUS":
            cells = getattr(msg, "voltages", None) or []
            valid = [v for v in cells if 0 < v < 65535]
            values = {
                "current": _num(getattr(msg, "current_battery", None), 100.0, -1),
                "batteryRemaining": _num(getattr(msg, "battery_remaining", None), 1.0, -1),
            }
            if valid:
                values["batteryVoltage"] = sum(valid) / 1000.0
            self._emit("battery", **values)
        elif kind == "GPS_RAW_INT":
            sats = int(getattr(msg, "satellites_visible", 0))
            eph = getattr(msg, "eph", 65535)
            self._emit(
                "gps",
                gpsFix=int(getattr(msg, "fix_type", 0)),
                satellites=None if sats == 255 else sats,
                hdop=None if eph == 65535 else eph / 100.0,
            )
        elif kind == "GLOBAL_POSITION_INT":
            self._position = (msg.lat / 1e7, msg.lon / 1e7)
            hdg = getattr(msg, "hdg", 65535)
            self._emit(
                "position",
                latitude=self._position[0] if any(self._position) else None,
                longitude=self._position[1] if any(self._position) else None,
                altitude=msg.relative_alt / 1000.0,
                heading=None if hdg == 65535 else hdg / 100.0,
                homeDistance=_distance_m(self._home, self._position),
                homeBearing=_bearing_deg(self._position, self._home),
            )
        elif kind == "VFR_HUD":
            self._emit(
                "position",
                groundSpeed=float(msg.groundspeed),
                heading=float(msg.heading),
                altitude=float(msg.alt),
                homeDistance=_distance_m(self._home, self._position),
                homeBearing=_bearing_deg(self._position, self._home),
            )
        elif kind == "ATTITUDE":
            self._emit(
                "attitude", roll=math.degrees(msg.roll), pitch=math.degrees(msg.pitch), yaw=math.degrees(msg.yaw)
            )
        elif kind == "RADIO_STATUS":
            self._emit(
                "radio",
                rssi=int(msg.rssi) if getattr(msg, "rssi", 255) != 255 else None,
                rssiSource="RADIO_STATUS",
                remoteRssi=int(msg.remrssi) if getattr(msg, "remrssi", 255) != 255 else None,
                txBuffer=int(getattr(msg, "txbuf", 0)),
                localNoise=int(getattr(msg, "noise", 0)),
                remoteNoise=int(getattr(msg, "remnoise", 0)),
                rxErrors=int(getattr(msg, "rxerrors", 0)),
                fixedErrors=int(getattr(msg, "fixed", 0)),
            )
        elif kind == "RC_CHANNELS":
            self._emit(
                "radio", rssi=int(msg.rssi) if getattr(msg, "rssi", 255) != 255 else None, rssiSource="RC_CHANNELS"
            )
        elif kind == "HOME_POSITION":
            lat, lon = msg.latitude / 1e7, msg.longitude / 1e7
            if lat or lon:
                self._home = (lat, lon)
                self._touch("home")
                # Kept while the flight lasts: the home point does not go stale like a position.
                self._data["homeLatitude"], self._data["homeLongitude"] = lat, lon
            self._emit(
                "position",
                homeDistance=_distance_m(self._home, self._position),
                homeBearing=_bearing_deg(self._position, self._home),
            )
        else:
            self.telemetry.emit(self._snapshot())

    def run(self):
        try:
            kwargs = {"autoreconnect": True, "robust_parsing": True}
            if not self.endpoint.startswith(("udp", "tcp")):
                kwargs["baud"] = self.baud
            self._master = mavutil.mavlink_connection(self.endpoint, **kwargs)
            self._emit()
            while not self._stop.is_set():
                msg = self._master.recv_match(blocking=True, timeout=0.25)
                if msg is not None:
                    self._handle(msg)
                else:
                    self.telemetry.emit(self._snapshot())
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
    notice = Signal(str)

    def __init__(self, auto_start=True):
        super().__init__()
        settings = QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        self._endpoint = str(settings.value("mavlink/endpoint", DEFAULT_ENDPOINT))
        self._baud = int(settings.value("mavlink/baud", 115200))
        self._enabled = str(settings.value("mavlink/enabled", "true")).lower() not in ("0", "false")
        self._target_system = int(settings.value("mavlink/system", 0))
        self._target_component = int(settings.value("mavlink/component", 0))
        self._worker = None
        self._error = ""
        self._telemetry = {"connected": False, "heartbeat": False, "health": "disconnected", "link": {}}
        self._generation = 0
        if auto_start and self._enabled:
            self.start()

    @Property(str, notify=changed)
    def endpoint(self):
        return self._endpoint

    @Property(int, notify=changed)
    def baud(self):
        return self._baud

    @Property(bool, notify=changed)
    def enabled(self):
        return self._enabled

    @Property(int, notify=changed)
    def targetSystem(self):
        return self._target_system

    @Property(int, notify=changed)
    def targetComponent(self):
        return self._target_component

    @Property("QVariantList", constant=True)
    def presets(self):
        return [{"name": k, "endpoint": v} for k, v in PRESETS.items()]

    @Property(bool, notify=changed)
    def running(self):
        return self._worker is not None and self._worker.isRunning()

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property("QVariantMap", notify=changed)
    def telemetry(self):
        return self._telemetry

    @Slot(str, int, bool, int, int)
    def configure(self, endpoint, baud, enabled, target_system=0, target_component=0):
        endpoint = endpoint.strip()
        if not endpoint:
            self._error = "MAVLink endpoint не може бути порожнім"
            self.changed.emit()
            return
        self.stop()
        self._endpoint = endpoint
        self._baud = max(1200, min(int(baud), 4000000))
        self._enabled = bool(enabled)
        self._target_system = max(0, min(int(target_system), 255))
        self._target_component = max(0, min(int(target_component), 255))
        settings = QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        settings.setValue("mavlink/endpoint", self._endpoint)
        settings.setValue("mavlink/baud", self._baud)
        settings.setValue("mavlink/enabled", self._enabled)
        settings.setValue("mavlink/system", self._target_system)
        settings.setValue("mavlink/component", self._target_component)
        self._error = ""
        self.changed.emit()
        if self._enabled:
            self.start()

    @Slot(str, result=str)
    def applyPreset(self, name):
        return PRESETS.get(name, self._endpoint)

    @Slot(result=str)
    def exportReport(self):
        DATA.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
        path = DATA / f"mavlink-diagnostics-{stamp}.json"
        safe = {
            "generatedUtc": datetime.now(timezone.utc).isoformat(),
            "endpoint": self._endpoint,
            "baud": self._baud,
            "targetSystem": self._target_system,
            "targetComponent": self._target_component,
            "enabled": self._enabled,
            "backendError": self._error,
            "telemetry": self._telemetry,
        }
        path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
        self.notice.emit("Звіт MAVLink збережено: " + str(path))
        return str(path)

    @Slot()
    def start(self):
        if self._worker is not None or not self._enabled:
            return
        self._generation += 1
        generation = self._generation
        self._error = ""
        worker = MavlinkWorker(self._endpoint, self._baud, self._target_system, self._target_component)
        self._worker = worker
        worker.telemetry.connect(lambda values, g=generation: self._on_telemetry(g, values))
        worker.failed.connect(lambda error, g=generation: self._on_error(g, error))
        worker.finished.connect(lambda g=generation, w=worker: self._on_finished(g, w))
        worker.start()
        self.changed.emit()

    @Slot()
    def stop(self):
        self._generation += 1
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.stop()
            worker.wait(1500)
        self._telemetry = {"connected": False, "heartbeat": False, "health": "disconnected", "link": {}}
        self.changed.emit()

    def _on_telemetry(self, generation, values):
        if generation != self._generation:
            return
        self._telemetry = dict(values)
        self.changed.emit()

    def _on_error(self, generation, error):
        if generation != self._generation:
            return
        self._error = error
        self._telemetry = {"connected": False, "heartbeat": False, "health": "disconnected", "link": {}}
        self.changed.emit()

    def _on_finished(self, generation, worker):
        if generation == self._generation and worker is self._worker:
            self._worker = None
            self._telemetry = {"connected": False, "heartbeat": False, "health": "disconnected", "link": {}}
        worker.deleteLater()
        self.changed.emit()

    def shutdown(self):
        self.stop()
