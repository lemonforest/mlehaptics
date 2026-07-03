"""0.9.0rc109 — ``srmech.qm.quaternion``: the 4×4 left/right multiplication
operators + the hypercomplex ``exp(μθ)`` twiddle — the QDFT/ODFT foundation
(issue #1234 Item 1a, re-raise of #863 BX-5/6/7; F380 / the in-repo R21 proof).

The consistency gates this rc must hold (the transforms stand on them):

  (1) OCTONION RESTRICTION — ℍ is the dim-4 rung of the SAME Cayley-Dickson
      ladder as qm.octonion: the (4,4,4) table == the (8,8,8) table on
      {e0..e3}, and quaternion_left/right_mult(q) == the top-left 4×4 block
      of octonion_left/right_mult(q ⊕ 0₄) (with the off-blocks zero).
  (2) KLEIN-4 BRIDGE (the R21 proof re-run against this module) — the signed
      basis units close into Q₈ (order 8, non-abelian); the quotient
      Q₈/{±e0} is abelian and IS the hdc.klein4 XOR table (identity relabel;
      live-checked against hdc.klein4_bind); quaternion_left_mult's
      basis-column sign structure has its unique nonzero at row i⊕j.
  (3) L/R LAWS — L(p)R(q) = R(q)L(p) (the associativity witness);
      L(pq) = L(p)L(q); R(pq) = R(q)R(p) (the anti-homomorphism); L ≠ R for
      a generic q (ℍ non-commutative). Exact on integer quaternions.
  (4) TWIDDLE — ‖exp(μθ)‖ = 1; exp(μθ₁)·exp(μθ₂) = exp(μ(θ₁+θ₂)) same-axis;
      conj(exp(μθ)) = exp(−μθ); exp(μ·2π/N)^N = 1 (the DFT twiddle closure).
  (5) SERIES TIER — quaternion_exp_series_truncate == the exact Fraction
      Taylor oracle; the unit property converges; the float tier agrees.
  (6) PARITY — native vs forced-pure byte-exact per op (the C peers are pure
      speedups, never divergences).
  (7) REGISTRATION — 9 ToolEntries; tools.total == 367.

numpy-free by construction (no numpy import, no ``np.``); the oracle for the
series tier is stdlib ``fractions.Fraction``
(``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc import hdc
from srmech.amsc.mat import Mat
from srmech.qm import octonion as octo
from srmech.qm import quaternion as quat
from srmech.qm.quaternion import (
    quaternion_conjugate,
    quaternion_exp,
    quaternion_exp_series_truncate,
    quaternion_left_mult,
    quaternion_mult_table,
    quaternion_norm,
    quaternion_right_mult,
    quaternion_table_attestation,
    quaternion_twiddle,
)

H = (0, 1, 2, 3)

# Integer-valued quaternions: every product/sum below is exact in float64,
# so the algebraic-law checks are EXACT equality, not tolerance.
P_INT = [1.0, 2.0, -3.0, 4.0]
Q_INT = [-2.0, 1.0, 5.0, -1.0]

THETAS = [i * 0.1 for i in range(-50, 51)] + [1e-9, 0.123456789, 1000.0]
AXES = ("i", "j", "k", "ijk")


def _prod(i: int, j: int):
    """``e_i·e_j = (sign, index)`` from the shipped table (single signed unit)."""
    row = quaternion_mult_table()[i][j]
    ks = [k for k in range(4) if row[k] != 0]
    assert len(ks) == 1, f"e{i}*e{j} is not a single basis unit: {ks}"
    return row[ks[0]], ks[0]


def _qmul(a, b):
    """Quaternion product via the shipped left operator (a·b = L_a b)."""
    v = quaternion_left_mult(a) @ list(b)
    return [float(x) for x in v]


# ────────────────────────────────────────────────────────────────────
# (1) Octonion restriction — ℍ IS the top 4×4 of the same convention
# ────────────────────────────────────────────────────────────────────

def test_table_is_octonion_table_restricted():
    """The (4,4,4) ℍ tensor == the (8,8,8) 𝕆 tensor on {e0..e3}, and the
    octonion products of the first four basis elements never leave the span."""
    qt = quaternion_mult_table()
    ot = octo.octonion_mult_table()
    for i in H:
        for j in H:
            # Closure: e_i·e_j (i, j < 4) stays in span{e0..e3} in 𝕆.
            for k in range(4, 8):
                assert ot[i][j][k] == 0, f"H not closed in O at e{i}*e{j}: e{k}"
            for k in H:
                assert qt[i][j][k] == ot[i][j][k], (
                    f"table mismatch at C[{i}][{j}][{k}]: "
                    f"H={qt[i][j][k]} O={ot[i][j][k]}"
                )


@pytest.mark.parametrize("q4", [P_INT, Q_INT, [0.5, -1.25, 3.75, 0.125]])
def test_left_right_mult_are_octonion_top_left_blocks(q4):
    """quaternion_left/right_mult(q) == the top-left 4×4 block of the 8×8
    octonion operators on q ⊕ 0₄ — and the coupling blocks vanish (ℍ is an
    invariant subalgebra of its own left/right action)."""
    q8 = list(q4) + [0.0] * 4
    for qop, oop in ((quaternion_left_mult, octo.octonion_left_mult),
                     (quaternion_right_mult, octo.octonion_right_mult)):
        m4 = qop(q4).tolist()
        m8 = oop(q8).tolist()
        for r in range(4):
            for c in range(4):
                assert m4[r][c] == m8[r][c], (
                    f"{qop.__name__}[{r}][{c}] != octonion block: "
                    f"{m4[r][c]} vs {m8[r][c]}"
                )
                # Off-blocks: ℍ ⊄→ ℍ⊥ under a quaternion argument.
                assert m8[r][c + 4] == 0.0
                assert m8[r + 4][c] == 0.0


# ────────────────────────────────────────────────────────────────────
# (2) The Klein-4 bridge — Q₈/{±1} ≅ Z₂×Z₂ (F380 / R21)
# ────────────────────────────────────────────────────────────────────

def test_signed_units_close_into_q8():
    """The signed basis units {±e0, ±e1, ±e2, ±e3} close under · — Q₈, order 8."""
    signed_units = set()
    for i in H:
        for j in H:
            s, k = _prod(i, j)
            assert k in H
            signed_units.add((s, k))
    assert len(signed_units) == 8, f"Q8 has order 8; got {len(signed_units)}"


def test_q8_nonabelian_but_quotient_is_klein4_xor():
    """Q₈ is non-abelian (i·j ≠ j·i) yet Q₈/{±e0} is abelian AND its coset
    table is EXACTLY the Z₂×Z₂ XOR table hdc.klein4 uses (identity relabel —
    the F380 bridge the QDFT stands on)."""
    assert any(_prod(a, b) != _prod(b, a) for a in H for b in H), \
        "Q8 must be non-abelian"
    coset = [[_prod(a, b)[1] for b in H] for a in H]
    assert all(coset[a][b] == coset[b][a] for a in H for b in H), \
        "the quotient must be abelian"
    assert coset == [[a ^ b for b in H] for a in H], (
        f"Q8/{{±1}} coset table must be the Klein-4 XOR table; got {coset}"
    )


def test_quotient_matches_live_hdc_klein4_bind():
    """The live bridge: the coset (mod ±1) of e_a·e_b == hdc.klein4_bind's
    group op on the sector symbols a, b — the SAME Klein-4 the γ₅/iω₇
    chirality object uses (F380)."""
    for a in H:
        for b in H:
            _, k = _prod(a, b)
            bound = list(hdc.klein4_bind([a], [b]))
            assert bound == [k], (
                f"klein4_bind([{a}],[{b}]) = {bound} but Q8 coset gives {k}"
            )


def test_left_mult_sign_structure_is_klein4():
    """quaternion_left_mult(e_i): every column j has EXACTLY ONE nonzero, at
    row i⊕j, valued ±1 per the table — the operator-level Klein-4 bridge."""
    for i in H:
        e = [0.0] * 4
        e[i] = 1.0
        L = quaternion_left_mult(e).tolist()
        for j in H:
            col = [L[k][j] for k in H]
            nz = [k for k in H if col[k] != 0.0]
            assert nz == [i ^ j], (
                f"L_e{i} column {j}: nonzero rows {nz}, expected [{i ^ j}]"
            )
            s, k = _prod(i, j)
            assert col[i ^ j] == float(s) and k == i ^ j


# ────────────────────────────────────────────────────────────────────
# (3) L/R multiplication laws (exact on integer quaternions)
# ────────────────────────────────────────────────────────────────────

def test_left_right_commute_the_associativity_witness():
    """L(p)R(q) == R(q)L(p) — left and right multiplications commute (the
    associativity ℍ has and 𝕆 lacks)."""
    Lp = quaternion_left_mult(P_INT)
    Rq = quaternion_right_mult(Q_INT)
    assert (Lp @ Rq).tolist() == (Rq @ Lp).tolist()


def test_left_mult_is_a_homomorphism():
    """L(pq) == L(p)L(q) — exact (integer quaternions)."""
    pq = _qmul(P_INT, Q_INT)
    assert quaternion_left_mult(pq).tolist() == \
        (quaternion_left_mult(P_INT) @ quaternion_left_mult(Q_INT)).tolist()


def test_right_mult_is_an_anti_homomorphism():
    """R(pq) == R(q)R(p) — the order REVERSES (exact)."""
    pq = _qmul(P_INT, Q_INT)
    assert quaternion_right_mult(pq).tolist() == \
        (quaternion_right_mult(Q_INT) @ quaternion_right_mult(P_INT)).tolist()


def test_left_and_right_are_genuinely_distinct():
    """ℍ is non-commutative: L_q ≠ R_q for a generic q (they agree only on
    the centre ℝ·e0)."""
    assert quaternion_left_mult(Q_INT).tolist() != \
        quaternion_right_mult(Q_INT).tolist()
    # ... and DO agree on a real (central) quaternion.
    r = [2.5, 0.0, 0.0, 0.0]
    assert quaternion_left_mult(r).tolist() == quaternion_right_mult(r).tolist()


def test_basis_imaginary_operators_are_antisymmetric():
    """L_{e_i} / R_{e_i} (i ≥ 1) are antisymmetric (∈ so(4)) — the dim-4
    mirror of the octonion so(8) coset property."""
    for i in (1, 2, 3):
        e = [0.0] * 4
        e[i] = 1.0
        for op in (quaternion_left_mult, quaternion_right_mult):
            m = op(e).tolist()
            for r in range(4):
                for c in range(4):
                    assert m[r][c] == -m[c][r]


def test_conjugate_and_norm():
    """conj flips the imaginary axes; N(x) = ‖x‖ via the Class-K∘N cascade
    (‖(3,4,0,0)‖ = 5; ‖x·y‖ = ‖x‖·‖y‖ — the composition-algebra law)."""
    assert quaternion_conjugate([1.0, 2.0, -3.0, 4.0]) == [1.0, -2.0, 3.0, -4.0]
    assert abs(quaternion_norm([3.0, 4.0, 0.0, 0.0]) - 5.0) <= 1e-12
    nx = quaternion_norm(P_INT)
    ny = quaternion_norm(Q_INT)
    nxy = quaternion_norm(_qmul(P_INT, Q_INT))
    assert abs(nxy - nx * ny) <= 1e-9 * nx * ny


# ────────────────────────────────────────────────────────────────────
# (4) The twiddle — exp(μθ) properties + the DFT closure
# ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("axis", AXES)
def test_exp_is_unit(axis):
    for theta in (0.0, 0.4, 1.1, 3.9, -2.5):
        w = quaternion_exp(theta, axis)
        assert len(w) == 4
        assert abs(quaternion_norm(w) - 1.0) <= 1e-9


def test_exp_zero_is_identity():
    for axis in AXES:
        assert quaternion_exp(0.0, axis) == [1.0, 0.0, 0.0, 0.0]


@pytest.mark.parametrize("axis", AXES)
def test_exp_same_axis_addition_law(axis):
    """exp(μθ₁)·exp(μθ₂) == exp(μ(θ₁+θ₂)) — the twiddle lives in the
    commutative ℝ[μ̂] ≅ ℂ (why the one-sided QDFT inverts)."""
    t1, t2 = 0.7, -0.3
    lhs = _qmul(quaternion_exp(t1, axis), quaternion_exp(t2, axis))
    rhs = quaternion_exp(t1 + t2, axis)
    assert all(abs(lhs[i] - rhs[i]) <= 1e-12 for i in range(4))


@pytest.mark.parametrize("axis", AXES)
def test_exp_conjugate_is_inverse(axis):
    """conj(exp(μθ)) == exp(−μθ), and their product is 1 (the inverse-QDFT
    twiddle)."""
    theta = 0.9
    w = quaternion_exp(theta, axis)
    wc = quaternion_conjugate(w)
    wm = quaternion_exp(-theta, axis)
    assert all(abs(wc[i] - wm[i]) <= 1e-15 for i in range(4))
    ident = _qmul(w, wc)
    expect = [1.0, 0.0, 0.0, 0.0]
    assert all(abs(ident[i] - expect[i]) <= 1e-12 for i in range(4))


@pytest.mark.parametrize("n_points", [1, 2, 3, 4, 6, 8, 12, 16])
def test_twiddle_nth_roots_of_unity_closure(n_points):
    """exp(μ·2π/N)^N == 1 for BOTH σ orientations — the twiddle closure the
    DFT's orthogonality needs."""
    for sigma in (-1, 1):
        w = quaternion_twiddle(1, 1, n_points, sigma=sigma)
        acc = [1.0, 0.0, 0.0, 0.0]
        for _ in range(n_points):
            acc = _qmul(w, acc)
        assert abs(acc[0] - 1.0) <= 1e-9 * n_points
        assert all(abs(acc[i]) <= 1e-9 * n_points for i in (1, 2, 3))


