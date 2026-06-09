"""The One — S(σ,θ) generator (v0.7.0rc49; #887).

Tests the cascade-native, numpy-free, exact-rational generator
``srmech.amsc.cascade.one.the_one`` that holds the entire 1+3+7+3 = 14
A–N substrate as a single (σ, θ)-parameterised object.
"""

import importlib

import pytest

from srmech.amsc.cascade import the_one, s_generator, One, Block
from srmech.amsc.cascade import one as one_mod
from srmech.amsc.rational import cos_series_truncate, sin_series_truncate


# ── structure: the 1+3+7+3 = 14 partition ─────────────────────────────

def test_dim_is_14_and_partition_is_1_3_7_3():
    s = the_one(+1, 0, 1)
    assert s.dim == 14
    assert s.partition == (1, 3, 7, 3)
    assert sum(s.partition) == 14
    assert s.imag_dims == (1, 3, 7)


def test_block_dims_are_2_4_8():
    s = the_one(+1, 1, 1)
    assert tuple(b.dim for b in s.blocks) == (2, 4, 8)
    assert sum(b.dim for b in s.blocks) == 14
    assert tuple(len(b.imag) for b in s.blocks) == (1, 3, 7)
    assert tuple(b.algebra for b in s.blocks) == ("C", "H", "O")
    assert tuple(b.n for b in s.blocks) == (1, 2, 3)


def test_plane_counts_are_0_1_3():
    # The octonion-native epicycle: ℂ/ℍ/𝕆 turn 0/1/3 Fano planes by θ.
    s = the_one(+1, 1, 1)
    assert s.plane_counts == (0, 1, 3)
    assert tuple(len(b.rotated_planes) for b in s.blocks) == (0, 1, 3)
    # 𝕆's three planes are the Fano triples through Î₃ = e₇.
    assert s.blocks[2].rotated_planes == ((1, 6, -1), (2, 5, 1), (3, 4, 1))


def test_an_slots_tile_the_14_classes():
    s = the_one(+1, 0, 1)
    imag_slots = [c for b in s.blocks for c in b.an_imag_slots]
    assert imag_slots == list("AICJDEFGKLM")          # 1 + 3 + 7 = 11
    assert s.grammar_slots == ("B", "H", "N")          # the +3 grammar
    # every class A–N appears exactly once across imaginary ∪ grammar
    full = sorted(imag_slots + list(s.grammar_slots))
    assert full == list("ABCDEFGHIJKLMN")


def test_real_anchors_are_unit():
    s = the_one(-1, 3, 7)
    for b in s.blocks:
        assert b.real == (1, 1)                         # the ℝ·1 grammar unit
        assert b.grammar_slot in ("B", "H", "N")
    assert tuple(b.grammar_slot for b in s.blocks) == ("B", "H", "N")


# ── the headline structural prediction: n=1 degenerates to σ ───────────

@pytest.mark.parametrize("sigma", [+1, -1])
@pytest.mark.parametrize("theta", [(0, 1), (1, 1), (99, 100), (314, 100), (-7, 3)])
def test_n1_is_sigma_only_independent_of_theta(sigma, theta):
    s = the_one(sigma, theta[0], theta[1])
    # Im ℂ is 1-D: the seed coincides with the rotation axis Î₁, so θ is
    # inert and the only freedom is σ.
    assert s.blocks[0].imag == ((sigma, 1),)
    assert s.n1_is_sigma_only is True


def test_n1_independent_of_terms():
    a = the_one(+1, 2, 1, terms=8).blocks[0].imag
    b = the_one(+1, 2, 1, terms=40).blocks[0].imag
    assert a == b == ((1, 1),)                          # θ and terms inert at n=1


# ── θ = 0 → the σ-seed (no rotation) ──────────────────────────────────

@pytest.mark.parametrize("sigma", [+1, -1])
def test_theta_zero_is_sigma_seed(sigma):
    s = the_one(sigma, 0, 1)
    # cos 0 = 1, sin 0 = 0 → seed e₁ scaled by σ; other imaginary axes zero.
    assert s.blocks[1].imag == ((sigma, 1), (0, 1), (0, 1))            # ℍ
    assert s.blocks[2].imag == ((sigma, 1),) + ((0, 1),) * 6          # 𝕆


# ── the rotation IS the exact-rational Class-N cos/sin ─────────────────

def test_imaginary_entries_are_exact_rational_cos_sin():
    terms = 20
    tn, td = 1, 1                                       # θ = 1 radian
    s = the_one(+1, tn, td, terms=terms)
    cos_t = cos_series_truncate(tn, td, terms)
    sin_t = sin_series_truncate(tn, td, terms)
    neg_sin = (-sin_t[0], sin_t[1])
    # ℍ block: seed e₁ in plane (1,2,+1) → (σ cos θ, σ sin θ, 0).
    assert s.blocks[1].imag[0] == cos_t
    assert s.blocks[1].imag[1] == sin_t
    assert s.blocks[1].imag[2] == (0, 1)
    # 𝕆 block: seed e₁ lies in the Fano plane (1,6,−1) (e₁e₆=−e₇), so it
    # rotates e₁ → cos θ·e₁ − sin θ·e₆ — cos θ on index 0, −sin θ on index 5,
    # zeros elsewhere. (The full 3-plane structure lives in to_matrix; a
    # single seed only excites its own plane.)
    o = s.blocks[2].imag
    assert o[0] == cos_t
    assert o[5] == neg_sin
    assert all(o[i] == (0, 1) for i in (1, 2, 3, 4, 6))


