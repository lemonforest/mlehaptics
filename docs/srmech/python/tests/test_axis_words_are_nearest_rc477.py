"""rc477 (`#T1188`) — THE AXIS IS THE NEAREST Q61 WORD, AND WAS NOT.

The certificates this release rests on, decided by EXACT INTEGER arithmetic and
each one paired with a can-fail control that must reject a value one unit away.
No ``math.*``, no ``fractions``, no numpy, no libm: the oracle is Python ``int``
and the shipped Class-N cascade, and the only float in the file is the value
under test.

⚠️ **Why a parity row is not enough.** Through rc476 both projections normalised
the axis the same wrong way, so byte-identity between them was green while the
served value was 179 Q61 words off. The C↔Python parity rows in
``test_quaternion_log_slerp_rc385`` and ``test_hypercomplex_couple_parity`` say
the two agree; these rows say WHAT they agree on. Neither claim substitutes for
the other, and this file exists because the missing half is the one that hid a
defect for the life of the op.

WHAT IS CERTIFIED

* ``_axis_q61`` returns the NEAREST Q61 word of ``sign(wᵢ)·√(wᵢ²/S)``, by

      (2u − 1)²·S  <  wᵢ²·2¹²⁴  <  (2u + 1)²·S

* ``_axis_float`` returns the CORRECTLY ROUNDED double of the same quantity,
  decided against the TRUE adjacent doubles' midpoints (so a binade boundary,
  where the gap below is half the gap above, is exact too).
* the norm residue obeys a STATED envelope — and is **not** claimed to be zero,
  which would be false.
* the in-tree ``_HC_INV_Q61`` anchor is ABSORBED by the general formula rather
  than duplicated by it.

WHAT IS NOT CERTIFIED HERE. The octonion multiply's accumulation order, any
iterative float kernel, and any ``precision=`` route. rc477 touches none of
them and this file claims nothing about them.
"""
from __future__ import annotations

import struct

import pytest

from srmech.cascade import hypercomplex_dft as H
from srmech.math import qalg as _qalg
from srmech.math import rational as R
from srmech.math.q import Q

Q61 = 1 << 61

#: ``(name, integer direction, S)`` — the named axes, the exactly-representable
#: 3-4-5 direction, a signed one, and two general integer vectors.
_AXES = [
    ("i        k=1", [0, 1, 0, 0, 0, 0, 0, 0], 1),
    ("ijk      S=3", [0, 1, 1, 1, 0, 0, 0, 0], 3),
    ("diagonal S=7", [0, 1, 1, 1, 1, 1, 1, 1], 7),
    ("3-4-5    S=25", [0, 3, 4, 0, 0, 0, 0, 0], 25),
    ("[2,6,9]  S=121", [0, 2, 6, 9, 0, 0, 0, 0], 121),
    ("signed   S=3", [0, 1, -1, 1, 0, 0, 0, 0], 3),
    ("[0,1,1,0] S=2", [0, 1, 1, 0, 0, 0, 0, 0], 2),
]


# ── the two certificates, as exact integer predicates ─────────────────────
def _word_is_nearest(u: int, w: int, s: int) -> bool:
    """``(2u−1)²·S < w²·2¹²⁴ < (2u+1)²·S`` — no float anywhere."""
    mid = (w * w) << 124
    return (2 * u - 1) ** 2 * s < mid < (2 * u + 1) ** 2 * s


def _pair(x: float):
    """``(n, e)`` with ``x == n·2**e`` EXACTLY."""
    n, d = float(x).as_integer_ratio()
    e = 0
    while d > 1:
        d >>= 1
        e -= 1
    return n, e


def _neighbour(x: float, step: int) -> float:
    u = int.from_bytes(struct.pack("<d", x), "little")
    return struct.unpack("<d", (u + step).to_bytes(8, "little"))[0]


def _midpoint(a: float, b: float):
    na, ea = _pair(a)
    nb, eb = _pair(b)
    e0 = min(ea, eb)
    return na * (1 << (ea - e0)) + nb * (1 << (eb - e0)), e0 - 1


def _double_is_cr(x: float, w: int, s: int) -> bool:
    """``x`` IS the correctly rounded double of ``√(w²/S)``.

    Decided against the TRUE adjacent doubles rather than against ``m ± 1`` on
    a reduced significand — that shortcut accepts a value one ulp low, measured
    on 143 of 399 ``k`` while this file was being written."""
    if x <= 0.0:
        return False

    def below(n, e):                     # (n·2**e)² < w²/S ?
        lhs = n * n
        if 2 * e >= 0:
            return (lhs << (2 * e)) * s < w * w
        return lhs * s < ((w * w) << (-2 * e))

    lo = _midpoint(_neighbour(x, -1), x)
    hi = _midpoint(x, _neighbour(x, 1))
    return below(*lo) and not below(*hi)


