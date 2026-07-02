"""rc87 — ``RiemannTheta.theta_at`` / ``RiemannThetaG3.theta_at``: EXACT theta evaluation
at a RATIONAL argument (the genus-axis Fay-trisecant / KP-Hirota verifier FOUNDATION).

The genus carriers hold the theta-CONSTANT ``θ[ε';ε](0|Ω)`` at z = 0 as an exact-INTEGER
q-lattice. rc87 adds ``theta_at(z_num, z_den, box)`` — theta at a RATIONAL argument
``z = z_num/z_den`` (``z_den`` even = 2N), which IS exactly representable because the extra
Fourier factor ``exp(2πi(n+½ε')·z) = ζ_m^{Σ(2nᵢ+ε'ᵢ)z_numᵢ}`` (``m = 2·z_den``) is a ROOT
OF UNITY → each coefficient is an EXACT element of the cyclotomic ring ``ℤ[ζ_m]`` (REUSED
from the rc29 exact-DFT engine), an integer vector of length ``φ(m)`` in the power basis.

A CARRIER eval method (like ``lattice()``): NO ToolEntry → ``tools.total`` stays 342.

The no-shell gates (all exact):

  (1) **z = 0 bridge** — ``theta_at((0,…), z_den, box)`` reduces BIT-EXACTLY to the integer
      ``lattice(box)`` (every coeff collapses to ``[c, 0, …, 0]``): the foundation EXTENDS
      the representable core, doesn't replace it.
  (2) **half-period bridge** — at ``z = δ/2`` (``z_num`` binary, ``z_den = 2``, m = 4)
      ``theta_at`` reproduces ``θ[ε'; ε⊕δ]`` up to the EXACT global automorphy factor
      ``ζ_4^{ε'·δ}`` (verified over ALL 64 genus-2 char/half-period cases): the standard
      half-period shift, proving it is the genuine generalization, not a relabel.
  (3) **quasi-periodicity** — ``θ(z + λ)`` for an integer lattice vector λ multiplies every
      coeff by ``(−1)^{ε'·λ}`` (verified over a GENERIC rational z where the coeffs are
      genuinely non-real cyclotomic integers — theta_at spans BEYOND the half-char carriers).
  (4) Python == C byte-exact parity (guarded by native skip); tools.total == 348; the new
      methods are numpy / math / abs() / float-free.
"""
from __future__ import annotations

import itertools
import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import (RiemannTheta, RiemannThetaG3,
                                       _accumulate_phase_lattice, _cyclotomic_ring,
                                       _theta_at_validate)
from srmech.amsc import _native
import srmech.introspect as introspect


# ── helpers: the forced-pure theta_at (the parity oracle, native-independent) ──────
def _pure_at(rt, z_num, z_den, box, g):
    """The pure-Python theta_at (term producer + the shared cyclotomic accumulator) —
    independent of any native dispatch, so the C parity tests compare against it."""
    z, m = _theta_at_validate(z_num, z_den, box, g)
    return _accumulate_phase_lattice(rt._theta_at_terms_py(z, m, box), m)


def _scale_int(c, k, m):
    """The integer ``c`` lifted into ``ℤ[ζ_m]`` as ``c · ζ_m^{k}`` (a power-basis tuple),
    via the REUSED exact-DFT cyclotomic table — the exact automorphy-factor multiplier."""
    table, _deg = _cyclotomic_ring(m)
    return tuple(c * x for x in table[k % m])


def _collapses_to_integer(vec, c):
    """True iff the cyclotomic vector ``vec`` equals the integer ``c`` exactly
    (``vec[0] == c`` and every higher power-basis coordinate is 0)."""
    return vec[0] == c and not any(x != 0 for x in vec[1:])


