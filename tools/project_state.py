#!/usr/bin/env python3
"""Load, validate and derive FPV Uhyliant machine-readable canonical project state."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "PROJECT_STATE.json"
ALLOWED_CAPABILITY_STATUS = {"pending", "partial", "ready", "complete", "deferred", "blocked"}
EXPECTED_CAPABILITIES = {
    "projectDoctor",
    "unifiedHealthEvidence",
    "nextBestAction",
    "zeroConfigStartup",
    "hardwareSimulator",
    "scenarioDrivenCI",
}
SOFTWARE_ORDER = (
    ("projectDoctor", "E5"),
    ("unifiedHealthEvidence", "E2"),
    ("nextBestAction", "E3"),
    ("zeroConfigStartup", "E4"),
    ("hardwareSimulator", "E6"),
    ("scenarioDrivenCI", "E7"),
)
TERMINAL_CAPABILITY_STATUS = {"complete"}
CAPABILITY_EPIC = {
    "projectDoctor": "E5",
    "unifiedHealthEvidence": "E2",
    "nextBestAction": "E3",
    "zeroConfigStartup": "E4",
    "hardwareSimulator": "E6",
    "scenarioDrivenCI": "E7",
}
EPIC_NAMES = {
    "E2": "Unified Health and Evidence Contract",
    "E3": "Next Best Action Engine",
    "E4": "Zero-Config Startup and Restore",
    "E5": "Project Doctor and Machine-Readable Project State",
    "E6": "Hardware Simulator and Fault Injection",
    "E7": "Scenario-Driven CI",
}


def derive_next_milestone(data):
    capabilities = data.get("capabilities", {})
    for capability, milestone in SOFTWARE_ORDER:
        if capabilities.get(capability) not in TERMINAL_CAPABILITY_STATUS:
            return milestone
    return None


def canonical_drift_errors(data, root=ROOT):
    root = Path(root)
    errors = []
    hardware = data.get("hardwareValidation", {})
    roadmap = (root / "DELIVERY_ROADMAP.md").read_text(encoding="utf-8")
    project_state_md = (root / "PROJECT_STATE.md").read_text(encoding="utf-8")

    if hardware.get("physicalEvidenceComplete") is False:
        if "E0 - Physical OpenIPC Hardware E2E | BLOCKED ON PHYSICAL EVIDENCE" not in roadmap:
            errors.append("roadmap-hardware-boundary")
        if "Complete Hardware E2E first" not in project_state_md:
            errors.append("project-state-hardware-boundary")

    derived = derive_next_milestone(data)
    recorded = data.get("softwareTrack", {}).get("nextMilestone")
    if recorded != derived:
        errors.append(f"next-milestone:{recorded}->{derived}")

    capabilities = data.get("capabilities", {})
    for capability, epic in CAPABILITY_EPIC.items():
        status = capabilities.get(capability)
        heading = f"### {epic} - {EPIC_NAMES[epic]}"
        if status == "complete":
            if heading not in roadmap or f"{heading} | COMPLETE" not in roadmap:
                errors.append(f"roadmap-{epic}-complete")
        elif heading in roadmap:
            if f"{heading} | COMPLETE" in roadmap:
                errors.append(f"roadmap-{epic}-not-complete")
    return errors


def load_project_state(path=STATE_PATH, root=None, check_drift=True):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    if data.get("schemaVersion") != 1:
        errors.append("schema-version")
    if data.get("project") != "FPV Uhyliant":
        errors.append("project-name")
    estimate = data.get("planningEstimatePercent")
    if not isinstance(estimate, int) or not 0 <= estimate <= 100:
        errors.append("planning-estimate")
    hardware = data.get("hardwareValidation", {})
    if hardware.get("epic") != "E0":
        errors.append("hardware-epic")
    if hardware.get("status") not in {"DEFERRED", "READY", "BLOCKED", "COMPLETE"}:
        errors.append("hardware-status")
    if not isinstance(hardware.get("physicalEvidenceComplete"), bool):
        errors.append("physical-evidence-type")
    if hardware.get("status") == "DEFERRED" and hardware.get("physicalEvidenceComplete") is not False:
        errors.append("deferred-hardware-evidence")
    if hardware.get("status") == "COMPLETE" and hardware.get("physicalEvidenceComplete") is not True:
        errors.append("complete-hardware-evidence")
    capabilities = data.get("capabilities", {})
    if not isinstance(capabilities, dict) or not capabilities:
        errors.append("capabilities")
    else:
        missing = EXPECTED_CAPABILITIES.difference(capabilities)
        extra = set(capabilities).difference(EXPECTED_CAPABILITIES)
        if missing:
            errors.append("capabilities-missing:" + ",".join(sorted(missing)))
        if extra:
            errors.append("capabilities-unknown:" + ",".join(sorted(extra)))
        for name, status in sorted(capabilities.items()):
            if status not in ALLOWED_CAPABILITY_STATUS:
                errors.append("capability-status:" + name)
    software = data.get("softwareTrack", {})
    if software.get("status") not in {"READY", "BLOCKED"}:
        errors.append("software-track-status")
    derived = derive_next_milestone(data)
    if software.get("nextMilestone") != derived:
        errors.append("next-milestone")
    if check_drift and not errors:
        errors.extend(canonical_drift_errors(data, root or path.parent))
    if errors:
        raise ValueError(",".join(errors))
    return data
