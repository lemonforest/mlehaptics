"""rc103 — the ThetaSum ``is_zero`` CHIRALITY-PRESERVING PARALLEL fan-out suite.

The native ``srmech_thetasum_is_zero_interpolation_parallel`` is the FIRST
realization of the general ``parallel_independent_dispatch`` pattern: it peels
the top branching levels of the exact structural elliptic-interpolation tree
(``srmech_thetasum_is_zero_interpolation``, rc99) into independent sub-problems,
runs the UNCHANGED sequential DFS on each over a PAL worker pool, and AND-folds
the per-task verdicts. It is an ACCELERATOR — the Python sequential peer stays the
oracle (GIL). Two first-class contracts, both tested here as BLOCKERS:

  (1) CARRIER-PRESERVATION (exact-ℚ, no float): the parallel verdict is
      BYTE-FOR-BYTE the sequential interpolation verdict on EVERY case — the
      Weierstrass three-term identity, the Warnaar Cₙ ``Lemma 2.2`` completion,
      perturbations, single-term products, the rc102 ``θ(x⁴)·θ(x⁻⁴)`` case, and a
      ≥300-case randomized fuzz. Bit-identical IS the proof exactness was kept.

  (2) CHIRALITY-PRESERVATION (order-free over the ±-pair chiral halves): the
      verdict is INVARIANT to the task enumeration/scheduling order — two
      different task orders (``task_order`` 0 vs 1) and every worker count give the
      IDENTICAL verdict. This proves the fan-out holds both chiralities
      symmetrically, favoring neither (mirrors klein4's symmetric-over-sectors
      guarantee + the is_elliptic ``x → x⁻¹`` relabel invariance).

The parallel peer does NOT lift the fundamental n=2/N=2 wall (the documented
elliptic frontier); its value is the reusable, correctness-guaranteed pattern.
When the native peer is absent every assertion is skipped (the sequential peer +
pure oracle remain the deciders)."""

import faulthandler
import gc
import os
import random

import pytest

from srmech.amsc import ThetaSum
from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.q import Q
from srmech.amsc import _native

_A, _B, _C, _D = M.symbol("a"), M.symbol("b"), M.symbol("c"), M.symbol("d")
_X, _Y = M.symbol("x"), M.symbol("y")

_HAS_PAR = _native.has_native_thetasum_interpolation_parallel()
_HAS_SEQ = _native.has_native_thetasum_interpolation()
_skip = pytest.mark.skipif(
    not (_HAS_PAR and _HAS_SEQ),
    reason="native srmech_thetasum_is_zero_interpolation(_parallel) not loaded")


# ── HARD per-test timeout (defensive) ───────────────────────────────────────────
# The parallel peer is thread-based; a future deadlock would present as a STUCK job.
# Arm a stdlib ``faulthandler`` watchdog per test: if any test runs past the deadline
# it dumps ALL thread stacks and force-exits — a CLEAN, DIAGNOSED FAIL instead of a
# job that hangs until the runner force-kills it. Generous (180 s) so a slow-but-
# healthy CI runner never trips it (every right-sized test here is < 30 s even on a
# 2-core cell); cross-platform (Windows / macOS / Linux). No new dep (not
# pytest-timeout).
@pytest.fixture(autouse=True)
def _hard_timeout():
    faulthandler.dump_traceback_later(180, exit=True)
    try:
        yield
    finally:
        faulthandler.cancel_dump_traceback_later()


def _pm(u, v):
    """The plus/minus pair θ(u·v^±) = θ(uv)·θ(u/v) as its two Theta factors."""
    return (Theta(u * v), Theta(u / v))


def _seq(ts):
    """The SEQUENTIAL interpolation C verdict (the byte-for-byte parity oracle)."""
    m = ts._is_zero_c_marshal()
    if m is None:
        return True
    n_syms, xsym, ysym, psym, term_nthetas, monomials = m
    return _native.thetasum_is_zero_interpolation_c(
        n_syms, xsym, ysym, psym, term_nthetas, monomials)


