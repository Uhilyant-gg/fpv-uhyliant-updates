"""Video presets of each camera. Key 1 is "Auto"; nine slots on the keys 2…0 go from the
weakest link (2) up.

A preset is written into the camera itself (majestic's settings) and the video
service reloads; the station re-opens the video by itself. In flight this goes
through a connection the station can log in to the camera on (local or ZeroTier);
over a static IP or Starlink's public address the camera sends video only.
Only fixed, validated values ever go into the commands.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

import camera_setup as cs

AUTO_KEY = "1"
KEYS = ("2", "3", "4", "5", "6", "7", "8", "9", "0")
SIZES = ("640x360", "960x540", "1280x720", "1920x1080")
FPS = (30, 60, 90)
GOPS = (0.5, 1, 2)
MIN_KBPS, MAX_KBPS = 256, 20000
BITRATE_STEPS = (512, 768, 1024, 1536, 2048, 2560, 3072, 4096, 6144)

# The automatic ladder: nine bitrates for the keys 2…0. For each, the largest picture
# that still gets enough data per pixel to stay clean (no blocks), never below 30 fps,
# 60 fps as soon as the bitrate carries it: smoothness and detail together.
# Starlink on the drone carries at most ~6 Mbit/s and works reliably up to ~2.5 Mbit/s
# (owner's measurements), so the ladder is dense below 2.5 and stops at 6.
LADDER_KBPS = (512, 768, 1024, 1536, 2048, 2560, 3072, 4096, 6144)
LADDER_NAMES = (
    "Мінімум",
    "Дуже слабкий канал",
    "Слабкий канал",
    "Нижче середнього",
    "Середній",
    "Добрий канал",
    "Високий",
    "Дуже високий",
    "Максимум",
)
# H.265 bits per pixel per frame below which fast FPV motion turns into blocks.
MIN_BITS_PER_PIXEL = 0.05
# From the least to the most wanted picture for FPV: smoothness before size.
PICTURES = (("640x360", 30), ("960x540", 30), ("1280x720", 30), ("1280x720", 60), ("1920x1080", 60))


def picture_for(kbps: int) -> tuple[str, int]:
    best = PICTURES[0]
    for size, fps in PICTURES:
        w, h = (int(x) for x in size.split("x"))
        if kbps * 1000 >= w * h * fps * MIN_BITS_PER_PIXEL:
            best = (size, fps)
    return best


def build_ladder() -> dict:
    """The camera's presets built by the station: no manual filling needed."""
    ladder = {}
    for key, kbps, name in zip(KEYS, LADDER_KBPS, LADDER_NAMES):
        size, fps = picture_for(kbps)
        # Short full-frame interval on weak links: a dropout heals faster there.
        ladder[key] = {
            "name": name,
            "size": size,
            "fps": fps,
            "bitrateKbps": kbps,
            "gopS": 0.5 if kbps <= 2048 else 1,
            "auto": True,
        }
    return ladder


DEFAULTS = build_ladder()

MESSAGES = {
    "applied": "Пресет {key} «{name}» застосовано в камері",
    "bitrate": "Бітрейт {mbps} Мбіт/с застосовано в камері",
    "busy": "Камера ще застосовує попередню зміну",
    "no-camera": "Камеру не вибрано",
    "unreachable": "Камера недоступна для керування: потрібне підключення через локальну мережу або ZeroTier",
    "empty": "Цей слот порожній. Задайте пресет у налаштуваннях пресетів відео.",
    "invalid": "Перевірте значення пресета",
}


def validate(preset) -> dict:
    """A clean preset, or ValueError. Names are free text; numbers only from the allowed sets."""
    if not isinstance(preset, dict):
        raise ValueError("preset")
    name = str(preset.get("name", "")).strip()[:30]
    size = preset.get("size")
    fps = int(preset.get("fps", 0))
    kbps = int(preset.get("bitrateKbps", 0))
    gop = float(preset.get("gopS", 0))
    if not name or size not in SIZES or fps not in FPS or not MIN_KBPS <= kbps <= MAX_KBPS or gop not in GOPS:
        raise ValueError("preset")
    clean = {"name": name, "size": size, "fps": fps, "bitrateKbps": kbps, "gopS": int(gop) if gop == int(gop) else gop}
    if preset.get("auto"):
        clean["auto"] = True
    return clean