# ── the certificates fire, and their controls fire too ────────────────────
@pytest.mark.parametrize("name,w,s", _AXES)
def test_every_q61_axis_word_is_the_nearest(name, w, s):
    """The Q61 projection, per component."""
    words = _qalg._axis_q61(w, s)
    assert len(words) == len(w)
    for wi, u in zip(w, words):
        if wi == 0:
            assert u == 0, f"{name}: a zero direction gave a non-zero word {u}"
            continue
        mag = u if u > 0 else -u             # Class K pin-slot, never abs()
        assert (u > 0) == (wi > 0), f"{name}: the Class-C sign did not survive"
        assert _word_is_nearest(mag, wi, s), (
            f"{name}: word {mag} is not the nearest Q61 word of √({wi}²/{s})")


@pytest.mark.parametrize("name,w,s", _AXES)
def test_the_word_certificate_rejects_both_neighbours(name, w, s):
    """THE CAN-FAIL CONTROL. A predicate that cannot say no is not a test."""
    for wi, u in zip(w, _qalg._axis_q61(w, s)):
        if wi == 0:
            continue
        mag = u if u > 0 else -u
        assert not _word_is_nearest(mag + 1, wi, s), (
            f"{name}: the certificate ACCEPTED the word one unit above nearest")
        assert not _word_is_nearest(mag - 1, wi, s), (
            f"{name}: the certificate ACCEPTED the word one unit below nearest")


@pytest.mark.parametrize("name,w,s", _AXES)
def test_every_float_axis_component_is_correctly_rounded(name, w, s):
    """The float projection, per component."""
    got = _qalg._axis_float(w, s)
    for wi, x in zip(w, got):
        if wi == 0:
            assert x == 0.0
            continue
        mag = x if x > 0.0 else -x          # Class K pin-slot
        assert (x > 0.0) == (wi > 0)
        assert _double_is_cr(mag, wi, s), (
            f"{name}: {mag!r} is not the correctly rounded √({wi}²/{s})")


@pytest.mark.parametrize("name,w,s", _AXES)
def test_the_double_certificate_rejects_both_neighbours(name, w, s):
    """THE CAN-FAIL CONTROL for the float half."""
    for wi, x in zip(w, _qalg._axis_float(w, s)):
        if wi == 0:
            continue
        mag = x if x > 0.0 else -x
        assert not _double_is_cr(_neighbour(mag, 1), wi, s), (
            f"{name}: the certificate ACCEPTED one ulp ABOVE the CR double")
        assert not _double_is_cr(_neighbour(mag, -1), wi, s), (
            f"{name}: the certificate ACCEPTED one ulp BELOW the CR double")


# ── the norm envelope: STATED, decidable, and NOT claimed to be zero ───────
def _envelope_holds(words, w, s) -> bool:
    """``(4·|D| − n)²·S ≤ 2¹²⁶·(Σ|wᵢ|)²`` with ``D = Σuᵢ² − 2¹²²``.

    The residue is NOT zero and this file does not pretend it is: 61 bits of
    grid cannot hold an irrational unit. What IS decidable is that the residue
    stays inside the per-axis envelope ``(Σ|wᵢ|)/√S`` grid units, restated here
    without the square root so it is an integer predicate."""
    d = sum(u * u for u in words) - (1 << 122)
    d = d if d >= 0 else -d                  # Class K pin-slot
    n = sum(1 for x in w if x != 0)
    sw = sum(x if x > 0 else -x for x in w)
    if 4 * d < n:
        return True                          # trivially inside
    return (4 * d - n) ** 2 * s <= (sw * sw) << 126


@pytest.mark.parametrize("name,w,s", _AXES)
def test_the_norm_residue_is_inside_the_stated_envelope(name, w, s):
    assert _envelope_holds(_qalg._axis_q61(w, s), w, s), (
        f"{name}: the norm residue is outside the stated envelope")


@pytest.mark.parametrize("name,w,s", _AXES)
def test_the_envelope_rejects_a_perturbed_word(name, w, s):
    """THE CAN-FAIL CONTROL. One word moved by 4·10⁸ must leave the envelope."""
    words = list(_qalg._axis_q61(w, s))
    idx = next(i for i, x in enumerate(w) if x != 0)
    words[idx] += 400000000
    assert not _envelope_holds(words, w, s), (
        f"{name}: the envelope ACCEPTED a word perturbed by 4e8 — it is not "
        "measuring anything")


