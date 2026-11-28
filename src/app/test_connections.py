import json

import pytest
from PySide6.QtCore import QObject, Signal

import connection_profiles as cp
from connections_runtime import ConnectionsRuntime


@pytest.mark.parametrize(
    "kind,value,expected",
    [
        ("static", " 93.170.12.5 ", "93.170.12.5"),
        ("static", "Drone.DDNS.net", "drone.ddns.net"),
        ("starlink", "2001:db8::10", "2001:db8::10"),
        ("starlink", "[2001:0db8:0000::0010]", "2001:db8::10"),
    ],
)
def test_valid_addresses(kind, value, expected):
    assert cp.validate_address(kind, value) == expected


@pytest.mark.parametrize(
    "kind,value",
    [
        ("static", ""),
        ("static", "0.0.0.0"),
        ("static", "127.0.0.1"),
        ("static", "999.1.1.1"),
        ("static", "bad host!"),
        ("starlink", "93.170.12.5"),
        ("starlink", "::1"),
        ("starlink", "not-an-address"),
        ("local", "192.168.1.10"),
    ],
)
def test_invalid_addresses(kind, value):
    with pytest.raises(ValueError):
        cp.validate_address(kind, value)


def test_status_labels_and_fly_rule():
    assert cp.status_entry("available", 12)["label"] == "12 мс"
    assert cp.status_entry("unconfigured")["label"] == "вказати адресу"
    assert cp.status_entry("unsupported")["label"] == "немає сервера"
    statuses = {"local": cp.status_entry("available", 5), "static": cp.status_entry("unavailable")}
    assert cp.can_fly("local", statuses)
    assert not cp.can_fly("static", statuses)
    assert not cp.can_fly("", statuses)
    assert not cp.can_fly("cloud", statuses)


def test_url_host_brackets_ipv6():
    assert cp.url_host("2001:db8::10") == "[2001:db8::10]"
    assert cp.url_host("192.168.1.10") == "192.168.1.10"
    assert cp.url_host("drone.ddns.net") == "drone.ddns.net"


def test_store_ignores_invalid_entries(tmp_path):
    path = tmp_path / "connections.json"
    path.write_text(json.dumps({"c1": {"static": "1.2.3.4", "starlink": "bad"}, "c2": "x", "c3": {"static": "::"}}))
    assert cp.ConnectionStore(path).load() == {"c1": {"static": "1.2.3.4"}}
    assert cp.ConnectionStore(tmp_path / "missing.json").load() == {}


class FakeDevices(QObject):
    changed = Signal()
    streamsChanged = Signal()

    def __init__(self):
        super().__init__()
        self.items = [{"id": "c1", "host": "192.168.1.10", "onboardingState": "ready"}]
        self.streams = [{"device_id": "c1", "enabled": True, "port": 8554}]

    @property
    def homeItems(self):
        return [d for d in self.items if d.get("onboardingState") == "ready"]


class Prober:
    def __init__(self):
        self.reachable = {"192.168.1.10": 4}
        self.calls = []

    def __call__(self, host, port):
        self.calls.append((host, port))
        return self.reachable.get(host)


@pytest.fixture
def runtime(tmp_path):
    prober = Prober()
    rt = ConnectionsRuntime(FakeDevices(), cp.ConnectionStore(tmp_path / "c.json"), prober=prober, run_async=False)
    rt.prober = prober
    return rt


def test_initial_statuses(runtime):
    statuses = runtime.statuses["c1"]
    assert statuses["local"]["state"] == "checking"
    assert statuses["static"]["state"] == "unconfigured"
    assert statuses["starlink"]["state"] == "unconfigured"
    assert statuses["cloud"]["state"] == "unsupported"
    assert not runtime.canFly("c1"), "nothing is selected yet"


def test_refresh_probes_the_video_port_and_fly_needs_a_selection(runtime):
    runtime.refresh()
    assert runtime.prober.calls == [("192.168.1.10", 8554)]
    assert runtime.statuses["c1"]["local"] == cp.status_entry("available", 4)
    assert not runtime.canFly("c1")
    assert runtime.select("c1", "local")
    assert runtime.canFly("c1")


