import unittest

from unified_health import (
    HEALTH_ATTENTION,
    HEALTH_PROBLEM,
    HEALTH_READY,
    HEALTH_UNKNOWN,
    SAFE_ACTION_VALUES,
    aggregate_health,
    health_evidence,
    unknown_health,
)


class UnifiedHealthTests(unittest.TestCase):
    def item(self, health):
        return health_evidence(
            state="observed",
            health=health,
            summary=f"Health is {health}.",
            reason_code=f"observed-{health}",
            evidence={"observed": True},
        )

    def test_contract_contains_canonical_fields(self):
        item = health_evidence(
            state="connected",
            health=HEALTH_READY,
            summary="Camera is ready.",
            reason_code="camera-ready",
            evidence={"verified": True},
            safe_actions=("show-video",),
        )
        self.assertEqual(
            set(item.as_dict()),
            {"state", "health", "summary", "reasonCode", "evidence", "safeActions"},
        )
        self.assertEqual(item.as_dict()["safeActions"], ["show-video"])

    def test_health_vocabulary_is_closed(self):
        with self.assertRaisesRegex(ValueError, "invalid-health"):
            self.item("reconnecting")

    def test_unknown_factory_never_claims_ready(self):
        item = unknown_health(evidence={"connected": None})
        self.assertEqual(item.health, HEALTH_UNKNOWN)
        self.assertNotEqual(item.health, HEALTH_READY)

    def test_empty_aggregate_is_unknown(self):
        self.assertEqual(aggregate_health([]).health, HEALTH_UNKNOWN)

    def test_unknown_prevents_aggregate_ready(self):
        result = aggregate_health([self.item(HEALTH_READY), self.item(HEALTH_UNKNOWN)])
        self.assertEqual(result.health, HEALTH_UNKNOWN)

    def test_problem_dominates_unknown(self):
        result = aggregate_health([self.item(HEALTH_UNKNOWN), self.item(HEALTH_PROBLEM)])
        self.assertEqual(result.health, HEALTH_PROBLEM)

    def test_attention_prevents_ready(self):
        result = aggregate_health([self.item(HEALTH_READY), self.item(HEALTH_ATTENTION)])
        self.assertEqual(result.health, HEALTH_ATTENTION)

    def test_ready_requires_all_components_ready(self):
        result = aggregate_health([self.item(HEALTH_READY), self.item(HEALTH_READY)])
        self.assertEqual(result.health, HEALTH_READY)
        self.assertEqual(result.reasonCode, "all-components-ready")

    def test_safe_actions_are_explicit_not_inferred(self):
        item = self.item(HEALTH_PROBLEM)
        self.assertEqual(item.safeActions, ())

    def test_normal_camera_connection_action_is_canonical(self):
        self.assertIn("connect-camera", SAFE_ACTION_VALUES)
        item = health_evidence(
            state="disconnected",
            health=HEALTH_ATTENTION,
            summary="Verified camera needs connection.",
            reason_code="camera-connection-needed",
            safe_actions=("connect-camera",),
        )
        self.assertEqual(item.safeActions, ("connect-camera",))

    def test_safe_action_vocabulary_is_closed(self):
        self.assertIn("diagnose", SAFE_ACTION_VALUES)
        with self.assertRaisesRegex(ValueError, "safe-action-not-allowed"):
            health_evidence(
                state="fault",
                health=HEALTH_PROBLEM,
                summary="Problem.",
                reason_code="problem",
                safe_actions=("flash-firmware",),
            )

    def test_duplicate_safe_actions_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "safe-actions-duplicate"):
            unknown_health(safe_actions=("diagnose", "diagnose"))


if __name__ == "__main__":
    unittest.main()
