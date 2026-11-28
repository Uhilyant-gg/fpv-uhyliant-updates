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
    assert json.loads((tmp_path / "c.json").read_text()) == {
        "c1": {"starlink": "2001:db8::10", "starlinkSource": "manual"}
    }


def test_cloud_cannot_be_used_yet(runtime):
    assert runtime.select("c1", "cloud")
    assert not runtime.canFly("c1")
    assert not runtime.setAddress("c1", "cloud", "1.2.3.4")


def test_video_uses_the_selected_address(runtime):
    device = {"id": "c1", "host": "192.168.1.10"}
    assert runtime.host_for(device) == "192.168.1.10"
    runtime.setAddress("c1", "starlink", "2001:db8::10")
    runtime.select("c1", "starlink")
    assert runtime.host_for(device) == "2001:db8::10"


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
    runtime.prober.reachable["2001:db8::10"] = 20
    runtime.setAddress("c1", "starlink", "2001:db8::10")
    runtime.select("c1", "starlink")
    assert runtime.canFly("c1")
    runtime.clearAddress("c1", "starlink")
    assert runtime.selected == {}
    assert runtime.statuses["c1"]["starlink"]["state"] == "unconfigured"
    assert json.loads((tmp_path / "c.json").read_text()) == {}
    runtime.clearAddress("c1", "static")  # nothing saved: no error


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
    assert saved == {"c1": {"ztNetwork": "8056c2e21c000001", "ztNode": "89e92ceee5", "ztSource": "manual"}}
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


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def push_runtime(tmp_path):
    clock = Clock()
    results = []

    def binder(port):
        results.append(port)
        return push_runtime.bind_result

    rt = ConnectionsRuntime(
        FakeDevices(),
        cp.ConnectionStore(tmp_path / "c.json"),
        prober=Prober(),
        run_async=False,
        listen=False,
        sdp_folder=tmp_path / "sdp",
        binder=binder,
        clock=clock,
    )
    rt.clock, rt.bind_ports = clock, results
    push_runtime.bind_result = {"state": "ready", "publicIp": "93.170.12.5", "message": "Готово"}
    return rt


def test_static_ip_waits_for_the_camera_to_send_video(push_runtime, tmp_path):
    rt = push_runtime
    assert rt.setAddress("c1", "static", "93.170.12.5")
    assert rt.pushPortFor("c1") == 5600
    assert rt.statuses["c1"]["static"]["label"] == "чекає камеру"
    rt.select("c1", "static")
    assert not rt.canFly("c1")

    rt._note_packet(5600)
    assert rt.statuses["c1"]["static"] == cp.status_entry("available", None, "камера надсилає")
    assert rt.canFly("c1")

    url = rt.push_url_for({"id": "c1"})
    assert url.startswith("file://") and url.endswith("push-c1.sdp")
    assert "m=video 5600 RTP/AVP 97" in (tmp_path / "sdp" / "push-c1.sdp").read_text()
    assert rt.host_for({"id": "c1", "host": "192.168.1.10"}) == "192.168.1.10"

    rt.clock.now += 5
    rt.refresh()
    assert rt.statuses["c1"]["static"]["label"] == "чекає камеру", "no packets for a while"
    assert not rt.canFly("c1")


def test_push_url_only_for_the_static_choice(push_runtime):
    rt = push_runtime
    rt.setAddress("c1", "static", "93.170.12.5")
    assert rt.push_url_for({"id": "c1"}) == ""
    rt.select("c1", "local")
    assert rt.push_url_for({"id": "c1"}) == ""


def test_push_ports_are_unique_and_saved(push_runtime, tmp_path):
    rt = push_runtime
    rt._addresses["other"] = {"pushPort": 5600}
    rt.setAddress("c1", "static", "93.170.12.5")
    assert rt.pushPortFor("c1") == 5602
    assert cp.ConnectionStore(tmp_path / "c.json").load()["c1"]["pushPort"] == 5602


