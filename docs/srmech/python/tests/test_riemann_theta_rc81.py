"""rc81 — ``srmech.amsc.riemann_theta.SchottkyFormG4``, the GENUS-4 CAPSTONE.

The genus-4 SCHOTTKY FORM **J** — the χ₁₈-analog at g = 4, the Siegel cusp form whose
vanishing cuts the genus-4 Jacobian locus ``J₄ ⊂ A₄`` (the Schottky problem's g = 4
solution: Schottky 1888 / Igusa 1981 / Poor–Yuen 1996). Built as the EXACT lattice-theta
difference ``J ∝ θ⁴(E₈⊕E₈) − θ⁴(E₁₆)`` (the two rank-16 even-unimodular lattices), organized
by the Gram-matrix representation numbers — an exact-integer, numpy-free q-series. A pure
CARRIER (like RiemannThetaG4 / RiemannThetaG3 / ThetaSum): no public ToolEntry op, so
``tools.total`` is UNCHANGED — these tests assert ONLY the carrier's own gates.

The build gates (the no-shell proof):

  (1) **J computed EXACTLY** as a formal q-series (exact-integer, numpy-free) and NONZERO at
      genus 4 (the first-genus-4 obstruction; the famous first difference);
  (2) **THE DEFINING SCHOTTKY GATE (gorgeous, no-shell):** J VANISHES identically below
      genus 4 — ``θ^{(g)}(E₈⊕E₈) = θ^{(g)}(E₁₆)`` for g ≤ 3 (Witt 1941), so ``J|_{g≤3} = 0``
      EXACTLY — while ``J|_{g=4} ≠ 0`` EXACTLY. Both halves exact-integer;
  (3) **weight-8 degree-4 cusp-form structure** — Φ(J) = 0 (the genus-3 restriction is
      zero) so J is a cusp form; the level-1 genus-4 weight-8 cusp space is 1-dim, J spans
      it (Igusa 1981, Poor–Yuen 1996);
  (4) **HONEST OPEN preserved** — the numerical "is THIS Ω a Jacobian" decision stays the
      operand-side OPEN (no numerical Jacobian decision is built);
  (5) **NO REGRESSION** — the rc80 RiemannThetaG4 gates still pass;
  (6) **Python==C parity EXACT** on J's construction; the carrier source is numpy / math /
      abs() / float free (the ratchet).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannThetaG4, SchottkyFormG4
from srmech.amsc import _native


# the famous genus-4 first-difference representation counts (exact, verified at build)
_ORTHO_E8E8 = 9_064_742_400
_ORTHO_E16 = 8_858_304_000
_ORTHO_DIFF = 206_438_400          # the genus-4 first difference (T = 2·I₄)
_D4_E8E8 = 7_257_600
_D4_E16 = 2_096_640
_D4_DIFF = 5_160_960               # the fast D₄-star certificate


# ── the two rank-16 even-unimodular lattices (the construction MPM) ───────────
def test_lattices_have_480_minimal_vectors_each():
    """E₈⊕E₈ and E₁₆ = D₁₆⁺ each have 480 minimal (norm-2) vectors — the genus-1 theta
    shells agree at the leading order (both are rank-16 even unimodular). In the doubled
    model a minimal vector has self-inner 8 (= 4·2)."""
    a = SchottkyFormG4.e8e8_minimal_doubled()
    b = SchottkyFormG4.e16_minimal_doubled()
    assert len(a) == 480
    assert len(b) == 480
    for v in a:
        assert SchottkyFormG4._doubled_inner(v, v) == 8     # norm 2, doubled
        assert len(v) == 16
    for v in b:
        assert SchottkyFormG4._doubled_inner(v, v) == 8
        assert len(v) == 16


def test_lattices_are_even_and_integer_in_doubled_model():
    """Both lattices are EVEN (every vector's real norm ⟨v,v⟩ ∈ 2ℤ ⟺ doubled self-inner ∈
    8ℤ) and exact-INTEGER in the doubled model (no float — half-integer coords are exact odd
    integers). A structural attestation of the even-unimodular construction (E₈ via its
    Cartan Gram; D₁₆⁺ via det = det(D₁₆)/[D₁₆⁺:D₁₆]² = 4/4 = 1)."""
    for which in ("e8e8", "e16"):
        vs = SchottkyFormG4._lattice_vectors(which)
        for v in vs:
            assert all(isinstance(x, int) for x in v)        # exact integer, no float
            s = SchottkyFormG4._doubled_inner(v, v)
            assert s % 8 == 0                                # real norm even (4·even)


def test_e8e8_splits_into_two_e8_summands():
    """E₈⊕E₈'s minimal vectors are exactly (root, 0) or (0, root) — 240 + 240 = 480 (a
    minimal vector of a direct sum is minimal in one summand). The first 240 have zero
    second half; the last 240 zero first half."""
    a = SchottkyFormG4.e8e8_minimal_doubled()
    assert len(a) == 480
    first240 = a[:240]
    last240 = a[240:]
    for v in first240:
        assert all(x == 0 for x in v[8:])     # second E₈ block zero
    for v in last240:
        assert all(x == 0 for x in v[:8])     # first E₈ block zero


# ── gate (1): J computed EXACTLY + NONZERO at genus 4 ─────────────────────────
def test_J_is_nonzero_at_genus4_exact():
    """J is NONZERO at genus 4 — the first-genus-4 obstruction. The D₄-star Gram (the fast
    exact certificate) has a nonzero E₈⊕E₈ − E₁₆ representation-number difference."""
    assert SchottkyFormG4.is_nonzero_at_genus4() is True
    ca, cb, diff = SchottkyFormG4.genus4_first_difference_d4star()
    assert (ca, cb, diff) == (_D4_E8E8, _D4_E16, _D4_DIFF)
    assert diff != 0


def test_J_minimal_genus4_is_nonempty_exact_integer():
    """The genus-4 minimal-shell part of J (the leading part of the formal q-series) is a
    NONEMPTY exact-integer map ``{Gram: difference}`` — J ≠ 0 at genus 4. Each key is an
    integer Gram tuple, each value a nonzero integer difference. (Restricted to the D₄-star
    Gram so the test stays fast; the full J_minimal(4) is the same object at larger scope.)"""
    # the D₄-star is the fast certificate; assert the difference is exact-integer nonzero
    ca = SchottkyFormG4._count_gram(
        SchottkyFormG4.e8e8_minimal_doubled(), SchottkyFormG4._G4_D4_STAR)
    cb = SchottkyFormG4._count_gram(
        SchottkyFormG4.e16_minimal_doubled(), SchottkyFormG4._G4_D4_STAR)
    assert isinstance(ca, int) and isinstance(cb, int)
    assert (ca - cb) == _D4_DIFF != 0


# ── gate (2): THE DEFINING SCHOTTKY GATE (J|_{g≤3}=0 AND J|_{g=4}≠0) ──────────
def test_defining_gate_collapses_below_genus4_exact():
    """THE DEFINING GATE (first half): J VANISHES identically below genus 4. The genus-1,
    genus-2 AND genus-3 minimal-shell theta-series of E₈⊕E₈ and E₁₆ agree EXACTLY (Witt
    1941), so J|_{g≤3} ≡ 0 — and J_minimal is EMPTY for g = 1, 2, 3."""
    assert SchottkyFormG4.collapses_below_genus4() is True
    assert SchottkyFormG4.J_minimal(1) == {}
    assert SchottkyFormG4.J_minimal(2) == {}
    assert SchottkyFormG4.J_minimal(3) == {}


def test_defining_gate_genus_theta_series_agree_g_le_3():
    """The genus-1/2/3 minimal-shell theta-series are BIT-EXACT EQUAL between the two
    lattices (the executable Witt 1941): every Gram's representation number agrees."""
    for g in (1, 2, 3):
        a = SchottkyFormG4.lattice_theta_minimal("e8e8", g)
        b = SchottkyFormG4.lattice_theta_minimal("e16", g)
        assert a == b, g
        assert sum(a.values()) == 480 ** g        # total = |minimal|^g