def test_twiddle_zero_index_is_exact_identity():
    """jk ≡ 0 (mod N) → the EXACT identity (θ = ±0.0; no truncation residue)."""
    for (j, k, n) in ((0, 5, 7), (5, 0, 7), (7, 3, 7), (6, 14, 12)):
        assert quaternion_twiddle(j, k, n) == [1.0, 0.0, 0.0, 0.0]


def test_twiddle_reduces_indices_cyclically():
    """The Class-I reduction: twiddle(j, k, N) == twiddle(j mod N, k mod N, N)
    (exact — the SAME reduced angle feeds the same cascade)."""
    assert quaternion_twiddle(7, 5, 6) == quaternion_twiddle(1, 5, 6)
    assert quaternion_twiddle(19, 23, 12) == quaternion_twiddle(7, 11, 12)


def test_twiddle_sigma_orientations_are_conjugate():
    w_f = quaternion_twiddle(2, 3, 16, sigma=-1)
    w_i = quaternion_twiddle(2, 3, 16, sigma=1)
    assert quaternion_conjugate(w_f) == w_i


def test_exp_axis_placement_and_general_axis():
    """Named axes place sin θ on the right slot; a general pure-imaginary
    vector is normalised via the Class-N sqrt cascade."""
    theta = 0.6
    wi = quaternion_exp(theta, "i")
    wj = quaternion_exp(theta, "j")
    wk = quaternion_exp(theta, "k")
    assert wi[2] == wi[3] == 0.0 and wi[1] != 0.0
    assert wj[1] == wj[3] == 0.0 and wj[2] != 0.0
    assert wk[1] == wk[2] == 0.0 and wk[3] != 0.0
    assert wi[0] == wj[0] == wk[0]                    # same cos θ
    # 3-4-5 axis: μ̂ = (0, 0.6, 0.8, 0) exactly.
    wg = quaternion_exp(theta, [0.0, 3.0, 4.0, 0.0])
    assert abs(wg[1] / wg[2] - 0.75) <= 1e-15 and wg[3] == 0.0
    assert abs(quaternion_norm(wg) - 1.0) <= 1e-12


