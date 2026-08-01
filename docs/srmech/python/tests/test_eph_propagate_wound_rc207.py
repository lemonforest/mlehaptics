"""rc207 — EPH WOUND: ``laplacian.propagate_wound`` — the 2π seam-fold's
DIVMOD quotient KEPT (siona gh#1276; the #741 mod-should-be-divmod audit's
first concrete instance).

WHY: ``propagate``'s mandatory 2π seam-fold argument-reduces each per-mode
oscillation argument ``Im(z)·λ_k`` modulo 2π. That fold IS a divmod —
quotient ``w_k = round(Im(z)·λ_k / 2π)`` = the METACYCLE winding (thrown
away by propagate, the mod-collapse), remainder ``θ_k`` = the EPICYCLE
residue (what propagate keeps). ``propagate_wound`` keeps the GRADING: both
harvests at the seam, from the SAME fold, wired in the One's
``the_one(σ, θ, w)`` crank vocabulary (σ = the tower-graded
``sigma_effective``, θ = the epicycle phase, w = the metacycle winding).

Covers:
  (a) the DIFFERENTIAL — the epicycle harvest is BYTE-IDENTICAL to
      :func:`propagate`'s at the same dispatch tier (native AND forced-pure;
      carrying w must NOT perturb it);
  (b) the LOSSLESS ROUND-TRIP — ``2π·w_k + θ_k`` reconstructs the raw
      (unfolded) phase ``Im(z)·λ_k`` per mode (the One.unwrapped_phase
      reconstruction), |θ| ≤ π, w a whole int;
  (c) hand-checked windings (eigenvalues 1, 3 at t = 44/3 → w = 2, 7) +
      the RETROGRADE (negative-z) windings;
  (d) the TOWER-GRADED σ_eff anti-collapse — w = 5 (popcount 2 → +1) is
      DISTINGUISHED from w = 7 (popcount 3 → −1), where the bare ``w mod 2``
      would meld them; spinor_sign = the double-cover (−1)^w;
  (e) the thermal limit — z real → every winding 0, every θ 0 (the
      metacycle harvest genuinely lives on the oscillation);
  (f) Python == C parity — winding / σ_eff / spinor exact-integer equal,
      θ / harvest within-tol (the eigensolve tolerance);
  (g) read-only inputs; contracts (non-square L, u0 mismatch, n = 0);
      registration (ToolEntry; tools.total == 418; LAPLACIAN_OPS).

numpy-free. The 2π used by the round-trip check is the module's own
Machin-2π (``_EPH_TWO_PI``) — no forked constant in the test either.
"""
import cmath

from srmech import _native
from srmech.math import laplacian as L


# ── helpers (no numpy) ──────────────────────────────────────────────────


def _mag2(z):
    """Born |z|² = re² + im² (Class-K squares)."""
    c = complex(z)
    return c.real * c.real + c.imag * c.imag


def _force_pure(fn):
    """Run fn with the native dispatch masked (the complete pure path)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def _two_pi() -> float:
    """The module's own Machin-2π (no forked constant in the test)."""
    pn, pd = L._EPH_TWO_PI
    return pn / pd


def _modes_sorted(r):
    """The per-mode readout as (λ, w, θ, σ, spin) tuples sorted by λ —
    eigensolve mode order is an implementation detail, so parity checks
    compare mode SETS via the eigenvalue key."""
    return sorted(zip(r["eigenvalues"], r["winding"], r["theta"],
                      r["sigma_effective"], r["spinor_sign"]))


def _L2():
    """[[2,-1],[-1,2]] — eigenvalues exactly 1 and 3."""
    return [[2.0, -1.0], [-1.0, 2.0]]


def _rand_lap(n, seed):
    """A random real-symmetric graph Laplacian L = D − A (no numpy)."""
    st = seed

    def rnd():
        nonlocal st
        st = (st * 1103515245 + 12345) & 0x7FFFFFFF
        return st / float(0x7FFFFFFF)

    A = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            w = rnd()
            A[i][j] = w
            A[j][i] = w
    out = [[0.0] * n for _ in range(n)]
    for i in range(n):
        deg = sum(A[i])
        for j in range(n):
            out[i][j] = (deg if i == j else 0.0) - A[i][j]
    return out


