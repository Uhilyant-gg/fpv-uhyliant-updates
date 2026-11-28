"""MGRS (military grid) coordinates <-> latitude/longitude, WGS 84.

Used by the map: a point is shown and entered as, for example, "36U VV 12345 67890".
Implements the standard UTM transverse Mercator series and the MGRS 100 km square letters;
accurate to well under a metre inside the UTM zones (latitudes 80° S to 84° N).
"""

from __future__ import annotations

import math
import re

_A = 6378137.0
_F = 1 / 298.257223563
_E2 = _F * (2 - _F)
_EP2 = _E2 / (1 - _E2)
_K0 = 0.9996
_BANDS = "CDEFGHJKLMNPQRSTUVWX"
_COLUMN_SETS = ("ABCDEFGH", "JKLMNPQR", "STUVWXYZ")
_ROWS = "ABCDEFGHJKLMNPQRSTUV"


def _zone(lat, lon):
    zone = int((lon + 180) // 6) + 1
    if 56 <= lat < 64 and 3 <= lon < 12:
        zone = 32
    if 72 <= lat < 84:
        for z, lo, hi in ((31, 0, 9), (33, 9, 21), (35, 21, 33), (37, 33, 42)):
            if lo <= lon < hi:
                zone = z
    return min(max(zone, 1), 60)


def _meridian(phi):
    e2, e4, e6 = _E2, _E2**2, _E2**3
    return _A * (
        (1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi
        - (3 * e2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * phi)
        + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * phi)
        - (35 * e6 / 3072) * math.sin(6 * phi)
    )


def to_utm(lat: float, lon: float) -> tuple[int, float, float]:
    zone = _zone(lat, lon)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    phi, lam = math.radians(lat), math.radians(lon)
    n = _A / math.sqrt(1 - _E2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = _EP2 * math.cos(phi) ** 2
    a = math.cos(phi) * (lam - lon0)
    easting = _K0 * n * (a + (1 - t + c) * a**3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * _EP2) * a**5 / 120) + 500000
    northing = _K0 * (
        _meridian(phi)
        + n
        * math.tan(phi)
        * (
            a * a / 2
            + (5 - t + 9 * c + 4 * c * c) * a**4 / 24
            + (61 - 58 * t + t * t + 600 * c - 330 * _EP2) * a**6 / 720
        )
    )
    if lat < 0:
        northing += 10000000
    return zone, easting, northing


def from_utm(zone: int, easting: float, northing: float, south: bool) -> tuple[float, float]:
    x = easting - 500000
    y = northing - (10000000 if south else 0)
    m = y / _K0
    mu = m / (_A * (1 - _E2 / 4 - 3 * _E2**2 / 64 - 5 * _E2**3 / 256))
    e1 = (1 - math.sqrt(1 - _E2)) / (1 + math.sqrt(1 - _E2))
    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )
    n1 = _A / math.sqrt(1 - _E2 * math.sin(phi1) ** 2)
    t1 = math.tan(phi1) ** 2
    c1 = _EP2 * math.cos(phi1) ** 2
    r1 = _A * (1 - _E2) / (1 - _E2 * math.sin(phi1) ** 2) ** 1.5
    d = x / (n1 * _K0)
    lat = phi1 - (n1 * math.tan(phi1) / r1) * (
        d * d / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * _EP2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * _EP2 - 3 * c1 * c1) * d**6 / 720
    )
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    lon = lon0 + (
        d - (1 + 2 * t1 + c1) * d**3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 * c1 + 8 * _EP2 + 24 * t1 * t1) * d**5 / 120
    ) / math.cos(phi1)
    return math.degrees(lat), math.degrees(lon)


def _band(lat):
    if not -80 <= lat <= 84:
        raise ValueError("MGRS covers latitudes 80° S to 84° N")
    return _BANDS[min(int((lat + 80) // 8), 19)]


def to_mgrs(lat: float, lon: float, digits: int = 5) -> str:
    """'36U VV 12345 67890' (five digits: one metre)."""
    zone, easting, northing = to_utm(lat, lon)
    band = _band(lat)
    column = _COLUMN_SETS[(zone - 1) % 3][int(easting // 100000) - 1]
    row = _ROWS[(int(northing // 100000) + (5 if zone % 2 == 0 else 0)) % 20]
    scale = 10 ** (5 - digits)
    e = int(easting % 100000) // scale
    n = int(northing % 100000) // scale
    return f"{zone}{band} {column}{row} {e:0{digits}d} {n:0{digits}d}"


_MGRS = re.compile(r"^\s*(\d{1,2})\s*([C-HJ-NP-X])\s*([A-HJ-NP-Z])\s*([A-HJ-NP-V])\s*(\d*)\s*(\d*)\s*$", re.I)


def from_mgrs(text: str) -> tuple[float, float]:
    """Latitude and longitude of the centre-ish (south-west corner) of the MGRS square; ValueError if wrong."""
    match = _MGRS.match(str(text or ""))
    if not match:
        raise ValueError("not an MGRS coordinate")
    zone, band, column, row, e_text, n_text = match.groups()
    zone, band, column, row = int(zone), band.upper(), column.upper(), row.upper()
    digits = e_text + n_text
    if not 1 <= zone <= 60 or len(digits) % 2 or len(digits) > 10:
        raise ValueError("not an MGRS coordinate")
    half = len(digits) // 2
    e_text, n_text = digits[:half], digits[half:]
    scale = 10 ** (5 - half) if half else 100000
    columns = _COLUMN_SETS[(zone - 1) % 3]
    if column not in columns:
        raise ValueError("square letter does not fit the zone")
    easting = (columns.index(column) + 1) * 100000 + (int(e_text) * scale if half else 0)
    row_north = (_ROWS.index(row) - (5 if zone % 2 == 0 else 0)) % 20 * 100000 + (int(n_text) * scale if half else 0)
    south = band < "N"
    # The band gives the latitude roughly; add 2000 km cycles until the northing falls in it.
    band_lat = -80 + _BANDS.index(band) * 8
    _z, _e, band_north = to_utm(band_lat if band != "X" else 72, (zone - 1) * 6 - 180 + 3)
    northing = row_north
    while northing < band_north - 100000:
        northing += 2000000
    return from_utm(zone, easting, northing, south)