def _par(ts, n_workers, task_order=0):
    """The PARALLEL interpolation C verdict at the given width + task order."""
    m = ts._is_zero_c_marshal()
    if m is None:
        return True
    n_syms, xsym, ysym, psym, term_nthetas, monomials = m
    return _native.thetasum_is_zero_interpolation_parallel_c(
        n_syms, xsym, ysym, psym, term_nthetas, monomials,
        n_workers=n_workers, task_order=task_order)


# workers spanning the serial fallback (1), typical (2, 3), and 4. Capped at 4 for
# MEMORY FRUGALITY: the parallel arena grows like (nw+1)·1.5·ws_bound2, so higher
# widths on the heaviest fixtures would need >7 GB on a py3.10 CI runner. Every
# fixture here is right-sized so its arena DECIDES within the edge budget at these
# widths (the test asserts the real verdict — it never "passes" by declining).
# Different widths still permute the static task partition (a schedule-invariance
# probe); the odd width 3 exercises an uneven task-to-worker split.
_WIDTHS = (1, 2, 3, 4)


def _assert_carrier_and_chirality(ts, expect):
    """BOTH contracts on one input: CARRIER (parallel == sequential == expect,
    bit-identical at every width) + CHIRALITY (forward task order == reverse task
    order — order-free). These fixtures are RIGHT-SIZED so the parallel peer DECIDES
    within the edge memory budget at every tested width — so we assert it actually
    decides (a ``None`` here would be the forbidden "pass by declining", not a
    contract check)."""
    seq = _seq(ts)
    assert seq is expect, (
        f"sequential interpolation mismatch: got {seq}, expect {expect}")
    for nw in _WIDTHS:
        fwd = _par(ts, nw, task_order=0)
        rev = _par(ts, nw, task_order=1)
        # CARRIER: the parallel peer DECIDES (never None — the fixtures fit the budget)
        # and its verdict is BIT-IDENTICAL to the sequential verdict at every width.
        assert fwd is seq, (
            f"CARRIER (nw={nw}, fwd): parallel {fwd} must DECIDE == sequential {seq}")
        assert rev is seq, (
            f"CARRIER (nw={nw}, rev): parallel {rev} must DECIDE == sequential {seq}")
        # CHIRALITY: forward and reverse task orders give the IDENTICAL verdict.
        assert fwd is rev, (
            f"CHIRALITY divergence (nw={nw}): task_order=0 gave {fwd}, "
            f"task_order=1 gave {rev} — the fan-out is NOT order-free (BLOCKER)")


# ── the Warnaar Cₙ elliptic Lemma 2.2 (n=2) residual (the rc98/rc99 keystone —
# Rosengren, arXiv:math/0101073 eq (6)) — the cross-variable identity whose ±-pair
# midpoint carries the √a obstruction, so ONLY the interpolation decides it. ──────
def _lemma22_cert():
    a, b, c, d, X, Y = _A, _B, _C, _D, _X, _Y

    def qp(k):
        return M.symbol("q", k)

    q = qp(1)
    e = a * a * q * (b * c * d).inv()
    xs = [X, Y]

    def th(m):
        return Theta(m)

    def term(k1, k2):
        ks = [k1, k2]
        num, den = [], []
        for i in range(2):
            xi, ki = xs[i], ks[i]
            if ki == 1:
                for u in (b, c, d, e):
                    num.append(th(u * xi))
                for u in (b, c, d, e):
                    den.append(th(a * q * xi * u.inv()))
        num.append(th(qp(k1 - k2) * X * Y.inv()))
        num.append(th(a * X * Y * qp(k1 + k2)))
        den.append(th(X * Y.inv()))
        den.append(th(a * X * Y * q))
        return R(M.scalar(Q((-1) ** ((k1 + k2) % 2), 1)) * qp(k2), num=num, den=den)

    lhs = ThetaSum.zero()
    for k1 in (0, 1):
        for k2 in (0, 1):
            lhs = lhs + ThetaSum.from_ellratio(term(k1, k2))
    rnum, rden = [], []
    for pr in (b * c, b * d, c * d):
        rnum.append(th(a * q * pr.inv()))
        rnum.append(th(a * pr.inv()))
    for xi in xs:
        rnum.append(th(a * q * xi * xi))
        rden.append(th(a * (b * c * d * xi).inv()))
        rden.append(th(a * q * xi * b.inv()))
        rden.append(th(a * q * xi * c.inv()))
        rden.append(th(a * q * xi * d.inv()))
    rhs = ThetaSum.from_ellratio(R(M.one(), num=rnum, den=rden))
    return lhs - rhs


