"""Station-level unified health assembled only from observed component evidence."""
from typing import Iterable

from unified_health import HealthEvidence, aggregate_health, health_evidence


def station_health(components: Iterable[HealthEvidence]) -> HealthEvidence:
    """Return one conservative station presentation state.

    Component evidence remains authoritative. The station is ready only when every
    supplied component is ready; unknown evidence therefore remains unknown.
    Safe actions are intentionally not inferred at this aggregation boundary.
    """
    components = tuple(components)
    combined = aggregate_health(
        components,
        state="station",
        summary="Combined station health is derived from observed component evidence.",
    )
    return health_evidence(
        state=combined.state,
        health=combined.health,
        summary=combined.summary,
        reason_code=combined.reasonCode,
        evidence={"components": [item.as_dict() for item in components]},
    )
