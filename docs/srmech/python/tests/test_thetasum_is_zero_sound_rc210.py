"""rc210 — the ``ThetaSum.is_zero`` SOUNDNESS rebuild regression guards.

STOP-THE-LINE context: the pre-rc210 ``is_zero`` "structural interpolation completion"
certified provably-NONZERO objects as zero through two unsound devices —

  D1  the single-variable p-order BAND ``k = max-term(Σe²)−1+3`` (the old
      ``_struct_one_var``) under-counts MULTI-TERM cancellation gaps: a T-term
      one-character family can cancel through p^B for B far above the band
      (Witness A below: 6 terms, first nonzero coefficient at p⁶ > band 4);
  D2  the mixed-character node count ``d = max-term Σe²`` (the old
      ``_structural_is_zero``) has no supporting theorem — a sum of terms of
      DIFFERENT quasi-periodicity lies in no single theta-section space, so
      "degree-d section ⇒ d+1 nodes" does not apply to it (Witness B below:
      11 single-theta terms of pairwise-distinct character, first nonzero
      coefficient at p¹⁵ > the pretended band 11);
  D3  ``_struct_variables`` scanned theta args only, silently dropping
      prefactor-only symbols (``a·θ(2x) − b·θ(2x)`` was certified zero);
  D4  augment primes were not deduplicated against zero-node constants
      (a duplicate node under-counts the interpolation).

rc210 replaced the True side WHOLESALE with the sound certificate recursion
(``srmech.apokatastasis.thetasum._decide_struct``): True ⟺ Z1 exact cancellation / Z2
Weierstrass ±-pair reduction to the empty normal form / Z3s all character
components proven zero / Z4 per-character interpolation at D+1 distinct nodes.
There is NO numeric band anywhere on the True side; False = "not proven".

Every NONZERO witness here carries an INDEPENDENT exact proof (a pinned lowest
lattice coefficient computed by stdlib-``Fraction``-free exact ``Q`` expansion, or
an exact-``ℚ`` ``eval_trunc`` stabilisation at a rational point) so the guard does
not route through the machinery under test. The kernel GENERATORS for the gap
families are committed below (computational-provenance discipline).
"""
from fractions import Fraction

from srmech.amsc import ThetaSum
from srmech.apokatastasis.ellbase import EllMonomial as M, Theta
from srmech.math.q import Q
from srmech.apokatastasis.thetasum import (
    _NONZERO, _UNKNOWN, _ZERO, _Q_ZERO,
    _decide_thetasum, _struct_pexp_mul, _struct_theta_p, _term_char_v,
)

_X = M.symbol("x")
_Y = M.symbol("y")


# ── the committed witnesses ──────────────────────────────────────────────────────

# Witness A (defect D1): the 6-term ONE-character ±-pair family Σ c_u·θ(u·x^±)
# whose exact kernel cancels the lattice through p⁵ — the first nonzero coefficient
# sits at p⁶, strictly above the old band k = Σe²−1+3 = 4. Shipped rc209 is_zero: True
# (a false theorem). The coefficients were produced by the committed rank-1 kernel
# generator below (B=5-band nullspace over the u ∈ {2..7} pair family).
_A_US = (2, 3, 4, 5, 6, 7)
_A_CS = (Q(-133824, 26411), Q(388557, 26411), Q(-231961600, 11541607),
         Q(19987500, 1322951), Q(-15163200, 2516591), Q(1, 1))


def _witness_a():
    return ThetaSum(terms=tuple(
        (c, M.one(), (Theta(M.scalar(Q(u, 1)) * _X), Theta(M.scalar(Q(u, 1)) * _X.inv())))
        for c, u in zip(_A_CS, _A_US)))


