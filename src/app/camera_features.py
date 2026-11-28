"""What the camera can send besides its main picture, found by the station itself.

Every few seconds (also in flight) the station asks the camera, over its own SSH
session, a fixed set of read-only questions:

* is the camera's second stream (video1) on;
* is a USB video device (a capture card or a UVC camera, e.g. a thermal one)
  plugged into the camera, and can this firmware encode it (majestic "usbcam");
* does the firmware have sound, is the microphone on, at what sample rate.

Streams that exist appear on the flight screen's side panel by themselves and
disappear when they are gone. A USB device that the firmware can encode is
switched on by the station (the camera's own encoder compresses it, so the
station controls its bitrate); this restarts the camera's video for a moment,
so it is done only while the drone is not armed.

Only fixed commands, or commands built from checked numbers, are sent.
"""

from __future__ import annotations

import re
import threading
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

POLL_MS = 15000

READ_COMMANDS = {
    "release": "cat /etc/os-release",
    "video1": "cli -g .video1.enabled",
    "usbEnabled": "cli -g .usbcam.enabled",
    "usbCodec": "cli -g .usbcam.codec",
    # Names of the USB video devices plugged into the camera (the sensor is not one of them).
    "usbDevices": "cat /sys/class/video4linux/*/name",
    "audioEnabled": "cli -g .audio.enabled",
    "audioRate": "cli -g .audio.srate",
    "audioVolume": "cli -g .audio.volume",
}

# RTSP paths of majestic: the second stream, and the USB camera encoded by the camera.
SECOND_PATH = "/stream=1"
USB_PATH = "/stream=3"
RTSP_PORT = 554
AUTO_PATHS = (SECOND_PATH, USB_PATH)

AUDIO_RATES = (8000, 16000, 48000)
# The reload's exit code is not an error (majestic re-reads its settings).
RELOAD = "killall -1 majestic"

_THERMAL = re.compile(r"thermal|infiray|topdon|p2 ?pro|seek|flir|hikmicro|guide|ircam|tc00\d|t2l|mini2", re.I)


def _flag(code_text):
    code, text = code_text
    if code != 0:
        return None
    text = text.strip().lower()
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off"):
        return False
    return None


def _number(code_text):
    code, text = code_text
    try:
        return int(float(text.strip())) if code == 0 else None
    except ValueError:
        return None


def parse_features(answers: dict) -> dict:
    """``answers`` maps a READ_COMMANDS key to (exit code, output)."""

    def get(key):
        value = answers.get(key)
        return value if isinstance(value, tuple) and len(value) == 2 else (1, "")

    release = dict(re.findall(r'^([A-Z_]+)="?([^"\n]*)"?$', get("release")[1], re.M)) if get("release")[0] == 0 else {}
    variant = release.get("BUILD_OPTION", "").strip().lower()

    code, names = get("usbDevices")
    devices = [line.strip() for line in names.splitlines() if line.strip()] if code == 0 else []
    usb_enabled = _flag(get("usbEnabled"))
    usb_codec = get("usbCodec")[1].strip().lower() if get("usbCodec")[0] == 0 else ""
    usb_supported = usb_enabled is not None
    usb_name = devices[0] if devices else ""

    audio_enabled = _flag(get("audioEnabled"))
    rate = _number(get("audioRate"))
    volume_code, volume_text = get("audioVolume")
    volume = _number(get("audioVolume"))
    # The FPV build of majestic has no sound at all; other builds answer the audio keys.
    audio_supported = variant != "fpv" and audio_enabled is not None
    return {
        "variant": variant,
        "second": _flag(get("video1")) is True,
        "usb": {
            "supported": usb_supported,
            "device": usb_name,
            "thermal": bool(_THERMAL.search(usb_name)),
            "enabled": usb_enabled is True,
            "codec": usb_codec,
        },
        "audio": {
            "supported": audio_supported,
            "enabled": audio_supported and audio_enabled is True,
            "rate": rate if rate in AUDIO_RATES else (rate or 8000),
            "volume": volume if volume is not None else ("auto" if volume_code == 0 and volume_text.strip() else None),
        },
    }


