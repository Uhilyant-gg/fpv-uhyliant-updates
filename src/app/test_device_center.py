import unittest

from device_center import device_center_fields


class DeviceCenterTests(unittest.TestCase):
    def test_categories_are_grouped_without_collapsing_physical_types(self):
        camera = device_center_fields({"type": "OpenIPC"})
        flight_controller = device_center_fields({"type": "Flight Controller"})
        controller = device_center_fields({"type": "Operator Controller"})

        self.assertEqual(camera["deviceGroupLabel"], "Камери")
        self.assertEqual(flight_controller["deviceGroupLabel"], "Польотні контролери")
        self.assertEqual(controller["deviceGroupLabel"], "Контролери")

    def test_unobserved_fields_remain_explicitly_unknown(self):
        fields = device_center_fields({"type": "OpenIPC"})

        self.assertEqual(fields["health"], "unknown")
        self.assertEqual(fields["versionLabel"], "Не спостерігалася")
        self.assertEqual(fields["lastObservedAt"], 0)

    def test_firmware_is_shown_only_for_verified_identity(self):
        fields = device_center_fields({
            "type": "OpenIPC",
            "openipcIdentity": {"verified": True, "firmware": "release-1"},
        })

        self.assertEqual(fields["versionLabel"], "release-1")


if __name__ == "__main__":
    unittest.main()