# ── (a) the DIFFERENTIAL: harvest byte-identical to propagate ───────────


def test_harvest_byte_identical_to_propagate_native_tier():
    """Carrying w must NOT perturb the epicycle harvest — at the native tier
    (fresh lib) the wound peer shares propagate's statics, so the complex
    harvest is EXACTLY equal, bit for bit."""
    for n, seed in ((2, 11), (4, 22), (7, 33)):
        Lm = _rand_lap(n, seed)
        u0 = [((i * 7 + 3) % 11) - 5.0 for i in range(n)]
        for z in (0.7 + 0j, 3.9j, 1.1 * cmath.exp(1j * 0.7), 44.0j / 3.0):
            hv = L.propagate(Lm, u0, z)
            r = L.propagate_wound(Lm, u0, z)
            for i in range(n):
                a = complex(hv[i])
                b = complex(r["harvest_re"][i], r["harvest_im"][i])
                assert a == b, (
                    f"n={n} z={z} node {i}: wound harvest {b!r} != "
                    f"propagate {a!r} (same tier must be byte-identical)")


def test_harvest_byte_identical_to_propagate_pure_tier():
    """The same byte-identity holds on the forced-pure path (the wound pure
    cascade IS _eph_propagate_eig_py — the same fold, the same order)."""
    Lm = _rand_lap(5, 99)
    u0 = [1.0, -0.5, 0.25, 0.0, 2.0]
    z = 2.5j

    def both():
        return L.propagate(Lm, u0, z), L.propagate_wound(Lm, u0, z)

    hv, r = _force_pure(both)
    for i in range(5):
        a = complex(hv[i])
        b = complex(r["harvest_re"][i], r["harvest_im"][i])
        assert a == b, f"pure tier node {i}: {b!r} != {a!r}"


# ── (b) the LOSSLESS round-trip: 2π·w + θ == Im(z)·λ per mode ───────────


def test_unwrapped_round_trip_per_mode():
    two_pi = _two_pi()
    for n, seed in ((3, 5), (6, 8)):
        Lm = _rand_lap(n, seed)
        u0 = [1.0] * n
        for z in (10.0j, -7.3j, 2.0 + 25.0j):
            r = L.propagate_wound(Lm, u0, z)
            for lam, w, th, _sig, _spin in _modes_sorted(r):
                raw = z.imag * lam
                rec = two_pi * w + th
                err2 = (raw - rec) * (raw - rec)
                assert err2 < 1e-18, (
                    f"z={z} λ={lam}: 2π·{w} + {th} = {rec} != raw {raw} "
                    f"(the round-trip must be lossless to the fold grid)")
                assert isinstance(w, int)
                assert th * th <= (two_pi / 2.0) ** 2 + 1e-12   # |θ| ≤ π


def test_winding_is_genuinely_nonzero_at_large_t_lambda():
    """The metacycle harvest exists: at t·λ ≫ 2π the fold makes whole turns
    — the quotient propagate used to throw away is here, whole."""
    r = L.propagate_wound(_L2(), [1.0, 0.0], 44.0j / 3.0)   # t·λ = 44/3, 44
    modes = _modes_sorted(r)
    assert modes[0][1] == 2       # λ=1: 44/3 / 2π = 2.33 → w = 2
    assert modes[1][1] == 7       # λ=3: 44   / 2π = 7.00 → w = 7


# ── (c) hand-checked + retrograde windings ──────────────────────────────


def test_retrograde_winding_negates():
    """z → −z reverses the crank: w flips sign (the Class-C orientation
    reversal), θ flips sign, and the round-trip still holds."""
    two_pi = _two_pi()
    fwd = L.propagate_wound(_L2(), [1.0, 0.0], 44.0j / 3.0)
    bwd = L.propagate_wound(_L2(), [1.0, 0.0], -44.0j / 3.0)
    for (lf, wf, tf, _s1, _s2), (lb, wb, tb, _s3, _s4) in zip(
            _modes_sorted(fwd), _modes_sorted(bwd)):
        assert lf == lb
        assert wb == -wf, f"retrograde winding must negate: {wb} != -{wf}"
        d = tb + tf
        assert d * d < 1e-18, f"retrograde θ must negate: {tb} != -{tf}"
        raw = -44.0 / 3.0 * lb
        rec = two_pi * wb + tb
        assert (raw - rec) * (raw - rec) < 1e-18


