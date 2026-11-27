import re
from pathlib import Path


def test_discovery_surfaces_auth_candidates():
    source=Path(__file__).with_name("route_discovery.py").read_text(encoding="utf-8")
    assert "authRequired" in source
    assert "_tcp_open" in source
    assert "Basic "+'"+token' in source


def test_credentials_are_requested_only_for_add():
    source=Path(__file__).with_name("DevicesPanel.qml").read_text(encoding="utf-8")
    assert "Потрібен логін" in source
    assert "authenticateAndAdd" in source
    assert re.search(r"echoMode\s*:\s*TextInput\.Password", source)


def test_authenticated_add_is_fail_closed():
    source=Path(__file__).with_name("devices_routeaware.py").read_text(encoding="utf-8")
    assert "def authenticateAndAdd" in source
    assert 'not result.get("openipc") or not result.get("identityVerified")' in source
