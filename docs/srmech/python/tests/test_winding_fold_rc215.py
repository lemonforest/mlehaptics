"""rc215 — the public ``cascade.winding_fold`` op: the 2π seam-fold's DIVMOD
``theta → (w, theta_res)`` with ``theta = 2π·w + theta_res`` exposed
first-class (the #741 mod-should-be-divmod audit, finding F-2).

WHY: the exact fold has existed since rc207/gh#1276 — natively as
``srmech_winding_fold`` (the Q61 2/π quarter-turn machinery) and pure as the
laplacian ``_eph_seam_fold`` (the exact-rational Machin-2π divmod) — but was
reachable ONLY through ``propagate_wound``. An external consumer with an
accumulated angle (a Kuramoto phase, an ``Im(z)·λ`` from its own solve) had to
hand-roll a float ``theta % (2*pi)``: BOTH the grading-collapse the divmod
audit hunts AND a precision hazard vs the exact fold.

Covers:
  (a) the BATTERY — 0, sub-seam small angles, ±π, ±(π+ε), ±(2π+ε), whole
      multiples of 2π (small and large), negatives: correct ``w`` (Fraction
      oracle on the module's own Machin-2π — no forked constant) and the
      LOSSLESS round-trip ``2π·w + theta_res == theta`` on the fold grid
      (Fraction-exact bound);
  (b) retrograde antisymmetry — ``winding_fold(−θ) == (−w, −θ_res)`` (the
      Class-C orientation reversal of both harvests);
  (c) the ≥2⁵⁵ native-domain boundary — the honest srmech_cos-family bound:
      native declines, the COMPLETE pure Machin-2π divmod answers exactly at
      any finite float (Fraction oracle);
  (d) native == forced-pure parity — ``w`` exact-integer equal; ``theta_res``
      to the fold grids' common resolution (Q61 native / 2⁻⁴⁴ pure);
  (e) the propagate_wound cross-check — the SAME fold, per mode: the public
      op reproduces the wound propagator's (w, θ) verdicts;
  (f) the One-readout reuse contract — the fold's w feeds the metacycle dial:
      the_one(+1, 0, 1, w=(w,0,0)) reports the matching sigma_effective /
      spinor_sign;
  (g) contracts — complex → TypeError, NaN/±Inf → ValueError, int accepted,
      (int, float) return types (never bool);
  (h) registration — ToolEntry; tools.total == 418; cascade.__all__.

numpy-free. The 2π used by every oracle is the module's own Machin-2π
(``laplacian._EPH_TWO_PI``) — no forked constant in the test either.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as L
from srmech.amsc.cascade import winding_fold


# ── helpers (no numpy) ──────────────────────────────────────────────────

#: The pure fold grid quantum (laplacian._EPH_FOLD_DEN = 2^44) — theta_res is
#: quantised to multiples of 2^-44 on the pure path (finer, Q61, native).
_GRID = Fraction(1, 1 << 44)

#: The two 2π approximations (Machin-2π pure / Q61 2/π native) agree to
#: ~2^-60; the round-trip bound carries |w| of that mismatch.
_TWO_PI_MISMATCH = Fraction(1, 1 << 60)


def _two_pi_fraction() -> Fraction:
    """The module's own Machin-2π as an exact Fraction (no forked constant)."""
    pn, pd = L._EPH_TWO_PI
    return Fraction(pn, pd)


def _oracle_w(theta: float) -> int:
    """The winding oracle: round-half-toward-+∞ of θ/2π in EXACT rational
    arithmetic (the _eph_round_div convention, reimplemented independently)."""
    q = Fraction(theta) / _two_pi_fraction()
    fl = q.numerator // q.denominator          # floor
    r = q - fl
    return fl + (1 if 2 * r >= 1 else 0)


def _assert_fold_contract(theta: float, w: int, theta_res: float,
                          *, w_expected: int = None) -> None:
    """The shared fold contract: types, |theta_res| ≤ π (+grid), the
    Fraction-exact lossless round-trip, and (optionally) the exact w."""
    assert type(w) is int, f"w must be int, got {type(w).__name__}"
    assert type(theta_res) is float, (
        f"theta_res must be float, got {type(theta_res).__name__}")
    two_pi = _two_pi_fraction()
    if w_expected is not None:
        assert w == w_expected, (
            f"theta={theta!r}: w={w} != expected {w_expected}")
    # |theta_res| ≤ π to the grid (Class-K magnitude via explicit branch)
    mag = theta_res if theta_res >= 0.0 else -theta_res
    assert Fraction(mag) <= two_pi / 2 + _GRID, (
        f"theta={theta!r}: |theta_res|={mag} exceeds π")
    # the LOSSLESS round-trip on the fold grid: theta − (2π·w + theta_res)
    # bounded by the grid quantum + |w|·(the 2π-approximation mismatch)
    err = Fraction(theta) - two_pi * w - Fraction(theta_res)
    mag_w = w if w >= 0 else -w
    bound = _GRID + mag_w * _TWO_PI_MISMATCH
    err_mag = err if err >= 0 else -err
    assert err_mag <= bound, (
        f"theta={theta!r}: round-trip residual {float(err_mag):.3e} exceeds "
        f"the fold-grid bound {float(bound):.3e} (w={w}, "
        f"theta_res={theta_res!r})")


