"""Repository-software progress summary for E3 without claiming physical evidence."""
from __future__ import annotations
from typing import Mapping

REQUIRED_E3_COMPONENTS = frozenset({"selector", "runtime-integration", "presentation", "dispatch", "observability", "snapshot"})


def e3_progress(components: Mapping[str, bool] | None) -> dict[str, object]:
    values = components if isinstance(components, Mapping) else {}
    complete = sorted(name for name in REQUIRED_E3_COMPONENTS if values.get(name) is True)
    missing = sorted(REQUIRED_E3_COMPONENTS.difference(complete))
    return {
        "complete": not missing,
        "completedComponents": complete,
        "missingComponents": missing,
        "physicalEvidenceClaimed": False,
    }
