from PySide6.QtCore import QObject, Signal

from extra_windows import MAX_WINDOWS, ExtraWindowsRuntime


class Devices(QObject):
    changed = Signal()
    streamsChanged = Signal()

    def __init__(self):
        super().__init__()
        self.activeId = "c1"
        self.activeStreams = [
            {"id": "main", "name": "Основний", "kind": "main", "enabled": True},
            {"id": "sub", "name": "Другий", "kind": "sub", "enabled": True},
            {"id": "thermal", "name": "Тепловізор", "kind": "thermal", "enabled": True},
            {"id": "cam2", "name": "Задня камера", "kind": "sub", "enabled": True},
            {"id": "cam3", "name": "Нижня камера", "kind": "sub", "enabled": True},
        ]


class Workspace(QObject):
    changed = Signal()
    state = {"primaryId": "main"}


class Runtime(QObject):
    changed = Signal()

    def __init__(self, ok=True):
        super().__init__()
        self.ok = ok
        self.url = ""
        self.state = "stopped"
        self.stopped = 0
        self.host_resolver = None

    def prepare(self, stream_id):
        if self.ok:
            self.url, self.state = f"rtsp://cam/{stream_id}", "ready"
        return self.ok

    def stop(self):
        self.stopped += 1
        self.url, self.state = "", "stopped"


def make(tmp_path, ok=True):
    devices = Devices()
    rt = ExtraWindowsRuntime(devices, Workspace(), tmp_path / "windows.json", runtime_factory=lambda: Runtime(ok))
    return rt, devices


def test_sources_are_the_cameras_other_streams(tmp_path):
    rt, _ = make(tmp_path)
    assert [s["id"] for s in rt.sources] == ["sub", "thermal", "cam2", "cam3"], "not the main one"
    assert all(s["slot"] == -1 for s in rt.sources)


def test_plus_opens_up_to_three_windows_and_minus_stops_the_stream(tmp_path):
    rt, _ = make(tmp_path)
    assert rt.open("thermal") == 0
    assert rt.open("thermal") == 0, "already open: the same window"
    assert rt.open("sub") == 1 and rt.open("cam2") == 2
    assert rt.open("cam3") == -1, "at most three windows"
    assert rt.openCount == MAX_WINDOWS
    assert rt.windows[0]["url"] == "rtsp://cam/thermal" and rt.windows[0]["name"] == "Тепловізор"
    assert rt.open("main") == -1, "the main stream is on the big screen already"
    rt.close(1)
    assert rt.openCount == 2 and rt._runtimes[1].stopped == 1, "a closed stream is stopped: no bitrate"
    assert [s["slot"] for s in rt.sources] == [-1, 0, 2, -1]


def test_new_windows_do_not_cover_each_other(tmp_path):
    rt, _ = make(tmp_path)
    rt.open("sub")
    rt.open("thermal")
    a, b = rt.windows[0], rt.windows[1]
    assert (a["x"], a["y"]) != (b["x"], b["y"])


def test_the_pilot_places_windows_within_the_area(tmp_path):
    rt, _ = make(tmp_path)
    rt.open("sub")
    rt.place(0, 0.95, -0.2, 0.9)
    w = rt.windows[0]
    assert w["w"] == 0.7 and abs(w["x"] - 0.3) < 1e-9 and w["y"] == 0.0, "kept on screen, not too big"
    rt.place(0, 0.1, 0.5, 0.01)
    assert rt.windows[0]["w"] == 0.12, "not too small to see"


def test_fullscreen_detach_and_last_used_for_tab(tmp_path):
    rt, _ = make(tmp_path)
    rt.open("sub")
    rt.open("thermal")
    assert rt.lastUsed == 1
    rt.touch(0)
    assert rt.lastUsed == 0
    rt.setFullscreen(0, True)
    assert rt.windows[0]["fullscreen"]
    rt.setDetached(0, True)
    assert rt.windows[0]["detached"] and not rt.windows[0]["fullscreen"]
    rt.close(0)
    assert rt.lastUsed == 1