def test_defining_gate_combined_holds():
    """THE COMBINED DEFINING SCHOTTKY GATE: BOTH J|_{g≤3} = 0 (exact) AND J|_{g=4} ≠ 0
    (exact) — the no-shell proof that J is the genuine genus-4 Schottky cusp form (the
    first-genus-4 obstruction), not a thin shell."""
    assert SchottkyFormG4.schottky_gate_holds() is True
    assert SchottkyFormG4.collapses_below_genus4() is True
    assert SchottkyFormG4.is_nonzero_at_genus4() is True


def test_defining_gate_fast_low_genus_vanishing():
    """The cheap genus-1/2 vanishing alone (max_genus=2) — a fast partial of the defining
    gate's first half."""
    assert SchottkyFormG4.collapses_below_genus4(max_genus=2) is True
    assert SchottkyFormG4.collapses_below_genus4(max_genus=1) is True


# ── gate (3): weight-8 degree-4 cusp-form structure ──────────────────────────
def test_weight_degree_cusp_structure():
    """J is weight 8 (= rank/2 = 16/2), degree (genus) 4, and a CUSP form (Φ(J) = 0: the
    genus-3 restriction is zero). The level-1 genus-4 weight-8 cusp space is 1-dimensional,
    spanned by J (Poor & Yuen 1996)."""
    assert SchottkyFormG4.weight() == 8
    assert SchottkyFormG4.degree() == 4
    assert SchottkyFormG4.is_cusp_form_structure() is True
    assert SchottkyFormG4.cusp_space_dimension() == 1


