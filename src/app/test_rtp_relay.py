import socket
import struct
import time

import pytest

from rtp_relay import RtpRelay, RtpStats, parse_rtp


def packet(seq, ts=0, ssrc=0x1234, payload=97, size=1200):
    header = struct.pack("!BBHII", 0x80, payload, seq & 0xFFFF, ts & 0xFFFFFFFF, ssrc)
    return header + b"\0" * (size - 12)


def test_parse_rtp_header():
    assert parse_rtp(packet(7, 900, 0xABCD, 96)) == (7, 900, 0xABCD, 96)
    assert parse_rtp(b"\x00" * 20) is None, "not RTP version 2"
    assert parse_rtp(b"\x80") is None


def test_loss_bitrate_and_window_reset():
    stats = RtpStats()
    for seq in range(100):
        if seq % 10 != 3:  # 10 of 100 lost
            stats.feed(packet(seq, seq * 3000), 10.0 + seq * 0.01)
    window = stats.window(11.0)
    assert window["packets"] == 90
    assert window["lossPct"] == 10.0
    assert window["kbps"] == round(90 * 1200 * 8 / 1000)
    empty = stats.window(12.0)
    assert empty["packets"] == 0 and empty["lossPct"] == 0.0, "each window counts only its own second"


def test_sequence_wraps_around_without_false_loss():
    stats = RtpStats()
    for i, seq in enumerate([65533, 65534, 65535, 0, 1, 2]):
        stats.feed(packet(seq, i * 3000), i * 0.033)
    assert stats.window(1.0)["lossPct"] == 0.0


def test_jitter_is_zero_for_even_arrival_and_grows_for_uneven():
    even = RtpStats()
    for seq in range(60):
        even.feed(packet(seq, seq * 3000), seq / 30)  # 3000 ticks of 90 kHz = 1/30 s
    assert even.window(2.0)["jitterMs"] < 1
    uneven = RtpStats()
    for seq in range(60):
        uneven.feed(packet(seq, seq * 3000), seq / 30 + (0.06 if seq % 2 else 0))
    assert uneven.window(2.0)["jitterMs"] > 20


def test_restarted_stream_is_noticed_by_its_new_source_id():
    stats = RtpStats()
    stats.feed(packet(1, ssrc=1), 0.0)
    assert stats.window(1.0)["restarted"] is False
    stats.feed(packet(5000, ssrc=2), 1.5)
    stats.feed(packet(5001, ssrc=2), 1.6)
    window = stats.window(2.0)
    assert window["restarted"] is True and window["lossPct"] == 0.0, "a new stream is not packet loss"


def test_last_packet_age():
    stats = RtpStats()
    assert stats.window(5.0)["lastPacketAge"] is None
    stats.feed(packet(1), 5.0)
    assert stats.window(7.5)["lastPacketAge"] == 2.5


def free_udp_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_relay_forwards_every_packet_and_counts_them():
    listen, forward = free_udp_port(), free_udp_port()
    player = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    player.bind(("127.0.0.1", forward))
    player.settimeout(2)
    relay = RtpRelay(listen, forward)
    assert relay.start()
    try:
        camera = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for seq in range(20):
            camera.sendto(packet(seq), ("127.0.0.1", listen))
        received = [player.recv(2048) for _ in range(20)]
        assert [parse_rtp(p)[0] for p in received] == list(range(20)), "same packets, same order"
        deadline = time.monotonic() + 2
        while relay.window()["packets"] < 20 and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        relay.stop()
        player.close()
        camera.close()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as again:
        again.bind(("0.0.0.0", listen))  # the port is free again after stop


def test_relay_that_cannot_take_the_port_says_so():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as busy:
        busy.bind(("0.0.0.0", 0))
        relay = RtpRelay(busy.getsockname()[1], free_udp_port())
        assert relay.start() is False
        relay.stop()


@pytest.mark.parametrize("seq", [0, 1])
def test_window_counts_a_single_packet(seq):
    stats = RtpStats()
    stats.feed(packet(seq), 1.0)
    assert stats.window(1.5)["packets"] == 1
