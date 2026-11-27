"""Connection choice per camera, with live reachability of every connection type.

Each type is probed in the background (a TCP connect to the camera's video port)
so the home screen shows current status without blocking the UI. "Fly" becomes
possible only after the pilot picks a type that is reachable right now, and the
video then uses that type's address.
"""

from __future__ import annotations

import socket
import threading
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

import connection_profiles as cp

PROBE_INTERVAL_MS = 5000
PROBE_TIMEOUT_S = 1.5


def tcp_probe(host: str, port: int, timeout: float = PROBE_TIMEOUT_S) -> int | None:
    """Return the TCP connect time in ms, or None when the camera does not answer."""
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError:
        return None
    return max(1, round((time.monotonic() - started) * 1000))


class ConnectionsRuntime(QObject):
    changed = Signal()
    _probed = Signal(str, str, str, object)  # device id, type, host, latency ms or None

    def __init__(self, devices, store, prober=tcp_probe, interval_ms=PROBE_INTERVAL_MS, run_async=True):
        super().__init__()
        self._devices = devices
        self._store = store
        self._prober = prober
        self._run_async = run_async
        self._addresses = store.load()
        self._selected: dict[str, str] = {}
        self._statuses: dict[str, dict[str, dict]] = {}
        self._in_flight: set[tuple[str, str]] = set()
        self._probed.connect(self._apply_probe)
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.refresh)
        for name in ("changed", "streamsChanged"):
            signal = getattr(devices, name, None)
            if signal is not None:
                signal.connect(self._devices_changed)
        self._rebuild()

    # --- properties used by QML ------------------------------------------------
    @Property("QVariantMap", notify=changed)
    def statuses(self):
        return self._statuses

    @Property("QVariantMap", notify=changed)
    def selected(self):
        return dict(self._selected)

    @Property("QVariantList", constant=True)
    def types(self):
        return [{"key": kind, "label": cp.LABELS[kind], "needsAddress": kind in cp.ADDRESS_TYPES} for kind in cp.TYPES]

    # --- slots -----------------------------------------------------------------
    @Slot()
    def start(self):
        self.refresh()
        self._timer.start()

    @Slot()
    def stop(self):
        self._timer.stop()

    @Slot(str, str, result=bool)
    def select(self, device_id, kind):
        if kind not in cp.TYPES or device_id not in self._statuses:
            return False
        self._selected[device_id] = kind
        self.changed.emit()
        self._probe(device_id, kind)
        return True

    @Slot(str, str, result=str)
    def addressFor(self, device_id, kind):
        return self._addresses.get(device_id, {}).get(kind, "")

    @Slot(str, str, str, result=bool)
    def setAddress(self, device_id, kind, address):
        if kind not in cp.ADDRESS_TYPES:
            return False
        try:
            value = cp.validate_address(kind, address)
        except ValueError:
            return False
        self._addresses.setdefault(device_id, {})[kind] = value
        self._store.save(self._addresses)
        self._rebuild()
        self._probe(device_id, kind)
        return True

    @Slot(str, str)
    def clearAddress(self, device_id, kind):
        addresses = self._addresses.get(device_id, {})
        if kind in addresses:
            del addresses[kind]
            if not addresses:
                self._addresses.pop(device_id, None)
            self._store.save(self._addresses)
            if self._selected.get(device_id) == kind:
                self._selected.pop(device_id)
            self._rebuild()

    @Slot(str, result=bool)
    def canFly(self, device_id):
        return cp.can_fly(self._selected.get(device_id, ""), self._statuses.get(device_id, {}))

    @Slot()
    def refresh(self):
        for device_id, statuses in self._statuses.items():
            for kind, entry in statuses.items():
                if entry["state"] not in ("unconfigured", "unsupported"):
                    self._probe(device_id, kind)

    # --- used by the video runtime ---------------------------------------------
    def host_for(self, device) -> str:
        """Address the video should use for this camera, by the selected connection type."""
        device_id = device.get("id", "")
        kind = self._selected.get(device_id, "local")
        if kind in cp.ADDRESS_TYPES:
            return self._addresses.get(device_id, {}).get(kind, "")
        return str(device.get("host", "")).strip()

    # --- internals -------------------------------------------------------------
    def _devices_changed(self):
        self._rebuild()

    def _port(self, device_id):
        for stream in getattr(self._devices, "streams", []):
            if stream.get("device_id") == device_id and stream.get("enabled"):
                try:
                    return int(stream.get("port"))
                except (TypeError, ValueError):
                    break
        return cp.DEFAULT_VIDEO_PORT

    def _host(self, device_id, kind):
        if kind == "local":
            device = next((d for d in self._devices.items if d.get("id") == device_id), {})
            return str(device.get("host", "")).strip()
        if kind in cp.ADDRESS_TYPES:
            return self._addresses.get(device_id, {}).get(kind, "")
        return ""

    def _rebuild(self):
        statuses = {}
        for device in self._devices.homeItems:
            device_id = device.get("id", "")
            old = self._statuses.get(device_id, {})
            entry = {}
            for kind in cp.TYPES:
                if kind == "cloud":
                    entry[kind] = cp.status_entry("unsupported")
                elif not self._host(device_id, kind):
                    entry[kind] = cp.status_entry("unconfigured")
                elif kind in old and old[kind]["state"] not in ("unconfigured", "unsupported"):
                    entry[kind] = old[kind]
                else:
                    entry[kind] = cp.status_entry("checking")
            statuses[device_id] = entry
        self._statuses = statuses
        self._selected = {k: v for k, v in self._selected.items() if k in statuses}
        self.changed.emit()

    def _probe(self, device_id, kind):
        host = self._host(device_id, kind)
        if not host or (device_id, kind) in self._in_flight:
            return
        port = self._port(device_id)
        self._in_flight.add((device_id, kind))

        def work():
            try:
                latency = self._prober(host, port)
            except Exception:
                latency = None
            self._probed.emit(device_id, kind, host, latency)

        if self._run_async:
            threading.Thread(target=work, daemon=True).start()
        else:
            work()

    def _apply_probe(self, device_id, kind, host, latency):
        self._in_flight.discard((device_id, kind))
        if device_id not in self._statuses or self._host(device_id, kind) != host:
            return  # the camera or its address changed while probing
        state = "available" if latency is not None else "unavailable"
        self._statuses[device_id][kind] = cp.status_entry(state, latency)
        self.changed.emit()
