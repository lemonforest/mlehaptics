"""rc468 (`#T1188`) — THE EXACT TWIDDLE. Strict zero, both directions.

Every assertion in this file is ``==`` on an exact object or ``!=`` on the
float one. There is no tolerance anywhere, deliberately: the whole point of
the rc is that ``exp(μ·2πk/n)`` IS a root of unity — an algebraic integer that
satisfies ``W**n == 1`` exactly — and that the float64 carrier the DFT family
shipped through rc467 does not satisfy it at all.

**Why this file exists rather than a census row.** The rc463 carrier probe
substitutes its ``2**53+1`` witness at a numeric leaf of a SEQUENCE-shaped
parameter. ``quaternion_twiddle`` / ``octonion_twiddle`` take ``int`` scalars
and a ``str`` axis, so the committed census
(``tests/demotion_census.ndjson``) holds ZERO rows for either — measured, not
inferred — and the probe's own P/F/G oracle reads ``qdft_summand`` /
``odft_summand`` as EXACT at ``n = 8, k = m = 1``, the residue where the rc467
twiddle demonstrably rounded. A green carrier gate said nothing whatever about
this defect. So the strict-zero witness is here, and it carries BOTH halves —
the exact route's equality AND the float route's inequality — so the file
cannot go vacuous by the two routes quietly converging.

Rows that would have FAILED at rc467, and the number they returned:

  * ``hypercomplex_exp(2π/8, 1)**8`` — a ratio of 147-digit integers, not 1.
  * ``qdft_summand([[0]*4, [2**60+1, 0, 0, 0]], 1, 1, 8, True, -1, [0,1,0,0])``
    slot 0 — ``Q(1879812259125035306248210951689718979, 2**61)``, where the
    exact value is ``(2**60+1)·√2/2``. ``2·slot² − ((2**60+1)²)`` was
    ``8.2e19``; it is now exactly ``0``.
  * ``hypercomplex_couple([2**60+1, 0, 0, 0], axis='i')`` slot 0 — ``70.5``
    grid units in a slot a quarter turn makes exactly ``0``. **That was the
    op's DEFAULT call through rc467, and it still is what ``theta=π/2``
    returns**; since the second rc468 pass the default is the exact turn and
    the slot is strictly ``0`` (see
    ``test_the_couple_DEFAULT_call_is_the_exact_route``, which replaced this
    file's own ``..._is_untouched`` row when the maintainer rejected the
    deferral that wrote it).
  * ``quaternion_twiddle(1, 1, N)`` ``‖W‖² − 1`` — nonzero at EVERY N tested.
"""
from __future__ import annotations

import pytest

from srmech.cascade import hypercomplex_dft as _hdft
from srmech.cascade import (
    cd_mult,
    hypercomplex_couple,
    hypercomplex_exp,
    odft_summand,
    qdft_summand,
)
from srmech.math.q import Q
from srmech.math.qalg import (
    MAX_CYCLOTOMIC_INDEX,
    Qalg,
    cos_sin_2pi_k_over_n,
)
from srmech.physics.qm.octonion import octonion_twiddle
from srmech.physics.qm.quaternion import quaternion_twiddle

#: The discriminating operand: an odd integer above 2**53, so a float64 round
#: trip is visible in the value and not only in a bound.
P = 2 ** 60 + 1

#: ``fl(π/2)`` — the float64 quarter turn the coupler's default USED to be,
#: still reachable as ``theta=`` and still rounding. Read off the shipped
#: cascade-π rather than ``math.pi`` (srmech has no libm), so this is the
#: same double the pre-rc468 default passed to the C twin.
_FLOAT_QUARTER = _hdft._PI / 2.0


# ── an INDEPENDENT instrument ───────────────────────────────────────────────
# The closure witnesses below multiply field-valued hypercomplex vectors with a
# grade decomposition written HERE, not with the shipped `_graded_one_sided` /
# `_cd_mult_graded` helpers the ops use. A witness that reuses the code under
# test can only report that the code agrees with itself.

def _field_of(vec):
    """The ``Qalg`` field one of ``vec``, or ``None`` if every slot is ``Q``."""
    for v in vec:
        if isinstance(v, Qalg):
            return v
    return None


def _grade(vec, degree: int, a: int):
    """The ``a``-th ``ζ``-power-basis grade of ``vec`` as a rational vector."""
    zero = Q(0, 1)
    return [(v.coords[a] if isinstance(v, Qalg) else (v if a == 0 else zero))
            for v in vec]


