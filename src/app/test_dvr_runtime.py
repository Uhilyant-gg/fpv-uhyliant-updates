"""DvrRuntime logic with a fake encoder; the real Qt encoder is in test_dvr_recording_qt."""

from datetime import datetime

import pytest
from PySide6.QtCore import QObject, QSettings, Signal

import dvr
from dvr_runtime import FOLDER_KEY, DvrRuntime


class FakePipeline:
    instances = []

    def __init__(self, path, on_finished):
        self.path = path
        self.on_finished = on_finished
        self.frames = []
        self.started = False
        self.stopped = False
        self.accept = True
        FakePipeline.instances.append(self)

    def start(self):
        self.started = True
        self.path.write_bytes(b"")

    def send(self, frame):
        if self.accept:
            self.frames.append(frame.startTime())
            with self.path.open("ab") as out:
                out.write(b"frame")
        return self.accept

    def stop(self):
        self.stopped = True

    def finish(self, failed=False):
        self.on_finished(failed)


class FakeFrame:
    def __init__(self, valid=True):
        self.valid = valid
        self.start = None

    def isValid(self):
        return self.valid

    def setStartTime(self, value):
        self.start = value

    def setEndTime(self, value):
        pass

    def startTime(self):
        return self.start


class FakeSink(QObject):
    videoFrameChanged = Signal(object)


class Clock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value


@pytest.fixture
def make(tmp_path):
    FakePipeline.instances = []

    def build(**kwargs):
        settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
        clock = kwargs.pop("clock", Clock())
        opened = []
        runtime = DvrRuntime(
            settings=settings,
            pipeline_factory=FakePipeline,
            clock=clock,
            now=lambda: datetime(2026, 11, 27, 12, 0, 0),
            default_folder=str(tmp_path / "Videos" / "FPV Uhyliant"),
            open_url=lambda url: opened.append(url.toLocalFile()) or True,
            **kwargs,
        )
        runtime.opened = opened
        runtime.clock = clock
        runtime.settings_store = settings
        return runtime

    return build


def test_default_folder_is_used_until_changed(make, tmp_path):
    runtime = make()
    assert runtime.folder == str(tmp_path / "Videos" / "FPV Uhyliant")
    assert runtime.folderIsDefault


def test_folder_setting_is_persisted_and_accepts_file_urls(make, tmp_path):
    runtime = make()
    target = tmp_path / "Записи"
    assert runtime.setFolder("file://" + str(target))
    assert runtime.folder == str(target)
    assert not runtime.folderIsDefault
    assert runtime.settings_store.value(FOLDER_KEY) == str(target)
    assert make().folder == str(target), "a new runtime reads the saved folder"
    runtime.resetFolder()
    assert runtime.folderIsDefault
    assert make().folderIsDefault


def test_unusable_folder_is_rejected_with_a_safe_message(make, tmp_path):
    runtime = make()
    blocker = tmp_path / "file.txt"
    blocker.write_text("x")
    assert not runtime.setFolder(str(blocker))
    assert runtime.folderIsDefault
    assert runtime.status == dvr.problem_text("folder-unavailable")
    assert runtime.statusLevel == "error"


def test_cannot_start_without_video(make):
    runtime = make()
    assert not runtime.canStart
    assert not runtime.start()
    assert not runtime.recording
    assert runtime.status == dvr.problem_text("no-video")
    assert FakePipeline.instances == []


def test_record_frames_from_the_sink_and_save(make, tmp_path):
    runtime = make()
    sink = FakeSink()
    runtime.setVideoSink(sink)
    runtime.setVideoAvailable(True)
    runtime.setCameraName("Квадрик")
    events = []
    runtime.recordingChanged.connect(lambda: events.append(runtime.recording))
    assert runtime.canStart
    assert runtime.start()
    assert runtime.recording and not runtime.canStart
    pipeline = FakePipeline.instances[0]
    assert pipeline.path == tmp_path / "Videos" / "FPV Uhyliant" / "FPV_Квадрик_2026-11-27_12-00-00.mp4"
    assert pipeline.started

    runtime.clock.value = 100.5
    sink.videoFrameChanged.emit(FakeFrame())
    runtime.clock.value = 100.54
    sink.videoFrameChanged.emit(FakeFrame())
    sink.videoFrameChanged.emit(FakeFrame(valid=False))
    assert pipeline.frames == [0, 40000], "timestamps start at zero with the first frame"

    runtime.clock.value = 165.0
    runtime._tick()
    assert runtime.elapsedText == "01:05"

    runtime.toggle()
    assert pipeline.stopped
    assert not runtime.recording
    assert not runtime.canStart, "a new recording waits until the file is finalized"
    pipeline.finish()
    assert runtime.canStart
    assert runtime.status == "Запис збережено: " + pipeline.path.name
    assert runtime.statusLevel == "info"
    assert runtime.lastFileName == pipeline.path.name
    assert events == [True, False]


def test_frames_are_ignored_when_not_recording(make):
    runtime = make()
    sink = FakeSink()
    runtime.setVideoSink(sink)
    sink.videoFrameChanged.emit(FakeFrame())
    assert FakePipeline.instances == []


def test_switching_sink_stops_frames_from_the_old_one(make):
    runtime = make()
    old, new = FakeSink(), FakeSink()
    runtime.setVideoSink(old)
    runtime.setVideoSink(new)
    runtime.setVideoAvailable(True)
    runtime.start()
    old.videoFrameChanged.emit(FakeFrame())
    new.videoFrameChanged.emit(FakeFrame())
    assert len(FakePipeline.instances[0].frames) == 1


