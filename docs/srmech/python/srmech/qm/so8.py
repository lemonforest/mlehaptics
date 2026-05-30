"""The 28-generator ``so(8)`` adjoint, partitioned ``14 + 7 + 7``.

The middle layer of the ``srmech.qm`` so(8)/Spin(8) triality engine
(v0.5.0rc17). ``so(8)`` is the 28-dimensional Lie algebra of ``8x8`` real
antisymmetric matrices. Built from the octonion multiplication table
(:mod:`srmech.qm.octonion`), it splits as a vector space into

- ``14 = g2 = Der(O)`` — the Lie subalgebra of octonion derivations
  ``D_{a,b} = [L_a, L_b] + [R_a, R_b] + [L_a, R_b]`` (Schafer 1966); and
- ``7 + 7`` — the L-type / R-type coset directions ``L_{e_i}`` / ``R_{e_i}``
  (``i = 1..7``), which are antisymmetric but not derivations.

This ``14`` is exactly the ``1 + 3 + 7 + 3 = 14`` A-N partition: the
triality automorphism's fixed subalgebra ``Fix(tau) = g2`` (the
``D4 --(Z3 fold)--> G2`` theorem; see :mod:`srmech.qm.triality`).

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites the
canonical literature, **not** a project instantiation.

A-N placement (per ``[[feedback_no_privileged_primitive_classes]]``):

- ``so8_adjoint_basis`` / ``g2_subalgebra`` — **Class M** (the L/R
  octonion-multiplication binders + the ``g2`` derivations bind octonion
  products).
- ``so7_subalgebra`` — **Class C** (the ``Z2``-swap-fixed subalgebra; the
  ``D4 --(Z2 fold)--> B3`` Dynkin reflection is Class C chirality).

DETERMINISM: the ``14``-element ``g2`` basis is a deterministic
rank-revealing column subset of the 21 ``D_{e_i, e_j}`` (a numpy-only
greedy independent-column walk in fixed order — the pivoted-QR equivalent,
**no scipy**); the ``21``-dim ``so(7)`` basis is an SVD nullspace. **No
``np.random``** anywhere — the clean-MCP no-RNG mandate, and so the
``Fix(tau) = g2`` killer test is reproducible. (``srmech`` treats scipy as
an OPTIONAL dependency, lazily imported with a numpy fallback elsewhere, so
``srmech.qm`` must import cleanly on a scipy-less / Pyodide install.)

Canonical SSoT:

- Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205
  (arXiv:math/0105155) — ``G2 = Aut(O)``, ``Lie(G2) = Der(O)``, Spin(8).
- Schafer, R.D. (1966) *An Introduction to Nonassociative Algebras*,
  Academic Press — the derivation ``D_{a,b}`` of a composition algebra.
- Cartan, E. (1925) *Le principe de dualite et la theorie des groupes
  simples et semi-simples*, Bull. Sci. Math. 49, 361-374 — triality.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from srmech.qm.octonion import (
    octonion_left_mult,
    octonion_mult_table,
    octonion_right_mult,
)

#: Octonion / so(8)-acting dimension.
_DIM = 8

#: Rank-reveal / nullspace tolerance for the deterministic basis extraction.
_RANK_TOL = 1e-9

#: Dimensions of the three pieces (the partition the whole engine turns on).
_DIM_G2 = 14
_DIM_SO7 = 21
_DIM_SO8 = 28


def _basis_vectors() -> np.ndarray:
    """The 8 octonion basis vectors ``e_0 .. e_7`` as rows of ``I_8``."""
    return np.eye(_DIM)


def _commutator(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Matrix commutator ``[X, Y] = X Y - Y X`` (Class L building block)."""
    return x @ y - y @ x


