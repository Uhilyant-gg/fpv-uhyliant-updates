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
    windowReturnedToWorkspace = Signal(QObject)

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
        reference = next(
            (ref for ref, _screen in self._window_refs if ref() is window),
            None,
        )
        if reference is None:
            reference = weakref.ref(window)
            window.screenChanged.connect(
                lambda _screen, tracked=reference: self._remember_window_screen(tracked)
            )
        self._remember_window_screen(reference)
        return True

    def _remember_window_screen(self, reference):
        window = reference()
        if window is None:
            self._window_refs = [
                (ref, screen)
                for ref, screen in self._window_refs
                if ref() is not None
            ]
            return
        screen = window.screen()
        self._window_refs = [
            (ref, tracked_screen)
            for ref, tracked_screen in self._window_refs
            if ref() is not None and ref() is not window
        ]
        self._window_refs.append((reference, screen))

    def _screen_changed(self, _screen):
        self.changed.emit()

    def _screen_removed(self, removed):
        remaining = []
        for reference, screen in self._window_refs:
            window = reference()
            if window is None:
                continue
            if screen == removed:
                self.windowReturnedToWorkspace.emit(window)
            else:
                remaining.append((reference, screen))
        self._window_refs = remaining
        self.changed.emit()
