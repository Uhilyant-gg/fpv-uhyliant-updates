from PySide6.QtCore import QObject, Signal

from link_monitor import HISTORY_SECONDS, LOST_AFTER_S, RETRY_EVERY_S, STARTUP_GRACE_S, LinkMonitor


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class Sink(QObject):
    videoFrameChanged = Signal(object)


def make():
    clock = Clock()
    monitor = LinkMonitor(clock=clock)
    sink = Sink()
    monitor.setVideoSink(sink)
    return monitor, sink, clock


def test_nothing_is_reported_off_the_flight_screen():
    monitor, sink, clock = make()
    clock.now += 60
    monitor.evaluate()
    assert not monitor.lost and monitor.text == ""


def test_lost_when_frames_stop_and_counts_seconds():
    monitor, sink, clock = make()
    monitor.setActive(True)
    sink.videoFrameChanged.emit(object())
    clock.now += LOST_AFTER_S - 0.1
    monitor.evaluate()
    assert not monitor.lost, "a short pause between frames is not a loss"
    clock.now += 0.2
    monitor.evaluate()
    assert monitor.lost
    clock.now += 4
    monitor.evaluate()
    assert monitor.lostSeconds == 5
    assert monitor.text == "Зв’язок із камерою втрачено · 5 с · відновлюю автоматично"


def test_restored_when_frames_come_back():
    monitor, sink, clock = make()
    monitor.setActive(True)
    sink.videoFrameChanged.emit(object())
    clock.now += 3
    monitor.evaluate()
    assert monitor.lost
    sink.videoFrameChanged.emit(object())
    assert not monitor.lost and monitor.justRestored
    assert monitor.text == "Зв’язок відновлено"
    for _ in range(4):  # video keeps coming
        clock.now += 0.8
        sink.videoFrameChanged.emit(object())
        monitor.evaluate()
    assert not monitor.lost and not monitor.justRestored and monitor.text == ""


def test_video_start_has_a_grace_period():
    monitor, sink, clock = make()
    monitor.setActive(True)
    clock.now += STARTUP_GRACE_S - 1
    monitor.evaluate()
    assert not monitor.lost, "the first frame may take a few seconds"
    clock.now += 2
    monitor.evaluate()
    assert monitor.lost and monitor.lostSeconds == int(STARTUP_GRACE_S + 1)


def test_leaving_the_flight_screen_clears_the_state():
    monitor, sink, clock = make()
    monitor.setActive(True)
    sink.videoFrameChanged.emit(object())
    clock.now += 3
    monitor.evaluate()
    monitor.setActive(False)
    assert not monitor.lost and monitor.text == ""


def test_switching_sinks_follows_the_new_video_output():
    monitor, sink, clock = make()
    other = Sink()
    monitor.setVideoSink(other)
    monitor.setActive(True)
    other.videoFrameChanged.emit(object())
    clock.now += 1
    sink.videoFrameChanged.emit(object())
    clock.now += 1
    monitor.evaluate()
    assert monitor.lost, "frames from the old output do not count"
    other.videoFrameChanged.emit(object())
    assert not monitor.lost


def test_video_is_reopened_again_and_again_while_lost():
    """UDP push gives no player error, so the monitor itself asks to re-open the video."""
    monitor, sink, clock = make()
    retries = []
    monitor.retryNeeded.connect(lambda: retries.append(clock.now))
    monitor.setActive(True)
    sink.videoFrameChanged.emit(object())
    clock.now += LOST_AFTER_S + 0.1
    monitor.evaluate()
    assert len(retries) == 1, "first re-open right when the loss is noticed"
    clock.now += RETRY_EVERY_S - 0.5
    monitor.evaluate()
    assert len(retries) == 1
    for _ in range(10):
        clock.now += RETRY_EVERY_S
        monitor.evaluate()
    assert len(retries) == 11, "no limit on attempts"
    for _ in range(10):
        sink.videoFrameChanged.emit(object())
        clock.now += 1
        monitor.evaluate()
    assert len(retries) == 11, "no re-opening once video is back"


class Frame:
    def __init__(self, valid):
        self.valid = valid

    def isValid(self):
        return self.valid


def test_an_empty_frame_from_reopening_the_player_is_not_video():
    monitor, sink, clock = make()
    monitor.setActive(True)
    sink.videoFrameChanged.emit(Frame(True))
    clock.now += LOST_AFTER_S + 0.1
    monitor.evaluate()
    assert monitor.lost
    sink.videoFrameChanged.emit(Frame(False))
    assert monitor.lost, "the player was only re-opened, video is not back yet"
    sink.videoFrameChanged.emit(Frame(True))
    assert not monitor.lost and monitor.justRestored


def test_frames_per_second_history_for_the_link_graph():
    monitor, sink, clock = make()
    monitor.setActive(True)
    assert monitor.history == [] and monitor.fps == 0
    for second in range(3):
        for _ in range(30 if second != 1 else 5):
            sink.videoFrameChanged.emit(Frame(True))
        sink.videoFrameChanged.emit(Frame(False))  # empty frames are not counted
        clock.now += 1.0
        monitor.evaluate()
    assert monitor.history == [30, 5, 30]
    assert monitor.fps == 30
    for _ in range(HISTORY_SECONDS + 5):
        clock.now += 1.0
        monitor.evaluate()
    assert len(monitor.history) == HISTORY_SECONDS and monitor.history[-1] == 0
    monitor.setActive(False)
    assert monitor.history == []


class SizedFrame(Frame):
    def width(self):
        return 1280

    def height(self):
        return 720


def test_the_size_of_the_frames_actually_shown():
    monitor, sink, clock = make()
    monitor.setActive(True)
    assert monitor.frameSize == ""
    sink.videoFrameChanged.emit(SizedFrame(True))
    assert monitor.frameSize == "1280×720"
