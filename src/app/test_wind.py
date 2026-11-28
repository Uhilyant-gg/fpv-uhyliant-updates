from PySide6.QtCore import QCoreApplication

import wind

APP = QCoreApplication.instance() or QCoreApplication([])

ANSWER = {
    "current": {
        "wind_speed_10m": 3.2,
        "wind_direction_10m": 270,
        "wind_speed_80m": 5.1,
        "wind_direction_80m": 280,
        "wind_speed_120m": 6.04,
        "wind_direction_120m": 285,
        "wind_speed_180m": 7.0,
        "wind_direction_180m": 290,
        "wind_gusts_10m": 8.3,
    }
}


class Telemetry:
    telemetry = {}


class Clock:
    t = 0.0

    def __call__(self):
        return self.t


def test_level_and_parsing():
    assert [wind.level_for(a) for a in (None, 0, 50, 100, 130, 400)] == [10, 10, 80, 80, 120, 180]
    assert wind.parse(ANSWER, 120) == {"speedMs": 6.0, "fromDeg": 285.0, "gustMs": 8.3, "levelM": 120}
    assert wind.parse({"current": {"wind_speed_10m": 1, "wind_direction_10m": 10}}, 180)["levelM"] == 10
    url = wind.request_url(50.4501, 30.5234)
    assert "latitude=50.45&longitude=30.5" in url, "the position is rounded before it leaves the PC"
    assert wind.compass(285) == "Зх" and wind.compass(0) == "Пн" and wind.compass(135) == "ПдСх"


def test_asked_for_the_drone_and_again_only_when_needed():
    asked = []
    telemetry, clock = Telemetry(), Clock()
    rt = wind.WindRuntime(telemetry, fetcher=lambda url: asked.append(url) or ANSWER, run_async=False, clock=clock)
    rt.setActive(True)
    assert not rt.available and "чекаю координати" in rt.text and asked == []
    telemetry.telemetry = {"latitude": 50.45, "longitude": 30.52, "altitude": 110}
    rt.check()
    assert rt.text == "Вітер Зх 6 м/с, пориви 8,3 · 120 м"
    rt.check()
    assert len(asked) == 1, "not again within 10 minutes at the same place"
    telemetry.telemetry = {"latitude": 50.55, "longitude": 30.52, "altitude": 110}
    rt.check()
    assert len(asked) == 2, "moved more than 5 km"
    clock.t += wind.REFRESH_S
    rt._fetcher = lambda url: (_ for _ in ()).throw(OSError("offline"))
    rt.check()
    assert rt.available and rt.wind["levelM"] == 120, "the last known wind is kept when the internet is gone"
