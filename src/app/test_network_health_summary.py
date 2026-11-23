import unittest
from network_health_summary import network_health_summary

class NetworkHealthSummaryTests(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(network_health_summary(None)["health"], "unknown")

    def test_existing_non_mutating_action_is_preserved(self):
        result = network_health_summary({"state":"attention","problem":"Нестабільна мережа","action":"rediscover"})
        self.assertEqual(result["safeAction"], "rediscover")
        self.assertEqual(result["health"], "attention")

    def test_unmapped_state_fails_closed(self):
        self.assertEqual(network_health_summary({"state":"future"})["health"], "unknown")

if __name__ == "__main__": unittest.main()
