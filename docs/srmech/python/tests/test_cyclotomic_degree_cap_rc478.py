"""The exact-field DEGREE cap — 0.9.0rc478, `#T1188`.

rc478 replaced ``MAX_CYCLOTOMIC_INDEX = 256`` (a bound on the cyclotomic
INDEX ``M``) with ``MAX_CYCLOTOMIC_DEGREE = 888`` (a bound on
``φ(M) = deg Φ_M``, the size of the object the op actually builds), and
memoised ``_inv_sqrt_k`` in the same commit.

**What each gate here does NOT prove is stated in its own docstring.** None of
them asserts a millisecond: the machine band on one unchanged configuration is
1.54×, so a ms threshold would be a gate that fails on a loaded CI cell. The
measured costs live in the CHANGELOG as recorded numbers.

The admission SWEEP itself (``G-CAP-SIEVE``) is not here — it is the widened
``test_exact_axis_summand_rc469.py`` parametrisation, which now walks
``("diagonal", 7)`` as well as the two cheap axes.
"""
from __future__ import annotations

import pytest

from srmech.cascade import (
    hypercomplex_exp,
    odft_resolve_mu,
    odft_summand,
    qdft_summand,
)
from srmech.math import qalg as _qalg
from srmech.math.cyclic import gcd
from srmech.math.poly import cyclotomic_polynomial
from srmech.math.q import Q
from srmech.math.qalg import (
    MAX_CYCLOTOMIC_DEGREE,
    Qalg,
    cos_sin_2pi_k_over_n,
    _cyclotomic_degree as cyclotomic_degree,
)
from srmech.physics.qm.octonion import octonion_twiddle
from srmech.physics.qm.quaternion import quaternion_twiddle

#: ``base`` per axis width, as :data:`srmech.math.qalg._AXIS_SCALE_INDEX`.
AXIS_BASE = {1: 4, 3: 12, 7: 28}

#: The rc477 predicate, kept here so the widening gate can compare against the
#: rule that actually shipped rather than against a remembered one.
OLD_INDEX_CAP = 256


def _index(n: int, axis_k: int) -> int:
    return _qalg._turn_field_index(n, axis_k)


def _admits(n: int, axis_k: int, bound: int = MAX_CYCLOTOMIC_DEGREE) -> bool:
    return cyclotomic_degree(_index(n, axis_k)) <= bound


# ── G-CAP-DEGREE-ORACLE ─────────────────────────────────────────────────────
def _totient_trialdiv(m: int) -> int:
    """An INDEPENDENT totient — trial division over plain ints, no srmech."""
    result, rest, p = m, m, 2
    while p * p <= rest:
        if rest % p == 0:
            while rest % p == 0:
                rest //= p
            result -= result // p
        p += 1
    if rest > 1:
        result -= result // rest
    return result


def test_G_CAP_DEGREE_ORACLE_the_new_helper_is_the_field_degree() -> None:
    """:func:`cyclotomic_degree` IS ``deg Φ_M``, on two independent oracles.

    The whole criterion rests on this one function, and it is the one function
    in the change that never builds the object it measures — so it is checked
    against the tree's own ``Φ_M`` (which does build it) AND against a
    trial-division totient written here from scratch.

    Does NOT prove: that ``factor`` is correct for indices beyond the scanned
    range, nor anything about ``Φ_M``'s COEFFICIENTS — only its degree.
    """
    for m in range(1, 601):
        assert cyclotomic_degree(m) == cyclotomic_polynomial(m)["degree"], m
    for m in range(1, 5001):
        assert cyclotomic_degree(m) == _totient_trialdiv(m), m
    # the named indices the cap is derived from
    assert cyclotomic_degree(2676) == 888          # Exeligmos / Saros on 1/√3
    assert cyclotomic_degree(18732) == 5328        # Exeligmos on 1/√7
    assert cyclotomic_degree(1) == 1               # Φ_1 = x − 1
    assert cyclotomic_degree(2) == 1
    # NEGATIVE CONTROLS — the instrument can return otherwise
    assert cyclotomic_degree(1004) != 501          # it is 500
    shifted = sum(1 for m in range(1, 199)
                  if cyclotomic_degree(m) == cyclotomic_polynomial(m + 1)["degree"])
    assert shifted == 6, shifted                   # 192 of 198 DISAGREE
    with pytest.raises(TypeError):
        cyclotomic_degree(True)
    with pytest.raises(TypeError):
        cyclotomic_degree(4.0)
    with pytest.raises(ValueError):
        cyclotomic_degree(0)