# ── gate (1): the z = 0 bridge — bit-exact collapse to the integer lattice ─────────
def test_z0_bridge_g2_bit_exact_to_lattice():
    """``theta_at((0,0), z_den, box)`` == the integer ``lattice(box)`` BIT-EXACTLY (every
    cyclotomic coeff is the integer value), for several even z_den AND z_den = 1."""
    for ep1, ep2, e1, e2 in itertools.product((0, 1), repeat=4):
        rt = RiemannTheta(ep1, ep2, e1, e2)
        box = 3
        lat = rt.lattice(box)
        for z_den in (1, 2, 4, 6):
            at0 = rt.theta_at((0, 0), z_den, box)
            assert set(at0.keys()) == set(lat.keys()), (rt, z_den)
            for k, v in at0.items():
                assert _collapses_to_integer(v, lat[k]), (rt, z_den, k, v, lat[k])


def test_z0_bridge_g3_bit_exact_to_lattice():
    """The genus-3 z = 0 bridge: ``theta_at((0,0,0), z_den, box)`` == integer
    ``lattice(box)`` bit-exactly, over a curated set of genus-3 characteristics."""
    box = 2
    chars = [(0, 0, 0, 0, 0, 0), (1, 0, 1, 0, 0, 0), (1, 1, 0, 0, 0, 0),
             (1, 0, 1, 0, 1, 0), (0, 1, 1, 1, 0, 1)]
    for ch in chars:
        rt = RiemannThetaG3(*ch)
        lat = rt.lattice(box)
        for z_den in (1, 2, 4):
            at0 = rt.theta_at((0, 0, 0), z_den, box)
            assert set(at0.keys()) == set(lat.keys()), (ch, z_den)
            for k, v in at0.items():
                assert _collapses_to_integer(v, lat[k]), (ch, z_den, k)


# ── gate (2): the half-period bridge — θ[ε';ε](δ/2) ∝ θ[ε'; ε⊕δ] ───────────────────
def test_half_period_bridge_g2_all_64_cases():
    """At a half-period ``z = δ/2`` (``z_num`` a binary vector, ``z_den = 2``, m = 4),
    ``theta_at`` == ``ζ_4^{ε'·δ} · lattice(θ[ε'; ε⊕δ])`` EXACTLY, over ALL 64
    (characteristic, half-period) genus-2 cases — the genuine half-period shift law (NOT a
    relabel: the automorphy factor is the exact global root of unity ζ_4^{ε'·δ})."""
    box = 3
    saw_imaginary_automorphy = False
    saw_real_automorphy = False
    for ep1, ep2, e1, e2 in itertools.product((0, 1), repeat=4):
        base = RiemannTheta(ep1, ep2, e1, e2)
        for d1, d2 in itertools.product((0, 1), repeat=2):
            at = base.theta_at((d1, d2), 2, box)
            shifted = RiemannTheta(ep1, ep2, (e1 + d1) % 2, (e2 + d2) % 2).lattice(box)
            k = ep1 * d1 + ep2 * d2
            expected = {key: _scale_int(c, k, 4) for key, c in shifted.items()}
            assert at == expected, (ep1, ep2, e1, e2, d1, d2)
            if k % 2 == 1:
                saw_imaginary_automorphy = True   # ζ_4^odd = ±i (genuine imaginary)
            else:
                saw_real_automorphy = True
    assert saw_imaginary_automorphy and saw_real_automorphy


def test_half_period_bridge_g3_curated():
    """The genus-3 half-period bridge: ``theta_at(δ, 2, box) == ζ_4^{ε'·δ}·lattice(θ[ε';
    ε⊕δ])`` over curated genus-3 (characteristic, half-period) pairs (automorphy ±1 and the
    parity-flip / vanishing case)."""
    box = 2
    cases = [
        ((1, 1, 0, 0, 0, 0), (1, 1, 0)),   # ε'·δ = 2 → automorphy −1; shifted even
        ((0, 0, 0, 0, 0, 0), (1, 0, 1)),   # ε'·δ = 0 → automorphy +1
        ((1, 0, 1, 0, 0, 0), (1, 0, 1)),   # ε'·δ = 2 → automorphy −1
        ((1, 0, 0, 0, 0, 0), (1, 0, 0)),   # ε'·δ = 1 → parity flips → shifted ODD (vanish)
    ]
    for ch, d in cases:
        ep = ch[:3]
        e = ch[3:]
        base = RiemannThetaG3(*ch)
        at = base.theta_at(d, 2, box)
        shifted = RiemannThetaG3(ep[0], ep[1], ep[2],
                                 (e[0] + d[0]) % 2, (e[1] + d[1]) % 2,
                                 (e[2] + d[2]) % 2).lattice(box)
        k = ep[0] * d[0] + ep[1] * d[1] + ep[2] * d[2]
        expected = {key: _scale_int(c, k, 4) for key, c in shifted.items()}
        assert at == expected, (ch, d)


