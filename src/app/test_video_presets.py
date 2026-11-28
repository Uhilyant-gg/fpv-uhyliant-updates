import pytest
from PySide6.QtCore import QObject, Signal

import video_presets as vp


class Devices(QObject):
    changed = Signal()

    def __init__(self, active="c1"):
        super().__init__()
        self.activeId = active


class Connections:
    def __init__(self, host="10.147.17.5"):
        self.host = host

    def control_host(self, device_id):
        return self.host


def make(tmp_path, host="10.147.17.5", result=None):
    sent = []

    def apply(h, lines):
        sent.append((h, list(lines)))
        return result or {"state": "applied"}

    store = vp.VideoPresetStore(tmp_path / "video-presets.json")
    rt = vp.VideoPresetsRuntime(store, Devices(), Connections(host), apply, run_async=False)
    return rt, sent, store


def test_nine_slots_on_keys_2_to_0_with_defaults_from_the_weakest_link(tmp_path):
    rt, _, _ = make(tmp_path)
    keys = [s["key"] for s in rt.slots]
    assert keys == ["2", "3", "4", "5", "6", "7", "8", "9", "0"]
    assert rt.slots[0]["name"] == "Мінімум" and rt.slots[0]["bitrateKbps"] == 512
    assert rt.slots[8]["name"] == "Максимум" and rt.slots[8]["bitrateKbps"] == 6144
    assert not any(s["empty"] for s in rt.slots), "the station fills every slot by itself"
    assert rt.label == "Пресет відео не вибрано"


def test_applying_a_preset_writes_it_into_the_camera(tmp_path):
    rt, sent, store = make(tmp_path)
    assert rt.apply("6")
    assert sent == [
        (
            "10.147.17.5",
            [
                "cli -s .video0.rcMode cbr",
                "cli -s .video0.size 1280x720",
                "cli -s .video0.fps 30",
                "cli -s .video0.bitrate 2048",
                "cli -s .video0.gopSize 0.5",
                "killall -1 majestic",
            ],
        )
    ]
    assert rt.activeKey == "6" and rt.label == "6 · Середній · 2 Мбіт/с"
    assert rt.message == "Пресет 6 «Середній» застосовано в камері" and rt.messageOk
    assert store.load()["c1"]["active"] == "6", "remembered for this camera"


def test_quick_bitrate_steps_mark_the_preset_as_changed(tmp_path):
    rt, sent, _ = make(tmp_path)
    rt.apply("6")
    assert rt.stepBitrate(-1)
    assert sent[-1][1] == ["cli -s .video0.bitrate 1536", "killall -1 majestic"]
    assert rt.label == "6 · Середній* · 1,5 Мбіт/с"
    rt.stepBitrate(+1)
    rt.stepBitrate(+1)
    assert rt.bitrateKbps == 2560
    assert not rt.setBitrate(50000), "out of range never reaches the camera"


def test_unreachable_camera_and_empty_slot_are_explained(tmp_path):
    rt, sent, _ = make(tmp_path, host="")
    assert not rt.apply("2")
    assert rt.message.startswith("Камера недоступна для керування")
    rt2, sent2, _ = make(tmp_path / "b")
    rt2.clearSlot("7")
    assert not rt2.apply("7") and rt2.message.startswith("Цей слот порожній")
    assert sent == [] and sent2 == []


def test_a_failed_apply_keeps_the_old_preset(tmp_path):
    rt, _, _ = make(tmp_path, result={"state": "no-access", "message": "Немає доступу"})
    rt.apply("3")
    assert rt.activeKey == "" and rt.message == "Немає доступу" and not rt.messageOk


def test_saving_and_clearing_slots_validates_values(tmp_path):
    rt, _, store = make(tmp_path)
    good = {"name": "Ніч", "size": "1280x720", "fps": 60, "bitrateKbps": 3000, "gopS": 0.5}
    assert rt.saveSlot("9", good)
    assert rt.slots[7]["name"] == "Ніч" and store.load()["c1"]["slots"]["9"]["fps"] == 60
    assert "auto" not in store.load()["c1"]["slots"]["9"], "edited by the pilot"
    for bad in (
        {**good, "size": "1x1; reboot"},
        {**good, "fps": 25},
        {**good, "bitrateKbps": 10},
        {**good, "name": " "},
    ):
        assert not rt.saveSlot("8", bad), bad
    assert rt.slots[6]["name"] == "Високий", "a refused value changes nothing"
    rt.apply("9")
    assert rt.clearSlot("9") and rt.activeKey == ""


def test_presets_belong_to_each_camera(tmp_path):
    rt, _, _ = make(tmp_path)
    rt.saveSlot("5", {"name": "Моє", "size": "1280x720", "fps": 30, "bitrateKbps": 3000, "gopS": 1})
    rt.apply("5")
    rt._devices.activeId = "c2"
    assert rt.activeKey == "" and rt.slots[3]["name"] == "Нижче середнього"


