from pathlib import Path


def test_modern_chrome_has_safe_window_actions_without_close_button():
    source = Path(__file__).with_name("ModernWindowChrome.qml").read_text(encoding="utf-8")
    assert "startSystemMove" in source
    assert "showMinimized" in source
    assert "showMaximized" in source
    assert "showNormal" in source
    assert "window.close()" not in source
    assert 'text: "×"' not in source


def test_modern_chrome_uses_current_visual_tokens():
    source = Path(__file__).with_name("ModernWindowChrome.qml").read_text(encoding="utf-8")
    assert 'font.family: "Segoe UI Variable"' in source
    assert 'background: "#0A111B"' in source
    assert 'foreground: "#F7F9FC"' in source
    assert 'muted: "#8EA0B5"' in source
