"""Presentation model for the operational home dashboard."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from device_health import device_health
from next_action_presentation import present_next_action
from next_best_action import select_next_best_action
from station_health import station_health


def _human_state(health: str) -> str:
    return {
        "ready": "Усе готово",
        "attention": "Потрібна увага",
        "problem": "Є проблема",
        "unknown": "Стан перевіряється",
    }.get(health, "Стан перевіряється")


def _human_summary(reason_code: str) -> str:
    return {
        "device-not-selected": "Камеру ще не додано. Знайдіть її автоматично.",
        "device-identity-unknown": "Ідентичність камери ще не перевірена.",
        "openipc-not-verified": "Камеру знайдено, але її тип ще не підтверджено.",
        "hardware-identity-incomplete": "Камеру OpenIPC підтверджено, але даних про платформу або сенсор бракує.",
        "camera-firmware-required": "Камеру знайдено. Підтвердіть сумісну прошивку — після перевірки відеопотоку вона з’явиться на головному екрані.",
        "camera-video-unverified": "Прошивку камери підтверджено. Повторно знайдіть її, щоб перевірити відеопотік.",
        "camera-connection-problem": "Не вдалося підключитися до камери. Перевірте з’єднання.",
        "camera-connection-needed": "Камера доступна, але ще не підключена.",
        "camera-video-ready": "Камера підключена, відеопотік доступний.",
        "camera-identity-ready": "Камеру OpenIPC і її апаратні дані підтверджено.",
    }.get(reason_code, "Стан камери ще перевіряється.")


def _controller_component(controller: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """A PC-connected RC controller is optional: only an observed controller that
    needs setup contributes, and only its calibrate action."""
    if not isinstance(controller, Mapping) or controller.get("health") != "attention":
        return None
    actions = controller.get("safeActions")
    if not isinstance(actions, (list, tuple)) or "calibrate-controller" not in actions:
        return None
    return {"health": "attention", "safeActions": ["calibrate-controller"]}


def home_dashboard(
    devices: Iterable[Mapping[str, Any]] | None,
    streams: Iterable[Mapping[str, Any]] | None,
    controller: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    all_items = tuple(device for device in (devices or ()) if isinstance(device, Mapping))
    pending = tuple(
        device for device in all_items if device.get("onboardingState") in ("pending-firmware", "pending-video")
    )
    items = tuple(
        device for device in all_items if device.get("onboardingState") not in ("pending-firmware", "pending-video")
    )
    available_streams = tuple(stream for stream in (streams or ()) if isinstance(stream, Mapping))

    if not items:
        camera = device_health(pending[0]) if pending else device_health(None)
    else:
        active = next((device for device in items if device.get("active") is True), items[0])
        active_streams = [
            dict(stream)
            for stream in available_streams
            if stream.get("device_id") == active.get("id") and stream.get("enabled") is True
        ]
        camera_data = dict(active)
        camera_data["streams"] = active_streams
        camera = device_health(camera_data)

    combined = station_health([camera])
    components: dict[str, Any] = {"camera": camera.as_dict()}
    controller_component = _controller_component(controller)
    if controller_component is not None:
        components["controller"] = controller_component
    next_action = present_next_action(select_next_best_action(components).as_dict())

    verified = sum(
        1
        for device in items
        if isinstance(device.get("openipcIdentity"), Mapping) and device["openipcIdentity"].get("verified") is True
    )
    warning_count = len(pending) + sum(
        1
        for device in items
        if not isinstance(device.get("openipcIdentity"), Mapping)
        or device["openipcIdentity"].get("verified") is not True
    )

    return {
        "health": combined.health,
        "title": _human_state(combined.health),
        "summary": _human_summary(camera.reasonCode),
        "deviceCount": len(items),
        "pendingCount": len(pending),
        "verifiedCount": verified,
        "warningCount": warning_count,
        "nextAction": next_action,
    }
