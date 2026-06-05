"""qm.hurwitz — the octonion-native matrix peer of "the One" (v0.7.0rc50; #887).

The Rosetta cross-check: srmech.qm.hurwitz builds S(σ,θ) as a 14×14 matrix
with the Fano planes DERIVED from octonion_mult_table, and it must agree
bit-for-bit with the numpy-free cascade srmech.amsc.cascade.the_one.

The whole module is the scientific tier (srmech.qm requires numpy), so it is
skipped wholesale where numpy is absent.
"""

import pytest

pytest.importorskip("numpy")  # qm tier; skip the file on a numpy-free install

import numpy as np

from srmech.amsc.cascade import the_one
from srmech.amsc.cascade.one import FANO_PLANES
from srmech.qm.hurwitz import hurwitz_matrix, hurwitz_planes


# ── the planes are DERIVED from the octonion table (not hardcoded) ────

def test_hurwitz_planes_derived_from_octonion_table():
    planes = hurwitz_planes()
    # ℂ: none; ℍ: {1,2,3} → (1,2,+1); 𝕆: the 3 Fano triples through e₇.
    assert planes == ((), ((1, 2, 1),), ((1, 6, -1), (2, 5, 1), (3, 4, 1)))
    assert tuple(len(p) for p in planes) == (0, 1, 3)


def test_cascade_fano_planes_match_table_derived_bit_exact():
    # The cascade form HARDCODES FANO_PLANES; the qm peer DERIVES them from
    # octonion_mult_table. They must be identical (the bit-exact structure
    # cross-derivation).
    assert FANO_PLANES == hurwitz_planes()


# ── the matrix realisation ────────────────────────────────────────────

def test_hurwitz_matrix_shape_and_anchors():
    g = hurwitz_matrix(+1, 1, 1)
    assert g.shape == (14, 14)
    # the three ℝ·1 anchors (rows/cols 0, 2, 6) are fixed.
    for r in (0, 2, 6):
        e = np.zeros(14); e[r] = 1.0
        assert np.allclose(g @ e, e)


@pytest.mark.parametrize("sigma", [+1, -1])
@pytest.mark.parametrize("theta", [(0, 1), (1, 1), (3, 5), (-2, 3), (314, 100)])
def test_bit_exact_parity_cascade_vs_qm(sigma, theta):
    # The headline: cascade One.to_matrix() == qm hurwitz_matrix(), bit-exact
    # (same exact-rational cos/sin, same Fano planes → identical float64).
    terms = 24
    cascade = the_one(sigma, theta[0], theta[1], terms=terms).to_matrix()
    qm = hurwitz_matrix(sigma, theta[0], theta[1], terms=terms)
    assert np.array_equal(cascade, qm)


def test_octonion_block_is_three_plane_rotation():
    g = hurwitz_matrix(+1, 6, 10, terms=26)        # θ = 0.6
    o_block = g[6:14, 6:14]
    ang = np.sort(np.round(np.angle(np.linalg.eigvals(o_block)), 3))
    assert list(ang).count(0.0) == 2               # e₀ and Î₃=e₇ fixed
    assert len([a for a in ang if a > 1e-6]) == 3  # 3 planes at +θ
    assert len([a for a in ang if a < -1e-6]) == 3  # 3 planes at -θ


def test_quaternion_block_is_single_plane_rotation():
    g = hurwitz_matrix(+1, 6, 10, terms=26)
    h_block = g[2:6, 2:6]                           # ℍ block (1 ⊕ R₂)
    ang = np.sort(np.round(np.angle(np.linalg.eigvals(h_block)), 3))
    assert list(ang).count(0.0) == 2               # e₀ and Î₂=e₃ fixed
    assert len([a for a in ang if abs(a) > 1e-6]) == 2  # one ±θ plane


@pytest.mark.parametrize("sigma", [+1, -1])
def test_proper_sign_orthogonality(sigma):
    g = hurwitz_matrix(sigma, 1, 1, terms=24)
    # σ·R is orthogonal either way (G Gᵀ = I); det reflects the chirality.
    assert np.allclose(g @ g.T, np.eye(14), atol=1e-9)


# ── validation ────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [0, 2, -2])
def test_bad_sigma_rejected(bad):
    with pytest.raises(ValueError):
        hurwitz_matrix(bad, 1, 1)


def test_nonpositive_theta_den_rejected():
    with pytest.raises(ValueError):
        hurwitz_matrix(+1, 1, 0)