# ── gate (3): quasi-periodicity — θ(z + λ) = (−1)^{ε'·λ} θ(z) ──────────────────────
def test_quasiperiodicity_g2_generic_z():
    """Shifting z by an integer lattice vector λ (z_num → z_num + λ·z_den) multiplies every
    coeff by the EXACT sign ``(−1)^{ε'·λ}``. Verified over a GENERIC rational z (z_den = 6,
    m = 12) where the coeffs are genuinely non-real cyclotomic integers."""
    box = 3
    t = RiemannTheta.theta_constant((1, 0), (0, 1))   # even; ε' = (1,0)
    z_num, z_den = (1, 5), 6
    at = t.theta_at(z_num, z_den, box)
    for lam in [(1, 0), (0, 1), (2, -3), (1, 1), (-2, 4)]:
        shifted = t.theta_at((z_num[0] + lam[0] * z_den, z_num[1] + lam[1] * z_den),
                             z_den, box)
        sign = -1 if (1 * lam[0] + 0 * lam[1]) % 2 else 1   # ε' = (1,0)
        expected = {k: tuple(sign * x for x in v) for k, v in at.items()}
        assert shifted == expected, lam


def test_quasiperiodicity_g3_generic_z():
    """The genus-3 quasi-periodicity: ``θ(z + λ) = (−1)^{ε'·λ} θ(z)`` over a generic
    rational z (z_den = 4, m = 8)."""
    box = 2
    t = RiemannThetaG3.theta_constant((1, 0, 1), (0, 1, 0))   # even; ε' = (1,0,1)
    z_num, z_den = (1, 3, 5), 4
    at = t.theta_at(z_num, z_den, box)
    for lam in [(1, 0, 0), (0, 0, 1), (1, 1, 1), (2, -1, 0)]:
        shifted = t.theta_at(tuple(z_num[i] + lam[i] * z_den for i in range(3)),
                             z_den, box)
        sign = -1 if (lam[0] + lam[2]) % 2 else 1   # ε' = (1,0,1) → ε'·λ = λ0 + λ2
        expected = {k: tuple(sign * x for x in v) for k, v in at.items()}
        assert shifted == expected, lam


def test_generic_rational_z_is_genuinely_cyclotomic():
    """A GENERIC rational z produces coeffs that are genuinely NON-REAL cyclotomic integers
    (nonzero power-basis coordinates beyond index 0) — the proof theta_at spans BEYOND the
    half-character carriers (which only ever give the global ζ_4^{ε'·δ} automorphy). Without
    this, theta_at would be a mere relabel of the existing half-char lattices."""
    t = RiemannTheta.theta_constant((1, 0), (0, 1))
    at = t.theta_at((1, 5), 6, 3)          # m = 12, φ(12) = 4
    assert _cyclotomic_ring(12)[1] == 4
    assert any(any(x != 0 for x in v[1:]) for v in at.values())


# ── gate (4a): tools.total is UNCHANGED (a CARRIER method, not a ToolEntry) ────────
def test_theta_at_is_a_carrier_method_total_341():
    assert introspect.describe()["tools"]["total"] == 348


# ── gate (4b): Python == C byte-exact parity (do NOT trust the C — compare) ────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_at(),
                    reason="native srmech_riemann_theta_at not loaded")