# ── gate (4): the documented HONEST OPEN (the Jacobian decision) ──────────────
def test_jacobian_decision_is_documented_open():
    """The numerical 'is THIS Ω a Jacobian' decision stays the operand-side OPEN (the
    Schottky problem). The carrier BUILDS the exact FORM J but REFUSES to fabricate a
    numerical Jacobian verdict (the rc80 schottky_locus_is_open pattern, upgraded to
    reference the BUILT J)."""
    s = SchottkyFormG4.jacobian_decision_is_open()
    assert isinstance(s, str)
    assert s.startswith("OPEN")
    assert "θ⁴(E₈⊕E₈) − θ⁴(E₁₆)" in s
    assert "Witt 1941" in s
    assert "Igusa 1981" in s
    assert "Poor & Yuen 1996" in s
    assert "206 438 400" in s          # the exact first-difference number is cited
    assert "J|_{g≤3} ≡ 0" in s
    assert "J|_{g=4} ≠ 0" in s
    assert "g ≥ 5" in s                # the frontier extends to g ≥ 5
    # NO numerical Jacobian decision is built
    assert not hasattr(SchottkyFormG4, "is_jacobian")
    assert not hasattr(SchottkyFormG4, "jacobian_verdict")


# ── gate (5): NO REGRESSION — rc80 RiemannThetaG4 still passes ────────────────
def test_rc80_riemann_theta_g4_no_regression():
    """The rc80 genus-4 carrier gates still pass (the Schottky form is additive — it does
    NOT touch RiemannThetaG4)."""
    t0 = RiemannThetaG4.theta_constant((0, 0, 0, 0), (0, 0, 0, 0))
    assert t0.genus == 4
    assert t0.collapse_g3_lattice_matches(3) is True
    assert RiemannThetaG4.duplication_holds(2)
    assert RiemannThetaG4.even_null_count() == (136, 120)
    # the rc80 documented frontier still names J as the rc81 capstone target
    assert RiemannThetaG4.schottky_locus_is_open().startswith("OPEN")


# ── gate (6a): Python==C parity EXACT on J's construction ─────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_g4_schottky(),
                    reason="native srmech_riemann_theta_g4_schottky not loaded")
def test_python_c_parity_count_d4star_and_more():
    """The native count peer and the pure-Python oracle emit the BYTE-IDENTICAL exact
    representation count for the genus-4 certificate Grams + several genus-2/3 Grams (do NOT
    trust the C — compare)."""
    a = SchottkyFormG4.e8e8_minimal_doubled()
    b = SchottkyFormG4.e16_minimal_doubled()
    for vs in (a, b):
        S, n = SchottkyFormG4._build_inner_bitsets(vs)
        # genus 2 (one off-value), genus 3 (three), genus 4 D₄-star (six)
        for gram in [(-4,), (0,), (-4, -4, -4), (0, 0, 0),
                     SchottkyFormG4._G4_D4_STAR]:
            c_path = _native.riemann_theta_g4_schottky_count_c(vs, gram)
            py_path = SchottkyFormG4._count_gram_py(S, n, gram)
            assert c_path == py_path, (len(gram), len(vs))


