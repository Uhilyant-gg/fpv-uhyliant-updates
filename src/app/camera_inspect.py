"""Read from the camera what a technician would otherwise type: ZeroTier IDs, the
Starlink IPv6 address, firmware variant, flash size and free space.

Only a fixed set of read-only commands is sent. Every parser tolerates a missing
command or an unexpected answer: the value then stays unknown.
"""

from __future__ import annotations

import ipaddress
import re

import camera_setup as cs
import zerotier_local as zt

READ_ONLY_COMMANDS = {
    "ztInfo": "zerotier-cli info",
    "ztNetworks": "zerotier-cli listnetworks",
    "ipv6": "ip -6 -o addr show scope global",
    "release": "cat /etc/os-release",
    "mtd": "cat /proc/mtd",
    "overlay": "df -k /overlay",
}


def parse_zt_node(text: str) -> str:
    match = re.search(r"^200 info ([0-9a-f]{10}) ", text, re.M)
    return match.group(1) if match else ""


def parse_zt_networks(text: str) -> list[dict]:
    """Joined networks; the header line ("<nwid> <name> ...") is skipped."""
    networks = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 6 and parts[:2] == ["200", "listnetworks"] and re.fullmatch(r"[0-9a-f]{16}", parts[2]):
            networks.append({"id": parts[2], "status": parts[5] if len(parts) > 5 else ""})
    return networks


def pick_network(networks: list[dict]) -> str:
    """The camera's network: the only one, or the only one that is up."""
    if len(networks) == 1:
        return networks[0]["id"]
    up = [n for n in networks if n["status"] == "OK"]
    return up[0]["id"] if len(up) == 1 else ""


def parse_global_ipv6(text: str) -> list[str]:
    """Public IPv6 addresses (not ZeroTier/ULA, not link-local)."""
    found = []
    for match in re.finditer(r"inet6 ([0-9a-fA-F:]+)/\d+", text):
        try:
            address = ipaddress.IPv6Address(match.group(1))
        except ValueError:
            continue
        if address.is_global:
            found.append(str(address))
    return found


def parse_release(text: str) -> dict:
    values = dict(re.findall(r'^([A-Z_]+)="?([^"\n]*)"?$', text, re.M))
    return {
        "firmware": values.get("NAME", ""),
        "variant": values.get("BUILD_OPTION", ""),
        "version": values.get("OPENIPC_VERSION") or values.get("VERSION_ID", ""),
    }


def parse_flash_mb(text: str) -> int:
    sizes = re.findall(r"^mtd\d+:\s+([0-9a-fA-F]+)\s", text, re.M)
    total = sum(int(size, 16) for size in sizes)
    return round(total / (1024 * 1024)) if total else 0


def parse_free_kb(text: str) -> int:
    lines = [line.split() for line in text.splitlines() if line.strip()]
    if len(lines) >= 2 and len(lines[-1]) >= 4 and lines[-1][3].isdigit():
        return int(lines[-1][3])
    return 0


def read_facts(session) -> dict:
    def run(key):
        code, output = session.run(READ_ONLY_COMMANDS[key])
        return output if code == 0 else ""

    zt_info = run("ztInfo")
    facts = {
        "ztInstalled": bool(zt_info),
        "ztNode": parse_zt_node(zt_info),
        "ztNetwork": pick_network(parse_zt_networks(run("ztNetworks"))) if zt_info else "",
        "ipv6": parse_global_ipv6(run("ipv6")),
        "flashMb": parse_flash_mb(run("mtd")),
        "freeKb": parse_free_kb(run("overlay")),
    }
    facts.update(parse_release(run("release")))
    return facts


def inspect_camera(host: str, credentials, shell) -> dict:
    """Facts about the camera, or a login/connection problem. Never raises."""

    def action(session):
        return {"state": "read", **read_facts(session)}

    return cs.with_camera(host, credentials, shell, action)


class InspectorPool:
    """Keeps one SSH session per camera open between reads.

    Reading every few seconds must not log in every time: the handshake is the
    expensive part on the camera's small CPU. The session is reused until it
    fails or ``close_all`` is called (before a flight).
    """

    def __init__(self, credentials, shell):
        import threading

        self._credentials = credentials
        self._shell = shell
        self._sessions: dict[str, object] = {}
        self._lock = threading.Lock()

    def inspect(self, host: str) -> dict:
        with self._lock:
            session = self._sessions.get(host)
        if session is not None:
            try:
                return {"state": "read", **read_facts(session)}
            except Exception:
                self._close(host)
        return self._login_and_read(host)

    def _login_and_read(self, host: str) -> dict:
        last = "no-access"
        for username, password in self._credentials():
            if not password:
                continue
            shell = self._shell(host, username, password)
            try:
                session = shell.__enter__()
            except cs.SetupError as error:
                last = error.state
                if last != "no-access":
                    break
                continue
            except Exception:
                last = "failed"
                break
            try:
                facts = read_facts(session)
            except Exception:
                shell.__exit__(None, None, None)
                return {"state": "failed", "message": cs.MESSAGES["failed"]}
            with self._lock:
                self._sessions[host] = session
            return {"state": "read", **facts}
        return {"state": last, "message": cs.MESSAGES[last]}

    def _close(self, host: str):
        with self._lock:
            session = self._sessions.pop(host, None)
        if session is not None:
            try:
                session.__exit__(None, None, None)
            except Exception:
                pass

    def close_all(self):
        with self._lock:
            hosts = list(self._sessions)
        for host in hosts:
            self._close(host)

    @property
    def open_sessions(self) -> int:
        return len(self._sessions)


def summary(facts: dict) -> str:
    """One line for the camera settings, in plain language."""
    if not facts:
        return ""
    parts = []
    name = " ".join(x for x in (facts.get("firmware"), facts.get("variant"), facts.get("version")) if x)
    if name:
        parts.append(name)
    if facts.get("flashMb"):
        parts.append(f"флеш {facts['flashMb']} МБ")
    if facts.get("freeKb"):
        parts.append(f"вільно {facts['freeKb'] / 1024:.1f} МБ".replace(".", ","))
    parts.append("ZeroTier є" if facts.get("ztInstalled") else "ZeroTier немає")
    return " · ".join(parts)


def valid_zt(facts: dict) -> tuple[str, str]:
    """Network and node IDs from the facts if both are well-formed, else empty strings."""
    try:
        return zt.validate_network_id(facts.get("ztNetwork")), zt.validate_node_id(facts.get("ztNode"))
    except ValueError:
        return "", ""