def _cd_mult_exact(u, v):
    """``u ⊗ v`` for two hypercomplex vectors over ℚ or over ℚ(ζ_M).

    ℚ(ζ_M) is a ``φ(M)``-dimensional ℚ-vector space and ``cd_mult`` is
    ℚ-bilinear, so ``u ⊗ v = Σ_{a,b} ζ^(a+b)·(u_a ⊗ v_b)`` — every ``cd_mult``
    call here takes rational vectors only, which is the whole reason
    ``cayley_dickson.py`` needed no change in this rc."""
    fu, fv = _field_of(u), _field_of(v)
    if fu is None and fv is None:
        return list(cd_mult(u, v))
    field = fu if fu is not None else fv
    alpha = Qalg.alpha(field.m)
    degree = field.degree
    dim = len(u)
    acc = [None] * dim
    for a in range(degree):
        ua = _grade(u, degree, a)
        if not any(x for x in ua):
            continue
        for b in range(degree):
            vb = _grade(v, degree, b)
            if not any(x for x in vb):
                continue
            prod = cd_mult(ua, vb)
            zab = alpha ** (a + b)
            for i in range(dim):
                if prod[i]:
                    term = zab * prod[i]
                    acc[i] = term if acc[i] is None else acc[i] + term
    zero = alpha - alpha
    return [zero if x is None else x for x in acc]


def _power(w, n: int):
    """``w**n`` in the Cayley-Dickson algebra (``n >= 1``), left-associated."""
    acc = list(w)
    for _ in range(n - 1):
        acc = _cd_mult_exact(acc, list(w))
    return acc


def _is_identity(w) -> bool:
    """``w == [1, 0, …]`` EXACTLY, on whichever exact carrier it rides."""
    head = w[0]
    one = head.one() if isinstance(head, Qalg) else Q(1, 1)
    zero = one - one
    return head == one and all(c == zero for c in w[1:])


def _norm_sq(w):
    """``Σ wᵢ²`` on the exact carrier — never ``abs``, never a float."""
    acc = None
    for c in w:
        t = c * c
        acc = t if acc is None else acc + t
    return acc


def _is_one(x) -> bool:
    one = x.one() if isinstance(x, Qalg) else Q(1, 1)
    return x == one


# ── 1. the general-turn constructor ─────────────────────────────────────────
@pytest.mark.parametrize("n", [3, 5, 7, 8, 12, 16, 64])
def test_the_general_turn_satisfies_pythagoras_and_closure_exactly(n) -> None:
    """STRICT ZERO. Both values live in ONE field, so they COMPOSE — which the
    two ``k = 1`` constructors could not do for ``4 ∤ n`` at all."""
    c, s = cos_sin_2pi_k_over_n(n)
    one = c.one()
    assert c * c + s * s == one, n
    # i = ζ_N^(N/4), with N READ OFF the field by its defining property rather
    # than recomputed from the op's own lcm — a witness that recomputes the
    # thing under test is checking the code against itself.
    i = Qalg.alpha(c.m) ** (_cyclotomic_index_of(c) // 4)
    assert (c + s * i) ** n == one, n


def _cyclotomic_index_of(x: "Qalg") -> int:
    """The cyclotomic index ``N`` of ``x``'s field, found by the ONE property
    that identifies it: ``ζ_N`` has multiplicative order exactly ``N``."""
    alpha = Qalg.alpha(x.m)
    one = alpha.one()
    for candidate in range(1, 4 * MAX_CYCLOTOMIC_INDEX + 1):
        if alpha ** candidate == one:
            return candidate
    raise AssertionError("no cyclotomic order found for this field")


def test_the_k_equals_one_case_IS_the_two_ops_it_absorbed() -> None:
    """⚠️ THIS ROW USED TO PROVE A WIDENING; it now records a REMOVAL.

    Through the first rc468 pass it asserted
    ``cos_sin_2pi_k_over_n(n) == (cos_2pi_over_n(n), sin_2pi_over_n(n))`` at
    ``n in {4, 8, 12, 16}`` — and it PASSED, which is exactly what made the two
    older ops duplicates rather than peers: a generalisation had shipped beside
    its own special cases. Both were removed in the same rc, so the equality
    can no longer be written, and what is left to assert is the two halves of
    that identity that survive it:

      * the values themselves, pinned against the ``Φ₈`` coordinates the
        removed ``cos_2pi_over_n(8)`` returned (``lcm(8, 4) = 8``, so this is
        the same field and the same element — the removal moved no value); and
      * the removal itself, so no alias can quietly reintroduce the pair.
    """
    c8, s8 = cos_sin_2pi_k_over_n(8)
    assert c8.m == (1, 0, 0, 0, 1)
    assert c8.coords == (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2))
    assert s8 == c8                       # sin(pi/4) == cos(pi/4), exactly
    import srmech.math.qalg as _qalg_mod
    for gone in ("cos_2pi_over_n", "sin_2pi_over_n"):
        assert not hasattr(_qalg_mod, gone), gone


def test_the_rational_collapse_set_is_EXACTLY_the_quarter_turns() -> None:
    """MEASURED, not assumed — and it is the whole justification for the mixed
    carrier. ``list[Q]`` is returned exactly where both the cosine and the sine
    of the turn are rational, and that set is ``4k ≡ 0 (mod n)``."""
    both_rational = {(n, k) for n in range(1, 17) for k in range(n)
                     if all(v.is_rational() for v in cos_sin_2pi_k_over_n(n, k))}
    quarter_turns = {(n, k) for n in range(1, 17) for k in range(n)
                     if (4 * k) % n == 0}
    assert both_rational == quarter_turns
    # the instrument can return otherwise: the set is neither empty nor all of
    # the turns it ranged over
    assert 0 < len(both_rational) < sum(range(1, 17))


