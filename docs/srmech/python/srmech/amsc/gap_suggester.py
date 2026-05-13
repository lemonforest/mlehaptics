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

from .descriptor import (
    Descriptor,
    discover_descriptors,
)


# ──────────────────────────────────────────────────────────────────────
# Cross-package classifier / probes registration
# ──────────────────────────────────────────────────────────────────────
#
# The classifier (``classify_dynamical_regime``) and probe roster
# (``REGIME_PROBES``) are ephemerides-specific data sources living in
# ``ephemerides_spectral._research.dynamical_regime_catalog`` and
# ``ephemerides_spectral._research.dynamical_regime_probes_data``.
# Pre-refactor these were lazy-imported via the AMSC framework's
# in-package relative-import (``from .dynamical_regime_catalog import
# classify_dynamical_regime``) because the framework itself lived
# inside ephemerides's ``_research/`` namespace.
#
# After the AMSC-to-srmech refactor (Task #197 Phase 3) the framework
# lives at ``srmech.amsc.*`` and no longer has access to ephemerides's
# private ``_research/`` modules via relative import. Downstream
# consumers PUSH the modules at package-import time via
# :func:`register_classifier` / :func:`register_probes`. The
# suggester resolves them at call time, raising a clear runtime error
# if no consumer has registered.
#
# Discipline mirrors :func:`srmech.amsc.catalog.register_attested_root`:
# push-only, idempotent re-registration, fail-clearly with an
# actionable error message when missing.


_registered_classifier: Optional[Any] = None
"""The registered classifier module. Set via :func:`register_classifier`.

The module is expected to expose a top-level
``classify_dynamical_regime(feature_vector, *, ood_threshold)``
function returning a dict shaped like::

    {"nearest_regime": {"regime_label": str, ...},
     "calibration_ratio": float,
     "out_of_distribution": bool,
     ...}
"""

_registered_probes: Optional[Any] = None
"""The registered probes module. Set via :func:`register_probes`.

The module is expected to expose a top-level ``REGIME_PROBES``
iterable of probe objects. Each probe has ``.name`` (str),
``.expected_regime`` (str | None), ``.ood_expected`` (bool), and
``.feature_vector()`` (callable returning the feature vector for
the classifier).
"""


def register_classifier(classifier_module: Any) -> Dict[str, Any]:
    """Register the classifier module used by :func:`suggest_gap_collections`.

    Downstream packages whose ``classify_dynamical_regime`` symbol
    lives outside ``srmech.amsc`` call this at package-import time so
    the suggester can resolve the classifier without a relative
    import.

    Parameters
    ----------
    classifier_module
        A module (or module-like object) exposing the top-level
        callable ``classify_dynamical_regime(feature_vector, *,
        ood_threshold)``.

    Returns
    -------
    dict
        ``{"ok": True, "module": repr(classifier_module)}`` for
        confirmation. Idempotent: re-registering is a no-op.

    Notes
    -----
    Conflict policy: re-registration silently replaces the previous
    registration. The suggester is a single-classifier consumer and
    the last-registered module wins, mirroring the consumer-bootstrap
    convention.
    """
    global _registered_classifier
    _registered_classifier = classifier_module
    return {"ok": True, "module": repr(classifier_module)}


def register_probes(probes_module: Any) -> Dict[str, Any]:
    """Register the probes module used by :func:`suggest_gap_collections`.

    Downstream packages whose ``REGIME_PROBES`` roster lives outside
    ``srmech.amsc`` call this at package-import time.

    Parameters
    ----------
    probes_module
        A module (or module-like object) exposing the top-level
        iterable ``REGIME_PROBES``.

    Returns
    -------
    dict
        ``{"ok": True, "module": repr(probes_module)}`` for
        confirmation. Idempotent: re-registering is a no-op.
    """
    global _registered_probes
    _registered_probes = probes_module
    return {"ok": True, "module": repr(probes_module)}


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
    # Resolve classifier + probes from the cross-package registry.
    # Downstream consumers (e.g. ephemerides-spectral) call
    # :func:`register_classifier` / :func:`register_probes` at
    # package-import time; we read from the registry at call time so
    # registration order doesn't depend on import order.
    if _registered_classifier is None:
        raise RuntimeError(
            "srmech.amsc.gap_suggester: no classifier registered. "
            "Call srmech.amsc.gap_suggester.register_classifier("
            "<module exposing classify_dynamical_regime>) first. "
            "Downstream consumers normally register at package-"
            "import time; this error indicates the consumer's "
            "bootstrap did not run."
        )
    if _registered_probes is None:
        raise RuntimeError(
            "srmech.amsc.gap_suggester: no probes registered. "
            "Call srmech.amsc.gap_suggester.register_probes("
            "<module exposing REGIME_PROBES>) first. Downstream "
            "consumers normally register at package-import time; "
            "this error indicates the consumer's bootstrap did "
            "not run."
        )
    classify_dynamical_regime = _registered_classifier.classify_dynamical_regime
    REGIME_PROBES = _registered_probes.REGIME_PROBES

    if descriptors is None:
        # Cross-package descriptor discovery: prefer the unified
        # :func:`_descriptors` from catalog (which walks srmech's
        # own root + every externally-registered root) so the
        # suggester sees descriptors from all consumers, not just
        # srmech's own subtree.
        from .catalog import _descriptors as _all_descriptors
        descriptors = _all_descriptors()

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
    "register_classifier",
    "register_probes",
    "suggest_gap_collections",
]
