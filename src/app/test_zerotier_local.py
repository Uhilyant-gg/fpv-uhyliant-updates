import urllib.error

import pytest

import zerotier_local as zt


def test_rfc4193_address_matches_zerotier_layout():
    # fd + network ID + 9993 + node ID
    assert zt.rfc4193_address("8056c2e21c000001", "89e92ceee5") == "fd80:56c2:e21c:0:199:9389:e92c:eee5"
    assert zt.rfc4193_address("8056C2E21C000001", " 89E92CEEE5 ") == "fd80:56c2:e21c:0:199:9389:e92c:eee5"


@pytest.mark.parametrize("value", ["", "123", "8056c2e21c00000g", "8056c2e21c0000011"])
def test_invalid_network_ids(value):
    with pytest.raises(ValueError):
        zt.validate_network_id(value)


@pytest.mark.parametrize("value", ["", "89e92ceee", "0000000000", "89e92ceeez"])
def test_invalid_node_ids(value):
    with pytest.raises(ValueError):
        zt.validate_node_id(value)


def test_token_is_read_from_the_first_readable_file(tmp_path):
    missing = tmp_path / "missing"
    empty = tmp_path / "empty"
    empty.write_text("  ")
    good = tmp_path / "good"
    good.write_text("secret-token\n")
    assert zt.read_token([missing, empty, good]) == "secret-token"
    assert zt.read_token([missing]) == ""


def test_windows_token_locations():
    paths = zt.token_candidates({"LOCALAPPDATA": r"C:\Users\p\AppData\Local", "PROGRAMDATA": r"C:\ProgramData"})
    text = [str(p) for p in paths]
    assert any("Local" in t and "authtoken.secret" in t for t in text)
    assert any("ProgramData" in t and "One" in t for t in text)


def make(responses, token="tok", installed=True):
    calls = []

    def request(method, path, token_value, body):
        calls.append((method, path, token_value, body))
        value = responses[(method, path)]
        if isinstance(value, Exception):
            raise value
        return value

    client = zt.ZeroTierLocal(request=request, token_paths=[], installed=lambda: installed)
    client._token = lambda: token
    client.calls = calls
    return client


RESPONSES = {
    ("GET", "/status"): {"address": "a1b2c3d4e5", "online": True},
    ("GET", "/network"): [
        {"id": "8056C2E21C000001", "status": "OK", "name": "Квадрик"},
        {"id": "1111111111111111", "status": "ACCESS_DENIED"},
    ],
    ("GET", "/peer"): [
        {"address": "89e92ceee5", "role": "LEAF", "latency": 42, "paths": [{"active": True, "expired": False}]},
        {"address": "1234567890", "role": "LEAF", "latency": 130, "paths": []},
        {"address": "778cde7190", "role": "PLANET", "latency": 20, "paths": [{"active": True}]},
    ],
}


def test_snapshot_reads_service_networks_and_peers():
    snapshot = make(RESPONSES).snapshot()
    assert snapshot["service"] == "ok"
    assert snapshot["nodeId"] == "a1b2c3d4e5"
    assert snapshot["networks"]["8056c2e21c000001"]["status"] == "OK"
    assert snapshot["peers"] == {
        "89e92ceee5": {"latency": 42, "direct": True},
        "1234567890": {"latency": 130, "direct": False},
    }, "root servers are not cameras"


def test_snapshot_states():
    assert make(RESPONSES, token="", installed=False).snapshot()["service"] == "missing"
    assert make(RESPONSES, token="", installed=True).snapshot()["service"] == "no-access"
    refused = {**RESPONSES, ("GET", "/status"): urllib.error.URLError("refused")}
    assert make(refused).snapshot()["service"] == "stopped"
    denied = {**RESPONSES, ("GET", "/status"): urllib.error.HTTPError("u", 401, "no", {}, None)}
    assert make(denied).snapshot()["service"] == "no-access"
    offline = {**RESPONSES, ("GET", "/status"): {"address": "a1b2c3d4e5", "online": False}}
    assert make(offline).snapshot()["service"] == "offline"


def test_join_posts_to_the_local_service_only_for_valid_ids():
    client = make({("POST", "/network/8056c2e21c000001"): {}})
    assert client.join("8056C2E21C000001")
    assert client.calls == [("POST", "/network/8056c2e21c000001", "tok", b"{}")]
    assert not client.join("bad")


def test_cloud_status_explains_every_blocker():
    snapshot = make(RESPONSES).snapshot()
    assert zt.cloud_status(snapshot, "8056c2e21c000001", "89e92ceee5") == ("ready", "")
    assert zt.cloud_status(snapshot, "1111111111111111", "89e92ceee5") == ("unavailable", "чекає дозволу")
    assert zt.cloud_status(snapshot, "2222222222222222", "89e92ceee5") == ("unavailable", "не в мережі")
    assert zt.cloud_status(snapshot, "8056c2e21c000001", "aaaaaaaaaa") == ("unavailable", "камера не в мережі")
    assert zt.cloud_status({"service": "missing"}, "8056c2e21c000001", "89e92ceee5")[1] == "встановіть ZeroTier"
    assert zt.cloud_status({"service": "stopped"}, "8056c2e21c000001", "89e92ceee5")[1] == "ZeroTier вимкнено"


def test_path_label():
    snapshot = make(RESPONSES).snapshot()
    assert zt.path_label(snapshot, "89e92ceee5", 45) == "45 мс · напряму"
    assert zt.path_label(snapshot, "1234567890", 120) == "120 мс · через сервер"