# ── G-CAP-BOUNDARY ──────────────────────────────────────────────────────────
#: ``(label, call, index, degree)`` — the REFUSE side of each pair.
_REFUSALS = [
    ("k=1 quaternion 'i'",
     lambda: quaternion_twiddle(1, 1, 449, mu="i", exact=True), 1796, 896),
    ("k=3 quaternion 'ijk'",
     lambda: quaternion_twiddle(1, 1, 227, mu="ijk", exact=True), 2724, 904),
    ("k=7 octonion 'diagonal'",
     lambda: octonion_twiddle(1, 1, 79, mu="diagonal", exact=True), 2212, 936),
    ("cos_sin_2pi_k_over_n", lambda: cos_sin_2pi_k_over_n(449), 1796, 896),
    ("hypercomplex_exp turn=",
     lambda: hypercomplex_exp(k_axes=7, turn=(1, 79)), 2212, 936),
    ("qdft_summand",
     lambda: qdft_summand([[1, 0, 0, 0]] * 2, 1, 1, 449, True, -1,
                          [0, 1, 0, 0]), 1796, 896),
    ("odft_summand",
     lambda: odft_summand([[0] * 8] * 2, 1, 1, 79, "left", "left_associated",
                          -1, odft_resolve_mu("diagonal"),
                          odft_resolve_mu("diagonal")), 2212, 936),
]


@pytest.mark.parametrize("label,call,index,degree",
                         _REFUSALS, ids=[r[0] for r in _REFUSALS])
def test_G_CAP_BOUNDARY_every_refusal_names_its_DEGREE(label, call, index,
                                                       degree) -> None:
    """Six guard sites, and each message must name the computed DEGREE.

    ⚠️ This is the row a mechanical rename would have passed while saying
    nothing true. Renaming ``MAX_CYCLOTOMIC_INDEX={…}`` to
    ``MAX_CYCLOTOMIC_DEGREE={…}`` at the five twiddle sites yields *"builds
    Q(zeta_2212) … above the measured MAX_CYCLOTOMIC_DEGREE=888 cap"* — in
    which **the degree 936 never appears**, so the message names the bound and
    not the thing that exceeded it. Each guard therefore computes the degree
    and interpolates it, and this row reads it back out of the message.

    Does NOT prove: that the boundary is in the RIGHT place — only that it is
    where the constant says, and that the refusal is legible.
    """
    assert cyclotomic_degree(index) == degree
    assert degree > MAX_CYCLOTOMIC_DEGREE
    with pytest.raises(ValueError) as caught:
        call()
    msg = str(caught.value)
    assert f"degree {degree}" in msg, msg
    assert str(index) in msg, msg
    assert "MAX_CYCLOTOMIC_DEGREE" in msg, msg


@pytest.mark.parametrize("axis_k,below,above,at_refusal", [
    (1, 448, 450, 449),
    (3, 226, 228, 227),
    (7, 78, 80, 79),
])
def test_G_CAP_BOUNDARY_is_two_sided_on_every_axis(axis_k, below, above,
                                                   at_refusal) -> None:
    """The refusal is REACHABLE and has an admitted neighbour on BOTH sides.

    That second side is what only a DEGREE criterion can show: under the rc477
    index rule the admitted set was an interval in ``M``, so "one above the
    last accepted" was the whole story. Here ``n`` ABOVE a refusal is admitted
    again, on every axis — the sieve, executed rather than asserted.

    Does NOT prove anything about ``n > 128`` on the diagonal axis, nor that
    the refusals between ``below`` and ``above`` are the only ones.
    """
    assert _admits(below, axis_k)
    assert not _admits(at_refusal, axis_k)
    assert _admits(above, axis_k)
    assert below < at_refusal < above
    # and the degrees invert, which is the whole point
    assert (cyclotomic_degree(_index(above, axis_k))
            < cyclotomic_degree(_index(at_refusal, axis_k)))


