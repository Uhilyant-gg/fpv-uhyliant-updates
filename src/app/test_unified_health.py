import unittest

from unified_health import (
    HEALTH_ATTENTION,
    HEALTH_PROBLEM,
    HEALTH_READY,
    HEALTH_UNKNOWN,
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


if __name__ == "__main__":
    unittest.main()
