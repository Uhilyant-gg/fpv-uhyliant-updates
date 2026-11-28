from PySide6.QtCore import QCoreApplication

import link_test as lt

APP = QCoreApplication.instance() or QCoreApplication([])


def run(samples):
    rt = lt.LinkTestRuntime(lambda: samples[len(rt._samples) % len(samples)], duration_s=20)
    rt.start()
    assert rt.running and rt.secondsLeft == 20
    for _ in range(20):
        rt.tick()
    assert not rt.running and rt.progress == 1.0
    return rt.result


def test_a_good_link_over_starlink():
    result = run([{"reachable": True, "latencyMs": 50, "video": True, "fps": 30, "lossPct": 0}])
    assert result["level"] == "ok" and result["title"].startswith("Можна летіти")
    assert "Затримка зв’язку: у середньому 50 мс, найбільша 50 мс." in result["lines"]


def test_a_camera_that_does_not_answer():
    result = run([{"reachable": False}])
    assert result["level"] == "bad" and "не відповідає" in result["title"]


def test_slow_link_advises_the_auto_preset():
    result = run([{"reachable": True, "latencyMs": 220, "video": True, "fps": 30, "lossPct": 0}])
    assert result["level"] == "warning"
    assert any("170 мс" in line and "«Авто»" in line for line in result["lines"]), result["lines"]


def test_video_dropouts_and_losses():
    samples = [{"reachable": True, "latencyMs": 40, "video": True, "fps": 30, "lossPct": 2.5}] * 16 + [
        {"reachable": True, "latencyMs": 40, "video": True, "lost": True, "fps": 0}
    ] * 4
    rt = lt.LinkTestRuntime(lambda: samples[len(rt._samples)], duration_s=20)
    rt.start()
    for _ in range(20):
        rt.tick()
    assert rt.result["level"] == "bad"
    assert "Відео зникало на 4 с за тест." in rt.result["lines"]
    assert any("2,5% пакетів" in line for line in rt.result["lines"])


def test_without_the_flight_screen_only_the_link_is_checked():
    result = run(
        [{"reachable": True, "latencyMs": 30}, {"reachable": False}] + [{"reachable": True, "latencyMs": 30}] * 8
    )
    assert result["level"] == "warning"
    assert any("не відповіла 2 раз(и) з 20" in line for line in result["lines"]), result["lines"]
    assert any("Відео не перевірялося" in line for line in result["lines"])


def test_jumpy_latency():
    result = run([{"reachable": True, "latencyMs": 30}, {"reachable": True, "latencyMs": 140}])
    assert any("скаче на 110 мс" in line for line in result["lines"]), result["lines"]


def test_a_camera_pushing_to_a_static_ip():
    result = run([{"reachable": True, "pushed": True, "video": True, "fps": 30, "lossPct": 0}])
    assert result["level"] == "ok"
    assert "Затримку зв’язку не виміряти: камера сама надсилає відео на статичний IP." in result["lines"]