def test_G_CAP_BOUNDARY_a_huge_n_refuses_WITHOUT_factoring() -> None:
    """The cheap-refusal path, and the regression it repairs.

    Moving the criterion from the index to the DEGREE means the guard must
    SIZE the field before refusing it, and sizing means factoring —
    ``srmech.math.primes.factor`` is trial division, so the refusal cost grew
    as ``√n``. MEASURED on this tree before the repair:
    ``cos_sin_2pi_k_over_n`` refused ``n = 10¹¹`` in 55 ms, ``n = 10¹⁵`` in
    2.36 s and ``n = 2⁶² − 57`` in **211.8 s**, where rc477's index comparison
    refused all three in microseconds. The ANSWERS were never wrong; what
    regressed is how long a refusal takes, and a three-minute refusal on a
    public op is a defect whether or not anyone passes that ``n``.

    ``φ(M) ≥ √(M/2)`` for every ``M ≥ 1``, so ``φ(M) ≤ P`` forces
    ``M ≤ 2P²`` and any index above that is refused with no factorisation at
    all. This row asserts the two things that make it safe: the refusal still
    happens, and the shortcut **cannot change a verdict**.

    Does NOT assert a time. It asserts the ARITHMETIC that makes the shortcut
    sound; the milliseconds are recorded in the CHANGELOG.
    """
    bound = _qalg._DEGREE_CERTAIN_INDEX_MAX
    assert bound == 2 * MAX_CYCLOTOMIC_DEGREE ** 2 == 1_577_088

    # (1) the inequality, verified DIRECTLY over the whole shortcut range
    # rather than cited: 2*phi(M)^2 >= M, in integers, no float and no sqrt.
    for m in range(1, 200_001):
        assert 2 * cyclotomic_degree(m) ** 2 >= m, m
    for m in (bound, bound - 1, bound + 1, 510_510, 9_699_690):
        assert 2 * cyclotomic_degree(m) ** 2 >= m, m

    # (2) no ADMITTED index comes anywhere near the shortcut, so it cannot
    # refuse something the degree rule would admit. 3990 is 395x below it.
    admitted_max = max(m for m in range(1, 100_001)
                       if cyclotomic_degree(m) <= MAX_CYCLOTOMIC_DEGREE)
    assert admitted_max == 3990
    assert admitted_max * 395 < bound

    # (3) the shortcut fires, says so, and does NOT name a degree it did not
    # compute — the honest half of the two message shapes.
    phrase = _qalg._field_too_big(bound + 1)
    assert phrase is not None
    assert "without factoring" in phrase
    assert "of a degree above" in phrase
    # ...while just below it the exact degree IS named
    near = _qalg._field_too_big(3991)
    assert near is not None and "of degree " in near
    assert "without factoring" not in near
    # ...and an admitted field returns None on both sides of the helper
    assert _qalg._field_too_big(3990) is None
    assert _qalg._field_too_big(2676) is None

    # (4) end to end, on the two routes that can actually reach a huge index.
    # The twiddle routes cannot: _TWIDDLE_N_MAX = 2**32 refuses first, which is
    # why their worst exposure was ~30 ms rather than 211 s — so this row uses
    # the largest n each route admits at all, not one number for all three.
    with pytest.raises(ValueError, match="without factoring"):
        cos_sin_2pi_k_over_n(2 ** 62 - 57)
    with pytest.raises(ValueError, match="without factoring"):
        hypercomplex_exp(k_axes=3, turn=(1, 2 ** 62 - 57))
    with pytest.raises(ValueError, match="without factoring"):
        quaternion_twiddle(1, 1, 2 ** 31 - 1, mu="ijk", exact=True)
    with pytest.raises(ValueError, match=r"n_points must be in \[1, 2\*\*32\)"):
        quaternion_twiddle(1, 1, 2 ** 62 - 57, mu="ijk", exact=True)


