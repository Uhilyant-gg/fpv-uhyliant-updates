import json
import os
from datetime import datetime, timezone
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot

DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FPV-Uhyliant"


class VehicleRuntime(QObject):
    changed = Signal()

    def __init__(self, telemetry_provider, video):
        super().__init__()
        self.telemetry_provider = telemetry_provider
        self.video = video
        self._snapshot = {}
        self._diagnostics = {}
        telemetry_provider.changed.connect(self.refresh)
        video.changed.connect(self.refresh)
        self.refresh()

    @Property("QVariantMap", notify=changed)
    def snapshot(self):
        return self._snapshot

    @Property("QVariantMap", notify=changed)
    def diagnostics(self):
        return self._diagnostics

    @Property(str, notify=changed)
    def health(self):
        return self._diagnostics.get("health", "unknown")

    @Slot()
    def refresh(self):
        provider = self.telemetry_provider
        telemetry = dict(provider.telemetry or {})
        video_state = self.video.state
        self._snapshot = {
            "protocol": provider.name,
            "telemetry": telemetry,
            "video": {
                "state": video_state,
                "url": self.video.url,
                "attempts": self.video.attempts,
                "lastEvent": self.video.lastEvent,
            },
        }
        issues = []
        connected = telemetry.get("connected")
        if provider.error:
            issues.append({"severity": "error", "source": provider.name, "message": provider.error})
        elif connected is not True:
            issues.append(
                {"severity": "warning", "source": provider.name, "message": "Немає підтвердженої актуальної телеметрії"}
            )
        if self.video.error:
            issues.append(
                {
                    "severity": "error" if video_state == "error" else "warning",
                    "source": "Відео",
                    "message": self.video.error,
                }
            )
        elif video_state == "stalled":
            issues.append({"severity": "warning", "source": "Відео", "message": "Відеопотік зупинено"})
        health = "error" if any(item["severity"] == "error" for item in issues) else ("warning" if issues else "ok")
        self._diagnostics = {
            "health": health,
            "issues": issues,
            "generatedUtc": datetime.now(timezone.utc).isoformat(),
            "telemetryProvider": provider.name,
            "telemetryConnected": connected,
            "telemetryHealth": telemetry.get("health"),
            "videoState": video_state,
        }
        self.changed.emit()

    @Slot(result=str)
    def exportReport(self):
        DATA.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
        path = DATA / f"vehicle-diagnostics-{stamp}.json"
        path.write_text(
            json.dumps({"vehicle": self._snapshot, "diagnostics": self._diagnostics}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(path)