def _force_pure(fn):
    """Run fn with the native dispatch masked (the complete pure path)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def _float_pi() -> float:
    """float(π) from the module's own Machin-2π (no math import)."""
    pn, pd = L._EPH_TWO_PI
    return pn / pd / 2.0


def _float_two_pi() -> float:
    pn, pd = L._EPH_TWO_PI
    return pn / pd


# ── (a) the battery ─────────────────────────────────────────────────────


def test_zero_is_the_rest_state():
    assert winding_fold(0.0) == (0, 0.0)
    assert winding_fold(-0.0) == (0, 0.0)


def test_sub_seam_angles_have_zero_winding():
    """|θ| < π → w = 0 and theta_res IS θ (the fold is the identity inside
    one seam) — to the fold grid."""
    for theta in (1e-9, -1e-9, 0.25, -0.25, 0.5, 3.0, -3.0, 3.14159, -3.14159):
        w, tr = winding_fold(theta)
        _assert_fold_contract(theta, w, tr, w_expected=0)
        d = tr - theta
        assert d * d <= float(_GRID) ** 2 * 4.0, (
            f"theta={theta}: theta_res {tr} != theta inside one seam")


def test_pi_boundary_stays_inside_the_first_seam():
    """float(π) is BELOW the true half-turn (float rounds π down), so both
    ±float(π) fold to w = 0 with theta_res = ±float(π) — the exact fold
    resolves what a float `theta % (2π)` blurs at the seam."""
    fpi = _float_pi()
    for theta, w_exp in ((fpi, 0), (-fpi, 0)):
        w, tr = winding_fold(theta)
        _assert_fold_contract(theta, w, tr, w_expected=w_exp)


def test_just_past_the_seam_winds_once():
    fpi = _float_pi()
    for theta, w_exp in ((fpi + 0.1, 1), (-(fpi + 0.1), -1)):
        w, tr = winding_fold(theta)
        _assert_fold_contract(theta, w, tr, w_expected=w_exp)


def test_one_turn_plus_residue():
    ftp = _float_two_pi()
    for theta, w_exp, tr_exp in ((ftp + 0.25, 1, 0.25),
                                 (-(ftp + 0.25), -1, -0.25)):
        w, tr = winding_fold(theta)
        _assert_fold_contract(theta, w, tr, w_expected=w_exp)
        d = tr - tr_exp
        assert d * d < 1e-24, f"theta={theta}: residue {tr} != {tr_exp}"


def test_whole_multiples_of_two_pi():
    """k·float(2π) → w = k with a near-zero residue (the float-vs-exact 2π
    gap × k), for small AND large k, both signs."""
    ftp = _float_two_pi()
    for k in (1, 2, 3, 10, 1000, 123456, 1000000):
        for sk in (k, -k):
            theta = sk * ftp
            w, tr = winding_fold(theta)
            _assert_fold_contract(theta, w, tr, w_expected=sk)
            # the residue is the accumulated float-2π error: tiny vs π
            mag = tr if tr >= 0.0 else -tr
            assert mag < 1e-6, (
                f"k={sk}: residue {tr} unexpectedly large for a whole turn")


def test_generic_angles_match_the_fraction_oracle():
    """Generic (non-boundary) angles: w equals the independent exact-rational
    round-half-up oracle, and the round-trip is lossless."""
    for theta in (7.0, -7.0, 44.0 / 3.0, -44.0 / 3.0, 44.0, 100.5, -273.75,
                  12345.6789, -98765.4321, 1.0e6, -1.0e6):
        w, tr = winding_fold(theta)
        _assert_fold_contract(theta, w, tr, w_expected=_oracle_w(theta))


# ── (b) retrograde antisymmetry ─────────────────────────────────────────


def test_retrograde_negates_both_harvests():
    """θ → −θ reverses the crank: w flips sign (Class-C orientation
    reversal), theta_res flips sign — generic angles (no seam-boundary
    half-grid cases)."""
    for theta in (0.5, 3.0, 7.0, 44.0 / 3.0, 100.5, 12345.6789):
        wf, tf = winding_fold(theta)
        wb, tb = winding_fold(-theta)
        assert wb == -wf, f"theta={theta}: retrograde w {wb} != {-wf}"
        d = tb + tf
        assert d * d <= float(_GRID) ** 2 * 4.0, (
            f"theta={theta}: retrograde theta_res {tb} != {-tf}")


# ── (c) the ≥2⁵⁵ native-domain boundary ─────────────────────────────────


def test_beyond_native_domain_falls_to_the_exact_pure_fold():
    """|θ| ≥ 2^55 is outside the native (srmech_cos-family) domain — the op
    still answers, via the COMPLETE exact-rational Machin-2π divmod, and the
    answer matches the Fraction oracle at any finite float."""
    for theta in (2.0 ** 55, -(2.0 ** 55), 2.0 ** 56, 2.0 ** 60 + 12345.0,
                  -(2.0 ** 60 + 12345.0)):
        w, tr = winding_fold(theta)
        _assert_fold_contract(theta, w, tr, w_expected=_oracle_w(theta))