# ── G-CAP-EXELIGMOS ─────────────────────────────────────────────────────────
def test_G_CAP_EXELIGMOS_answers_on_both_cheap_axes_and_is_NAMED_on_the_seventh(
) -> None:
    """The ruling this rc exists for, executed.

    ``669`` years is the Antikythera **Exeligmos**, the back panel's triple
    Saros. ``669 = 3·223`` is odd, so ``lcm(669, 4) = lcm(669, 12) = 2676``:
    the two cheap axes are the SAME field at degree 888, which is where the
    constant comes from. The seventh axis needs a factor 7 the index does not
    carry, so it costs ``φ(18732) = 5328`` — six times the degree — and it
    REFUSES, by name, with the degree in the message.

    Does NOT prove that Exeligmos is USEFUL at that length — only that it is
    exact (see the oracle below) and reachable, and that its one refusal is
    named rather than silently demoted to the float carrier.
    """
    assert _index(669, 1) == _index(669, 3) == 2676
    assert cyclotomic_degree(2676) == 888 == MAX_CYCLOTOMIC_DEGREE
    assert _index(669, 7) == 18732
    assert cyclotomic_degree(18732) == 5328

    assert quaternion_twiddle(1, 1, 669, mu="i", exact=True)
    assert quaternion_twiddle(1, 1, 669, mu="ijk", exact=True)
    assert cos_sin_2pi_k_over_n(669)
    with pytest.raises(ValueError, match="degree 5328"):
        octonion_twiddle(1, 1, 669, mu="diagonal", exact=True)

    # 888 is the SMALLEST bound that does it — at 864 Exeligmos refuses on
    # every axis, so the constant is derived and not rounded to a nice number.
    for axis_k in (1, 3, 7):
        assert not _admits(669, axis_k, bound=864)

    # all four canonical dial periods, on both cheap axes: 8 of 12
    dials = {"Saros": 223, "Metonic": 235, "Callippic": 940, "Exeligmos": 669}
    exact_cells = [(name, k) for name, n in dials.items() for k in (1, 3, 7)
                   if _admits(n, k)]
    assert len(exact_cells) == 8
    assert all(k != 7 for _, k in exact_cells)


# ── G-CAP-WIDENING ──────────────────────────────────────────────────────────
def test_G_CAP_WIDENING_loses_nothing_and_the_control_loses_twelve() -> None:
    """A STRICT widening: 0 of 12 288 admitted rows become refusals.

    Closed-form arithmetic — no field is built anywhere in this row, which is
    why it can afford ``n`` to 4096 on three axes. The ``φ <= 100`` arm is the
    POSITIVE CONTROL: it loses 12 twiddle rows and 132 ``cos_sin`` rows, so
    the instrument demonstrably returns otherwise.

    Does NOT prove anything about ``n > 4096``, nor about callers outside this
    tree who may have pinned the removed ``MAX_CYCLOTOMIC_INDEX`` symbol — for
    them this is a BREAK, deliberately and without an alias.
    """
    def sweep(bound):
        lost = gained = 0
        for n in range(1, 4097):
            for axis_k in (1, 3, 7):
                m = _index(n, axis_k)
                old = m <= OLD_INDEX_CAP
                new = cyclotomic_degree(m) <= bound
                lost += old and not new
                gained += new and not old
        return lost, gained

    lost, gained = sweep(MAX_CYCLOTOMIC_DEGREE)
    assert lost == 0, lost
    assert gained == 2118, gained
    ctl_lost, _ = sweep(100)
    assert ctl_lost == 12, ctl_lost

    def sweep_cos_sin(bound):
        lost = gained = 0
        best = 0
        for n in range(1, 4097):
            m = 4 * n // gcd(n, 4)
            old = n <= OLD_INDEX_CAP
            new = cyclotomic_degree(m) <= bound
            if new:
                best = n
            lost += old and not new
            gained += new and not old
        return lost, gained, best

    lost, gained, best = sweep_cos_sin(MAX_CYCLOTOMIC_DEGREE)
    assert (lost, gained, best) == (0, 908, 3780)
    assert sweep_cos_sin(100)[0] == 132


# ── G-CAP-WORST / G-CAP-DENSITY ─────────────────────────────────────────────
def test_G_CAP_WORST_the_named_dearest_admitted_row_is_admitted() -> None:
    """The worst admitted object this cap lets in, named and pinned by its
    ARITHMETIC — ``octonion_twiddle(1, 1, 95, mu="diagonal", exact=True)``,
    ``M = 2660``, ``φ = 864``, 287 terms.

    MEASURED at rc478 and RECORDED in the CHANGELOG, never asserted here:
    44–67 s cold, 11.7 s warm, 0.686 MiB peak. A millisecond threshold is
    machine-shaped — the band on one unchanged configuration is 1.54× — so
    this row asserts what is invariant and leaves the clock to the record.

    Does NOT prove that ``n = 95`` is the dearest admitted row. It was found by
    ranking distinct fields on a ``φ²·terms`` proxy and measuring the top two
    per axis interleaved; the proxy is wrong by up to 2.2× in the sparse
    direction, so a dearer row may sit below it.
    """
    assert _admits(95, 7)
    assert _index(95, 7) == 2660
    assert cyclotomic_degree(2660) == 864
    coef = cyclotomic_polynomial(2660)["coefficients"]
    assert sum(1 for c in coef if c != 0) == 287