def test_diagonal_hand_windings():
    """Diagonal L with λ chosen to land w = 5 and w = 7 at z = i — the
    winding is per-MODE, read straight off the eigenvalue."""
    two_pi = _two_pi()
    lam5 = 5.0 * two_pi          # Im(z)·λ / 2π = 5 exactly (to the grid)
    lam7 = 7.0 * two_pi
    Lm = [[lam5, 0.0], [0.0, lam7]]
    r = L.propagate_wound(Lm, [1.0, 1.0], 1.0j)
    modes = _modes_sorted(r)
    assert [m[1] for m in modes] == [5, 7]
    for _lam, _w, th, _sig, _spin in modes:
        assert th * th < 1e-12    # residue ≈ 0 at an exact multiple


# ── (d) the crank chirality dials: tower-graded σ_eff + spinor sign ─────


def test_sigma_effective_is_tower_graded_not_bare_mod2():
    """THE anti-collapse: w = 5 (binary 101, popcount 2) → σ_eff = +1;
    w = 7 (binary 111, popcount 3) → σ_eff = −1. The bare ``w mod 2`` melds
    them (both odd); the divmod binary tower distinguishes them. Both have
    spinor_sign = −1 (the double cover sees only the parity — correct
    physics, the winding itself stays whole)."""
    two_pi = _two_pi()
    Lm = [[5.0 * two_pi, 0.0], [0.0, 7.0 * two_pi]]
    r = L.propagate_wound(Lm, [1.0, 1.0], 1.0j)
    modes = _modes_sorted(r)
    assert [m[1] for m in modes] == [5, 7]
    assert [m[3] for m in modes] == [+1, -1], (
        "σ_eff must grade by the tower popcount (5→+1, 7→−1), "
        "not the melding bare w mod 2")
    assert [m[4] for m in modes] == [-1, -1]   # (−1)^5 = (−1)^7 = −1


def test_crank_readouts_match_the_one():
    """The wound readouts ARE the One's readouts: for each mode,
    the_one(+1, 0, 1, w=(w_k, 0, 0)) reports the SAME sigma_effective and
    spinor_sign (the reuse contract — never re-derived)."""
    from srmech.amsc.cascade.one import the_one
    r = L.propagate_wound(_L2(), [1.0, 0.0], 44.0j / 3.0)
    for lam, w, th, sig, spin in _modes_sorted(r):
        one = the_one(+1, 0, 1, w=(w, 0, 0))
        assert one.sigma_effective() == sig
        assert one.spinor_sign == spin


# ── (e) the thermal limit: z real → no oscillation → no winding ─────────


def test_thermal_z_has_zero_winding():
    r = L.propagate_wound(_rand_lap(4, 7), [1.0, 0.5, -0.5, 1.0], 0.8 + 0j)
    assert r["winding"] == [0, 0, 0, 0]
    assert all(t == 0.0 for t in r["theta"])
    assert r["sigma_effective"] == [1, 1, 1, 1]    # at rest → σ = +1
    assert r["spinor_sign"] == [1, 1, 1, 1]


def test_small_coherent_t_winding_zero_theta_is_phase():
    """|Im(z)·λ| < π → w = 0 and θ IS the raw phase (the fold is the
    identity inside one seam)."""
    r = L.propagate_wound(_L2(), [1.0, 0.0], 0.5j)   # t·λ = 0.5, 1.5 < π
    for lam, w, th, _sig, _spin in _modes_sorted(r):
        assert w == 0
        d = th - 0.5 * lam
        assert d * d < 1e-18


# ── (f) Python == C parity ──────────────────────────────────────────────


