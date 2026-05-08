"""Schema-gap-driven trigger — the system identifies what it doesn't
know and points at attested sources that could populate the gap.

Closes the Mathematical Provenance Method loop established by the
v0.24.x → v0.25.x ship sequence:

* v0.24.9 dynamical-regime classifier projects ground-proof rows
  through a closed-form eigenbasis.
* v0.24.10 OOS probe roster + calibration-ratio metric flag bodies
  whose physics doesn't match any existing ground-proof row.
* v0.24.11 / v0.24.12 demonstrated the manual loop: a probe's gap
  surfaces → a new ground-proof row populates the regime → the
  eigenbasis recomputes byte-identically.
* v0.25.x ships shipped the attested-collector framework with
  ``[gap_targeting]`` declarations on every descriptor.
* **v0.26.0 (this module)** closes the loop: read the OOS probe
  results, identify gaps (high calibration ratio, spurious match,
  surprise landing), match each gap against the descriptor
  registry via ``[gap_targeting].regime_labels``, and emit a
  suggestion list.

The suggester is **deterministic and closed-form**. No LLM, no
SGD, no random init. Same Mathematical Provenance Method
discipline as every other v0.24.x / v0.25.x surface — every
suggestion has citable provenance: probe name + classifier
output + descriptor key + matching regime labels.

The CI automation that consumes the suggestion surface and opens
auto-PRs for targeted T1 collection is left for a future ship.
v0.26.0 ships the analysis half; the trigger half lands when a
maintainer-review-grade auto-PR mechanism is wired up.

Reference: notebook §18.5 (T1 re-bake triggers; option 3 — the
schema-gap-driven trigger).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .attested_collector_descriptor import (
    Descriptor,
    discover_descriptors,
)


# ──────────────────────────────────────────────────────────────────────
# Gap kinds
# ──────────────────────────────────────────────────────────────────────


GAP_KIND_OOD: str = "ood"
"""Probe's calibration ratio exceeds the OOD threshold — no close
neighbour exists in the ground-proof eigenbasis."""

GAP_KIND_SPURIOUS: str = "spurious_match"
"""Probe's expected regime label disagrees with the classifier's
nearest regime — the eigenbasis is matching the wrong physics."""

GAP_KIND_SURPRISE: str = "surprise"
"""Probe was declared `expected_regime=None, ood_expected=False`
(a "let classifier surprise us" probe). Suggester flags whichever
regime label the classifier emitted so descriptors targeting that
label can be considered for densification."""

GAP_KIND_NONE: str = "none"
"""Probe matches expectation and isn't a surprise; no gap."""


# ──────────────────────────────────────────────────────────────────────
# Suggester
# ──────────────────────────────────────────────────────────────────────