def test_bind_this_network_fills_the_static_address(push_runtime):
    rt = push_runtime
    rt.bindThisNetwork("c1")
    assert rt.bind_ports == [5600]
    assert rt.bindStatus["state"] == "ready" and not rt.bindStatus["busy"]
    assert rt.addressFor("c1", "static") == "93.170.12.5"


def test_bind_on_a_grey_network_keeps_the_address_empty(push_runtime):
    rt = push_runtime
    push_runtime_result = {"state": "grey", "publicIp": "93.170.12.5", "message": "сіру"}
    rt._binder = lambda port: push_runtime_result
    rt.bindThisNetwork("c1")
    assert rt.bindStatus["state"] == "grey"
    assert rt.addressFor("c1", "static") == ""


@pytest.fixture
def setup_runtime(tmp_path):
    clock = Clock()
    calls = []
    prober = Prober()

    def camera_setup(host, address, port):
        calls.append((host, address, port))
        return rt.result

    rt = ConnectionsRuntime(
        FakeDevices(),
        cp.ConnectionStore(tmp_path / "c.json"),
        prober=prober,
        run_async=False,
        listen=False,
        sdp_folder=tmp_path / "sdp",
        clock=clock,
        camera_setup=camera_setup,
    )
    rt.clock, rt.calls, rt.store_path, rt.prober = clock, calls, tmp_path / "c.json", prober
    rt.result = {"state": "configured", "message": "ok", "codec": "h264"}
    return rt


def test_camera_is_configured_automatically_when_on_the_local_network(setup_runtime):
    rt = setup_runtime
    rt.refresh()  # the camera answers on the local network
    rt.setAddress("c1", "static", "93.170.12.5")
    assert rt.calls == [("192.168.1.10", "93.170.12.5", 5600)]
    assert rt.cameraSetup["c1"]["state"] == "configured"
    saved = cp.ConnectionStore(rt.store_path).load()["c1"]
    assert saved["pushConfigured"] == "udp://93.170.12.5:5600" and saved["pushCodec"] == "h264"
    rt.refresh()
    assert len(rt.calls) == 1, "a configured camera is not configured again"


def test_camera_setup_waits_for_the_local_network_and_not_while_flying(setup_runtime):
    rt = setup_runtime
    rt.prober.reachable = {}
    rt.setAddress("c1", "static", "93.170.12.5")
    rt.refresh()
    assert rt.calls == [], "camera not on the local network"
    rt.prober.reachable = {"192.168.1.10": 4}
    rt.pauseListening()
    rt.refresh()
    assert rt.calls == [], "never while flying"
    rt.resumeListening()
    rt.refresh()
    assert len(rt.calls) == 1


def test_failed_setup_is_retried_later_and_shown_on_the_card(setup_runtime):
    rt = setup_runtime
    rt.refresh()
    rt.result = {"state": "no-access", "message": "пароль"}
    rt.setAddress("c1", "static", "93.170.12.5")
    assert rt.statuses["c1"]["static"]["label"] == "потрібен пароль камери"
    rt.refresh()
    assert len(rt.calls) == 1, "no immediate retry"
    rt.clock.now += 61
    rt.result = {"state": "configured", "message": "ok", "codec": "h265"}
    rt.refresh()
    assert len(rt.calls) == 2 and rt.cameraSetup["c1"]["state"] == "configured"
    assert rt.statuses["c1"]["static"]["label"] == "чекає камеру"


def test_retry_runs_at_once_after_a_new_password(setup_runtime):
    rt = setup_runtime
    rt.refresh()
    rt.result = {"state": "no-access", "message": "пароль"}
    rt.setAddress("c1", "static", "93.170.12.5")
    rt.result = {"state": "configured", "message": "ok", "codec": "h265"}
    rt.retryCameraSetup("c1")
    assert len(rt.calls) == 2 and rt.cameraSetup["c1"]["state"] == "configured"


