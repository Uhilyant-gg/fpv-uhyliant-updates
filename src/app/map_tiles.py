"""The satellite map kept on this PC, filled around the drone by itself.

A tiny map server runs on this PC only (127.0.0.1). The map asks it for tiles; it answers from
its own folder and, for a tile it does not have yet, fetches it once from Esri and keeps it.
While flying, the station also fetches ahead a small area around the drone (about 1-2 km in
detail, 15 km as an overview), so the map is there even if the PC's internet drops later. When
the drone moves elsewhere, the new area is added; tiles already kept are never fetched again.

Only what the pilot flies over is fetched, at a polite pace, the way a map viewer would load it
(no bulk download of whole regions). The folder is limited in size; the oldest tiles go first.
"""

from __future__ import annotations

import math
import os
import re
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

SOURCE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
AGENT = "FPV-Uhyliant-ground-station"
MAX_TILE_BYTES = 2 * 1024 * 1024
MAX_STORE_BYTES = 1500 * 1024 * 1024
# (zoom, radius in km) fetched ahead around the drone: a wide overview, then ever finer detail nearer.
AHEAD = ((10, 15.0), (12, 6.0), (13, 4.0), (14, 3.0), (15, 2.0), (16, 1.5), (17, 1.0))
MOVED_KM = 1.0  # a new area is added once the drone is this far from the last one
PACE_S = 0.12  # between fetched tiles, about eight a second at most
_PATH = re.compile(r"^/tile/(\d{1,2})/(\d{1,7})/(\d{1,7})$")


def tile_xy(lat: float, lon: float, z: int) -> tuple[float, float]:
    n = 2**z
    lat = max(-85.0511, min(85.0511, lat))
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def tiles_around(lat: float, lon: float, ahead=AHEAD) -> list[tuple[int, int, int]]:
    """(z, x, y) of the tiles within each level's radius of the point, coarse levels first."""
    out = []
    for z, radius_km in ahead:
        n = 2**z
        cx, cy = tile_xy(lat, lon, z)
        tile_km = 40075.0 * math.cos(math.radians(lat)) / n
        r = max(1, math.ceil(radius_km / max(tile_km, 1e-6)))
        for x in range(int(cx) - r, int(cx) + r + 1):
            for y in range(int(cy) - r, int(cy) + r + 1):
                if 0 <= y < n and math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r + 0.5:
                    out.append((z, x % n, y))
    return out


def distance_km(a, b) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def fetch_tile(z: int, x: int, y: int, timeout=10.0) -> bytes:
    req = urllib.request.Request(SOURCE.format(z=z, x=x, y=y), headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # fixed https host
        kind = response.headers.get("Content-Type", "")
        data = response.read(MAX_TILE_BYTES + 1)
    if not kind.startswith("image/") or not data or len(data) > MAX_TILE_BYTES:
        raise ValueError("not a map tile")
    return data


class TileStore:
    """Tiles as files: <root>/<z>/<x>/<y>.jpg, written whole or not at all."""

    def __init__(self, root: Path, limit=MAX_STORE_BYTES):
        self.root = Path(root)
        self.limit = limit
        self._lock = threading.Lock()

    def path(self, z, x, y) -> Path:
        return self.root / str(int(z)) / str(int(x)) / f"{int(y)}.jpg"

    def has(self, z, x, y) -> bool:
        return self.path(z, x, y).is_file()

    def read(self, z, x, y) -> bytes | None:
        try:
            return self.path(z, x, y).read_bytes()
        except OSError:
            return None

    def write(self, z, x, y, data: bytes):
        path = self.path(z, x, y)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{threading.get_ident()}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)

    def stats(self) -> tuple[int, int]:
        count = size = 0
        for file in self.root.rglob("*.jpg"):
            try:
                size += file.stat().st_size
                count += 1
            except OSError:
                pass
        return count, size

    def prune(self):
        """Keep the folder under its limit: the tiles not used for the longest go first."""
        with self._lock:
            files = []
            for file in self.root.rglob("*.jpg"):
                try:
                    st = file.stat()
                except OSError:
                    continue
                files.append((st.st_atime, st.st_size, file))
            total = sum(f[1] for f in files)
            for _atime, size, file in sorted(files):
                if total <= self.limit:
                    break
                try:
                    file.unlink()
                    total -= size
                except OSError:
                    pass

    def get_or_fetch(self, z, x, y, fetcher=fetch_tile) -> bytes | None:
        data = self.read(z, x, y)
        if data is not None:
            return data
        try:
            data = fetcher(z, x, y)
        except Exception:
            return None
        try:
            self.write(z, x, y, data)
        except OSError:
            pass
        return data