def test_recording_without_frames_leaves_no_file(make):
    runtime = make()
    runtime.setVideoAvailable(True)
    runtime.start()
    pipeline = FakePipeline.instances[0]
    runtime.stop()
    pipeline.finish()
    assert not pipeline.path.exists()
    assert runtime.status == dvr.problem_text("no-video")
    assert runtime.lastFileName == ""


def test_dropped_frames_are_not_counted(make):
    runtime = make()
    sink = FakeSink()
    runtime.setVideoSink(sink)
    runtime.setVideoAvailable(True)
    runtime.start()
    pipeline = FakePipeline.instances[0]
    pipeline.accept = False
    sink.videoFrameChanged.emit(FakeFrame())
    runtime.stop()
    pipeline.finish()
    assert runtime.status == dvr.problem_text("no-video")


def test_encoder_failure_mid_flight_keeps_what_was_written(make):
    runtime = make()
    sink = FakeSink()
    runtime.setVideoSink(sink)
    runtime.setVideoAvailable(True)
    runtime.start()
    pipeline = FakePipeline.instances[0]
    sink.videoFrameChanged.emit(FakeFrame())
    runtime.stop()
    pipeline.finish(failed=True)
    assert runtime.statusLevel == "error"
    assert runtime.status == "Запис перервано. Збережено: " + pipeline.path.name


def test_encoder_that_cannot_start_reports_failure(make):
    def broken(path, on_finished):
        raise RuntimeError("codec")

    runtime = make()
    runtime._pipeline_factory = broken
    runtime.setVideoAvailable(True)
    assert not runtime.start()
    assert not runtime.recording
    assert runtime.status == dvr.problem_text("recorder-failed")


def test_low_space_blocks_start(make, monkeypatch):
    runtime = make()
    runtime.setVideoAvailable(True)
    monkeypatch.setattr(dvr, "free_bytes", lambda path: dvr.MIN_FREE_BYTES - 1)
    assert not runtime.start()
    assert runtime.status == dvr.problem_text("low-space")


def test_recording_stops_when_disk_fills(make, monkeypatch):
    runtime = make()
    sink = FakeSink()
    runtime.setVideoSink(sink)
    runtime.setVideoAvailable(True)
    runtime.start()
    pipeline = FakePipeline.instances[0]
    sink.videoFrameChanged.emit(FakeFrame())
    monkeypatch.setattr(dvr, "free_bytes", lambda path: dvr.STOP_FREE_BYTES - 1)
    for _ in range(10):
        runtime._tick()
    assert not runtime.recording
    assert pipeline.stopped
    pipeline.finish()
    assert runtime.status == dvr.problem_text("disk-full")
    assert pipeline.path.exists()


def test_second_recording_gets_a_new_file(make):
    runtime = make()
    sink = FakeSink()
    runtime.setVideoSink(sink)
    runtime.setVideoAvailable(True)
    for _ in range(2):
        runtime.start()
        sink.videoFrameChanged.emit(FakeFrame())
        runtime.stop()
        FakePipeline.instances[-1].finish()
    first, second = (p.path.name for p in FakePipeline.instances)
    assert first == "FPV_2026-11-27_12-00-00.mp4"
    assert second == "FPV_2026-11-27_12-00-00_2.mp4"


def test_open_folder_creates_and_opens_it(make, tmp_path):
    runtime = make()
    assert runtime.openFolder()
    assert runtime.opened == [str(tmp_path / "Videos" / "FPV Uhyliant")]


def test_shutdown_stops_an_active_recording(make):
    runtime = make()
    runtime.setVideoAvailable(True)
    runtime.start()
    runtime.shutdown(timeout_ms=50)
    assert FakePipeline.instances[0].stopped
    assert not runtime.recording


def test_active_recording_blocks_app_update(tmp_path):
    from backend import Station

    station = Station(QSettings(str(tmp_path / "station.ini"), QSettings.IniFormat))
    assert station.canInstallUpdate()[0]
    station.setRecordingActive(True)
    allowed, reason = station.canInstallUpdate()
    assert not allowed and "активний запис" in reason
    station.setRecordingActive(False)
    assert station.canInstallUpdate()[0]


def test_free_space_is_shown_for_a_missing_folder(make, monkeypatch):
    runtime = make()
    monkeypatch.setattr(dvr, "free_bytes", lambda path: 120 * 1024**3)
    assert runtime.freeSpaceText == "вільно 120 ГБ"


def test_shutdown_wait_is_bounded_with_a_running_qt_app(make):
    # With a Qt application present shutdown really waits for the encoder; it must
    # still return on time when the encoder never reports that the file is finished.
    import time

    from PySide6.QtCore import QCoreApplication

    app = QCoreApplication.instance() or QCoreApplication([])
    assert app is not None
    runtime = make()
    sink = FakeSink()
    runtime.setVideoSink(sink)
    runtime.setVideoAvailable(True)
    runtime.start()
    sink.videoFrameChanged.emit(FakeFrame())
    started = time.monotonic()
    runtime.shutdown(timeout_ms=300)
    assert time.monotonic() - started < 3
    assert FakePipeline.instances[0].stopped
    assert not runtime.recording


def test_shutdown_returns_as_soon_as_the_file_is_finished(make):
    import time

    from PySide6.QtCore import QCoreApplication, QTimer

    app = QCoreApplication.instance() or QCoreApplication([])
    assert app is not None
    runtime = make()
    sink = FakeSink()
    runtime.setVideoSink(sink)
    runtime.setVideoAvailable(True)
    runtime.start()
    sink.videoFrameChanged.emit(FakeFrame())
    pipeline = FakePipeline.instances[0]
    QTimer.singleShot(50, pipeline.finish)
    started = time.monotonic()
    runtime.shutdown(timeout_ms=5000)
    assert time.monotonic() - started < 2
    assert runtime.status == "Запис збережено: " + pipeline.path.name
