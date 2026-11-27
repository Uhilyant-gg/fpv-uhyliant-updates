"""Flight video recording (DVR) started and stopped by the pilot.

Frames come from the video sink of the primary player, so the recording is
exactly the picture shown on screen, encoded into an MP4 file through Qt
Multimedia (H.264 where the platform has an encoder, as on Windows).
The recordings folder is a station setting, not part of a vehicle preset.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QCoreApplication,
    QEventLoop,
    QObject,
    QSettings,
    QStandardPaths,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtMultimedia import QMediaCaptureSession, QMediaFormat, QMediaRecorder, QVideoFrameInput, QVideoSink

import dvr

FOLDER_KEY = "recording/folder"
DISK_CHECK_EVERY_TICKS = 10


def _local_path(value) -> str:
    text = str(value or "").strip()
    url = QUrl(text)
    return url.toLocalFile() if url.isLocalFile() else text


def system_default_folder() -> str:
    movies = QStandardPaths.writableLocation(QStandardPaths.MoviesLocation)
    return str(Path(movies) / "FPV Uhyliant") if movies else dvr.default_recordings_folder()


class QtRecorderPipeline:
    """Qt Multimedia encoder fed with QVideoFrames."""

    def __init__(self, path: Path, on_finished):
        self._on_finished = on_finished
        self._failed = False
        self._done = False
        self.input = QVideoFrameInput()
        self.session = QMediaCaptureSession()
        self.session.setVideoFrameInput(self.input)
        self.recorder = QMediaRecorder()
        self.session.setRecorder(self.recorder)
        media_format = QMediaFormat(QMediaFormat.FileFormat.MPEG4)
        if QMediaFormat.VideoCodec.H264 in media_format.supportedVideoCodecs(QMediaFormat.ConversionMode.Encode):
            media_format.setVideoCodec(QMediaFormat.VideoCodec.H264)
        self.recorder.setMediaFormat(media_format)
        self.recorder.setQuality(QMediaRecorder.Quality.HighQuality)
        self.recorder.setOutputLocation(QUrl.fromLocalFile(str(path)))
        self.recorder.errorOccurred.connect(self._error)
        self.recorder.recorderStateChanged.connect(self._state)

    def start(self):
        self.recorder.record()

    def send(self, frame) -> bool:
        return bool(self.input.sendVideoFrame(frame))

    def stop(self):
        self.recorder.stop()

    def _error(self, *_):
        self._failed = True
        if self.recorder.recorderState() == self.recorder.RecorderState.StoppedState:
            self._finish()

    def _state(self, state):
        if state == self.recorder.RecorderState.StoppedState:
            self._finish()

    def _finish(self):
        if not self._done:
            self._done = True
            self._on_finished(self._failed)


class DvrRuntime(QObject):
    changed = Signal()
    recordingChanged = Signal()

    def __init__(
        self,
        settings=None,
        pipeline_factory=QtRecorderPipeline,
        clock=time.monotonic,
        now=datetime.now,
        default_folder=None,
        open_url=QDesktopServices.openUrl,
    ):
        super().__init__()
        self._settings = settings or QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        self._pipeline_factory = pipeline_factory
        self._clock = clock
        self._now = now
        self._default_folder = default_folder or system_default_folder()
        self._open_url = open_url
        self._folder = str(self._settings.value(FOLDER_KEY, "") or "").strip()
        self._sink = None
        self._video_available = False
        self._camera_name = ""
        self._pipeline = None
        self._recording = False
        self._finishing = False
        self._stop_reason = ""
        self._path = None
        self._started = 0.0
        self._first_frame_us = None
        self._frames = 0
        self._elapsed = 0.0
        self._ticks = 0
        self._status = ""
        self._status_level = ""
        self._last_file = ""
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    # --- properties -----------------------------------------------------
    @Property(bool, notify=changed)
    def recording(self):
        return self._recording

    @Property(bool, notify=changed)
    def canStart(self):
        return self._video_available and not self._recording and not self._finishing

    @Property(str, notify=changed)
    def folder(self):
        return self._folder or self._default_folder

    @Property(QUrl, notify=changed)
    def folderUrl(self):
        return QUrl.fromLocalFile(self.folder)

    @Property(bool, notify=changed)
    def folderIsDefault(self):
        return not self._folder

    @Property(str, notify=changed)
    def elapsedText(self):
        return dvr.format_duration(self._elapsed)

    @Property(str, notify=changed)
    def freeSpaceText(self):
        folder = Path(self.folder)
        while not folder.exists() and folder.parent != folder:
            folder = folder.parent
        return dvr.format_free_space(dvr.free_bytes(folder))

    @Property(str, notify=changed)
    def status(self):
        return self._status

    @Property(str, notify=changed)
    def statusLevel(self):
        return self._status_level

    @Property(str, notify=changed)
    def lastFileName(self):
        return self._last_file

    # --- wiring from QML -------------------------------------------------
    @Slot(QVideoSink)
    def setVideoSink(self, sink):
        if sink is self._sink:
            return
        if self._sink is not None:
            try:
                self._sink.videoFrameChanged.disconnect(self._frame)
            except (RuntimeError, TypeError):
                pass
        self._sink = sink
        if sink is not None:
            sink.videoFrameChanged.connect(self._frame)

    @Slot(bool)
    def setVideoAvailable(self, available):
        available = bool(available)
        if available != self._video_available:
            self._video_available = available
            self.changed.emit()

    @Slot(str)
    def setCameraName(self, name):
        self._camera_name = str(name or "")

    # --- folder setting -------------------------------------------------
    @Slot(str, result=bool)
    def setFolder(self, value):
        path = _local_path(value)
        problem = dvr.check_folder(path, min_free=0)
        if problem:
            self._set_status(dvr.problem_text(problem), "error")
            return False
        self._folder = str(Path(path))
        self._settings.setValue(FOLDER_KEY, self._folder)
        self._settings.sync()
        self._set_status("Нові записи зберігатимуться в цю папку.", "info")
        return True

    @Slot()
    def resetFolder(self):
        self._folder = ""
        self._settings.remove(FOLDER_KEY)
        self._settings.sync()
        self._set_status("Повернуто типову папку для записів.", "info")

    @Slot(result=bool)
    def openFolder(self):
        folder = self.folder
        if dvr.check_folder(folder, min_free=0):
            self._set_status(dvr.problem_text("folder-unavailable"), "error")
            return False
        return bool(self._open_url(QUrl.fromLocalFile(folder)))

    # --- recording ------------------------------------------------------
    @Slot()
    def toggle(self):
        if self._recording:
            self.stop()
        else:
            self.start()

    @Slot(result=bool)
    def start(self):
        if self._recording or self._finishing:
            return False
        if not self._video_available:
            self._set_status(dvr.problem_text("no-video"), "error")
            return False
        folder = self.folder
        problem = dvr.check_folder(folder)
        if problem:
            self._set_status(dvr.problem_text(problem), "error")
            return False
        path = dvr.unique_path(folder, dvr.recording_file_name(self._now(), self._camera_name))
        try:
            pipeline = self._pipeline_factory(path, self._finished)
            pipeline.start()
        except Exception:
            self._set_status(dvr.problem_text("recorder-failed"), "error")
            return False
        self._pipeline = pipeline
        self._path = path
        self._recording = True
        self._started = self._clock()
        self._first_frame_us = None
        self._frames = 0
        self._elapsed = 0.0
        self._ticks = 0
        self._status = ""
        self._status_level = ""
        self._timer.start()
        self.changed.emit()
        self.recordingChanged.emit()
        return True

    @Slot()
    def stop(self):
        self._stop("")

    @Slot()
    def shutdown(self, timeout_ms=5000):
        """Stop and wait until the file is finalized, so closing the app keeps the video playable."""
        self._stop("")
        if not self._finishing or QCoreApplication.instance() is None:
            return
        loop = QEventLoop()
        self.changed.connect(loop.quit)
        QTimer.singleShot(timeout_ms, loop.quit)
        deadline = time.monotonic() + timeout_ms / 1000
        while self._finishing and time.monotonic() < deadline:
            loop.exec()
        self.changed.disconnect(loop.quit)

    def _stop(self, reason):
        if not self._recording:
            return
        self._recording = False
        self._finishing = True
        self._stop_reason = reason
        self._timer.stop()
        self._elapsed = max(0.0, self._clock() - self._started)
        self.changed.emit()
        self.recordingChanged.emit()
        pipeline = self._pipeline
        try:
            pipeline.stop()
        except Exception:
            self._finished(True)

    def _frame(self, frame):
        if not self._recording or self._pipeline is None:
            return
        try:
            if not frame.isValid():
                return
        except AttributeError:
            return
        now_us = int(self._clock() * 1_000_000)
        if self._first_frame_us is None:
            self._first_frame_us = now_us
        start_us = now_us - self._first_frame_us
        try:
            frame.setStartTime(start_us)
            frame.setEndTime(-1)
        except AttributeError:
            pass
        try:
            if self._pipeline.send(frame):
                self._frames += 1
        except Exception:
            self._stop("recorder-failed")

    def _tick(self):
        if not self._recording:
            return
        self._elapsed = max(0.0, self._clock() - self._started)
        self._ticks += 1
        if self._ticks % DISK_CHECK_EVERY_TICKS == 0 and self._path is not None:
            free = dvr.free_bytes(self._path.parent)
            if free is not None and free < dvr.STOP_FREE_BYTES:
                self._stop("disk-full")
                return
        self.changed.emit()

    def _finished(self, failed):
        if not self._finishing:
            return
        self._finishing = False
        self._pipeline = None
        path, self._path = self._path, None
        reason = self._stop_reason
        saved = path is not None and self._frames > 0 and _non_empty(path)
        if not saved and path is not None:
            _remove_quietly(path)
        if saved:
            self._last_file = path.name
        if failed and not saved:
            self._set_status(dvr.problem_text("recorder-failed"), "error")
        elif not saved:
            self._set_status(dvr.problem_text("no-video"), "error")
        elif reason == "disk-full":
            self._set_status(dvr.problem_text("disk-full"), "error")
        elif failed or reason:
            self._set_status("Запис перервано. Збережено: " + path.name, "error")
        else:
            self._set_status("Запис збережено: " + path.name, "info")

    def _set_status(self, text, level):
        self._status = text
        self._status_level = level
        self.changed.emit()


def _non_empty(path: Path) -> bool:
    try:
        return path.stat().st_size > 0
    except OSError:
        return False


def _remove_quietly(path: Path):
    try:
        os.remove(path)
    except OSError:
        pass
