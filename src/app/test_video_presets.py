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


def test_ten_slots_on_keys_1_to_0_with_defaults_from_the_weakest_link(tmp_path):
    rt, _, _ = make(tmp_path)
    keys = [s["key"] for s in rt.slots]
    assert keys == ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
    assert rt.slots[0]["name"] == "Слабкий канал" and rt.slots[0]["bitrateKbps"] == 1024
    assert rt.slots[4]["empty"] and rt.slots[9]["empty"]
    assert rt.label == "Пресет відео не вибрано"


def test_applying_a_preset_writes_it_into_the_camera(tmp_path):
    rt, sent, store = make(tmp_path)
    assert rt.apply("3")
    assert sent == [
        (
            "10.147.17.5",
            [
                "cli -s .video0.size 1920x1080",
                "cli -s .video0.fps 30",
                "cli -s .video0.bitrate 4096",
                "cli -s .video0.gopSize 1",
                "killall -1 majestic",
            ],
        )
    ]
    assert rt.activeKey == "3" and rt.label == "3 · Баланс · 4 Мбіт/с"
    assert rt.message == "Пресет 3 «Баланс» застосовано в камері" and rt.messageOk
    assert store.load()["c1"]["active"] == "3", "remembered for this camera"


def test_quick_bitrate_steps_mark_the_preset_as_changed(tmp_path):
    rt, sent, _ = make(tmp_path)
    rt.apply("3")
    assert rt.stepBitrate(-1)
    assert sent[-1][1] == ["cli -s .video0.bitrate 3072", "killall -1 majestic"]
    assert rt.label == "3 · Баланс* · 3 Мбіт/с"
    rt.stepBitrate(+1)
    rt.stepBitrate(+1)
    assert rt.bitrateKbps == 6144
    assert not rt.setBitrate(50000), "out of range never reaches the camera"


def test_unreachable_camera_and_empty_slot_are_explained(tmp_path):
    rt, sent, _ = make(tmp_path, host="")
    assert not rt.apply("1")
    assert rt.message.startswith("Камера недоступна для керування")
    rt2, sent2, _ = make(tmp_path / "b")
    assert not rt2.apply("7") and rt2.message.startswith("Цей слот порожній")
    assert sent == [] and sent2 == []


def test_a_failed_apply_keeps_the_old_preset(tmp_path):
    rt, _, _ = make(tmp_path, result={"state": "no-access", "message": "Немає доступу"})
    rt.apply("2")
    assert rt.activeKey == "" and rt.message == "Немає доступу" and not rt.messageOk


def test_saving_and_clearing_slots_validates_values(tmp_path):
    rt, _, store = make(tmp_path)
    good = {"name": "Ніч", "size": "1280x720", "fps": 60, "bitrateKbps": 3000, "gopS": 0.5}
    assert rt.saveSlot("9", good)
    assert rt.slots[8]["name"] == "Ніч" and store.load()["c1"]["slots"]["9"]["fps"] == 60
    for bad in (
        {**good, "size": "1x1; reboot"},
        {**good, "fps": 25},
        {**good, "bitrateKbps": 10},
        {**good, "name": " "},
    ):
        assert not rt.saveSlot("8", bad), bad
    assert rt.slots[7]["empty"]
    rt.apply("9")
    assert rt.clearSlot("9") and rt.activeKey == ""


def test_presets_belong_to_each_camera(tmp_path):
    rt, _, _ = make(tmp_path)
    rt.apply("4")
    rt._devices.activeId = "c2"
    assert rt.activeKey == "" and rt.slots[3]["name"] == "Якість"


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
