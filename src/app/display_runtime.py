import weakref

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QGuiApplication, QWindow


def display_inventory(screens):
    displays = []
    for index, screen in enumerate(screens):
        geometry = screen.availableGeometry()
        displays.append({
            "index": index,
            "label": f"Екран {index + 1} · {geometry.width()} × {geometry.height()}",
        })
    return displays


class DisplayRuntime(QObject):
    changed = Signal()

    def __init__(self, application=None):
        super().__init__()
        self._application = application or QGuiApplication.instance()
        if self._application is None:
            raise RuntimeError("Display runtime requires a GUI application")
        self._window_refs = []
        self._application.screenAdded.connect(self._screen_changed)
        self._application.screenRemoved.connect(self._screen_removed)

    @Property("QVariantList", notify=changed)
    def displays(self):
        return display_inventory(self._application.screens())

    @Slot(QObject, int, result=bool)
    def moveWindow(self, window, index):
        screens = self._application.screens()
        if not isinstance(window, QWindow) or index < 0 or index >= len(screens):
            return False
        screen = screens[index]
        available = screen.availableGeometry()
        width = min(max(1, window.width()), available.width())
        height = min(max(1, window.height()), available.height())
        window.setScreen(screen)
        window.resize(width, height)
        window.setPosition(
            available.x() + max(0, (available.width() - width) // 2),
            available.y() + max(0, (available.height() - height) // 2),
        )
        self.trackWindow(window)
        return True

    @Slot(QObject, result=bool)
    def trackWindow(self, window):
        if not isinstance(window, QWindow):
            return False
        self._window_refs = [ref for ref in self._window_refs if ref() is not None and ref() is not window]
        self._window_refs.append(weakref.ref(window))
        return True

    def _screen_changed(self, _screen):
        self.changed.emit()

    def _screen_removed(self, removed):
        screens = self._application.screens()
        primary = self._application.primaryScreen()
        if primary is not None and primary in screens:
            primary_index = screens.index(primary)
            for reference in tuple(self._window_refs):
                window = reference()
                if window is not None and window.screen() == removed:
                    self.moveWindow(window, primary_index)
        self.changed.emit()