def test_all_entries_are_reduced_integer_pairs():
    s = the_one(-1, 22, 7, terms=18)                    # θ ≈ π
    for e in s.to_flat_rational():
        assert isinstance(e, tuple) and len(e) == 2
        num, den = e
        assert isinstance(num, int) and isinstance(den, int)
        assert den > 0


# ── σ chirality flip is Class K·C (no abs); negates the imaginary ──────

@pytest.mark.parametrize("theta", [(0, 1), (1, 1), (5, 4)])
def test_sigma_flip_negates_imaginary_not_anchor(theta):
    plus = the_one(+1, theta[0], theta[1])
    minus = the_one(-1, theta[0], theta[1])
    for bp, bm in zip(plus.blocks, minus.blocks):
        assert bp.real == bm.real == (1, 1)             # anchors unchanged
        for ep, em in zip(bp.imag, bm.imag):
            # σ=-1 is the Class-C orientation reversal: numerator negated.
            assert em == (-ep[0], ep[1])


def test_flat_rational_has_length_14():
    assert len(the_one(+1, 1, 1).to_flat_rational()) == 14


# ── input validation ──────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [0, 2, -2, +3])
def test_bad_sigma_rejected(bad):
    with pytest.raises(ValueError):
        the_one(bad, 1, 1)


def test_nonpositive_theta_den_rejected():
    with pytest.raises(ValueError):
        the_one(+1, 1, 0)
    with pytest.raises(ValueError):
        the_one(+1, 1, -3)


def test_non_int_theta_rejected():
    with pytest.raises(TypeError):
        the_one(+1, 1.5, 1)        # type: ignore[arg-type]


# ── aliases + repr ────────────────────────────────────────────────────

def test_s_generator_is_the_one_alias():
    assert s_generator is the_one
    assert s_generator(+1, 0, 1).to_flat_rational() == the_one(+1, 0, 1).to_flat_rational()


def test_repr_mentions_dim_and_partition():
    r = repr(the_one(+1, 1, 1))
    assert "dim=14" in r
    assert "(1, 3, 7, 3)" in r


# ── numpy-free at import (the §22 discipline) ─────────────────────────

def test_module_has_no_module_level_numpy_import():
    # The exact-rational core must not import numpy at load time; the AST
    # ratchet test_numpy_optional_rc47 enforces this across amsc/**, this is
    # a fast local sentinel. Parse the AST and inspect only MODULE-LEVEL
    # statements (lazy imports inside .to_numpy/.to_matrix are nested in
    # FunctionDef/ClassDef and correctly excluded; docstrings aren't imports).
    import ast

    src = importlib.util.find_spec("srmech.amsc.cascade.one").origin
    with open(src, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(a.name.split(".")[0] != "numpy" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "numpy"


# ── opt-in float realisations (scientific tier; skip if numpy absent) ──

def _has_numpy():
    return importlib.util.find_spec("numpy") is not None


@pytest.mark.skipif(not _has_numpy(), reason="numpy (scientific tier) not installed")
def test_to_numpy_is_14_vector_matching_rationals():
    import numpy as np

    s = the_one(+1, 1, 1, terms=20)
    v = s.to_numpy()
    assert v.shape == (14,)
    flat = s.to_flat_rational()
    expected = np.array([n / d for (n, d) in flat], dtype=float)
    assert np.allclose(v, expected, atol=0.0, rtol=0.0)


@pytest.mark.skipif(not _has_numpy(), reason="numpy (scientific tier) not installed")
def test_to_matrix_applied_to_seed_reproduces_state():
    import numpy as np

    s = the_one(-1, 5, 4, terms=22)
    g = s.to_matrix()
    assert g.shape == (14, 14)
    # canonical seed: real anchor = 1, imaginary axis e₁ = 1, rest 0
    seed = np.zeros(14, dtype=float)
    offset = 0
    for d in (1, 3, 7):
        seed[offset] = 1.0          # ℝ·1 anchor
        seed[offset + 1] = 1.0      # imaginary e₁
        offset += 1 + d
    assert np.allclose(g @ seed, s.to_numpy(), atol=1e-12)


@pytest.mark.skipif(not _has_numpy(), reason="numpy (scientific tier) not installed")
def test_to_matrix_is_block_diagonal_orthogonal_up_to_sigma():
    import numpy as np

    s = the_one(+1, 1, 1, terms=24)     # σ=+1 → proper rotation, G Gᵀ ≈ I
    g = s.to_matrix()
    assert np.allclose(g @ g.T, np.eye(14), atol=1e-9)


@pytest.mark.skipif(not _has_numpy(), reason="numpy (scientific tier) not installed")
def test_octonion_block_turns_three_planes():
    # The 𝕆 block (dims 6..13: real e₀ then imaginary e₁..e₇) is the
    # octonion-native 3-plane rotation: eigenvalues {1 (e₀), 1 (e₇=Î₃),
    # e^{±iθ}×3} on the 8-D block.
    import numpy as np

    theta = 0.6
    # match the cascade's exact-rational θ to a clean fraction
    s = the_one(+1, 6, 10, terms=26)
    g = s.to_matrix()
    o_block = g[6:14, 6:14]                       # the 8×8 𝕆 block (1 ⊕ R₃)
    ang = np.sort(np.round(np.angle(np.linalg.eigvals(o_block)), 3))
    # two fixed axes (angle 0) + three planes at ±θ
    assert list(ang).count(0.0) == 2
    pos = [a for a in ang if a > 1e-6]
    neg = [a for a in ang if a < -1e-6]
    assert len(pos) == 3 and len(neg) == 3
    assert np.allclose(pos, round(theta, 3), atol=1e-2)
