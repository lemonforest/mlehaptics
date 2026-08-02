"""Bit-exact acceptance tests for the so(9)/Spin(9) rung (rc323, task #945).

One Cayley-Dickson step above the so(8)/triality voxel
(:mod:`srmech.physics.qm.so8` / :mod:`srmech.physics.qm.triality`). The tests prove, all
bit-exact and numpy-free:

1. ``so(9)`` adjoint (vector rep) — 36 antisymmetric ``9x9``, rank exactly 36.
2. The 16-dim real spinor ``Δ₉`` — 9 symmetric ``16x16`` Clifford ``Γ`` with
   ``{Γ_a, Γ_b} = 2 δ_{ab} I`` (residual 0), recomputed independently here.
3. The 36 spin(9) spinor generators ``Σ = ¼[Γ, Γ]`` — antisymmetric, rank 36,
   satisfying the ``so(9)`` structure constants.
4. The ``Spin(8) ⊂ Spin(9)`` branching ``16 = 8_s ⊕ 8_c`` — block-diagonal,
   ``Γ_8`` commutes, ``28 + 28`` half-spinor ranks, distinct actions,
   attested.
5. The associator ↔ Spin(9)-holonomy conjecture — verdict PARTIAL, tiered
   honestly (RECOGNIZED carrier / DERIVED g₂-persistence / NULL "fills
   Spin(9)"; ``dim(spin(9) ∩ Der(𝕊)) = 14 ≪ 36``, ``Spin(9) ≠ Aut(𝕊)``).
6. Tower consistency — ``so(9) ⊃ so(8)`` (the ``E_{pq}`` with ``p, q ≤ 7``).

ALL deviations are reduced through the **scalar** Class K pin-slot magnitude
(:func:`srmech.cascade.magnitude`) — NEVER Python ``abs()`` per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`` — by first
reducing the matrix to a scalar Frobenius norm via the numpy-free Class-N
:func:`srmech.math.laplacian.mat_norm`. numpy-FREE (per
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``): the
so9 surfaces return :class:`srmech.math.mat.Mat`; ranks ride the EXACT
rational :func:`srmech.physics.qm.so9._q_rank`.
"""

from __future__ import annotations

from srmech.cascade import magnitude
from srmech.math.laplacian import mat_matmul, mat_norm
from srmech.math.mat import Mat
from srmech.physics.qm import so9

_TOL = 1e-12


# ----------------------------------------------------------------------
# Helpers — numpy-free, scalar reductions through cascade.magnitude.
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


def _add(a: Mat, b: Mat) -> Mat:
    """Element-wise ``A + B`` over two real :class:`Mat` → :class:`Mat`."""
    ar, br = _rows(a), _rows(b)
    return Mat.from_rows([[ar[i][j] + br[i][j] for j in range(len(ar[0]))]
                          for i in range(len(ar))])


def _frob(matrix) -> float:
    """Frobenius-norm deviation reduced through the scalar Class K magnitude
    (numpy-free ``mat_norm`` first, then ``cascade.magnitude``; NEVER abs())."""
    scalar = mat_norm(matrix if isinstance(matrix, Mat) else Mat.from_rows(matrix))
    return magnitude(scalar)


def _flatten_mat(m: Mat) -> list:
    """Row-major flatten of a real :class:`Mat` to ints (entries are exact)."""
    rows = _rows(m)
    return [int(round(x.real if isinstance(x, complex) else x))
            for row in rows for x in row]


def _rank(mats) -> int:
    """EXACT rank over ℚ of a list of :class:`Mat`, via ``so9._q_rank`` on the
    integer flattenings (the ``½`` dyadic Σ entries are ranked via their exact
    ``×2`` integer form — rank is scale-invariant)."""
    rows = []
    for m in mats:
        vals = [x.real if isinstance(x, complex) else x for r in _rows(m) for x in r]
        rows.append([int(round(2 * v)) for v in vals])   # ×2 clears the ½ dyadics
    return so9._q_rank(rows)


# ----------------------------------------------------------------------
# TEST 1 — so(9) adjoint (vector rep): 36 antisymmetric 9x9, rank 36.
# ----------------------------------------------------------------------