def test_payload_type_is_learnt_from_packets(setup_runtime, tmp_path):
    rt = setup_runtime
    rt.setAddress("c1", "static", "93.170.12.5")
    rt.select("c1", "static")
    rt._note_packet(5600, payload=96)
    assert cp.ConnectionStore(rt.store_path).load()["c1"]["pushPayload"] == 96
    rt.push_url_for({"id": "c1"})
    assert "m=video 5600 RTP/AVP 96" in (tmp_path / "sdp" / "push-c1.sdp").read_text()


def test_grey_address_is_shown_on_the_card(setup_runtime):
    rt = setup_runtime
    rt._binder = lambda port: {"state": "grey", "message": "сіра"}
    rt.setAddress("c1", "static", "93.170.12.5")
    rt.bindThisNetwork("c1")
    assert rt.statuses["c1"]["static"]["label"] == "сіра адреса"


FACTS = {
    "state": "read",
    "ztInstalled": True,
    "ztNode": "89e92ceee5",
    "ztNetwork": "8056c2e21c000001",
    "ipv6": ["2a0d:3344:1:2::10"],
    "flashMb": 16,
    "freeKb": 7120,
    "firmware": "OpenIPC",
    "variant": "fpv",
    "version": "2.5",
}


@pytest.fixture
def inspect_runtime(tmp_path):
    clock = Clock()
    calls = []
    prober = Prober()
    zerotier = FakeZeroTier()

    def inspect(host):
        calls.append(host)
        return rt.facts

    rt = ConnectionsRuntime(
        FakeDevices(),
        cp.ConnectionStore(tmp_path / "c.json"),
        prober=prober,
        run_async=False,
        listen=False,
        clock=clock,
        zerotier=zerotier,
        camera_inspect=inspect,
    )
    rt.clock, rt.calls, rt.prober, rt.facts, rt.store_path = clock, calls, prober, dict(FACTS), tmp_path / "c.json"
    return rt


def test_ids_are_read_from_the_camera_on_the_local_network(inspect_runtime):
    rt = inspect_runtime
    rt.prober.reachable[CAMERA_ZT] = 40
    rt.refresh()
    assert rt.calls == ["192.168.1.10"]
    assert rt.zerotierNetworkFor("c1") == "8056c2e21c000001" and rt.zerotierNodeFor("c1") == "89e92ceee5"
    assert rt.cameraFacts["c1"]["ztFromCamera"]
    assert rt.cameraFacts["c1"]["summary"].startswith("OpenIPC fpv 2.5 · флеш 16 МБ")
    assert rt.addressFor("c1", "starlink") == "", "on the local network the IPv6 is not Starlink's"
    assert rt.statuses["c1"]["cloud"]["label"] == "40 мс · напряму", "ZeroTier works without typing anything"
    rt.refresh()
    assert len(rt.calls) == 1, "not twice within the same periodic check"
    rt.clock.now += 5
    rt.refresh()
    assert len(rt.calls) == 2, "read again on the next 5-second check"


def test_manual_zerotier_ids_are_not_overwritten(inspect_runtime):
    rt = inspect_runtime
    rt.setZeroTier("c1", "2222222222222222", "1234567890")
    rt.refresh()
    assert rt.zerotierNetworkFor("c1") == "2222222222222222"
    assert not rt.cameraFacts["c1"]["ztFromCamera"]


def test_starlink_ipv6_is_taken_when_the_camera_is_seen_through_zerotier(inspect_runtime):
    rt = inspect_runtime
    rt.prober.reachable = {CAMERA_ZT: 45}  # not on the local network: in the field
    rt.setZeroTier("c1", "8056c2e21c000001", "89e92ceee5")
    rt.refresh()
    assert rt.calls == [CAMERA_ZT]
    assert rt.addressFor("c1", "starlink") == "2a0d:3344:1:2::10"
    assert rt.cameraFacts["c1"]["starlinkFromCamera"]


