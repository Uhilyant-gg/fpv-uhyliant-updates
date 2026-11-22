#!/usr/bin/env python3
"""Load and validate FPV Uhyliant machine-readable canonical project state."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "PROJECT_STATE.json"
ALLOWED_CAPABILITY_STATUS = {"pending", "partial", "ready", "complete", "deferred", "blocked"}


def load_project_state(path=STATE_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    if data.get("schemaVersion") != 1:
        errors.append("schema-version")
    if data.get("project") != "FPV Uhyliant":
        errors.append("project-name")
    estimate = data.get("planningEstimatePercent")
    if not isinstance(estimate, int) or not 0 <= estimate <= 100:
        errors.append("planning-estimate")
    hardware = data.get("hardwareValidation", {})
    if hardware.get("status") == "DEFERRED" and hardware.get("physicalEvidenceComplete") is not False:
        errors.append("deferred-hardware-evidence")
    capabilities = data.get("capabilities", {})
    if not isinstance(capabilities, dict) or not capabilities:
        errors.append("capabilities")
    else:
        for name, status in sorted(capabilities.items()):
            if status not in ALLOWED_CAPABILITY_STATUS:
                errors.append("capability-status:" + name)
    software = data.get("softwareTrack", {})
    if software.get("status") not in {"READY", "BLOCKED"}:
        errors.append("software-track-status")
    if errors:
        raise ValueError(",".join(errors))
    return data
