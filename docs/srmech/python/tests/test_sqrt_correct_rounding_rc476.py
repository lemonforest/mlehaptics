"""0.9.0rc476 (`#T1188`) — √ is CORRECTLY ROUNDED, decided by EXACT INTEGERS.

THE DEFECT THIS GATE EXISTS FOR. Through rc475 the Class-N float route read
``x = M·2^e`` straight out of the IEEE fields and computed ``isqrt(M << 54)``.
``M`` is the raw mantissa, so for a SUBNORMAL ``x`` it is far below ``2**52`` —
``M = 1`` gives ``isqrt(1 << 54) = 2**27``, a **28-bit** root where 53 are
needed — and the root's width therefore tracked the operand's magnitude instead
of being fixed. Measured at rc475 through :func:`srmech.math.rational.sqrt`
itself with native dispatch live:

* **480 / 1956** non-square integers in 2..2000 served a double that is not the
  correctly rounded root, every one of them one ulp LOW;
* **4032 / 4096** subnormal mantissas did, the worst by **16,609,076 ulps**;
* the narrowest root over that row set was **28 bits**;
* and the old file banner's evidence was *"validated vs libm to machine epsilon
  (rel err <= 2.3e-16)"* — a **libm oracle**, which this library does not use,
  and a RELATIVE-ERROR bound, which cannot see a 1-ulp misround at all. That is
  why it passed for the whole life of the defect.

So this gate uses neither libm nor ``math`` nor ``numpy`` nor ``fractions``.
Every verdict below is an exact integer comparison, and the integers are
printable, so any row can be re-derived by hand.

TWO INDEPENDENT INSTRUMENTS, DELIBERATELY. :func:`_cr_bits` DERIVES the
correctly rounded double (integer ``isqrt`` on a scaled radicand, then one
midpoint comparison). :func:`_certify` CHECKS a candidate against the midpoint
inequalities WITHOUT using the derivation. A derivation bug has to survive
both, and :func:`test_the_oracle_can_fail` proves the certificate rejects the
two neighbours of a known answer rather than accepting whatever it is handed.

WHAT THIS DOES NOT PROVE. Correct rounding, not that the returned ``Q`` is the
BEST rational of its width, and nothing about ``precision=P`` beyond its
floored-grid promise (which :func:`test_the_precision_grid_is_untouched`
pins separately). The seeded patterns are a SAMPLE; only the integers 2..2000,
the subnormal mantissas 1..4096, the boundary rows and the rational grid are
exhaustive over their declared ranges. There is no sweep of the 2**63 positive
finite doubles and there will not be one.
"""
from __future__ import annotations

import struct

import pytest

from srmech import _native
from srmech.math import rational as R
from srmech.math.q import Q

_MANT = 1 << 52
_MANT_HI = 1 << 53
_SEED = 20260918          # the seed IS the provenance of the sampled rows


