"""User-facing presentation fields for saved device records."""

from device_health import device_health


def _category(device_type):
    normalized = str(device_type or "").strip().casefold().replace("_", " ").replace("-", " ")
    if any(value in normalized for value in ("openipc", "camera", "камера")):
        return "01", "Камери", "Камера"
    if normalized in {"fc", "flight controller", "flightcontroller"} or any(
        value in normalized for value in ("польотний контролер", "flight controller")
    ):
        return "02", "Польотні контролери", "Польотний контролер"
    if any(value in normalized for value in ("vehicle", "drone", "літак", "дрон", "транспорт")):
        return "03", "Транспорт", "Транспорт"
    if any(value in normalized for value in ("controller", "пульт", "контролер")):
        return "04", "Контролери", "Контролер"
    return "99", "Інші пристрої", "Інший пристрій"


def device_center_fields(device):
    group_key, group_label, type_label = _category(device.get("type"))
    health = device_health(device)
    identity = device.get("openipcIdentity")
    identity = identity if isinstance(identity, dict) else {}
    version = identity.get("firmware") if identity.get("verified") is True else ""
    try:
        last_observed_at = max(0, int(device.get("lastObservedAt") or 0))
    except (TypeError, ValueError):
        last_observed_at = 0

    labels = {
        "ready": "Ідентичність підтверджена",
        "attention": "Потрібна перевірка",
        "problem": "Є проблема",
        "unknown": "Стан не підтверджено",
    }
    return {
        "deviceGroup": group_key,
        "deviceGroupLabel": group_label,
        "deviceTypeLabel": type_label,
        "health": health.health,
        "healthLabel": labels[health.health],
        "healthSummary": health.summary,
        "versionLabel": str(version).strip() or "Не спостерігалася",
        "lastObservedAt": last_observed_at,
    }