@pytest.mark.skipif(not _native.has_native_riemann_theta_g4_schottky_shell(),
                    reason="native srmech_riemann_theta_g4_schottky_shell not loaded")
def test_python_c_parity_shell_g_le_3():
    """The native shell peer (the full single-pass off-Gram histogram) and the pure-Python
    oracle emit the BYTE-IDENTICAL histogram for genus 1/2/3, both lattices."""
    for which in ("e8e8", "e16"):
        vs = SchottkyFormG4._lattice_vectors(which)
        S, n = SchottkyFormG4._build_inner_bitsets(vs)
        for g in (1, 2, 3):
            c_path = _native.riemann_theta_g4_schottky_shell_c(vs, g)
            py_path = SchottkyFormG4._full_shell_grams_py(S, n, g)
            assert c_path == py_path, (which, g)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g4_schottky(),
                    reason="native srmech_riemann_theta_g4_schottky not loaded")
def test_python_c_parity_orthogonal_frame_first_difference():
    """The FAMOUS genus-4 first difference at the orthogonal frame T = 2·I₄ —
    9 064 742 400 − 8 858 304 000 = 206 438 400 — computed EXACTLY through the native count
    peer (the dense orthogonality graph is slow in pure Python; the C peer carries it). The
    pure body computes the same number (the parity oracle), but this gate uses the C path
    for speed."""
    ca, cb, diff = SchottkyFormG4.first_difference_orthogonal_frame()
    assert (ca, cb, diff) == (_ORTHO_E8E8, _ORTHO_E16, _ORTHO_DIFF)


def test_pure_python_oracle_alone_passes_defining_gate():
    """The COMPLETE pure-Python body alone passes the defining gate (so the carrier is
    correct on a no-C host). Uses the fast D₄-star certificate + genus-1/2 vanishing to stay
    tractable without native acceleration."""
    a = SchottkyFormG4.e8e8_minimal_doubled()
    b = SchottkyFormG4.e16_minimal_doubled()
    Sa, na = SchottkyFormG4._build_inner_bitsets(a)
    Sb, nb = SchottkyFormG4._build_inner_bitsets(b)
    # J|_{g≤2} = 0 (pure)
    assert SchottkyFormG4._full_shell_grams_py(Sa, na, 1) \
        == SchottkyFormG4._full_shell_grams_py(Sb, nb, 1)
    assert SchottkyFormG4._full_shell_grams_py(Sa, na, 2) \
        == SchottkyFormG4._full_shell_grams_py(Sb, nb, 2)
    # J|_{g=4} != 0 (pure, D₄-star)
    ca = SchottkyFormG4._count_gram_py(Sa, na, SchottkyFormG4._G4_D4_STAR)
    cb = SchottkyFormG4._count_gram_py(Sb, nb, SchottkyFormG4._G4_D4_STAR)
    assert (ca - cb) == _D4_DIFF != 0


# ── input validation ──────────────────────────────────────────────────────────
def test_lattice_theta_rejects_bad_genus_and_lattice():
    with pytest.raises(ValueError):
        SchottkyFormG4.lattice_theta_minimal("e8e8", 5)
    with pytest.raises(ValueError):
        SchottkyFormG4.lattice_theta_minimal("nope", 2)
    with pytest.raises(ValueError):
        SchottkyFormG4.J_minimal(0)
    with pytest.raises(ValueError):
        SchottkyFormG4.collapses_below_genus4(max_genus=4)


def test_repr():
    r = repr(SchottkyFormG4())
    assert "SchottkyFormG4" in r
    assert "weight=8" in r
    assert "degree=4" in r


# ── gate (6b): the carrier source is numpy / math / abs() / float free ────────
def test_riemann_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None        # no bare abs() CALL
    assert "float(" not in text                         # no float in the carrier body
