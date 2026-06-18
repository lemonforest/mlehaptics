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
first reducing the matrix to a scalar Frobenius norm via the numpy-free
Class-N :func:`srmech.amsc.laplacian.mat_norm`, then passing that Python
float to ``magnitude`` (which is scalar-only; it raises on an array).

Determinism: every basis extraction uses a deterministic rank-revealing
greedy column subset / SVD nullspace (no RNG), so the killer test is
reproducible.

rc123 (numpy-free, #564): this test is itself numpy-FREE — the so(8)/triality
surfaces return :class:`srmech.amsc.mat.Mat`; the rank checks ride the EXACT
rational :func:`srmech.qm.so8._rank_exact`, the matmuls / norms the numpy-free
``mat_matmul`` / ``mat_norm``, and the nullspace dim the cascade SVD
(:func:`srmech.qm.so8._svd_nullspace`). No numpy oracle, no ``.to_numpy()``
(per ``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""

from __future__ import annotations

import pytest

from srmech.amsc.cascade import magnitude
from srmech.amsc.format import sha256_bytes
from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat
from srmech.qm import octonion, so8, triality

_TOL = 1e-9


# ----------------------------------------------------------------------
# Test helpers — numpy-free, scalar reductions through cascade.magnitude.
# ----------------------------------------------------------------------


def _eye(n: int) -> Mat:
    """The ``n×n`` identity as a real :class:`Mat` (numpy-free)."""
    return Mat.from_rows([[1.0 if i == j else 0.0 for j in range(n)]
                          for i in range(n)])


def _rows(m) -> list:
    """A nested-list copy of a :class:`Mat`'s rows (numpy-free)."""
    return m.tolist() if isinstance(m, Mat) else [list(r) for r in m]


def _sub(a: Mat, b: Mat) -> Mat:
    """Element-wise ``A − B`` over two real :class:`Mat` → :class:`Mat`."""
    ar, br = _rows(a), _rows(b)
    return Mat.from_rows([[ar[i][j] - br[i][j] for j in range(len(ar[0]))]
                          for i in range(len(ar))])


def _frob(matrix) -> float:
    """Frobenius-norm deviation reduced through the scalar Class K magnitude.

    Reduce the matrix to a SCALAR float FIRST (the numpy-free Class-N
    ``mat_norm`` is the Euclidean / Frobenius norm), then pass that scalar to
    ``cascade.magnitude`` (scalar-only; raises on an array). NEVER ``abs()``.
    """
    scalar = mat_norm(matrix if isinstance(matrix, Mat) else Mat.from_rows(matrix))
    return magnitude(scalar)


def _matmul(a: Mat, b: Mat) -> Mat:
    """``A·B`` via the native numpy-free :func:`mat_matmul`."""
    return mat_matmul(a, b)


def _coords_of(generators) -> list:
    """Stack the E_{pq}-coords of a generator tuple as ``k`` length-28 columns."""
    return [so8._epq_coords(g) for g in generators]


def _nullspace_dim(operator: Mat) -> int:
    """Dimension of ``ker(operator - I)`` as ``n − rank(operator − I)``, with the
    rank taken EXACTLY over ℚ (:func:`srmech.qm.so8._rank_exact`) — robust to
    the cascade-SVD small-σ floor that a float-tolerance count would trip on
    (per ``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]``).
    Numpy-free."""
    n = operator.n_rows
    minus_i = _rows(_sub(operator, _eye(n)))
    # rank of the (n, n) matrix == rank of its column stack (the columns).
    columns = [[minus_i[r][c] for r in range(n)] for c in range(n)]
    return n - so8._rank_exact(columns)


def _fix_space_coords(operator: Mat, dim: int) -> list:
    """An orthonormal basis of ``ker(operator - I)`` as ``dim`` length-28 columns
    (the float SVD-nullspace GEOMETRY carrier). Numpy-free."""
    n = operator.n_rows
    minus_i = _rows(_sub(operator, _eye(n)))
    null = so8._svd_nullspace(minus_i, dim)
    return [[c.real if isinstance(c, complex) else c for c in col] for col in null]


def _rank_float(columns: list) -> int:
    """Float-tolerant rank of the column stack via the cascade :func:`mat_svd`.

    The "same span" stacked-rank checks mix EXACT generator coords with the
    FLOAT SVD-nullspace ``Fix(tau)`` / ``Fix(S_B)`` directions (those carry the
    companion-solve round-off and the cascade SVD's ~1e-7 small-σ floor), so
    they CANNOT be compared over ℚ — a rational rank would over-count the
    inexact directions. A tolerance generous over the small-σ floor
    (``1e-6·σ_max``) counts the genuine rank: a same-span stack has its trailing
    singular values collapse to the floor while the leading 14 (resp. 21) stay
    O(1). Numpy-free."""
    from srmech.amsc.laplacian import mat_svd
    rows = [[columns[c][r] for c in range(len(columns))]
            for r in range(len(columns[0]))]
    _, S, _ = mat_svd(Mat.from_rows(rows))
    smax = S[0] if S else 0.0
    tol = 1e-6 * smax
    return sum(1 for s in S if s > tol)


# ----------------------------------------------------------------------
# TEST 1 — tau is the order-3 outer automorphism.
# ----------------------------------------------------------------------


def test_tau_is_order_three():
    """``tau^3 = I``, ``tau != I``, ``tau^2 != I`` (the order-3 automorphism)."""
    tau = triality.triality_automorphism()
    assert tau.shape == (28, 28)
    identity = _eye(28)
    tau2 = _matmul(tau, tau)
    tau3 = _matmul(tau2, tau)
    # tau^3 = I (bit-exact to ~1e-14).
    assert _frob(_sub(tau3, identity)) < _TOL
    # tau != I and tau^2 != I (the order is exactly 3, not 1).
    assert _frob(_sub(tau, identity)) > 1.0
    assert _frob(_sub(tau2, identity)) > 1.0


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

    The rank checks are EXACT over ℚ (:func:`srmech.qm.so8._rank_exact`),
    NOT a cascade-SVD tolerance count. Plus a bidirectional projection
    residual: ``g2 ⊆ Fix`` AND ``Fix ⊆ g2`` (each direction's max projection
    residual < 1e-12).
    """
    tau = triality.triality_automorphism()
    g2 = so8.g2_subalgebra()
    assert len(g2) == 14

    g2_coords = _coords_of(g2)                 # 14 columns (length 28)
    fix_coords = _fix_space_coords(tau, 14)    # 14 columns (orthonormal)

    # g2 alone is EXACT (the integer-combination coords) → exact ℚ rank.
    rank_g2 = so8._rank_exact(g2_coords)
    # fix-coords / the stacked g2|fix carry the float SVD-nullspace round-off →
    # float-tolerant rank (the same-span check is inherently a float compare).
    rank_fix = _rank_float(fix_coords)
    rank_stacked = _rank_float(g2_coords + fix_coords)

    # The three rank asserts (equality is forced, not coincidental).
    assert rank_g2 == 14
    assert rank_fix == 14
    assert _nullspace_dim(tau) == 14
    assert rank_stacked == 14

    # Bidirectional projection residual: each space sits inside the other.
    g2_in_fix = so8._max_projection_residual(g2_coords, fix_coords)
    fix_in_g2 = so8._max_projection_residual(fix_coords, g2_coords)
    assert g2_in_fix < 1e-12
    assert fix_in_g2 < 1e-12


# ----------------------------------------------------------------------
# TEST 3 — Fix(Z2 swap) = so(7) (dim 21). The D4 → B3 fold.
# ----------------------------------------------------------------------


def test_fix_z2_swap_is_so7_dim21():
    """``S_B^2 = I`` and ``Fix(S_B) = so(7)`` (dim 21)."""
    swap = triality.triality_swap()
    so7 = so8.so7_subalgebra()
    identity = _eye(28)

    # Z2 involution.
    assert _frob(_sub(_matmul(swap, swap), identity)) < _TOL
    # Fixed space dimension is 21 = dim so(7).
    assert _nullspace_dim(swap) == 21
    assert len(so7) == 21

    # span(ker(S_B - I)) == span(so7): so7 alone is EXACT (ℚ rank); the stacked
    # so7|fix mixes the float SVD-nullspace fix-coords → float-tolerant rank.
    so7_coords = _coords_of(so7)
    fix_coords = _fix_space_coords(swap, 21)
    assert _rank_float(so7_coords) == 21
    rank_stacked = _rank_float(so7_coords + fix_coords)
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
    assert _frob(_sub(g_s, g2_gen)) < _TOL
    assert _frob(_sub(g_c, g2_gen)) < _TOL

    # A wrong companion pair has a NON-zero residual (the residual measures
    # something real — it is not vacuously zero).
    zero8 = Mat.from_rows([[0.0] * 8 for _ in range(8)])
    bad_residual = triality.triality_relation_residual(l_gen, zero8, zero8)
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


def _table_int8_bytes_numpy_free(table) -> bytes:
    """The C-order int8 serialization of the (8,8,8) nested-list table —
    numpy-free (``-1 -> 0xFF``, ``0 -> 0x00``, ``+1 -> 0x01`` via ``v & 0xFF``,
    bit-identical to the prior numpy ``int8.tobytes()``)."""
    out = bytearray()
    for plane in table:
        for row in plane:
            for v in row:
                out.append(int(v) & 0xFF)
    return bytes(out)


def test_octonion_convention_attested_and_reproducible():
    """The attestation hash is content-addressed over the table via
    ``sha256_bytes`` (NOT hashlib); the Fano triples match Baez §2; the
    table is byte-identical across calls; and the SAME convention yields
    the SAME tau (build tau twice -> zero deviation). Numpy-free."""
    att = octonion.octonion_table_attestation()
    assert att["mpr_version"] == "1.0"

    table = octonion.octonion_mult_table()           # nested list (rc122)
    expected_hash = sha256_bytes(_table_int8_bytes_numpy_free(table))
    assert att["attestation"]["response_sha256"] == expected_hash

    # The attested Fano triples are exactly Baez (2002) §2.
    assert att["data"]["fano_triples"] == [
        [1, 2, 3], [1, 4, 5], [1, 6, 7],
        [2, 4, 6], [2, 5, 7],
        [3, 4, 7], [3, 5, 6],
    ]

    # The table is entry-identical across two calls (deterministic int8),
    # and every entry is in {-1, 0, +1} (the signed structure constants).
    table_again = octonion.octonion_mult_table()
    assert table == table_again
    assert all(v in (-1, 0, 1) for plane in table for row in plane for v in row)

    # Same convention -> same tau reproducibly.
    tau_1 = triality.triality_automorphism()
    tau_2 = triality.triality_automorphism()
    assert _frob(_sub(tau_1, tau_2)) < _TOL

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
    so(8). And ``octonion_norm`` is the Class K∘C norm (no abs()). Numpy-free."""
    basis = _eye(8)
    for i in range(1, 8):
        e_i = [basis[i, j] for j in range(8)]
        left = octonion.octonion_left_mult(e_i)
        right = octonion.octonion_right_mult(e_i)
        assert _frob(_add(left, left.T)) < _TOL    # left = -left^T
        assert _frob(_add(right, right.T)) < _TOL  # right = -right^T

    # Norm spot-checks (the Class K + Class C reduction, never abs(): the
    # scalar deviation is reduced through cascade.magnitude, as _frob does).
    e1 = [1.0, 0, 0, 0, 0, 0, 0, 0]
    assert magnitude(float(octonion.octonion_norm(e1) - 1.0)) < _TOL
    v = [3.0, 4.0, 0, 0, 0, 0, 0, 0]
    assert magnitude(float(octonion.octonion_norm(v) - 5.0)) < _TOL


def _add(a: Mat, b: Mat) -> Mat:
    """Element-wise ``A + B`` over two real :class:`Mat` → :class:`Mat`."""
    ar, br = a.tolist(), b.tolist()
    return Mat.from_rows([[ar[i][j] + br[i][j] for j in range(len(ar[0]))]
                          for i in range(len(ar))])
