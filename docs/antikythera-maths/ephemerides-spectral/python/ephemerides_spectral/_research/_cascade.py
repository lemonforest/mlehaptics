"""Cascade-compute helpers — route ephemerides catalog math through
srmech's 14-class ops, not raw numpy / ``math``.

This is the ephemerides-side realisation of the srmech v0.7.0 thesis —
*every continuous-math op a cascade of the 14*. Catalog query surfaces
import these instead of calling ``math.sin`` / ``np.linalg.eigh`` /
``** (2/3)`` directly:

* **Class L** — graph-Laplacian build + eigendecomposition (the
  bounded-local-Laplacian eigenbasis) via
  :func:`srmech.amsc.laplacian.dense_laplacian` +
  :func:`symmetric_eigendecompose`.
* **Class N** — trig / pow / sqrt / asin via
  :mod:`srmech.amsc.rational` (exact-rational Taylor partials projected
  to float; ``π`` from the Archimedes hexagon-doubling cascade
  ``pi_cascade_digits``; ``exp`` argument-halved, ``sqrt`` integer-Newton).
* **Class K** — magnitude / sign re-application without ``abs()``.

Every value crosses to float only at the boundary; the transcendental
core is the srmech cascade. Numerically these agree with ``math`` /
``numpy`` to well under the catalog tolerances (verified against them).
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np

from srmech.amsc import laplacian as _lap
from srmech.amsc import rational as _rat


# ---------------------------------------------------------------------------
# π from the Archimedes hexagon-doubling cascade (Class N) — the same
# pattern srmech's own cascade modules use.
# ---------------------------------------------------------------------------


def _pi_from_cascade(digits: int = 30) -> float:
    ip, _, fp = _rat.pi_cascade_digits(digits).partition(".")
    return int(ip + fp) / (10 ** len(fp))


#: π via the Class-N geometric cascade (not ``math.pi``).
PI: float = _pi_from_cascade()


def radians(degrees: float) -> float:
    """Degrees → radians using the cascade π (Class N)."""
    return degrees * PI / 180.0


def degrees(radians_value: float) -> float:
    """Radians → degrees using the cascade π (Class N)."""
    return radians_value * 180.0 / PI


def sqrt(x: float) -> float:
    """``√x`` via the Class-N integer-Newton sqrt cascade (re-export)."""
    return _rat.sqrt(x)


def sin_deg(degrees: float, *, terms: int = 24) -> float:
    """``sin`` of an angle in degrees via the Class-N rational sine."""
    return _rat.sin(radians(degrees), terms=terms)


def cos_deg(degrees: float, *, terms: int = 24) -> float:
    """``cos`` of an angle in degrees via the Class-N rational cosine."""
    return _rat.cos(radians(degrees), terms=terms)


def pow_frac(
    x_num: int, x_den: int, p_num: int, p_den: int, *, terms: int = 48,
) -> float:
    """``(x_num/x_den) ** (p_num/p_den)`` via the Class-N exp∘log cascade.

    ``x^p = exp(p · log x)`` with ``log x = log1p(x − 1)`` from the
    exact-rational ``log1p`` partial sum and the argument-halved
    ``exp``. Requires ``0 < x < 2`` (so ``|x − 1| < 1``, the log1p
    convergence radius) — true for every interior ``(q/p)`` mean-motion
    ratio (``q < p`` ⟹ ``x − 1 ∈ (−1, 0)``).
    """
    if not (0 < x_num and 0 < x_den):
        raise ValueError("pow_frac requires x_num, x_den > 0")
    ln, ld = _rat.log1p_series_truncate(x_num - x_den, x_den, terms)
    log_x = ln / ld
    return _rat.exp((p_num / p_den) * log_x, terms=terms)


def asin(x: float, *, terms: int = 48) -> float:
    """``asin(x)`` via the Class-N atan + sqrt cascade.

    ``asin(x) = atan( x / √(1 − x²) )`` — the rational ``atan`` of the
    rational ``sqrt`` quotient. Endpoints ±1 map to ±π/2 (Class-K
    pin-slot at the domain boundary).
    """
    x = float(x)
    if x <= -1.0:
        return -PI / 2.0
    if x >= 1.0:
        return PI / 2.0
    denom = _rat.sqrt(1.0 - x * x)
    return _rat.atan(x / denom, terms=terms)


def gaussian_proximity_eigs(
    coords: Sequence[float], sigma: float, *, terms: int = 64,
) -> Tuple[np.ndarray, np.ndarray]:
    """Bounded-local-Laplacian eigenbasis on a 1-D coordinate chain
    (Class-L build + eigendecompose; Class-N Gaussian edge weights).

    Builds the Gaussian-proximity graph
    ``w_ij = exp(−(c_i − c_j)² / (2σ²))`` as an srmech edge list (each
    weight from the Class-N argument-halved ``exp``), forms the
    Laplacian via :func:`srmech.amsc.laplacian.dense_laplacian`, and
    reads its eigenpairs via :func:`symmetric_eigendecompose`.

    Returns ``(eigvals, V)`` — ``eigvals`` ascending, ``V`` columns the
    corresponding eigenvectors (so ``V[:, 1]`` is the Fiedler vector).
    """
    n = len(coords)
    two_sigma_sq = 2.0 * sigma * sigma
    edges: List[Tuple[int, int]] = []
    weights: List[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            d = coords[i] - coords[j]
            arg = -(d * d) / two_sigma_sq
            # Class-N exp (argument-halved, well-conditioned); the deep
            # tail (w → 0) is clamped to keep the edge list finite-valued.
            w = 0.0 if arg < -45.0 else _rat.exp(arg, terms=terms)
            edges.append((i, j))
            weights.append(w)
    L = _lap.dense_laplacian(n, edges, weights)
    eigvals, V = _lap.symmetric_eigendecompose(L)
    return eigvals, V


__all__ = [
    "PI",
    "radians",
    "degrees",
    "sqrt",
    "sin_deg",
    "cos_deg",
    "pow_frac",
    "asin",
    "gaussian_proximity_eigs",
]
