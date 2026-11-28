"""Real UDP: packets from the camera to this PC turn the "Static IP" status into "camera sends"."""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = r"""
import socket, sys, tempfile
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QObject, QTimer, Signal
import connection_profiles as cp
from connections_runtime import ConnectionsRuntime

class Devices(QObject):
    changed = Signal()
    streamsChanged = Signal()
    items = [{"id": "c1", "host": "192.168.1.10", "onboardingState": "ready"}]
    streams = []
    @property
    def homeItems(self):
        return self.items

app = QCoreApplication(sys.argv)
tmp = Path(tempfile.mkdtemp())
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind(("127.0.0.1", 0)); port = s.getsockname()[1] + 1
store = cp.ConnectionStore(tmp / "c.json")
store.save({"c1": {"static": "93.170.12.5", "pushPort": port}})
rt = ConnectionsRuntime(Devices(), store, run_async=False, sdp_folder=tmp)
assert rt.statuses["c1"]["static"]["label"] == "чекає камеру"
assert port in rt._sockets, "listening on the camera's port"

def send():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(b"\x80" + b"\x00" * 20, ("127.0.0.1", port))

def check():
    assert rt.statuses["c1"]["static"]["label"] == "камера надсилає", rt.statuses
    rt.pauseListening()
    assert rt._sockets == {}, "ports are freed for the player while flying"
    # the player can now bind the same port
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("0.0.0.0", port))
    rt.resumeListening()
    assert port in rt._sockets
    print("ok")
    app.quit()

QTimer.singleShot(50, send)
QTimer.singleShot(400, check)
QTimer.singleShot(5000, lambda: app.exit(2))
sys.exit(app.exec())
"""


def test_udp_packets_mark_the_camera_as_sending():
    result = subprocess.run(
        [sys.executable, "-c", SCRIPT],
        cwd=Path(__file__).resolve().parent,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout
