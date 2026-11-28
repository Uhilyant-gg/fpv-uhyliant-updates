import json
from datetime import datetime, timedelta

from PySide6.QtCore import QCoreApplication, QSettings

import flight_log as fl

APP = QCoreApplication.instance() or QCoreApplication([])


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def make(tmp_path, samples):
    clock = Clock()
    times = {"now": datetime(2026, 11, 28, 10, 0, 0)}
    opened = []
    rt = fl.BlackBoxRuntime(
        lambda: samples[min(int(clock.t), len(samples) - 1)],
        lambda: {"camera": "Квадрик 7\"", "link": "Starlink IPv6"},
        settings=QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat),
        default_folder=str(tmp_path / "box"),
        clock=clock,
        now=lambda: times["now"] + timedelta(seconds=clock.t),
        open_url=lambda url: opened.append(url.toLocalFile()) or True,
    )
    return rt, clock, opened


def fly(rt, clock, seconds):
    rt.setActive(True)
    for _ in range(seconds):
        clock.t += 1
        rt.tick()
    rt.setActive(False)


def test_each_flight_gets_its_own_folder_with_seconds_events_and_summary(tmp_path):
    good = {
        "fps": 30,
        "lost": False,
        "latencyMs": 60,
        "lossPct": 0,
        "preset": "720p30",
        "armed": True,
        "verdictLevel": "ok",
        "verdictText": "",
    }
    lost = {
        "fps": 0,
        "lost": True,
        "latencyMs": None,
        "lossPct": 100,
        "preset": "720p30",
        "armed": True,
        "verdictLevel": "lost",
        "verdictText": "Starlink: перешкода в небі",
    }
    samples = [dict(good, armed=False)] + [good] * 10 + [lost] * 3 + [dict(good, fps=24, preset="540p30")] * 20
    rt, clock, opened = make(tmp_path, samples)
    finished = []
    rt.finished.connect(lambda: finished.append(1))
    fly(rt, clock, 34)
    folders = list((tmp_path / "box").iterdir())
    names = [f.name for f in folders]
    assert names == ["2026-11-28_10-00-00 Квадрик 7"], "date, time and camera; no quotes in the name"
    folder = folders[0]
    assert len((folder / "seconds.jsonl").read_text(encoding="utf-8").splitlines()) == 35
    events = [json.loads(x)["text"] for x in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events == [
        "Дрон заармлено",
        "Відео зникло",
        "Причина: Starlink: перешкода в небі",
        "Відео повернулося",
        "Пресет відео: 540p30",
    ], events
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    assert (summary["outages"], summary["longestOutageS"], summary["durationS"]) == (1, 3, 34)
    assert summary["fpsMin"] == 24 and summary["causes"] == ["Starlink: перешкода в небі"]
    assert finished == [1], "a summary is shown after a real flight"
    text = (folder / "Підсумок.txt").read_text(encoding="utf-8")
    assert "Обривів відео: 1, найдовший 3 с" in text and "Тривалість: 34 с" in text
    assert rt.lastSummaryLines[0] == "Тривалість: 34 с"
    rt.openLastFlight()
    assert opened == [str(folder)]


def test_a_short_visit_writes_a_log_but_no_popup(tmp_path):
    rt, clock, _ = make(tmp_path, [{"fps": 30, "lost": False}])
    finished = []
    rt.finished.connect(lambda: finished.append(1))
    fly(rt, clock, 5)
    assert finished == [] and len(list((tmp_path / "box").iterdir())) == 1


def test_own_folder_setting_and_oldest_flights_removed(tmp_path):
    rt, clock, _ = make(tmp_path, [{"fps": 30}])
    assert rt.folderIsDefault and rt.folder == str(tmp_path / "box")
    assert rt.setFolder(str(tmp_path / "mine"))
    assert not rt.folderIsDefault
    root = tmp_path / "mine"
    for i in range(5):
        (root / f"2026-01-0{i + 1}_00-00-00").mkdir(parents=True)
        (root / f"2026-01-0{i + 1}_00-00-00" / fl.HEADER).write_text("{}")
    (root / "my notes").mkdir()
    fl.prune(root, keep=2)
    assert sorted(p.name for p in root.iterdir()) == ["2026-01-04_00-00-00", "2026-01-05_00-00-00", "my notes"]
    rt.resetFolder()
    assert rt.folderIsDefault


def test_unwritable_folder_is_told_not_crashed(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    rt, clock, _ = make(tmp_path, [{"fps": 30}])
    rt._folder = str(blocker / "box")
    rt.setActive(True)
    assert not rt.active and "не може писати" in rt.error


def test_durations_in_plain_words():
    assert fl.format_duration(42) == "42 с"
    assert fl.format_duration(125) == "2 хв 05 с"
    assert fl.format_duration(3725) == "1 год 02 хв"
    assert fl.safe_name('a/b:c*"d"') == "a b c d"


def test_the_journal_lists_flights_newest_first_grouped_by_day(tmp_path):
    rt, clock, opened = make(tmp_path, [{"fps": 30, "lost": False, "verdictText": ""}])
    root = tmp_path / "box"
    for name, summary in (
        ("2026-11-26_09-15-00 Крило", {"durationS": 600, "outages": 2, "camera": "Крило"}),
        ("2026-11-27_18-40-10 Квадрик", {"durationS": 125, "outages": 0, "camera": "Квадрик"}),
        ("2026-11-28_08-05-00 Квадрик", None),
    ):
        (root / name).mkdir(parents=True)
        (root / name / fl.HEADER).write_text(json.dumps({"camera": name.split(" ")[1], "link": "Starlink IPv6"}))
        if summary:
            (root / name / "summary.json").write_text(json.dumps(summary))
    (root / "2026-11-27_18-40-10 Квадрик" / "events.jsonl").write_text(
        json.dumps({"time": "18:41:02", "text": "Відео зникло"}) + "\nbroken\n", encoding="utf-8"
    )
    (root / "not a flight").mkdir()
    rt.refresh()
    flights = rt.flights
    assert [f["day"] for f in flights] == ["Сьогодні", "Вчора", "26 листопада 2026"]
    assert [(f["time"], f["duration"], f["outages"]) for f in flights] == [
        ("08:05", "", 0),
        ("18:40", "2 хв 05 с", 0),
        ("09:15", "10 хв 00 с", 2),
    ]
    assert not flights[0]["finished"]
    details = rt.flightDetails(flights[1]["path"])
    assert details["events"] == [{"time": "18:41:02", "text": "Відео зникло"}]
    assert details["lines"][0] == "Тривалість: 2 хв 05 с"
    assert "не завершився" in rt.flightDetails(flights[0]["path"])["lines"][0]
    assert rt.flightDetails(str(tmp_path)) == {}, "only folders of this black box"
    assert not rt.deleteFlight(str(root / "not a flight"))
    assert rt.deleteFlight(flights[2]["path"])
    assert len(rt.flights) == 2 and (root / "not a flight").exists()
    rt.openFlight(rt.flights[0]["path"])
    assert opened == [rt.flights[0]["path"]]
