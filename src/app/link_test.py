"""A 20-second link test before take-off (Preflight).

For 20 seconds the station checks the selected link once a second: does the camera
answer and how fast, and — when the flight screen already shows the video — how many
frames arrive, how many packets are lost and how unevenly they come. Then it says in
plain words whether the link is fit to fly and what to change if it is not.

The test starts by itself when Preflight opens; the pilot can repeat it.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

DURATION_S = 20
TARGET_MS = 150  # camera to screen, agreed with the owner
DECODE_MS = 60  # encoder, decoder and screen, as in the "Авто" preset


def _avg(values):
    return sum(values) / len(values) if values else None


def _num(text):
    return f"{text:g}".replace(".", ",")


def judge(samples: list[dict]) -> dict:
    """{level: ok|warning|bad, title, lines} from one sample a second."""
    if not samples:
        return {"level": "bad", "title": "Тест не відбувся", "lines": ["Немає даних про зв’язок."]}
    reachable = [s for s in samples if s.get("reachable")]
    if not reachable:
        return {
            "level": "bad",
            "title": "Не летіти: камера не відповідає",
            "lines": [
                "Жодна перевірка за 20 с не дісталася камери через вибране з’єднання.",
                "Перевірте живлення камери і з’єднання (Starlink, ZeroTier або локальна мережа).",
            ],
        }
    lines, level = [], "ok"
    silent = len(samples) - len(reachable)
    if silent:
        lines.append(f"Камера не відповіла {silent} раз(и) з {len(samples)}: зв’язок переривається.")
        level = "warning" if silent <= len(samples) // 5 else "bad"

    latency = [s["latencyMs"] for s in reachable if isinstance(s.get("latencyMs"), (int, float))]
    if latency:
        avg, worst = _avg(latency), max(latency)
        spread = worst - min(latency)
        lines.append(f"Затримка зв’язку: у середньому {_num(round(avg))} мс, найбільша {_num(worst)} мс.")
        smoothing = _avg([s.get("smoothingMs", 0) or 0 for s in samples]) or 0
        screen = round(avg / 2 + DECODE_MS + smoothing)
        if screen > TARGET_MS:
            lines.append(
                f"Від камери до екрана вийде приблизно {screen} мс — більше за ціль {TARGET_MS} мс. "
                "Радимо пресет «Авто» (клавіша 1) або слабший пресет."
            )
            level = "warning" if level == "ok" else level
        if spread > 80:
            lines.append(f"Затримка скаче на {_num(spread)} мс: можливі посмикування відео.")
            level = "warning" if level == "ok" else level
    elif any(s.get("pushed") for s in samples):
        lines.append("Затримку зв’язку не виміряти: камера сама надсилає відео на статичний IP.")
    else:
        lines.append("Затримку зв’язку виміряти не вдалося.")

    video = [s for s in samples if s.get("video")]
    if video:
        lost = sum(1 for s in video if s.get("lost"))
        fps = [s["fps"] for s in video if not s.get("lost") and (s.get("fps") or 0) > 0]
        loss = [s["lossPct"] for s in video if isinstance(s.get("lossPct"), (int, float))]
        if lost:
            lines.append(f"Відео зникало на {lost} с за тест.")
            level = "bad" if lost >= 3 else ("warning" if level == "ok" else level)
        if fps:
            lines.append(f"Кадрів за секунду: у середньому {_num(round(_avg(fps), 1))}, найменше {_num(min(fps))}.")
        if loss and max(loss) >= 1:
            lines.append(
                f"Втрачається до {_num(round(max(loss), 1))}% пакетів відео: радимо «Авто» або слабший пресет."
            )
            level = "warning" if level == "ok" else level
    else:
        lines.append("Відео не перевірялося: відкрийте екран польоту, і тест перевірить і картинку.")

    title = {
        "ok": "Можна летіти: зв’язок стабільний",
        "warning": "Можна летіти, але зверніть увагу",
        "bad": "Краще не летіти, поки зв’язок не стане кращим",
    }[level]
    return {"level": level, "title": title, "lines": lines}


class LinkTestRuntime(QObject):
    changed = Signal()

    def __init__(self, sample, probe=lambda: None, duration_s=DURATION_S, interval_ms=1000):
        super().__init__()
        self._sample = sample  # () -> dict: reachable, latencyMs, video, fps, lost, lossPct, smoothingMs
        self._probe = probe  # () -> None: ask the link once more
        self._duration = duration_s
        self._samples: list[dict] = []
        self._running = False
        self._result: dict = {}
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.tick)

    @Property(bool, notify=changed)
    def running(self):
        return self._running

    @Property(float, notify=changed)
    def progress(self):
        return min(1.0, len(self._samples) / self._duration)

    @Property(int, notify=changed)
    def secondsLeft(self):
        return max(0, self._duration - len(self._samples))

    @Property("QVariantMap", notify=changed)
    def result(self):
        return dict(self._result)

    @Slot()
    def start(self):
        self._samples, self._result, self._running = [], {}, True
        self._probe()
        self._timer.start()
        self.changed.emit()

    @Slot()
    def stop(self):
        self._timer.stop()
        self._running = False
        self.changed.emit()

    @Slot()
    def tick(self):
        if not self._running:
            return
        try:
            self._samples.append(dict(self._sample() or {}))
        except Exception:
            self._samples.append({})
        if len(self._samples) >= self._duration:
            self._timer.stop()
            self._running = False
            self._result = judge(self._samples)
        else:
            self._probe()
        self.changed.emit()