def test_G_CAP_DENSITY_phi_bounds_the_OBJECT_and_not_the_clock() -> None:
    """At ONE identical degree the admitted cost spans 98×, MEASURED.

    ``octonion_twiddle(…, 256, "diagonal")`` and ``(…, 85, "diagonal")`` are
    both ``φ = 768`` on the same axis, and differ only in how DENSE ``Φ_M``
    is: 7 terms against 253. Measured interleaved and non-overlapping, 0.36 s
    against 35.7 s. This row asserts the arithmetic that CAUSES the spread,
    not the spread itself.

    It is why rc478 ships ONE criterion. A per-axis degree bound tight enough
    to block the 35.7 s row would have to refuse the 0.36 s row at the SAME
    degree — the removed defect in a new coordinate.

    Does NOT prove the ratio; that is a recorded measurement, and it moves
    with the machine.
    """
    assert _index(256, 7) == 1792 and cyclotomic_degree(1792) == 768
    assert _index(85, 7) == 2380 and cyclotomic_degree(2380) == 768
    assert _admits(256, 7) and _admits(85, 7)
    sparse = cyclotomic_polynomial(1792)["coefficients"]
    dense = cyclotomic_polynomial(2380)["coefficients"]
    assert sum(1 for c in sparse if c != 0) == 7
    assert sum(1 for c in dense if c != 0) == 253


# ── G-CAP-INDEX ─────────────────────────────────────────────────────────────
def test_G_CAP_INDEX_the_admitted_index_reach_and_the_phi_filter() -> None:
    """The largest index a DEGREE cap admits is 3990, and the ``φ(c) == d``
    filter that makes an order-finding walk over that range affordable.

    ``tests/test_exact_twiddle_rc468.py``'s ``_cyclotomic_index_of`` walked
    ``range(1, 4 * MAX_CYCLOTOMIC_INDEX + 1)`` = 1..1024. Under a degree cap
    that bound is wrong twice: the admitted reach is 3990, and for any field
    of index above 1024 the helper raised ``AssertionError`` **on a correct
    value**. The repair is not a divisor walk of ``M`` — ``M`` is what the
    helper is looking for — but a totient filter, which is sound because a
    field of degree ``d`` can only have index ``c`` with ``φ(c) = d``.

    Does NOT prove that no other site in the tree is sized on the index,
    though a predicate scan of every arithmetic-position use found only three:
    this one and two ``MAX + 1`` boundary probes, both restated in rc478.
    """
    admitted = [m for m in range(1, 100_001)
                if cyclotomic_degree(m) <= MAX_CYCLOTOMIC_DEGREE]
    assert max(admitted) == 3990
    assert cyclotomic_degree(3990) == 864
    assert len(admitted) == 1740
    for m, want_after in ((1020, 10), (1540, 37), (2676, 8), (3990, 45)):
        d = cyclotomic_degree(m)
        cands = [c for c in range(1, 3991) if cyclotomic_degree(c) == d]
        assert len(cands) == want_after, (m, len(cands))
        assert m in cands


# ── G-CAP-SQRTK + G-CAP-MEMO-BOUND ──────────────────────────────────────────
@pytest.mark.parametrize("axis_k,index", [(3, 1524), (3, 2676), (7, 308),
                                          (7, 2660)])
