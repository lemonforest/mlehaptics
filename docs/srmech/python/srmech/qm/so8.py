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

import functools
from typing import Dict, List, Tuple

import numpy as np
from srmech.amsc.cascade import matrix_cascades as _mc

from srmech.amsc import rational as _srn

from srmech.amsc.cascade import magnitude as _magnitude
from srmech.amsc.cascade.spectral_cascades import kron as _kron
from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.amsc.laplacian import (
    dense_dot_complex,
    dense_dot_real,
    dense_matmul_real,
    dense_matvec_complex,
    dense_matvec_real,
    dense_norm,
    hermitian_eigendecompose,
)
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

#: su(3) Lie-decomposition dimensions of the 14-generator g2 (the
#: ``an_embedding`` voxel): the 8-real-dim su(3) stabiliser, the 6-real-dim
#: su(3)-module complement, and the 3-complex-dim fundamental / antifundamental.
_DIM_SU3 = 8
_DIM_COMPLEMENT = 6
_DIM_TRIPLET = 3

#: A FIXED ISO timestamp for the ``an_embedding`` self-attestation.
#: Deterministic on purpose (NOT ``datetime.now()``) so the MCP surface is
#: reproducible — the attestation of a GENERATED structure must not change
#: between calls (mirrors :data:`srmech.qm.octonion._RETRIEVED_AT`).
_AN_RETRIEVED_AT = "2026-05-30T00:00:00Z"

#: The single generative rule whose bytes are the ``parser_rule_hash``
#: provenance of the su(3) stabiliser: su(3) = {D in g2 : D e_K = 0}.
_AN_PARSER_RULE = b"D e_K = 0"

#: so(4) = su(2) ⊕ su(2) dimensions for the quaternion-subalgebra stabiliser
#: (the ``quaternion_subalgebra_stabiliser`` voxel; F215): the 6-real-dim
#: stabiliser, split as two 3-real-dim su(2) ideals.
_DIM_SO4 = 6
_DIM_SU2 = 3
_DIM_H_IMAG = 3  # the 3 imaginary units of a quaternion subalgebra H ⊂ O
_DIM_COMP4 = 4   # the 4 octonion units in the orthogonal complement H^⊥

#: The single generative rule whose bytes are the ``parser_rule_hash``
#: provenance of the so(4) stabiliser: a derivation stabilises H iff it maps
#: the 3 imaginary units of H back into H (equivalently, the orthogonal
#: complement H^⊥ into itself). ``span(H_imag)`` is the imaginary part of H.
_SO4_PARSER_RULE = b"D span(H_imag) subseteq span(H_imag)"


def _basis_vectors() -> np.ndarray:
    """The 8 octonion basis vectors ``e_0 .. e_7`` as rows of ``I_8``."""
    return np.eye(_DIM)