def test_exp_and_twiddle_contract_errors():
    with pytest.raises(ValueError):
        quaternion_exp(float("nan"), "i")
    with pytest.raises(ValueError):
        quaternion_exp(float("inf"), "i")
    with pytest.raises(ValueError):
        quaternion_exp(0.5, "bogus")
    with pytest.raises(ValueError):
        quaternion_exp(0.5, [1.0, 1.0, 0.0, 0.0])     # e0 != 0
    with pytest.raises(ValueError):
        quaternion_exp(0.5, [0.0, 0.0, 0.0, 0.0])     # zero axis
    with pytest.raises(ValueError):
        quaternion_twiddle(-1, 0, 4)
    with pytest.raises(ValueError):
        quaternion_twiddle(0, 0, 0)
    with pytest.raises(ValueError):
        quaternion_twiddle(0, 0, 2 ** 32)             # the uint32 parity bound
    with pytest.raises(ValueError):
        quaternion_twiddle(1, 1, 4, sigma=2)
    for op in (quaternion_left_mult, quaternion_right_mult,
               quaternion_conjugate, quaternion_norm):
        with pytest.raises(ValueError):
            op([1.0, 2.0, 3.0])                       # not a 4-vector
        with pytest.raises(ValueError):
            op(Mat.from_rows([[1.0, 0.0], [0.0, 1.0]]))