def _derivation(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Schafer octonion derivation ``D_{a,b}`` as an ``8x8`` real matrix.

    ``D_{a,b} = [L_a, L_b] + [R_a, R_b] + [L_a, R_b]`` (Schafer 1966). Each
    ``D_{a,b}`` is antisymmetric and obeys the Leibniz rule
    ``D(xy) = D(x) y + x D(y)``, so it lies in ``g2 = Der(O) subset so(8)``.
    Internal helper (reused by :mod:`srmech.qm.triality`).
    """
    la = octonion_left_mult(a)
    lb = octonion_left_mult(b)
    ra = octonion_right_mult(a)
    rb = octonion_right_mult(b)
    return _commutator(la, lb) + _commutator(ra, rb) + _commutator(la, rb)


def _all_derivations() -> List[np.ndarray]:
    """The 21 derivations ``D_{e_i, e_j}`` for ``1 <= i < j <= 7``.

    Their span has rank exactly ``14 = dim g2`` (verified bit-exact).
    """
    basis = _basis_vectors()
    out: List[np.ndarray] = []
    for i in range(1, _DIM):
        for j in range(i + 1, _DIM):
            out.append(_derivation(basis[i], basis[j]))
    return out


def _epq_pairs() -> Tuple[Tuple[int, int], ...]:
    """The 28 index pairs ``(p, q)``, ``0 <= p < q <= 7``.

    The shared ``E_{pq}`` coordinate frame for the whole engine: the
    28-dim space of antisymmetric ``8x8`` matrices is coordinatised by
    ``coords(M)[index(p, q)] = M[p, q]``. **One** shared helper so the
    ``28x28`` ``tau`` (triality) and the ``g2`` generators' vectorisation
    use the IDENTICAL frame — a mismatch would make ``Fix(tau) = g2`` fail
    spuriously.
    """
    return tuple((p, q) for p in range(_DIM) for q in range(p + 1, _DIM))


def _epq_coords(matrix: np.ndarray) -> np.ndarray:
    """Project an antisymmetric ``8x8`` onto the 28-dim ``E_{pq}`` frame."""
    pairs = _epq_pairs()
    return np.array([matrix[p, q] for (p, q) in pairs])


def _epq_basis() -> List[np.ndarray]:
    """The 28 ``E_{pq} = e_p e_q^T - e_q e_p^T`` antisymmetric basis matrices."""
    out: List[np.ndarray] = []
    for (p, q) in _epq_pairs():
        m = np.zeros((_DIM, _DIM))
        m[p, q] = 1.0
        m[q, p] = -1.0
        out.append(m)
    return out


def _deterministic_rank_subset(
    matrices: List[np.ndarray], n_keep: int
) -> List[np.ndarray]:
    """Deterministic rank-revealing column subset of ``matrices``.

    Vectorises each matrix, then performs a deterministic greedy
    independent-column selection: walk the columns in fixed (ascending)
    order, keeping a column iff it raises the rank of the kept set (its
    residual norm against the span of the already-kept columns exceeds the
    rank tolerance). This is the numpy-only equivalent of a rank-revealing
    pivoted QR — **no RNG and no scipy** (scipy is an optional dependency
    in srmech, lazily imported with a fallback; ``srmech.qm`` must import on
    a scipy-less / Pyodide install). The verified fact (Verify V2) is that a
    pivoted-QR subset and this greedy / SVD subset span the IDENTICAL
    subspace (residual ``~2.5e-15``), so the ``Fix(tau) = g2`` killer test is
    robust to the selection method.
    """
    vectors = np.array([m.flatten() for m in matrices]).T  # (dim, n)
    total_rank = int(np.linalg.matrix_rank(vectors, tol=_RANK_TOL))
    assert total_rank == n_keep, (
        f"rank-revealing subset expected rank {n_keep}; got {total_rank}"
    )
    kept_indices: List[int] = []
    kept_basis: List[np.ndarray] = []  # orthonormal span of kept columns
    norm_scale = max(1.0, float(np.linalg.norm(vectors)))
    for col in range(vectors.shape[1]):
        v = vectors[:, col].astype(float)
        residual = v.copy()
        for q in kept_basis:
            residual = residual - float(q @ residual) * q
        if float(np.linalg.norm(residual)) > _RANK_TOL * norm_scale:
            kept_indices.append(col)
            kept_basis.append(residual / float(np.linalg.norm(residual)))
            if len(kept_indices) == n_keep:
                break
    assert len(kept_indices) == n_keep, (
        f"greedy subset kept {len(kept_indices)}; expected {n_keep}"
    )
    return [matrices[k] for k in kept_indices]


def g2_subalgebra() -> Tuple[np.ndarray, ...]:
    """The 14 octonion derivations ``Der(O) = g2`` as antisymmetric ``8x8``.

    A deterministic rank-revealing (numpy-only greedy independent-column)
    ``14``-element subset of the 21 ``D_{e_i, e_j}`` (``1 <= i < j <= 7``);
    the span has rank exactly 14.
    This is the KILLER-test target: ``Fix(tau) = span(g2)`` (the
    ``D4 --(Z3 fold)--> G2`` theorem), the same ``14`` as the A-N
    ``1 + 3 + 7 + 3`` partition.

    Class M (the ``g2`` Lie subalgebra; derivations bind octonion products).

    Canonical SSoT: Baez (2002) §4.1 (``g2 = Der(O)``, dim 14); Schafer (1966).

    Returns:
        Tuple of 14 antisymmetric ``8x8`` real matrices spanning ``g2``.
    """
    return tuple(_deterministic_rank_subset(_all_derivations(), _DIM_G2))


def so8_adjoint_basis() -> Tuple[np.ndarray, ...]:
    """The 28 ``so(8)`` generators, partitioned ``14 (g2) + 7 (L) + 7 (R)``.

    Order: the 14 ``g2`` derivations, then the 7 L-type ``L_{e_i}``, then the
    7 R-type ``R_{e_i}`` (``i = 1..7``). Each is antisymmetric; together they
    span ``so(8)`` as a vector space (rank 28). The ``g2`` block is the Lie
    subalgebra; the ``7 + 7`` are coset directions.

    Class M (the L/R octonion-multiplication binders are the ``14`` non-``g2``
    directions; ``g2`` is the other 14).

    Canonical SSoT: Baez (2002) §2.4 + §4.1 (so(8) from octonion
    multiplication; ``g2 = Der(O)``).

    Returns:
        Tuple of 28 antisymmetric ``8x8`` real matrices.
    """
    basis = _basis_vectors()
    g2 = list(g2_subalgebra())
    l_type = [octonion_left_mult(basis[i]) for i in range(1, _DIM)]
    r_type = [octonion_right_mult(basis[i]) for i in range(1, _DIM)]
    return tuple(g2 + l_type + r_type)


def so7_subalgebra() -> Tuple[np.ndarray, ...]:
    """The 21-dim ``so(7)`` fixed space of the ``Z2`` swap (``D4 -> B3`` fold).

    ``so(7) = ker(S_B - I)`` where ``S_B`` is the companion involution (see
    :func:`srmech.qm.triality.triality_swap`). Returned as a deterministic
    SVD-nullspace basis of 21 antisymmetric ``8x8`` generators (re-expressed
    from the ``E_{pq}`` frame back to matrices).

    Class C (the ``Z2``-swap-fixed subalgebra; ``Z2`` swap = Class C
    chirality / the ``D4 --(Z2 fold)--> B3`` Dynkin reflection).

    Canonical SSoT: Baez (2002) §2.4 + the ``D4 -> B3`` Dynkin fold.

    Returns:
        Tuple of 21 antisymmetric ``8x8`` real matrices spanning ``so(7)``.
    """
    # Imported here to keep the module DAG acyclic at import time
    # (octonion <- so8 <- triality): so7 needs the triality companion map.
    from srmech.qm.triality import triality_swap

    swap = triality_swap()
    fixed = _fixed_space_matrices(swap, _DIM_SO7)
    return tuple(fixed)


def _fixed_space_matrices(operator: np.ndarray, dim: int) -> List[np.ndarray]:
    """An orthonormal basis of ``ker(operator - I)`` as antisymmetric ``8x8``.

    Deterministic SVD nullspace (sorted singular values; no RNG). Each
    returned 28-vector is mapped back to an antisymmetric ``8x8`` matrix via
    the shared ``E_{pq}`` frame.
    """
    identity = np.eye(operator.shape[0])
    _, singular, vh = np.linalg.svd(operator - identity)
    null_columns = vh.T[:, singular < _RANK_TOL * max(1.0, singular[0])]
    found = null_columns.shape[1]
    assert found == dim, (
        f"fixed-space dimension expected {dim}; got {found}"
    )
    pairs = _epq_pairs()
    out: List[np.ndarray] = []
    for c in range(dim):
        coeffs = null_columns[:, c]
        m = np.zeros((_DIM, _DIM))
        for idx, (p, q) in enumerate(pairs):
            m[p, q] = coeffs[idx]
            m[q, p] = -coeffs[idx]
        out.append(m)
    return out


__all__ = [
    "g2_subalgebra",
    "so7_subalgebra",
    "so8_adjoint_basis",
]