# Witness B (defect D2): Σ_t c_t·θ(t·x³) over t = 2..12 with the divided-difference
# kernel c_t = t⁴/∏_{s≠t}(t−s) — 11 terms of PAIRWISE-DISTINCT character (the μ_x
# multiplier carries t⁻³), so the sum lies in no single section space and the old
# mixed-character node count had no theorem. First nonzero coefficient at
# (p¹⁵, x⁻¹⁵) = −1/12!. Shipped rc209 is_zero: True (a false theorem).
_B_TS = tuple(range(2, 13))


def _witness_b_coeff(t):
    v = Q(t, 1) ** 4
    for s in _B_TS:
        if s != t:
            v = v / Q(t - s, 1)
    return v


def _witness_b():
    return ThetaSum(terms=tuple(
        (_witness_b_coeff(t), M.one(), (Theta(M.scalar(Q(t, 1)) * _X * _X * _X),))
        for t in _B_TS))


# Witness D3: a·θ(2x) − b·θ(2x), a ≠ b — nonzero (= (a−b)·θ(2x)), yet the shipped
# variable scan dropped the prefactor-only symbols a, b and certified it zero.
def _witness_d3():
    return ThetaSum(terms=(
        (Q(1, 1), M.symbol("a"), (Theta(M.scalar(2) * _X),)),
        (Q(-1, 1), M.symbol("b"), (Theta(M.scalar(2) * _X),)),
    ))


def _lowest_lattice_coeff(e_and_coeffs, K):
    """The lowest (p_pow, x_exp, coeff) of the exact-``Q`` p-expansion of
    Σ c·∏θ(coeff·x^e) — an INDEPENDENT nonzero witness that does not route through
    ``is_zero`` (the same primitive the #693 guard uses)."""
    total = {}
    for c, factors in e_and_coeffs:
        term = {0: {0: c}}
        for coeff, e in factors:
            term = _struct_pexp_mul(term, _struct_theta_p(coeff, e, K), K)
        for pp, lp in term.items():
            dst = total.setdefault(pp, {})
            for kk, vv in lp.items():
                dst[kk] = dst.get(kk, _Q_ZERO) + vv
    for pp in sorted(total):
        for xe in sorted(total[pp]):
            if total[pp][xe] != _Q_ZERO:
                return pp, xe, total[pp][xe]
    return None


# ── Witness A: proven nonzero, must never be certified zero again ────────────────

def test_witness_a_is_exactly_nonzero_independent():
    lo = _lowest_lattice_coeff(
        [(c, ((Q(u, 1), 1), (Q(u, 1), -1))) for c, u in zip(_A_CS, _A_US)],
        K=10)
    assert lo == (6, 0, Q(1630980, 2401))
    # the gap: p-order 6 strictly above the old (unsound) band max(Σe²−1,0)+3 = 4
    assert lo[0] > (2 - 1) + 3


def test_witness_a_is_zero_false():
    a = _witness_a()
    assert a.is_zero is False                       # the dispatched decision
    assert a._is_zero_py() is False                 # the pure oracle
    assert _decide_thetasum(a) == _NONZERO          # proven nonzero, not a decline


def test_witness_a_eval_trunc_stabilises_nonzero():
    a = _witness_a()
    v16 = a.eval_trunc({"p": Q(1, 9), "x": Q(2, 3)}, 16)
    v20 = a.eval_trunc({"p": Q(1, 9), "x": Q(2, 3)}, 20)
    f16 = Fraction(v16.numerator, v16.denominator)
    f20 = Fraction(v20.numerator, v20.denominator)
    assert f20 != 0
    # stabilised: successive depths agree to ~1e-12 relative, far from shrinking to 0
    assert abs(f16 - f20) < abs(f20) * Fraction(1, 10**9)
    assert abs(f20) > Fraction(1, 10**3)            # ≈ 2.02e-3 at (p,x)=(1/9,2/3)


# ── Witness B: proven nonzero, must never be certified zero again ────────────────

