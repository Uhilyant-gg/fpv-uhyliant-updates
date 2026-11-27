from source_text import read_source
from pathlib import Path


def test_manual_ip_edit_invalidates_previous_evidence():
    backend = read_source(Path(__file__).with_name("devices_routeaware.py"))
    qml = Path(__file__).with_name("DevicesPanel.qml").read_text(encoding="utf-8")
    assert "def invalidateManualIp" in backend
    assert "onTextEdited: manualPopup.invalidateEvidence(text)" in qml
    assert 'self._manual_result={};self._manual_requested_host="";self._set_manual("idle","","")' in backend


def test_manual_result_is_bound_to_requested_host():
    source = read_source(Path(__file__).with_name("devices_routeaware.py"))
    assert "result_host!=requested" in source
    assert "Результат перевірки не відповідає поточній адресі" in source


def test_verified_card_and_add_require_current_verified_host():
    source = Path(__file__).with_name("DevicesPanel.qml").read_text(encoding="utf-8")
    assert 'devicesModel.manualStatus === "verified"' in source
    assert 'manualIp.text.trim() === manualPopup.verifiedHost' in source
    assert 'devicesModel.manualResult.openipc === true' in source
    assert 'devicesModel.manualResult.identityVerified === true' in source


def test_successful_add_has_visible_feedback():
    source = Path(__file__).with_name("DevicesPanel.qml").read_text(encoding="utf-8")
    assert 'devicesModel.manualStatus === "added"' in source
    assert "додано до Моїх камер" in source


def test_add_discovered_normalizes_and_revalidates_host():
    source = read_source(Path(__file__).with_name("devices_routeaware.py"))
    assert "address=_safe_private_host(host)" in source
    assert 'not candidate.get("openipc")' in source
    assert 'not candidate.get("identityVerified")' in source
    assert 'not identity.get("verified")' in source
