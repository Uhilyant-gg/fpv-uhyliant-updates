import pytest

import push_video as pv


def test_sdp_describes_the_pushed_stream():
    text = pv.sdp_text(5602, "h265")
    assert "m=video 5602 RTP/AVP 97" in text and "a=rtpmap:97 H265/90000" in text
    assert "a=rtpmap:96 H264/90000" in pv.sdp_text(5600, "h264")
    assert "H265" in pv.sdp_text(5600, "unknown")


def test_sdp_file_name_is_safe(tmp_path):
    path = pv.write_sdp(tmp_path, "../c1", 5600)
    assert path.parent == tmp_path and path.name == "push-___c1.sdp"
    assert "5600" in path.read_text()


@pytest.mark.parametrize(
    "value,public",
    [("93.170.12.5", True), ("100.64.1.2", False), ("192.168.1.1", False), ("10.0.0.1", False), ("x", False)],
)
def test_public_ipv4(value, public):
    assert pv.is_public_ipv4(value) is public


def test_free_port_skips_used_even_ports():
    assert pv.free_port(set()) == 5600
    assert pv.free_port({5600, 5602}) == 5604


DESCRIPTION = b"""<?xml version="1.0"?><root xmlns="urn:schemas-upnp-org:device-1-0"><device><deviceList><device>
<serviceList><service><serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>
<controlURL>/ctl/IPConn</controlURL></service></serviceList></device></deviceList></device></root>"""


class Router:
    def __init__(self, external="93.170.12.5", accept_forward=True):
        self.external = external
        self.accept_forward = accept_forward
        self.calls = []

    def http(self, url, body=None, headers=None):
        self.calls.append((url, headers.get("SOAPAction") if headers else None, body))
        if body is None:
            return DESCRIPTION
        if b"GetExternalIPAddress" in body:
            return b"<NewExternalIPAddress>" + self.external.encode() + b"</NewExternalIPAddress>"
        if not self.accept_forward:
            raise OSError("refused")
        return b"<ok/>"


def upnp(router):
    return pv.Upnp(discover=lambda: ["http://192.168.1.1:5000/rootDesc.xml"], http=router.http)


def test_upnp_reads_external_address_and_forwards_udp():
    router = Router()
    client = upnp(router)
    assert client.external_ip() == "93.170.12.5"
    assert client.forward_udp(5602, "192.168.1.20")
    url, action, body = router.calls[-1]
    assert url == "http://192.168.1.1:5000/ctl/IPConn"
    assert action.endswith('#AddPortMapping"')
    assert b"<NewExternalPort>5602</NewExternalPort>" in body and b"<NewProtocol>UDP</NewProtocol>" in body
    assert b"<NewInternalClient>192.168.1.20</NewInternalClient>" in body


def test_no_router_found():
    client = pv.Upnp(discover=lambda: [], http=Router().http)
    assert client.external_ip() == ""
    assert not client.forward_udp(5600, "192.168.1.20")


def test_bind_ready_when_address_is_white_and_port_opens():
    result = pv.bind_this_network(5600, upnp(Router()), lambda: "93.170.12.5", lambda: "192.168.1.20")
    assert result["state"] == "ready" and result["forwarded"]
    assert result["publicIp"] == "93.170.12.5"


def test_bind_detects_a_grey_address():
    result = pv.bind_this_network(
        5600, upnp(Router(external="100.64.3.4")), lambda: "93.170.12.5", lambda: "192.168.1.20"
    )
    assert result["state"] == "grey"
    assert "сіру" in result["message"]


def test_bind_asks_for_manual_forwarding_when_router_refuses():
    router = Router(accept_forward=False)
    result = pv.bind_this_network(5600, upnp(router), lambda: "93.170.12.5", lambda: "192.168.1.20")
    assert result["state"] == "manual"
    assert "5600" in result["message"] and "192.168.1.20" in result["message"]


def test_bind_without_internet():
    result = pv.bind_this_network(5600, upnp(Router()), lambda: "", lambda: "192.168.1.20")
    assert result["state"] == "no-internet"


def test_public_ip_https_rejects_non_public_answers():
    assert pv.public_ip_https(lambda url: b"93.170.12.5\n") == "93.170.12.5"
    assert pv.public_ip_https(lambda url: b"10.0.0.1") == ""

    def broken(url):
        raise OSError("offline")

    assert pv.public_ip_https(broken) == ""


def test_rtp_payload_type_is_read_from_the_header():
    assert pv.rtp_payload_type(bytes([0x80, 0x61]) + bytes(10)) == 97
    assert pv.rtp_payload_type(bytes([0x80, 0xE0]) + bytes(10)) == 96, "marker bit is ignored"
    assert pv.rtp_payload_type(bytes([0x40, 0x61]) + bytes(10)) is None, "not RTP v2"
    assert pv.rtp_payload_type(b"\x80\x61") is None, "too short"
    assert pv.rtp_payload_type(bytes([0x80, 0x21]) + bytes(10)) is None, "static payload types are not video here"
    assert "RTP/AVP 100" in pv.sdp_text(5600, "h265", 100)
