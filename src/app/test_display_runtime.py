import unittest
import weakref

from PySide6.QtCore import QObject

from display_runtime import DisplayRuntime, display_inventory


class Geometry:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    def width(self):
        return self._width

    def height(self):
        return self._height


class Screen:
    def __init__(self, width, height):
        self._geometry = Geometry(width, height)

    def availableGeometry(self):
        return self._geometry


class DisplayRuntimeTests(unittest.TestCase):
    def test_inventory_uses_friendly_labels_and_preserves_screen_order(self):
        self.assertEqual(
            display_inventory([Screen(1920, 1080), Screen(1280, 720)]),
            [
                {"index": 0, "label": "Екран 1 · 1920 × 1080"},
                {"index": 1, "label": "Екран 2 · 1280 × 720"},
            ],
        )

    def test_removed_display_returns_only_its_tracked_windows_to_workspace(self):
        runtime = DisplayRuntime.__new__(DisplayRuntime)
        QObject.__init__(runtime)
        removed_screen = object()
        remaining_screen = object()
        removed_window = QObject()
        remaining_window = QObject()
        runtime._window_refs = [
            (weakref.ref(removed_window), removed_screen),
            (weakref.ref(remaining_window), remaining_screen),
        ]
        returned = []
        runtime.windowReturnedToWorkspace.connect(returned.append)

        runtime._screen_removed(removed_screen)

        self.assertEqual(returned, [removed_window])
        self.assertEqual(runtime._window_refs, [(weakref.ref(remaining_window), remaining_screen)])


if __name__ == "__main__":
    unittest.main()