def test_unreachable_selection_cannot_fly(runtime):
    runtime.prober.reachable = {}
    runtime.select("c1", "local")
    assert runtime.statuses["c1"]["local"]["state"] == "unavailable"
    assert not runtime.canFly("c1")


def test_address_types_need_an_address(runtime, tmp_path):
    runtime.select("c1", "starlink")
    assert not runtime.canFly("c1")
    assert not runtime.setAddress("c1", "starlink", "1.2.3.4")
    runtime.prober.reachable["2001:db8::10"] = 61
    assert runtime.setAddress("c1", "starlink", "2001:db8::10")
    assert runtime.statuses["c1"]["starlink"] == cp.status_entry("available", 61)
    assert runtime.canFly("c1")
    assert runtime.addressFor("c1", "starlink") == "2001:db8::10"
    assert json.loads((tmp_path / "c.json").read_text()) == {"c1": {"starlink": "2001:db8::10"}}


def test_cloud_cannot_be_used_yet(runtime):
    assert runtime.select("c1", "cloud")
    assert not runtime.canFly("c1")
    assert not runtime.setAddress("c1", "cloud", "1.2.3.4")


def test_video_uses_the_selected_address(runtime):
    device = {"id": "c1", "host": "192.168.1.10"}
    assert runtime.host_for(device) == "192.168.1.10"
    runtime.setAddress("c1", "static", "93.170.12.5")
    runtime.select("c1", "static")
    assert runtime.host_for(device) == "93.170.12.5"


def test_stale_probe_result_is_ignored(runtime):
    runtime.setAddress("c1", "static", "93.170.12.5")
    runtime._in_flight.add(("c1", "static"))
    runtime._apply_probe("c1", "static", "10.0.0.1", 7)
    assert runtime.statuses["c1"]["static"]["state"] != "available"


def test_unknown_camera_or_type_is_rejected(runtime):
    assert not runtime.select("nope", "local")
    assert not runtime.select("c1", "radio")


def test_types_for_qml(runtime):
    assert [t["key"] for t in runtime.types] == ["local", "static", "cloud", "starlink"]
    assert [t["needsAddress"] for t in runtime.types] == [False, True, True, True]


def test_video_runtime_builds_url_from_the_selected_ipv6_address(monkeypatch):
    from video import VideoRuntime

    class Devices:
        activeStreams = [
            {"id": "s1", "device_id": "c1", "enabled": True, "protocol": "rtsp", "port": 554, "path": "stream=0"}
        ]
        items = [{"id": "c1", "host": "192.168.1.10"}]
        videoProfiles = []

    video = VideoRuntime(Devices())
    video.host_resolver = lambda device: "2001:db8::10"
    monkeypatch.setattr(video, "_check_endpoint", lambda: True)
    assert video.prepare("s1")
    assert video.url == "rtsp://[2001:db8::10]:554/stream=0"


def test_clear_address_unselects_and_forgets(runtime, tmp_path):
    runtime.prober.reachable["93.170.12.5"] = 20
    runtime.setAddress("c1", "static", "93.170.12.5")
    runtime.select("c1", "static")
    assert runtime.canFly("c1")
    runtime.clearAddress("c1", "static")
    assert runtime.selected == {}
    assert runtime.statuses["c1"]["static"]["state"] == "unconfigured"
    assert json.loads((tmp_path / "c.json").read_text()) == {}
    runtime.clearAddress("c1", "starlink")  # nothing saved: no error


class FakeZeroTier:
    def __init__(self):
        self.state = {
            "service": "ok",
            "nodeId": "a1b2c3d4e5",
            "networks": {"8056c2e21c000001": {"status": "OK", "name": ""}},
            "peers": {"89e92ceee5": {"latency": 40, "direct": True}},
        }
        self.joined = []

    def snapshot(self):
        return self.state

    def join(self, network):
        self.joined.append(network)
        self.state["networks"][network] = {"status": "REQUESTING_CONFIGURATION", "name": ""}
        return True


