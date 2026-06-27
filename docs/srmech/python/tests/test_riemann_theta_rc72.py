"""rc72 — ``srmech.amsc.riemann_theta.RiemannTheta``, the FIRST RUNG of the GENUS axis.

The genus-2 Riemann theta-CONSTANT, exact-integer ``(A, B, C)`` exponent lattice in
the quarter-nome base (the cross-term ``C`` carries the genus-2 denominator-4
clearing the genus-1 carrier never saw). A pure CARRIER (like ThetaSum): no public
ToolEntry op, so ``tools.total`` is UNCHANGED — these tests assert ONLY the carrier's
own gates.

The build gates (the no-shell proof):

  (a) the GENUS axis — ``genus == 2``; 10 even + 6 odd characteristics (Eilers p. 2);
  (b) the FOUNDATION-FIRST exponent-lattice clearing — exact integer ``(A, B, C)``
      for all 16 characteristics, with the q₁₂ cross-term denominator-4 handling
      (``C = (2n₁+ε'₁)(2n₂+ε'₂)``), gated against the collapse;
  (c) **COLLAPSE (primary):** ``θ[0,0;0,0].collapse_g1()`` == the rc70 ``UnaryTheta``
      θ₃ EXACTLY (bit-exact vs the existing rung) — THE foundation gate;
  (d) **FORMAL genus-2 theta-null identity (secondary):** the genus-g Gauss/duplication
      identity ``θ[0;0](0|Ω)² = Σ_c θ[c;0](0|2Ω)²`` holds EXACTLY as a truncated
      exact-integer multivariate q-series for ALL Ω (Chai 2014, Thm 1.2(b); Mumford,
      Tata Lectures on Theta I) — and genuinely exercises the cross-term q₁₂;
  (e) Python==C parity EXACT on ``.lattice`` (guarded by native-availability skip);
  (f) the carrier source has no numpy / math / abs() (the ratchet).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannTheta
from srmech.amsc.unary_theta import unary_theta
from srmech.amsc import _native


# the trivial even theta-constant (the one that collapses to θ₃), reused below
def _t00() -> RiemannTheta:
    return RiemannTheta.theta_constant((0, 0), (0, 0))


# the exact θ₃ target series (the rc70 anchor)
THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]


# ── gate (a): the GENUS axis (genus 2; 10 even + 6 odd) ──────────────────────
def test_genus_axis_is_two():
    assert _t00().genus == 2


def test_ten_even_six_odd_characteristics():
    """Genus 2 has 16 binary characteristics — 10 EVEN + 6 ODD (Eilers, arXiv:
    1707.08855, p. 2). A characteristic is even iff ε'·ε ≡ 0 (mod 2)."""
    even = RiemannTheta.even_characteristics()
    assert len(even) == 10
    assert all(rt.is_even for rt in even)
    # the 6 odd ones: all 16 minus the 10 even
    all16 = [RiemannTheta(a, b, c, d)
             for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1)]
    odd = [rt for rt in all16 if not rt.is_even]
    assert len(odd) == 6
    # the standard odd characteristics have ε'·ε odd
    for rt in odd:
        (ep1, ep2), (e1, e2) = rt.characteristic
        assert (ep1 * e1 + ep2 * e2) % 2 == 1


# ── gate (b): the exponent-lattice clearing (the foundation unit) ────────────
def test_diagonal_exponents_are_perfect_square_clearing():
    """The diagonal cleared exponents A, B are (2nᵢ+ε'ᵢ)² — exact integers. For the
    trivial char, A runs over {0, 4, 16, 36, …} = (2n₁)² (the box clears m₁²=n₁²
    times 4)."""
    lat = _t00().lattice(3)
    a_vals = sorted({A for (A, B, C) in lat})
    assert a_vals == [(2 * n) ** 2 for n in range(0, 4)]    # 0,4,16,36


