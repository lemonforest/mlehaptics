"""Eclipse-anchor accessor facade.

Six well-attested Almagest IV-VI Hellenistic anchors (-382 .. +125 CE)
plus a handful of modern Saros controls. Each anchor carries the
Julian Day in TDB, eclipse type, historical citation, and an
``interpretation_confidence`` tag.

Re-exported from ``_research.hellenistic_eclipses``.
"""

from __future__ import annotations

from antikythera_spectral._research.hellenistic_eclipses import (
    EclipseAnchor,
    HELLENISTIC_ANCHORS,
    MODERN_SAROS_ANCHORS,
    anchors_for_era,
    anchors_in_jd_range,
    filter_by_confidence,
)

__all__ = [
    "EclipseAnchor",
    "HELLENISTIC_ANCHORS",
    "MODERN_SAROS_ANCHORS",
    "anchors_for_era",
    "anchors_in_jd_range",
    "filter_by_confidence",
]
