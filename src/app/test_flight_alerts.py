import unittest

from flight_alerts import DEFAULT_THRESHOLDS, evaluate_alerts, validate_threshold, validate_thresholds


def codes(alerts):
    return [a["code"] for a in alerts]


class EvaluateTests(unittest.TestCase):
    def test_healthy_flight_has_no_alerts(self):
        telemetry = {"connected": True, "linkQuality": 99, "batteryRemaining": 80, "batteryVoltage": 16.4}
        self.assertEqual(evaluate_alerts(telemetry, {"cellCount": 4}), [])

    def test_low_values_raise_alerts_most_severe_first(self):
        telemetry = {"connected": True, "linkQuality": 40, "batteryRemaining": 10, "batteryVoltage": 13.6}
        alerts = evaluate_alerts(telemetry, {"cellCount": 4})
        self.assertEqual(codes(alerts), ["link-quality-low", "cell-voltage-low", "battery-remaining-low"])
        self.assertEqual([a["level"] for a in alerts], ["critical", "critical", "warning"])
        self.assertIn("3.40 В на банку", alerts[1]["text"])

    def test_cell_voltage_needs_operator_cell_count(self):
        telemetry = {"connected": True, "batteryVoltage": 10.0}
        self.assertEqual(evaluate_alerts(telemetry, {}), [])
        self.assertEqual(codes(evaluate_alerts(telemetry, {"cellCount": 4})), ["cell-voltage-low"])

    def test_stale_or_unknown_values_never_alert(self):
        telemetry = {
            "connected": True,
            "linkQuality": 10,
            "batteryRemaining": None,
            "freshness": {"linkQuality": False},
        }
        self.assertEqual(evaluate_alerts(telemetry, None), [])
        self.assertEqual(evaluate_alerts({"connected": None, "linkQuality": 10}, None), [])
        self.assertEqual(evaluate_alerts(None, None), [])

    def test_lost_telemetry_is_critical(self):
        self.assertEqual(codes(evaluate_alerts({"connected": False, "linkQuality": 10}, None)), ["telemetry-lost"])

    def test_zero_threshold_disables_alert(self):
        telemetry = {"connected": True, "linkQuality": 10, "batteryRemaining": 5}
        self.assertEqual(evaluate_alerts(telemetry, {"linkQualityMin": 0, "batteryRemainingMin": 0}), [])


class ThresholdTests(unittest.TestCase):
    def test_validation(self):
        self.assertEqual(validate_threshold("linkQualityMin", 70), 70)
        self.assertEqual(validate_threshold("cellVoltageMin", 3.456), 3.46)
        for name, value in (
            ("linkQualityMin", 101),
            ("linkQualityMin", 50.5),
            ("cellCount", True),
            ("cellVoltageMin", float("nan")),
            ("unknown", 1),
        ):
            with self.assertRaises(ValueError, msg=(name, value)):
                validate_threshold(name, value)

    def test_stored_values_merge_over_defaults_and_invalid_fall_back(self):
        result = validate_thresholds({"linkQualityMin": 60, "cellCount": 99, "extra": 1})
        self.assertEqual(result["linkQualityMin"], 60)
        self.assertEqual(result["cellCount"], DEFAULT_THRESHOLDS["cellCount"])
        self.assertNotIn("extra", result)
        self.assertEqual(validate_thresholds("garbage"), DEFAULT_THRESHOLDS)


if __name__ == "__main__":
    unittest.main()