def test_the_turn_numerator_is_reduced_in_Z_n_first() -> None:
    """Class I, exactly: ``k`` and ``k + n`` are the same turn, and ``−k`` is
    the conjugate one."""
    c0, s0 = cos_sin_2pi_k_over_n(8, 1)
    c1, s1 = cos_sin_2pi_k_over_n(8, 9)
    assert (c0, s0) == (c1, s1)
    cm, sm = cos_sin_2pi_k_over_n(8, -1)
    assert cm == c0 and sm == -s0


def test_the_general_turn_refuses_a_non_int_and_an_out_of_range_index() -> None:
    with pytest.raises(TypeError):
        cos_sin_2pi_k_over_n(True)
    with pytest.raises(TypeError):
        cos_sin_2pi_k_over_n(8, 1.0)
    with pytest.raises(ValueError):
        cos_sin_2pi_k_over_n(0)
    with pytest.raises(ValueError):
        cos_sin_2pi_k_over_n(MAX_CYCLOTOMIC_INDEX + 1)


# ── 2. the twiddles: closure and unit norm, EXACTLY ─────────────────────────
_Q_AXES = ["i", "j", "k", "ijk"]
_O_AXES = ["i", "e4", "e7", "ijk", "diagonal"]


@pytest.mark.parametrize("n", [3, 4, 5, 8, 12, 16])
@pytest.mark.parametrize("axis", _Q_AXES)
def test_quaternion_twiddle_exact_closes_on_the_identity(n, axis) -> None:
    """STRICT ZERO — the identity the op is NAMED for. ``W**N`` is the EXACT
    identity, on every named axis including the irrational body diagonal, where
    the float route satisfies it only to ``1e-9·N``."""
    w = quaternion_twiddle(1, 1, n, mu=axis, sigma=1, exact=True)
    assert _is_identity(_power(w, n)), (n, axis, w)
    assert _is_one(_norm_sq(w)), (n, axis)


@pytest.mark.parametrize("n", [3, 4, 7, 8])
@pytest.mark.parametrize("axis", _O_AXES)
def test_octonion_twiddle_exact_closes_on_the_identity(n, axis) -> None:
    """The dim-8 peer, ``'diagonal'`` (``1/√7``, via the quadratic Gauss sum)
    included."""
    w = octonion_twiddle(1, 1, n, mu=axis, sigma=1, exact=True)
    assert _is_identity(_power(w, n)), (n, axis, w)
    assert _is_one(_norm_sq(w)), (n, axis)


@pytest.mark.parametrize("n", [3, 5, 7, 8, 12])
def test_the_float_route_satisfies_NEITHER_identity(n) -> None:
    """THE OTHER HALF, so this file cannot go vacuous. The float64 twiddle is
    not a unit and does not close — and the gap is in the VALUE, not in a
    bound. Read exactly, via the exact rational of each float64.

    (If this ever passes, the float route became exact and the strict-zero
    peers above are no longer measuring a difference — which is news, not a
    reason to delete the test.)"""
    w = quaternion_twiddle(1, 1, n, sigma=1)
    exact_read = [Q.from_float(c) for c in w]
    assert _norm_sq(exact_read) != Q(1, 1), n
    assert not _is_identity(_power(exact_read, n)), n


def test_the_float_route_is_unchanged_byte_for_byte() -> None:
    """``exact=False`` did not move in rc468 — no C source was touched and
    ``SRMECH_ABI_VERSION`` did not bump. These literals were MEASURED on the
    rc467 tree before the exact rung was written."""
    assert quaternion_twiddle(1, 1, 8) == [
        0.7071067811865476, -0.7071067811865475, -0.0, -0.0]
    assert octonion_twiddle(1, 1, 8)[:2] == [
        0.7071067811865476, -0.7071067811865475]


def test_the_quarter_turns_come_back_on_the_RATIONAL_carrier() -> None:
    """The narrowest carrier that holds the value. A quarter turn on a
    rational axis is a Gaussian unit, so it is ``list[Q]`` — which is what the
    committed census rows and the Layer-1 witnesses already read."""
    assert quaternion_twiddle(1, 1, 4, exact=True) == [
        Q(0, 1), Q(-1, 1), Q(0, 1), Q(0, 1)]
    assert all(isinstance(v, Q)
               for v in octonion_twiddle(1, 1, 4, exact=True))
    # ...and every OTHER turn rides the field carrier, uniformly, never mixed
    for v in quaternion_twiddle(1, 1, 8, exact=True):
        assert isinstance(v, Qalg)
    for v in quaternion_twiddle(1, 1, 4, mu="ijk", exact=True):
        assert isinstance(v, Qalg)       # rational turn, IRRATIONAL axis


