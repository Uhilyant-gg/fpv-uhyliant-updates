#!/usr/bin/env python3
"""Deterministic E7 scenario CI runner over the side-effect-free E6 simulator."""

from __future__ import annotations

import json

from hardware_simulator import VirtualDeviceState
from hardware_simulator_scenarios import replay


SCENARIOS = (
    ("healthy-revalidation", VirtualDeviceState("camera-1"), ({"type": "verify-identity", "verified": True},), "ready"),
    (
        "reconnect-revalidation",
        VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True),
        ({"type": "disconnect"}, {"type": "reconnect"}, {"type": "verify-identity", "verified": True}),
        "ready",
    ),
    ("update-failure", VirtualDeviceState("camera-1"), ({"type": "start-update"}, {"type": "fail-update"}), "problem"),
    (
        "identity-mismatch",
        VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True),
        ({"type": "identity-mismatch"},),
        "problem",
    ),
)


def run_scenarios() -> dict:
    results = []
    for name, initial, events, expected in SCENARIOS:
        result = replay(initial, events)
        boundary_ok = result.get("evidenceKind") == "simulation" and result.get("physicalEvidenceComplete") is False
        passed = result.get("status") == expected and boundary_ok
        results.append(
            {
                "name": name,
                "expectedStatus": expected,
                "actualStatus": result.get("status"),
                "reasonCode": result.get("reasonCode"),
                "passed": passed,
            }
        )
    return {
        "schemaVersion": 1,
        "status": "passed" if all(item["passed"] for item in results) else "failed",
        "evidenceKind": "simulation",
        "physicalEvidenceComplete": False,
        "scenarios": results,
    }


def main() -> int:
    report = run_scenarios()
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
