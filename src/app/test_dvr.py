from datetime import datetime
from pathlib import Path

import pytest

import dvr


def test_file_name_uses_local_time_and_camera_name():
    now = datetime(2026, 11, 27, 21, 5, 9)
    assert dvr.recording_file_name(now, "Квадрик 5\"") == "FPV_Квадрик-5_2026-11-27_21-05-09.mp4"


def test_file_name_without_camera_name():
    now = datetime(2026, 1, 2, 3, 4, 5)
    assert dvr.recording_file_name(now, "") == "FPV_2026-01-02_03-04-05.mp4"
    assert dvr.recording_file_name(now, " :/\\*?<>| ") == "FPV_2026-01-02_03-04-05.mp4"


def test_file_name_limits_camera_name_length():
    name = dvr.recording_file_name(datetime(2026, 1, 2, 3, 4, 5), "x" * 200)
    assert name == "FPV_" + "x" * dvr.MAX_CAMERA_NAME + "_2026-01-02_03-04-05.mp4"


def test_unique_path_adds_a_counter(tmp_path):
    assert dvr.unique_path(tmp_path, "a.mp4") == tmp_path / "a.mp4"
    (tmp_path / "a.mp4").write_bytes(b"")
    (tmp_path / "a_2.mp4").write_bytes(b"")
    assert dvr.unique_path(tmp_path, "a.mp4") == tmp_path / "a_3.mp4"


def test_check_folder_creates_missing_folder(tmp_path):
    folder = tmp_path / "нова" / "папка"
    assert dvr.check_folder(folder) == ""
    assert folder.is_dir()
    assert list(folder.iterdir()) == [], "the write probe is removed"


def test_check_folder_rejects_a_file(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("x")
    assert dvr.check_folder(target) == "folder-unavailable"


def test_check_folder_rejects_empty_or_relative_path():
    assert dvr.check_folder("") == "folder-unavailable"
    assert dvr.check_folder("relative/dir") == "folder-unavailable"


def test_check_folder_reports_low_space(tmp_path, monkeypatch):
    class Usage:
        free = dvr.MIN_FREE_BYTES - 1

    monkeypatch.setattr(dvr.shutil, "disk_usage", lambda path: Usage())
    assert dvr.check_folder(tmp_path) == "low-space"


def test_every_problem_has_a_user_message():
    for code in ("folder-unavailable", "low-space", "no-video", "recorder-failed", "disk-full"):
        assert dvr.problem_text(code)
    assert dvr.problem_text("anything-else") == dvr.problem_text("recorder-failed")


@pytest.mark.parametrize(
    "seconds,text",
    [(0, "00:00"), (9.9, "00:09"), (65, "01:05"), (3599, "59:59"), (3600, "1:00:00"), (7384, "2:03:04"), (-5, "00:00")],
)
def test_format_duration(seconds, text):
    assert dvr.format_duration(seconds) == text


def test_default_folder_is_absolute():
    assert Path(dvr.default_recordings_folder()).is_absolute()


@pytest.mark.parametrize(
    "free,text",
    [
        (None, ""),
        (300 * 1024**2, "вільно 300 МБ"),
        (int(2.5 * 1024**3), "вільно 2,5 ГБ"),
        (120 * 1024**3, "вільно 120 ГБ"),
    ],
)
def test_format_free_space(free, text):
    assert dvr.format_free_space(free) == text