# ──────────────────────────────────────────────────────────────────────
# The instrument: integers only.
# ──────────────────────────────────────────────────────────────────────
def _isqrt(n: int) -> int:
    """``floor(√n)`` by integer Newton. The stdlib is deliberately NOT borrowed
    here: this module's claim is that every step is arithmetic a reader can
    re-derive, and importing the answer is not re-derivable."""
    assert n >= 0
    if n < 2:
        return n
    r = 1 << ((n.bit_length() + 1) // 2)
    while True:
        nxt = (r + n // r) >> 1
        if nxt >= r:
            break
        r = nxt
    assert r * r <= n < (r + 1) * (r + 1)
    return r


def _bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def _from_bits(b: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def _pack(m: int, f: int) -> int:
    assert _MANT <= m < _MANT_HI
    biased = f + 52 + 1023
    assert 1 <= biased <= 2046, f"exponent out of the normal range: {biased}"
    return (biased << 52) | (m - _MANT)


def _unpack(b: int) -> "tuple[int, int]":
    biased = (b >> 52) & 0x7FF
    assert 1 <= biased <= 2046, "positive NORMAL doubles only"
    return (b & (_MANT - 1)) | _MANT, biased - 1023 - 52


def _scaled_floor_root(p: int, q: int, t: int) -> int:
    """``floor(√(p/q) · 2**t)`` exactly, for ANY sign of ``t``.

    ``floor(√(floor(z))) == floor(√z)`` for real ``z >= 0``, so flooring the
    scaled radicand first costs nothing. ``t`` must be allowed to go NEGATIVE:
    the max double and ``hypot(2**500, 2**500)`` both need it, and an earlier
    draft of this helper asserted ``t >= 0`` and aborted on exactly those rows.
    """
    assert p > 0 and q > 0
    if t >= 0:
        return _isqrt((p << (2 * t)) // q)
    return _isqrt(p // (q << (-2 * t)))


def _cmp_root_scaled(p: int, q: int, n: int, t: int) -> int:
    """Sign of ``√(p/q) · 2**t − n/2``, as an exact integer comparison.

    ``√(p/q)·2^t ⋚ n/2`` ⟺ ``p · 2^(2t+2) ⋚ n² · q``, both sides shifted into
    integers whichever way the exponent points.
    """
    e = 2 * t + 2
    lhs, rhs = (p << e, n * n * q) if e >= 0 else (p, (n * n * q) << (-e))
    return (lhs > rhs) - (lhs < rhs)


def _cr_bits(p: int, q: int) -> int:
    """Bit pattern of the correctly rounded binary64 nearest ``√(p/q)``.

    Round-to-nearest, ties-to-even, decided by ONE exact integer comparison of
    the scaled root against the midpoint ``(2m+1)/2``.
    """
    assert p > 0 and q > 0
    t = 53 - ((p.bit_length() - q.bit_length()) // 2)
    v = _scaled_floor_root(p, q, t)
    while v.bit_length() < 54:
        t += 1
        v = _scaled_floor_root(p, q, t)
    while v.bit_length() > 54:
        t -= 1
        v = _scaled_floor_root(p, q, t)
    m0 = v >> 1
    order = _cmp_root_scaled(p, q, 2 * m0 + 1, t - 1)
    m = m0 + 1 if order > 0 else (m0 if order < 0 else
                                  (m0 if (m0 & 1) == 0 else m0 + 1))
    f = -(t - 1)
    if m == _MANT_HI:
        m >>= 1
        f += 1
    return _pack(m, f)


def _certify(m: int, f: int, p: int, q: int) -> bool:
    """Is ``m · 2**f`` the correctly rounded double of ``√(p/q)``?

    From the midpoint inequalities ALONE, never from :func:`_cr_bits`::

        lo · 2**(f-1)  <  √(p/q)  <  (2m+1) · 2**(f-1)

    with ``lo = (4m-1)/2`` at the binade floor, where the double below is half
    as widely spaced. An exact midpoint is accepted only when ``m`` is even.
    """
    assert _MANT <= m < _MANT_HI and p > 0 and q > 0
    hi_num = (2 * m + 1) ** 2 * q
    e_hi = 2 * f - 2
    hi_l, hi_r = (p, hi_num << e_hi) if e_hi >= 0 else (p << (-e_hi), hi_num)
    if hi_l > hi_r or (hi_l == hi_r and (m & 1) != 0):
        return False
    if m == _MANT:
        lo_num, e_lo = (4 * m - 1) ** 2 * q, 2 * f - 4
    else:
        lo_num, e_lo = (2 * m - 1) ** 2 * q, 2 * f - 2
    lo_l, lo_r = (p, lo_num << e_lo) if e_lo >= 0 else (p << (-e_lo), lo_num)
    if lo_l < lo_r or (lo_l == lo_r and (m & 1) != 0):
        return False
    return True


def _lcg(seed: int, count: int):
    """A declared, reproducible bit-pattern sample. Not ``random`` — the seed is
    the provenance, and a stdlib generator's stream is not part of this file."""
    state = seed & ((1 << 64) - 1)
    for _ in range(count):
        state = (state * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        yield state


# ──────────────────────────────────────────────────────────────────────
# The rows.
# ──────────────────────────────────────────────────────────────────────
def _float_rows() -> "list[tuple[str, float]]":
    """Every positive finite double this gate roots, with a label."""
    rows: "list[tuple[str, float]]" = []
    rows += [(f"int:{x}", float(x)) for x in range(2, 2001)]
    rows += [(f"sub:{m}", _from_bits(m)) for m in range(1, 4097)]       # EVERY one
    for k in range(1, 52):
        for d in (-1, 0, 1):
            mant = (1 << k) + d
            if 1 <= mant < _MANT:
                rows.append((f"subclass:2^{k}{d:+d}", _from_bits(mant)))
    rows.append(("max_subnormal", _from_bits(_MANT - 1)))
    rows.append(("min_normal", _from_bits(_MANT)))
    rows.append(("max_double", _from_bits((2046 << 52) | (_MANT - 1))))
    rows += [("one", 1.0), ("two", 2.0), ("four", 4.0), ("threequarter", 0.75)]
    for pat in _lcg(_SEED, 20000):
        raw = (pat >> 52) & 0x7FF
        if raw == 0x7FF:                 # Inf / NaN have no rational root
            continue
        val = _from_bits(pat & ((1 << 63) - 1))
        if val > 0.0:
            rows.append((f"seed:{pat:#018x}", val))
    return rows


def _rational_rows() -> "list[tuple[str, int, int]]":
    """Exact rational radicands the float carrier cannot express."""
    rows = [(f"recip:{k}", 1, k) for k in range(2, 2001)]
    rows.append(("three_quarters", 3, 4))
    for a in range(1, 60):
        for b in range(1, 60):
            rows.append((f"grid:{a}/{b}", a, b))
    rows.append(("near_one", (1 << 52) - 1, (1 << 52) - 3))
    rows.append(("tiny", 1, (1 << 62) - 1))
    rows.append(("huge", (1 << 62) - 1, 1))
    return rows


# ──────────────────────────────────────────────────────────────────────
# 1. The instrument must be able to fail.
# ──────────────────────────────────────────────────────────────────────
def test_the_oracle_can_fail() -> None:
    """The certificate REJECTS both neighbours of a known answer.

    Without this, every assertion below is a tautology: a predicate that
    accepts whatever it is handed reports a clean tree and a broken one alike.
    """
    b = _cr_bits(2, 1)
    assert b == 0x3FF6A09E667F3BCD, f"CR(√2) derived as {b:#018x}"
    m, f = _unpack(b)
    assert _certify(m, f, 2, 1), "the certificate rejected the true CR(√2)"
    for nb, side in ((b - 1, "below"), (b + 1, "above")):
        mm, ff = _unpack(nb)
        assert not _certify(mm, ff, 2, 1), (
            f"the certificate ACCEPTED the neighbour {side} CR(√2) "
            f"({nb:#018x}) — it is not deciding anything"
        )
    assert _cr_bits(4, 1) == _bits(2.0)          # exact squares stay exact
    assert _cr_bits(1, 4) == _bits(0.5)
    assert _cr_bits(9, 16) == _bits(0.75)


def test_the_shipped_defect_would_still_be_caught() -> None:
    """The rc475 recipe, run here, must FAIL the certificate.

    A gate that cannot reproduce the defect it was written for is a gate that
    would pass on the defective tree. This reconstructs the OLD float route —
    ``isqrt(M << 54)`` with no normalise — and shows the certificate rejecting
    it on the very rows the rc475 measurement named.
    """
    bad = 0
    for x in (2, 8, 10, 17, 19):                 # the first five rc475 rows
        mant, e = _unpack(_bits(float(x)))
        if e & 1:
            mant <<= 1
            e -= 1
        root = _isqrt(mant << 54)
        got = float(root) * float(2.0) ** (e // 2 - 27)
        if _bits(got) != _cr_bits(x, 1):
            bad += 1
    assert bad == 5, (
        f"the pre-rc476 recipe misrounded {bad} of 5 known-bad rows, not 5 — "
        "the reconstruction no longer reproduces the defect this gate is for"
    )


# ──────────────────────────────────────────────────────────────────────
# 2. The shipped routes.
# ──────────────────────────────────────────────────────────────────────
def test_the_float_route_is_correctly_rounded() -> None:
    """Every row of :func:`_float_rows`, through ``sqrt()`` itself.

    Through ``sqrt()`` and not through the pure helper on purpose:
    ``rational.py`` dispatches to ``_native.sqrt_q61_c`` BEFORE any Python root
    code whenever a library is loaded, which is the shipped configuration, so a
    measurement that bypasses the entry point measures a different route from
    the one that ships.
    """
    rows = _float_rows()
    assert len(rows) > 20000, f"the row set collapsed to {len(rows)}"
    bad: "list[str]" = []
    for label, xv in rows:
        p, q = xv.as_integer_ratio()
        got = _bits(float(R.sqrt(xv)))
        want = _cr_bits(p, q)
        if got != want:
            m, f = _unpack(want)
            assert _certify(m, f, p, q), f"the certificate disowns its own CR at {label}"
            if len(bad) < 12:
                bad.append(f"{label}: got {got:#018x} want {want:#018x} "
                           f"({got - want:+d} ulps)")
    assert not bad, f"{len(bad)}+ rows misround: " + "; ".join(bad)


def test_the_exact_route_is_correctly_rounded() -> None:
    """``int`` and ``Q`` operands — the rc474 exact entry, plus every rational
    radicand the float carrier cannot hold."""
    bad: "list[str]" = []
    for x in range(2, 2001):
        got = _bits(float(R.sqrt(x)))
        want = _cr_bits(x, 1)
        if got != want and len(bad) < 12:
            bad.append(f"int {x}: {got:#018x} != {want:#018x}")
    for label, p, q in _rational_rows():
        got = _bits(float(R.sqrt(Q(p, q))))
        want = _cr_bits(p, q)
        if got != want and len(bad) < 12:
            bad.append(f"{label}: {got:#018x} != {want:#018x}")
    assert not bad, "; ".join(bad)


def test_hypot_is_correctly_rounded() -> None:
    """``hypot`` forms the sum of squares EXACTLY and then takes the exact
    route, so its ``float()`` is the CR double of ``√(a²+b²)``."""
    pairs = [(1.0, 1.0), (3.0, 4.0), (1e-17, 0.0), (1e-300, 1e-300),
             (5.0, 12.0), (0.1, 0.2), (2.0 ** 500, 2.0 ** 500),
             (1.0, 1e-200), (7.0, 24.0), (1.5, 2.5)]
    for a, b in pairs:
        an, ad = a.as_integer_ratio()
        bn, bd = b.as_integer_ratio()
        p = an * an * bd * bd + bn * bn * ad * ad
        q = ad * ad * bd * bd
        if p == 0:
            continue
        got = _bits(float(R.hypot(a, b)))
        want = _cr_bits(p, q)
        assert got == want, (
            f"hypot({a!r}, {b!r}): {got:#018x} != CR {want:#018x}"
        )
    assert R.hypot(3.0, 4.0) == Q(5, 1)          # the exact row stays exact


def test_the_root_is_never_narrower_than_54_bits() -> None:
    """The NORMALISE step, stated as the quantity that WAS the defect.

    ``_sqrt_core``'s contract is ``root >= 2**53``. At rc475 the minimum over
    this row set was **28** bits. It is 54 here — 54 and not 55, because a
    PERFECT SQUARE takes the exact branch and its root can sit at the bottom of
    the window (measured: 9, 36, 49, 144, 169 are the first five such rows).
    """
    widths: "set[int]" = set()
    for _label, xv in _float_rows()[:6500]:
        mant, e = _unpack(_bits(xv)) if xv >= _from_bits(_MANT) else (
            _bits(xv), -1074)
        root, _p = R._sqrt_core(mant, 1, e)
        widths.add(int(root).bit_length())
    assert widths, "no rows measured"
    assert min(widths) >= 54, (
        f"a root came back {min(widths)} bits wide; the core promises >= 54 "
        f"(the full set seen: {sorted(widths)})"
    )
    assert max(widths) <= 56, f"root wider than the window: {sorted(widths)}"


def test_the_sticky_bit_is_odd_exactly_when_the_radicand_is_not_a_square() -> None:
    """What makes the midpoint decidable, asserted as a property of the pair.

    An ODD root cannot be a rounding midpoint at ``k >= 2`` discarded bits,
    because a midpoint's low bits are ``2**(k-1)``, whose low bit is 0. The
    exact branch must stay exact or ``√4`` would answer ``Q(5, 2)``.
    """
    for x in range(2, 400):
        root, p = R._sqrt_core(x, 1, 0)
        square = _isqrt(x) ** 2 == x
        assert p <= 0, f"√{x} scaled UP: p = {p}"
        if square:
            assert root * root == x << (-2 * p), (
                f"√{x} is exact but the core's root {root} at 2^{p} is not it"
            )
        else:
            assert root & 1, (
                f"√{x} is irrational, so the core root must carry the STICKY "
                f"low bit; got the even {root}"
            )
            # and the sticky pair must still BRACKET the true root
            assert (root - 1) ** 2 < x << (-2 * p) < (root + 1) ** 2, (
                f"√{x}: the sticky pair ({root}, {p}) does not bracket"
            )
    assert R.sqrt(4.0) == Q(2, 1)
    assert R.sqrt(0.25) == Q(1, 2)
    assert R.sqrt(2 ** 100) == Q(2 ** 50, 1)


# ──────────────────────────────────────────────────────────────────────
# 3. Can-fail controls on the FIX: each mutation must misround.
# ──────────────────────────────────────────────────────────────────────
def _mutated_core(num: int, den: int, e0: int, *, bump=0, sticky=True,
                  normalise=True):
    """``_sqrt_core`` with one property removed — the controls' instrument."""
    if normalise:
        s = 108 - (num.bit_length() - den.bit_length())
    else:
        s = 54                                    # the rc475 fixed shift
    if (e0 - s) & 1:
        s -= 1
    if s >= 0:
        rad, rem = divmod(num << s, den)
    else:
        rad, rem = divmod(num, den << (-s))
    root = _isqrt(rad)
    if rem == 0 and root * root == rad:
        return root + bump, (e0 - s) // 2
    if not sticky:
        return root + bump, (e0 - s) // 2
    return 2 * root + 1 + bump, (e0 - s) // 2 - 1


def _project(root: int, p: int) -> int:
    """The shipped integer projection, so a mutation is compared like for like."""
    bl = root.bit_length()
    k = bl - 53
    if k <= 0:
        return _bits(float(root) * 2.0 ** p)
    m = root >> k
    low = root & ((1 << k) - 1)
    half = 1 << (k - 1)
    if low > half or (low == half and (m & 1)):
        m += 1
    if m >> 53:
        m >>= 1
        p += 1
    return _pack(m, p + k)


@pytest.mark.parametrize(
    "name,kw,floor",
    [
        ("root+1", {"bump": 1}, 50),
        ("root-1", {"bump": -1}, 50),
        ("no sticky bit", {"sticky": False}, 200),
        ("no normalise", {"normalise": False}, 200),
    ],
)
def test_each_mutation_misrounds(name, kw, floor) -> None:
    """Every property the fix adds must be LOAD-BEARING, and that is measured
    by removing it and counting the misrounds it lets back in.

    ``no normalise`` is the one that matters most: it shows the sticky bit
    ALONE does not close the defect, which is why both halves shipped.
    """
    rows = _float_rows()[:6200]
    bad = 0
    for _label, xv in rows:
        p, q = xv.as_integer_ratio()
        mant, e = (_bits(xv), -1074) if xv < _from_bits(_MANT) else _unpack(_bits(xv))
        try:
            root, pp = _mutated_core(mant, 1, e, **kw)
            if root <= 0:
                bad += 1
                continue
            got = _project(root, pp)
        except (AssertionError, OverflowError, ValueError):
            bad += 1
            continue
        if got != _cr_bits(p, q):
            bad += 1
    assert bad >= floor, (
        f"removing '{name}' only broke {bad} of {len(rows)} rows (floor "
        f"{floor}) — either the property is not load-bearing or the control "
        f"is not reaching the code"
    )


def test_the_certificate_rejects_a_neighbour_on_every_shape() -> None:
    """The can-fail control run over the row shapes, not just over √2."""
    for p, q in ((2, 1), (3, 1), (1, 2), (1, 3), (3, 4), (8, 1), (1, 1 << 1074)):
        b = _cr_bits(p, q)
        m, f = _unpack(b)
        assert _certify(m, f, p, q)
        for nb in (b - 1, b + 1):
            mm, ff = _unpack(nb)
            assert not _certify(mm, ff, p, q), (
                f"certificate accepted a neighbour of CR(√({p}/{q}))"
            )


# ──────────────────────────────────────────────────────────────────────
# 4. What must NOT have moved.
# ──────────────────────────────────────────────────────────────────────
def test_the_precision_grid_is_untouched() -> None:
    """``precision=P`` is the literal ABSOLUTE floored grid a caller asked for.

    It is NOT correctly rounded and is not meant to be: the contract is
    ``Q(floor(√x · 2**P), 2**P)``, error in ``[0, 2**-P)``, always LOW. rc476
    changes the ``precision=None`` routes and leaves this one alone.
    """
    for x, P in ((2.0, 200), (2.0, 64), (3.0, 100), (0.5, 53)):
        got = R.sqrt(x, precision=P)
        n, d = got.as_pair()
        p, q = x.as_integer_ratio()
        want = _isqrt((p << (2 * P)) // q)
        # the Q reduces, so compare the VALUE against the floored grid point
        assert n * (1 << P) == want * d, (
            f"sqrt({x}, precision={P}) is not the floored grid point"
        )
        assert (n * n) * q <= p * (d * d), "the grid point must never exceed √x"


def test_the_exact_operand_stays_observably_exact() -> None:
    """rc474's witness SURVIVES: the exact route still carries more than the
    float route, which is why the two entries did NOT collapse onto one core.

    Routing the exact entry through ``_sqrt_core`` as well is also correctly
    rounded, and it makes these two equal — measured. That would have retired
    a shipped property to save one rule, so the exact route keeps
    ``_sqrt_relative_k``'s RELATIVE grid and gains only the sticky bit.
    """
    assert R.sqrt(2 ** 53 + 1) != R.sqrt(float(2 ** 53 + 1))
    exact_n, exact_d = R.sqrt(2 ** 53 + 1).as_pair()
    float_n, float_d = R.sqrt(float(2 ** 53 + 1)).as_pair()
    assert exact_d > float_d, (
        "the exact route must root on a FINER grid than the float route; "
        f"got 1/{exact_d} against 1/{float_d}"
    )
    # and both project to the same, correct, double
    assert _bits(float(R.sqrt(2 ** 53 + 1))) == _cr_bits(2 ** 53 + 1, 1)


def test_the_domain_refusals_are_unmoved() -> None:
    """The Class-K pin-slot at zero, on both carriers."""
    with pytest.raises(ValueError):
        R.sqrt(-1.0)
    with pytest.raises(ValueError):
        R.sqrt(-1)
    with pytest.raises(ValueError):
        R.sqrt(Q(-1, 3))
    with pytest.raises(ValueError):
        R.sqrt(float("nan"))
    with pytest.raises(ValueError):
        R.sqrt(float("inf"))
    assert R.sqrt(0.0) == Q(0, 1)
    assert R.sqrt(0) == Q(0, 1)


# ──────────────────────────────────────────────────────────────────────
# 5. The constants the 19 site rewrites serve.
# ──────────────────────────────────────────────────────────────────────
def test_the_rewritten_sites_serve_correctly_rounded_constants() -> None:
    """The reciprocal was the SECOND rounding, and fixing the root alone made
    it visible rather than fixing it.

    Measured: with the repaired root but the old ``1.0 / float(sqrt(2.0))``
    spelling, ``bell``'s ``inv_sqrt2`` went from ``0x3ff6a09e667f3bcd`` (right,
    by the two errors cancelling) to ``0x…bcc`` (wrong). Each site now puts the
    reciprocal INSIDE the exact radicand, so there is one rounding.
    """
    from srmech.physics.qm import bell, gauge

    lam8 = gauge.su3_gell_mann_matrices()[7]
    assert _bits(lam8[0, 0].real) == _cr_bits(1, 3), "λ⁸'s 1/√3 is not CR"
    assert _bits(-lam8[2, 2].real) == _cr_bits(4, 3), "λ⁸'s 2/√3 is not CR"
    f = gauge.su3_structure_constants()
    assert _bits(f[3][4][7]) == _cr_bits(3, 4), "f^458 = √3/2 is not CR"
    assert _bits(f[5][6][7]) == _cr_bits(3, 4), "f^678 = √3/2 is not CR"
    assert _bits(bell.TSIRELSON_BOUND) == _cr_bits(8, 1), "2√2 is not CR"
    # CHSH's ``inv_sqrt2`` is a local, so it is asserted where it LANDS: each
    # non-zero entry of the operator is ``2 · inv_sqrt2``, and doubling is
    # exact, so the entry is the CR √2 iff the scale was the CR 1/√2. At rc475
    # this read 0x3ff6a09e667f3bcd from a scale that was wrong the other way;
    # repairing the root alone would have moved it to 0x…bcc, which is what
    # makes the SITE rewrite, not just the primitive, load-bearing here.
    H = bell.chsh_operator()
    assert _bits(H[0, 0].real) == _cr_bits(2, 1), "CHSH's 2·(1/√2) is not CR √2"
    assert _bits(-H[1, 1].real) == _cr_bits(2, 1)


def test_the_inverse_root_helper_is_correctly_rounded() -> None:
    """``_finv_sqrt`` — the D^(−1/2) scale the three Laplacian sites share."""
    from srmech.math.laplacian import _finv_sqrt

    for d in (1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 0.5, 1.5, 1e-8, 1e8,
              1234.5678, 2.0 ** -1000, 2.0 ** 900):
        p, q = d.as_integer_ratio()
        assert _bits(_finv_sqrt(d)) == _cr_bits(q, p), (
            f"_finv_sqrt({d!r}) is not the CR 1/√x"
        )
    assert _finv_sqrt(float("inf")) == 0.0
    assert _finv_sqrt(float("nan")) != _finv_sqrt(float("nan"))
    with pytest.raises(ValueError):
        _finv_sqrt(-1.0)
    with pytest.raises(ZeroDivisionError):
        _finv_sqrt(0.0)


def test_square_qam_still_raises_on_every_non_square_M() -> None:
    """CF-031: the perfect-square test became EXACT and must keep refusing.

    An integer question routed through the continuous carrier and back is what
    was there before — ``int(round(float(sqrt(float(M)))))`` — and its answer
    depended on the root's last bit and on ``round``'s banker's rule.
    """
    from srmech.signal_processing.closed_form_ops import psk_qam

    for M in (4, 16, 64, 256, 1024, 4096, 1 << 20):
        got = psk_qam.op(list(range(4)), modulation="qam", M=M, demodulate=False)
        assert len(got) == 4
    for M in (2, 3, 5, 8, 12, 32, 1023, (1 << 20) - 1):
        with pytest.raises(ValueError):
            psk_qam.op([0], modulation="qam", M=M, demodulate=False)


# ──────────────────────────────────────────────────────────────────────
# 6. The two projections must agree on the PAIR, not merely on the double.
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.skipif(
    not _native.has_native_trans_q61(),
    reason="no native library loaded; this asserts C-vs-Python pair parity",
)
def test_the_c_and_python_cores_agree_bit_for_bit() -> None:
    """``srmech_sqrt_q61`` and ``_sqrt_core`` must return the SAME (root, p).

    The doubles agreeing is weaker: two different pairs can project to the same
    double. This is the claim the Python glue depends on, since it rebuilds the
    exact ``Q`` from the pair the C side hands back.
    """
    rows = _float_rows()[:6500]
    bad: "list[str]" = []
    for label, xv in rows:
        mant, e = (_bits(xv), -1074) if xv < _from_bits(_MANT) else _unpack(_bits(xv))
        py_root, py_p = R._sqrt_core(mant, 1, e)
        c_root, c_p = _native.sqrt_q61_c(xv)
        if (int(c_root), int(c_p)) != (py_root, py_p) and len(bad) < 10:
            bad.append(f"{label}: C ({c_root}, {c_p}) != PY ({py_root}, {py_p})")
    assert not bad, "; ".join(bad)