def test_witness_b_is_exactly_nonzero_independent():
    lo = _lowest_lattice_coeff(
        [(_witness_b_coeff(t), ((Q(t, 1), 3),)) for t in _B_TS],
        K=18)
    assert lo == (15, -15, Q(-1, 479001600))        # −1/12! at (p¹⁵, x⁻¹⁵)
    # the gap: p-order 15 strictly above the old pretended band Σe²−1+3 = 11
    assert lo[0] > (9 - 1) + 3


def test_witness_b_characters_are_pairwise_distinct():
    """The 11 terms have pairwise-distinct x-characters (μ_x carries t⁻³), so the
    old mixed-character interpolation had no section-space theorem to stand on —
    and the new character split resolves each term as a singleton (N1)."""
    b = _witness_b()
    chars = {_term_char_v(pref, [t.arg for t in thetas], "x")
             for pref, thetas in b.terms}
    assert len(chars) == len(b.terms) == 11


def test_witness_b_is_zero_false():
    b = _witness_b()
    assert b.is_zero is False
    assert b._is_zero_py() is False
    assert _decide_thetasum(b) == _NONZERO


# ── Witness D3: prefactor-only symbols must not be dropped ────────────────────────

def test_witness_d3_is_zero_false():
    d3 = _witness_d3()
    assert d3.is_zero is False
    assert d3._is_zero_py() is False
    assert _decide_thetasum(d3) == _NONZERO


def test_witness_d3_eval_trunc_nonzero():
    d3 = _witness_d3()
    v = d3.eval_trunc({"p": Q(1, 9), "x": Q(2, 3), "a": Q(3, 5), "b": Q(4, 7)}, 16)
    assert Fraction(v.numerator, v.denominator) != 0


# ── the committed kernel GENERATORS (computational provenance) ───────────────────
#
# The rank-1 generator reproduces Witness A's family from scratch: exact-Fraction
# theta series (an INDEPENDENT oracle — deliberately not srmech's Q), a nullspace
# over the lattice coefficients with p-order ≤ B, and the safety property that any
# kernel object it emits is (a) exactly nonzero above the band and (b) NEVER
# certified zero by the rebuilt decision. The rank-2 generator searches the
# 3-theta family θ(a·x)θ(b·x)θ(c·x⁻²) with a·b constant (exponent-kernel rank 2);
# the committed pair family currently yields NO kernel — the search is pinned so a
# future family enlargement keeps the safety property.

def _ser_mul(a, b, J):
    out = {}
    for (n1, j1), v1 in a.items():
        for (n2, j2), v2 in b.items():
            j = j1 + j2
            if j > J:
                continue
            k = (n1 + n2, j)
            out[k] = out.get(k, Fraction(0)) + v1 * v2
    return {k: v for k, v in out.items() if v != 0}


def _theta_series(c, e, J):
    acc = {(0, 0): Fraction(1)}
    ci = Fraction(1) / c
    for j in range(0, J + 1):
        acc = _ser_mul(acc, {(0, 0): Fraction(1), (e, j): -c}, J)
        if j + 1 <= J:
            acc = _ser_mul(acc, {(0, 0): Fraction(1), (-e, j + 1): -ci}, J)
    return acc


def _nullspace(rows, ncols):
    m = [list(r) for r in rows]
    piv = {}
    r = 0
    for c in range(ncols):
        pr = next((i for i in range(r, len(m)) if m[i][c] != 0), None)
        if pr is None:
            continue
        m[r], m[pr] = m[pr], m[r]
        pv = m[r][c]
        m[r] = [v / pv for v in m[r]]
        for i in range(len(m)):
            if i != r and m[i][c] != 0:
                f = m[i][c]
                m[i] = [a2 - f * b2 for a2, b2 in zip(m[i], m[r])]
        piv[c] = r
        r += 1
        if r == len(m):
            break
    basis = []
    for fc in [c for c in range(ncols) if c not in piv]:
        v = [Fraction(0)] * ncols
        v[fc] = Fraction(1)
        for c, pr in piv.items():
            v[c] = -m[pr][fc]
        basis.append(v)
    return basis