def test_the_residue_is_not_zero_and_the_figures_are_the_release_s(capsys):
    """The residue MOVED, and by how much is the release's claim.

    Before rc477 the served words came from a thrice-rounded float axis; after,
    from the integer direction. The before figures are recorded in the rc477
    CHANGELOG entry and the ``srmech.h`` v29 history; what this row asserts is
    the AFTER, so a regression toward the old value fails here."""
    seen = {}
    for name, w, s in _AXES:
        words = _qalg._axis_q61(w, s)
        d = sum(u * u for u in words) - (1 << 122)
        seen[name] = d / float(1 << 61)
    with capsys.disabled():
        print("\n  ‖μ‖²−1, in Q61 grid units:")
        for k, v in seen.items():
            print("    %-16s %+8.2f" % (k, v))
    assert -1.0 < seen["ijk      S=3"] < 0.0, seen
    assert -2.0 < seen["diagonal S=7"] < -1.0, seen
    assert 0.0 < seen["3-4-5    S=25"] < 1.0, seen
    assert seen["i        k=1"] == 0.0, "a k=1 axis has NO residue at all"


# ── the in-tree anchor is ABSORBED, not duplicated ────────────────────────
def test_the_shipped_hc_inv_q61_anchor_is_reproduced_by_the_general_formula():
    """``_HC_INV_Q61`` is LIVE (``hypercomplex_dft`` uses it in the pure Q61 arm
    of ``hypercomplex_exp``), and the general axis formula must return exactly
    it — otherwise rc477 shipped a second spelling of a value the file already
    had, which is the duplication the one-op rule forbids."""
    for k, direction in ((1, [1]), (3, [1, 1, 1]), (7, [1] * 7)):
        got = _qalg._axis_q61(direction, k)
        assert set(got) == {H._HC_INV_Q61[k]}, (
            f"the general formula at S={k} gave {sorted(set(got))}, not the "
            f"shipped anchor {H._HC_INV_Q61[k]}")
        assert _word_is_nearest(H._HC_INV_Q61[k], 1, k), (
            f"the shipped anchor at k={k} is not the nearest word")


# ── the two spellings, and the rate that separates them ───────────────────
def test_the_reciprocal_spelling_misses_and_the_radicand_spelling_does_not(capsys):
    """The measurement that decides the whole release, over k = 2..400.

    ``1.0 / float(sqrt(float(k)))`` is a root, a reciprocal and a multiply;
    ``float(sqrt(Q(1, k)))`` puts the reciprocal INSIDE the radicand and rounds
    once. The first misses the correctly rounded value on a substantial
    fraction; the second on none."""
    miss_detour = sum(
        1 for k in range(2, 401)
        if not _double_is_cr(1.0 / float(R.sqrt(float(k))), 1, k))
    miss_exact = sum(
        1 for k in range(2, 401)
        if not _double_is_cr(float(R.sqrt(Q(1, k))), 1, k))
    with capsys.disabled():
        print("\n  1.0/float(sqrt(float(k))) misses CR on %d / 399" % miss_detour)
        print("  float(sqrt(Q(1, k)))      misses CR on %d / 399" % miss_exact)
    assert miss_exact == 0, (
        f"the one-rounding spelling missed the correctly rounded value on "
        f"{miss_exact} of 399 — the repair does not hold")
    assert miss_detour > 50, (
        f"the float detour missed on only {miss_detour} of 399, where rc476 "
        "measured 101 — either libm changed under us or this oracle has gone "
        "blind, and a control that cannot fail is not evidence")


# ── the ripple the axis change carries into the twiddle product ───────────
def test_the_twiddle_product_rate_is_stated_not_assumed(capsys):
    """``s * μᵢ`` — the PL-16..19 ripple, MEASURED rather than asserted.

    The axis components are correctly rounded now, but the product of the Q61
    sine with them is still one float multiply in the carrier the operand
    elected: the site does not change and its rate is not zero. Stating the
    number is the contract ("state the bound in units"); an unquantified
    "accurate to round-off" is exactly the wording this release withdraws
    elsewhere."""
    w, s = [0, 1, 1, 1, 0, 0, 0, 0], 3
    mu = _qalg._axis_float(w, s)
    miss = 0
    tot = 0
    seed = 20260918
    for i in range(2000):
        seed = (seed * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        theta = (seed % (1 << 52)) / float(1 << 52) * 6.0 - 3.0
        sin_t = float(R.sin(theta))
        for comp, wi in zip(mu[1:4], w[1:4]):
            tot += 1
            got = sin_t * comp
            exact = Q.from_float(sin_t) * Q(wi, 1) * R.sqrt(
                Q(1, s), precision=120)
            if got != float(exact):
                miss += 1
    with capsys.disabled():
        print("\n  s*mu[i] != the once-projected exact product on %d / %d"
              % (miss, tot))
    assert tot == 6000
    assert miss > 0, (
        "the product is exact on every draw, which would mean this row is "
        "measuring nothing — the site is a float multiply and its rate is the "
        "number the docstrings must state")
