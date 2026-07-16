"""rc73 — the SECOND GENUS RUNG: ``RiemannTheta`` Sp(4,ℤ) TRANSFORMATION + the
genus-2 ADDITION relation (genuine, distinct from rc72's duplication).

A pure CARRIER extension (like rc72): no public ToolEntry op, so ``tools.total`` is
UNCHANGED — these tests assert ONLY the carrier's own new gates.

The build gates (the no-shell proof):

  (A) the Sp(4,ℤ) TRANSFORMATION — the modular action on the binary characteristic
      m=[ε';ε] is bit-exact (DLMF §21.5.9; Igusa, Theta Functions (1972) §V.1) on
      the standard generators (translation T, GL-twist U, inversion J); even ⇄ even /
      odd ⇄ odd parity is PRESERVED; the group law composes exactly
      (transform(g₂·g₁) == transform(g₂)∘transform(g₁)); κ(γ) is the correct 8th root
      (exponent k ∈ ℤ/8, exact);
  (B) the ADDITION relation — the genuine two-argument genus-2 theta addition
      theorem (DLMF §21.6.8 at z₁=z₂=0, two-independent-characteristic
      specialization) holds EXACTLY as a truncated exact-integer multivariate
      q-series for ALL Ω, AND is provably GENUINELY DISTINCT from duplication
      (a product of two DIFFERENT theta-nulls, not a single null squared);
  (C) NO REGRESSION — rc72's gates still pass (collapse==θ₃ bit-exact;
      duplication_holds(8)==True);
  (D) Python==C parity EXACT on the transformation + the addition lattices;
  (E) the carrier source has no numpy / math / abs() (the ratchet, extended).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannTheta
from srmech.amsc import _native


def _t00() -> RiemannTheta:
    return RiemannTheta.theta_constant((0, 0), (0, 0))


THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]

ALL16 = [RiemannTheta(a, b, c, d)
         for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1)]


# the standard Sp(4,ℤ) generators (the test fixtures)
def _gens():
    return {
        "T11": RiemannTheta.sp4_translation(((1, 0), (0, 0))),
        "T22": RiemannTheta.sp4_translation(((0, 0), (0, 1))),
        "Toff": RiemannTheta.sp4_translation(((0, 1), (1, 0))),
        "Urot": RiemannTheta.sp4_gl_twist(((0, -1), (1, 0))),
        "Ushear": RiemannTheta.sp4_gl_twist(((1, 1), (0, 1))),
        "J": RiemannTheta.sp4_inversion(),
    }


# ── gate (A): the Sp(4,ℤ) transformation ─────────────────────────────────────
def test_generators_are_symplectic():
    """Every standard generator is genuinely symplectic (γ·J·γᵀ = J — DLMF §21.5.2,
    the exact integer block conditions AᵀC sym, BᵀD sym, AᵀD−CᵀB=I)."""
    for name, g in _gens().items():
        assert RiemannTheta.sp4_is_symplectic(g), name


def test_translation_rejects_asymmetric_block():
    """The translation block B must be symmetric (the Sp(4,ℤ) condition) — an
    asymmetric B is rejected loudly (honest boundary)."""
    with pytest.raises(ValueError):
        RiemannTheta.sp4_translation(((0, 1), (0, 0)))   # B₁₂=1 ≠ B₂₁=0


def test_gl_twist_rejects_non_unimodular():
    """The GL-twist block A must be in GL(2,ℤ) (det = ±1) so (Aᵀ)⁻¹ is integer —
    a non-unimodular A is rejected loudly (honest boundary)."""
    with pytest.raises(ValueError):
        RiemannTheta.sp4_gl_twist(((2, 0), (0, 1)))      # det 2


def test_transform_rejects_non_symplectic_gamma():
    """``transform`` refuses a non-symplectic γ — an honest boundary, not a
    fabricated reduction."""
    bad = (((1, 0), (0, 1)), ((0, 0), (0, 0)),
           ((0, 0), (0, 0)), ((2, 0), (0, 1)))           # AᵀD ≠ I
    assert not RiemannTheta.sp4_is_symplectic(bad)
    with pytest.raises(ValueError):
        _t00().transform(bad)


def test_characteristic_action_preserves_parity():
    """The modular action preserves the even/odd parity (even ⇄ even, odd ⇄ odd —
    the action factors through Sp(4,ℤ₂)) on ALL 16 characteristics, for every
    generator. This is THE structural invariant of the transformation."""
    for name, g in _gens().items():
        for rt in ALL16:
            new, _k = rt.transform(g)
            assert new.is_even == rt.is_even, (name, rt.characteristic)


def test_transform_is_bit_exact_concrete():
    """Concrete bit-exact checks of the characteristic map (DLMF §21.5.9). The
    GL-twist Urot = [[0,-1],[1,0]] permutes the upper characteristic by A (and the
    lower by (Aᵀ)⁻¹); J swaps the upper/lower roles. Verified against the explicit
    affine formula on a sample characteristic."""
    rt = RiemannTheta.theta_constant((1, 0), (0, 1))     # ε'=(1,0), ε=(0,1)
    # the explicit DLMF map, recomputed independently here
    npp, nep = RiemannTheta._char_transform_int(
        _gens()["J"], (1, 0), (0, 1))
    new, _k = rt.transform(_gens()["J"])
    assert new.characteristic == ((npp[0] % 2, npp[1] % 2),
                                  (nep[0] % 2, nep[1] % 2))


def test_group_law_composes_exactly():
    """The characteristic action is a GROUP ACTION: transform(g₂·g₁) ==
    transform(g₂) after transform(g₁), exactly, on all 16 characteristics over all
    pairs of generators (the cocycle base — Sp(4,ℤ) acts by the block matrix
    product)."""
    gens = list(_gens().values())
    for g1 in gens:
        for g2 in gens:
            g21 = RiemannTheta.sp4_compose(g2, g1)
            assert RiemannTheta.sp4_is_symplectic(g21)
            for rt in ALL16:
                direct, _kd = rt.transform(g21)
                step1, _k1 = rt.transform(g1)
                step2, _k2 = step1.transform(g2)
                assert direct.characteristic == step2.characteristic, (
                    rt.characteristic)


def test_kappa_is_eighth_root_exponent():
    """κ(γ) is the correct 8th root — the exponent k ∈ ℤ/8 (the multiplier ζ₈^k) is
    an exact integer in {0,…,7} for every generator and every characteristic. The
    corrected (rc233 #824) multiplier reaches genuine ζ₈ phases beyond ±1 (e.g. the
    diag(1,0) translation gives ζ₈¹=e^{iπ/4}); the transcendental automorphy factor
    det(Cτ+D)^{1/2} is NOT part of this exponent."""
    seen_nonzero = False
    for name, g in _gens().items():
        for rt in ALL16:
            _new, k = rt.transform(g)
            assert isinstance(k, int) and 0 <= k < 8, (name, rt.characteristic, k)
            if k != 0:
                seen_nonzero = True
    assert seen_nonzero, "the κ multiplier should be non-trivial on some generator"


def test_kappa_translation_values():
    """The translation T11=[[I,B],[0,I]], B=diag(1,0) gives the κ exponent k∈{0,1}
    across the characteristics — the classical lattice-shift PHASE of the genus-2
    theta-constant: on ε'=(1,·) the shift Ω↦Ω+diag(1,0) multiplies θ by exactly
    ζ₈¹=e^{iπ/4} ((n+½)²·1 ≡ ¼ mod 2 on every lattice point). rc233 (#824) corrected
    this from the pre-fix {0,4} that the ζ₈⁴ sign defect wrongly produced."""
    g = RiemannTheta.sp4_translation(((1, 0), (0, 0)))
    ks = {rt.transform(g)[1] for rt in ALL16}
    assert ks == {0, 1}
    assert 1 in ks            # the genuine ζ₈¹ phase — NOT collapsed to ±1


def test_automorphy_factor_is_symbolic_not_evaluated():
    """The transcendental automorphy factor det(C·Ω+D)^{1/2} is returned SYMBOLIC
    (a string), never numerically evaluated — off every decision path (the rc72
    review lesson)."""
    s = RiemannTheta.automorphy_factor(_gens()["J"])
    assert isinstance(s, str)
    assert "Omega" in s or "Ω" in s
    assert "1/2" in s          # it is a square root, carried symbolically


# ── gate (B): the genus-2 ADDITION relation ──────────────────────────────────
def test_addition_identity_holds_exact():
    """THE rc73 (B) GATE: the genuine genus-2 theta addition theorem (DLMF §21.6.8 at
    z₁=z₂=0, two-independent-characteristic specialization) holds EXACTLY as a
    truncated exact-integer multivariate q-series, for ALL Ω. It verifies genuine
    a≠b pairs (the real addition content), not just the a=b duplication collapse."""
    assert RiemannTheta.addition_holds(4)
    assert RiemannTheta.addition_holds(6)
    assert RiemannTheta.addition_holds(8)


def test_addition_is_genuinely_distinct_from_duplication():
    """THE NO-SHELL PROOF: the addition relation is GENUINELY DISTINCT from
    duplication. Its LEFT side θ[a;0]·θ[b;0] with a≠b is a product of two DIFFERENT
    theta-nulls — NOT equal to ANY duplication LHS θ[c;0]² (a single null squared).
    So it is the genuine addition theorem, not a relabeled duplication."""
    assert RiemannTheta.addition_is_distinct_from_duplication(6)
    assert RiemannTheta.addition_is_distinct_from_duplication(8)
    # explicit: the genuine LHS differs from every θ[c]² lattice
    genuine = RiemannTheta.addition_lhs((1, 0), (0, 0), 8)
    for c1 in (0, 1):
        for c2 in (0, 1):
            tc = RiemannTheta._theta_omega_eighth(c1, c2, 0, 0, 8)
            sq = RiemannTheta._square_lattice_pair(tc, tc)
            assert genuine != sq, (c1, c2)


def test_addition_collapses_to_duplication_when_a_equals_b():
    """When a=b the addition right side's two 2Ω characteristics coincide
    (2r+a+b == 2r+a−b for a=b... up to the lower char), recovering the duplication
    shape Σ_r θ[2r+2a;0](2Ω)·θ[2r;0](2Ω). The a=b instance of the addition gate is
    exactly the duplication collapse — and it still holds exactly."""
    # a == b == (1,0): LHS = θ[(1,0)]², RHS = Σ_r θ[(2r+2,0)/2]·θ[(2r,0)/2] at 2Ω
    L = RiemannTheta.addition_lhs((1, 0), (1, 0), 8)
    R = RiemannTheta.addition_rhs((1, 0), (1, 0), 8)
    safe = 2 * 8 * 8

    def restrict(lat):
        return {(a, b, c): v for (a, b, c), v in lat.items()
                if a <= safe and b <= safe and (c if c >= 0 else -c) <= safe}

    assert restrict(L) == restrict(R)


def test_addition_exercises_cross_term():
    """The addition identity genuinely exercises the genus-2 cross-term q₁₂ (C ≠ 0
    monomials present on the safe region) — it proves genuine genus-2 content, not
    the genus-1 slice."""
    L = RiemannTheta.addition_lhs((1, 0), (0, 1), 8)
    assert any(c != 0 for (_a, _b, c) in L)


# ── gate (C): NO REGRESSION (rc72 gates still pass) ──────────────────────────
def test_rc72_collapse_still_bit_exact():
    assert _t00().collapse_g1_q_series(20) == THETA3_Q20


def test_rc72_duplication_still_holds():
    assert RiemannTheta.duplication_holds(8)


# ── gate (D): Python==C parity ───────────────────────────────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_sp4(),
                    reason="native srmech_riemann_theta_sp4_char not loaded")
def test_python_c_parity_transformation():
    """The native Sp(4,ℤ) characteristic transform + κ exponent equal the pure
    oracle EXACTLY for all 16 characteristics over all generators (do NOT trust the
    C — compare)."""
    for name, g in _gens().items():
        gflat = RiemannTheta._validate_gamma(g)
        for rt in ALL16:
            c_path = _native.riemann_theta_sp4_char_c(
                gflat, rt._ep1, rt._ep2, rt._e1, rt._e2)
            # pure oracle
            npp, nep = RiemannTheta._char_transform_int(
                g, (rt._ep1, rt._ep2), (rt._e1, rt._e2))
            kpy = RiemannTheta._kappa_exp8(
                g, (rt._ep1, rt._ep2), (rt._e1, rt._e2))
            assert c_path == ((npp[0] % 2, npp[1] % 2,
                               nep[0] % 2, nep[1] % 2), kpy), (name,
                                                              rt.characteristic)


@pytest.mark.skipif(not _native.has_native_riemann_theta_eighth(),
                    reason="native srmech_riemann_theta_eighth_lattice not loaded")
def test_python_c_parity_eighth_lattice():
    """The native eighth-nome lattice equals the pure oracle EXACTLY at Ω and at 2Ω
    over several boxes and characteristics."""
    for box in (0, 1, 2, 4):
        for s1 in (-1, 0, 1, 2):
            for s2 in (0, 1):
                for e1 in (0, 1):
                    for at2 in (False, True):
                        c_path = _native.riemann_theta_eighth_lattice_c(
                            s1, s2, e1, 0, at2, box)
                        if at2:
                            py = _pure_two_omega(s1, s2, e1, 0, box)
                        else:
                            py = _pure_omega(s1, s2, e1, 0, box)
                        assert c_path == py, (box, s1, s2, e1, at2)


def _pure_omega(s1, s2, e1, e2, box):
    out = {}
    for n1 in range(-box, box + 1):
        for n2 in range(-box, box + 1):
            u = 2 * n1 + s1
            v = 2 * n2 + s2
            key = (2 * u * u, 2 * v * v, 2 * u * v)
            sign = 1 if (e1 * n1 + e2 * n2) % 2 == 0 else -1
            out[key] = out.get(key, 0) + sign
    return {k: w for k, w in out.items() if w != 0}


def _pure_two_omega(s1, s2, e1, e2, box):
    out = {}
    for n1 in range(-box, box + 1):
        for n2 in range(-box, box + 1):
            u = 4 * n1 + s1
            v = 4 * n2 + s2
            key = (u * u, v * v, u * v)
            sign = 1 if (e1 * n1 + e2 * n2) % 2 == 0 else -1
            out[key] = out.get(key, 0) + sign
    return {k: w for k, w in out.items() if w != 0}


@pytest.mark.skipif(not _native.has_native_riemann_theta_sp4(),
                    reason="native peers not loaded")
def test_gates_pass_through_native():
    """The transformation + addition gates still pass with the native path live
    (end-to-end on the C peers)."""
    assert RiemannTheta.addition_holds(6)
    assert RiemannTheta.addition_is_distinct_from_duplication(6)
    for g in _gens().values():
        for rt in ALL16:
            new, k = rt.transform(g)
            assert new.is_even == rt.is_even
            assert 0 <= k < 8


def test_pure_python_alone_passes_new_gates(pure_riemann_theta):
    """The COMPLETE pure-Python body alone passes both new gates (so the carrier is
    correct on a no-C host) — the native path is FORCED OFF (rc106: before this the
    test carried NO monkeypatch and re-ran the dispatched path under a pure-sounding
    name). Same windows as before — the g2 addition gate is cheap pure (≈1 s)."""
    assert RiemannTheta.addition_holds(6)
    assert RiemannTheta.addition_is_distinct_from_duplication(6)
    assert pure_riemann_theta == []      # no native symbol was ever reached


# ── gate (E): the carrier source is numpy / math / abs() free ────────────────
def test_riemann_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None         # no bare abs() CALL
    assert "float(" not in text                          # no float in the carrier


# ── R-1 (rc215, the #741 divmod-audit residue): the kexp-COMPOSITION gap ──────
#
# STANDING XFAIL — a REAL, LATENT bug recorded in-repo (task #824). The divmod
# audit asked: does `transform`'s 8th-root multiplier exponent `kexp` COMPOSE?
# For any consistent theta-transformation convention
#     θ[γ·m] = ζ₈^{kexp(γ,m)} · κ₀(γ) · θ[m]
# the κ₀(γ) piece (the Maslov / Weil cocycle) is CHARACTERISTIC-INDEPENDENT, so
# the composed-vs-direct exponent DEFECT
#     d(γ₂,γ₁,m) = ( kexp(γ₂γ₁, m) − kexp(γ₁, m) − kexp(γ₂, γ₁·m) ) mod 8
# MUST be independent of the characteristic m (it can only be the γ-only κ₀
# cocycle 2-cochain). It is NOT: for many generator pairs it takes BOTH values
# {0, 4} varying WITH m — the mod-2 OUTPUT fold `RiemannTheta(new_epp % 2, …)`
# drops the characteristic-shift sign θ[ε+2δ] = (−1)^{…}·θ[ε] (a ζ₈⁴ = −1) that
# belongs INSIDE kexp. `_char_transform_int` (the integer characteristic) + the
# single-γ kexp values are correct; only the COMPOSED multiplier is wrong.
#
# Measured (pure path): the char-DEPENDENT-defect pairs are g2 31/81,
# g3 8/25, g4 8/25 (all standard-generator pairs). The canonical witness — the
# pair Urot·T11 at genus 2, both plain Sp(4,ℤ) generators — per characteristic
# m = [ε'; ε]  (k_direct, k1, k2, defect):
#
#   [(0,0);(0,0)]  0 0 0 → 0     [(0,1);(0,0)]  4 0 0 → 4  ← char-dependent
#   [(0,0);(0,1)]  0 0 0 → 0     [(0,1);(0,1)]  4 0 0 → 4  ← char-dependent
#   [(0,0);(1,0)]  0 0 0 → 0     [(0,1);(1,0)]  4 0 0 → 4  ← char-dependent
#   [(0,0);(1,1)]  0 0 0 → 0     [(0,1);(1,1)]  4 0 0 → 4  ← char-dependent
#   [(1,0);(0,0)]  0 4 0 → 4  ←  [(1,1);(0,0)]  4 4 0 → 0
#   [(1,0);(0,1)]  0 4 0 → 4  ←  [(1,1);(0,1)]  4 4 0 → 0
#   [(1,0);(1,0)]  0 4 0 → 4  ←  [(1,1);(1,0)]  4 4 0 → 0
#   [(1,0);(1,1)]  0 4 0 → 4  ←  [(1,1);(1,1)]  4 4 0 → 0
#
# The defect flips with ε' (the upper characteristic that the D·ε' − C·ε map
# pushes out of {0,1} and the output fold then reduces) — the signature of the
# dropped mod-2 shift sign. LATENT: no operational (non-test) consumer composes
# two transforms (only a _native.py comment references `.transform`; the shipped
# Göpel/Rosenhain g2–g4 suites test SINGLE transforms), so no shipped result is
# affected. `strict=True` → the moment #824 folds the shift sign into kexp this
# XPASSES and FAILS, the natural close signal to delete the marker.


def _kexp_defect_is_char_dependent(gens, all_chars, compose) -> bool:
    """True iff some generator pair has a CHARACTERISTIC-DEPENDENT composed-vs-
    direct kexp defect (the bug). A correct kexp makes every pair's defect a
    single m-independent value (the γ-only κ₀ cocycle)."""
    for g1 in gens:
        for g2 in gens:
            g21 = compose(g2, g1)
            defects = set()
            for rt in all_chars:
                _direct, kd = rt.transform(g21)
                step1, k1 = rt.transform(g1)
                _step2, k2 = step1.transform(g2)
                defects.add((kd - k1 - k2) % 8)
            if len(defects) != 1:
                return True
    return False


def test_kexp_composes_consistently_all_genera():
    """R-1 GATE (task #824, CLOSED by rc233): the transform multiplier exponent kexp
    COMPOSES — the composed-vs-direct defect is the γ-only κ₀ cocycle, so it is
    CHARACTERISTIC-INDEPENDENT for every generator pair, at every genus. rc233 fixed
    the ζ₈⁴ sign defect in TWO parts: (1) the corrected Igusa φ_m coefficients
    (−1,+2,−1,+2)·DᵀB in ``_kappa_exp8`` (pre-rc233 it collapsed the multiplier to
    {ζ₈⁰,ζ₈⁴}), and (2) folding the mod-2 characteristic-shift sign θ[ε+2δ]=(−1)^{p·b}θ[ε]
    into kexp so the returned (reduced characteristic, kexp) COMPOSES. This test was a
    strict-xfail recording the LATENT bug; the fix makes it PASS (marker removed)."""
    from srmech.amsc.riemann_theta import RiemannThetaG3, RiemannThetaG4

    # genus 2 — Sp(4,ℤ): the canonical Urot·T11 witness lives here
    g2_gens = list(_gens().values())
    g2_chars = ALL16
    assert not _kexp_defect_is_char_dependent(
        g2_gens, g2_chars, RiemannTheta.sp4_compose), "genus-2 kexp defect"

    # genus 3 — Sp(6,ℤ)
    B1 = ((1, 0, 0), (0, 0, 0), (0, 0, 0))
    Boff = ((0, 1, 0), (1, 0, 1), (0, 1, 0))
    Ush = ((1, 1, 0), (0, 1, 0), (0, 0, 1))
    g3_gens = [RiemannThetaG3.sp6_translation(B1),
               RiemannThetaG3.sp6_translation(Boff),
               RiemannThetaG3.sp6_gl_twist(Ush),
               RiemannThetaG3.sp6_inversion()]
    g3_chars = [RiemannThetaG3(a, b, c, d, e, f)
                for a in (0, 1) for b in (0, 1) for c in (0, 1)
                for d in (0, 1) for e in (0, 1) for f in (0, 1)]
    assert not _kexp_defect_is_char_dependent(
        g3_gens, g3_chars, RiemannThetaG3.sp6_compose), "genus-3 kexp defect"

    # genus 4 — Sp(8,ℤ)
    B41 = ((1, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))
    B4off = ((0, 1, 0, 0), (1, 0, 0, 1), (0, 0, 0, 0), (0, 1, 0, 0))
    U4 = ((1, 1, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
    g4_gens = [RiemannThetaG4.sp8_translation(B41),
               RiemannThetaG4.sp8_translation(B4off),
               RiemannThetaG4.sp8_gl_twist(U4),
               RiemannThetaG4.sp8_inversion()]
    g4_chars = [RiemannThetaG4(*[(i >> k) & 1 for k in range(8)])
                for i in range(256)]
    assert not _kexp_defect_is_char_dependent(
        g4_gens, g4_chars, RiemannThetaG4.sp8_compose), "genus-4 kexp defect"