def test_open_as_last_time_only_on_the_pilots_press(tmp_path):
    rt, devices = make(tmp_path)
    rt.open("thermal")
    rt.place(0, 0.05, 0.6, 0.25)
    rt.open("sub")
    rt.closeAll()
    assert rt.openCount == 0 and rt.canRestore
    again = ExtraWindowsRuntime(devices, Workspace(), tmp_path / "windows.json", runtime_factory=Runtime)
    assert again.openCount == 0, "nothing opens by itself"
    assert again.restoreLast() == 2
    w = again.windows[0]
    assert w["streamId"] == "thermal" and (w["x"], w["y"], w["w"]) == (0.05, 0.6, 0.25)
    assert not again.canRestore, "already open"


def test_a_stream_that_cannot_start_opens_no_window(tmp_path):
    rt, _ = make(tmp_path, ok=False)
    assert rt.open("sub") == -1 and rt.openCount == 0


def test_another_camera_closes_the_windows(tmp_path):
    rt, devices = make(tmp_path)
    rt.open("sub")
    devices.activeId = "c2"
    devices.changed.emit()
    assert rt.openCount == 0


def test_layout_presets_are_saved_and_applied_by_the_pilot(tmp_path):
    rt, _ = make(tmp_path)
    assert rt.saveLayout() == -1, "nothing open: nothing to save"
    rt.open("thermal")
    rt.place(0, 0.0, 0.0, 0.4)
    assert rt.saveLayout() == 0
    rt.open("sub")
    assert rt.saveLayout() == 1
    assert [x["name"] for x in rt.layouts] == ["Розташування 1", "Розташування 2"]
    assert [x["count"] for x in rt.layouts] == [1, 2]
    assert rt.layouts[0]["windows"] == [{"x": 0.0, "y": 0.0, "w": 0.4}], "a little picture of the arrangement"
    assert rt.applyLayout(0) == 1
    assert rt.openCount == 1 and rt.windows[0]["streamId"] == "thermal" and rt.windows[0]["w"] == 0.4
    rt.deleteLayout(0)
    assert [x["name"] for x in rt.layouts] == ["Розташування 2"]


def test_an_older_file_with_only_the_last_arrangement_still_restores(tmp_path):
    import json

    (tmp_path / "windows.json").write_text(json.dumps({"c1": [{"streamId": "sub", "x": 0.1, "y": 0.1, "w": 0.3}]}))
    rt, _ = make(tmp_path)
    assert rt.canRestore and rt.restoreLast() == 1


def overlap(a, b, aspect):
    ah, bh = a["w"] * 9 / 16 * aspect, b["w"] * 9 / 16 * aspect
    return a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + bh and b["y"] < a["y"] + ah


def no_overlaps(rt):
    shown = [w for w in rt.windows if w["open"]]
    return all(not overlap(a, b, rt._aspect) for i, a in enumerate(shown) for b in shown[i + 1 :])


def test_windows_never_lie_over_each_other(tmp_path):
    rt, _ = make(tmp_path)
    rt.open("sub")
    rt.open("thermal")
    rt.open("cam2")
    assert rt.openCount == 3 and no_overlaps(rt), "opened next to each other"
    first = dict(rt.windows[0])
    rt.place(1, first["x"] + 0.02, first["y"] + 0.02, 0.3)
    assert no_overlaps(rt), "dropped onto another: it stops next to it"
    rt.place(2, 0.0, 0.0, 0.7)
    assert no_overlaps(rt), "made too big: it gets smaller instead of covering"
    rt.setAspect(1.3)
    assert no_overlaps(rt), "a taller screen: still apart"
    assert all(w["y"] + w["w"] * 9 / 16 * 1.3 <= 1.0 + 1e-9 for w in rt.windows if w["open"]), "and on screen"


def test_a_window_with_room_stays_where_the_pilot_put_it(tmp_path):
    rt, _ = make(tmp_path)
    rt.open("sub")
    rt.open("thermal")
    rt.place(1, 0.05, 0.5, 0.25)
    w = rt.windows[1]
    assert (round(w["x"], 3), round(w["y"], 3), w["w"]) == (0.05, 0.5, 0.25)