# ── (1) CARRIER + CHIRALITY on the canonical fixtures ───────────────────────────
@_skip
def test_three_term_identity_parallel():
    _assert_carrier_and_chirality(ThetaSum.three_term(_A, _B, _C), True)
    _assert_carrier_and_chirality(ThetaSum.three_term(_A, _B, _C, x=_Y), True)
    _assert_carrier_and_chirality(ThetaSum.three_term(_A, _D, _C), True)


@_skip
def test_broken_three_term_parallel():
    broken = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_A, _X) + _pm(_B, _C)),
        (Q(-1, 1), M.one(), _pm(_B, _X) + _pm(_A, _C)),
        (Q(-1, 1), M.one(), _pm(_C, _X) + _pm(_B, _A)),   # weight 1, should be a/c
    ))
    _assert_carrier_and_chirality(broken, False)


@_skip
def test_lemma22_multivariate_parallel():
    """THE COMPLETION — the cross-variable Cₙ identity the whole arc exists for."""
    _assert_carrier_and_chirality(_lemma22_cert(), True)


@_skip
def test_lemma22_perturbations_parallel():
    cert = _lemma22_cert()
    terms = cert._terms
    pert = ThetaSum(
        terms=tuple((Q(2, 1) if i == 0 else Q(1, 1), pr, th)
                    for i, (pr, th) in enumerate(terms)),
        den_prefactor=cert._den_pref, den_thetas=cert._den_thetas)
    _assert_carrier_and_chirality(pert, False)
    dropped = ThetaSum(terms=tuple((Q(1, 1), pr, th) for (pr, th) in terms[1:]),
                       den_prefactor=cert._den_pref, den_thetas=cert._den_thetas)
    _assert_carrier_and_chirality(dropped, False)


@_skip
def test_single_term_products_parallel():
    """SOUNDNESS — single-term theta products are never proved ≡0."""
    prod = ThetaSum(terms=((Q(-1, 2), M.one(),
                            tuple(_pm(_A, M.symbol("f")) + _pm(_B, _C) + _pm(_B, _D)
                                  + _pm(_D, _X))),))
    _assert_carrier_and_chirality(prod, False)
    _assert_carrier_and_chirality(ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X)),)), False)
    _assert_carrier_and_chirality(
        ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X) + _pm(_A, _B)),)), False)


@_skip
def test_rc102_even_theta_deep_parallel():
    """The rc102 even-θ ``θ(a·xᵏ)·θ(a·x⁻ᵏ)`` single-term case (a genuine False that the
    rc102 ws_bound fix sized the base band for) — parallel keeps it False,
    bit-identically, at every width + both task orders. Right-sized to k=3 (a deep
    even-θ base band that DECIDES within the edge budget at nw ≤ 4); the full k=4
    sequential-sizing regression is covered by ``test_thetasum_interpolation_rc98``/
    ``_rc99`` (this parallel peer only needs a representative deep even-θ leaf)."""
    x3 = ThetaSum(terms=((Q(1, 1), M.one(),
                          (Theta(_A * _X * _X * _X),
                           Theta(_A * (_X * _X * _X).inv()))),))
    _assert_carrier_and_chirality(x3, False)
    _assert_carrier_and_chirality(
        ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X * _X)),)), False)  # even θ(a x²)


# ── (2) the serial fallback path (n_workers == 1 == the has_threads()==0 code) ───
@_skip
def test_serial_fallback_bit_identical():
    """``n_workers == 1`` takes the EXACT serial fallback (the same code a
    thread-less PAL runs) — its verdict is byte-for-byte the sequential peer on
    every fixture (True AND False)."""
    fixtures = [
        (ThetaSum.three_term(_A, _B, _C), True),
        (ThetaSum.three_term(_A, _B, _C, x=_Y), True),
        (_lemma22_cert(), True),
        (ThetaSum(terms=((Q(1, 1), M.one(), _pm(_A, _X)),)), False),
    ]
    for ts, exp in fixtures:
        seq = _seq(ts)
        one = _par(ts, 1)
        assert seq is exp, f"sequential mismatch: {seq} != {exp}"
        assert one is seq, (
            f"serial fallback (nw=1) divergence: {one} != {seq} (must DECIDE, not decline)")