def test_G_CAP_SQRTK_the_memo_returns_the_same_exact_value(axis_k,
                                                           index) -> None:
    """``_inv_sqrt_k(k, M)² · k == 1`` IN THE FIELD, with ``==``; and the
    memoised value is the unmemoised one under both ``==`` and ``is``.

    ``Qalg`` is immutable (``__slots__``, a tuple of ``Q``), so handing back
    the same object is safe — this row is what says so out loud.

    Does NOT prove the memo's SPEED. Measured and recorded, interleaved and
    non-overlapping: 54.4 % off the Exeligmos body-diagonal turn, 78.4 % off
    the dearest admitted row, and at the ``axis_k = 1`` control **nothing** —
    the memo holds 0 entries there, because ``_turn_scalars`` only calls this
    function when ``axis_k != 1``, and the A/B difference measured −4.1 % to
    +11.0 %, overlapping, i.e. drift.
    """
    cache = _qalg._INV_SQRT_K_CACHE
    cache.clear()
    try:
        first = _qalg._inv_sqrt_k(axis_k, index)
        again = _qalg._inv_sqrt_k(axis_k, index)
        assert again is first                       # the memo, not a rebuild
        assert (axis_k, index) in cache
        cache.clear()
        rebuilt = _qalg._inv_sqrt_k(axis_k, index)
        assert rebuilt is not first                 # the control: it CAN rebuild
        assert rebuilt == first                     # and the value is the same
        one = first.one()
        assert (first * first) * axis_k == one      # 1/√k squared, times k
    finally:
        cache.clear()


def test_G_CAP_SQRTK_the_axis_one_control_never_consults_the_memo() -> None:
    """The control that makes the saving figures readable: at ``axis_k = 1``
    the turn loop never calls ``_inv_sqrt_k`` at all, so the memo stays EMPTY
    and any measured "saving" there is the instrument's noise floor."""
    cache = _qalg._INV_SQRT_K_CACHE
    cache.clear()
    try:
        _qalg._turn_scalars(1, 669, 1, 1)
        assert len(cache) == 0
        _qalg._turn_scalars(3, 669, 1, 1)
        assert len(cache) == 1
    finally:
        cache.clear()


def test_G_CAP_MEMO_BOUND_the_plain_dict_needs_no_eviction() -> None:
    """The memo's worst residency at this cap is BOUNDED and computed.

    345 distinct keys — 249 reachable indices divisible by 12, 96 divisible by
    28, the largest 3780 on both — whose degrees sum to 156 368. At a measured
    112.05 bytes per degree (the coordinate tuple and its ``Q``, EXCLUDING the
    ``Φ`` tuple already resident in ``_PHI_CACHE``) that is **16.7 MiB** worst
    case, and reaching it means having built all 345 fields, which is hours of
    compute. So a plain dict with no eviction is the right shape.

    Does NOT prove the 16.7 MiB as a measured total — it is computed from one
    measured rate, and ``sys.getsizeof`` accounting is a floor, not a
    guarantee.
    """
    k3 = {_index(n, 3) for n in range(1, 40_001) if _admits(n, 3)}
    k7 = {_index(n, 7) for n in range(1, 40_001) if _admits(n, 7)}
    assert len(k3) == 249
    assert len(k7) == 96
    assert len(k3) + len(k7) == 345
    assert max(k3) == max(k7) == 3780
    assert all(m % 12 == 0 for m in k3)
    assert all(m % 28 == 0 for m in k7)
    total_degree = (sum(cyclotomic_degree(m) for m in k3)
                    + sum(cyclotomic_degree(m) for m in k7))
    assert total_degree == 156_368


# ── G-CAP-EXACT — the INDEPENDENT integer oracle ────────────────────────────
# Everything below builds Φ_M, ζ^e and √k from scratch over plain Python ints.
# It never calls Qalg.__mul__, Qalg.inverse, Qalg.__pow__, Qalg.one,
# Qalg.alpha or cyclotomic_polynomial, so it cannot agree with the carrier by
# sharing its arithmetic. `fractions` is not used: every value is an int pair.
_ORACLE_PHI: "dict[int, list]" = {}
_QR7 = (1, 2, 4)