def test_python_equals_c_parity():
    """Winding / σ_eff / spinor are exact integers → EQUAL native vs pure
    (generic angles — no seam-boundary cases here); θ and the harvest agree
    within the eigensolve tolerance."""
    for n in (2, 3, 5, 8):
        Lm = _rand_lap(n, 1234 + n)
        u0 = [((i * 7 + 3) % 11) - 5.0 for i in range(n)]
        for z in (0.7 + 0j, 9.9j, 1.1 * cmath.exp(1j * 0.7), -13.0j):
            nat = L.propagate_wound(Lm, u0, z)
            pur = _force_pure(lambda: L.propagate_wound(Lm, u0, z))
            nm = _modes_sorted(nat)
            pm = _modes_sorted(pur)
            for (ln, wn, tn, sn, pn), (lp, wp, tp, sp, pp) in zip(nm, pm):
                dl = ln - lp
                assert dl * dl < 1e-16, f"λ drift: {ln} vs {lp}"
                assert wn == wp, f"winding native {wn} != pure {wp}"
                assert sn == sp and pn == pp
                dt = tn - tp
                assert dt * dt < 1e-20, f"θ native {tn} != pure {tp}"
            # harvest within-tol (basis-invariant, eigensolve tolerance)
            err = max(
                _mag2(complex(a, b) - complex(c, d))
                for a, b, c, d in zip(nat["harvest_re"], nat["harvest_im"],
                                      pur["harvest_re"], pur["harvest_im"])
            ) ** 0.5
            assert err < 1e-8, f"n={n} z={z}: harvest err={err:.3e}"


def test_complex_hermitian_input():
    """Hermitian [[2, i], [-i, 2]] — eigenvalues 1, 3; the wound readout
    rides the complex path too."""
    two_pi = _two_pi()
    H = [[2.0 + 0j, 1j], [-1j, 2.0 + 0j]]
    r = L.propagate_wound(H, [1.0 + 0j, 0.0 + 0j], 15.0j)
    modes = _modes_sorted(r)
    assert [m[1] for m in modes] == [2, 7]     # 15/2π=2.39; 45/2π=7.16
    for lam, w, th, _sig, _spin in modes:
        raw = 15.0 * lam
        rec = two_pi * w + th
        assert (raw - rec) * (raw - rec) < 1e-18


# ── (g) read-only + contracts + registration ────────────────────────────


def test_inputs_unmutated():
    Lm = _L2()
    u0 = [1.0, 0.5]
    Lsnap = [row[:] for row in Lm]
    usnap = u0[:]
    L.propagate_wound(Lm, u0, 0.7 + 0.3j)
    assert Lm == Lsnap, "L mutated"
    assert u0 == usnap, "u0 mutated"


def test_contracts():
    import pytest
    with pytest.raises(ValueError):
        L.propagate_wound([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], [1.0, 2.0],
                          1.0)                                  # non-square
    with pytest.raises(ValueError):
        L.propagate_wound([[1.0, 0.0], [0.0, 1.0]], [1.0], 1.0)  # u0 mismatch
    r0 = L.propagate_wound([], [], 1.0)                          # n = 0
    assert r0 == {
        "harvest_re": [], "harvest_im": [], "eigenvalues": [],
        "winding": [], "theta": [], "sigma_effective": [], "spinor_sign": [],
    }


def test_json_native_types():
    r = L.propagate_wound(_L2(), [1.0, 0.0], 10.0j)
    assert all(isinstance(x, float) for x in r["harvest_re"])
    assert all(isinstance(x, float) for x in r["harvest_im"])
    assert all(isinstance(x, float) for x in r["eigenvalues"])
    assert all(isinstance(x, int) for x in r["winding"])
    assert all(isinstance(x, float) for x in r["theta"])
    assert all(x in (1, -1) for x in r["sigma_effective"])
    assert all(x in (1, -1) for x in r["spinor_sign"])


def test_registration_and_count():
    import srmech
    from srmech.introspect.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.math.laplacian.propagate_wound" in names
    assert len(get_tool_schema().tools) == 525
    assert srmech.describe()["tools"]["total"] == 525
    assert "propagate_wound" in L.LAPLACIAN_OPS