def streams_for(features: dict) -> list[dict]:
    """The camera's additional streams that exist right now."""
    streams = []
    if features.get("second"):
        streams.append({"name": "Другий потік", "kind": "sub", "path": SECOND_PATH, "port": RTSP_PORT})
    usb = features.get("usb") or {}
    if usb.get("supported") and usb.get("enabled") and usb.get("device"):
        name = "Тепловізор" if usb.get("thermal") else "USB-камера"
        streams.append(
            {"name": name, "kind": "thermal" if usb.get("thermal") else "usb", "path": USB_PATH, "port": RTSP_PORT}
        )
    return streams


def usb_needs_enabling(features: dict) -> bool:
    usb = features.get("usb") or {}
    return bool(usb.get("supported") and usb.get("device") and not usb.get("enabled"))


def usb_enable_commands() -> list[str]:
    # "transcode": the camera's own encoder compresses the USB picture, so the station sets its bitrate.
    return ["cli -s .usbcam.enabled true", "cli -s .usbcam.codec transcode", RELOAD]


def audio_commands(enabled=None, volume=None, rate=None) -> list[str]:
    """Commands for the camera's microphone, from checked values only."""
    lines = []
    if enabled is not None:
        lines.append(f"cli -s .audio.enabled {'true' if enabled else 'false'}")
    if volume is not None:
        lines.append(f"cli -s .audio.volume {max(1, min(100, int(volume)))}")
    if rate is not None:
        if int(rate) not in AUDIO_RATES:
            raise ValueError("rate")
        lines.append(f"cli -s .audio.srate {int(rate)}")
    return lines + [RELOAD] if lines else []


def usb_text(features: dict) -> str:
    """The USB video state in plain words (hardware panel)."""
    usb = features.get("usb") or {}
    if not features:
        return "ще не перевірено"
    if not usb.get("device"):
        return "не підключено" if usb.get("supported") else "не підключено · ця прошивка не кодує USB-відео"
    name = usb["device"]
    if not usb.get("supported"):
        return f"{name}: прошивка камери не вміє кодувати USB-відео (вміють Goke gk7205v200/v500 з OTG)"
    if not usb.get("enabled"):
        return f"{name}: увімкну, коли дрон не заармлено"
    return f"{name}: камера кодує, потік на бічній панелі"


def audio_text(features: dict) -> str:
    audio = features.get("audio") or {}
    if not features:
        return "ще не перевірено"
    if features.get("variant") == "fpv":
        return "у прошивці FPV звуку немає (потрібна Lite або Ultimate)"
    if not audio.get("supported"):
        return "камера не повідомила про мікрофон"
    if not audio.get("enabled"):
        return "мікрофон камери вимкнено"
    return f"мікрофон увімкнено · {audio.get('rate', 8000) // 1000} кГц"