def _divisors(m):
    out, d = [], 1
    while d * d <= m:
        if m % d == 0:
            out.append(d)
            if d != m // d:
                out.append(m // d)
        d += 1
    return sorted(out)


def _divexact(num, den):
    """Exact division of ascending int lists by a MONIC divisor."""
    num = list(num)
    dn, dd = len(num) - 1, len(den) - 1
    assert den[-1] == 1
    quo = [0] * (dn - dd + 1)
    for j in range(dn - dd, -1, -1):
        c = num[j + dd]
        quo[j] = c
        if c:
            for i in range(dd + 1):
                num[j + i] -= c * den[i]
    assert all(v == 0 for v in num), "non-zero remainder"
    return quo


def _oracle_phi(m):
    """``Φ_m`` from ``x^m − 1`` up the divisor lattice, by my own division."""
    if m in _ORACLE_PHI:
        return _ORACLE_PHI[m]
    cur = [0] * (m + 1)
    cur[0] = -1
    cur[m] = 1
    for d in _divisors(m):
        if d != m:
            cur = _divexact(cur, _oracle_phi(d))
    _ORACLE_PHI[m] = cur
    return cur


def _gcd_int(a, b):
    while b:
        a, b = b, a % b
    return a if a >= 0 else -a


def _norm(nums, den):
    g = 0
    for v in nums:
        g = _gcd_int(g, v)
    g = _gcd_int(g, den) or 1
    if den < 0:
        g = -g
    return [v // g for v in nums], den // g


def _shift(nums, phi, deg):
    """``x · nums`` reduced mod ``Φ`` — a Class-K carry, no multiplication."""
    carry = nums[deg - 1]
    out = [0] * deg
    for i in range(1, deg):
        out[i] = nums[i - 1]
    if carry:
        for i in range(deg):
            out[i] -= carry * phi[i]
    return out


def _zeta_pow(e, phi, deg):
    """``ω^e`` by ``e`` shift-reduce steps — no multiplication at all."""
    nums = [0] * deg
    nums[0] = 1
    for _ in range(e):
        nums = _shift(nums, phi, deg)
    return nums, 1


def _add(a, b):
    (an, ad), (bn, bd) = a, b
    return _norm([x * bd + y * ad for x, y in zip(an, bn)], ad * bd)


def _sub(a, b):
    (an, ad), (bn, bd) = a, b
    return _norm([x * bd - y * ad for x, y in zip(an, bn)], ad * bd)


def _mul(a, b, phi, deg):
    (an, ad), (bn, bd) = a, b
    conv = [0] * (2 * deg - 1)
    for i, x in enumerate(an):
        if x:
            for j, y in enumerate(bn):
                if y:
                    conv[i + j] += x * y
    for j in range(2 * deg - 2, deg - 1, -1):
        c = conv[j]
        if c:
            conv[j] = 0
            for i in range(deg):
                conv[j - deg + i] -= c * phi[i]
    return _norm(conv[:deg], ad * bd)


def _scale(a, num, den):
    an, ad = a
    return _norm([v * num for v in an], ad * den)


def _eq(a, b):
    return _norm(*a) == _norm(*b)


def _const(v, deg):
    nums = [0] * deg
    nums[0] = v
    return nums, 1


def _read(value, deg):
    """The tree's returned ``Qalg``/``Q`` as ``(nums, den)`` — a DATA read,
    with no arithmetic borrowed from the carrier."""
    if isinstance(value, Q):
        nums = [0] * deg
        n, d = value.as_pair()
        nums[0] = n
        return _norm(nums, d)
    pairs = [c.as_pair() for c in value.coords]
    den = 1
    for _, d in pairs:
        den = den * d // _gcd_int(den, d)
    return _norm([n * (den // d) for n, d in pairs], den)


_EXACT_ROWS = [
    ("Exeligmos k=1 n=669 NEW", 669, 1),
    ("Exeligmos k=3 n=669 NEW", 669, 3),
    ("Saros k=3 n=223 NEW", 223, 3),
    ("dearest k=1 n=443 NEW", 443, 1),
    ("sparse k=7 n=256 NEW", 256, 7),
    ("Saros k=1 n=223", 223, 1),
    ("Metonic k=1 n=235", 235, 1),
    ("the 512 anchor k=3 n=127", 127, 3),
    ("sieve qdft ijk n=23 NEW", 23, 3),
    ("sieve odft diagonal n=11 NEW", 11, 7),
    ("sieve odft diagonal n=13 NEW", 13, 7),
    ("sieve odft diagonal n=15 NEW", 15, 7),
]
#: ⚠️ THIRTEEN rows were run and all THIRTEEN were EXACT; the thirteenth,
#: ``("dearest k=7 n=95", 95, 7)``, is NOT parametrised here and the omission
#: is deliberate rather than a gap: the tree's own call at that row is a
#: 44–67 s field construction, and it is already pinned ARITHMETICALLY by
#: ``test_G_CAP_WORST_...`` above. Its oracle verdict is recorded in the
#: CHANGELOG as a measurement. The twelve here cover both Exeligmos axes, the
#: dearest ``axis_k = 1`` row, the sparse ``axis_k = 7`` row and every sieve
#: witness rc479 will need.


@pytest.mark.parametrize("label,n,axis_k", _EXACT_ROWS,
                         ids=[r[0] for r in _EXACT_ROWS])
def test_G_CAP_EXACT_newly_admitted_fields_are_exact_in_VALUE_and_in_SIGN(
        label, n, axis_k) -> None:
    """The newly-admitted fields are EXACT, by an oracle that never touches
    ``Qalg`` arithmetic.

    Checks, per row: (O1) my ``deg Φ_M`` equals my own totient · (O2) my
    ``Φ_M`` IS the minimal polynomial the returned carrier declares ·
    (O3) the returned cosine EQUALS my ``(ζ + ζ⁻¹)/2`` · (O4) the returned
    SCALED sine times my ``√k`` equals my ``(ζ − ζ⁻¹)/(2i)`` — **value AND
    sign**, because ``√k`` is built and verified by squaring rather than
    squared away · (O4b) ``σ = −1`` negates exactly that · (O5)
    ``cos² + k·sin² == 1`` · (R) my ``√k`` really squares to ``k`` ·
    and three NEGATIVE CONTROLS against a ``+1``-perturbed cosine, which must
    all come back False.

    Does NOT prove that ``Qalg.__mul__`` is correct in general — only that
    these values satisfy the defining identities of the field they claim.
    """
    index = _index(n, axis_k)
    phi = _oracle_phi(index)
    deg = len(phi) - 1
    assert deg == _totient_trialdiv(index)                            # O1

    cos_t, sin_t = _qalg._turn_scalars(axis_k, n, 1, 1)
    _, sin_neg = _qalg._turn_scalars(axis_k, n, 1, -1)
    if hasattr(cos_t, "m"):
        assert list(cos_t.m) == phi                                   # O2

    cos_v = _read(cos_t, deg)
    sin_v = _read(sin_t, deg)
    sin_v_neg = _read(sin_neg, deg)

    z = _zeta_pow((index // n) % index, phi, deg)
    zi = _zeta_pow((index - index // n) % index, phi, deg)
    ref_cos = _scale(_add(z, zi), 1, 2)
    assert _eq(cos_v, ref_cos), f"{label}: cosine VALUE"               # O3

    if axis_k == 1:
        root = _const(1, deg)
    elif axis_k == 3:                       # √3 = ζ₁₂ + ζ₁₂⁻¹
        root = _add(_zeta_pow(index // 12, phi, deg),
                    _zeta_pow((index - index // 12) % index, phi, deg))
    else:                                   # √7 = g/i, g the Legendre sum
        root = _const(0, deg)
        for a in range(1, 7):
            term = _zeta_pow((a * (index // 7)) % index, phi, deg)
            root = _add(root, term) if a in _QR7 else _sub(root, term)
        nums = root[0]
        for _ in range(3 * (index // 4)):
            nums = _shift(nums, phi, deg)
        root = _norm(nums, root[1])
    assert _eq(_mul(root, root, phi, deg), _const(axis_k, deg))        # R

    diff = _sub(z, zi)
    nums = diff[0]
    for _ in range(3 * (index // 4)):       # divide by i = ω^(M/4)
        nums = _shift(nums, phi, deg)
    ref_sin = _scale((nums, diff[1]), 1, 2)
    lhs = _mul(sin_v, root, phi, deg)
    assert _eq(lhs, ref_sin), f"{label}: sine VALUE AND SIGN"          # O4
    assert _eq(_mul(sin_v_neg, root, phi, deg),
               _scale(ref_sin, -1, 1)), f"{label}: sigma=-1"           # O4b

    s2 = _mul(sin_v, sin_v, phi, deg)
    assert _eq(_add(_mul(cos_v, cos_v, phi, deg), _scale(s2, axis_k, 1)),
               _const(1, deg))                                         # O5

    bad = _add(cos_v, _const(1, deg))                          # NEGATIVE
    assert not _eq(bad, ref_cos)
    assert not _eq(_add(_mul(bad, bad, phi, deg), _scale(s2, axis_k, 1)),
                   _const(1, deg))
    assert not _eq(lhs, _scale(ref_sin, -1, 1))
