import os
import urllib.request

from PySide6.QtCore import QCoreApplication

import map_tiles as mt

APP = QCoreApplication.instance() or QCoreApplication([])


class Telemetry:
    telemetry = {}


def fake_fetch(calls):
    def fetch(z, x, y):
        calls.append((z, x, y))
        return b"\xff\xd8jpeg" + bytes(f"{z}/{x}/{y}", "ascii")

    return fetch


def test_area_around_the_drone_is_small_and_detailed_near_it():
    tiles = mt.tiles_around(50.45, 30.52)
    assert 200 < len(tiles) < 400, len(tiles)
    zooms = {z for z, _, _ in tiles}
    assert zooms == {10, 12, 13, 14, 15, 16, 17}
    x, y = mt.tile_xy(50.45, 30.52, 17)
    assert (17, int(x), int(y)) in tiles, "the tile under the drone is in"


def test_ahead_fetches_only_missing_tiles_and_a_new_area_when_the_drone_moves(tmp_path):
    calls, telemetry = [], Telemetry()
    rt = mt.MapTilesRuntime(tmp_path, telemetry, fetcher=fake_fetch(calls), serve=False, run_async=False)
    rt.setActive(True)
    assert calls == [], "no position: nothing fetched"
    telemetry.telemetry = {"latitude": 50.45, "longitude": 30.52}
    rt.check()
    first = len(calls)
    assert first == len(mt.tiles_around(50.45, 30.52)) and not rt.downloading
    assert rt.text == "Карта навколо дрона збережена"
    telemetry.telemetry = {"latitude": 50.4505, "longitude": 30.5205}
    rt.check()
    assert len(calls) == first, "moved less than 1 km: nothing new"
    telemetry.telemetry = {"latitude": 50.45, "longitude": 30.52}
    rt._area = None
    rt.check()
    assert len(calls) == first, "the same area again: every tile is kept, none fetched twice"
    telemetry.telemetry = {"latitude": 50.50, "longitude": 30.52}
    rt.check()
    assert first < len(calls) < 2 * first, "a new area: only the tiles not kept yet"


def test_the_local_map_server_answers_from_the_folder_and_fetches_once(tmp_path):
    calls = []
    rt = mt.MapTilesRuntime(tmp_path, Telemetry(), fetcher=fake_fetch(calls), run_async=False)
    try:
        url = rt.url.replace("%z", "5").replace("%y", "11").replace("%x", "18")
        assert url.startswith("http://127.0.0.1:")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        assert opener.open(url, timeout=5).read() == b"\xff\xd8jpeg5/18/11"
        assert opener.open(url, timeout=5).read() == b"\xff\xd8jpeg5/18/11"
        assert calls == [(5, 18, 11)], "kept after the first time"
        bad = url.replace("/tile/5/", "/../etc/")
        try:
            opener.open(bad, timeout=5)
            raise AssertionError("only tiles are served")
        except urllib.error.HTTPError as error:
            assert error.code == 404
    finally:
        rt.shutdown()


def test_store_limit_removes_the_oldest(tmp_path):
    store = mt.TileStore(tmp_path, limit=25)
    for i in range(5):
        store.write(10, i, 0, b"0123456789")
        os.utime(store.path(10, i, 0), (1000 + i, 1000 + i))
    store.prune()
    assert [store.has(10, i, 0) for i in range(5)] == [False, False, False, True, True]


def test_what_the_window_shows_is_fetched_with_one_level_closer(tmp_path):
    calls = []
    rt = mt.MapTilesRuntime(tmp_path, Telemetry(), fetcher=fake_fetch(calls), serve=False, run_async=False)
    rt.prefetchView(50.46, 30.50, 50.44, 30.54, 15.4)
    zooms = sorted({z for z, _, _ in calls})
    assert zooms == [15, 16], zooms
    assert set(calls) == set(
        mt.tiles_in_box(50.46, 30.50, 50.44, 30.54, 15) + mt.tiles_in_box(50.46, 30.50, 50.44, 30.54, 16)
    )
    before = len(calls)
    rt.prefetchView(50.46, 30.50, 50.44, 30.54, 15.4)
    assert len(calls) == before, "kept tiles are not fetched again"
    rt.prefetchView(80, -170, -80, 170, 12)
    assert len(calls) == before, "a whole-world view is not bulk-downloaded"


def test_a_missing_detailed_tile_is_an_enlarged_part_of_a_coarser_one(tmp_path):
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from PySide6.QtGui import QColor, QImage

    image = QImage(256, 256, QImage.Format_RGB32)
    image.fill(QColor("darkgreen"))
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "JPG")
    store = mt.TileStore(tmp_path)
    store.write(16, 100, 200, bytes(data))
    out = mt.overzoom(store, 18, 401, 803)
    enlarged = QImage.fromData(QByteArray(out))
    assert enlarged.width() == 256 and enlarged.pixelColor(128, 128).green() > 80
    assert mt.overzoom(store, 18, 0, 0) is None, "nothing coarser kept: nothing to show"
    assert not store.has(18, 401, 803), "an enlarged part is not kept: the real tile comes later"
