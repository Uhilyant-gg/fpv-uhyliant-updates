"""Local RC controller detection and live input acquisition.

Radios such as EdgeTX/OpenTX transmitters expose themselves to Windows as USB HID
joysticks. This module observes them through the WinMM joystick API (no extra
dependency) behind an injectable source, so tests and non-Windows hosts never
synthesize controller presence or channel values.

Evidence rules:
- a controller is only ``connected`` when the source returned a live input frame;
- identity is derived from observed vendor/product/name only, never from the
  joystick slot index, and identical devices are reported as ambiguous instead of
  guessed;
- every observation carries ``observedAt`` so consumers can reject stale input.
"""
from __future__ import annotations

import math
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

TRANSPORT_USB_HID = "usb-hid"
DEFAULT_MAX_AGE_SECONDS = 1.0
_MAX_CHANNELS = 16
_MAX_NAME_LENGTH = 64


class ControllerSourceUnavailable(RuntimeError):
    """The local controller input API cannot be used on this host."""


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _clean_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    printable = "".join(ch for ch in value if ch.isprintable()).strip()
    return printable[:_MAX_NAME_LENGTH]


def _hardware_key(raw: Mapping[str, Any]) -> str | None:
    vendor, product = raw.get("vendorId"), raw.get("productId")
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 0xFFFF for v in (vendor, product)):
        return None
    name = _clean_name(raw.get("name"))
    if not name:
        return None
    return f"{TRANSPORT_USB_HID}:{vendor:04x}:{product:04x}:{name}"


def _channels(raw: Mapping[str, Any]) -> list[int | float] | None:
    channels = raw.get("channels")
    if not isinstance(channels, (list, tuple)) or not 0 < len(channels) <= _MAX_CHANNELS:
        return None
    if any(not _finite_number(v) for v in channels):
        return None
    return list(channels)


def discover_controllers(source: Any, clock: Callable[[], float] | None = None) -> dict[str, Any]:
    """Return fresh observations for all locally visible controllers.

    The result is ``{"available": bool, "reasonCode": str, "controllers": [...]}``.
    A failing or missing source is ``available: False`` (unknown), never "no controller".
    """
    clock = clock or time.monotonic
    if source is None:
        return {"available": False, "reasonCode": "controller-source-unavailable", "controllers": []}
    try:
        raw_devices = list(source.poll())
    except ControllerSourceUnavailable:
        return {"available": False, "reasonCode": "controller-source-unavailable", "controllers": []}
    except Exception:  # noqa: BLE001 - any API failure is unknown evidence, not absence
        return {"available": False, "reasonCode": "controller-source-failed", "controllers": []}
    observed_at = clock()

    keyed: dict[str, list[dict[str, Any]]] = {}
    unidentified: list[dict[str, Any]] = []
    for raw in raw_devices:
        if not isinstance(raw, Mapping):
            continue
        key = _hardware_key(raw)
        channels = _channels(raw)
        entry = {
            "name": _clean_name(raw.get("name")) or None,
            "transport": TRANSPORT_USB_HID,
            "connected": channels is not None,
            "channels": channels,
            "observedAt": observed_at,
        }
        if key is None:
            unidentified.append({**entry, "id": None, "reasonCode": "controller-identity-unavailable"})
        else:
            keyed.setdefault(key, []).append(entry)

    controllers: list[dict[str, Any]] = []
    for key in sorted(keyed):
        group = keyed[key]
        if len(group) == 1:
            reason = "controller-input-observed" if group[0]["connected"] else "controller-input-unavailable"
            controllers.append({**group[0], "id": key, "reasonCode": reason})
        else:
            for entry in group:
                controllers.append({**entry, "id": None, "reasonCode": "controller-identity-ambiguous"})
    controllers.extend(unidentified)
    return {"available": True, "reasonCode": "controller-source-observed", "controllers": controllers}


def is_fresh(observation: Mapping[str, Any] | None, now: float, max_age: float = DEFAULT_MAX_AGE_SECONDS) -> bool:
    if not isinstance(observation, Mapping):
        return False
    observed_at = observation.get("observedAt")
    if not _finite_number(observed_at):
        return False
    return 0 <= now - observed_at <= max_age


