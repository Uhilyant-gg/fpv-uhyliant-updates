"""Wind forecast at the drone's point and height, for the map (no warnings, by the owner's decision).

The forecast comes from Open-Meteo (free, no key) over the PC's internet. The drone's position is
rounded to about 5 km before it is sent, which is finer than the forecast grid anyway. The level
nearest to the drone's height above the take-off point is used: 10, 80, 120 or 180 m.
Asked again every 10 minutes, or sooner when the drone has moved more than 5 km.
"""

from __future__ import annotations

import json
import math
import threading
import time
import urllib.request

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

URL = "https://api.open-meteo.com/v1/forecast"
LEVELS = (10, 80, 120, 180)
ROUND_DEG = 0.05
REFRESH_S = 600
MOVED_KM = 5.0


def level_for(altitude_m) -> int:
    try:
        altitude = max(0.0, float(altitude_m))
    except (TypeError, ValueError):
        return 10
    return min(LEVELS, key=lambda level: abs(level - altitude))


def rounded(value: float) -> float:
    return round(round(float(value) / ROUND_DEG) * ROUND_DEG, 3)


def request_url(lat: float, lon: float) -> str:
    fields = ",".join(f"wind_speed_{h}m,wind_direction_{h}m" for h in LEVELS) + ",wind_gusts_10m"
    return f"{URL}?latitude={rounded(lat)}&longitude={rounded(lon)}&current={fields}&wind_speed_unit=ms&timezone=UTC"


def parse(data: dict, level: int) -> dict:
    """{speedMs, fromDeg, gustMs, levelM} for the chosen level; a missing level falls back to 10 m."""
    current = data.get("current") if isinstance(data, dict) else None
    if not isinstance(current, dict):
        raise ValueError("no current wind")
    for lv in (level, 10):
        speed, direction = current.get(f"wind_speed_{lv}m"), current.get(f"wind_direction_{lv}m")
        if isinstance(speed, (int, float)) and isinstance(direction, (int, float)):
            gust = current.get("wind_gusts_10m")
            return {
                "speedMs": round(float(speed), 1),
                "fromDeg": float(direction) % 360,
                "gustMs": round(float(gust), 1) if isinstance(gust, (int, float)) else None,
                "levelM": lv,
            }
    raise ValueError("no wind values")


def distance_km(a, b) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def fetch(url: str, timeout=10.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "FPV-Uhyliant-ground-station"})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - fixed https host
        return json.loads(response.read().decode("utf-8"))


def compass(deg: float) -> str:
    names = ("Пн", "ПнСх", "Сх", "ПдСх", "Пд", "ПдЗх", "Зх", "ПнЗх")
    return names[int((deg % 360 + 22.5) // 45) % 8]


class WindRuntime(QObject):
    changed = Signal()
    _fetched = Signal(object, object)

    def __init__(self, telemetry, fetcher=fetch, run_async=True, clock=time.monotonic, interval_ms=30000):
        super().__init__()
        self._telemetry = telemetry
        self._fetcher = fetcher
        self._run_async = run_async
        self._clock = clock
        self._wind: dict = {}
        self._asked_at = -1e9
        self._asked_where = None
        self._busy = False
        self._error = ""
        self._fetched.connect(self._apply)
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.check)

    @Property(bool, notify=changed)
    def available(self):
        return bool(self._wind)

    @Property("QVariantMap", notify=changed)
    def wind(self):
        return dict(self._wind)

    @Property(str, notify=changed)
    def text(self):
        if not self._wind:
            return self._error or "Вітер: чекаю координати дрона"
        w = self._wind
        gust = f", пориви {w['gustMs']:g}" if w.get("gustMs") else ""
        return f"Вітер {compass(w['fromDeg'])} {w['speedMs']:g} м/с{gust} · {w['levelM']} м".replace(".", ",")

    @Slot(bool)
    def setActive(self, active):
        if active:
            self._timer.start()
            self.check()
        else:
            self._timer.stop()

    def _position(self):
        t = getattr(self._telemetry, "telemetry", {}) or {}
        try:
            lat, lon = float(t.get("latitude")), float(t.get("longitude"))
        except (TypeError, ValueError):
            return None, None
        return (lat, lon), t.get("altitude")

    @Slot()
    def check(self):
        where, altitude = self._position()
        if where is None or self._busy:
            return
        level = level_for(altitude)
        stale = self._clock() - self._asked_at >= REFRESH_S
        moved = self._asked_where is None or distance_km(where, self._asked_where) > MOVED_KM
        if not (stale or moved or (self._wind and self._wind.get("levelM") != level)):
            return
        self._busy, self._asked_at, self._asked_where = True, self._clock(), where
        url = request_url(*where)

        def work():
            try:
                result = parse(self._fetcher(url), level)
            except Exception:
                result = None
            self._fetched.emit(result, level)

        if self._run_async:
            threading.Thread(target=work, name="wind", daemon=True).start()
        else:
            work()

    def _apply(self, result, _level):
        self._busy = False
        if result is None:
            self._error = "Вітер: прогноз недоступний (немає інтернету на ПК?)"
            if self._wind:
                return self.changed.emit()  # keep the last known wind
        else:
            self._wind, self._error = result, ""
        self.changed.emit()