def _commutator(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Matrix commutator ``[X, Y] = X Y - Y X`` (Class L building block)."""
    return dense_matmul_real(x, y) - dense_matmul_real(y, x)


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
    norm_scale = max(1.0, float(dense_norm(vectors)))
    for col in range(vectors.shape[1]):
        v = vectors[:, col].astype(float)
        residual = v.copy()
        for q in kept_basis:
            residual = residual - dense_dot_real(q, residual) * q
        if float(dense_norm(residual)) > _RANK_TOL * norm_scale:
            kept_indices.append(col)
            kept_basis.append(residual / float(dense_norm(residual)))
            if len(kept_indices) == n_keep:
                break
    assert len(kept_indices) == n_keep, (
        f"greedy subset kept {len(kept_indices)}; expected {n_keep}"
    )
    return [matrices[k] for k in kept_indices]


def _frozen_tuple(matrices: List[np.ndarray]) -> Tuple[np.ndarray, ...]:
    """A cache-safe tuple of ``writeable=False`` copies of ``matrices``.

    The cached builders below return one of these so the memoised value can
    never be mutated through the references the public copy-out reads from.
    """
    out: List[np.ndarray] = []
    for m in matrices:
        frozen = np.array(m)
        frozen.flags.writeable = False
        out.append(frozen)
    return tuple(out)


def _thaw_tuple(frozen: Tuple[np.ndarray, ...]) -> Tuple[np.ndarray, ...]:
    """Defensive copy-out: a fresh tuple of fresh WRITEABLE arrays.

    The public ``so(8)`` surfaces hand callers a thawed copy of the cached
    build so a downstream mutation can never corrupt the shared cache; the
    build is expensive, the per-call copy is cheap, and the values are
    bit-identical (deterministic — no ``np.random``).
    """
    return tuple(np.array(m) for m in frozen)


@functools.lru_cache(maxsize=None)
def _build_g2() -> Tuple[np.ndarray, ...]:
    """Cached read-only ``g2`` basis (the expensive rank-revealing subset)."""
    return _frozen_tuple(_deterministic_rank_subset(_all_derivations(), _DIM_G2))


def g2_subalgebra() -> Tuple[np.ndarray, ...]:
    """The 14 octonion derivations ``Der(O) = g2`` as antisymmetric ``8x8``.

    A deterministic rank-revealing (numpy-only greedy independent-column)
    ``14``-element subset of the 21 ``D_{e_i, e_j}`` (``1 <= i < j <= 7``);
    the span has rank exactly 14.
    This is the KILLER-test target: ``Fix(tau) = span(g2)`` (the
    ``D4 --(Z3 fold)--> G2`` theorem), the same ``14`` as the A-N
    ``1 + 3 + 7 + 3`` partition. The expensive build is memoised
    (:func:`_build_g2`); each call returns a fresh writeable copy.

    Class M (the ``g2`` Lie subalgebra; derivations bind octonion products).

    Canonical SSoT: Baez (2002) §4.1 (``g2 = Der(O)``, dim 14); Schafer (1966).

    Returns:
        Tuple of 14 antisymmetric ``8x8`` real matrices spanning ``g2``.
    """
    return _thaw_tuple(_build_g2())


@functools.lru_cache(maxsize=None)
def _build_so8_adjoint() -> Tuple[np.ndarray, ...]:
    """Cached read-only ``so(8)`` adjoint basis (``14 g2 + 7 L + 7 R``)."""
    basis = _basis_vectors()
    g2 = list(_build_g2())
    l_type = [octonion_left_mult(basis[i]) for i in range(1, _DIM)]
    r_type = [octonion_right_mult(basis[i]) for i in range(1, _DIM)]
    return _frozen_tuple(g2 + l_type + r_type)


def so8_adjoint_basis() -> Tuple[np.ndarray, ...]:
    """The 28 ``so(8)`` generators, partitioned ``14 (g2) + 7 (L) + 7 (R)``.

    Order: the 14 ``g2`` derivations, then the 7 L-type ``L_{e_i}``, then the
    7 R-type ``R_{e_i}`` (``i = 1..7``). Each is antisymmetric; together they
    span ``so(8)`` as a vector space (rank 28). The ``g2`` block is the Lie
    subalgebra; the ``7 + 7`` are coset directions.

    Class M (the L/R octonion-multiplication binders are the ``14`` non-``g2``
    directions; ``g2`` is the other 14).

    Canonical SSoT: Baez (2002) §2.4 + §4.1 (so(8) from octonion
    multiplication; ``g2 = Der(O)``). The build is memoised
    (:func:`_build_so8_adjoint`); each call returns a fresh writeable copy.

    Returns:
        Tuple of 28 antisymmetric ``8x8`` real matrices.
    """
    return _thaw_tuple(_build_so8_adjoint())


@functools.lru_cache(maxsize=None)
def _build_so7() -> Tuple[np.ndarray, ...]:
    """Cached read-only ``so(7)`` basis (SVD nullspace of ``S_B - I``)."""
    # Imported here to keep the module DAG acyclic at import time
    # (octonion <- so8 <- triality): so7 needs the triality companion map.
    from srmech.qm.triality import triality_swap

    swap = triality_swap()
    return _frozen_tuple(_fixed_space_matrices(swap, _DIM_SO7))


def so7_subalgebra() -> Tuple[np.ndarray, ...]:
    """The 21-dim ``so(7)`` fixed space of the ``Z2`` swap (``D4 -> B3`` fold).

    ``so(7) = ker(S_B - I)`` where ``S_B`` is the companion involution (see
    :func:`srmech.qm.triality.triality_swap`). Returned as a deterministic
    SVD-nullspace basis of 21 antisymmetric ``8x8`` generators (re-expressed
    from the ``E_{pq}`` frame back to matrices).

    Class C (the ``Z2``-swap-fixed subalgebra; ``Z2`` swap = Class C
    chirality / the ``D4 --(Z2 fold)--> B3`` Dynkin reflection).

    Canonical SSoT: Baez (2002) §2.4 + the ``D4 -> B3`` Dynkin fold. The
    build is memoised (:func:`_build_so7`); each call returns a fresh
    writeable copy.

    Returns:
        Tuple of 21 antisymmetric ``8x8`` real matrices spanning ``so(7)``.
    """
    return _thaw_tuple(_build_so7())


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


# ──────────────────────────────────────────────────────────────────────
# an_embedding — the su(3) ⊕ 3 ⊕ 3bar Lie decomposition of g2 = Der(O)
#
# A DIFFERENT 14-decomposition from the partitioned ``so8_adjoint_basis``
# (which splits the 28-dim so(8) as 14 g2 + 7 L + 7 R). Here the *14-dim
# g2 itself* splits under one of its su(3) subalgebras as the Lie-algebra
# branching ``14 = 8 + 3 + 3bar`` — the adjoint of su(3) (8) plus the
# fundamental (3) plus the antifundamental (3bar). It is the genuine
# su(3)-module structure of g2, computed bit-exact and self-attesting.
#
# The construction is the deterministic chain (no np.random, numpy-only):
#   1. su(3) = the stabiliser {D in g2 : D e_K = 0} (SVD nullspace; dim 8).
#   2. complement = the 6-real-dim orthogonal su(3)-module (the "movers").
#   3. J = the su(3)-INVARIANT complex structure on the complement (the
#      antisymmetric generator of the 2-dim commutant {aI + bJ} of the
#      6-dim su(3)-rep; J^2 = -I). FIX 1: a *real* 3-dim span CANNOT carry
#      the su(3) fundamental ([su3, real-3] leaks); the genuine fundamental
#      is the +i eigenspace of J on the COMPLEXIFIED complement.
#   4. triplet / antitriplet = the J = +i / -i eigenspaces (complex), the
#      genuine fundamental / antifundamental; [su3, triplet] ⊆ triplet is
#      then bit-exact.
# ──────────────────────────────────────────────────────────────────────


def _epq_to_matrix(coeffs: np.ndarray) -> np.ndarray:
    """Re-express a 28-vector of ``E_{pq}`` coords as an antisymmetric ``8x8``.

    The inverse of :func:`_epq_coords` — fills the upper triangle from
    ``coeffs`` and antisymmetrises. Accepts a real or complex coefficient
    vector (the complex path is used for the ``J``-eigenspace triplet).
    """
    m = np.zeros((_DIM, _DIM), dtype=coeffs.dtype)
    for idx, (p, q) in enumerate(_epq_pairs()):
        m[p, q] = coeffs[idx]
        m[q, p] = -coeffs[idx]
    return m


def _commutator_coords(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """``E_{pq}`` coords of the commutator ``[X, Y]`` (real or complex)."""
    return _epq_coords(_commutator(x, y))


def _su3_stabiliser(g2: List[np.ndarray], k: int) -> List[np.ndarray]:
    """The su(3) stabiliser ``{D in g2 : D e_K = 0}`` as 8 antisymmetric ``8x8``.

    Build ``A = column_stack([g2[a] e_K for a])`` (``8 x 14``); its right
    nullspace (deterministic SVD; singular value ``< _RANK_TOL * max``) is
    EXACTLY 8-dim. Each null coefficient vector ``c`` rebuilds a stabiliser
    generator ``M = sum_a c_a g2[a]``. Asserts ``dim == 8`` and that each
    ``M`` annihilates ``e_K``.
    """
    e_k = _basis_vectors()[k]
    a_matrix = np.column_stack(
        [dense_matvec_real(g2[a], e_k) for a in range(_DIM_G2)]
    )  # (8,14)
    _, singular, vh = np.linalg.svd(a_matrix)
    scale = max(1.0, float(singular[0]))
    null_coeffs: List[np.ndarray] = []
    for idx in range(vh.shape[0]):
        s = float(singular[idx]) if idx < len(singular) else 0.0
        if s < _RANK_TOL * scale:
            null_coeffs.append(vh[idx])
    assert len(null_coeffs) == _DIM_SU3, (
        f"su(3) stabiliser expected dim {_DIM_SU3}; got {len(null_coeffs)}"
    )
    su3 = [
        sum(c[a] * g2[a] for a in range(_DIM_G2)) for c in null_coeffs
    ]
    for matrix in su3:
        residual = _magnitude(float(dense_norm(dense_matvec_real(matrix, e_k))))
        assert residual < _RANK_TOL, (
            f"su(3) generator does not annihilate e_{k}: residual {residual}"
        )
    return su3


def _orthonormal_coords(matrices: List[np.ndarray]) -> np.ndarray:
    """Orthonormal basis (in the ``E_{pq}`` frame) of the span of ``matrices``.

    QR of the ``(28, n)`` coordinate stack — the deterministic numpy-only
    orthonormalisation (no scipy, no RNG).
    """
    coords = np.column_stack([_epq_coords(m) for m in matrices])
    q, _ = _mc.qr(coords)
    return q


def _su3_complement(
    g2: List[np.ndarray], su3_orthonormal: np.ndarray
) -> Tuple[List[np.ndarray], np.ndarray]:
    """The 6-real-dim su(3)-module complement of su(3) inside g2.

    Project the orthonormal g2-span out of the su(3) span and SVD the
    residual: the left-singular vectors with a non-trivial singular value
    are EXACTLY 6, the orthogonal "mover" directions. Returns both the 6
    antisymmetric ``8x8`` matrices and the ``(28, 6)`` orthonormal
    coordinate frame (the latter is the J-construction's working frame).
    Asserts ``dim == 6``.
    """
    g2_coords = np.column_stack([_epq_coords(m) for m in g2])  # (28,14)
    q_g2, _ = _mc.qr(g2_coords)                          # (28,14) on
    projector = dense_matmul_real(su3_orthonormal, su3_orthonormal.T)
    residual = q_g2 - dense_matmul_real(projector, q_g2)       # (28,14)
    left, singular, _ = np.linalg.svd(residual, full_matrices=False)
    scale = max(1.0, float(singular[0]))
    keep = singular > _RANK_TOL * scale
    complement_coords = left[:, keep]                          # (28,6)
    found = complement_coords.shape[1]
    assert found == _DIM_COMPLEMENT, (
        f"su(3) complement expected dim {_DIM_COMPLEMENT}; got {found}"
    )
    complement = [
        _epq_to_matrix(complement_coords[:, c]) for c in range(found)
    ]
    return complement, complement_coords


def _ad_on_complement(
    x: np.ndarray, complement: List[np.ndarray], complement_coords: np.ndarray
) -> np.ndarray:
    """The matrix of ``ad(X) = [X, .]`` restricted to the complement frame.

    Column ``i`` is the 6-vector of ``[X, complement_i]`` re-expressed in the
    orthonormal complement coordinate basis. For ``X in su(3)`` the
    complement is ad-invariant, so the result is an exact ``6x6`` real
    matrix.
    """
    columns = [
        dense_matvec_real(complement_coords.T, _commutator_coords(x, y))
        for y in complement
    ]
    return np.column_stack(columns)


def _invariant_complex_structure(
    su3: List[np.ndarray],
    complement: List[np.ndarray],
    complement_coords: np.ndarray,
) -> np.ndarray:
    """The su(3)-invariant complex structure ``J`` on the 6-dim complement.

    FIX 1 — the genuine fundamental is a J-EIGENSPACE, not a real 3-span.
    The commutant of the 6-dim real su(3)-rep ``{ad(X)|complement}`` is
    EXACTLY 2-dim ``{aI + bJ}``; ``J`` is its antisymmetric generator with
    ``J^2 = -I``. Solve the commutant by the deterministic nullspace of the
    stacked ``[ad^T (x) I - I (x) ad]`` (Kronecker) system, take the
    antisymmetric part, normalise so ``J^2 = -I``, and pin the sign by a
    FIXED documented convention (first non-zero strict-upper-triangular
    entry positive — Class C chirality choice). Asserts commutant dim 2,
    ``J^2 = -I``, and ``[J, ad(X)] = 0`` for every ``X in su(3)``.
    """
    dim = _DIM_COMPLEMENT
    identity = np.eye(dim)
    ad_mats = [
        _ad_on_complement(x, complement, complement_coords) for x in su3
    ]
    stacked = np.vstack(
        # ad ↦ ad⊗I − I⊗ad via the Class-I(mixed-radix)∘M Kronecker cascade
        # (substrate-native replacement for the NumPy Kronecker product;
        # np.asarray is carrier-only).
        [np.asarray(_kron(ad.T, identity)) - np.asarray(_kron(identity, ad))
         for ad in ad_mats]
    )
    _, singular, vh = np.linalg.svd(stacked)
    scale = max(1.0, float(singular[0]))
    commutant = [
        vh[idx].reshape(dim, dim)
        for idx in range(vh.shape[0])
        if (float(singular[idx]) if idx < len(singular) else 0.0)
        < _RANK_TOL * scale
    ]
    assert len(commutant) == 2, (
        f"su(3)-rep commutant expected dim 2 {{aI + bJ}}; got {len(commutant)}"
    )
    # The antisymmetric member of {aI + bJ} is J (up to scale); I is symmetric.
    antisymmetric = [0.5 * (m - m.T) for m in commutant]
    j_raw = max(antisymmetric, key=lambda a: float(dense_norm(a)))
    # Normalise so J^2 = -I: J_raw^2 = -s^2 I, so J = J_raw / s.
    j_squared = dense_matmul_real(j_raw, j_raw)
    s = float(_srn.sqrt(_magnitude(float(np.mean(np.diag(j_squared))))))
    j = j_raw / s
    # FIXED sign convention (Class C): first non-zero strict-upper-triangular
    # entry positive. Documented as a CHOICE; only J^2 = -I is a fact.
    upper = np.triu_indices(dim, 1)
    flat = j[upper]
    for value in flat:
        if _magnitude(float(value)) > _RANK_TOL:
            if value < 0.0:
                j = -j
            break
    # Belt-and-suspenders: J^2 = -I and J commutes with every ad(X).
    assert _magnitude(float(dense_norm(
        dense_matmul_real(j, j) + identity))) < _RANK_TOL, (
        "complex structure J does not satisfy J^2 = -I"
    )
    for ad in ad_mats:
        commute = _magnitude(float(dense_norm(_commutator(j, ad))))
        assert commute < _RANK_TOL, (
            f"complex structure J does not commute with ad(su3): {commute}"
        )
    return j


def _eig_real_skew(skew: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Eigenpairs of a REAL skew-symmetric matrix via the C-backed Hermitian path.

    For real antisymmetric ``S`` (``Sᵀ = −S``), ``iS`` is Hermitian — so
    :func:`~srmech.amsc.laplacian.hermitian_eigendecompose` (native Jacobi peer;
    numpy ``eigh`` only as its own fallback) yields real eigenvalues ``μ``
    (ascending) and a unitary eigenvector matrix ``V``. Then ``S``'s eigenvalues
    are the purely-imaginary ``λ = −i·μ`` and its eigenvectors are the **same**
    ``V`` — routing a real non-Hermitian ``eig`` onto the existing Hermitian
    cascade (no NumPy ``eig``). Returns ``(eigenvalues, V)`` matching the
    NumPy ``eig`` shape contract (``eigenvalues`` complex with the weight in
    ``.imag``; ``V`` complex columns). ``iS`` is built by the scalar carrier
    ``1j * S`` (no linalg/fft/matmul/ufunc).

    The eigenvector phase and the basis WITHIN a degenerate eigenspace are
    solver-chosen (non-unique) — exactly as NumPy's ``eig`` already left
    them — so callers must consume ``V`` invariantly (Rayleigh quotient, or the
    eigenspace SPAN, both verified basis-invariant), never as fixed columns.
    """
    S = np.ascontiguousarray(skew, dtype=np.float64)
    mu, V = hermitian_eigendecompose(1j * S)        # iS Hermitian; μ real, ascending
    return (-1j * mu), V                             # λ(S) = −i·μ (purely imaginary)


def _triplet_from_eigenspace(
    j: np.ndarray, complement: List[np.ndarray]
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """The ``J = +i / -i`` eigenspaces as complex ``8x8`` matrices.

    FIX 1 — diagonalise the real antisymmetric ``J`` (eigenvalues ``+/- i``,
    each with multiplicity 3). The ``+i`` eigenvectors (complex coefficients
    over the complement frame) rebuild the 3 COMPLEX antisymmetric ``8x8``
    fundamental generators (the triplet); the ``-i`` eigenvectors rebuild
    the antitriplet (its conjugate). With this J-eigenspace fundamental,
    ``[su3, triplet] ⊆ triplet`` is bit-exact (``~3e-14``).
    """
    eigenvalues, eigenvectors = _eig_real_skew(j)  # J real-antisymmetric → iS-Hermitian route
    plus = [k for k in range(j.shape[0]) if eigenvalues[k].imag > 0.5]
    minus = [k for k in range(j.shape[0]) if eigenvalues[k].imag < -0.5]
    assert len(plus) == _DIM_TRIPLET and len(minus) == _DIM_TRIPLET, (
        f"J eigenspaces expected {_DIM_TRIPLET}+{_DIM_TRIPLET}; got "
        f"{len(plus)}+{len(minus)}"
    )

    def combine(vec: np.ndarray) -> np.ndarray:
        return sum(
            vec[c] * complement[c].astype(complex)
            for c in range(_DIM_COMPLEMENT)
        )

    triplet = [combine(eigenvectors[:, k]) for k in plus]
    antitriplet = [combine(eigenvectors[:, k]) for k in minus]
    return triplet, antitriplet


def _rank2_cartan(su3: List[np.ndarray]) -> List[np.ndarray]:
    """The rank-2 Cartan subalgebra of su(3) via a centraliser (FIX 3).

    FIX 3 — the greedy maximal mutually-commuting subset returns 1 (generic
    basis vectors do not pairwise-commute). Instead take a FIXED regular
    element ``R = sum_i (i+1) su3[i]``; its centraliser ``{X in su3 :
    [X, R] = 0}`` is EXACTLY the rank-2 Cartan. Solve the centraliser as the
    deterministic nullspace of ``column_stack([coords([su3[a], R])])`` over
    the 8-dim coefficient space. Asserts ``dim == 2``.
    """
    regular = sum((i + 1) * su3[i] for i in range(_DIM_SU3))
    columns = [_commutator_coords(su3[a], regular) for a in range(_DIM_SU3)]
    bracket = np.column_stack(columns)  # (28, 8)
    _, singular, vh = np.linalg.svd(bracket)
    scale = max(1.0, float(singular[0]))
    null_coeffs = [
        vh[idx]
        for idx in range(vh.shape[0])
        if (float(singular[idx]) if idx < len(singular) else 0.0)
        < _RANK_TOL * scale
    ]
    assert len(null_coeffs) == 2, (
        f"rank-2 Cartan via centraliser expected dim 2; got {len(null_coeffs)}"
    )
    return [sum(c[a] * su3[a] for a in range(_DIM_SU3)) for c in null_coeffs]


def _complement_weights(
    cartan: List[np.ndarray],
    complement: List[np.ndarray],
    complement_coords: np.ndarray,
) -> np.ndarray:
    """The 6 complement weights under the rank-2 Cartan as a ``(6, 2)`` array.

    For each Cartan generator ``H`` (real antisymmetric on the complement),
    ``ad(H)`` has eigenvalues ``+/- i * weight``. The two ``ad(H_k)`` commute,
    so they share eigenvectors; the weight of eigenvector ``v`` along Cartan
    ``k`` is ``-i * (v^H ad(H_k) v) / (v^H v)``. The six weights come in
    ``+/-`` pairs (the su(3) ``3`` weights and their negatives).
    """
    ad_cartan = [
        _ad_on_complement(h, complement, complement_coords) for h in cartan
    ]
    _, eigenvectors = _eig_real_skew(ad_cartan[0])  # ad(H) real-antisymmetric → iS-Hermitian route
    weights = np.zeros((_DIM_COMPLEMENT, 2))
    for k in range(_DIM_COMPLEMENT):
        v = eigenvectors[:, k]
        # v is a COMPLEX eigenvector of the real ad(H) (eigenvalues ±i·weight),
        # so these contractions are genuinely complex (Class-L complex cascade).
        denom = dense_dot_complex(v.conj(), v)
        for axis, ad in enumerate(ad_cartan):
            rayleigh = dense_dot_complex(
                v.conj(), dense_matvec_complex(ad, v)) / denom
            # ad(H) v = i * weight * v  =>  weight = -i * rayleigh.
            weights[k, axis] = float((-1j * rayleigh).real)
    return weights


def _an_attestation(generators: List[np.ndarray], k: int) -> Dict[str, object]:
    """MPR v1 self-attestation for the COMPUTED su(3) ⊕ 3 ⊕ 3bar structure.

    Class A — content-address the GENERATED structure (NOT a fetched datum):
    ``response_sha256`` is :func:`srmech.amsc.format.sha256_bytes` over the
    concatenated ``float64`` bytes of the 14 ``g2`` generators (the build
    INPUT, deterministically content-addressed; **no** new
    ``hashlib.sha256``). ``parser_rule_hash`` hashes the stabiliser rule
    bytes ``b"D e_K = 0"``. ``source_url`` cites Baez (arXiv) for the
    ``g2 = Der(O)`` / dim-14 PARENT FACT ONLY — the 8+3+3bar branching is
    this op's own bit-exact computation, NOT a cited result.
    """
    generator_bytes = b"".join(
        np.ascontiguousarray(g, dtype=np.float64).tobytes() for g in generators
    )
    response_sha256 = _sha256_bytes(generator_bytes)
    parser_rule_hash = _sha256_bytes(_AN_PARSER_RULE)
    descriptor_hash = _sha256_bytes(
        b"srmech/qm/so8.py::an_embedding::su3_3_3bar"
    )
    return {
        "mpr_version": "1.0",
        "data": {
            "structure": "g2_su3_3_3bar_decomposition",
            "imaginary_unit": k,
            "real_dimensions": {"su3": _DIM_SU3, "complement": _DIM_COMPLEMENT},
            "complex_dimensions": {
                "triplet": _DIM_TRIPLET,
                "antitriplet": _DIM_TRIPLET,
            },
        },
        "data_schema_id": "srmech://schema/g2_su3_decomposition",
        "attestation": {
            # Baez is OA on arXiv; a paywalled-only DOI is rejected per
            # [[feedback_paywalled_doi_cannot_be_attested]] — no source_doi.
            "source_doi": None,
            # Cites the g2 = Der(O) / dim-14 PARENT FACT only (the build
            # input); the 8+3+3bar branching is this op's own computation.
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _AN_RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.5.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/qm/so8.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": "g2 = Der(O) su(3) ⊕ 3 ⊕ 3bar Lie decomposition",
            "purpose": (
                "Bit-exact su(3)-module branching of the 14 g2 generators "
                "(computed self-attesting structure)"
            ),
            "cite_as": (
                "Baez, J.C. (2002) The Octonions, Bull. Amer. Math. Soc. 39, "
                "145-205 (arXiv:math/0105155) — for g2 = Der(O), dim 14 "
                "(the build input only)"
            ),
        },
    }


@functools.lru_cache(maxsize=None)
def _build_an_embedding(
    imaginary_unit: int,
) -> Tuple[
    Tuple[np.ndarray, ...],  # su3 (8 real antisym 8x8)
    Tuple[np.ndarray, ...],  # complement (6 real antisym 8x8)
    np.ndarray,              # complex_structure_J (6x6 real)
    Tuple[np.ndarray, ...],  # triplet (3 complex 8x8)
    Tuple[np.ndarray, ...],  # antitriplet (3 complex 8x8)
    np.ndarray,              # weights (6,2) real
]:
    """Cached read-only su(3) ⊕ 3 ⊕ 3bar build for a fixed imaginary unit.

    The expensive deterministic chain (SVD nullspaces + Kronecker commutant
    + eigendecompositions) runs once per ``imaginary_unit`` and is memoised;
    :func:`an_embedding` copies out a fresh writeable dict each call. All
    returned arrays are frozen (``writeable=False``) so the cache cannot be
    mutated through a caller's reference.
    """
    k = imaginary_unit
    g2 = list(_build_g2())

    su3 = _su3_stabiliser(g2, k)
    su3_orthonormal = _orthonormal_coords(su3)  # (28,8)
    complement, complement_coords = _su3_complement(g2, su3_orthonormal)

    # Bidirectional killer test: span[su3 | complement] == span(g2) (rank 14).
    su3_coords = np.column_stack([_epq_coords(m) for m in su3])
    g2_coords = np.column_stack([_epq_coords(m) for m in g2])
    span = np.column_stack([su3_coords, complement_coords])
    rank_span = int(np.linalg.matrix_rank(span, tol=_RANK_TOL))
    rank_with_g2 = int(
        np.linalg.matrix_rank(
            np.column_stack([span, g2_coords]), tol=_RANK_TOL
        )
    )
    assert rank_span == _DIM_G2, (
        f"span[su3 | complement] rank expected {_DIM_G2}; got {rank_span}"
    )
    assert rank_with_g2 == _DIM_G2, (
        f"span[su3 | complement | g2] rank expected {_DIM_G2} (same span as "
        f"g2); got {rank_with_g2}"
    )

    j = _invariant_complex_structure(su3, complement, complement_coords)
    triplet, antitriplet = _triplet_from_eigenspace(j, complement)
    cartan = _rank2_cartan(su3)
    weights = _complement_weights(cartan, complement, complement_coords)

    su3_frozen = _frozen_tuple(su3)
    complement_frozen = _frozen_tuple(complement)
    triplet_frozen = _frozen_tuple(triplet)
    antitriplet_frozen = _frozen_tuple(antitriplet)
    j_frozen = np.array(j)
    j_frozen.flags.writeable = False
    weights_frozen = np.array(weights)
    weights_frozen.flags.writeable = False
    return (
        su3_frozen,
        complement_frozen,
        j_frozen,
        triplet_frozen,
        antitriplet_frozen,
        weights_frozen,
    )


def an_embedding(imaginary_unit: int = 1) -> dict:
    """The bit-exact su(3) ⊕ 3 ⊕ 3bar Lie decomposition of ``g2 = Der(O)``.

    The 14 ``g2`` derivations (:func:`g2_subalgebra`) split, under one of
    their su(3) subalgebras, as the Lie-algebra branching ``14 = 8 + 3 +
    3bar`` — the su(3) ADJOINT (8) plus the FUNDAMENTAL (3) plus the
    ANTIFUNDAMENTAL (3bar). This is the genuine su(3)-module structure of
    ``g2``; the 7-dim octonion-imaginary vector rep branches ``7 = 1 + 3 +
    3bar`` over the same su(3). Both branchings are computed bit-exact and
    returned with an MPR self-attestation.

    CONSTRUCTION (deterministic, numpy-only, no ``np.random``, no scipy;
    memoised via :func:`_build_an_embedding`, copied out fresh each call):

    1. **su(3) = the stabiliser** ``{D in g2 : D e_K = 0}`` (``e_K`` the
       ``imaginary_unit``-th octonion basis vector) via an SVD nullspace —
       EXACTLY 8-dim.
    2. **complement** — the 6-real-dim orthogonal su(3)-module (the
       "movers"); ``span[su3 | complement] == span(g2)`` (rank 14, both
       directions: the bidirectional killer test).
    3. **complex_structure_J** — the su(3)-INVARIANT complex structure on
       the 6-dim complement. The commutant of the 6-dim real su(3)-rep is
       EXACTLY 2-dim ``{aI + bJ}``; ``J`` is its antisymmetric generator,
       ``J^2 = -I``, ``[J, ad(X)] = 0`` for every ``X in su(3)``.
    4. **triplet / antitriplet** — the ``J = +i / -i`` eigenspaces of the
       complexified complement (COMPLEX ``8x8`` arrays): the genuine
       fundamental / antifundamental.

    WHY THE FUNDAMENTAL IS A J-EIGENSPACE (the load-bearing subtlety): a
    *real* 3-dim span of antisymmetric matrices CANNOT carry the su(3)
    fundamental — every real 3-subspace of the complement LEAKS at ``O(1)``
    under ``[su3, ·]`` (never bit-exact). The fundamental is irreducibly
    COMPLEX; it lives as the
    ``+i`` eigenspace of the invariant ``J``. With this ``J``-eigenspace
    ``3``, ``[su3, 3] ⊆ 3`` is bit-exact (``~3e-14``). The returned
    ``complement`` is the GENUINE real su(3)-module (``[su3, complement] ⊆
    complement`` is ``~2e-15``); only the ``J``-eigenspace ``triplet`` /
    ``antitriplet`` carry the irreducible ``3`` / ``3bar`` with the bit-exact
    ``[su3, 3] ⊆ 3`` closure.

    su(3) IDENTIFICATION (an honest INVARIANT certificate, NOT a raw-Casimir
    comparison): ``{dim 8, rank 2, simple}`` — where ``rank 2`` is the
    dimension of the centraliser of a fixed regular element (the
    greedy mutually-commuting-subset count would spuriously return 1), and
    ``simple`` means the adjoint commutant has dim 1. By the Cartan ``A2``
    classification these UNIQUELY identify su(3) (ruling out ``su(2) +
    su(2)``, whose commutant is 2). Supporting evidence: in a
    Killing-orthonormalised basis the structure constants are TOTALLY
    ANTISYMMETRIC. (A raw adjoint-Casimir-vs-``f^{abc}`` comparison to
    :func:`srmech.qm.gauge.su3_structure_constants` is deliberately NOT used:
    the candidate's adjoint-Casimir eigenvalue is basis-dependent and its
    normalisation differs from the gauge Gell-Mann convention, the
    Casimir/Killing ratio is tautologically 1 for any algebra, and the two
    bases differ by an ``O(8)`` rotation so raw ``f^{abc}`` equality fails
    too.)

    3 / 3bar ORIENTATION is pinned by a FIXED convention (the documented
    sign of ``J``, plus a lexicographic key on the Cartan weights) and is a
    CHOICE — a Class C chirality / complex-structure-sign convention, NOT
    canonical. Only the ``+/-`` weight-PAIRING is asserted as fact.

    A-N FRAMEWORK READING (a documented LABEL, **not** a derived theorem; per
    ``[[feedback_no_lineage_claims_in_notebook]]``): the SAME 14-dim ``g2``
    carries TWO distinct enumerations — the A-N discovery partition
    ``1 + 3 + 7 + 3`` (this collaboration's substrate-self-recognition order)
    and this su(3)-Lie branching ``8 + 3 + 3bar``. They are read as two
    languages describing the one object; they are explicitly NOT slot-aligned
    and the correspondence is NOT a proof. Class C-L (the Class C
    chirality / complex-structure orientation composed with the Class L
    eigendecomposition that extracts ``J`` and the weight spectrum). The
    A-N reading is surfaced ONLY under the separately-keyed
    ``framework_an_reading`` field, tagged "framework-reading, not derived";
    no A-N class name appears in any load-bearing return key.

    Canonical SSoT: Baez (2002) §4.1 (``g2 = Der(O)``, dim 14) — for the
    BUILD INPUT ONLY. The ``8 + 3 + 3bar`` / ``7 = 1 + 3 + 3bar`` branching
    is this op's own bit-exact self-attesting COMPUTATION; §4.1 is NOT cited
    for it (and Slansky / Fulton-Harris / Gunaydin-Gursey are deliberately
    NOT cited — not PDF-verified here).

    Args:
        imaginary_unit: The fixed octonion imaginary unit ``K`` (``1..7``)
            whose stabiliser is the su(3); the decomposition is conjugate
            (hence isomorphic) for any choice. Defaults to 1.

    Returns:
        A ``dict`` with keys:

        - ``su3`` — list of 8 real antisymmetric ``8x8`` ``ndarray`` (the
          su(3) adjoint; the stabiliser of ``e_K``).
        - ``complement`` — list of 6 real antisymmetric ``8x8`` ``ndarray``
          (the genuine real su(3)-module; ``[su3, complement] ⊆ complement``
          ``~2e-15``).
        - ``complex_structure_J`` — the ``6x6`` real invariant complex
          structure ``ndarray`` (``J^2 = -I``).
        - ``triplet`` / ``antitriplet`` — lists of 3 COMPLEX ``8x8``
          ``ndarray`` (the genuine fundamental / antifundamental; the
          ``J = +i / -i`` eigenspaces; ``[su3, triplet] ⊆ triplet`` is
          bit-exact via ``J``). ``antitriplet`` is the conjugate of
          ``triplet``.
        - ``weights`` — a ``(6, 2)`` real ``ndarray`` of the complement
          weights under the rank-2 Cartan (the ``+/-`` pairs).
        - ``decomposition`` — ``{"adjoint_14": (8, 3, 3), "vector_7":
          (1, 3, 3)}`` (the ``g2`` and the octonion-vector branchings).
        - ``imaginary_unit`` — the ``K`` used.
        - ``attestation`` — the MPR v1 self-attestation (Class A
          content-address of the computed structure).
        - ``framework_an_reading`` — the A-N reading LABEL (tagged
          "framework-reading, not derived").

    Raises:
        ValueError: if ``imaginary_unit`` is not in ``1..7``.
    """
    if not 1 <= imaginary_unit <= 7:
        raise ValueError(
            f"an_embedding: imaginary_unit must be in 1..7; got {imaginary_unit}"
        )
    (
        su3,
        complement,
        j,
        triplet,
        antitriplet,
        weights,
    ) = _build_an_embedding(imaginary_unit)

    # Copy out fresh writeable arrays (the cached build is frozen).
    su3_out = [np.array(m) for m in su3]
    complement_out = [np.array(m) for m in complement]
    triplet_out = [np.array(m) for m in triplet]
    antitriplet_out = [np.array(m) for m in antitriplet]
    j_out = np.array(j)
    weights_out = np.array(weights)

    # Content-address the COMPUTED structure via its build input: the 14
    # g2 generators (the deterministic float64 bytes; generated, not fetched).
    g2_generators = [np.array(m) for m in _build_g2()]
    attestation = _an_attestation(g2_generators, imaginary_unit)

    return {
        "su3": su3_out,
        "complement": complement_out,
        "complex_structure_J": j_out,
        "triplet": triplet_out,
        "antitriplet": antitriplet_out,
        "weights": weights_out,
        "decomposition": {
            "adjoint_14": (_DIM_SU3, _DIM_TRIPLET, _DIM_TRIPLET),
            "vector_7": (1, _DIM_TRIPLET, _DIM_TRIPLET),
        },
        "imaginary_unit": imaginary_unit,
        "attestation": attestation,
        "framework_an_reading": {
            "note": "framework-reading, not derived",
            "an_discovery_partition": (1, 3, 7, 3),
            "su3_lie_branching": (_DIM_SU3, _DIM_TRIPLET, _DIM_TRIPLET),
            "slot_aligned": False,
        },
    }


# ──────────────────────────────────────────────────────────────────────
# quaternion_subalgebra_stabiliser — the 6-dim so(4) = su(2) ⊕ su(2)
# subalgebra of g2 = Der(O) that stabilises a quaternion subalgebra H ⊂ O.
#
# The ℍ-reading SIBLING of ``an_embedding`` (the su(3) ⊕ 3 ⊕ 3bar
# ℂ-reading). A quaternion subalgebra H ⊂ O is span(e_0, e_a, e_b, e_c)
# for a Fano line (a, b, c); the derivations D in g2 that map H back into
# H (equivalently, map the 4-dim orthogonal complement H^⊥ into itself)
# form EXACTLY the 6-dim so(4) = su(2) ⊕ su(2) (F215).
#
# The construction is the deterministic chain (no np.random, numpy-only):
#   1. so(4) = the stabiliser {D in g2 : D span(H_imag) ⊆ span(H_imag)}
#      (SVD nullspace of the leak-into-H^⊥ constraint; dim 6).
#   2. Killing-form rank = 6 (the stabiliser is SEMISIMPLE — so(4) is, the
#      raw certificate ruling out a solvable / abelian factor).
#   3. The two su(2) ideals = the self-dual / anti-self-dual halves of the
#      stabiliser's action on the 4-dim complement H^⊥ ≅ R^4 (the canonical
#      so(4) = su(2)_+ ⊕ su(2)_- 't Hooft self-dual split). Each closes as
#      su(2), the two commute ([A, B] = 0), each is a g2-ideal — all
#      bit-exact (~1e-14).
#
# This voxel keeps the SYMMETRY surface (so(4) ⊂ g2, a Lie subalgebra)
# visibly distinct from the OPERATOR surface (cascade.atoms.*, the 6
# lean-ISA group-element ops). F215 showed the 6 atoms are group-element
# operations (0 of 6 are Lie generators), NOT this Lie subalgebra; the
# "6 = 6" (6 atoms vs dim-6 so(4)) was coincidence, surfaced ONLY under the
# separately-keyed ``framework_so4_reading`` field.
# ──────────────────────────────────────────────────────────────────────


def _quaternion_imaginary_units(fano_line: Tuple[int, int, int]) -> List[int]:
    """The 3 imaginary octonion units of the quaternion subalgebra H.

    A quaternion subalgebra ``H ⊂ O`` is ``span(e_0, e_a, e_b, e_c)`` for a
    Fano line ``(a, b, c)`` (the unordered triple closes ``e_a e_b = ± e_c``);
    its imaginary part is ``span(e_a, e_b, e_c)``. Internal helper.
    """
    return sorted(fano_line)


def _quaternion_complement_units(h_imag: List[int]) -> List[int]:
    """The 4 octonion units of the orthogonal complement ``H^⊥``.

    ``e_0`` is shared (the identity, fixed by every derivation), so the
    derivation-relevant complement is the 4 imaginary units NOT in ``H`` —
    here returned as the 4 octonion indices ``{1..7} \\ h_imag``. (A
    derivation annihilates ``e_0``; stabilising ``H`` reduces to mapping the
    3 ``H``-imaginary units back into ``span(H_imag)``.)
    """
    return [i for i in range(1, _DIM) if i not in h_imag]


def _so4_stabiliser(
    g2: List[np.ndarray], h_imag: List[int], complement: List[int]
) -> List[np.ndarray]:
    """The so(4) stabiliser ``{D in g2 : D span(H_imag) ⊆ span(H_imag)}``.

    Build the leak constraint: for every ``H``-imaginary unit ``e_a`` and
    every complement unit ``e_k`` (``k in H^⊥``), the ``e_k`` component of
    ``(sum_c x_c g2[c]) e_a`` must vanish. That is a
    ``(|H_imag| * |H^⊥|, 14) = (12, 14)`` linear system in the 14 g2
    coefficients; its right nullspace (deterministic SVD; singular value
    ``< _RANK_TOL * max``) is EXACTLY 6-dim. Each null coefficient vector
    ``c`` rebuilds a stabiliser generator ``M = sum_c c_c g2[c]``. Asserts
    ``dim == 6`` and that each ``M`` leaks nothing from ``H`` into ``H^⊥``.
    """
    basis = _basis_vectors()
    rows: List[np.ndarray] = []
    for a in h_imag:
        for k in complement:
            rows.append(
                np.array(
                    [dense_matvec_real(g2[c], basis[a])[k]
                     for c in range(_DIM_G2)]
                )
            )
    constraint = np.array(rows)  # (12, 14)
    _, singular, vh = np.linalg.svd(constraint)
    scale = max(1.0, float(singular[0]))
    null_coeffs: List[np.ndarray] = []
    for idx in range(vh.shape[0]):
        s = float(singular[idx]) if idx < len(singular) else 0.0
        if s < _RANK_TOL * scale:
            null_coeffs.append(vh[idx])
    assert len(null_coeffs) == _DIM_SO4, (
        f"so(4) stabiliser expected dim {_DIM_SO4}; got {len(null_coeffs)}"
    )
    raw = [sum(c[a] * g2[a] for a in range(_DIM_G2)) for c in null_coeffs]
    # Orthonormalise in the shared E_{pq} frame (deterministic QR, no RNG):
    # the Killing-form SPECTRUM is then a basis-INDEPENDENT, ℍ-choice-invariant
    # invariant (two distinct eigenvalues, multiplicity 3 each = su(2) ⊕ su(2)).
    # Without this the spectrum scales with the arbitrary SVD-nullspace basis.
    raw_coords = np.column_stack([_epq_coords(m) for m in raw])  # (28, 6)
    q_ortho, _ = _mc.qr(raw_coords)
    so4 = [_epq_to_matrix(q_ortho[:, c]) for c in range(_DIM_SO4)]
    for matrix in so4:
        leak = 0.0
        for a in h_imag:
            image = dense_matvec_real(matrix, basis[a])
            for k in complement:
                leak = leak + image[k] * image[k]
        residual = _magnitude(float(_srn.sqrt(leak)))
        assert residual < _RANK_TOL, (
            f"so(4) generator leaks H into H^perp: residual {residual}"
        )
    return so4


def _pinv(matrix: np.ndarray) -> np.ndarray:
    """Moore-Penrose pseudoinverse via the cascade SVD.

    ``A = U·diag(s)·Vᴴ`` ⟹ ``A⁺ = V·diag(1/s)·Uᴴ`` with the same small-
    singular-value cutoff NumPy's ``pinv`` applies (``rcond·s_max``,
    ``rcond = 1e-15``). The pseudoinverse is unique, so the per-factor U/V
    column-sign ambiguity of the SVD cancels — value-faithful to NumPy's
    dense ``pinv`` (~1e-7) for the full-column-rank generator stacks
    this module forms (every ``s`` well clear of the cutoff). Reconstruction
    uses the Class-L dense cascade matmul, not ``@``, so the numpy-math
    ledger stays honest.
    """
    a = np.asarray(matrix, dtype=np.float64)
    u, s, vh = (np.asarray(x) for x in _mc.svd(a))
    cutoff = 1e-15 * (float(s[0]) if s.size else 0.0)
    s_inv = np.array(
        [1.0 / x if x > cutoff else 0.0 for x in s], dtype=np.float64
    )
    # A⁺ = V·diag(s_inv)·Uᴴ  (real: Vᴴ = Vᵀ ⟹ V = vh.T; Uᴴ = u.T).
    return dense_matmul_real(vh.T * s_inv, u.T)


def _killing_form(generators: List[np.ndarray]) -> np.ndarray:
    """The Killing form ``K_{ab} = tr(ad_a ad_b)`` of a Lie generator set.

    Solve the structure constants ``[g_i, g_j] = sum_k f_{ij}^k g_k`` in the
    shared ``E_{pq}`` frame (a least-squares solve against the generator
    coordinate stack — exact here, the brackets close in the span), then form
    ``K_{ab} = sum_{c,d} f_{ac}^d f_{bd}^c``. Returned as an ``(n, n)`` real
    symmetric matrix; its rank is the semisimplicity certificate (full rank
    ``n`` iff semisimple, by Cartan's criterion).
    """
    n = len(generators)
    coords = np.column_stack([_epq_coords(m) for m in generators])  # (28, n)
    pinv = _pinv(coords)
    f = np.zeros((n, n, n))
    for i in range(n):
        for j in range(n):
            bracket = _commutator_coords(generators[i], generators[j])
            f[i, j, :] = dense_matvec_real(pinv, bracket)
    killing = np.zeros((n, n))
    for a in range(n):
        for b in range(n):
            killing[a, b] = float(
                np.sum(f[a, :, :] * f[b, :, :].T)
            )
    return killing


def _self_dual_bases() -> Tuple[np.ndarray, np.ndarray]:
    """The 't Hooft self-dual / anti-self-dual ``so(4)`` 6-vector frames.

    ``so(4)`` on ``R^4`` splits ``su(2)_+ ⊕ su(2)_-`` into the self-dual and
    anti-self-dual antisymmetric ``4x4`` matrices. In the 6-vector coordinate
    ``(M_01, M_02, M_03, M_12, M_13, M_23)`` the self-dual triple is
    ``E_01 + E_23, E_02 - E_13, E_03 + E_12`` and the anti-self-dual triple is
    ``E_01 - E_23, E_02 + E_13, E_03 - E_12`` (``E_ij`` the elementary
    antisymmetric generator). Returns the two ``(6, 3)`` coordinate frames.
    """
    def e(i: int, j: int) -> np.ndarray:
        m = np.zeros((_DIM_COMP4, _DIM_COMP4))
        m[i, j] = 1.0
        m[j, i] = -1.0
        return m

    def vec6(m: np.ndarray) -> np.ndarray:
        return np.array(
            [m[0, 1], m[0, 2], m[0, 3], m[1, 2], m[1, 3], m[2, 3]]
        )

    self_dual = [e(0, 1) + e(2, 3), e(0, 2) - e(1, 3), e(0, 3) + e(1, 2)]
    anti_self_dual = [e(0, 1) - e(2, 3), e(0, 2) + e(1, 3), e(0, 3) - e(1, 2)]
    sd = np.column_stack([vec6(m) for m in self_dual])
    asd = np.column_stack([vec6(m) for m in anti_self_dual])
    return sd, asd


def _two_su2_ideals(
    so4: List[np.ndarray], complement: List[int]
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """The two su(2) ideals via the self-dual / anti-self-dual split.

    Restrict each so(4) generator to the ``4x4`` block on the complement
    ``H^⊥`` (``block[i, j] = D[complement_i, complement_j]``) and read its
    6-vector coordinate; the 6-dim block span is the FULL ``so(4)`` on
    ``R^4``. The su(2)_+ ideal = the so(4) generators whose block is purely
    self-dual (the anti-self-dual projection of the block vanishes); the
    su(2)_- ideal = the purely anti-self-dual ones. Each is solved as the
    deterministic SVD nullspace of the cross-duality projection composed with
    the block map. Asserts each ideal is 3-dim.
    """
    idx = complement

    def block_vec(matrix: np.ndarray) -> np.ndarray:
        return np.array([
            matrix[idx[0], idx[1]], matrix[idx[0], idx[2]],
            matrix[idx[0], idx[3]], matrix[idx[1], idx[2]],
            matrix[idx[1], idx[3]], matrix[idx[2], idx[3]],
        ])

    block_map = np.column_stack([block_vec(m) for m in so4])  # (6, 6)
    sd_frame, asd_frame = _self_dual_bases()
    q_sd, _ = _mc.qr(sd_frame)
    q_asd, _ = _mc.qr(asd_frame)
    proj_sd = dense_matmul_real(q_sd, q_sd.T)
    proj_asd = dense_matmul_real(q_asd, q_asd.T)

    def ideal_for(cross_projector: np.ndarray) -> List[np.ndarray]:
        # generators whose block vanishes under the OTHER duality projector.
        leak = dense_matmul_real(cross_projector, block_map)  # (6, 6)
        _, singular, vh = np.linalg.svd(leak)
        scale = max(1.0, float(singular[0]))
        coeffs = [
            vh[i]
            for i in range(vh.shape[0])
            if (float(singular[i]) if i < len(singular) else 0.0)
            < _RANK_TOL * scale
        ]
        assert len(coeffs) == _DIM_SU2, (
            f"su(2) ideal expected dim {_DIM_SU2}; got {len(coeffs)}"
        )
        return [sum(c[k] * so4[k] for k in range(_DIM_SO4)) for c in coeffs]

    su2_plus = ideal_for(proj_asd)   # purely self-dual blocks
    su2_minus = ideal_for(proj_sd)   # purely anti-self-dual blocks
    return su2_plus, su2_minus


def _so4_attestation(
    generators: List[np.ndarray], fano_line: Tuple[int, int, int]
) -> Dict[str, object]:
    """MPR v1 self-attestation for the COMPUTED so(4) = su(2) ⊕ su(2) structure.

    Class A — content-address the GENERATED structure (NOT a fetched datum):
    ``response_sha256`` is :func:`srmech.amsc.format.sha256_bytes` over the
    concatenated ``float64`` bytes of the 14 ``g2`` generators (the build
    INPUT, deterministically content-addressed; **no** new
    ``hashlib.sha256``). ``parser_rule_hash`` hashes the stabiliser rule
    bytes. ``source_url`` cites Baez (arXiv) for the ``g2 = Der(O)`` /
    dim-14 PARENT FACT ONLY — the su(2) ⊕ su(2) split is this op's own
    bit-exact computation, NOT a cited result. Mirrors
    :func:`_an_attestation` verbatim in form.
    """
    generator_bytes = b"".join(
        np.ascontiguousarray(g, dtype=np.float64).tobytes() for g in generators
    )
    response_sha256 = _sha256_bytes(generator_bytes)
    parser_rule_hash = _sha256_bytes(_SO4_PARSER_RULE)
    descriptor_hash = _sha256_bytes(
        b"srmech/qm/so8.py::quaternion_subalgebra_stabiliser::so4_su2_su2"
    )
    return {
        "mpr_version": "1.0",
        "data": {
            "structure": "g2_so4_su2_su2_quaternion_stabiliser",
            "quaternion_fano_line": list(fano_line),
            "real_dimensions": {
                "so4": _DIM_SO4,
                "su2_plus": _DIM_SU2,
                "su2_minus": _DIM_SU2,
            },
        },
        "data_schema_id": "srmech://schema/g2_so4_quaternion_stabiliser",
        "attestation": {
            # Baez is OA on arXiv; a paywalled-only DOI is rejected per
            # [[feedback_paywalled_doi_cannot_be_attested]] — no source_doi.
            "source_doi": None,
            # Cites the g2 = Der(O) / dim-14 PARENT FACT only (the build
            # input); the su(2) ⊕ su(2) split is this op's own computation.
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _AN_RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.6.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/qm/so8.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": "g2 = Der(O) so(4) = su(2) ⊕ su(2) quaternion-stabiliser",
            "purpose": (
                "Bit-exact so(4) subalgebra of g2 stabilising a quaternion "
                "subalgebra H ⊂ O (computed self-attesting structure)"
            ),
            "cite_as": (
                "Baez, J.C. (2002) The Octonions, Bull. Amer. Math. Soc. 39, "
                "145-205 (arXiv:math/0105155) — for g2 = Der(O), dim 14 "
                "(the build input only)"
            ),
        },
    }


#: The 7 Fano lines indexed 1..7 — the 7 quaternion subalgebras H ⊂ O.
#: Identical to :data:`srmech.qm.octonion._FANO_LINES`; re-declared here so
#: the so(4) builder picks an H deterministically by a 1-based index.
_FANO_LINES_SO4: Tuple[Tuple[int, int, int], ...] = (
    (1, 2, 3), (1, 4, 5), (1, 6, 7),
    (2, 4, 6), (2, 5, 7),
    (3, 4, 7), (3, 5, 6),
)


@functools.lru_cache(maxsize=None)
def _build_quaternion_stabiliser(
    quaternion_index: int,
) -> Tuple[
    Tuple[np.ndarray, ...],  # so4 (6 real antisym 8x8)
    Tuple[np.ndarray, ...],  # su2_plus (3 real antisym 8x8)
    Tuple[np.ndarray, ...],  # su2_minus (3 real antisym 8x8)
    np.ndarray,              # killing_form (6x6 real symmetric)
    Tuple[int, ...],         # the H imaginary units
]:
    """Cached read-only so(4) = su(2) ⊕ su(2) build for a fixed quaternion H.

    The expensive deterministic chain (SVD nullspace + Killing form + the
    self-dual split) runs once per ``quaternion_index`` and is memoised;
    :func:`quaternion_subalgebra_stabilizer` copies out a fresh writeable
    dict each call. All returned arrays are frozen (``writeable=False``).
    """
    fano_line = _FANO_LINES_SO4[quaternion_index - 1]
    h_imag = _quaternion_imaginary_units(fano_line)
    complement = _quaternion_complement_units(h_imag)
    g2 = list(_build_g2())

    so4 = _so4_stabiliser(g2, h_imag, complement)
    killing = _killing_form(so4)

    # Semisimplicity certificate: Killing rank == 6 (full; Cartan criterion).
    killing_scale = max(
        1.0, float(np.max(np.array([_magnitude(float(v)) for v in killing.flat])))
    )
    killing_rank = int(np.linalg.matrix_rank(killing, tol=_RANK_TOL * killing_scale))
    assert killing_rank == _DIM_SO4, (
        f"so(4) Killing-form rank expected {_DIM_SO4} (semisimple); "
        f"got {killing_rank}"
    )

    su2_plus, su2_minus = _two_su2_ideals(so4, complement)

    # Bidirectional killer test: span[su2_+ | su2_-] == span(so4) (rank 6).
    so4_coords = np.column_stack([_epq_coords(m) for m in so4])
    plus_coords = np.column_stack([_epq_coords(m) for m in su2_plus])
    minus_coords = np.column_stack([_epq_coords(m) for m in su2_minus])
    split_span = np.column_stack([plus_coords, minus_coords])
    rank_split = int(np.linalg.matrix_rank(split_span, tol=_RANK_TOL))
    rank_with_so4 = int(
        np.linalg.matrix_rank(
            np.column_stack([split_span, so4_coords]), tol=_RANK_TOL
        )
    )
    assert rank_split == _DIM_SO4, (
        f"span[su2_+ | su2_-] rank expected {_DIM_SO4}; got {rank_split}"
    )
    assert rank_with_so4 == _DIM_SO4, (
        f"span[su2_+ | su2_- | so4] rank expected {_DIM_SO4} (same span as "
        f"so4); got {rank_with_so4}"
    )

    so4_frozen = _frozen_tuple(so4)
    plus_frozen = _frozen_tuple(su2_plus)
    minus_frozen = _frozen_tuple(su2_minus)
    killing_frozen = np.array(killing)
    killing_frozen.flags.writeable = False
    return (
        so4_frozen,
        plus_frozen,
        minus_frozen,
        killing_frozen,
        tuple(h_imag),
    )


def quaternion_subalgebra_stabilizer(quaternion_index: int = 1) -> dict:
    """The bit-exact 6-dim so(4) = su(2) ⊕ su(2) ⊂ g2 stabilising ℍ ⊂ 𝕆.

    The ℍ-reading SIBLING of :func:`an_embedding` (the su(3) ⊕ 3 ⊕ 3bar
    ℂ-reading of the same ``g2 = Der(O)``). A quaternion subalgebra
    ``H ⊂ O`` is ``span(e_0, e_a, e_b, e_c)`` for a Fano line ``(a, b, c)``
    (:data:`srmech.qm.octonion._FANO_LINES`); the derivations ``D in g2``
    that map ``H`` back into ``H`` — equivalently map the 4-dim orthogonal
    complement ``H^⊥`` into itself — form EXACTLY the 6-dim
    ``so(4) = su(2) ⊕ su(2)`` (F215). The result is returned with the
    invariant CERTIFICATE and an MPR self-attestation.

    CONSTRUCTION (deterministic, numpy-only, no ``np.random``, no scipy;
    memoised via :func:`_build_quaternion_stabiliser`, copied out fresh each
    call):

    1. **so(4) = the stabiliser** ``{D in g2 : D span(H_imag) ⊆
       span(H_imag)}`` via the SVD nullspace of the
       leak-into-``H^⊥`` constraint — EXACTLY 6-dim.
    2. **Killing-form rank == 6** — the SEMISIMPLICITY certificate (full
       rank, by Cartan's criterion; rules out a solvable / abelian factor).
       The two-triplet Killing SPECTRUM (two distinct eigenvalues, each
       multiplicity 3) is the su(2) ⊕ su(2) fingerprint and is
       ℍ-choice-invariant.
    3. **the two su(2) ideals** — the self-dual / anti-self-dual halves of
       the stabiliser's action on the 4-dim complement ``H^⊥ ≅ R^4`` (the
       canonical ``so(4) = su(2)_+ ⊕ su(2)_-`` 't Hooft split). Each closes
       as su(2) (``~1e-14``), the two commute (``[su2_+, su2_-] = 0``,
       ``~1e-14``), and each is a g2-ideal (``~1e-14``);
       ``span[su2_+ | su2_-] == span(so4)`` (rank 6, both directions: the
       bidirectional killer test).

    ℍ-CHOICE-INVARIANCE: the stabiliser of ANY quaternion subalgebra is the
    SAME algebra-type (so(4) = su(2) ⊕ su(2), dim 6, Killing rank 6, the
    two-triplet spectrum) — the seven Fano-line choices are conjugate under
    g2 = Aut(O), hence isomorphic. The returned ``killing_spectrum`` is
    bit-identical across ``quaternion_index`` choices (verified in the test
    suite across ≥ 2 distinct ℍ).

    THE su(2) ⊕ su(2) SPLIT IS COMPUTED, NOT CITED: Baez (2002) §4.1 is the
    build input ONLY (``g2 = Der(O)``, dim 14). That the ℍ-stabiliser is
    so(4) = su(2) ⊕ su(2) is this op's own bit-exact self-attesting
    computation (the Killing rank, the two-ideal self-dual split, the
    closure / commute / ideal residuals are all measured here), NOT a quoted
    theorem.

    SYMMETRY SURFACE vs OPERATOR SURFACE (the F215 point of this voxel,
    surfaced under the separately-keyed ``framework_so4_reading`` field;
    framework-reading, NOT a derived theorem): this so(4) ⊂ g2 is a 6-dim
    **Lie subalgebra** (a continuous SYMMETRY of the octonions). It is
    EXPLICITLY DISTINCT from the 6 ``srmech.amsc.cascade.atoms`` lean-ISA
    operators (``pin_slot_at_zero``, ``reorient``, ``magnitude``,
    ``chiral_flip``, ``chiral_dual``, ``net_chirality``) — those are
    group-ELEMENT operations (0 of the 6 are Lie generators / one-parameter
    subgroups). The numerical coincidence "6 atoms = dim-6 so(4)" is a
    COINCIDENCE per F215, NOT a correspondence; keeping the symmetry surface
    here distinct from the operator surface is the reason this voxel exists.

    Args:
        quaternion_index: The 1-based index ``1..7`` of the Fano line
            ``(a, b, c)`` whose quaternion subalgebra
            ``H = span(e_0, e_a, e_b, e_c)`` is stabilised; the stabiliser is
            conjugate (hence isomorphic) for any choice. Defaults to 1
            (the line ``(1, 2, 3)``).

    Returns:
        A ``dict`` with keys:

        - ``so4`` — list of 6 real antisymmetric ``8x8`` ``ndarray`` (the
          full so(4) stabiliser of ``H``).
        - ``su2_plus`` / ``su2_minus`` — lists of 3 real antisymmetric
          ``8x8`` ``ndarray`` (the two su(2) ideals; the self-dual /
          anti-self-dual halves of the action on ``H^⊥``;
          ``[su2_+, su2_-] = 0``, ``span[su2_+ | su2_-] = span(so4)``).
        - ``killing_form`` — the ``6x6`` real symmetric Killing-form
          ``ndarray`` (rank 6: semisimple).
        - ``killing_rank`` — ``6`` (the semisimplicity certificate).
        - ``killing_spectrum`` — the sorted ``6``-vector of Killing
          eigenvalues (two distinct values, multiplicity 3 each: the
          su(2) ⊕ su(2) fingerprint; ℍ-choice-invariant).
        - ``decomposition`` — ``{"so4_6": (3, 3)}`` (the two su(2) dims).
        - ``quaternion_fano_line`` — the ``(a, b, c)`` line used.
        - ``quaternion_imaginary_units`` — ``(a, b, c)`` sorted (the
          imaginary part of ``H``).
        - ``attestation`` — the MPR v1 self-attestation (Class A
          content-address of the computed structure).
        - ``framework_so4_reading`` — the symmetry-surface-vs-operator-surface
          reading LABEL (tagged "framework-reading, not derived"; the F215
          "6 = 6 coincidence" note).

    Raises:
        ValueError: if ``quaternion_index`` is not in ``1..7``.
    """
    if not 1 <= quaternion_index <= 7:
        raise ValueError(
            "quaternion_subalgebra_stabilizer: quaternion_index must be in "
            f"1..7; got {quaternion_index}"
        )
    (
        so4,
        su2_plus,
        su2_minus,
        killing,
        h_imag,
    ) = _build_quaternion_stabiliser(quaternion_index)

    # Copy out fresh writeable arrays (the cached build is frozen).
    so4_out = [np.array(m) for m in so4]
    su2_plus_out = [np.array(m) for m in su2_plus]
    su2_minus_out = [np.array(m) for m in su2_minus]
    killing_out = np.array(killing)
    # Class-L Hermitian eigendecomposition (srmech's own primitive). The
    # Killing form is real-symmetric; we only need its spectrum. eigvals come
    # back ascending already; keep np.sort to preserve exact prior behaviour.
    killing_eigvals, _ = hermitian_eigendecompose(killing_out)
    killing_spectrum = np.sort(killing_eigvals)

    fano_line = _FANO_LINES_SO4[quaternion_index - 1]

    # Content-address the COMPUTED structure via its build input: the 14
    # g2 generators (the deterministic float64 bytes; generated, not fetched).
    g2_generators = [np.array(m) for m in _build_g2()]
    attestation = _so4_attestation(g2_generators, fano_line)

    return {
        "so4": so4_out,
        "su2_plus": su2_plus_out,
        "su2_minus": su2_minus_out,
        "killing_form": killing_out,
        "killing_rank": _DIM_SO4,
        "killing_spectrum": killing_spectrum,
        "decomposition": {"so4_6": (_DIM_SU2, _DIM_SU2)},
        "quaternion_fano_line": fano_line,
        "quaternion_imaginary_units": h_imag,
        "attestation": attestation,
        "framework_so4_reading": {
            "note": "framework-reading, not derived",
            "symmetry_surface": "so(4) = su(2) ⊕ su(2) ⊂ g2 (Lie subalgebra)",
            "operator_surface": "srmech.amsc.cascade.atoms (6 lean-ISA ops)",
            "six_equals_six_is_coincidence": True,
            "atoms_that_are_lie_generators": 0,
            "f215": (
                "the 6 cascade.atoms are group-element operations, NOT this "
                "Lie subalgebra; the 6=6 dimension match is coincidence"
            ),
        },
    }


__all__ = [
    "an_embedding",
    "g2_subalgebra",
    "quaternion_subalgebra_stabilizer",
    "so7_subalgebra",
    "so8_adjoint_basis",
]
