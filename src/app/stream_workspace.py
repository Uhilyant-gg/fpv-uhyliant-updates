"""Video workspace selection for primary/secondary/PiP without synthesizing streams."""

from PySide6.QtCore import QObject, Property, Signal, Slot


class StreamWorkspace(QObject):
    changed = Signal()

    def __init__(self, devices):
        super().__init__()
        self.devices = devices
        self._primary = ""
        self._secondary = ""

    def _active(self):
        return [s for s in self.devices.activeStreams if s.get("enabled")]

    def _get(self, sid):
        return next((s for s in self._active() if s.get("id") == sid), None)

    def _preferred_primary(self, streams):
        return next((s for s in streams if s.get("kind") == "main"), streams[0] if streams else {})

    def _preferred_secondary(self, streams, primary):
        return next(
            (s for s in streams if s.get("id") != primary and s.get("kind") in ("sub", "secondary", "thermal")), {}
        )

    @Property("QVariantMap", notify=changed)
    def state(self):
        p = self._get(self._primary)
        s = self._get(self._secondary)
        return {
            "primaryId": self._primary if p else "",
            "secondaryId": self._secondary if s else "",
            "primaryKind": (p or {}).get("kind"),
            "secondaryKind": (s or {}).get("kind"),
            "pipAvailable": bool(p and s and p.get("id") != s.get("id")),
        }

    @Slot()
    def autoSelect(self):
        streams = self._active()
        ids = {s.get("id") for s in streams}
        old = (self._primary, self._secondary)
        if self._primary not in ids:
            self._primary = self._preferred_primary(streams).get("id", "")
        if self._secondary not in ids or self._secondary == self._primary:
            self._secondary = self._preferred_secondary(streams, self._primary).get("id", "")
        if old != (self._primary, self._secondary):
            self.changed.emit()

    @Slot(str, result=bool)
    def selectPrimary(self, sid):
        if not self._get(sid):
            return False
        old = (self._primary, self._secondary)
        self._primary = sid
        if self._secondary == sid:
            self._secondary = self._preferred_secondary(self._active(), self._primary).get("id", "")
        if old != (self._primary, self._secondary):
            self.changed.emit()
        return True

    @Slot(str, result=bool)
    def selectSecondary(self, sid):
        if not self._get(sid) or sid == self._primary:
            return False
        if self._secondary != sid:
            self._secondary = sid
            self.changed.emit()
        return True

    @Slot()
    def swap(self):
        if self.state["pipAvailable"]:
            self._primary, self._secondary = self._secondary, self._primary
            self.changed.emit()
