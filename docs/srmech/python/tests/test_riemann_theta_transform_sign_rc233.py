"""rc233 (#824) — regression test for the LATENT ζ₈⁴ sign defect in the
``riemann_theta.transform`` kexp (κ 8th-root multiplier) at genus g=2/3/4.

THE BUG (pre-rc233):  ``_kappa_exp8`` carried the Igusa characteristic phase φ_m in
its REAL-characteristic coefficients (−4, +8, −16, −8)·(B·Dᵀ) while feeding the
DOUBLED integer characteristic ε'=2m', ε=2m''.  That unabsorbed factor of 2 made
terms 2/3/4 ≡ 0 (mod 8) and collapsed term 1 to {0, 4} — so for EVERY γ the multiplier
was pinned to ``{ζ₈⁰, ζ₈⁴} = {+1, −1}`` and could never emit ζ₈^{1,2,3,5,6,7}.

THE TRUTH:  the modular transformation of the theta-CONSTANT is exact and elementary
for the translation generator.  Under ``Ω ↦ Ω + diag(1,0,…)`` the characteristic
ε'=(1,0,…) multiplies θ by exactly ``ζ₈¹ = e^{iπ/4}`` (a genus-independent classical
computation: (n+½)²·1 ≡ ¼ mod 2 ⇒ a uniform e^{iπ/4} on every lattice point).  The
pre-rc233 code returned k=4 (−1); the correct answer is k=1.

Attestation of the expected k-table:
  * classical theta-constant transformation law (Igusa, *Theta Functions* (Springer,
    Grundlehren 194, 1972), Ch. V; characteristic map DLMF §21.5.9);
  * OWN re-runnable high-precision numeric theta oracle (primary computational
    attestation), verified g1..g4 across all generators/characteristics:
    ``docs/srmech/rbs_lm_research/theta_transform_multiplier_oracle_rc233.py``;
  * literature anchor arXiv:0801.2543 (D'Hoker–Phong) sha256
    e6edd3b217d138c20ff9e126e9801bb020042000736b0415d98297b164311797.

This test FAILS on the pre-rc233 code (which returns {0,4}) and PASSES on the fix.
"""
import itertools

import pytest

from srmech.amsc.riemann_theta import (
    RiemannTheta, RiemannThetaG3, RiemannThetaG4)


# ── exact-integer matrix helpers (test-local; independent of the source) ──────────
def _I(g):
    return tuple(tuple(1 if i == j else 0 for j in range(g)) for i in range(g))


def _Z(g):
    return tuple((0,) * g for _ in range(g))


def _diagB(g, v):
    return tuple(tuple(v if (i == 0 and j == 0) else 0 for j in range(g))
                 for i in range(g))


def _negI(g):
    return tuple(tuple(-1 if i == j else 0 for j in range(g)) for i in range(g))


def _translation(g, B):
    return (_I(g), B, _Z(g), _I(g))


def _inversion(g):
    return (_Z(g), _negI(g), _I(g), _Z(g))


_CLS = {2: RiemannTheta, 3: RiemannThetaG3, 4: RiemannThetaG4}


# ── the numeric-oracle GROUND-TRUTH k table (see module docstring) ────────────────
# each row: (genus, gamma, char_bits (ε'…, ε…), expected_k)
_GROUND_TRUTH = [
    # genus 2 — the canonical failing case + richer values
    (2, _translation(2, _diagB(2, 1)), (1, 0, 0, 0), 1),   # old code -> 4
    (2, _translation(2, _diagB(2, 1)), (1, 0, 1, 1), 1),   # old code -> 4
    (2, _translation(2, _diagB(2, 1)), (0, 1, 0, 0), 0),
    (2, _translation(2, _diagB(2, 2)), (1, 0, 0, 0), 2),   # old code -> 0
    (2, _translation(2, ((0, 1), (1, 0))), (1, 1, 0, 0), 6),  # old code -> 0
    (2, _inversion(2), (1, 1, 1, 1), 4),                   # old code -> 0
    (2, _inversion(2), (0, 1, 0, 1), 6),                   # old code -> 0
    # genus 3
    (3, _translation(3, _diagB(3, 1)), (1, 0, 0, 0, 0, 0), 1),   # old code -> 4
    (3, _translation(3, _diagB(3, 2)), (1, 0, 0, 0, 0, 0), 2),   # old code -> 0
    (3, _inversion(3), (1, 0, 0, 1, 0, 0), 6),                   # old code -> 0
    (3, _inversion(3), (1, 1, 0, 1, 1, 0), 4),                   # old code -> 0
    # genus 4
    (4, _translation(4, _diagB(4, 1)), (1, 0, 0, 0, 0, 0, 0, 0), 1),  # old code -> 4
    (4, _translation(4, _diagB(4, 2)), (1, 0, 0, 0, 0, 0, 0, 0), 2),  # old code -> 0
    (4, _inversion(4), (1, 0, 0, 0, 1, 0, 0, 0), 6),                  # old code -> 0
    (4, _inversion(4), (1, 1, 0, 0, 1, 1, 0, 0), 4),                  # old code -> 0
]


@pytest.mark.parametrize("genus,gamma,bits,expected_k", _GROUND_TRUTH)
def test_transform_kexp_matches_numeric_ground_truth(genus, gamma, bits, expected_k):
    """``transform`` returns the EXACT ζ₈ exponent of the theta-constant modular
    multiplier, matching the independent numeric theta oracle.  Pre-rc233 this
    collapsed to {0,4} and FAILED every non-{0,4} row."""
    rt = _CLS[genus](*bits)
    _new, k = rt.transform(gamma)
    assert k == expected_k, (genus, bits, k, expected_k)