@pytest.mark.parametrize("kbps", [100, 30000])
def test_bitrate_commands_refuse_out_of_range(kbps):
    with pytest.raises(ValueError):
        vp.bitrate_commands(kbps)


def test_run_on_camera_uses_one_login_and_ignores_the_reload_code():
    ran = []

    class Session:
        def run(self, line):
            ran.append(line)
            return (1, "") if line.startswith("killall") else (0, "")

    class Shell:
        def __init__(self, *a):
            pass

        def __enter__(self):
            return Session()

        def __exit__(self, *a):
            return False

    result = vp.run_on_camera("10.0.0.2", [("root", "12345")], Shell, vp.bitrate_commands(2048))
    assert result == {"state": "applied"} and ran == ["cli -s .video0.bitrate 2048", "killall -1 majestic"]


def test_auto_decider_steps_down_on_a_bad_link_and_up_after_a_long_good_one():
    d = vp.AutoDecider(target_ms=150)
    bad = {"lossPct": 5, "jitterMs": 3, "latencyMs": 60}
    good = {"lossPct": 0, "jitterMs": 3, "latencyMs": 60}
    assert [d.update(bad, t) for t in range(3)] == [0, 0, -1]
    assert [d.update(bad, t) for t in range(3, 12)] == [0] * 9, "at least 10 s between changes"
    assert d.update(bad, 13) == -1
    assert [d.update(good, t) for t in range(14, 43)] == [0] * 29
    assert d.update(good, 43) == 1, "30 good seconds"
    assert d.update({"lost": True}, 44) == 0, "nothing changes while the video is lost"
    assert vp.AutoDecider(150).bad({"latencyMs": 200}), "100 + 60 ms to the screen is over 150"
    assert not vp.AutoDecider(150).bad({"latencyMs": 120}), "60 + 60 ms is within 150"


def test_auto_moves_between_this_cameras_own_presets(tmp_path):
    clock = [0.0]
    sent = []
    store = vp.VideoPresetStore(tmp_path / "v.json")
    rt = vp.VideoPresetsRuntime(
        store,
        Devices(),
        Connections(),
        lambda h, lines: sent.append(lines) or {"state": "applied"},
        run_async=False,
        clock=lambda: clock[0],
    )
    rt.apply("6")
    assert rt.choose("1"), "key 1 is Auto"
    assert rt.auto and rt.label == "Авто · 6 · Середній · 2 Мбіт/с"
    for _ in range(3):
        clock[0] += 1
        rt.observe({"lossPct": 6, "jitterMs": 2})
    assert rt.activeKey == "5", "one step down"
    assert rt.choose("5") and not rt.auto, "the pilot's key wins over Auto"


def test_key_1_starts_auto_from_the_middle_preset_when_none_was_chosen(tmp_path):
    rt, sent, _ = make(tmp_path)
    assert rt.choose("1") and rt.auto and rt.activeKey == "6"


def test_the_ladder_keeps_enough_data_per_pixel_and_smoothness_first():
    for kbps in vp.LADDER_KBPS:
        size, fps = vp.picture_for(kbps)
        w, h = (int(x) for x in size.split("x"))
        assert fps >= 30
        if (size, fps) != vp.PICTURES[0]:
            assert kbps * 1000 / (w * h * fps) >= vp.MIN_BITS_PER_PIXEL, (kbps, size, fps)
    assert vp.picture_for(3072) == ("1280x720", 60), "60 fps before 1080p"
    assert vp.picture_for(8192) == ("1920x1080", 60)
    assert max(vp.LADDER_KBPS) <= 6144, "Starlink on the drone carries at most ~6 Mbit/s"
    assert sum(k <= 2560 for k in vp.LADDER_KBPS) >= 6, "most steps where Starlink works reliably"


def test_rebuild_brings_back_the_stations_presets(tmp_path):
    rt, _, _ = make(tmp_path)
    rt.saveSlot("4", {"name": "Моє", "size": "1920x1080", "fps": 30, "bitrateKbps": 3000, "gopS": 2})
    assert rt.rebuildLadder() and rt.slots[2]["name"] == "Слабкий канал"


def test_an_older_camera_without_cbr_still_gets_the_preset():
    ran = []

    class Session:
        def run(self, line):
            ran.append(line)
            return (1, "unknown key") if "rcMode" in line else (0, "")

    class Shell:
        def __init__(self, *a):
            pass

        def __enter__(self):
            return Session()

        def __exit__(self, *a):
            return False

    preset = vp.build_ladder()["6"]
    assert vp.run_on_camera("10.0.0.2", [("root", "12345")], Shell, vp.commands(preset)) == {"state": "applied"}
    assert len(ran) == 6