# ── (d) native == pure parity ───────────────────────────────────────────


def test_native_equals_pure_verdicts():
    """w exact-integer equal; theta_res to the fold grids' common resolution
    (Q61 native / 2⁻⁴⁴ pure quantise the SAME real residue) PLUS |w|·(the
    2π-approximation mismatch) — the two paths subtract w windings of two
    DIFFERENT exact-rational 2π's (Q61 quarter-turn native / Machin pure,
    agreeing to ≲2⁻⁶⁰), so the residues drift apart by |w| of that gap —
    generic angles, both signs, small through large windings."""
    battery = (0.0, 1e-9, 0.5, 3.0, _float_pi(), 7.0, 44.0 / 3.0, 44.0,
               100.5, 12345.6789, 1.0e6, 2.0 ** 40 + 0.375)
    for theta in battery:
        for s in (1.0, -1.0):
            t = s * theta
            wn, tn = winding_fold(t)
            wp, tp = _force_pure(lambda: winding_fold(t))
            assert wn == wp, f"theta={t}: native w {wn} != pure {wp}"
            mag_w = wn if wn >= 0 else -wn
            bound = 2.0 * float(_GRID) + mag_w * float(_TWO_PI_MISMATCH)
            d = tn - tp
            assert d * d <= bound * bound, (
                f"theta={t}: native theta_res {tn} != pure {tp} beyond the "
                f"common fold-grid resolution (bound {bound:.3e}, w={wn})")


# ── (e) the propagate_wound cross-check (the SAME fold) ─────────────────


def test_matches_propagate_wound_per_mode():
    """The wound propagator's per-mode (w, θ) verdicts ARE this fold applied
    to Im(z)·λ_k — one divmod, both surfaces (the L2 fixture: eigenvalues
    exactly 1 and 3; t = 44/3 → w = 2, 7 — the rc207 hand-checked pair)."""
    r = L.propagate_wound([[2.0, -1.0], [-1.0, 2.0]], [1.0, 0.0], 44.0j / 3.0)
    modes = sorted(zip(r["eigenvalues"], r["winding"], r["theta"]))
    assert [m[1] for m in modes] == [2, 7]
    for lam, w_mode, th_mode in modes:
        w, tr = winding_fold(44.0 / 3.0 * lam)
        assert w == w_mode, (
            f"λ={lam}: winding_fold w {w} != propagate_wound {w_mode}")
        d = tr - th_mode
        # the mode's t·λ carries the eigensolve tolerance; grid + slack
        assert d * d < 1e-16, (
            f"λ={lam}: winding_fold theta_res {tr} != wound θ {th_mode}")


# ── (f) the One-readout reuse contract ──────────────────────────────────


def test_winding_feeds_the_one_metacycle_dial():
    """The fold's w lifts straight into the One: the_one(+1, 0, 1,
    w=(w,0,0)) reports the tower-graded sigma_effective and the double-cover
    spinor_sign for THIS winding (never re-derived)."""
    from srmech.amsc.cascade.one import the_one, winding_tower
    for theta in (44.0 / 3.0, 44.0, 100.5, -100.5):
        w, _tr = winding_fold(theta)
        one = the_one(+1, 0, 1, w=(w, 0, 0))
        assert one.spinor_sign == (1 if w % 2 == 0 else -1)
        pop = sum(winding_tower(w))
        assert one.sigma_effective() == (1 if pop % 2 == 0 else -1)


# ── (g) contracts ───────────────────────────────────────────────────────


def test_complex_rejected():
    with pytest.raises(TypeError):
        winding_fold(1.0 + 2.0j)


def test_non_finite_rejected():
    nan = float("nan")
    inf = float("inf")
    for bad in (nan, inf, -inf):
        with pytest.raises(ValueError):
            winding_fold(bad)


def test_int_input_accepted():
    assert winding_fold(0) == (0, 0.0)
    w, tr = winding_fold(7)
    w_f, tr_f = winding_fold(7.0)
    assert (w, tr) == (w_f, tr_f)


def test_pure_path_contracts_match():
    """The forced-pure path enforces the SAME boundary contracts."""
    def probe():
        with pytest.raises(TypeError):
            winding_fold(1.0j)
        with pytest.raises(ValueError):
            winding_fold(float("inf"))
        return winding_fold(7.0)
    w, tr = _force_pure(probe)
    assert w == _oracle_w(7.0)


# ── (h) registration ────────────────────────────────────────────────────


def test_registration_and_count():
    import srmech
    from srmech.amsc import cascade
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    names = {t.name for t in schema.tools}
    assert "srmech.amsc.cascade.winding_fold" in names
    assert len(schema.tools) == 418
    assert srmech.describe()["tools"]["total"] == 418
    assert "winding_fold" in cascade.__all__
    entry = schema.lookup("srmech.amsc.cascade.winding_fold")
    assert entry.category == "cascade"
    assert entry.owner == "srmech"
    assert [p.name for p in entry.parameters] == ["theta"]