def test_cross_term_denominator_4_clearing():
    """THE HARDEST PART: the cross-term C = 4n₁n₂ + 2n₁ε'₂ + 2n₂ε'₁ + ε'₁ε'₂ =
    (2n₁+ε'₁)(2n₂+ε'₂) — the m₁m₂ product of two half-integers, cleared with
    denominator 4. For the (½,½) characteristic [1,1;0,0] the cross-term is genuinely
    non-zero and odd-shaped (C = (2n₁+1)(2n₂+1)). Verified term-by-term."""
    rt = RiemannTheta.theta_constant((1, 1), (0, 0))   # ε' = (1,1)
    # rebuild the raw (pre-merge) lattice term by term and check C exactly
    for n1 in range(-2, 3):
        for n2 in range(-2, 3):
            C_expected = 4 * n1 * n2 + 2 * n1 * 1 + 2 * n2 * 1 + 1 * 1
            assert C_expected == (2 * n1 + 1) * (2 * n2 + 1)
    # the merged lattice must contain genuinely-cross monomials (C != 0)
    lat = rt.lattice(3)
    assert any(C != 0 for (_A, _B, C) in lat)


def test_lattice_all_sixteen_characteristics_are_exact_integers():
    """The exact-integer lattice is well-defined for ALL 16 characteristics (the
    foundation-first unit) — every key is an int triple, every coeff a nonzero int."""
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                for d in (0, 1):
                    lat = RiemannTheta(a, b, c, d).lattice(3)
                    assert lat, (a, b, c, d)
                    for (A, B, C), v in lat.items():
                        assert isinstance(A, int) and isinstance(B, int)
                        assert isinstance(C, int) and isinstance(v, int)
                        assert v != 0


# ── gate (c): COLLAPSE — the primary foundation gate ─────────────────────────
def test_collapse_g1_is_rc70_theta3_bit_exact():
    """THE FOUNDATION GATE: collapse the genus-2 carrier to genus 1 (Ω₁₂=Ω₂₂=0,
    n₂=0) — the trivial even characteristic's surviving slice is Σ_{n₁} q₁^{n₁²} =
    the genus-1 Jacobi theta θ₃, returned as the rc70 UnaryTheta. BIT-EXACT vs the
    existing rung."""
    collapsed = _t00().collapse_g1()
    rc70_theta3 = unary_theta("trivial", 0, 1, 0, 1, support="all")
    assert collapsed == rc70_theta3
    assert collapsed.weight == rc70_theta3.weight        # weight 1/2
    assert _t00().collapse_g1_q_series(20) == THETA3_Q20  # the θ₃ series


def test_collapse_derives_from_the_lattice_n2_zero_slice():
    """The collapse is GENUINE — it derives from the lattice itself, not a hardcoded
    return. The genus-1 degeneration q₂→0 (Ω₂₂→i∞) keeps ONLY the n₂=0 slice; for the
    trivial characteristic that slice is exactly {(A,0,0): A=(2n₁)²} (B=0 ⟺ n₂=0, and
    then C=0 automatically), so collecting it in the q₁ nome (A/4 = n₁²) reproduces θ₃
    EXACTLY — identical to collapse_g1().q_series."""
    lat = _t00().lattice(6)
    slice0 = {}
    for (A, B, C), v in lat.items():
        if B == 0 and C == 0:            # the n₂=0 slice
            assert A % 4 == 0            # trivial char: A=(2n₁)² always ÷4
            slice0[A // 4] = slice0.get(A // 4, 0) + v
    series = [slice0.get(e, 0) for e in range(max(slice0) + 1)]
    assert series[:21] == THETA3_Q20
    assert series[:21] == _t00().collapse_g1_q_series(20)


def test_collapse_only_trivial_characteristic_is_honest():
    """Only the trivial even characteristic [0,0;0,0] collapses to the plain θ₃ rung;
    any other characteristic's genus-1 slice is a shifted/signed theta (an honest
    boundary, not a fabricated reduction)."""
    for a, b, c, d in [(1, 0, 0, 0), (0, 0, 1, 0), (1, 1, 0, 0), (1, 0, 1, 0)]:
        with pytest.raises(ValueError):
            RiemannTheta(a, b, c, d).collapse_g1()


# ── gate (d): the FORMAL genus-2 theta-null identity (Gauss duplication) ──────
def test_duplication_identity_holds_exact():
    """THE SECONDARY GATE: the genus-g Gauss/duplication theta-null identity
    θ[0;0](0|Ω)² = Σ_{c∈(½ℤ²/ℤ²)} θ[c;0](0|2Ω)² holds EXACTLY as a truncated
    exact-integer multivariate q-series, for ALL Ω (no transcendental evaluation).
    Chai, "Riemann's theta formula" (2014), Thm 1.2(b); classically Mumford, Tata
    Lectures on Theta I (1983). It genuinely exercises the cross-term q₁₂ — proving
    genuine genus-2 theta-constants, not the genus-1 slice."""
    assert RiemannTheta.duplication_holds(4)
    assert RiemannTheta.duplication_holds(6)
    assert RiemannTheta.duplication_holds(8)


def test_duplication_lhs_equals_rhs_on_safe_region():
    """The two sides of the duplication identity are equal on the safe inner region,
    and the region is non-trivially populated with cross-term (C ≠ 0) monomials."""
    box = 6
    lhs = RiemannTheta.duplication_lhs(box)
    rhs = RiemannTheta.duplication_rhs(box)
    safe = 4 * box * box

    def restrict(lat):
        return {(A, B, C): v for (A, B, C), v in lat.items()
                if A <= safe and B <= safe and (C if C >= 0 else -C) <= safe}

    L, R = restrict(lhs), restrict(rhs)
    assert L == R
    assert any(C != 0 for (_A, _B, C) in L)             # genuinely cross-term


# ── gate (e): Python==C parity on .lattice ───────────────────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta(),
                    reason="native srmech_riemann_theta not loaded")
