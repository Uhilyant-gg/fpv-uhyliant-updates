"""Record real frames through a QVideoSink into an MP4 file with Qt Multimedia."""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = r"""
import sys, tempfile
from pathlib import Path
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QImage
from PySide6.QtMultimedia import QVideoFrame, QVideoSink
from dvr_runtime import DvrRuntime

app = QGuiApplication(sys.argv)
tmp = Path(tempfile.mkdtemp())
runtime = DvrRuntime(settings=QSettings(str(tmp / "s.ini"), QSettings.IniFormat), default_folder=str(tmp / "rec"))
sink = QVideoSink()
runtime.setVideoSink(sink)
runtime.setVideoAvailable(True)
assert runtime.start(), runtime.status
sent = [0]

def push():
    image = QImage(320, 180, QImage.Format_RGB32)
    image.fill(QColor((sent[0] * 8) % 255, 90, 160))
    sink.setVideoFrame(QVideoFrame(image))
    sent[0] += 1
    if sent[0] == 45:
        timer.stop()
        runtime.shutdown()
        assert not runtime.recording and runtime.canStart, "shutdown waits for the file"
        app.quit()

timer = QTimer(); timer.timeout.connect(push); timer.start(20)
QTimer.singleShot(30000, lambda: (print("timeout"), app.exit(2)))
code = app.exec()
assert code == 0, "recording did not finish"
files = list((tmp / "rec").glob("*.mp4"))
assert len(files) == 1, files
data = files[0].read_bytes()
assert data[4:8] == b"ftyp", data[:16]
assert b"moov" in data, "file is finalized"
assert len(data) > 1000, len(data)
assert runtime.statusLevel == "info", runtime.status
assert runtime.lastFileName == files[0].name
print("ok", len(data))
"""


def test_frames_from_a_video_sink_are_saved_as_mp4(tmp_path):
    # Qt Multimedia may start an audio daemon (PulseAudio autospawn) that outlives the
    # child and keeps inherited pipes open, so output goes to files and autospawn is off.
    client_conf = tmp_path / "pulse-client.conf"
    client_conf.write_text("autospawn = no\n")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PULSE_CLIENTCONFIG=str(client_conf))
    out_path, err_path = tmp_path / "out.txt", tmp_path / "err.txt"
    with out_path.open("w") as out, err_path.open("w") as err:
        process = subprocess.Popen(
            [sys.executable, "-c", SCRIPT],
            cwd=Path(__file__).resolve().parent,
            env=env,
            stdout=out,
            stderr=err,
            start_new_session=True,
        )
        try:
            code = process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            code = "timeout"
    output = out_path.read_text() + err_path.read_text()
    assert code == 0, output
    assert "ok" in output