def test_the_axis_scale_SHIFTS_the_rational_set_rather_than_emptying_it() -> None:
    """MEASURED — and it falsified the claim this rc first wrote down.

    "``list[Q]`` exactly on the quarter turns" is true of the axis-free
    constructor and of a RATIONAL axis. It is NOT true once the ``1/sqrt(k)``
    scale is in play: ``sin(2*pi/3)/sqrt(3) = 1/2`` exactly, so the THIRD turn
    on the body diagonal is all-rational — and the value is the order-3 unit
    quaternion of the binary tetrahedral group, a fact about the algebra rather
    than an artefact of the carrier rule. The same turn on a basis axis stays
    irrational, so neither arm subsumes the other and the rule has to be
    stated as "every component rational".

    This was caught by the op's own worked example failing to execute, not by
    review of the sentence — which is the argument for shipping the example.
    """
    assert list(hypercomplex_exp(k_axes=3, turn=(1, 3)))[:4] == [
        Q(-1, 2), Q(1, 2), Q(1, 2), Q(1, 2)]
    assert quaternion_twiddle(1, 1, 3, mu="ijk", sigma=1, exact=True) == [
        Q(-1, 2), Q(1, 2), Q(1, 2), Q(1, 2)]
    # ...and it IS a cube root of one, exactly, on the rational carrier
    assert _is_identity(_power(
        quaternion_twiddle(1, 1, 3, mu="ijk", sigma=1, exact=True), 3))
    # the SAME turn on a basis axis has nothing to cancel the sqrt(3)
    for v in quaternion_twiddle(1, 1, 3, mu="i", exact=True):
        assert isinstance(v, Qalg)
    for v in hypercomplex_exp(k_axes=1, turn=(1, 3))[:2]:
        assert isinstance(v, Qalg)


def test_the_exact_route_RAISES_above_the_field_cap_rather_than_falling_back() -> None:
    """A fallback to the float carrier would be a silent demotion — the exact
    defect class this rc removes. Each axis family has its own bound, and the
    message names the index it would have built."""
    for mu, n in (("ijk", 128), ("i", 255)):
        with pytest.raises(ValueError, match="MAX_CYCLOTOMIC_INDEX"):
            quaternion_twiddle(1, 1, n, mu=mu, exact=True)
    for mu, n in (("diagonal", 64), ("ijk", 128)):
        with pytest.raises(ValueError, match="MAX_CYCLOTOMIC_INDEX"):
            octonion_twiddle(1, 1, n, mu=mu, exact=True)
    # and just below each bound it ANSWERS, so the refusal is a boundary and
    # not a blanket
    assert _is_identity(_power(
        octonion_twiddle(1, 1, 32, mu="diagonal", sigma=1, exact=True), 32))


def test_a_sequence_axis_is_normalised_exactly_or_REFUSED() -> None:
    """``[0,1,1,1]`` and the float64 ``'ijk'`` vector are the same DIRECTION,
    so both land on the same exact ``(0,1,1,1)/√3``. A direction with no exact
    unit in the shipped fields is refused rather than rounded."""
    named = quaternion_twiddle(1, 1, 8, mu="ijk", sigma=1, exact=True)
    from srmech.physics.qm.quaternion import _MU_AXES
    assert quaternion_twiddle(1, 1, 8, mu=[0, 1, 1, 1], sigma=1,
                              exact=True) == named
    assert quaternion_twiddle(1, 1, 8, mu=list(_MU_AXES["ijk"]), sigma=1,
                              exact=True) == named
    with pytest.raises(ValueError, match="rational square"):
        quaternion_twiddle(1, 1, 8, mu=[0, 1, 2, 0], exact=True)


# ── 3. the summands ─────────────────────────────────────────────────────────
def test_the_qdft_summand_is_exact_on_a_NON_quarter_turn() -> None:
    """THE ROW THAT MOVED. At ``n = 8, k = m = 1`` the real slot is exactly
    ``P·√2/2``, so ``2·slot² == P²`` holds with ``==``. rc467 returned
    ``Q(1879812259125035306248210951689718979, 2**61)`` there, which misses
    that identity by ``8.2e19``."""
    out = qdft_summand([[0, 0, 0, 0], [P, 0, 0, 0]], 1, 1, 8, True, -1,
                       [0, 1, 0, 0])
    slot0 = out[0]
    one = slot0.one()
    assert slot0 * slot0 * Q(2, 1) == one * Q(P * P, 1)
    # cos = −sin at this turn under σ = −1, so the two live slots cancel
    assert out[0] + out[1] == one - one
    # the rc467 value did NOT satisfy it — the instrument can fail
    stale = Q(1879812259125035306248210951689718979, 2 ** 61)
    assert stale * stale * Q(2, 1) != Q(P * P, 1)


def test_the_quarter_turn_summands_are_unmoved() -> None:
    """rc466's exact pin-slot rows are byte-identical under the new route —
    the widening added turns, it did not move the ones already exact."""
    assert qdft_summand([[0, 0, 0, 0], [P, 0, 0, 0]], 1, 1, 4, True, -1,
                        [0, 1, 0, 0]) == [Q(0, 1), Q(-P, 1), Q(0, 1), Q(0, 1)]
    assert qdft_summand([[P, 0, 0, 0]], 0, 0, 1, True, -1,
                        [0, 1, 0, 0])[0] == Q(P, 1)


