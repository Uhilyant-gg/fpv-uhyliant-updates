import unittest

from display_runtime import display_inventory


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


if __name__ == "__main__":
    unittest.main()
