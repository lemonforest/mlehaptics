"""Bit-exact acceptance tests for the so(8)/Spin(8) triality voxel (rc17).

The six acceptance tests prove the construction is the genuine
``D4 --(Z3 fold)--> G2`` theorem (Baez 2002 §2.4 / Cartan 1925), tying
``Fix(tau) = g2`` (dim 14) to the A-N ``1 + 3 + 7 + 3 = 14`` partition:

1. ``tau`` is order-3: ``tau^3 = I``, ``tau != I``, ``tau^2 != I``.
2. KILLER — ``Fix(tau) = g2`` (dim 14), with belt-and-suspenders rank
   asserts AND a bidirectional projection residual.
3. ``Fix(Z2 swap) = so(7)`` (dim 21).
4. Cartan-relation residual ``= 0`` over a generator-class sample.
5. rep inequivalence + cycle closure ``8v -> 8s -> 8c -> 8v``.
6. octonion convention attested + reproducible (same convention -> same tau).

ALL deviations are reduced through the **scalar** Class K pin-slot
magnitude (:func:`srmech.amsc.cascade.magnitude`) — NEVER Python ``abs()``
per ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`` — by
first reducing the matrix to a scalar Frobenius norm, then passing that
Python float to ``magnitude`` (which is scalar-only; it raises on an
ndarray).

Determinism: every basis extraction uses a deterministic rank-revealing
QR / SVD (no ``np.random``), so the killer test is reproducible.
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc.cascade import magnitude
from srmech.amsc.format import sha256_bytes
from srmech.qm import octonion, so8, triality

_TOL = 1e-9


# ----------------------------------------------------------------------
# Test helpers — scalar reductions through cascade.magnitude (no abs()).
# ----------------------------------------------------------------------


def _frob(matrix: np.ndarray) -> float:
    """Frobenius-norm deviation reduced through the scalar Class K magnitude.

    Reduce the matrix to a SCALAR float FIRST (``np.linalg.norm`` is the
    Euclidean / Frobenius norm), then pass that scalar to
    ``cascade.magnitude`` (scalar-only; raises on an ndarray). NEVER
    ``abs()``.
    """
    scalar = float(np.linalg.norm(matrix))
    return magnitude(scalar)


def _nullspace_dim(operator: np.ndarray, tol: float = _TOL) -> int:
    """Dimension of ``ker(operator - I)`` via a deterministic SVD count."""
    identity = np.eye(operator.shape[0])
    singular = np.linalg.svd(operator - identity, compute_uv=False)
    scale = max(1.0, float(singular[0]))
    return int(np.sum(singular < tol * scale))


def _coords_of(generators) -> np.ndarray:
    """Stack the E_{pq}-coords of a generator tuple as a ``(28, k)`` matrix."""
    return np.array([so8._epq_coords(g) for g in generators]).T


def _fix_space_coords(operator: np.ndarray, tol: float = _TOL) -> np.ndarray:
    """An orthonormal basis of ``ker(operator - I)`` as ``(28, k)`` columns."""
    identity = np.eye(operator.shape[0])
    _, singular, vh = np.linalg.svd(operator - identity)
    scale = max(1.0, float(singular[0]))
    columns = vh.T[:, singular < tol * scale]
    orthonormal, _ = np.linalg.qr(columns)
    return orthonormal


def _max_projection_residual(vectors: np.ndarray, onto: np.ndarray) -> float:
    """Max ``||v - P v||`` projecting each column of ``vectors`` onto ``onto``.

    Reduced through the scalar Class K magnitude (no ``abs()``).
    """
    basis, _ = np.linalg.qr(onto)
    projector = basis @ basis.T
    worst = 0.0
    for c in range(vectors.shape[1]):
        residual = float(np.linalg.norm(vectors[:, c] - projector @ vectors[:, c]))
        worst = max(worst, magnitude(residual))
    return worst


# ----------------------------------------------------------------------
# TEST 1 — tau is the order-3 outer automorphism.
# ----------------------------------------------------------------------


def test_tau_is_order_three():
    """``tau^3 = I``, ``tau != I``, ``tau^2 != I`` (the order-3 automorphism)."""
    tau = triality.triality_automorphism()
    assert tau.shape == (28, 28)
    identity = np.eye(28)
    # tau^3 = I (bit-exact to ~1e-14).
    assert _frob(tau @ tau @ tau - identity) < _TOL
    # tau != I and tau^2 != I (the order is exactly 3, not 1).
    assert _frob(tau - identity) > 1.0
    assert _frob(tau @ tau - identity) > 1.0


# ----------------------------------------------------------------------
# TEST 2 — KILLER: Fix(tau) = g2 (dim 14). Belt-and-suspenders.
# ----------------------------------------------------------------------


def test_killer_fix_tau_is_g2_dim14():
    """``Fix(tau) = g2`` (dim 14) — the D4 →Z3 G2 theorem, the A-N 1+3+7+3.

    Belt-and-suspenders so the equality is NOT rank-coincidental:

    * ``rank(g2_basis) == 14`` (the 14 derivations are independent), AND
    * ``rank(ker(tau - I)) == 14`` (the tau-fixed space has dim 14), AND
    * ``rank([g2_basis | ker(tau - I)]) == 14`` (the stacked rank does not
      grow — the two 14-dim spaces are the SAME space).

    Plus a bidirectional projection residual: ``g2 ⊆ Fix`` AND ``Fix ⊆ g2``
    (each direction's max projection residual < 1e-12).
    """
    tau = triality.triality_automorphism()
    g2 = so8.g2_subalgebra()
    assert len(g2) == 14

    g2_coords = _coords_of(g2)                 # (28, 14)
    fix_coords = _fix_space_coords(tau)        # (28, 14) orthonormal

    rank_g2 = np.linalg.matrix_rank(g2_coords, tol=_TOL)
    rank_fix = np.linalg.matrix_rank(fix_coords, tol=_TOL)
    rank_stacked = np.linalg.matrix_rank(
        np.concatenate([g2_coords, fix_coords], axis=1), tol=_TOL
    )

    # The three rank asserts (equality is forced, not coincidental).
    assert rank_g2 == 14
    assert rank_fix == 14
    assert _nullspace_dim(tau) == 14
    assert rank_stacked == 14

    # Bidirectional projection residual: each space sits inside the other.
    g2_in_fix = _max_projection_residual(g2_coords, fix_coords)
    fix_in_g2 = _max_projection_residual(fix_coords, g2_coords)
    assert g2_in_fix < 1e-12
    assert fix_in_g2 < 1e-12


# ----------------------------------------------------------------------
# TEST 3 — Fix(Z2 swap) = so(7) (dim 21). The D4 → B3 fold.
# ----------------------------------------------------------------------


def test_fix_z2_swap_is_so7_dim21():
    """``S_B^2 = I`` and ``Fix(S_B) = so(7)`` (dim 21)."""
    swap = triality.triality_swap()
    so7 = so8.so7_subalgebra()
    identity = np.eye(28)

    # Z2 involution.
    assert _frob(swap @ swap - identity) < _TOL
    # Fixed space dimension is 21 = dim so(7).
    assert _nullspace_dim(swap) == 21
    assert len(so7) == 21

    # span(ker(S_B - I)) == span(so7): stacked rank stays 21.
    so7_coords = _coords_of(so7)
    fix_coords = _fix_space_coords(swap)
    assert np.linalg.matrix_rank(so7_coords, tol=_TOL) == 21
    rank_stacked = np.linalg.matrix_rank(
        np.concatenate([so7_coords, fix_coords], axis=1), tol=_TOL
    )
    assert rank_stacked == 21


# ----------------------------------------------------------------------
# TEST 4 — Cartan relation residual = 0 over a generator-class sample.
# ----------------------------------------------------------------------


def test_cartan_relation_residual_zero():
    """``triality_relation_residual == 0`` for a g2 / L-type / R-type sample;
    and the companions of a g2 derivation are ``g_s = g_c = g_v``."""
    basis = so8.so8_adjoint_basis()
    # Partition order is 14 (g2) + 7 (L) + 7 (R).
    g2_gen = basis[0]
    l_gen = basis[14]
    r_gen = basis[21]

    for generator in (g2_gen, l_gen, r_gen):
        g_s, g_c = triality.triality_companions(generator)
        residual = triality.triality_relation_residual(generator, g_s, g_c)
        assert residual < _TOL

    # Derivations are triality-fixed: g_s = g_c = g_v for a g2 generator.
    g_s, g_c = triality.triality_companions(g2_gen)
    assert _frob(g_s - g2_gen) < _TOL
    assert _frob(g_c - g2_gen) < _TOL

    # A wrong companion pair has a NON-zero residual (the residual measures
    # something real — it is not vacuously zero).
    bad_residual = triality.triality_relation_residual(
        l_gen, np.zeros((8, 8)), np.zeros((8, 8))
    )
    assert bad_residual > _TOL


# ----------------------------------------------------------------------
# TEST 5 — rep inequivalence + cycle closure (8v -> 8s -> 8c -> 8v).
# ----------------------------------------------------------------------


def test_rep_cycle_closure_and_inequivalence():
    """``triality_cycle`` is the order-3 Class-I permutation; closure after 3;
    the three frames are inequivalent; unknown frames raise ValueError."""
    assert triality.triality_cycle("v") == "s"
    assert triality.triality_cycle("s") == "c"
    assert triality.triality_cycle("c") == "v"
    # Long-form labels are accepted and canonicalise.
    assert triality.triality_cycle("8v") == "s"

    # Cycle closure after exactly 3 steps (the order-3 element).
    assert (
        triality.triality_cycle(
            triality.triality_cycle(triality.triality_cycle("v"))
        )
        == "v"
    )

    # The three frames are DISTINCT (inequivalence at the label level — the
    # three inequivalent 8-dim irreps 8v / 8s / 8c never coincide under the
    # order-3 cycle; a single step never returns the same frame).
    for frame in ("v", "s", "c"):
        assert triality.triality_cycle(frame) != frame

    # Unknown frame strings raise a clean ValueError (not KeyError / crash).
    with pytest.raises(ValueError):
        triality.triality_cycle("a")
    with pytest.raises(ValueError):
        triality.triality_cycle("8x")


# ----------------------------------------------------------------------
# TEST 6 — octonion convention attested + reproducible.
# ----------------------------------------------------------------------


def test_octonion_convention_attested_and_reproducible():
    """The attestation hash is content-addressed over the table via
    ``sha256_bytes`` (NOT hashlib); the Fano triples match Baez §2; the
    table is byte-identical across calls; and the SAME convention yields
    the SAME tau (build tau twice -> zero deviation)."""
    att = octonion.octonion_table_attestation()
    assert att["mpr_version"] == "1.0"

    table = octonion.octonion_mult_table()
    expected_hash = sha256_bytes(table.astype(np.int8).tobytes())
    assert att["attestation"]["response_sha256"] == expected_hash

    # The attested Fano triples are exactly Baez (2002) §2.
    assert att["data"]["fano_triples"] == [
        [1, 2, 3], [1, 4, 5], [1, 6, 7],
        [2, 4, 6], [2, 5, 7],
        [3, 4, 7], [3, 5, 6],
    ]

    # The table is byte-identical across two calls (deterministic int8).
    table_again = octonion.octonion_mult_table()
    assert np.array_equal(table, table_again)
    assert table.dtype == np.int8

    # Same convention -> same tau reproducibly.
    tau_1 = triality.triality_automorphism()
    tau_2 = triality.triality_automorphism()
    assert _frob(tau_1 - tau_2) < _TOL

    # The attestation routes the hash through sha256_bytes (no hashlib): the
    # parser_rule_hash and descriptor_hash are 64-hex SHA-256 digests.
    assert len(att["attestation"]["response_sha256"]) == 64
    assert len(att["attestation"]["parser_rule_hash"]) == 64
    assert att["attestation"]["source_url"] == "https://arxiv.org/abs/math/0105155"


# ----------------------------------------------------------------------
# Supporting: the 7 imaginary-unit L/R binders are antisymmetric (so8 ⊂).
# ----------------------------------------------------------------------


def test_imaginary_unit_binders_are_antisymmetric():
    """``L_{e_i}`` and ``R_{e_i}`` (i = 1..7) are antisymmetric, hence in
    so(8). And ``octonion_norm`` is the Class K∘C norm (no abs())."""
    basis = np.eye(8)
    for i in range(1, 8):
        left = octonion.octonion_left_mult(basis[i])
        right = octonion.octonion_right_mult(basis[i])
        assert _frob(left + left.T) < _TOL    # left = -left^T
        assert _frob(right + right.T) < _TOL  # right = -right^T

    # Norm spot-checks (the Class K + Class C reduction, never abs(): the
    # scalar deviation is reduced through cascade.magnitude, as _frob does).
    assert magnitude(float(octonion.octonion_norm(basis[1]) - 1.0)) < _TOL
    assert magnitude(
        float(octonion.octonion_norm(np.array([3.0, 4.0, 0, 0, 0, 0, 0, 0])) - 5.0)
    ) < _TOL