# ────────────────────────────────────────────────────────────────────
# (5) The exact series tier
# ────────────────────────────────────────────────────────────────────

def _oracle_cos(p: int, q: int, n_terms: int) -> Fraction:
    x = Fraction(p, q)
    acc = Fraction(0)
    fact = 1
    for k in range(n_terms + 1):
        e = 2 * k
        for m in range(e - 1, e + 1):
            if m >= 1:
                fact *= m
        acc += (-1) ** k * x ** e / fact
    return acc


def _oracle_sin(p: int, q: int, n_terms: int) -> Fraction:
    x = Fraction(p, q)
    acc = Fraction(0)
    fact = 1
    for k in range(n_terms + 1):
        e = 2 * k + 1
        for m in range(e - 1, e + 1):
            if m >= 1:
                fact *= m
        acc += (-1) ** k * x ** e / fact
    return acc


@pytest.mark.parametrize("axis", [1, 2, 3])
def test_series_truncate_matches_fraction_oracle(axis):
    """The exact tier == the Fraction Taylor oracle, slot-for-slot."""
    p, q, n = 1, 3, 8
    pairs = quaternion_exp_series_truncate(p, q, n, axis=axis)
    assert len(pairs) == 4
    assert Fraction(*pairs[0]) == _oracle_cos(p, q, n)
    assert Fraction(*pairs[axis]) == _oracle_sin(p, q, n)
    for slot in set((1, 2, 3)) - {axis}:
        assert Fraction(*pairs[slot]) == 0


