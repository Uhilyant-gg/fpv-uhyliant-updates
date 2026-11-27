"""Pure helpers for flight video recording (DVR).

Kept free of Qt so file naming, folder checks and the texts shown to the pilot
are tested directly.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

MIN_FREE_BYTES = 500 * 1024 * 1024
STOP_FREE_BYTES = 200 * 1024 * 1024
MAX_CAMERA_NAME = 40

_PROBLEMS = {
    "folder-unavailable": "Немає доступу до папки для записів. Виберіть іншу папку в розділі «Запис відео».",
    "low-space": "На диску з папкою для записів замало місця. Звільніть місце або виберіть іншу папку.",
    "no-video": "Запис можна почати, коли на екрані є відео з камери.",
    "recorder-failed": "Не вдалося записати відео. Перевірте папку для записів і спробуйте ще раз.",
    "disk-full": "Запис зупинено: на диску закінчується місце. Записане відео збережено.",
}


def default_recordings_folder() -> str:
    return str(Path.home() / "Videos" / "FPV Uhyliant")


def problem_text(code: str) -> str:
    return _PROBLEMS.get(code, _PROBLEMS["recorder-failed"])


def _safe_camera_name(name: str) -> str:
    cleaned = re.sub(r"[^\w-]+", "-", str(name or ""), flags=re.UNICODE).strip("-_")
    return cleaned[:MAX_CAMERA_NAME]


def recording_file_name(now: datetime, camera_name: str = "") -> str:
    stamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    camera = _safe_camera_name(camera_name)
    return f"FPV_{camera}_{stamp}.mp4" if camera else f"FPV_{stamp}.mp4"


def unique_path(folder: Path | str, name: str) -> Path:
    folder = Path(folder)
    candidate = folder / name
    stem, suffix = os.path.splitext(name)
    counter = 2
    while candidate.exists():
        candidate = folder / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def free_bytes(folder: Path | str) -> int | None:
    try:
        return int(shutil.disk_usage(str(folder)).free)
    except OSError:
        return None


def check_folder(folder: Path | str, min_free: int = MIN_FREE_BYTES) -> str:
    """Return "" when recording into ``folder`` can start, else a problem code.

    A missing folder is created; writability is probed with a temporary file.
    """
    text = str(folder or "").strip()
    if not text or not Path(text).is_absolute():
        return "folder-unavailable"
    path = Path(text)
    try:
        path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            return "folder-unavailable"
        handle, probe = tempfile.mkstemp(prefix=".fpv-write-check-", dir=str(path))
        os.close(handle)
        os.remove(probe)
    except OSError:
        return "folder-unavailable"
    free = free_bytes(path)
    if free is not None and free < min_free:
        return "low-space"
    return ""


def format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"