def commands(preset: dict, channel: int = 0) -> list[str]:
    """majestic settings of one stream (video0 main, video1 second) for a validated preset,
    then a reload of the video service."""
    v = f".video{int(channel)}"
    return [
        f"cli -s {v}.rcMode cbr",  # an even stream: no bursts that choke the link
        f"cli -s {v}.size {preset['size']}",
        f"cli -s {v}.fps {int(preset['fps'])}",
        f"cli -s {v}.bitrate {int(preset['bitrateKbps'])}",
        f"cli -s {v}.gopSize {preset['gopS']}",
        "killall -1 majestic",
    ]


def bitrate_commands(kbps: int, channel: int = 0) -> list[str]:
    if not MIN_KBPS <= int(kbps) <= MAX_KBPS:
        raise ValueError("bitrate")
    return [f"cli -s .video{int(channel)}.bitrate {int(kbps)}", "killall -1 majestic"]


# A reload's exit code, or a setting an older majestic does not know, is not a failure.
OPTIONAL_COMMANDS = ("killall", "cli -s .video0.rcMode", "cli -s .video1.rcMode")


def run_on_camera(host, credentials, shell, lines) -> dict:
    """Send the commands; never raises. The reload's own exit code is not an error."""

    def action(session):
        for line in lines:
            code, _ = session.run(line)
            if code != 0 and not line.startswith(OPTIONAL_COMMANDS):
                return {"state": "failed", "message": cs.MESSAGES["failed"]}
        return {"state": "applied"}

    return cs.with_camera(host, credentials, shell, action)


class VideoPresetStore:
    def __init__(self, path: Path):
        self._path = Path(path)

    def load(self) -> dict:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, data: dict):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self._path)