class CameraFeaturesRuntime(QObject):
    changed = Signal()
    _read = Signal(str, object)
    _applied = Signal(str, object)

    def __init__(
        self,
        devices,
        connections,
        shell_for,
        may_restart_video=lambda: True,
        run_async=True,
        poll_ms=POLL_MS,
        clock=time.monotonic,
    ):
        super().__init__()
        self._devices = devices
        self._connections = connections
        self._shell_for = shell_for
        self._may_restart = may_restart_video
        self._run_async = run_async
        self._clock = clock
        self._busy = False
        self._session = None
        self._session_host = ""
        self._lock = threading.Lock()
        self._features: dict = {}
        self._device = getattr(devices, "activeId", "") or ""
        self._message = ""
        self._usb_tried_at = -1e9
        self._read.connect(self._apply)
        self._applied.connect(self._apply_done)
        self._timer = QTimer(self)
        self._timer.setInterval(poll_ms)
        self._timer.timeout.connect(self.poll)
        for name in ("changed",):
            signal = getattr(devices, name, None)
            if signal is not None:
                signal.connect(self._camera_changed)

    # --- what QML shows -------------------------------------------------------
    @Property("QVariantMap", notify=changed)
    def features(self):
        return dict(self._features)

    @Property(str, notify=changed)
    def usbText(self):
        return usb_text(self._features)

    @Property(str, notify=changed)
    def audioText(self):
        return audio_text(self._features)

    @Property(bool, notify=changed)
    def audioSupported(self):
        return bool((self._features.get("audio") or {}).get("supported"))

    @Property(bool, notify=changed)
    def micEnabled(self):
        return bool((self._features.get("audio") or {}).get("enabled"))

    @Property(int, notify=changed)
    def micRate(self):
        return int((self._features.get("audio") or {}).get("rate") or 8000)

    @Property(int, notify=changed)
    def micVolume(self):
        volume = (self._features.get("audio") or {}).get("volume")
        return volume if isinstance(volume, int) else -1

    @Property(str, notify=changed)
    def message(self):
        return self._message

    # --- control ---------------------------------------------------------------
    @Slot()
    def start(self):
        self._timer.start()
        self.poll()

    @Slot()
    def stop(self):
        self._timer.stop()
        self._close()

    def _camera_changed(self):
        device = getattr(self._devices, "activeId", "") or ""
        if device != self._device:
            self._device, self._features, self._message = device, {}, ""
            self._close()
            self.changed.emit()
            if device and self._timer.isActive():
                self.poll()

    def _host(self):
        device_id = getattr(self._devices, "activeId", "") or ""
        return self._connections.control_host(device_id) if device_id else ""

    def _run(self, work):
        if self._run_async:
            threading.Thread(target=work, name="camera-features", daemon=True).start()
        else:
            work()

    def _with_session(self, host, action):
        with self._lock:
            if self._session is None or self._session_host != host:
                self._close_locked()
                self._session = self._shell_for(host).__enter__()
                self._session_host = host
            session = self._session
        try:
            return action(session)
        except Exception:
            self._close()
            raise

    def _close(self):
        with self._lock:
            self._close_locked()

    def _close_locked(self):
        if self._session is not None:
            try:
                self._session.__exit__(None, None, None)
            except Exception:
                pass
        self._session, self._session_host = None, ""

    @Slot()
    def poll(self):
        host = self._host()
        device = getattr(self._devices, "activeId", "") or ""
        if self._busy or not host or not device:
            return
        self._busy = True

        def work():
            try:
                answers = self._with_session(host, lambda s: {k: s.run(c) for k, c in READ_COMMANDS.items()})
                result = parse_features(answers)
            except Exception:
                result = None
            self._read.emit(device, result)

        self._run(work)

    def _apply(self, device, result):
        self._busy = False
        if result is None or device != (getattr(self._devices, "activeId", "") or ""):
            return
        self._features = result
        sync = getattr(self._devices, "syncAutoStreams", None)
        if sync is not None:
            sync(device, streams_for(result), list(AUTO_PATHS))
        self.changed.emit()
        if usb_needs_enabling(result) and self._may_restart() and self._clock() - self._usb_tried_at > 60:
            self._usb_tried_at = self._clock()
            self._send(device, usb_enable_commands(), "USB-відео увімкнено на камері")

    def _send(self, device, lines, done_text):
        host = self._host()
        if not host or not lines:
            return
        self._message = "Застосовую на камері…"
        self.changed.emit()

        def work():
            def action(session):
                for line in lines:
                    code, _ = session.run(line)
                    if code != 0 and line != RELOAD:
                        return False
                return True

            try:
                ok = self._with_session(host, action)
            except Exception:
                ok = False
            self._applied.emit(device, (ok, done_text))

        self._run(work)

    def _apply_done(self, device, result):
        ok, done_text = result
        self._message = done_text if ok else "Камера не прийняла зміну"
        self.changed.emit()
        if ok:
            QTimer.singleShot(3000, self.poll)

    # --- the camera's microphone ------------------------------------------------------
    @Slot(bool)
    def setMicEnabled(self, on):
        if self.audioSupported:
            self._send(
                self._device, audio_commands(enabled=bool(on)), "Мікрофон увімкнено" if on else "Мікрофон вимкнено"
            )

    @Slot(int)
    def setMicVolume(self, volume):
        if self.audioSupported:
            self._send(self._device, audio_commands(volume=volume), "Гучність мікрофона змінено")

    @Slot(int)
    def setMicRate(self, rate):
        if self.audioSupported and int(rate) in AUDIO_RATES:
            self._send(self._device, audio_commands(rate=rate), "Якість звуку змінено")
