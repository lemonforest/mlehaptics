"""rc313 PROVE-GATES — the exact-rational discrete writhe + the mod-2 CWF check.

Numpy-free (a test for a numpy-free surface is itself numpy-free). The four
gates the ship claims:

  W1  discrete_writhe on KNOWN configurations (planar -> 0 exactly; a known
      chiral crossing -> the known exact rational Wr; mirror -> negate; a
      non-integer rational embedding -> the same, denominator-scale invariant).
  W2  the mod-2 CWF check on a CONSTRUCTED strand+embedding with independently
      known Lk / Tw / Wr: (Tw + Wr) mod 2 == Lk mod 2, Wr from GEOMETRY (not
      Lk-Tw) — and a planar re-embedding FAILS (the geometric content has teeth).
  W3  no-embedding path returns ONLY the intrinsic mod-2 Lk (no fabricated Wr).
  W4  exactness: native == pure byte-identical (integer determinants — no float
      drift); the degeneracy guard raises on a strand meeting itself in 3D.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native


# ── fixtures: known embeddings ────────────────────────────────────────────
_PLANAR = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]          # simple square
_SKEW = [(0, 0, 0), (2, 2, 0), (2, 0, 10), (0, 2, 10)]          # +1 crossing
_SKEW_MIRROR = [(0, 0, 0), (2, 2, 0), (2, 0, -10), (0, 2, -10)]  # mirror -> -1
_PENTAGON = [(2, 0, 0), (0, 2, 0), (-2, 1, 0), (-1, -2, 0), (1, -2, 0)]

# a Q8 4-cycle whose ordered product i*i*1*1 = -1 (center_parity -1 -> Lk==1)
_I = [0.0, 1.0, 0.0, 0.0]
_ONE = [1.0, 0.0, 0.0, 0.0]
_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0)]
_GAINS = [_I, _I, _ONE, _ONE]


# ── W1 ────────────────────────────────────────────────────────────────────
def test_w1_planar_is_zero_exactly():
    assert G.discrete_writhe(_PLANAR)["writhe"] == (0, 1)
    assert G.discrete_writhe(_PENTAGON)["writhe"] == (0, 1)


def test_w1_chiral_crossing_is_known_rational():
    assert G.discrete_writhe(_SKEW)["writhe"] == (1, 1)


def test_w1_mirror_negates():
    assert G.discrete_writhe(_SKEW_MIRROR)["writhe"] == (-1, 1)


def test_w1_rational_coords_scale_invariant():
    # non-integer coordinates, same chirality as _SKEW -> still +1
    skew_rat = [(0, 0, 0), (2, 2, 0), (2, 0, Fraction(10, 3)),
                (0, 2, Fraction(10, 3))]
    assert G.discrete_writhe(skew_rat)["writhe"] == (1, 1)
    # explicit (num, den) pairs likewise
    skew_pair = [(0, 0, 0), (2, 2, 0), (2, 0, (10, 3)), (0, 2, (10, 3))]
    assert G.discrete_writhe(skew_pair)["writhe"] == (1, 1)


def test_w1_open_polyline_no_nonadjacent_pairs():
    # an open 3-point chain has no non-adjacent segment pair -> Wr = 0
    assert G.discrete_writhe([(0, 0, 0), (1, 0, 0), (1, 1, 1)],
                             closed=False)["writhe"] == (0, 1)


# ── W2 ────────────────────────────────────────────────────────────────────
def test_w2_mod2_cwf_holds_on_constructed_strand():
    res = G.cwf_consistency_mod2(_EDGES, _GAINS, embedding=_SKEW, closed=True)
    assert res["lk_center_parity"] == -1     # ordered product i*i*1*1 = -1
    assert res["lk_mod2"] == 1
    assert res["tw_mod2"] == 0               # no negative-coset gains
    assert res["wr"] == (1, 1)               # geometry, one crossing
    assert res["wr_mod2"] == 1
    # (Tw + Wr) mod 2 == Lk mod 2  ->  (0 + 1) % 2 == 1
    assert res["consistent"] is True


def test_w2_wr_is_geometric_not_lk_minus_tw():
    # SAME gains, PLANAR re-embedding: Wr parity flips 1 -> 0, so the check
    # MUST fail. Proves Wr comes from geometry, not from Lk - Tw.
    bad = G.cwf_consistency_mod2(_EDGES, _GAINS, embedding=_PLANAR, closed=True)
    assert bad["lk_mod2"] == 1 and bad["tw_mod2"] == 0
    assert bad["wr"] == (0, 1) and bad["wr_mod2"] == 0
    assert bad["consistent"] is False


def test_w2_tw_reads_negative_coset_parity():
    # inject a negative-coset gain (-i) -> Tw parity flips to 1
    neg_i = [0.0, -1.0, 0.0, 0.0]
    gains = [neg_i, _I, _ONE, _ONE]          # ordered product (-i)*i*1*1 = +1
    res = G.cwf_consistency_mod2(_EDGES, gains, embedding=_SKEW, closed=True)
    assert res["lk_center_parity"] == 1 and res["lk_mod2"] == 0
    assert res["tw_mod2"] == 1               # one negative-coset gain
    assert res["wr_mod2"] == 1
    # (1 + 1) % 2 == 0 == Lk  -> consistent
    assert res["consistent"] is True


# ── W3 ────────────────────────────────────────────────────────────────────
def test_w3_no_embedding_returns_intrinsic_only():
    res = G.cwf_consistency_mod2(_EDGES, _GAINS, embedding=None)
    assert res["lk_mod2"] == 1               # intrinsic mod-2 Lk available
    assert res["tw_mod2"] == 0
    assert res["wr"] is None                 # no fabricated Wr
    assert res["wr_mod2"] is None
    assert res["consistent"] is None
    assert "no embedding" in res["note"]


# ── W4 ────────────────────────────────────────────────────────────────────
def _lanes(embedding):
    return G._dw_normalise(list(embedding))


@pytest.mark.parametrize("emb", [
    _PLANAR, _SKEW, _SKEW_MIRROR, _PENTAGON,
    [(Fraction(1, 7), Fraction(-3, 2), 0), (2, 2, 0), (2, 0, Fraction(10, 3)),
     (0, Fraction(5, 4), Fraction(10, 3)), (-1, -1, 1), (3, -2, Fraction(-7, 5))],
])
def test_w4_native_equals_pure_byte_identical(emb):
    lanes = _lanes(emb)
    n = len(emb)
    pure = G._dw_writhe_pure(*lanes, n, True)
    if _native.has_native_genome_discrete_writhe():
        nat = G._dw_writhe_native(*lanes, n, True)
        assert nat is not None
        assert nat == (pure, 1), f"native {nat} != pure {(pure, 1)}"
    else:  # pragma: no cover - only when the .so is absent
        pytest.skip("native peer not loaded")


def test_w4_degeneracy_raises_on_meet_in_3d():
    # a coplanar-crossing configuration: the triple product vanishes at the
    # crossing (the strands meet in 3D) -> not an embedding -> ValueError.
    bad = [(0, 0, 0), (2, 2, 1), (2, 0, 0), (0, 2, 1)]
    with pytest.raises(ValueError):
        G.discrete_writhe(bad)


def test_w4_exact_rational_output_is_reduced_integer():
    # the directional writhe is integer-valued: den is always 1
    for emb in (_PLANAR, _SKEW, _SKEW_MIRROR):
        r = G.discrete_writhe(emb)
        assert r["den"] == 1
        assert isinstance(r["num"], int)


# ── surface hygiene ────────────────────────────────────────────────────────
def test_discrete_writhe_and_cwf_are_public():
    assert "discrete_writhe" in G.__all__
    assert "cwf_consistency_mod2" in G.__all__


def test_cwf_requires_single_cycle():
    # a tree (no cycle) -> n_cycles == 0 -> ValueError
    with pytest.raises(ValueError):
        G.cwf_consistency_mod2([(0, 1), (1, 2)], [_ONE, _ONE], embedding=None)


def test_discrete_writhe_rejects_floats():
    with pytest.raises((TypeError, ValueError)):
        G.discrete_writhe([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                           (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)])