class VideoPresetsRuntime(QObject):
    changed = Signal()
    _done = Signal(str, object, object)  # device id, what was applied, result

    def __init__(self, store, devices, connections, apply, run_async=True, clock=None):
        super().__init__()
        import time

        self._clock = clock or time.monotonic
        self._auto = AutoDecider()
        self._store = store
        self._devices = devices
        self._connections = connections
        self._apply = apply  # (host, command lines) -> result dict
        self._run_async = run_async
        self._data = store.load()
        self._busy = False
        self._message = ""
        self._ok = True
        # Which of the camera's streams the presets window shows: 0 main, 1 second.
        self._channel = 0
        self._stream_name = ""
        self._done.connect(self._finish)
        if hasattr(devices, "changed"):
            devices.changed.connect(self.changed)

    # --- state -----------------------------------------------------------------
    def _camera_id(self):
        return getattr(self._devices, "activeId", "") or ""

    def _device_id(self):
        """Where this stream's presets are kept: the camera, plus the stream after the first."""
        camera = self._camera_id()
        return camera if not camera or self._channel == 0 else f"{camera}#video{self._channel}"

    def _main(self, action):
        """Keys, Auto and the flight bar always act on the main stream."""
        saved = self._channel
        self._channel = 0
        try:
            return action()
        finally:
            self._channel = saved

    @Slot(int, str)
    def editStream(self, channel, name):
        """The presets window for one stream: 0 the main one, 1 the camera's second stream."""
        self._channel = 1 if int(channel) == 1 else 0
        self._stream_name = str(name or "")
        self._message = ""
        self.changed.emit()

    @Property(int, notify=changed)
    def channel(self):
        return self._channel

    @Property(str, notify=changed)
    def streamName(self):
        return self._stream_name if self._channel else "Основний потік"

    def _camera(self, device_id=None):
        device_id = device_id or self._device_id()
        camera = self._data.get(device_id)
        if not isinstance(camera, dict):
            camera = {"slots": {k: dict(v) for k, v in DEFAULTS.items()}, "active": "", "bitrateKbps": 0}
        return camera

    def _slot(self, key):
        preset = self._camera()["slots"].get(key)
        try:
            return validate(preset) if preset else None
        except (ValueError, TypeError):
            return None

    @Property("QVariantList", notify=changed)
    def slots(self):
        rows = []
        for key in KEYS:
            preset = self._slot(key)
            rows.append({"key": key, "empty": preset is None, **(preset or {})})
        return rows

    @Property(str, notify=changed)
    def activeKey(self):
        return self._camera().get("active", "") if self._device_id() else ""

    @Property(int, notify=changed)
    def bitrateKbps(self):
        return int(self._camera().get("bitrateKbps") or 0) if self._device_id() else 0

    @Property(str, notify=changed)
    def label(self):
        """For the flight bar (the main stream): "3 · Баланс · 4 Мбіт/с", * after a change by hand."""
        return self._main(self._label_now)

    @Property(str, notify=changed)
    def streamLabel(self):
        """The same for the stream shown in the presets window."""
        return self._label_now()

    def _label_now(self):
        key = self.activeKey
        preset = self._slot(key) if key else None
        if preset is None:
            return "Авто · як у камері" if self.auto else "Як у камері"
        kbps = self.bitrateKbps or preset["bitrateKbps"]
        mark = "*" if kbps != preset["bitrateKbps"] else ""
        head = f"Авто · {key}" if self.auto else key
        return f"{head} · {preset['name']}{mark} · {mbps(kbps)} Мбіт/с"

    @Property(bool, notify=changed)
    def auto(self):
        return bool(self._camera().get("auto")) if self._device_id() else False

    @Slot(bool)
    def setAuto(self, on):
        """The "Auto" preset: the station moves between this camera's own presets by itself."""
        device_id = self._device_id()
        if not device_id:
            return
        camera = self._camera()
        camera["auto"] = bool(on)
        self._data[device_id] = camera
        self._store.save(self._data)
        self._auto = AutoDecider()
        self._say("Авто: станція сама перемикає пресети цієї камери за станом каналу" if on else "Авто вимкнено", True)

    @Slot("QVariantMap")
    def observe(self, sample):
        """Once a second in flight: how the link behaves. In Auto, may step one preset (main stream)."""
        self._main(lambda: self._observe(sample))

    def _observe(self, sample):
        if not self.auto or self._busy:
            return
        step = self._auto.update(dict(sample), self._clock())
        if not step:
            return
        filled = [k for k in KEYS if self._slot(k) is not None]
        if not filled:
            return
        current = self.activeKey if self.activeKey in filled else filled[-1]
        index = max(0, min(len(filled) - 1, filled.index(current) + step))
        if filled[index] != current or self.activeKey not in filled:
            self.apply(filled[index])

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Property(bool, notify=changed)
    def messageOk(self):
        return self._ok

    # --- actions ---------------------------------------------------------------
    def _say(self, text, ok):
        self._message, self._ok = text, ok
        self.changed.emit()

    def _start(self, what, lines):
        device_id = self._device_id()
        if not device_id:
            self._say(MESSAGES["no-camera"], False)
            return False
        if self._busy:
            self._say(MESSAGES["busy"], False)
            return False
        host = self._connections.control_host(self._camera_id())
        if not host:
            self._say(MESSAGES["unreachable"], False)
            return False
        self._busy = True
        self._say("Застосовую в камері…", True)

        def work():
            try:
                result = self._apply(host, lines)
            except Exception:
                result = {"state": "failed", "message": cs.MESSAGES["failed"]}
            self._done.emit(device_id, what, result)

        if self._run_async:
            threading.Thread(target=work, name="video-preset", daemon=True).start()
        else:
            work()
        return True

    @Slot(str, result=bool)
    def choose(self, key):
        """A key or a click by the pilot. 1 turns Auto on; any preset key turns it off."""
        if key == AUTO_KEY:
            self.setAuto(True)
            filled = [k for k in KEYS if self._slot(k) is not None]
            if filled and self.activeKey not in filled:
                return self.apply(filled[len(filled) // 2])  # start from the middle
            return True
        if self.auto:
            self.setAuto(False)
        return self.apply(key)

    @Slot(str, result=bool)
    def chooseMain(self, key):
        return self._main(lambda: self.choose(key))

    @Slot(int, result=bool)
    def stepBitrateMain(self, direction):
        return self._main(lambda: self.stepBitrate(direction))

    @Slot(str, result=bool)
    def apply(self, key):
        preset = self._slot(key)
        if preset is None:
            self._say(MESSAGES["empty"], False)
            return False
        return self._start({"key": key, "bitrateKbps": preset["bitrateKbps"]}, commands(preset, self._channel))

    @Slot(int, result=bool)
    def setBitrate(self, kbps):
        try:
            lines = bitrate_commands(kbps, self._channel)
        except (ValueError, TypeError):
            self._say(MESSAGES["invalid"], False)
            return False
        return self._start({"bitrateKbps": int(kbps)}, lines)

    @Slot(int, result=bool)
    def stepBitrate(self, direction):
        """The quick − / + on the flight bar: the next step from the current bitrate."""
        current = self.bitrateKbps or (self._slot(self.activeKey) or {}).get("bitrateKbps") or 4096
        if direction > 0:
            target = next((s for s in BITRATE_STEPS if s > current), BITRATE_STEPS[-1])
        else:
            target = next((s for s in reversed(BITRATE_STEPS) if s < current), BITRATE_STEPS[0])
        return self.setBitrate(target)

    def _finish(self, device_id, what, result):
        self._busy = False
        if result.get("state") != "applied":
            self._say(result.get("message") or cs.MESSAGES["failed"], False)
            return
        camera = self._camera(device_id)
        if "key" in what:
            camera["active"] = what["key"]
        camera["bitrateKbps"] = what["bitrateKbps"]
        self._data[device_id] = camera
        self._store.save(self._data)
        if "key" in what:
            preset = self._slot(what["key"]) or {"name": ""}
            self._say(MESSAGES["applied"].format(key=what["key"], name=preset["name"]), True)
        else:
            self._say(MESSAGES["bitrate"].format(mbps=mbps(what["bitrateKbps"])), True)

    @Slot(str, "QVariantMap", result=bool)
    def saveSlot(self, key, preset):
        device_id = self._device_id()
        if key not in KEYS or not device_id:
            return False
        try:
            clean = validate(dict(preset))
        except (ValueError, TypeError):
            self._say(MESSAGES["invalid"], False)
            return False
        clean.pop("auto", None)  # edited by the pilot: the station leaves it as it is
        camera = self._camera()
        camera["slots"][key] = clean
        self._data[device_id] = camera
        self._store.save(self._data)
        self._say(f"Слот {key} збережено", True)
        return True

    @Slot(result=bool)
    def rebuildLadder(self):
        """Back to the station's own presets for this camera (edited ones are replaced too)."""
        device_id = self._device_id()
        if not device_id:
            return False
        camera = self._camera()
        camera["slots"] = build_ladder()
        if camera.get("active") not in camera["slots"]:
            camera["active"] = ""
        self._data[device_id] = camera
        self._store.save(self._data)
        self._say("Пресети побудовано заново", True)
        return True

    @Slot(str, result=bool)
    def clearSlot(self, key):
        device_id = self._device_id()
        if key not in KEYS or not device_id:
            return False
        camera = self._camera()
        camera["slots"].pop(key, None)
        if camera.get("active") == key:
            camera["active"] = ""
        self._data[device_id] = camera
        self._store.save(self._data)
        self._say(f"Слот {key} очищено", True)
        return True

    @Property("QVariantList", constant=True)
    def sizes(self):
        return list(SIZES)

    @Property("QVariantList", constant=True)
    def fpsChoices(self):
        return list(FPS)

    @Property("QVariantList", constant=True)
    def gopChoices(self):
        return list(GOPS)


def mbps(kbps) -> str:
    value = round(int(kbps) / 1024, 1)
    return (f"{value:g}").replace(".", ",")


class AutoDecider:
    """Chooses one preset step down or up from how the link behaves, with patience.

    Down: the link has been bad for 3 s in a row (loss, uneven arrival or latency over
    the target) and the last change was at least 10 s ago. Up: good for 30 s. Never while
    the video is lost (the camera may not be reachable then, and the cause is elsewhere).
    """

    BAD_FOR_S = 3
    GOOD_FOR_S = 30
    DOWN_GAP_S = 10
    UP_GAP_S = 30

    # Camera encoding plus decoding and showing on the PC, on top of the one-way network delay.
    PIPELINE_MS = 60

    def __init__(self, target_ms=150):
        self.target_ms = target_ms
        self._bad = 0
        self._good = 0
        self._changed_at = None

    def glass_to_glass(self, s):
        """Estimated delay from the camera to the pilot's screen, from the round trip."""
        rtt = s.get("latencyMs")
        return None if rtt is None else rtt / 2 + self.PIPELINE_MS + float(s.get("smoothingMs") or 0)

    def bad(self, s):
        delay = self.glass_to_glass(s)
        return (
            float(s.get("lossPct") or 0) >= 2
            or float(s.get("jitterMs") or 0) >= 30
            or (delay is not None and delay > self.target_ms)
        )

    def good(self, s):
        delay = self.glass_to_glass(s)
        return (
            float(s.get("lossPct") or 0) < 0.5
            and float(s.get("jitterMs") or 0) < 15
            and (delay is None or delay < self.target_ms * 0.8)
        )

    def update(self, sample: dict, now: float) -> int:
        if sample.get("lost"):
            self._bad = self._good = 0
            return 0
        self._bad = self._bad + 1 if self.bad(sample) else 0
        self._good = self._good + 1 if self.good(sample) else 0
        since = now - self._changed_at if self._changed_at is not None else 1e9
        if self._bad >= self.BAD_FOR_S and since >= self.DOWN_GAP_S:
            self._changed_at, self._bad, self._good = now, 0, 0
            return -1
        if self._good >= self.GOOD_FOR_S and since >= self.UP_GAP_S:
            self._changed_at, self._bad, self._good = now, 0, 0
            return 1
        return 0