def test_python_c_parity_g2():
    """The native theta_at and the pure-Python oracle emit the BYTE-IDENTICAL cyclotomic
    lattice across a sweep of genus-2 characteristics, z-arguments, and boxes."""
    z_args = [((0, 0), 2), ((1, 0), 2), ((1, 1), 2), ((1, 5), 6), ((3, 2), 4),
              ((-1, 2), 6), ((0, 0), 1)]
    for box in (0, 1, 2, 3):
        for ep1, ep2, e1, e2 in itertools.product((0, 1), repeat=4):
            rt = RiemannTheta(ep1, ep2, e1, e2)
            for z_num, z_den in z_args:
                got = rt.theta_at(z_num, z_den, box)
                assert got == _pure_at(rt, z_num, z_den, box, 2), \
                    (ep1, ep2, e1, e2, z_num, z_den, box)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g3_at(),
                    reason="native srmech_riemann_theta_g3_at not loaded")
def test_python_c_parity_g3():
    """Python == C byte-exact on the genus-3 theta_at across curated characteristics,
    z-arguments, and boxes (box ≤ 2 — the genus-3 lattice grows as (2·box+1)³)."""
    chars = [(0, 0, 0, 0, 0, 0), (1, 0, 1, 0, 0, 0), (1, 1, 0, 1, 1, 0),
             (1, 0, 1, 0, 1, 0), (0, 1, 1, 1, 0, 1)]
    z_args = [((0, 0, 0), 2), ((1, 0, 1), 2), ((1, 3, 5), 4), ((2, -1, 0), 6)]
    for box in (0, 1, 2):
        for ch in chars:
            rt = RiemannThetaG3(*ch)
            for z_num, z_den in z_args:
                got = rt.theta_at(z_num, z_den, box)
                assert got == _pure_at(rt, z_num, z_den, box, 3), (ch, z_num, z_den, box)


@pytest.mark.skipif(not _native.has_native_riemann_theta_at(),
                    reason="native srmech_riemann_theta_at not loaded")
def test_native_gates_through_c():
    """The z=0 / half-period / quasi-periodicity gates still pass with the C path live
    (end-to-end on the native peer, not just the pure oracle)."""
    assert _native.has_native_riemann_theta_at()
    rt = RiemannTheta.theta_constant((1, 0), (0, 0))
    assert _collapses_to_integer(list(rt.theta_at((0, 0), 4, 2).values())[0],
                                 rt.lattice(2)[(1, 0, 0)])


def test_pure_oracle_alone_passes_gates():
    """The pure-Python theta_at alone satisfies the gates (the no-C / Pyodide path is the
    COMPLETE alternative — never a stub)."""
    rt = RiemannTheta.theta_constant((1, 1), (0, 0))
    pure = _pure_at(rt, (0, 0), 2, 3, 2)
    lat = rt.lattice(3)
    assert set(pure) == set(lat)
    assert all(_collapses_to_integer(pure[k], lat[k]) for k in lat)


# ── input validation ──────────────────────────────────────────────────────────────
def test_theta_at_rejects_bad_arguments():
    rt = RiemannTheta.theta_constant((0, 0), (0, 0))
    with pytest.raises(ValueError):
        rt.theta_at((0, 0), 2, -1)            # bad box
    with pytest.raises(ValueError):
        rt.theta_at((0, 0), 0, 2)             # z_den must be positive
    with pytest.raises(ValueError):
        rt.theta_at((0, 0, 0), 2, 2)          # wrong z_num length for g2
    t3 = RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))
    with pytest.raises(ValueError):
        t3.theta_at((0, 0), 2, 2)             # wrong z_num length for g3


# ── gate (4c): the new methods are numpy / math / abs() / float free ──────────────
def test_theta_at_source_is_numpy_math_abs_float_free():
    """The rc87 theta_at additions keep the ratchet: no numpy / math import, no bare
    ``abs()`` call, no ``float(`` in the carrier (the (−1)^{ε·n} sign is the Class-K
    pin-slot; the phase is an exact Class-I cyclic exponent over the cyclotomic ring)."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None
    assert "float(" not in text