def test_so9_adjoint_dim36_rank36():
    """``so9_adjoint_basis`` is 36 antisymmetric ``9x9`` of rank exactly 36."""
    adj = so9.so9_adjoint_basis()
    assert len(adj) == 36
    for g in adj:
        assert g.shape == (9, 9)
        assert _frob(_add(g, g.T)) < _TOL          # antisymmetric: g = −gᵀ
    assert _rank(adj) == 36                          # rank exactly C(9,2) = 36


# ----------------------------------------------------------------------
# TEST 2 — Δ₉ Clifford: 9 symmetric 16x16 with {Γ_a, Γ_b} = 2 δ_ab I.
# ----------------------------------------------------------------------


def test_spin9_gamma_clifford_action():
    """The 9 ``Γ`` are symmetric ``16x16`` and satisfy the Clifford relation
    ``{Γ_a, Γ_b} = 2 δ_{ab} I`` bit-exact (recomputed independently here)."""
    gammas = so9.spin9_gamma_matrices()
    assert len(gammas) == 9
    ident = _eye(16)
    two_i = Mat.from_rows([[2.0 if i == j else 0.0 for j in range(16)]
                           for i in range(16)])
    for g in gammas:
        assert g.shape == (16, 16)
        assert _frob(_sub(g, g.T)) < _TOL          # symmetric: Γ = Γᵀ
    for a in range(9):
        for b in range(9):
            anti = _add(mat_matmul(gammas[a], gammas[b]),
                        mat_matmul(gammas[b], gammas[a]))
            expected = two_i if a == b else Mat.from_rows(
                [[0.0] * 16 for _ in range(16)])
            assert _frob(_sub(anti, expected)) < _TOL


# ----------------------------------------------------------------------
# TEST 3 — spin(9) spinor generators: 36 antisym 16x16, rank 36, so(9) brackets.
# ----------------------------------------------------------------------


def test_spin9_spinor_generators_rank36_and_brackets():
    """The 36 ``Σ = ¼[Γ, Γ]`` are antisymmetric ``16x16``, rank 36, and obey
    the ``so(9)`` structure constants (via the branching certificate)."""
    sigma = so9.spin9_spinor_generators()
    assert len(sigma) == 36
    for s in sigma:
        assert s.shape == (16, 16)
        assert _frob(_add(s, s.T)) < _TOL          # antisymmetric
    assert _rank(sigma) == 36                        # rank exactly 36

    cert = so9.spin8_in_spin9_branching()["spinor_rep"]
    assert cert["spinor_dim"] == 16
    assert cert["spin9_dim"] == 36
    assert cert["spinor_rank"] == 36
    assert cert["clifford_max_residual"] < _TOL
    assert cert["so9_bracket_max_residual"] < _TOL   # SAME so(9) as the vector rep


# ----------------------------------------------------------------------
# TEST 4 — Spin(8) ⊂ Spin(9) branching 16 = 8_s ⊕ 8_c.
# ----------------------------------------------------------------------


def test_spin8_in_spin9_branching_16_eq_8s_plus_8c():
    """The bit-exact ``16 = 8_s ⊕ 8_c`` branching: block-diagonal Spin(8),
    Γ_8 commutes, ``28 + 28`` half-spinor ranks, distinct actions, attested."""
    result = so9.spin8_in_spin9_branching()
    br = result["branching"]
    assert br["spinor_dim"] == 16
    assert br["spin8_generators"] == 28
    assert br["branch"] == (8, 8)
    assert br["branch_labels"] == ("8_s", "8_c")
    # the 28 Spin(8) generators are block-diagonal (no off-block leakage).
    assert br["off_block_max_residual"] < _TOL
    # Γ_8 (hence P_± = ½(I ± Γ_8)) commutes with the whole Spin(8) subalgebra.
    assert br["projector_commutator_max_residual"] < _TOL
    # each block carries a full faithful so(8) (rank 28).
    assert br["half_spinor_ranks"] == (28, 28)
    # the two half-spinors carry DIFFERENT actions (distinct 8_s / 8_c).
    assert br["half_spinors_distinct_actions"] is True
    assert br["half_spinor_action_difference"] > _TOL

    # MPR self-attestation: content-addressed, 64-hex, arXiv-cited, reproducible.
    att = result["attestation"]
    assert att["mpr_version"] == "1.0"
    assert len(att["attestation"]["response_sha256"]) == 64
    assert att["attestation"]["source_url"] == "https://arxiv.org/abs/math/0105155"
    again = so9.spin8_in_spin9_branching()["attestation"]["attestation"]
    assert again["response_sha256"] == att["attestation"]["response_sha256"]


