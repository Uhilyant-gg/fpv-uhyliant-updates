import unittest
from telemetry_health_summary import telemetry_health_summary


class TelemetryHealthSummaryTests(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(telemetry_health_summary(None)["health"], "unknown")

    def test_true_connection_is_ready(self):
        result = telemetry_health_summary({"connected": True, "provider": "MAVLink"})
        self.assertEqual(result["health"], "ready")
        self.assertEqual(result["provider"], "MAVLink")

    def test_false_is_attention_and_none_is_unknown(self):
        self.assertEqual(telemetry_health_summary({"connected": False})["health"], "attention")
        self.assertEqual(telemetry_health_summary({"connected": None})["health"], "unknown")


if __name__ == "__main__":
    unittest.main()
