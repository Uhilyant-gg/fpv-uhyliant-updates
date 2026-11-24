from pathlib import Path


def test_shared_ui_tokens_define_approved_visual_system():
    source = Path(__file__).with_name("UiTokens.qml").read_text(encoding="utf-8")
    for expected in ('fontFamily: "Segoe UI Variable"','canvas: "#07101A"','chrome: "#0A111B"','surface: "#0D1723"','foreground: "#F7F9FC"','primary: "#168AFF"','ready: "#2BD89F"','attention: "#FFB84D"','problem: "#FF6678"',"radiusCard: 16","controlHeight: 40","chromeHeight: 44"):
        assert expected in source


def test_tokens_are_registered_as_qml_singleton():
    qmldir = Path(__file__).with_name("qmldir").read_text(encoding="utf-8")
    assert "singleton UiTokens 1.0 UiTokens.qml" in qmldir


def test_primary_surfaces_consume_shared_tokens():
    root = Path(__file__).parent
    for name in ("ModernWindowChrome.qml", "HomePanel.qml", "DevicesPanel.qml"):
        source = (root / name).read_text(encoding="utf-8")
        assert "UiTokens." in source
    home = (root / "HomePanel.qml").read_text(encoding="utf-8")
    devices = (root / "DevicesPanel.qml").read_text(encoding="utf-8")
    assert 'property color fg:' not in home
    assert 'property color fg:' not in devices