# ── (3) the randomized CARRIER + CHIRALITY fuzz (≥300 decided cases) ─────────────
@_skip
def test_randomized_parallel_carrier_chirality_fuzz():
    """≥300 randomized ThetaSums — on EVERY one the NON-None parallel verdict (at
    several widths, BOTH task orders) EQUALS the sequential verdict, and the two
    task orders agree. A divergence in either contract is a BLOCKER."""
    syms = ["a", "b", "c", "d", "e", "f"]
    ms = {s: M.symbol(s) for s in syms}
    rng = random.Random(103103)

    def rp():
        return ms[rng.choice(syms)]

    def pmv(u, v):
        return (Theta(u * v), Theta(u / v))

    carrier_mism = 0
    chir_mism = 0
    decided = 0
    for _it in range(340):
        # Frugality: reclaim the prior iterations' ws arenas + ThetaSums so the fuzz
        # peak stays flat (each _par call can size up to the edge budget) rather than
        # accumulating across 340 iterations.
        if _it % 16 == 0:
            gc.collect()
        var = rng.choice([_X, _Y])
        kind = rng.choice(["tt", "tt_sum", "broken", "rand", "tt_minus", "scaled"])
        if kind == "tt":
            ts = ThetaSum.three_term(rp(), rp(), rp(), x=var)
        elif kind == "tt_sum":
            ts = (ThetaSum.three_term(rp(), rp(), rp(), x=_X)
                  + ThetaSum.three_term(rp(), rp(), rp(), x=_Y))
        elif kind == "broken":
            a, b, c = rp(), rp(), rp()
            w = rng.choice([Q(1, 1), Q(2, 1), Q(-1, 1), Q(3, 2)])
            ts = ThetaSum(terms=(
                (Q(1, 1), M.one(), pmv(a, var) + pmv(b, c)),
                (Q(-1, 1), M.one(), pmv(b, var) + pmv(a, c)),
                (w, M.one(), pmv(c, var) + pmv(b, a)),
            ))
        elif kind == "tt_minus":
            t = ThetaSum.three_term(rp(), rp(), rp(), x=var)
            ts = t - t
        elif kind == "scaled":
            t = ThetaSum.three_term(rp(), rp(), rp(), x=var)
            ts = t.scalar_mul(3) - t - t - t
        else:
            # ≤ 2 factors (memory frugality): every generated case DECIDES within the
            # edge budget at nw ≤ 4 — the fuzz asserts the real carrier/chirality
            # verdict, it does not "pass" by declining. (Wider products are the same
            # structural shape; the arena, not the contract, is what shrinks.)
            n = rng.choice([1, 2])
            facs = []
            for _i in range(n):
                facs.extend(pmv(rp(), rng.choice([var, rp()])))
            ts = ThetaSum(terms=((Q(rng.randint(-3, 3) or 1, rng.randint(1, 3)),
                                  M.one(), tuple(facs)),))
        seq = _seq(ts)
        nw = rng.choice([2, 3, 4])
        fwd = _par(ts, nw, 0)
        rev = _par(ts, nw, 1)
        # right-sized so the parallel peer always DECIDES — a None decline here would
        # be the forbidden "pass by declining" (the arena would have exceeded budget).
        assert fwd is not None and rev is not None, (
            f"parallel DECLINED a fuzz case (iter {_it}, nw={nw}) — right-size it")
        decided += 1
        if seq is not None and fwd is not seq:
            carrier_mism += 1
        if fwd is not rev:
            chir_mism += 1
    assert carrier_mism == 0, f"{carrier_mism} CARRIER (parallel≠sequential) divergences"
    assert chir_mism == 0, f"{chir_mism} CHIRALITY (order-dependent) divergences"
    assert decided >= 300, (
        f"only {decided} cases got a native parallel verdict — the peer must DECIDE")


