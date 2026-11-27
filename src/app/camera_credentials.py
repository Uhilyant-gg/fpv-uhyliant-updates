"""Session-only camera credentials. Secrets are never serialized or exposed in snapshots."""

from PySide6.QtCore import QObject, Property, Signal, Slot


class CameraCredentials(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self._username = 'root'
        self._password = ''

    @Property(str, notify=changed)
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = str(value or '').strip()
        self.changed.emit()

    @Property(str, notify=changed)
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = str(value or '')
        self.changed.emit()

    def secret(self):
        return self._password

    def snapshot(self):
        return {'username': self._username, 'hasPassword': bool(self._password)}

    @Slot()
    def clear(self):
        self._password = ''
        self.changed.emit()

    @Slot()
    def reset(self):
        self._username = 'root'
        self._password = ''
        self.changed.emit()