def select_controller(discovery: Mapping[str, Any], saved_ids: Iterable[str] = ()) -> dict[str, Any]:
    """Pick the single controller to use without guessing between candidates."""
    if not isinstance(discovery, Mapping) or discovery.get("available") is not True:
        reason = discovery.get("reasonCode") if isinstance(discovery, Mapping) else None
        return {"health": "unknown", "controller": None, "reasonCode": reason or "controller-source-unavailable"}
    controllers = [c for c in discovery.get("controllers", []) if isinstance(c, Mapping)]
    identified = [c for c in controllers if c.get("id")]
    if not controllers:
        return {"health": "unknown", "controller": None, "reasonCode": "controller-not-observed"}
    if not identified:
        reason = controllers[0].get("reasonCode") if len(controllers) == 1 else "controller-identity-ambiguous"
        return {"health": "attention", "controller": None, "reasonCode": reason or "controller-identity-unavailable"}
    if len(identified) == 1 and len(controllers) == 1:
        return {"health": "ready", "controller": dict(identified[0]), "reasonCode": "controller-selected"}
    saved = set(saved_ids)
    matches = [c for c in identified if c["id"] in saved]
    if len(matches) == 1:
        return {"health": "ready", "controller": dict(matches[0]), "reasonCode": "controller-selected-saved"}
    return {
        "health": "attention",
        "controller": None,
        "reasonCode": "controller-selection-required",
        "candidates": [c["id"] for c in identified],
    }


class WinMMJoystickSource:
    """Read USB HID joysticks through ``winmm.dll``; Windows only."""

    _JOY_RETURNALL = 0x000000FF
    _JOYERR_NOERROR = 0

    def __init__(self, dll: Any = None):
        if dll is None:
            if sys.platform != "win32":
                raise ControllerSourceUnavailable("winmm-unavailable")
            import ctypes

            dll = ctypes.WinDLL("winmm")
        self._dll = dll
        self._structs = self._build_structs()

    @staticmethod
    def _build_structs():
        import ctypes
        from ctypes import wintypes

        class JOYCAPSW(ctypes.Structure):
            _fields_ = [
                ("wMid", wintypes.WORD), ("wPid", wintypes.WORD), ("szPname", wintypes.WCHAR * 32),
                ("wXmin", wintypes.UINT), ("wXmax", wintypes.UINT), ("wYmin", wintypes.UINT), ("wYmax", wintypes.UINT),
                ("wZmin", wintypes.UINT), ("wZmax", wintypes.UINT), ("wNumButtons", wintypes.UINT),
                ("wPeriodMin", wintypes.UINT), ("wPeriodMax", wintypes.UINT), ("wRmin", wintypes.UINT),
                ("wRmax", wintypes.UINT), ("wUmin", wintypes.UINT), ("wUmax", wintypes.UINT), ("wVmin", wintypes.UINT),
                ("wVmax", wintypes.UINT), ("wCaps", wintypes.UINT), ("wMaxAxes", wintypes.UINT),
                ("wNumAxes", wintypes.UINT), ("wMaxButtons", wintypes.UINT), ("szRegKey", wintypes.WCHAR * 32),
                ("szOEMVxD", wintypes.WCHAR * 260),
            ]

        class JOYINFOEX(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD), ("dwFlags", wintypes.DWORD), ("dwXpos", wintypes.DWORD),
                ("dwYpos", wintypes.DWORD), ("dwZpos", wintypes.DWORD), ("dwRpos", wintypes.DWORD),
                ("dwUpos", wintypes.DWORD), ("dwVpos", wintypes.DWORD), ("dwButtons", wintypes.DWORD),
                ("dwButtonNumber", wintypes.DWORD), ("dwPOV", wintypes.DWORD), ("dwReserved1", wintypes.DWORD),
                ("dwReserved2", wintypes.DWORD),
            ]

        return JOYCAPSW, JOYINFOEX

    def poll(self) -> list[dict[str, Any]]:
        import ctypes

        JOYCAPSW, JOYINFOEX = self._structs
        devices: list[dict[str, Any]] = []
        for index in range(int(self._dll.joyGetNumDevs())):
            info = JOYINFOEX()
            info.dwSize = ctypes.sizeof(JOYINFOEX)
            info.dwFlags = self._JOY_RETURNALL
            if self._dll.joyGetPosEx(index, ctypes.byref(info)) != self._JOYERR_NOERROR:
                continue  # empty slot or unplugged device: no evidence, no entry
            caps = JOYCAPSW()
            if self._dll.joyGetDevCapsW(index, ctypes.byref(caps), ctypes.sizeof(JOYCAPSW)) != self._JOYERR_NOERROR:
                continue
            axes = [info.dwXpos, info.dwYpos, info.dwZpos, info.dwRpos, info.dwUpos, info.dwVpos]
            count = max(0, min(int(caps.wNumAxes), len(axes)))
            devices.append({
                "vendorId": int(caps.wMid),
                "productId": int(caps.wPid),
                "name": caps.szPname,
                "channels": [int(v) for v in axes[:count]],
            })
        return devices


def default_source() -> Any:
    """Return the platform controller source, or ``None`` when none is available."""
    try:
        return WinMMJoystickSource()
    except (ControllerSourceUnavailable, OSError):
        return None