def _gap_kernel(series_list, B, J):
    """A kernel vector killing every lattice coefficient of p-order ≤ B, or None;
    asserts (exactly) that the combination is NONZERO with valuation > B."""
    keys = sorted({k for t in series_list for k in t if k[1] <= B})
    rows = [[t.get(k, Fraction(0)) for t in series_list] for k in keys]
    basis = _nullspace(rows, len(series_list))
    if not basis:
        return None
    cvec = basis[0]
    comb = {}
    for ci, t in zip(cvec, series_list):
        if ci == 0:
            continue
        for k, v in t.items():
            comb[k] = comb.get(k, Fraction(0)) + ci * v
    comb = {k: v for k, v in comb.items() if v != 0}
    if not comb:
        return None                       # an accidental true identity — reject
    val = min(j for (_n, j) in comb)
    assert val > B
    return cvec, val


def test_rank1_kernel_generator_reproduces_witness_a_family():
    B, J = 4, 14
    us = list(range(2, 20))
    got = None
    for T in range(B + 2, len(us) + 1):
        ser = [_ser_mul(_theta_series(Fraction(u), 1, J),
                        _theta_series(Fraction(u), -1, J), J) for u in us[:T]]
        g = _gap_kernel(ser, B, J)
        if g:
            got = (us[:T], g)
            break
    assert got is not None, "the rank-1 gap family must exist (it produced Witness A)"
    uu, (cv, val) = got
    assert val > B                        # exactly nonzero strictly above the band
    terms = [(Q(c.numerator, c.denominator), M.one(),
              (Theta(M.scalar(Q(u, 1)) * _X), Theta(M.scalar(Q(u, 1)) * _X.inv())))
             for c, u in zip(cv, uu) if c != 0]
    obj = ThetaSum(terms=terms)
    # THE safety property: a generated gap object is NEVER certified zero.
    assert obj.is_zero is False
    assert _decide_thetasum(obj) in (_NONZERO, _UNKNOWN)


def test_rank2_kernel_generator_never_yields_a_false_zero():
    pairs = [(Fraction(k), Fraction(12) / k) for k in
             [Fraction(v) for v in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15,
                                    16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
                                    28, 29, 30, 31)]
             + [Fraction(1, 2), Fraction(1, 3), Fraction(2, 3), Fraction(3, 2),
                Fraction(5, 2), Fraction(5, 3), Fraction(7, 2), Fraction(7, 3),
                Fraction(4, 3), Fraction(3, 4), Fraction(5, 4), Fraction(7, 4),
                Fraction(9, 2), Fraction(9, 4), Fraction(11, 2), Fraction(11, 3)]]
    cc = Fraction(5)
    B, J = 4, 12
    got = None
    for T in range(20, len(pairs) + 1, 2):
        ser = []
        for (aa, bb) in pairs[:T]:
            s = _ser_mul(_theta_series(aa, 1, J), _theta_series(bb, 1, J), J)
            s = _ser_mul(s, _theta_series(cc, -2, J), J)
            ser.append(s)
        g = _gap_kernel(ser, B, J)
        if g:
            got = (pairs[:T], g)
            break
    if got is None:
        # The committed family has no rank-2 kernel (the dive's result, pinned).
        # Enlarging the family is legitimate future work; the safety property below
        # is what must hold for ANY kernel a future family produces.
        return
    pp, (cv, val) = got
    assert val > B
    terms = [(Q(c.numerator, c.denominator), M.one(),
              (Theta(M.scalar(Q(aa.numerator, aa.denominator)) * _X),
               Theta(M.scalar(Q(bb.numerator, bb.denominator)) * _X),
               Theta(M.scalar(Q(5, 1)) * _X.inv() * _X.inv())))
             for c, (aa, bb) in zip(cv, pp) if c != 0]
    obj = ThetaSum(terms=terms)
    assert obj.is_zero is False           # NEVER a false zero on a gap object
    assert _decide_thetasum(obj) in (_NONZERO, _UNKNOWN)


