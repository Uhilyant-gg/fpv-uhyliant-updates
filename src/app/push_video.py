"""Video that the camera sends to the pilot's static ("white") IPv4 address.

Starlink gives the drone a shared (CGNAT) IPv4 address, so the station cannot
connect to the camera over IPv4. The camera can connect out to the pilot's
public address instead and send RTP there. The station then plays the RTP
stream through a small SDP description, and helps the pilot prepare the home
network: find the public address, check it is really public, and ask the
router to forward the port (UPnP).
"""

from __future__ import annotations

import ipaddress
import re
import socket
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree

BASE_PORT = 5600
CODECS = {"h265": (97, "H265"), "h264": (96, "H264")}
# FFmpeg inside Qt opens only these protocols; RTP/UDP is needed for pushed video.
PROTOCOL_WHITELIST = "file,crypto,data,rtsp,rtp,udp,tcp"
CGNAT = ipaddress.ip_network("100.64.0.0/10")

WAN_SERVICES = (
    "urn:schemas-upnp-org:service:WANIPConnection:1",
    "urn:schemas-upnp-org:service:WANIPConnection:2",
    "urn:schemas-upnp-org:service:WANPPPConnection:1",
)


def sdp_text(port: int, codec: str = "h265") -> str:
    payload, name = CODECS.get(codec, CODECS["h265"])
    return (
        "v=0\r\no=- 0 0 IN IP4 0.0.0.0\r\ns=FPV Uhyliant\r\nc=IN IP4 0.0.0.0\r\nt=0 0\r\n"
        f"m=video {int(port)} RTP/AVP {payload}\r\na=rtpmap:{payload} {name}/90000\r\n"
    )


def write_sdp(folder: Path, device_id: str, port: int, codec: str = "h265") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", device_id) or "camera"
    path = folder / f"push-{safe}.sdp"
    path.write_text(sdp_text(port, codec), encoding="ascii")
    return path


def is_public_ipv4(value: str) -> bool:
    try:
        address = ipaddress.IPv4Address(str(value).strip())
    except ValueError:
        return False
    return address.is_global and address not in CGNAT


def free_port(used: set[int]) -> int:
    """Even ports from 5600 up; RTP traditionally uses even numbers."""
    port = BASE_PORT
    while port in used:
        port += 2
    return port


def lan_address(target: str = "192.0.2.1") -> str:
    """This PC's address on the home network (no packet is sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect((target, 9))
            return probe.getsockname()[0]
    except OSError:
        return ""


class Upnp:
    """Minimal UPnP IGD client: discover the router, read its public address, forward a UDP port."""

    def __init__(self, discover: Callable[[], list[str]] | None = None, http: Callable | None = None):
        self._discover = discover or self._ssdp
        self._http = http or self._fetch

    @staticmethod
    def _ssdp(timeout: float = 2.0) -> list[str]:
        message = (
            "M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nMX: 2\r\n"
            "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n\r\n"
        ).encode()
        locations = []
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(message, ("239.255.255.250", 1900))
            try:
                while True:
                    data, _ = sock.recvfrom(4096)
                    match = re.search(rb"(?im)^location:\s*(\S+)", data)
                    if match:
                        locations.append(match.group(1).decode(errors="ignore"))
            except OSError:
                pass
        return locations

    @staticmethod
    def _fetch(url: str, body: bytes | None = None, headers: dict | None = None) -> bytes:
        request = urllib.request.Request(url, data=body, headers=headers or {}, method="POST" if body else "GET")
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.read()

    def _control(self) -> tuple[str, str] | None:
        for location in self._discover():
            try:
                root = ElementTree.fromstring(self._http(location))
            except (OSError, ElementTree.ParseError, ValueError):
                continue
            for service in root.iter():
                if not service.tag.endswith("service"):
                    continue
                fields = {child.tag.split("}")[-1]: (child.text or "").strip() for child in service}
                if fields.get("serviceType") in WAN_SERVICES and fields.get("controlURL"):
                    return urllib.parse.urljoin(location, fields["controlURL"]), fields["serviceType"]
        return None

    def _soap(self, control, service, action, arguments=""):
        body = (
            '<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
            f'<u:{action} xmlns:u="{service}">{arguments}</u:{action}></s:Body></s:Envelope>'
        ).encode()
        headers = {"Content-Type": 'text/xml; charset="utf-8"', "SOAPAction": f'"{service}#{action}"'}
        return self._http(control, body, headers)

    def external_ip(self) -> str:
        control = self._control()
        if control is None:
            return ""
        try:
            reply = self._soap(*control, "GetExternalIPAddress")
        except OSError:
            return ""
        match = re.search(rb"<NewExternalIPAddress>([^<]*)</NewExternalIPAddress>", reply)
        return match.group(1).decode().strip() if match else ""

    def forward_udp(self, port: int, lan_ip: str, description: str = "FPV Uhyliant video") -> bool:
        control = self._control()
        if control is None or not lan_ip:
            return False
        arguments = (
            f"<NewRemoteHost></NewRemoteHost><NewExternalPort>{int(port)}</NewExternalPort>"
            f"<NewProtocol>UDP</NewProtocol><NewInternalPort>{int(port)}</NewInternalPort>"
            f"<NewInternalClient>{lan_ip}</NewInternalClient><NewEnabled>1</NewEnabled>"
            f"<NewPortMappingDescription>{description}</NewPortMappingDescription>"
            "<NewLeaseDuration>0</NewLeaseDuration>"
        )
        try:
            self._soap(*control, "AddPortMapping", arguments)
        except OSError:
            return False
        return True


def public_ip_https(fetch: Callable[[str], bytes] | None = None) -> str:
    """This network's public IPv4 as seen from the internet (only an address is requested)."""
    fetch = fetch or (lambda url: urllib.request.urlopen(url, timeout=4).read())
    try:
        text = fetch("https://api.ipify.org").decode().strip()
    except (OSError, ValueError):
        return ""
    return text if is_public_ipv4(text) else ""


def bind_this_network(port: int, upnp: Upnp, public_ip: Callable[[], str], lan_ip: Callable[[], str]) -> dict:
    """Prepare the home network so the camera can send video to this PC on ``port``."""
    seen = public_ip()
    router = upnp.external_ip()
    local = lan_ip()
    result = {"publicIp": seen, "routerIp": router, "lanIp": local, "port": int(port), "forwarded": False}
    if not seen:
        result.update(state="no-internet", message="Не вдалося визначити адресу цього інтернету. Перевірте з’єднання.")
        return result
    if router and router != seen or (router and not is_public_ipv4(router)):
        result.update(
            state="grey",
            message="Провайдер дає спільну (сіру) адресу, тож камера не зможе підключитися напряму. "
            "Попросіть у провайдера білу IP-адресу або використовуйте ZeroTier.",
        )
        return result
    result["forwarded"] = upnp.forward_udp(port, local)
    if result["forwarded"]:
        result.update(state="ready", message=f"Готово: роутер пересилатиме відео на цей комп’ютер (порт {port}).")
    else:
        result.update(
            state="manual",
            message=f"Адресу визначено. Роутер не відкрив порт сам: перешліть UDP-порт {port} на адресу {local or 'цього комп’ютера'} у налаштуваннях роутера.",
        )
    return result