def test_series_truncate_unit_property_converges():
    """cos² + sin² → 1 as num_terms grows (the truncation residue is the
    caller's precision dial — the exactness convention's exact form)."""
    p, q = 1, 2
    resid_short = Fraction(1) - (
        Fraction(*quaternion_exp_series_truncate(p, q, 2)[0]) ** 2
        + Fraction(*quaternion_exp_series_truncate(p, q, 2)[1]) ** 2)
    resid_long = Fraction(1) - (
        Fraction(*quaternion_exp_series_truncate(p, q, 12)[0]) ** 2
        + Fraction(*quaternion_exp_series_truncate(p, q, 12)[1]) ** 2)
    assert abs(resid_long) < abs(resid_short)
    assert abs(resid_long) < Fraction(1, 10 ** 15)


def test_series_tier_agrees_with_float_tier():
    """The exact series projected to float == quaternion_exp within Q61 +
    truncation residue (the two tiers of ONE convention)."""
    p, q, n = 1, 2, 20
    pairs = quaternion_exp_series_truncate(p, q, n, axis=1)
    w = quaternion_exp(0.5, "i")
    assert abs(pairs[0][0] / pairs[0][1] - w[0]) <= 1e-12
    assert abs(pairs[1][0] / pairs[1][1] - w[1]) <= 1e-12


def test_series_truncate_axis_validation():
    for bad in (0, 4, -1, "i"):
        with pytest.raises(ValueError):
            quaternion_exp_series_truncate(1, 3, 5, axis=bad)


# ────────────────────────────────────────────────────────────────────
# (6) Python == C parity (byte-exact; native is a pure speedup)
# ────────────────────────────────────────────────────────────────────