def suggest_gap_collections(
    *,
    ood_threshold: float = 0.85,
    descriptors: Optional[Dict[str, Descriptor]] = None,
) -> Dict[str, Any]:
    """Identify regime gaps from OOS probes and match each gap
    against attested-source descriptors via ``[gap_targeting]``.

    Parameters
    ----------
    ood_threshold
        Calibration-ratio threshold above which a probe is
        considered OOD (no close neighbour). Mirrors the threshold
        used by ``classify_dynamical_regime`` itself; default
        ``0.85`` is the project-wide convention.
    descriptors
        Optional descriptor map (for testing). When None, walks
        the attested-tree root for the current install.

    Returns
    -------
    dict
        ``{ok, n_probes, n_gaps, n_suggestions, suggestions: [...]}``
        where each suggestion is::

            {
                "probe_name": "...",
                "calibration_ratio": float,
                "current_landing": "regime_label",
                "expected_regime": "regime_label" | None,
                "gap_kind": GAP_KIND_*,
                "candidate_descriptors": [
                    {"source_key": "...",
                     "matching_regime_labels": ["..."],
                     "human_readable_name": "..."},
                    ...
                ],
            }

        The classifier is the v0.24.9 eigenbasis; probes are the
        v0.24.10 OOS roster. A gap with zero candidate descriptors
        signals "framework knows there's a gap but no source yet
        targets that regime" — a future-source backlog hint.
    """
    # Lazy imports to keep this module isolatable for unit tests.
    from .dynamical_regime_catalog import classify_dynamical_regime
    from .dynamical_regime_probes_data import REGIME_PROBES

    if descriptors is None:
        from .attested_collector_catalog import _attested_root
        descriptors = discover_descriptors(_attested_root())

    descriptor_index = _build_descriptor_index(descriptors)

    suggestions: List[Dict[str, Any]] = []
    n_probes = 0
    n_gaps = 0

    for probe in REGIME_PROBES:
        n_probes += 1
        result = classify_dynamical_regime(
            probe.feature_vector(), ood_threshold=ood_threshold
        )
        nearest_label = result["nearest_regime"]["regime_label"]
        cal_ratio = float(result["calibration_ratio"])
        is_ood = bool(result.get("out_of_distribution", False))

        gap_kind = _classify_gap(probe, nearest_label, is_ood)
        if gap_kind == GAP_KIND_NONE:
            continue

        n_gaps += 1
        # For OOD gaps: target the EXPECTED regime (or absent → no target).
        # For spurious matches: target the EXPECTED regime (the classifier's
        #   nearest is wrong; we want to densify the right regime).
        # For surprise probes: target the CURRENT landing (the classifier
        #   put it there; if a descriptor already covers that regime, more
        #   ground-proof rows would let the eigenbasis distinguish better).
        target_label: Optional[str]
        if gap_kind == GAP_KIND_SURPRISE:
            target_label = nearest_label
        else:
            target_label = probe.expected_regime

        candidates = (
            descriptor_index.get(target_label, []) if target_label else []
        )

        suggestions.append({
            "probe_name": probe.name,
            "calibration_ratio": cal_ratio,
            "current_landing": nearest_label,
            "expected_regime": probe.expected_regime,
            "gap_kind": gap_kind,
            "target_regime_label": target_label,
            "candidate_descriptors": candidates,
        })

    return {
        "ok": True,
        "ood_threshold": ood_threshold,
        "n_probes": n_probes,
        "n_gaps": n_gaps,
        "n_suggestions": len(suggestions),
        "suggestions": suggestions,
    }


def _classify_gap(
    probe: Any, nearest_label: str, is_ood: bool
) -> str:
    """Determine which kind of gap (if any) this probe surfaces."""
    if probe.expected_regime is not None:
        if nearest_label != probe.expected_regime:
            return GAP_KIND_SPURIOUS
        return GAP_KIND_NONE
    # No expected_regime — either OOD-expected or surprise.
    if probe.ood_expected:
        # OOD-expected probe: gap is "framework correctly says I
        # don't know" — surface it for descriptor matching against
        # a future expected_regime, but at this stage we just flag.
        return GAP_KIND_OOD if is_ood else GAP_KIND_SPURIOUS
    # Surprise probe: classifier landed it somewhere; flag for
    # densification of that landing.
    return GAP_KIND_SURPRISE


def _build_descriptor_index(
    descriptors: Dict[str, Descriptor],
) -> Dict[str, List[Dict[str, Any]]]:
    """Build a `regime_label -> [descriptor metadata]` index for
    fast lookup. Each descriptor's `[gap_targeting].regime_labels`
    entries register it under those labels."""
    index: Dict[str, List[Dict[str, Any]]] = {}
    for source_key, descriptor in sorted(descriptors.items()):
        labels: List[str] = list(
            descriptor.gap_targeting.get("regime_labels", [])
        )
        if not labels:
            continue
        for label in labels:
            entry = {
                "source_key": source_key,
                "matching_regime_labels": labels,
                "human_readable_name": str(
                    descriptor.source.get("human_readable_name", source_key)
                ),
            }
            index.setdefault(label, []).append(entry)
    return index


__all__ = [
    "GAP_KIND_OOD",
    "GAP_KIND_SPURIOUS",
    "GAP_KIND_SURPRISE",
    "GAP_KIND_NONE",
    "suggest_gap_collections",
]
