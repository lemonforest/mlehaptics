"""Gateway-navigation cascade ops — the SINGLE numpy-free realisation of
the ITN / etak navigation cascade, shared by :mod:`body_architecture`
(inner/outer Fiedler partition) and :mod:`predict_itn_accessibility`
(2-D Fiedler-embedding Δv predictor), and bound declaratively by the
``GatewayNavigation`` ``[class]`` catalog TOML.

etak ≡ ITN
----------

The PR #687 *etak* navigation (ETAK / BOARD / FLOCK triality) and the
ephemerides *ITN* gateway-graph search are the **same cascade** — both
hold an invariant reference frame (the Class-C Fiedler eigenbasis), let
the Class-L manifold's transport structure reveal accessible routes via
Fiedler distance, and Class-M-bind the triality. There is therefore
**one** code path, expressed here once. ``etak`` and ``itn`` are two
named views over it (see the class TOML), not two implementations.

Cascade vocabulary
------------------

* **Class L** — graph-Laplacian build + symmetric eigendecomposition,
  via :func:`srmech.amsc.laplacian.dense_laplacian` +
  :func:`symmetric_eigendecompose` (the numpy-free Jacobi solver, which
  is bit-identical to LAPACK ``eigh`` on these small well-conditioned
  resonance Laplacians — verified ``max |Δλ| = 0``).
* **Class C** — the deterministic Fiedler sign convention (an invariant
  frame so the partition / embedding is platform-reproducible).
* **Class K** — sign re-application as a list negation, never ``abs()``
  on the vector (the pin-slot phase boundary).

Every value is a plain Python ``float`` / ``list``; numpy is **not**
imported here. The eigenvectors arrive as :class:`srmech.amsc.vec.Vec`
columns through ``_cascade.symmetric_eigh`` and are read by index.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from srmech.amsc import laplacian as _lap

from . import _cascade


def adjacency_to_laplacian(n: int, edges: Sequence[Tuple[int, int]],
                           weights: Sequence[float]):
    """Class-L: combinatorial Laplacian ``L = D − W`` from an edge list,
    via :func:`srmech.amsc.laplacian.dense_laplacian` (numpy-free)."""
    return _lap.dense_laplacian(n, list(edges), list(weights))


def symmetric_pairs_to_edges(
    n: int, weight_of,
) -> Tuple[List[Tuple[int, int]], List[float]]:
    """Build the symmetric edge list for the complete graph on ``n``
    nodes, weighting pair ``(i, j)`` by ``weight_of(i, j)``.

    ``weight_of`` is any callable returning a non-negative float. Zero-
    weight pairs are still emitted (a zero entry in ``W`` is a no-op in
    ``L = D − W``); this keeps the edge list a pure function of ``n``.
    """
    edges: List[Tuple[int, int]] = []
    weights: List[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            edges.append((i, j))
            weights.append(float(weight_of(i, j)))
    return edges, weights


def _sign_canon(vec: List[float], pivot: int) -> List[float]:
    """Class-C frame + Class-K sign re-application: force ``vec[pivot]``
    non-negative by negating the whole vector if needed (no ``abs()``)."""
    if vec[pivot] < 0.0:
        return [-x for x in vec]
    return vec


def _argmax_abs(vec: Sequence[float]) -> int:
    """Index of the largest-magnitude entry (Class-K magnitude compare,
    no numpy ``argmax``/``abs`` array op)."""
    best_i = 0
    best_mag = -1.0
    for i, x in enumerate(vec):
        mag = x if x >= 0.0 else -x
        if mag > best_mag:
            best_mag = mag
            best_i = i
    return best_i


def fiedler_partition(L, pivot: int) -> Tuple[float, List[float]]:
    """Class-L eigendecompose + Class-C sign convention.

    Returns ``(λ₂, f₂)`` — the algebraic connectivity and the Fiedler
    vector with ``f₂[pivot] ≥ 0`` (the physics-anchored frame; ``pivot``
    is the shortest-period body so the deep-positive end is reproducible
    across platforms). ``f₂`` is a plain ``list[float]``.
    """
    eigvals, eigvecs_cols = _cascade.symmetric_eigh(L)
    lam2 = float(eigvals[1])
    f2 = _sign_canon([float(x) for x in eigvecs_cols[1]], pivot)
    return lam2, f2


def fiedler_embedding_2d(
    L, pivot: int,
) -> Tuple[float, float, List[float], List[float]]:
    """Class-L eigendecompose → the 2-D ``(f₂, f₃)`` Fiedler embedding
    with deterministic sign conventions.

    ``f₂`` uses the shortest-period ``pivot`` frame (as in
    :func:`fiedler_partition`); ``f₃`` uses the max-magnitude-entry frame
    (no physics anchor available for the third mode). Returns
    ``(λ₂, λ₃, f₂, f₃)`` with ``f₂``, ``f₃`` plain ``list[float]``.
    """
    eigvals, eigvecs_cols = _cascade.symmetric_eigh(L)
    lam2 = float(eigvals[1])
    lam3 = float(eigvals[2])
    f2 = _sign_canon([float(x) for x in eigvecs_cols[1]], pivot)
    f3_raw = [float(x) for x in eigvecs_cols[2]]
    f3 = _sign_canon(f3_raw, _argmax_abs(f3_raw))
    return lam2, lam3, f2, f3


def euclidean_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """L2 distance ‖a − b‖ via the Class-N integer-Newton ``sqrt``
    (``_cascade.sqrt``), numpy-free."""
    s = 0.0
    for ai, bi in zip(a, b):
        d = ai - bi
        s += d * d
    return _cascade.sqrt(s)


__all__ = [
    "adjacency_to_laplacian",
    "symmetric_pairs_to_edges",
    "fiedler_partition",
    "fiedler_embedding_2d",
    "euclidean_distance",
]