def test_native_symbols_present_on_native_build():
    """On a native build the four rc109 symbols exist (never pure-only by
    accident). Skipped only when the whole lib is absent (pure wheel)."""
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        pytest.skip("pure-Python environment (no native lib)")
    for sym in ("srmech_quaternion_left_mult", "srmech_quaternion_right_mult",
                "srmech_quaternion_exp", "srmech_quaternion_twiddle"):
        assert hasattr(_native.LIB, sym), f"native lib lacks {sym}"


@pytest.mark.parametrize("op", [quaternion_left_mult, quaternion_right_mult])
def test_mult_native_matches_pure_byte_for_byte(op, monkeypatch):
    """Whichever path is active, force the pure table path and assert
    IDENTICAL 4×4 entries (the rc10 hypercomplex_exp parity pattern)."""
    samples = [P_INT, Q_INT, [0.5, -1.25, 3.75, 0.125],
               [0.0, 1.0, 0.0, 0.0], [-7.5, 0.25, 1e-9, 3.0]]
    active = [op(s).tolist() for s in samples]
    monkeypatch.setattr(quat, "_native_ready", lambda s: False)
    pure = [op(s).tolist() for s in samples]
    assert active == pure


def test_exp_native_matches_pure_byte_for_byte(monkeypatch):
    grids = [(t, ax) for t in THETAS for ax in AXES]
    active = {g: quaternion_exp(g[0], g[1]) for g in grids}
    monkeypatch.setattr(quat, "_native_ready", lambda s: False)
    pure = {g: quaternion_exp(g[0], g[1]) for g in grids}
    for g in grids:
        assert active[g] == pure[g], f"quaternion_exp{g} diverged"


def test_twiddle_native_matches_pure_byte_for_byte(monkeypatch):
    grids = [(j, k, n, s) for n in (1, 2, 5, 12, 100, 4096)
             for (j, k) in ((0, 0), (1, 1), (2, 3), (7, 11), (999, 998))
             for s in (-1, 1)]
    active = {g: quaternion_twiddle(g[0], g[1], g[2], sigma=g[3]) for g in grids}
    monkeypatch.setattr(quat, "_native_ready", lambda s: False)
    pure = {g: quaternion_twiddle(g[0], g[1], g[2], sigma=g[3]) for g in grids}
    for g in grids:
        assert active[g] == pure[g], f"quaternion_twiddle{g} diverged"


# ────────────────────────────────────────────────────────────────────
# (7) Registration + attestation + carrier hygiene
# ────────────────────────────────────────────────────────────────────

def test_tools_total_is_367():
    """rc109 added the 9 qm.quaternion ToolEntries (350 → 359); the live
    pin tracks later rcs (rc111: +3 qm.octonion twiddle-family → 362)."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 367


def test_quaternion_tool_entries_registered():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    for op in ("quaternion_mult_table", "quaternion_table_attestation",
               "quaternion_left_mult", "quaternion_right_mult",
               "quaternion_conjugate", "quaternion_norm", "quaternion_exp",
               "quaternion_exp_series_truncate", "quaternion_twiddle"):
        assert f"srmech.qm.quaternion.{op}" in names, f"missing ToolEntry: {op}"


def test_attestation_is_deterministic_and_content_addressed():
    a1 = quaternion_table_attestation()
    a2 = quaternion_table_attestation()
    assert a1 == a2, "a generated-constant attestation must be reproducible"
    sha = a1["attestation"]["response_sha256"]
    assert isinstance(sha, str) and len(sha) == 64
    int(sha, 16)  # 64 hex chars
    assert a1["data"]["convention"] == "cayley_dickson_from_C"
    assert a1["data"]["oriented_triples"] == [[1, 2, 3]]
    assert a1["mpr_version"] == "1.0"


def test_mult_table_returns_independent_copies():
    t1 = quaternion_mult_table()
    t1[1][2][3] = 99
    assert quaternion_mult_table()[1][2][3] != 99


def test_left_mult_returns_real_mat_carrier():
    m = quaternion_left_mult(P_INT)
    assert isinstance(m, Mat)
    assert m.shape == (4, 4)
    assert not m.is_complex