# ── the zero side: genuine identities must STAY proven ───────────────────────────

def _abc():
    return M.symbol("a"), M.symbol("b"), M.symbol("c")


def test_three_term_stays_proven_zero_both_paths():
    a, b, c = _abc()
    w = ThetaSum.three_term(a, b, c)
    assert w.is_zero is True
    assert _decide_thetasum(w, use_fastpath=True) == _ZERO
    assert _decide_thetasum(w, use_fastpath=False) == _ZERO     # certificate recursion alone


def test_three_term_times_common_theta_proven_zero():
    """5-theta terms: the ±-pair recovery breaks (odd count), the Z4 interpolation
    must carry the proof."""
    a, b, c = _abc()
    g = M.symbol("g")
    w = ThetaSum.three_term(a, b, c) * ThetaSum(
        terms=((Q(1, 1), M.one(), (Theta(g * _X),)),))
    assert w.is_zero is True
    assert _decide_thetasum(w, use_fastpath=False) == _ZERO


def test_three_term_shifted_proven_zero():
    a, b, c = _abc()
    w = ThetaSum.three_term(a, b, c).shift_x()          # q enters the arguments
    assert w.is_zero is True
    assert _decide_thetasum(w, use_fastpath=False) == _ZERO


def test_three_term_monomial_prefactor_proven_zero():
    a, b, c = _abc()
    w = ThetaSum.three_term(a, b, c) * (a * a / b * _X * _X * _X)
    assert w.is_zero is True
    assert _decide_thetasum(w, use_fastpath=False) == _ZERO


def test_disjoint_three_term_sum_proven_zero():
    a, b, c = _abc()
    d, e, f = M.symbol("d"), M.symbol("e"), M.symbol("f")
    w = ThetaSum.three_term(a, b, c) + ThetaSum.three_term(d, e, f)
    assert w.is_zero is True
    assert _decide_thetasum(w, use_fastpath=False) == _ZERO


def test_three_term_concrete_constants_x_symbolic_proven_zero():
    w = ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(3, 1)), M.scalar(Q(5, 1)))
    assert w.is_zero is True
    assert _decide_thetasum(w, use_fastpath=False) == _ZERO


def test_perturbed_three_term_not_zero():
    a, b, c = _abc()
    w = ThetaSum.three_term(a, b, c) + ThetaSum(
        terms=((Q(1, 7), M.one(),
                (Theta(a * _X), Theta(a / _X), Theta(b * c), Theta(b / c))),))
    assert w.is_zero is False
    assert _decide_thetasum(w, use_fastpath=False) == _NONZERO


# ── the DOCUMENTED honest declines (decline parity with the shipped decision) ────

def test_all_constant_three_term_z5_certified_rc228():
    """The all-rational-constants Weierstrass identity is a TRUE zero — a 0-variable
    sum of theta-constants with NO interpolation variable, the leaf shape the
    pre-rc228 certificate vocabulary could not prove (Z1 needs carrier cancellation,
    Z2/Z4 a live variable, N-detect only NONZERO), so it was an honest decline.
    rc228's Z5 PRIME-LIFT certificate closes it: lifting a constant prime (here the
    ``c = 5`` or ``x = 7`` value) back to an elliptic variable recovers a
    Weierstrass ±-pair object the exact three-term reduction proves ``≡ 0``, and
    that specializes back to the constant leaf ``≡ 0`` (Rosengren Eq. 1.12). SOUND —
    ``three_term(a,b,c)`` IS identically zero, so a ZERO verdict is a theorem, not a
    band. This is the feasible-leaf proof that Z5 FIRES."""
    w = ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(3, 1)), M.scalar(Q(5, 1)),
                            x=M.scalar(Q(7, 1)))
    assert _decide_thetasum(w, use_fastpath=False) == _ZERO
    assert w.is_zero is True