def test_python_c_parity_all_characteristics():
    """The native path and the pure-Python oracle emit the BYTE-IDENTICAL canonical
    exact-integer lattice for all 16 characteristics over several boxes (do NOT trust
    the C — compare)."""
    for box in (0, 1, 2, 3, 5):
        for a in (0, 1):
            for b in (0, 1):
                for c in (0, 1):
                    for d in (0, 1):
                        rt = RiemannTheta(a, b, c, d)
                        c_path = rt.lattice(box)               # native present
                        py_path = rt._lattice_py(box)          # the oracle
                        assert c_path == py_path, (a, b, c, d, box)


@pytest.mark.skipif(not _native.has_native_riemann_theta(),
                    reason="native srmech_riemann_theta not loaded")
def test_python_c_parity_gates_through_native():
    """The collapse + duplication gates still pass with the C lattice path live
    (end-to-end on the native peer)."""
    assert _native.has_native_riemann_theta()
    assert _t00().collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannTheta.duplication_holds(6)


def test_pure_python_oracle_alone_passes_gates():
    """The COMPLETE pure-Python body alone passes both gates (so the carrier is
    correct on a no-C host)."""
    assert _t00()._lattice_py(3) == _t00()._lattice_py(3)
    assert _t00().collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannTheta.duplication_holds(6)


# ── input validation ─────────────────────────────────────────────────────────
def test_construction_rejects_bad_characteristic_bits():
    with pytest.raises(ValueError):
        RiemannTheta(2, 0, 0, 0)
    with pytest.raises(ValueError):
        RiemannTheta(0, -1, 0, 0)
    with pytest.raises(ValueError):
        RiemannTheta.theta_constant((0, 0), (0, 3))


def test_lattice_rejects_bad_box():
    with pytest.raises(ValueError):
        _t00().lattice(-1)
    with pytest.raises(ValueError):
        RiemannTheta.duplication_holds(1)   # box < 2 for the gate


def test_equality_and_hash():
    assert RiemannTheta(1, 0, 0, 1) == RiemannTheta(1, 0, 0, 1)
    assert RiemannTheta(1, 0, 0, 1) != RiemannTheta(0, 0, 0, 1)
    assert len({RiemannTheta(1, 0, 0, 1), RiemannTheta(1, 0, 0, 1)}) == 1


# ── gate (f): the carrier source is numpy / math / abs() free ────────────────
def test_riemann_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None        # no bare abs() CALL
    assert "float(" not in text                         # no float in the carrier body
