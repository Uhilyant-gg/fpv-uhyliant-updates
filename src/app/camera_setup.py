"""Configure an OpenIPC camera over SSH so it sends video to the pilot's static IP.

Runs while the camera is on the station's local network. Commands are built only
from validated values (an IPv4 address or host name, a port number), never from
free text, and only a fixed set of commands is ever sent.

Host keys: on the first connection to a camera on a private address the key is
remembered (trust on first use); afterwards a different key is refused.
"""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Callable, Iterable

import connection_profiles as cp

DEFAULT_CREDENTIALS = (("root", "12345"),)  # OpenIPC factory password
CODEC_FROM_CAMERA = {"h264": "h264", "h265": "h265", "hevc": "h265", "avc": "h264"}

MESSAGES = {
    "configured": "Камеру налаштовано: вона надсилатиме відео на статичний IP пілота.",
    "already": "Камера вже надсилає відео на статичний IP пілота.",
    "no-access": "Не вдалося увійти в камеру. Введіть пароль камери в налаштуваннях.",
    "unsafe": "Камера відповіла іншим ключем, ніж раніше. З міркувань безпеки налаштування не змінено.",
    "unreachable": "Камера недоступна в локальній мережі. Налаштування застосуються, коли вона з’явиться.",
    "failed": "Камера не прийняла налаштування. Перевірте, що на ній прошивка OpenIPC.",
}


class SetupError(Exception):
    def __init__(self, state):
        super().__init__(state)
        self.state = state


def push_target(address: str, port: int) -> str:
    """udp://address:port for the camera's outgoing stream, from validated parts only."""
    host = cp.validate_address("static", address)
    port = int(port)
    if not 1024 <= port <= 65535:
        raise ValueError("port-invalid")
    return f"udp://{host}:{port}"


def setup_commands(target: str) -> list[str]:
    if not re.fullmatch(r"udp://[A-Za-z0-9.-]+:\d{4,5}", target):
        raise ValueError("target-invalid")
    return [
        "cli -s .outgoing.enabled true",
        f"cli -s .outgoing.server {target}",
        "killall -1 majestic",
    ]


READ_COMMANDS = {
    "server": "cli -g .outgoing.server",
    "enabled": "cli -g .outgoing.enabled",
    "codec": "cli -g .video0.codec",
}


def trust_on_first_use_policy():
    """Accept an unknown host key only for a camera on a private network, and only the first time.

    A host whose key is already remembered never reaches this policy: paramiko refuses a changed
    key itself (BadHostKeyException). Any other unknown host is refused.
    """
    import paramiko

    class TrustOnFirstUse(paramiko.MissingHostKeyPolicy):
        def missing_host_key(self, client, hostname, key):
            host = hostname[1:].split("]:", 1)[0] if hostname.startswith("[") else hostname
            try:
                private = ipaddress.ip_address(host).is_private
            except ValueError:
                private = False
            if not private:
                raise paramiko.SSHException("unknown host key")
            client.get_host_keys().add(hostname, key.get_name(), key)

    return TrustOnFirstUse()


class CameraShell:
    """One SSH session to a camera (paramiko), with trust-on-first-use host keys."""

    def __init__(
        self, host: str, username: str, password: str, known_hosts: Path, client_factory=None, timeout=10, port=22
    ):
        self.host, self.username, self.password, self.port = host, username, password, port
        self.known_hosts = Path(known_hosts)
        self.client_factory = client_factory
        self.timeout = timeout
        self.client = None

    def __enter__(self):
        # Only cameras on the station's own networks: the local LAN or ZeroTier (private IPv6).
        if not ipaddress.ip_address(self.host).is_private:
            raise SetupError("unreachable")
        if self.client_factory:
            client = self.client_factory()
        else:
            import paramiko

            client = paramiko.SSHClient()
            if self.known_hosts.exists():
                client.load_host_keys(str(self.known_hosts))
            client.set_missing_host_key_policy(trust_on_first_use_policy())
        try:
            client.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                auth_timeout=self.timeout,
                banner_timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False,
            )
        except Exception as error:
            client.close()
            name = type(error).__name__
            if name == "BadHostKeyException":
                raise SetupError("unsafe") from None
            if name in ("AuthenticationException", "BadAuthenticationType"):
                raise SetupError("no-access") from None
            raise SetupError("unreachable") from None
        if not self.client_factory:
            self.known_hosts.parent.mkdir(parents=True, exist_ok=True)
            client.save_host_keys(str(self.known_hosts))
        self.client = client
        return self

    def run(self, command: str) -> tuple[int, str]:
        _stdin, stdout, _stderr = self.client.exec_command(command, timeout=self.timeout)
        output = stdout.read().decode("utf-8", "replace").strip()
        return stdout.channel.recv_exit_status(), output

    def __exit__(self, *exc):
        self.client.close()
        return False


def with_camera(host: str, credentials: Iterable[tuple[str, str]], shell, action) -> dict:
    """Log in with the first working credentials and run ``action(session)``. Never raises."""
    last = "no-access"
    for username, password in credentials:
        if not password:
            continue
        try:
            with shell(host, username, password) as session:
                return action(session)
        except SetupError as error:
            last = error.state
            if last != "no-access":
                break
        except Exception:
            last = "failed"
            break
    return {"state": last, "message": MESSAGES[last]}


def configure_push(
    host: str,
    address: str,
    port: int,
    credentials: Iterable[tuple[str, str]],
    shell: Callable[[str, str, str], CameraShell],
) -> dict:
    """Point the camera's outgoing stream at ``address:port``. Never raises."""
    try:
        target = push_target(address, port)
    except ValueError:
        return {"state": "failed", "message": MESSAGES["failed"]}

    def apply(session):
        code, codec = session.run(READ_COMMANDS["codec"])
        codec = CODEC_FROM_CAMERA.get(codec.strip().strip('"').lower(), "") if code == 0 else ""
        _, server = session.run(READ_COMMANDS["server"])
        _, enabled = session.run(READ_COMMANDS["enabled"])
        if server.strip().strip('"') == target and enabled.strip().strip('"') == "true":
            return {"state": "already", "message": MESSAGES["already"], "codec": codec, "target": target}
        for command in setup_commands(target):
            code, _ = session.run(command)
            if code != 0 and not command.startswith("killall"):
                return {"state": "failed", "message": MESSAGES["failed"]}
        return {"state": "configured", "message": MESSAGES["configured"], "codec": codec, "target": target}

    return with_camera(host, credentials, shell, apply)
