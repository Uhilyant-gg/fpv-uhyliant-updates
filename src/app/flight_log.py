"""The flight black box: every flight gets its own folder with everything that happened.

From the moment the flight screen opens until it closes, once a second the station
writes what it sees (video frames, losses, delay, the link doctor's verdict, the
Starlink dish, the flight controller, the video preset) to ``seconds.jsonl``.
Changes worth reading (link lost and back with the cause, preset changed, armed,
recording started, ...) go to ``events.jsonl``. When the flight ends, a short
summary is written to ``summary.json`` and, in plain words, ``Підсумок.txt``, and is
shown to the pilot.

The black box folder is its own setting, like the DVR folder. The oldest flights are
removed when there are more than ``KEEP_FLIGHTS``.
"""

from __future__ import annotations

import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Property, QObject, QSettings, QStandardPaths, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

FOLDER_KEY = "blackbox/folder"
KEEP_FLIGHTS = 200
SHORT_FLIGHT_S = 20  # shorter visits to the flight screen get no summary popup
HEADER = "flight.json"
_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")

# Fields whose change is an event, and how it is told.
WATCHED = {
    "lost": lambda old, new: "Відео зникло" if new else "Відео повернулося",
    "verdictText": lambda old, new: f"Причина: {new}" if new else "",
    "preset": lambda old, new: f"Пресет відео: {new}" if new else "",
    "armed": lambda old, new: "Дрон заармлено" if new else "Дрон роззброєно",
    "flightMode": lambda old, new: f"Режим польоту: {new}" if new else "",
    "recording": lambda old, new: "Почато запис відео" if new else "Запис відео зупинено",
    "starlinkObstructed": lambda old, new: "Starlink: перешкода в небі" if new else "Starlink: небо відкрите",
}


def system_default_folder() -> str:
    documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    base = Path(documents) if documents else Path.home()
    return str(base / "FPV Uhyliant" / "Чорна скринька")


def safe_name(text: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', " ", str(text or "")).strip(" .")
    return re.sub(r"\s+", " ", cleaned)[:40]


def format_duration(seconds: float) -> str:
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds} с"
    minutes, rest = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} хв {rest:02d} с"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} год {minutes:02d} хв"


def summarize(samples: list[dict], events: list[dict], started: str, ended: str, duration: float) -> dict:
    """The flight in a few numbers."""
    outages, current = [], 0.0
    for sample in samples:
        if sample.get("lost"):
            current += 1
        elif current:
            outages.append(current)
            current = 0.0
    if current:
        outages.append(current)
    # Only seconds with a picture: the first moments before the video starts do not count.
    fps = [s["fps"] for s in samples if isinstance(s.get("fps"), (int, float)) and s["fps"] > 0 and not s.get("lost")]
    latency = [s["latencyMs"] for s in samples if isinstance(s.get("latencyMs"), (int, float))]
    loss = [s["lossPct"] for s in samples if isinstance(s.get("lossPct"), (int, float))]
    causes = []
    for sample in samples:
        text = sample.get("verdictText") or ""
        if (
            sample.get("verdictLevel") in ("warning", "lost")
            and text
            and text not in causes
            and text != "Визначаю причину…"
        ):
            causes.append(text)
    return {
        "started": started,
        "ended": ended,
        "durationS": round(duration),
        "outages": len(outages),
        "longestOutageS": max(outages) if outages else 0,
        "lostS": sum(outages),
        "fpsAvg": round(sum(fps) / len(fps), 1) if fps else None,
        "fpsMin": min(fps) if fps else None,
        "latencyMaxMs": max(latency) if latency else None,
        "lossMaxPct": max(loss) if loss else None,
        "causes": causes[:5],
        "events": len(events),
    }


def summary_lines(summary: dict) -> list[str]:
    """The summary in plain words, a line each."""
    lines = [f"Тривалість: {format_duration(summary.get('durationS', 0))}"]
    if summary.get("outages"):
        lines.append(
            f"Обривів відео: {summary['outages']}, найдовший {format_duration(summary['longestOutageS'])}, "
            f"усього без відео {format_duration(summary['lostS'])}"
        )
    else:
        lines.append("Обривів відео не було")
    if summary.get("fpsAvg") is not None:
        lines.append(
            f"Кадрів за секунду: у середньому {summary['fpsAvg']:g}, найменше {summary['fpsMin']:g}".replace(".", ",")
        )
    if summary.get("latencyMaxMs") is not None:
        lines.append(f"Найбільша затримка зв’язку: {summary['latencyMaxMs']:g} мс".replace(".", ","))
    if summary.get("lossMaxPct"):
        lines.append(f"Найбільші втрати пакетів: {summary['lossMaxPct']:g}%".replace(".", ","))
    if summary.get("causes"):
        lines.append("Що заважало: " + "; ".join(summary["causes"]))
    return lines


MONTHS = (
    "січня",
    "лютого",
    "березня",
    "квітня",
    "травня",
    "червня",
    "липня",
    "серпня",
    "вересня",
    "жовтня",
    "листопада",
    "грудня",
)