@pytest.fixture
def zt_runtime(tmp_path):
    prober = Prober()
    zerotier = FakeZeroTier()
    rt = ConnectionsRuntime(
        FakeDevices(), cp.ConnectionStore(tmp_path / "c.json"), prober=prober, run_async=False, zerotier=zerotier
    )
    rt.prober, rt.zerotier = prober, zerotier
    return rt


CAMERA_ZT = "fd80:56c2:e21c:0:199:9389:e92c:eee5"


def test_zerotier_needs_network_and_node(zt_runtime):
    assert zt_runtime.statuses["c1"]["cloud"]["label"] == "вказати мережу"
    assert not zt_runtime.setZeroTier("c1", "bad", "89e92ceee5")
    assert not zt_runtime.setZeroTier("c1", "8056c2e21c000001", "")
    assert zt_runtime.zerotierNetworkFor("c1") == ""


def test_zerotier_camera_reachable_directly(zt_runtime, tmp_path):
    zt_runtime.prober.reachable[CAMERA_ZT] = 44
    assert zt_runtime.setZeroTier("c1", "8056C2E21C000001", "89E92CEEE5")
    assert zt_runtime.statuses["c1"]["cloud"] == cp.status_entry("available", 44, "44 мс · напряму")
    assert zt_runtime.zerotierState == "ok"
    assert zt_runtime.zerotierNodeId == "a1b2c3d4e5"
    zt_runtime.select("c1", "cloud")
    assert zt_runtime.canFly("c1")
    assert zt_runtime.host_for({"id": "c1", "host": "192.168.1.10"}) == CAMERA_ZT
    saved = json.loads((tmp_path / "c.json").read_text())
    assert saved == {"c1": {"ztNetwork": "8056c2e21c000001", "ztNode": "89e92ceee5"}}
    assert cp.ConnectionStore(tmp_path / "c.json").load() == saved


def test_zerotier_relayed_path_is_labelled(zt_runtime):
    zt_runtime.zerotier.state["peers"]["89e92ceee5"]["direct"] = False
    zt_runtime.prober.reachable[CAMERA_ZT] = 120
    zt_runtime.setZeroTier("c1", "8056c2e21c000001", "89e92ceee5")
    assert zt_runtime.statuses["c1"]["cloud"]["label"] == "120 мс · через сервер"


def test_selecting_zerotier_joins_the_camera_network_and_waits_for_permission(zt_runtime):
    zt_runtime.zerotier.state["networks"] = {}
    zt_runtime.setZeroTier("c1", "8056c2e21c000001", "89e92ceee5")
    assert zt_runtime.statuses["c1"]["cloud"]["label"] == "не в мережі"
    zt_runtime.select("c1", "cloud")
    assert zt_runtime.zerotier.joined == ["8056c2e21c000001"]
    assert zt_runtime.statuses["c1"]["cloud"]["label"] == "чекає дозволу"
    assert not zt_runtime.canFly("c1")


@pytest.mark.parametrize(
    "service,label",
    [("missing", "встановіть ZeroTier"), ("stopped", "ZeroTier вимкнено"), ("no-access", "немає доступу")],
)
def test_zerotier_service_problems_are_shown_on_the_card(zt_runtime, service, label):
    zt_runtime.zerotier.state = {"service": service, "nodeId": "", "networks": {}, "peers": {}}
    zt_runtime.setZeroTier("c1", "8056c2e21c000001", "89e92ceee5")
    assert zt_runtime.statuses["c1"]["cloud"]["label"] == label
    assert zt_runtime.zerotierText


def test_clearing_zerotier_unselects(zt_runtime):
    zt_runtime.prober.reachable[CAMERA_ZT] = 44
    zt_runtime.setZeroTier("c1", "8056c2e21c000001", "89e92ceee5")
    zt_runtime.select("c1", "cloud")
    assert zt_runtime.setZeroTier("c1", "", "")
    assert zt_runtime.selected == {}
    assert zt_runtime.statuses["c1"]["cloud"]["label"] == "вказати мережу"
