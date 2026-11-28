"""Talk to the ZeroTier One service on this PC through its local JSON API.

ZeroTier gives every camera a fixed address in a virtual network, whatever
Starlink does to the public addresses. With RFC4193 addressing the camera's
IPv6 address follows from the network ID and the camera's node ID, so the
station needs only those two numbers and never has to sync addresses.

Only localhost is contacted here. The service authenticates local clients with
a token stored in a file that ZeroTier writes on installation.
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

DEFAULT_PORT = 9993
NETWORK_ID = re.compile(r"^[0-9a-f]{16}$")
NODE_ID = re.compile(r"^[0-9a-f]{10}$")

SERVICE_TEXT = {
    "ok": "ZeroTier працює",
    "offline": "ZeroTier запущено, але немає зв’язку з інтернетом",
    "missing": "ZeroTier не встановлено на цьому комп’ютері",
    "stopped": "Служба ZeroTier не запущена",
    "no-access": "Немає доступу до ZeroTier. Один раз відкрийте застосунок ZeroTier на цьому комп’ютері.",
}


def validate_network_id(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not NETWORK_ID.match(text):
        raise ValueError("network-id-invalid")
    return text


def validate_node_id(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not NODE_ID.match(text) or text == "0" * 10:
        raise ValueError("node-id-invalid")
    return text


def rfc4193_address(network_id: str, node_id: str) -> str:
    """fd + network ID (8 bytes) + 0x9993 + node ID (5 bytes), as ZeroTier assigns it."""
    raw = bytes.fromhex("fd" + validate_network_id(network_id) + "9993" + validate_node_id(node_id))
    return str(ipaddress.IPv6Address(raw))


def token_candidates(env: dict | None = None) -> list[Path]:
    env = os.environ if env is None else env
    paths = []
    if env.get("LOCALAPPDATA"):
        paths.append(Path(env["LOCALAPPDATA"]) / "ZeroTier" / "authtoken.secret")
    if env.get("PROGRAMDATA"):
        paths.append(Path(env["PROGRAMDATA"]) / "ZeroTier" / "One" / "authtoken.secret")
    home = Path(env.get("HOME") or env.get("USERPROFILE") or Path.home())
    paths += [
        home / ".zeroTierOneAuthToken",
        home / "Library" / "Application Support" / "ZeroTier" / "One" / "authtoken.secret",
        Path("/var/lib/zerotier-one/authtoken.secret"),
    ]
    return paths


def service_installed(env: dict | None = None) -> bool:
    env = os.environ if env is None else env
    dirs = []
    if env.get("PROGRAMDATA"):
        dirs.append(Path(env["PROGRAMDATA"]) / "ZeroTier" / "One")
    dirs += [Path("/var/lib/zerotier-one"), Path("/Library/Application Support/ZeroTier/One")]
    return any(d.is_dir() for d in dirs)


def read_token(paths: list[Path]) -> str:
    for path in paths:
        try:
            token = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if token:
            return token
    return ""


def peer_path(peer: dict) -> tuple[int | None, bool]:
    """(latency ms or None, True when the link is direct, False when relayed)."""
    latency = peer.get("latency")
    latency = int(latency) if isinstance(latency, (int, float)) and latency >= 0 else None
    paths = peer.get("paths") or []
    direct = any(isinstance(p, dict) and p.get("active", True) and not p.get("expired") for p in paths)
    return latency, direct


class ZeroTierLocal:
    """Reads the state of the local ZeroTier service and joins networks."""

    def __init__(
        self,
        request: Callable[[str, str, str, bytes | None], Any] | None = None,
        token_paths: list[Path] | None = None,
        installed: Callable[[], bool] | None = None,
        port: int = DEFAULT_PORT,
    ):
        self._request = request or self._http
        self._token_paths = token_paths
        self._installed = installed or service_installed
        self._port = port

    def _http(self, method: str, path: str, token: str, body: bytes | None):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self._port}{path}", data=body, method=method, headers={"X-ZT1-Auth": token}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            return json.loads(response.read().decode("utf-8") or "null")

    def _token(self) -> str:
        return read_token(self._token_paths if self._token_paths is not None else token_candidates())

    def snapshot(self) -> dict:
        """Service state, this PC's node ID, joined networks and peers. Never raises."""
        result = {"service": "missing", "nodeId": "", "networks": {}, "peers": {}}
        token = self._token()
        if not token:
            result["service"] = "no-access" if self._installed() else "missing"
            return result
        try:
            status = self._request("GET", "/status", token, None) or {}
            networks = self._request("GET", "/network", token, None) or []
            peers = self._request("GET", "/peer", token, None) or []
        except urllib.error.HTTPError as error:
            result["service"] = "no-access" if error.code in (401, 403) else "stopped"
            return result
        except (OSError, ValueError):
            result["service"] = "stopped"
            return result
        result["service"] = "ok" if status.get("online") else "offline"
        result["nodeId"] = str(status.get("address") or "")
        for network in networks if isinstance(networks, list) else []:
            if isinstance(network, dict) and network.get("id"):
                result["networks"][str(network["id"]).lower()] = {
                    "status": str(network.get("status") or ""),
                    "name": str(network.get("name") or ""),
                }
        for peer in peers if isinstance(peers, list) else []:
            if isinstance(peer, dict) and peer.get("address") and peer.get("role", "LEAF") == "LEAF":
                latency, direct = peer_path(peer)
                result["peers"][str(peer["address"]).lower()] = {"latency": latency, "direct": direct}
        return result

    def join(self, network_id: str) -> bool:
        token = self._token()
        if not token:
            return False
        try:
            self._request("POST", f"/network/{validate_network_id(network_id)}", token, b"{}")
        except (OSError, ValueError):
            return False
        return True


def cloud_status(snapshot: dict, network_id: str, node_id: str) -> tuple[str, str]:
    """(state, label) of the ZeroTier connection to one camera before probing it."""
    service = snapshot.get("service")
    if service in ("missing", "stopped", "no-access"):
        return "unavailable", {
            "missing": "встановіть ZeroTier",
            "stopped": "ZeroTier вимкнено",
            "no-access": "немає доступу",
        }[service]
    if service == "offline":
        return "unavailable", "немає інтернету"
    network = snapshot.get("networks", {}).get(network_id)
    if network is None:
        return "unavailable", "не в мережі"
    if network["status"] in ("ACCESS_DENIED", "REQUESTING_CONFIGURATION"):
        return "unavailable", "чекає дозволу"
    if network["status"] != "OK":
        return "unavailable", "помилка мережі"
    if node_id not in snapshot.get("peers", {}):
        return "unavailable", "камера не в мережі"
    return "ready", ""


def path_label(snapshot: dict, node_id: str, latency_ms: int) -> str:
    peer = snapshot.get("peers", {}).get(node_id, {})
    return f"{latency_ms} мс · " + ("напряму" if peer.get("direct") else "через сервер")