# ── (4) the native peer is actually DISPATCHED (not always None) on the keystone ─
@_skip
def test_lemma22_decided_by_native_parallel():
    """``has_native_thetasum_interpolation_parallel`` is True AND the parallel peer
    DECIDES the genuine Cₙ Lemma 2.2 residual (== True) at width > 1."""
    assert _native.has_native_thetasum_interpolation_parallel() is True
    cert = _lemma22_cert()
    assert _par(cert, 4) is True
    assert _par(cert, 4, task_order=1) is True


def test_has_native_thetasum_interpolation_parallel_flag_present():
    """The probe exists + returns a bool (False on a pure / pre-rc103 build — the
    sequential peer + pure oracle then decide)."""
    assert isinstance(_native.has_native_thetasum_interpolation_parallel(), bool)


# ── (5) the SPEEDUP demonstration on a synthetic WIDE + DEEP is_zero tree ────────
def _wide_deep_true_case():
    """A genuine wide + deep interpolation tree: the Weierstrass three-term with
    THREE distinct degree-8 variables (each argument squared) and the interpolation
    point a rational scalar — so the min-degree variable is high, the root branches
    WIDE (d+1 nodes) and every level recurses deep (~9³ leaves, each a nontrivial
    base case). It is IDENTICALLY zero (the three-term identity), so the whole tree
    is explored (no early-exit) — the ideal fan-out shape. Real production is_zero
    inputs are either <0.5s or wall'd (dive A), so this SYNTHETIC case is what makes
    the parallel win measurable; production value is limited, the win is the pattern
    + the guardrails."""
    a, b, c = M.symbol("a"), M.symbol("b"), M.symbol("c")

    def sq(m):
        return m * m

    return ThetaSum.three_term(sq(a), sq(b), sq(c), x=M.scalar(Q(2, 1)))


@pytest.mark.skipif(
    not (_HAS_PAR and _HAS_SEQ and (os.cpu_count() or 1) >= 4),
    reason="parallel speedup demo needs the native peer + >= 4 cores")
def test_parallel_speedup_wide_deep():
    """Demonstrate a REAL wall-clock speedup on the synthetic wide+deep case while
    the verdict stays BYTE-FOR-BYTE the sequential verdict (the whole point: the
    fan-out is correct AND faster on a genuinely parallel tree). Gated to >= 4 cores
    so the assertion is not flaky on a 1-2 core CI runner; the verdict-parity is
    checked unconditionally in the suites above."""
    import time

    ts = _wide_deep_true_case()
    # Capped at 4 for memory frugality: wide_deep's arena at nw=4 (~0.2 GB) DECIDES
    # within the edge budget, and 4 workers already demonstrate the fan-out speedup.
    nw = min(os.cpu_count() or 1, 4)
    # warm (fault in the arena / JIT the marshal path) then time.
    seq0 = _seq(ts)
    t0 = time.perf_counter()
    seq = _seq(ts)
    seq_t = time.perf_counter() - t0
    t0 = time.perf_counter()
    par = _par(ts, nw)
    par_t = time.perf_counter() - t0
    par_rev = _par(ts, nw, task_order=1)
    # CARRIER: bit-identical verdict (hard, always).
    assert seq0 is True and seq is True, f"expected True sequential verdict, got {seq}"
    assert par is seq, f"CARRIER divergence: parallel={par} sequential={seq}"
    # CHIRALITY: reverse task order agrees.
    assert par_rev is par, f"CHIRALITY divergence: fwd={par} rev={par_rev}"
    # SPEEDUP: measurably faster (>= 4 cores). Generous margin absorbs jitter; the
    # observed win is ~1.9x at nw=4 (see the rc103 CHANGELOG).
    print(f"\nrc103 wide+deep is_zero speedup: seq={seq_t:.2f}s  "
          f"par(nw={nw})={par_t:.2f}s  speedup={seq_t / par_t:.2f}x")
    assert par_t < seq_t, (
        f"expected parallel faster on >= 4 cores: seq={seq_t:.2f}s par={par_t:.2f}s")