def day_label(day, today) -> str:
    """ "Сьогодні", "Вчора" or "28 листопада 2026"."""
    if day == today:
        return "Сьогодні"
    if (today - day).days == 1:
        return "Вчора"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def list_flights(root: Path, today) -> list[dict]:
    """The flights in the black box, newest first, each with its day for grouping."""
    try:
        folders = [p for p in Path(root).iterdir() if p.is_dir() and _NAME.match(p.name) and (p / HEADER).exists()]
    except OSError:
        return []
    flights = []
    for folder in sorted(folders, key=lambda p: p.name, reverse=True):
        header = _read_json(folder / HEADER)
        summary = _read_json(folder / "summary.json")
        try:
            started = datetime.strptime(folder.name[:19], "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            continue
        flights.append(
            {
                "path": str(folder),
                "day": day_label(started.date(), today),
                "time": started.strftime("%H:%M"),
                "camera": summary.get("camera") or header.get("camera", ""),
                "link": header.get("link", ""),
                "finished": bool(summary),
                "duration": format_duration(summary.get("durationS", 0)) if summary else "",
                "outages": int(summary.get("outages", 0) or 0),
            }
        )
    return flights


class FlightLog:
    """Writes one flight; the files stay valid line by line even if the PC loses power."""

    def __init__(self, folder: Path, header: dict, clock=time.monotonic):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self._clock = clock
        self._start = clock()
        self._last: dict = {}
        self.samples: list[dict] = []
        self.events: list[dict] = []
        self.header = dict(header)
        (self.folder / HEADER).write_text(json.dumps(self.header, ensure_ascii=False, indent=1), encoding="utf-8")
        self._seconds = open(self.folder / "seconds.jsonl", "a", encoding="utf-8")
        self._events = open(self.folder / "events.jsonl", "a", encoding="utf-8")

    def elapsed(self) -> float:
        return self._clock() - self._start

    def write(self, sample: dict):
        t = round(self.elapsed(), 1)
        line = {"t": t, **sample}
        self.samples.append(line)
        self._seconds.write(json.dumps(line, ensure_ascii=False) + "\n")
        self._seconds.flush()
        for key, tell in WATCHED.items():
            if key not in sample:
                continue
            old, new = self._last.get(key), sample[key]
            if key in self._last and old != new:
                text = tell(old, new)
                if text:
                    self.event(text, key)
            self._last[key] = new

    def event(self, text: str, kind: str = "note"):
        entry = {"t": round(self.elapsed(), 1), "time": datetime.now().strftime("%H:%M:%S"), "kind": kind, "text": text}
        self.events.append(entry)
        self._events.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._events.flush()

    def close(self, ended: str) -> dict:
        self._seconds.close()
        self._events.close()
        summary = summarize(self.samples, self.events, self.header.get("started", ""), ended, self.elapsed())
        summary["camera"] = self.header.get("camera", "")
        summary["folder"] = str(self.folder)
        (self.folder / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        text = [f"Політ {self.header.get('started', '')} · {self.header.get('camera', '')}", ""] + summary_lines(
            summary
        )
        if self.events:
            text += ["", "Події:"] + [f"{e['time']}  {e['text']}" for e in self.events]
        (self.folder / "Підсумок.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
        return summary


def prune(root: Path, keep: int = KEEP_FLIGHTS):
    """Remove the oldest flight folders (only folders this station wrote)."""
    try:
        flights = sorted(
            p for p in Path(root).iterdir() if p.is_dir() and _NAME.match(p.name) and (p / HEADER).exists()
        )
    except OSError:
        return
    for old in flights[: max(0, len(flights) - keep)]:
        shutil.rmtree(old, ignore_errors=True)


class BlackBoxRuntime(QObject):
    changed = Signal()
    finished = Signal()

    def __init__(
        self,
        sample,
        header,
        settings=None,
        default_folder=None,
        clock=time.monotonic,
        now=datetime.now,
        open_url=QDesktopServices.openUrl,
        interval_ms=1000,
    ):
        super().__init__()
        self._sample = sample  # () -> dict of what the station sees now
        self._header = header  # () -> dict about the camera and the link
        self._settings = settings or QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        self._default_folder = default_folder or system_default_folder()
        self._clock = clock
        self._now = now
        self._open_url = open_url
        self._folder = str(self._settings.value(FOLDER_KEY, "") or "").strip()
        self._log: FlightLog | None = None
        self._summary: dict = {}
        self._flights: list[dict] = []
        self._error = ""
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.tick)

    # --- what QML shows -------------------------------------------------------
    @Property(bool, notify=changed)
    def active(self):
        return self._log is not None

    @Property(str, notify=changed)
    def folder(self):
        return self._folder or self._default_folder

    @Property(bool, notify=changed)
    def folderIsDefault(self):
        return not self._folder

    @Property(QUrl, notify=changed)
    def folderUrl(self):
        return QUrl.fromLocalFile(self.folder)

    @Property("QVariantMap", notify=changed)
    def lastSummary(self):
        return dict(self._summary)

    @Property("QVariantList", notify=changed)
    def lastSummaryLines(self):
        return summary_lines(self._summary) if self._summary else []

    @Property(str, notify=changed)
    def error(self):
        return self._error

    # --- the folder -----------------------------------------------------------
    @Slot(str, result=bool)
    def setFolder(self, value):
        url = QUrl(str(value))
        path = url.toLocalFile() if url.isLocalFile() else str(value)
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except OSError:
            self._error = "Цю папку не вдалося відкрити для запису."
            self.changed.emit()
            return False
        self._folder, self._error = str(Path(path)), ""
        self._settings.setValue(FOLDER_KEY, self._folder)
        self._settings.sync()
        self.changed.emit()
        return True

    @Slot()
    def resetFolder(self):
        self._folder, self._error = "", ""
        self._settings.remove(FOLDER_KEY)
        self._settings.sync()
        self.changed.emit()

    @Slot(result=bool)
    def openFolder(self):
        Path(self.folder).mkdir(parents=True, exist_ok=True)
        return bool(self._open_url(QUrl.fromLocalFile(self.folder)))

    @Slot(result=bool)
    def openLastFlight(self):
        folder = self._summary.get("folder")
        return bool(folder and self._open_url(QUrl.fromLocalFile(folder)))

    # --- the flights journal --------------------------------------------------
    @Property("QVariantList", notify=changed)
    def flights(self):
        return list(self._flights)

    @Slot()
    def refresh(self):
        self._flights = list_flights(Path(self.folder), self._now().date())
        self.changed.emit()

    def _own(self, path) -> Path | None:
        """A flight folder of this black box, never anything else."""
        try:
            folder = Path(str(path)).resolve()
            root = Path(self.folder).resolve()
        except OSError:
            return None
        if folder.parent != root or not _NAME.match(folder.name) or not (folder / HEADER).exists():
            return None
        return folder

    @Slot(str, result="QVariantMap")
    def flightDetails(self, path):
        folder = self._own(path)
        if folder is None:
            return {}
        header = _read_json(folder / HEADER)
        summary = _read_json(folder / "summary.json")
        events = []
        try:
            for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines():
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if isinstance(entry, dict):
                    events.append({"time": str(entry.get("time", "")), "text": str(entry.get("text", ""))})
        except OSError:
            pass
        return {
            "camera": header.get("camera", ""),
            "link": header.get("link", ""),
            "started": header.get("started", ""),
            "lines": summary_lines(summary)
            if summary
            else ["Політ не завершився штатно (наприклад, станцію закрили)."],
            "events": events,
        }

    @Slot(str, result=bool)
    def openFlight(self, path):
        folder = self._own(path)
        return bool(folder and self._open_url(QUrl.fromLocalFile(str(folder))))

    @Slot(str, result=bool)
    def deleteFlight(self, path):
        folder = self._own(path)
        if folder is None or (self._log is not None and self._log.folder.resolve() == folder):
            return False
        shutil.rmtree(folder, ignore_errors=True)
        self.refresh()
        return not folder.exists()

    # --- a flight -------------------------------------------------------------
    @Slot(bool)
    def setActive(self, active):
        if active and self._log is None:
            self._begin()
        elif not active and self._log is not None:
            self._end()

    @Slot(str)
    def note(self, text):
        if self._log is not None and text:
            self._log.event(str(text))

    def _begin(self):
        header = dict(self._header() or {})
        started = self._now()
        header["started"] = started.strftime("%Y-%m-%d %H:%M:%S")
        name = started.strftime("%Y-%m-%d_%H-%M-%S")
        camera = safe_name(header.get("camera", ""))
        folder = Path(self.folder) / (f"{name} {camera}" if camera else name)
        try:
            prune(Path(self.folder), KEEP_FLIGHTS - 1)
            self._log = FlightLog(folder, header, clock=self._clock)
            self._error = ""
        except OSError:
            self._log = None
            self._error = "Чорна скринька не може писати в свою папку. Змініть папку в налаштуваннях запису."
        self.changed.emit()
        if self._log is not None:
            self._timer.start()
            self.tick()

    def _end(self):
        self._timer.stop()
        log, self._log = self._log, None
        try:
            summary = log.close(self._now().strftime("%Y-%m-%d %H:%M:%S"))
        except OSError:
            summary = {}
        self._summary = summary
        self._flights = list_flights(Path(self.folder), self._now().date())
        self.changed.emit()
        if summary and summary.get("durationS", 0) >= SHORT_FLIGHT_S:
            self.finished.emit()

    @Slot()
    def tick(self):
        if self._log is None:
            return
        try:
            sample = dict(self._sample() or {})
        except Exception:
            sample = {}
        try:
            self._log.write(sample)
        except OSError:
            self._timer.stop()
            self._error = "Чорна скринька не може писати: перевірте вільне місце."
            self.changed.emit()