def test_all_constant_native_interp_no_stale_exps_rc254():
    """Regression for the n_syms==0 native interpolation flake (the intermittent
    macOS ``is_zero`` divergence), STRENGTHENED at rc255. For an ALL-CONSTANT leaf
    the native peer must DETERMINISTICALLY prove it (``True``) via the Z5/Z6 constant-
    leaf certificates — and NEVER return a wrong ``False`` or a flaky verdict. Root
    cause of the flake: C ``ti_parse`` strided ``exps_flat`` by the CLAMPED
    ``c->n_syms == 1`` while the marshalled rows carried the REAL ``n_syms == 0``
    columns, memcpy'ing PAST the end of the 1-element ``exps_flat`` -> a garbage
    exponent -> ``present[0]`` picked up a phantom variable -> a false OVERFLOW
    decline (Linux, harmless) OR an occasional wrong verdict (macOS, the flake).
    rc254 fix: harden ``ti_parse`` (stride by the real ``in_n_syms``, zero the
    clamped row). rc255: the entry now reserves synthetic lift + p slots and runs
    Z5 then Z6 on the constant leaf, so a single Weierstrass seam is PROVEN True
    (was a decline). Loop to catch the (pre-fix) intermittency; the native gate
    keeps it a no-op assert on a pure build."""
    from srmech.amsc import _native as _nat
    native = _nat.has_native_thetasum_interpolation()
    for _ in range(50):
        w = ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(3, 1)),
                                M.scalar(Q(5, 1)), x=M.scalar(Q(7, 1)))
        if native:
            # rc255: the single-seam Weierstrass constant leaf is PROVEN zero by the
            # native Z5 prime-lift (deterministic True; a wrong False would fail here,
            # the flake regression; pre-rc255 it declined to None).
            assert w._is_zero_interpolation_c(parallel=False) is True
        assert w.is_zero is True


def test_large_coeff_constant_leaf_decided_rc256():
    """rc256: the native peer factors the bigint COEFF CARRIER directly (via
    ``srmech_bigint_divmod_small``) instead of downcasting to int64, so a constant leaf
    whose coefficient exceeds int64 is DECIDED — not declined to the pure oracle. A
    Weierstrass seam scaled by ``2**70`` is still identically zero, but every coefficient
    blows past int64 (the old ``ti_bi_to_i64`` magnitude decline); native must PROVE it
    ``True`` now. Also a ``3**41`` scale (a large odd-prime-power coefficient the int64
    path could not factor). This is the completeness win — verdicts are unchanged (the
    scaled identity was always zero), the native peer just no longer defers it."""
    from srmech.amsc import _native as _nat
    A = ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(5, 1)), M.scalar(Q(7, 1)),
                            x=M.scalar(Q(3, 1)))
    for factor in (Q(2 ** 70, 1), Q(3 ** 41, 1), Q(2 ** 64, 1)):
        big = A._scaled(factor)                       # factor * A, still identically zero
        assert big.is_zero is True
        assert big._is_zero_py() is True
        if _nat.has_native_thetasum_interpolation():
            # DECIDED (True), not declined (None): the int64-magnitude decline is gone.
            assert big._is_zero_interpolation_c(parallel=False) is True


def test_constant_core_times_theta_honest_decline():
    """A true identity whose proof needs the 0-variable theta-constant case → the
    recursion reaches the same honest decline (and the y-part alone cannot prove
    it). Pinned as UNKNOWN / False — decline parity, not a regression: the shipped
    rc209 decision FALSELY certified this object zero (the D1 band); rc210's honest
    False is the fix, not a capability loss."""
    d = M.symbol("d")
    core = ThetaSum.three_term(M.scalar(Q(2, 1)), M.scalar(Q(3, 1)), M.scalar(Q(5, 1)),
                               x=M.scalar(Q(7, 1)))
    w = core * ThetaSum(terms=((Q(1, 1), M.one(), (Theta(d * _Y),)),))
    assert _decide_thetasum(w, use_fastpath=False) == _UNKNOWN
    assert w.is_zero is False