def test_the_odft_two_sided_form_keeps_its_DECLARED_bracketing() -> None:
    """F378 is load-bearing and survives the carrier change: the two
    associations DIFFER on distinct axes, exactly as they do on the float
    route, because the ``s²`` term takes the nested product on the declared
    side."""
    # the sample must be IMAGINARY for the two bracketings to differ at all:
    # a real scalar associates with everything, so a real-only sample makes
    # this test vacuous on the float route too (measured).
    xs = [[0] * 8, [0, 0, P, 0, 0, 0, 0, 0]]
    mu, mu_r = [0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0]
    left_assoc = odft_summand(xs, 1, 1, 8, "two_sided", "left_associated", -1,
                              mu, mu_r)
    right_assoc = odft_summand(xs, 1, 1, 8, "two_sided", "right_associated",
                               -1, mu, mu_r)
    assert left_assoc != right_assoc
    # and each equals its own four-term closed form, built here from the
    # constructor rather than from the op
    c, s = cos_sin_2pi_k_over_n(8, 1)
    s = -s                                          # sigma = -1
    x = [Q(0, 1), Q(0, 1), Q(P, 1)] + [Q(0, 1)] * 5
    mx = cd_mult([Q(v, 1) for v in mu], x)
    xn = cd_mult(x, [Q(v, 1) for v in mu_r])
    nested_l = cd_mult(mx, [Q(v, 1) for v in mu_r])
    want_l = [c * c * x[i] + c * s * mx[i] + c * s * xn[i] + s * s * nested_l[i]
              for i in range(8)]
    assert left_assoc == want_l


def test_the_summand_RAISES_above_the_field_cap() -> None:
    """The exact operand elects the exact route; when the field is out of
    reach the op says so instead of answering from a rounded angle."""
    with pytest.raises(ValueError, match="MAX_CYCLOTOMIC_INDEX"):
        qdft_summand([[P, 0, 0, 0]] * 2, 1, 1, 65, True, -1, [0, 1, 0, 0])
    # a float sample still answers there, on the carrier it elected
    got = qdft_summand([[float(P), 0.0, 0.0, 0.0]] * 2, 1, 1, 65, True, -1,
                       [0, 1, 0, 0])
    assert all(isinstance(v, float) for v in got)


# ── 4. hypercomplex_exp's turn= route, the exact peer of its own radian ───
# rc468 (`#T1188`) shipped this route as a SEPARATE `hypercomplex_turn(k, n,
# k_axes)` and then folded it back in: two ops that differ only in which
# operand they are handed are one op, on the einsum/kron precedent. These rows
# are the same measurements through the surviving spelling.
@pytest.mark.parametrize("k_axes", [1, 3, 7])
@pytest.mark.parametrize("n", [3, 4, 8])
def test_the_turn_route_closes_where_the_radian_route_cannot(
        n, k_axes) -> None:
    w = list(hypercomplex_exp(k_axes=k_axes, turn=(1, n)))
    assert _is_identity(_power(w, n)), (n, k_axes)
    assert _is_one(_norm_sq(w)), (n, k_axes)


def test_the_radian_route_still_cannot_and_that_is_the_operand() -> None:
    """``theta=`` takes an ANGLE. ``fl(2π/8)`` is already not
    ``2π/8``, so no carrier downstream can recover the turn — the op's own
    rc467 note is TRUE and stays true. This is the negative control that keeps
    the two routes honest, and it is the reason ONE op can serve both: the
    operand really is different, so there is something to dispatch on."""
    from srmech.cascade.hypercomplex_dft import _PI
    w = list(hypercomplex_exp(2.0 * _PI / 8.0, 1))
    assert all(isinstance(v, Q) for v in w)
    assert not _is_identity(_power(w, 8))
    # ...while the SAME op, handed the same rotation as a TURN, does close
    assert _is_identity(_power(list(hypercomplex_exp(k_axes=1, turn=(1, 8))), 8))


def test_the_turn_route_refuses_its_boundaries() -> None:
    with pytest.raises(ValueError, match="k_axes"):
        hypercomplex_exp(k_axes=2, turn=(1, 8))
    with pytest.raises(ValueError, match=r"\(int, int\) pair"):
        hypercomplex_exp(k_axes=1, turn=(1.0, 8))
    with pytest.raises(ValueError, match="denominator must be >= 1"):
        hypercomplex_exp(k_axes=1, turn=(1, 0))
    with pytest.raises(ValueError, match="MAX_CYCLOTOMIC_INDEX"):
        hypercomplex_exp(k_axes=7, turn=(1, 64))


def test_exactly_one_of_theta_and_turn_is_given() -> None:
    """The two operands are MUTUALLY EXCLUSIVE, and both degenerate calls
    raise. Without this row the fold could ship a silent precedence rule —
    "turn wins" or "theta wins" — which is the shape of silent wrong answer
    the whole rc removes."""
    with pytest.raises(ValueError, match="exactly ONE"):
        hypercomplex_exp(k_axes=1)
    with pytest.raises(ValueError, match="exactly ONE"):
        hypercomplex_exp(0.5, 1, turn=(1, 8))