def make_server(store: TileStore, fetcher=fetch_tile) -> ThreadingHTTPServer:
    """The map server, on this PC only (127.0.0.1, a free port). Answers /tile/<z>/<y>/<x> only."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - the http.server name
            match = _PATH.match(self.path.split("?", 1)[0])
            if not match:
                self.send_error(404)
                return
            z, y, x = (int(v) for v in match.groups())
            if z > 22 or x >= 2**z or y >= 2**z:
                self.send_error(404)
                return
            data = store.get_or_fetch(z, x, y, fetcher)
            if data is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    return server


class MapTilesRuntime(QObject):
    changed = Signal()
    _progress = Signal(int, int)

    def __init__(self, root: Path, telemetry, fetcher=fetch_tile, serve=True, run_async=True, interval_ms=10000):
        super().__init__()
        self._store = TileStore(root)
        self._telemetry = telemetry
        self._fetcher = fetcher
        self._run_async = run_async
        self._server = None
        self._area = None
        self._queue: list[tuple[int, int, int]] = []
        self._done = 0
        self._total = 0
        self._busy = False
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._progress.connect(self._apply_progress)
        if serve:
            try:
                self._server = make_server(self._store, fetcher)
                threading.Thread(target=self._server.serve_forever, name="map-tiles", daemon=True).start()
            except OSError:
                self._server = None
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.check)

    # --- what QML shows -----------------------------------------------------------
    @Property(str, constant=True)
    def url(self):
        """The tile address for the map; Esri directly if the local server could not start."""
        if self._server is None:
            return SOURCE.replace("{z}", "%z").replace("{y}", "%y").replace("{x}", "%x")
        return f"http://127.0.0.1:{self._server.server_address[1]}/tile/%z/%y/%x"

    @Property(bool, notify=changed)
    def downloading(self):
        return self._busy

    @Property(str, notify=changed)
    def text(self):
        if self._busy:
            return f"Карта навколо дрона: {self._done} з {self._total}"
        return "Карта навколо дрона збережена" if self._area else ""

    # --- around the drone ---------------------------------------------------------------
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
            return None
        return (lat, lon) if -85 < lat < 85 and -180 <= lon <= 180 and (lat or lon) else None

    @Slot()
    def check(self):
        where = self._position()
        if where is None or (self._area is not None and distance_km(where, self._area) < MOVED_KM):
            return
        self._area = where
        missing = [t for t in tiles_around(*where) if not self._store.has(*t)]
        with self._lock:
            # The new area goes first: the drone is there now.
            first = set(missing)
            self._queue = missing + [t for t in self._queue if t not in first]
            if not self._busy:
                self._done = 0
            self._total = self._done + len(self._queue)
        if self._queue and not self._busy:
            self._busy = True
            self.changed.emit()
            self._run(self._work)
        else:
            self.changed.emit()

    def _run(self, work):
        if self._run_async:
            threading.Thread(target=work, name="map-ahead", daemon=True).start()
        else:
            work()

    def _work(self):
        done = 0
        while not self._stop.is_set():
            with self._lock:
                if not self._queue:
                    break
                tile = self._queue.pop(0)
                total = self._total
            if not self._store.has(*tile):
                self._store.get_or_fetch(*tile, fetcher=self._fetcher)
                if self._run_async:
                    time.sleep(PACE_S)
            done += 1
            self._progress.emit(done, total)
        self._store.prune()
        self._progress.emit(-1, 0)

    def _apply_progress(self, done, total):
        if done < 0:
            self._busy = False
        else:
            self._done, self._total = done, total
        self.changed.emit()

    def shutdown(self):
        self._stop.set()
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
