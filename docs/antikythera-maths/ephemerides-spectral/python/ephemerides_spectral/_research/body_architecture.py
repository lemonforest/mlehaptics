"""Body architecture — inner/outer classification of heliocentric bodies
from the resonance-weighted gateway-graph Laplacian Fiedler partition.

This is the ship version of the §13.8 research finding. The research
prototype (`research/gateway_graph_laplacian.py`) compared four edge
weightings on the gateway-graph Laplacian and found that **only the
resonance-weighted Laplacian** produces a Fiedler partition that
cleanly bipartitions the heliocentric body roster on the asteroid-belt
boundary — outer 5 (jupiter / saturn / uranus / neptune / pluto)
negative; inner 8 (mercury / venus / terra / mars / vesta / ceres /
pallas / hygiea) positive. The cyclic-group encoder discovers the
canonical inner/outer system division without being told it exists.

This module exposes that classification as a stable, deterministic,
pure-Python query. The result is a function of:

* the heliocentric body subset (parameter ``bodies`` defaults to the
  v0.16.0 13-body Tier-1 heliocentric roster)
* the resonance-weighting hyperparameters (constants below; chosen in
  §13.8 and held stable as part of the v0.18.0 ship contract)

Algorithm
---------

1. For each unordered pair (i, j) of bodies, compute the period ratio
   ``r = min(P_i, P_j) / max(P_i, P_j) ∈ (0, 1]`` and the best small-
   integer rational ``(p, q)`` approximation via
   :func:`_best_rational_approx` (the same v0.17.0 primitive used
   for ITN-chain resonance signatures).
2. Form the symmetric edge weight
   ``w_ij = exp(-|r - p/q| / RESIDUAL_SCALE) / (p + q)``. Strong
   low-order locks (Jupiter-Saturn 2:5, Neptune-Pluto 2:3,
   Ceres-Pallas 1:1) score high; spurious near-rationals are
   suppressed by the residual term.
3. Build the combinatorial Laplacian ``L = D - W`` where
   ``D = diag(W.sum(axis=1))``. Compute eigendecomposition. The
   Fiedler eigenvector is the eigenvector of the second-smallest
   eigenvalue λ₂ (the algebraic connectivity).
4. Classify each body by the sign of its Fiedler-vector entry:
   negative → "outer", positive → "inner".

Stability
---------

The classification is deterministic given the input ``bodies`` list and
the constants below. The numpy ``eigh`` symmetric eigensolver is used
(reproducible across platforms). A sign-convention is applied to the
Fiedler vector — the body with the largest absolute entry is forced
positive — so the inner/outer label assignment is also reproducible
(without this, eigh's sign is platform-dependent).

References
----------

* Notebook §13.8 — the resonance-weighted research result.
* Notebook §13.9 — the hybrid `inv_dv × resonance` follow-up which
  motivated the ship of *this* surface specifically (the resonance-
  only partition is the architectural finding; the hybrid is the
  deferred Δv predictor).
* :func:`_best_rational_approx` — the v0.17.0 ITN-chain primitive.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from .bodies import BODIES
from .itn_window import _best_rational_approx
from . import navigation_ops as _nav


# ---- Default heliocentric subset (v0.16.0 Tier-1 expansion). ---------
# Sun excluded: it is the central potential, not a transit node.
# Moons excluded: their parent-frame Δv is not yet modelled in
# v0.17.0 / v0.18.0 (would require CR3BP-aware extension).
HELIOCENTRIC_BODIES: List[str] = [
    "mercury", "venus", "terra", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
    "ceres", "vesta", "pallas", "hygiea",
]

# ---- Resonance-weighting hyperparameters (held stable for ship). -----
# RESONANCE_MAX_INT matches v0.17.0 _best_rational_approx default.
# RESONANCE_RESIDUAL_SCALE = 0.5% chosen empirically in §13.8: well-
# locked resonances (Earth-Mars 0.24% residual ⇒ exp(-0.48) ≈ 0.62
# kept) score high; Diophantine-luck near-rationals (Saturn-Uranus
# 1.3% residual ⇒ exp(-2.6) ≈ 0.07 suppressed) score low.
RESONANCE_MAX_INT: int = 30
RESONANCE_RESIDUAL_SCALE: float = 5.0e-3

# Class labels.
INNER_CLASS: str = "inner"
OUTER_CLASS: str = "outer"


def _resonance_weight(p_i: float, p_j: float) -> float:
    """Resonance-strength edge weight between two bodies.

    Returns ``exp(-residual / RESONANCE_RESIDUAL_SCALE) / (p + q)``
    where ``(p, q)`` is the best small-integer rational approximation
    of ``min(p_i, p_j) / max(p_i, p_j)`` via
    :func:`_best_rational_approx` (max_int=RESONANCE_MAX_INT, matching
    the v0.17.0 ITN-chain resonance signature convention).
    """
    if p_i <= 0.0 or p_j <= 0.0:
        return 0.0
    ratio = min(p_i, p_j) / max(p_i, p_j)
    p, q = _best_rational_approx(ratio, max_int=RESONANCE_MAX_INT)
    if (p, q) == (0, 0):
        return 0.0
    residual = abs(ratio - p / q)
    return math.exp(-residual / RESONANCE_RESIDUAL_SCALE) / float(p + q)


def _build_resonance_laplacian(bodies: List[str]):
    """Build the combinatorial Laplacian L = D - W on ``bodies`` via the
    shared Class-L navigation cascade (:mod:`navigation_ops`,
    numpy-free). Returns an :class:`srmech.amsc.mat.Mat`."""
    n = len(bodies)
    periods = [BODIES[name].period_days for name in bodies]
    edges, weights = _nav.symmetric_pairs_to_edges(
        n, lambda i, j: _resonance_weight(periods[i], periods[j])
    )
    return _nav.adjacency_to_laplacian(n, edges, weights)


def _fiedler_with_sign_convention(
    L,
    bodies: List[str],
) -> Tuple[float, List[float]]:
    """Return (λ₂, Fiedler eigenvector) with deterministic sign.

    Routes through the shared Class-L eigendecompose + Class-C frame in
    :func:`navigation_ops.fiedler_partition` (the srmech Jacobi solver,
    bit-identical to LAPACK ``eigh`` on these small resonance Laplacians;
    numpy-free). The physics-anchored convention forces the body with
    the *shortest sidereal period* to a positive Fiedler entry, so the
    canonical inner/outer label assignment (mercury deep-positive ⇒
    inner; pluto deep-negative ⇒ outer) is reproducible across
    platforms. ``f`` is a plain ``list[float]``.
    """
    periods = [BODIES[name].period_days for name in bodies]
    pivot = periods.index(min(periods))
    return _nav.fiedler_partition(L, pivot)


def compute_body_architecture(
    bodies: Optional[List[str]] = None,
) -> Dict[str, object]:
    """Compute the body-architecture classification.

    Parameters
    ----------
    bodies : list of body names, optional. Default: the 13-body
        heliocentric Tier-1 roster (planets + main-belt asteroids).
        Names must be keys in :data:`BODIES` and must satisfy
        ``period_days > 0`` (i.e. cannot include the Sun, which has
        period 0).

    Returns
    -------
    dict with keys:

    * ``ok`` (bool)
    * ``n_bodies`` (int)
    * ``lambda_2`` (float) — algebraic connectivity of the resonance-
      weighted gateway-graph Laplacian.
    * ``bodies`` (list[dict]) — per-body record with ``name``,
      ``class`` (``"inner"`` or ``"outer"``), ``fiedler_value``
      (float), ``period_days`` (float). Sorted by ``fiedler_value``
      ascending so the deepest-outer body appears first.
    * ``partitions`` (dict) — ``{"inner": [...], "outer": [...]}``
      with body names in each class.

    The convention is "negative Fiedler entry ⇒ outer; positive
    Fiedler entry ⇒ inner" — chosen so that for the default 13-body
    roster the canonical outer-system bodies (jupiter / saturn /
    uranus / neptune / pluto) land in the ``"outer"`` partition.

    Raises
    ------
    ValueError if ``bodies`` is empty, contains duplicates, contains a
        name not in :data:`BODIES`, contains a body with non-positive
        ``period_days``, or has fewer than 2 entries (Laplacian
        eigendecomposition needs ≥ 2 nodes for λ₂ to exist).
    """
    if bodies is None:
        bodies = list(HELIOCENTRIC_BODIES)
    else:
        bodies = list(bodies)

    if len(bodies) < 2:
        raise ValueError(
            f"compute_body_architecture needs ≥ 2 bodies, got {len(bodies)}"
        )
    if len(set(bodies)) != len(bodies):
        raise ValueError(
            f"compute_body_architecture: duplicate bodies in {bodies}"
        )
    for name in bodies:
        if name not in BODIES:
            raise ValueError(
                f"compute_body_architecture: unknown body {name!r}"
            )
        if BODIES[name].period_days <= 0.0:
            raise ValueError(
                f"compute_body_architecture: body {name!r} has non-"
                f"positive period_days {BODIES[name].period_days}"
            )

    L = _build_resonance_laplacian(bodies)
    lam2, fiedler = _fiedler_with_sign_convention(L, bodies)

    # The sign convention forces the shortest-period body to be
    # positive. Positive partition = "inner"; negative = "outer".
    body_records = []
    for i, name in enumerate(bodies):
        f_val = float(fiedler[i])
        cls = INNER_CLASS if f_val >= 0.0 else OUTER_CLASS
        body_records.append({
            "name": name,
            "class": cls,
            "fiedler_value": f_val,
            "period_days": float(BODIES[name].period_days),
        })
    body_records.sort(key=lambda r: r["fiedler_value"])

    inner = [r["name"] for r in body_records if r["class"] == INNER_CLASS]
    outer = [r["name"] for r in body_records if r["class"] == OUTER_CLASS]

    return {
        "ok": True,
        "n_bodies": len(bodies),
        "lambda_2": lam2,
        "bodies": body_records,
        "partitions": {INNER_CLASS: inner, OUTER_CLASS: outer},
    }


__all__ = [
    "HELIOCENTRIC_BODIES",
    "INNER_CLASS",
    "OUTER_CLASS",
    "compute_body_architecture",
]