def test_the_absorbed_op_is_GONE_with_no_alias() -> None:
    """Removal means removal: `hypercomplex_turn` is not importable, not an
    attribute of either module, and not in `srmech.cascade.__all__`."""
    import srmech.cascade as _casc
    from srmech.cascade import hypercomplex_dft as _mod
    assert not hasattr(_casc, "hypercomplex_turn")
    assert not hasattr(_mod, "hypercomplex_turn")
    assert "hypercomplex_turn" not in _casc.__all__
    assert "hypercomplex_exp" in _casc.__all__
    with pytest.raises(ImportError):
        from srmech.cascade import hypercomplex_turn  # noqa: F401


def test_the_exact_keyword_drains_NOTHING_and_execution_is_the_evidence() -> None:
    """rc468 (`#T1188`) — the Defect-3 adjudication, MEASURED both ways.

    ``tools/demotion_probe.py`` treats a parameter merely NAMED ``exact`` as an
    R3 accuracy declaration, so a keyword CAN drain a carrier-census row
    without any route ever running. The two DFT twiddles keep that keyword —
    they have no inexact operand to dispatch on, so there is nothing an
    operand-carrier rule could read — and this row proves the keyword is not
    what is doing the draining:

      * the marker really is produced for both ops (so the hazard is real and
        this assertion is not vacuous), AND
      * neither op has a single row in the committed demotion census, so there
        is nothing for the marker to drain — measured against a control op the
        probe DOES reach, so an empty census file cannot pass this silently.

    Therefore the only evidence that these two take an exact route is the
    EXECUTED strict-zero witness at the top of this file, which is the correct
    state and the one the maintainer asked to be confirmed rather than assumed.
    """
    import json
    import sys as _sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    tools = root / "tools"
    if str(tools) not in _sys.path:
        _sys.path.insert(0, str(tools))
    import demotion_probe as _dp

    for fn in (quaternion_twiddle, octonion_twiddle):
        hits = _dp.declaration_hits(fn)
        assert "exact= opt-in" in hits, (fn.__name__, hits)

    census = root / "tests" / "demotion_census.ndjson"
    rows = [json.loads(ln) for ln in
            census.read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows = [r for r in rows if "op" in r]
    named = {"srmech.physics.qm.quaternion.quaternion_twiddle",
             "srmech.physics.qm.octonion.octonion_twiddle"}
    assert [r for r in rows if r["op"] in named] == [], (
        "a twiddle now HAS census rows — the probe reaches it, so the "
        "'the keyword drains nothing' claim above is stale. Re-read it; this "
        "is good news, not a failure.")
    assert [r for r in rows if r["op"] == "srmech.cascade.qdft_summand"], (
        "the control is empty too, so the assertion above measures nothing")


# ── 5. the coupler's rational turn ──────────────────────────────────────────
def test_the_couple_quarter_turn_puts_EXACTLY_zero_in_the_anchor() -> None:
    """The slot the default float fold fills with ``70.5`` grid units."""
    out = hypercomplex_couple([P, 0, 0, 0], axis="i", turn=(1, 4))
    assert out == [Q(0, 1), Q(P, 1), Q(0, 1), Q(0, 1)]


def test_the_diagonal_couple_round_trip_is_EXACT() -> None:
    """F437 on the exact carrier. The float route misses ``2**60+1`` by
    ``309.8`` — the axis residue, ``‖μ_q61‖² − 1 = 2.7e-16`` — and that residue
    does not exist here, because ``1/√3`` is carried in the field rather than
    normalised in float64."""
    bound = hypercomplex_couple([P, 2, 3], axis="diagonal", turn=(1, 4))
    back = hypercomplex_couple(bound, axis="diagonal", turn=(1, 4), sigma=-1)
    assert [back[0], back[1], back[2], back[3]] == [
        Q(0, 1), Q(P, 1), Q(2, 1), Q(3, 1)]


def test_the_couple_DEFAULT_call_is_the_exact_route() -> None:
    """The rc468 review's own deferral, reversed — and this test is its
    inverse, kept at the same name-shape so the reversal is visible in the diff.

    Through the first rc468 pass the default stayed on the float ``theta``
    route and this file asserted so, on the stated ground that flipping it
    would make the default diverge from the C twin
    ``srmech_hypercomplex_couple_q61``. That reason did not survive: a C peer
    needing the same correction is WORK, not grounds to skip the Python half,
    and the correction landed in the same change
    (``srmech_hypercomplex_couple_turn_q61``). The default phase is now the
    exact rational turn ``(1, 4)`` in BOTH projections, and an exact operand on
    an exactly-normalisable axis takes the exact route — with the CARRIER
    still the operand's, which is the rc466 rule and is why a float leaf still
    comes back float."""
    #  the slot the ANGLE route fills with 70.5 grid units, on the DEFAULT call
    assert hypercomplex_couple([P, 0, 0], axis="i")[1] == Q(0, 1)
    assert hypercomplex_couple([P, 0, 0], axis="i") == [
        Q(-P, 1), Q(0, 1), Q(0, 1), Q(0, 1)]
    #  the default 'diagonal' axis carries 1/sqrt(3) in the FIELD, so the
    #  default call on an exact operand is Qalg and EXACT, not Q on the grid
    out = hypercomplex_couple([P, 0, 0])
    assert all(isinstance(v, Qalg) for v in out), out
    #  and the ANGLE route is still reachable, still rounding, deliberately
    ang = hypercomplex_couple([P, 0, 0], axis="i", theta=_FLOAT_QUARTER)
    assert ang[1] != Q(0, 1)
    assert all(isinstance(v, Q) and (2 ** 61) % v.denominator == 0
               for v in ang)
    #  the carrier is still the OPERAND'S: one float leaf elects float
    assert isinstance(hypercomplex_couple([1.0, 2, 3])[0], float)


def test_the_couple_default_agrees_across_BOTH_projections() -> None:
    """The deferral's stated reason, measured. The default no longer routes
    through a float64 angle in EITHER projection, and where the two carriers
    overlap — a dyadic operand on a rational axis inside the int64 Q61 ceiling
    — the exact Q(zeta) answer and the C fixed-point answer are EQUAL as
    rationals. Skipped, never silently vacuous, when no library is loaded."""
    from srmech import _native
    from srmech.cascade import hypercomplex_dft as _H
    if not _native.has_native_hypercomplex_couple_turn():
        pytest.skip("no native turn coupler loaded; the pure arm is the "
                    "complete alternative and is covered by the row above")
    one = _H._Q61_ONE
    mu_i = [0, one, 0, 0, 0, 0, 0, 0]
    streams = [Q(1, 2), Q(1, 4), Q(-1, 8)]
    for form in ("left", "right"):
        for sig, inv in ((1, False), (-1, False), (1, True)):
            exact = hypercomplex_couple(list(streams), axis="i", form=form,
                                        sigma=sig, inverse=inv)
            packed, _octo = _H._pack_streams_exact(streams)
            from_c = _native.hypercomplex_couple_turn_q61_c(
                [round(v * one) for v in packed], mu_i,
                _H._signed_turn_k(1, sig, inv), 4, form == "left")
            assert from_c is not None
            assert list(exact) == [Q(v, one) for v in from_c][:4]


def test_the_two_projections_agree_BYTE_FOR_BYTE_on_the_exact_turn() -> None:
    """THE deliverable of the rc468 stage-3 brief, as a standing gate rather
    than a one-off measurement.

    The stage-1 deferral's stated reason was that flipping the default would
    "make the default exact-stream call diverge from its C twin". It does not,
    because the C twin was corrected in the same change. This sweeps the pure
    Q61 quarter-turn twiddle against ``srmech_hypercomplex_couple_turn_q61``
    over three axes x four operands x both forms x nine turns and asserts
    INTEGER equality on all eight limbs of every row -- no tolerance anywhere,
    because there is nothing to round: both sides read the same four exact
    constants off the same quarter-turn index.

    Skipped, never silently vacuous, when no library is loaded: a pure host has
    no second projection to disagree with, and the pure arm is the complete
    alternative."""
    from srmech import _native
    from srmech.cascade import hypercomplex_dft as _H
    if not _native.has_native_hypercomplex_couple_turn():
        pytest.skip("no native turn coupler loaded; nothing to compare against")
    one = _H._Q61_ONE
    axes = {
        "i": [0, one, 0, 0, 0, 0, 0, 0],
        "diagonal": [0] + [_H._to_q61(1.0 / (3.0 ** 0.5))] * 3 + [0, 0, 0, 0],
        "octonion": [0] + [_H._to_q61(1.0 / (7.0 ** 0.5))] * 7,
    }
    operands = [
        [0, one, 0, 0, 0, 0, 0, 0],
        [0, one // 2, one // 4, -one // 8, 0, 0, 0, 0],
        [one // 3, -one, one, one // 7, one // 11, 0, -one // 5, one // 2],
        [0, 1, -1, 3, 5, 7, 11, 13],
    ]
    rows = 0
    for name, mu in axes.items():
        for streams in operands:
            for form in ("left", "right"):
                #  every quarter-turn index, both orientations, and turns whose
                #  numerator reduces onto one -- 5/4 and 8/4 are 1/4 and 0 again
                for k in (-3, -2, -1, 0, 1, 2, 3, 5, 8):
                    nat = _native.hypercomplex_couple_turn_q61_c(
                        streams, mu, k, 4, form == "left")
                    assert nat is not None, "operand inside the native ceiling"
                    quarters = ((4 * k) // 4) % 4
                    cos = _H._QUARTER_COS_Q61[quarters]
                    sin = _H._QUARTER_SIN_Q61[quarters]
                    tw = [cos] + [_H._q61_fxmul(sin, mu[i]) for i in range(1, 8)]
                    pure = (_H._octo_mult_q61(tw, streams) if form == "left"
                            else _H._octo_mult_q61(streams, tw))
                    assert nat == pure, (name, form, k, nat, pure)
                    rows += 1
    assert rows == 216, rows            # the sweep cannot silently shrink


def test_the_turn_coupler_REFUSES_a_turn_the_grid_cannot_hold() -> None:
    """The C peer and the pure peer make the SAME refusal, and it is the same
    one the ``turn=`` route makes: a turn that is not a whole number of quarter
    turns has no exact Q61 twiddle, so it raises rather than rounding. The
    complete alternative is the exact Q(zeta_M) carrier, which is not a
    fixed-point one and therefore has no C-host peer at this width."""
    from srmech import _native
    from srmech.cascade import hypercomplex_dft as _H
    one = _H._Q61_ONE
    mu = [0, one, 0, 0, 0, 0, 0, 0]
    st = [0, one // 2, 0, 0, 0, 0, 0, 0]
    with pytest.raises(ValueError, match="quarter turns"):
        _H._couple_q61_turn(st, mu, 1, 8, form="left")
    with pytest.raises(ValueError, match="denominator"):
        _H._couple_q61_turn(st, mu, 1, 0, form="left")
    if not _native.has_native_hypercomplex_couple_turn():
        pytest.skip("no native peer to cross-check the refusal against")
    with pytest.raises(ValueError, match="status"):
        _native.hypercomplex_couple_turn_q61_c(st, mu, 1, 8, True)
    #  and the turn it CAN hold answers, on both sides
    assert _native.hypercomplex_couple_turn_q61_c(st, mu, 1, 4, True) is not None


def test_the_couple_turn_route_REFUSES_rather_than_rounding() -> None:
    for bad, match in (
            ((1, 0), "denominator"),
            ("1/4", "must be an"),
    ):
        with pytest.raises(ValueError, match=match):
            hypercomplex_couple([P, 0, 0], axis="i", turn=bad)
    with pytest.raises(ValueError, match="every stream leaf must be exact"):
        hypercomplex_couple([1.0, 2, 3], axis="i", turn=(1, 4))
    with pytest.raises(ValueError, match="rational square"):
        hypercomplex_couple([P, 0, 0], axis=[0, 1, 2, 0], turn=(1, 4))
    # 5 streams pack an OCTONION, so 'diagonal' is the 1/sqrt(7) axis and the
    # field index is lcm(64, 28) = 448. (At 3 streams the same name is the
    # quaternion 1/sqrt(3) axis, lcm(64, 12) = 192, and it ANSWERS — the bound
    # is the axis's, not the turn's alone.)
    assert hypercomplex_couple([P, 0, 0], axis="diagonal", turn=(1, 64))
    with pytest.raises(ValueError, match="MAX_CYCLOTOMIC_INDEX"):
        hypercomplex_couple([P, 0, 0, 0, 0], axis="diagonal", turn=(1, 64))


# ── 6. the whole declared chain, exact on a NON-quarter bin ─────────────────
def test_the_declared_qdft_chain_is_exact_on_a_NON_quarter_bin() -> None:
    """The summand fix reaching the top of the composition, not just the leaf.

    The rc466 chain witness runs at ``n = 2``, where EVERY turn is a quarter
    turn, so it could not see this route at all — and at ``n = 3`` it reads
    only bin 0, whose turn is ``r = 0``. Bin 1 at ``n = 3`` is the first bin in
    the tree whose twiddle is genuinely irrational, and the declared
    ``quaternion_dft`` chain now carries it EXACTLY, over the field, matching
    the closed form built here from the constructor rather than from the op.

    Through rc467 that bin was a ``Q`` on the ``2**-61`` grid, of the cosine of
    a rounded angle.
    """
    import sys
    from pathlib import Path
    tests_dir = str(Path(__file__).resolve().parent)
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    import test_c_cascade_value_parity_rc450 as harness
    from srmech.dsl._cascade_chain import cascade_chain_specs

    _variant, spec, entry = cascade_chain_specs("quaternion_dft")[0]
    fwd = dict(harness._case_defaults(entry))
    fwd.update({"x": [[P, 0, 0, 0], [1, 0, 0, 0], [2, 0, 0, 0]],
                "mu_axis": "i", "inverse": False, "left": True})
    out = harness._py_run(spec, fwd)

    # bin 0 is the DC turn: still exactly the rational sum, unmoved
    assert all(isinstance(v, Q) for v in out[0])
    assert out[0][0] == Q(P + 3, 1)

    # bin 1 is a THIRD turn: the field carrier, and equal to the closed form
    assert all(isinstance(v, Qalg) for v in out[1]), [
        type(v).__name__ for v in out[1]]
    c1, s1 = cos_sin_2pi_k_over_n(3, 1)
    c2, s2 = cos_sin_2pi_k_over_n(3, 2)
    s1, s2 = -s1, -s2                       # sigma = -1, the forward transform
    one = c1.one()
    assert out[1][0] == one * Q(P, 1) + c1 * Q(1, 1) + c2 * Q(2, 1)
    assert out[1][1] == s1 * Q(1, 1) + s2 * Q(2, 1)