def test_not_read_while_flying_or_when_unreachable(inspect_runtime):
    rt = inspect_runtime
    rt.prober.reachable = {}
    rt.refresh()
    assert rt.calls == []
    rt.prober.reachable = {"192.168.1.10": 4}
    rt.pauseListening()
    rt.refresh()
    assert rt.calls == []


def test_failed_read_is_retried_after_a_minute(inspect_runtime):
    rt = inspect_runtime
    rt.facts = {"state": "no-access"}
    rt.refresh()
    rt.refresh()
    assert len(rt.calls) == 1
    rt.clock.now += 61
    rt.facts = dict(FACTS)
    rt.refresh()
    assert len(rt.calls) == 2 and rt.zerotierNodeFor("c1") == "89e92ceee5"


def test_camera_is_read_as_soon_as_it_answers(inspect_runtime):
    rt = inspect_runtime
    rt.select("c1", "local")  # the probe answers right away (synchronous in tests)
    assert rt.calls == ["192.168.1.10"], "no need to wait for the next periodic check"


def test_flight_closes_camera_sessions_and_stops_reading(inspect_runtime):
    rt = inspect_runtime
    closed = []
    rt._camera_inspect_close = lambda: closed.append(True)
    rt.refresh()
    assert len(rt.calls) == 1
    rt.pauseListening()
    assert closed == [True], "sessions are closed before the flight"
    for _ in range(5):
        rt.clock.now += 5
        rt.refresh()
    assert len(rt.calls) == 1, "nothing is read from the camera in flight"
    rt.resumeListening()
    rt.clock.now += 5
    rt.refresh()
    assert len(rt.calls) == 2


class FakeRelay:
    made = []

    def __init__(self, listen, forward, codec="h265", starts=True):
        self.listen, self.forward, self.starts, self.codec = listen, forward, starts, codec
        self.stopped = False
        FakeRelay.made.append(self)

    def start(self):
        return self.starts

    def stop(self):
        self.stopped = True

    def window(self):
        return {"packets": 30, "lossPct": 0.0}


def test_pushed_video_goes_through_the_station_relay(push_runtime, tmp_path):
    rt = push_runtime
    FakeRelay.made = []
    rt._relay_factory = FakeRelay
    rt.setAddress("c1", "static", "93.170.12.5")
    rt.select("c1", "static")
    rt.push_url_for({"id": "c1"})
    relay = FakeRelay.made[0]
    assert relay.listen == 5600 and relay.forward != 5600 and relay.forward % 2 == 0
    assert relay.codec == "h265", "the relay knows the codec to find full frames"
    assert f"m=video {relay.forward} RTP/AVP" in (tmp_path / "sdp" / "push-c1.sdp").read_text()
    assert rt.relay_window("c1") == {"packets": 30, "lossPct": 0.0}
    rt.push_url_for({"id": "c1"})
    assert relay.stopped and len(FakeRelay.made) == 2, "a new flight replaces the old relay"
    rt.resumeListening()
    assert FakeRelay.made[1].stopped and rt.relay_window("c1") is None, "leaving the flight frees the port"


def test_without_the_relay_the_player_gets_the_push_port(push_runtime, tmp_path):
    rt = push_runtime
    rt._relay_factory = lambda listen, forward, codec: FakeRelay(listen, forward, codec, starts=False)
    rt.setAddress("c1", "static", "93.170.12.5")
    rt.select("c1", "static")
    rt.push_url_for({"id": "c1"})
    assert "m=video 5600 RTP/AVP" in (tmp_path / "sdp" / "push-c1.sdp").read_text()
    assert rt.relay_window("c1") is None


def test_control_host_reaches_the_camera_by_any_working_way(runtime):
    assert runtime.control_host("c1") == "", "nothing checked yet"
    runtime.refresh()
    assert runtime.control_host("c1") == "192.168.1.10"
    runtime.prober.reachable["2001:db8::10"] = 61
    runtime.setAddress("c1", "starlink", "2001:db8::10")
    runtime.select("c1", "starlink")
    assert runtime.control_host("c1") == "192.168.1.10", "never over Starlink's public address"
