"""How the station reaches a camera: connection types, saved addresses and status texts.

Pure helpers shared by the runtime and its tests. The cloud type exists in the
list so the pilot sees it, but it stays unavailable until a server is configured.
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

TYPES = ("local", "static", "cloud", "starlink")
LABELS = {"local": "Локальна", "static": "Статичний IP", "cloud": "ZeroTier", "starlink": "Starlink IPv6"}
ADDRESS_TYPES = ("static", "starlink")
DEFAULT_VIDEO_PORT = 554

_HOSTNAME = re.compile(
    r"^(?=.{1,253}$)([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$"
)


def validate_address(kind: str, value: Any) -> str:
    """Return the normalized address for ``kind`` or raise ValueError."""
    text = str(value or "").strip().strip("[]")
    if kind == "starlink":
        try:
            address = ipaddress.IPv6Address(text)
        except ValueError:
            raise ValueError("address-invalid") from None
        if address.is_unspecified or address.is_loopback or address.is_multicast:
            raise ValueError("address-invalid")
        return str(address)
    if kind == "static":
        try:
            address = ipaddress.IPv4Address(text)
        except ValueError:
            if _HOSTNAME.match(text) and not text.replace(".", "").isdigit():
                return text.lower()
            raise ValueError("address-invalid") from None
        if address.is_unspecified or address.is_loopback or address.is_multicast:
            raise ValueError("address-invalid")
        return str(address)
    raise ValueError("address-invalid")


def status_entry(state: str, latency_ms: int | None = None, label: str | None = None) -> dict[str, Any]:
    labels = {
        "available": f"{latency_ms} мс" if latency_ms is not None else "доступно",
        "unavailable": "недоступно",
        "checking": "перевірка…",
        "unconfigured": "вказати адресу",
        "unsupported": "немає сервера",
    }
    return {"state": state, "latencyMs": latency_ms, "label": label or labels[state]}


def can_fly(selected: str, statuses: Mapping[str, Mapping[str, Any]]) -> bool:
    return bool(selected) and statuses.get(selected, {}).get("state") == "available"


def url_host(host: str) -> str:
    """IPv6 literals need brackets inside a URL."""
    try:
        return f"[{host}]" if isinstance(ipaddress.ip_address(host), ipaddress.IPv6Address) else host
    except ValueError:
        return host


class ConnectionStore:
    """Per-camera addresses: {device_id: {"static": "...", "starlink": "..."}}."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self) -> dict[str, dict[str, str]]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        result: dict[str, dict[str, str]] = {}
        if not isinstance(raw, dict):
            return result
        for device_id, addresses in raw.items():
            if not isinstance(addresses, dict):
                continue
            clean = {}
            for kind in ADDRESS_TYPES:
                try:
                    clean[kind] = validate_address(kind, addresses.get(kind))
                except ValueError:
                    continue
            try:
                from zerotier_local import validate_network_id, validate_node_id

                network, node = (
                    validate_network_id(addresses.get("ztNetwork")),
                    validate_node_id(addresses.get("ztNode")),
                )
                clean.update(ztNetwork=network, ztNode=node)
            except ValueError:
                pass
            if clean:
                result[str(device_id)] = clean
        return result

    def save(self, data: Mapping[str, Mapping[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)