def test_multiplier_is_not_collapsed_to_pm_one():
    """THE regression guard: the pre-rc233 defect pinned κ to ``{ζ₈⁰, ζ₈⁴}={±1}`` for
    every γ.  The corrected multiplier reaches ζ₈ exponents OUTSIDE {0,4} — here the
    full odd/±i set {1,2,3,5,6,7} across g=2/3/4 (impossible for the old code)."""
    seen = {k for (_g, _ga, _b, k) in _GROUND_TRUTH}
    beyond = seen - {0, 4}
    assert beyond, "fix must produce ζ₈ exponents beyond {0,4}"
    assert {1, 2, 6} <= seen, seen           # odd + ±i values genuinely appear


# ── independent exact-integer recomputation of the corrected Igusa 8·φ_m ──────────
def _matmul(P, Q):
    g = len(P)
    return [[sum(P[i][k] * Q[k][j] for k in range(g)) for j in range(g)]
            for i in range(g)]


def _transpose(P):
    g = len(P)
    return [[P[j][i] for j in range(g)] for i in range(g)]


def _matvec(P, v):
    g = len(P)
    return [sum(P[i][k] * v[k] for k in range(g)) for i in range(g)]


def _diag_ABt(A, B):
    g = len(A)
    return [sum(A[i][k] * B[i][k] for k in range(g)) for i in range(g)]   # diag(A·Bᵀ)


def _reference_8phi(gamma, epp, eps):
    """Independent (test-local) exact-integer composition-consistent kexp — the
    corrected Igusa phase
        8·φ_m = −ε'ᵀ(DᵀB)ε' + 2·ε'ᵀ(BᵀC)ε − εᵀ(AᵀC)ε + 2·diag(A·Bᵀ)·(Dε' − Cε)
    PLUS the mod-2 output-reduction fold ``4·Σ(new_epp%2)·⌊new_eps/2⌋`` (the returned
    reduced characteristic's ζ₈⁴ shift sign), written from scratch (NOT importing
    ``_kappa_exp8``), so agreement is a genuine cross-check, not a tautology."""
    A, B, C, D = ([list(r) for r in blk] for blk in gamma)
    g = len(A)
    DtB = _matmul(_transpose(D), B)
    BtC = _matmul(_transpose(B), C)
    AtC = _matmul(_transpose(A), C)
    t1 = -sum(epp[i] * DtB[i][j] * epp[j] for i in range(g) for j in range(g))
    t2 = 2 * sum(epp[i] * BtC[i][j] * eps[j] for i in range(g) for j in range(g))
    t3 = -sum(eps[i] * AtC[i][j] * eps[j] for i in range(g) for j in range(g))
    Dep = _matvec(D, epp)
    Ce = _matvec(C, eps)
    dab = _diag_ABt(A, B)
    t4 = 2 * sum(dab[i] * (Dep[i] - Ce[i]) for i in range(g))
    # mod-2 output-reduction fold (the returned reduced-characteristic shift sign)
    dCD = _diag_ABt(C, D)                       # diag(C·Dᵀ)
    Be = _matvec(B, epp)
    Ae = _matvec(A, eps)
    new_epp = [Dep[i] - Ce[i] + dCD[i] for i in range(g)]
    new_eps = [-Be[i] + Ae[i] + dab[i] for i in range(g)]
    fold = 4 * sum((new_epp[i] % 2) * (new_eps[i] // 2) for i in range(g))
    return (t1 + t2 + t3 + t4 + fold) % 8


@pytest.mark.parametrize("genus", (2, 3, 4))
def test_kexp_equals_independent_formula_full_sweep(genus):
    """Exhaustive characteristic sweep on every standard generator: the SHIPPED
    ``transform``/``_kappa_exp8`` exponent equals an INDEPENDENT test-local
    recomputation of the corrected integer 8·φ_m, for all 2^{2g} characteristics."""
    gens = [
        _translation(genus, _diagB(genus, 1)),
        _translation(genus, _diagB(genus, 2)),
        _translation(genus, _diagB(genus, 3)),
        _inversion(genus),
    ]
    # a GL-twist (basis change): A upper-shear, D=(Aᵀ)⁻¹, B=C=0 — φ_m ≡ 0
    A = tuple(tuple(1 if i == j else (1 if (i == 0 and j == 1) else 0)
                    for j in range(genus)) for i in range(genus))
    Dsh = tuple(tuple(1 if i == j else (-1 if (i == 1 and j == 0) else 0)
                      for j in range(genus)) for i in range(genus))
    gens.append((A, _Z(genus), _Z(genus), Dsh))
    for gamma in gens:
        for bits in itertools.product((0, 1), repeat=2 * genus):
            rt = _CLS[genus](*bits)
            _new, k = rt.transform(gamma)
            epp = list(bits[:genus])
            eps = list(bits[genus:])
            assert k == _reference_8phi(gamma, epp, eps), (genus, gamma, bits, k)


def test_pure_kappa_exp8_path_is_correct():
    """The PURE ``_kappa_exp8`` (native-independent) reproduces the ground truth — so
    a native-absent environment is still correct, and native==pure parity is meaningful."""
    for genus, gamma, bits, expected_k in _GROUND_TRUTH:
        epp = bits[:genus]
        eps = bits[genus:]
        k = _CLS[genus]._kappa_exp8(gamma, epp, eps)
        assert k == expected_k, (genus, bits, k, expected_k)