# ----------------------------------------------------------------------
# TEST 5 — the associator ↔ Spin(9)-holonomy conjecture (honest PARTIAL).
# ----------------------------------------------------------------------


def test_sedenion_holonomy_conjecture_partial_verdict():
    """The tiered verdict is PARTIAL, each tier bit-exact:

    - DERIVED: all 14 ``g₂ = Der(𝕊)`` diagonals ARE sedenion derivations
      (residual 0); ``dim(spin(9) ∩ Der(𝕊)) = 14``.
    - NULL (the honest bound ``Spin(9) ≠ Aut(𝕊)``): a block-mixing generator is
      NOT a derivation, 0 of 36 individual generators are, and the intersection
      (14) is far below ``dim spin(9) = 36``.
    """
    out = so9.sedenion_holonomy_conjecture()
    assert out["verdict"] == "PARTIAL"

    dims = out["dimensions"]
    assert dims["spinor_delta9"] == 16
    assert dims["sedenion_real"] == 16               # RECOGNIZED: shared carrier
    assert dims["spin9"] == 36
    assert dims["g2"] == 14
    assert dims["der_sedenion"] == 14                # Der(𝕊) = g₂ (Schafer 1954)
    assert dims["spin9_cap_der_sedenion"] == 14      # the honest bound: 14 ≪ 36

    cert = out["certificate"]
    # DERIVED (positive): the g₂ associator symmetry persists + embeds.
    assert cert["g2_diag_all_derivations"] is True
    assert cert["n_g2_diag"] == 14
    assert cert["g2_diag_max_leibniz_residual"] < _TOL
    assert cert["g2_diag_in_spin9_span"] is True
    assert cert["spin9_gg_dim"] == 36
    assert cert["spin9_cap_der_sedenion_dim"] == 14
    # NULL (the honest bound): NOT every Spin(9) direction preserves 𝕊.
    assert cert["block_mixer_is_derivation"] is False
    assert cert["block_mixer_leibniz_residual"] > _TOL
    assert cert["n_individual_spin9_derivations"] == 0

    # the tiers + the FORM-not-identity framework reading are present + honest.
    assert set(out["tiers"]) == {"RECOGNIZED", "DERIVED", "NULL"}
    assert out["framework_reading"]["note"] == "framework-reading, not derived"
    assert out["framework_reading"]["spin9_is_not_aut_sedenion"] is True

    # attestation reproducible + arXiv/Schafer-cited.
    att = out["attestation"]
    assert att["mpr_version"] == "1.0"
    assert len(att["attestation"]["response_sha256"]) == 64
    again = so9.sedenion_holonomy_conjecture()["attestation"]["attestation"]
    assert again["response_sha256"] == att["attestation"]["response_sha256"]


# ----------------------------------------------------------------------
# TEST 6 — tower consistency: so(9) ⊃ so(8).
# ----------------------------------------------------------------------


def test_so9_contains_so8():
    """The ``E_{pq}`` with ``p, q ≤ 7`` (the top-left ``8x8`` corner) span an
    ``so(8)`` (rank 28) inside the ``so(9)`` vector rep — the rung below."""
    adj = so9.so9_adjoint_basis()
    corner = []
    for g in adj:
        rows = _rows(g)
        # a generator is in the so(8) corner iff row/col 8 is entirely zero.
        if all(rows[8][j] == 0.0 for j in range(9)) and all(
                rows[i][8] == 0.0 for i in range(9)):
            corner.append(g)
    assert len(corner) == 28                         # C(8,2) = 28
    assert _rank(corner) == 28                        # a full so(8) inside so(9)
