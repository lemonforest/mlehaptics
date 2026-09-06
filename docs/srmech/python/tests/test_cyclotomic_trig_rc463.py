"""Gate for the exact cyclotomic trig constructor (rc463 surface, `#T1188`).

``srmech.math.qalg.cos_sin_2pi_k_over_n(n, k)`` returns ``cos(2πk/n)`` and
``sin(2πk/n)`` as EXACT number-field elements over ONE field ``Φ_lcm(n,4)``.
The whole point is that the values are CONSTRUCTED in the field they already
live in rather than floated and then rationalised, so every assertion here that
carries the claim is an assertion on exact ``Q`` coordinates or on an exact
field identity. Exactly one test projects to a float, and it is labelled as a
projection sanity check, not as the exactness evidence.

**rc468 (`#T1188`) — this file used to gate TWO ops.** rc463 shipped
``cos_2pi_over_n`` over ``Φ_n`` and ``sin_2pi_over_n`` over ``Φ_lcm(n,4)``;
rc468 added the general-turn constructor beside them and then REMOVED both,
because with ``k`` defaulting to 1 the general op IS the two. Every value this
file used to pin is pinned here still — the cosine's Niven census, the sine's
different census, the defining polynomials, the ``n = 8`` coordinates — because
the values did not move. What moved is the FIELD: the cosine now answers over
``Φ_lcm(n,4)`` like the sine, so the pair composes at EVERY ``n`` instead of
only at ``4 | n``. The old ``test_fields_differ_when_four_does_not_divide_n``
is inverted below into
:func:`test_the_two_values_now_share_ONE_field_at_every_n`, which is the
statement the removal makes true.

Four things this file is built to catch:

1. **A silently wrong field.** ``sin(2π/n)`` is generally NOT in ℚ(ζ_n) — the
   op works over ``Φ_lcm(n,4)``. :func:`test_field_is_phi_lcm_n_4_for_BOTH`
   pins the minimal polynomial of both values against
   ``cyclotomic_polynomial`` directly.
2. **A function named ``sin`` that answers ``i·sin``.** The rejected cheap
   construction ``(ζ − ζ⁻¹)/2`` differs from the shipped one by a factor of
   ``i``, which no float-free coordinate check would notice *unless* it is a
   check the factor of ``i`` breaks. Three do: the Pythagorean identity, the
   exact rational values at ``n = 4`` and ``n = 12``, and the minimal-
   polynomial relations (``i·sin`` satisfies the same polynomial with the
   sign of every odd-degree-in-``x²`` term flipped).
3. **A general turn that is not the turn.** ``k`` must be reduced in ``Z_n``
   and a negative ``k`` must be the conjugate turn, both exactly.
4. **A guard that cannot fire.** Every refusal asserted below is reachable.

No numpy. No ``fractions`` (the exact scalar is ``srmech.math.q.Q``). No
``abs``. No ``math``.
"""

import pytest

from srmech.math.poly import cyclotomic_polynomial
from srmech.math.q import Q
from srmech.math.qalg import (
    MAX_CYCLOTOMIC_INDEX,
    Qalg,
    cos_sin_2pi_k_over_n,
)

ZERO = Q(0, 1)


def _cos(n, k=1):
    return cos_sin_2pi_k_over_n(n, k)[0]


def _sin(n, k=1):
    return cos_sin_2pi_k_over_n(n, k)[1]


def _phi(index):
    """``Φ_index`` as the ascending int tuple ``Qalg`` uses for ``m``."""
    return tuple(cyclotomic_polynomial(index)["coefficients"])


def _is_exactly_zero(element):
    """True when EVERY coordinate is the exact rational zero. This is the
    exactness assertion the float-free relations below hang on: it reads the
    ``Q`` coordinates, never a magnitude and never a tolerance."""
    return element.coords == tuple(ZERO for _ in range(element.degree))


def _lcm4(n):
    """``lcm(n, 4)`` — the ONE field index the op works over."""
    a, b = n, 4
    while b:
        a, b = b, a % b
    return 4 * n // a


def _independent_cos(n):
    """``cos(2π/n)`` over ``Φ_lcm(n,4)`` rebuilt from PUBLIC PARTS ONLY —
    ``Qalg.alpha`` + ``cyclotomic_polynomial`` — never from the op under test.

    This is what keeps the Pythagorean gate below a check ON the shipped
    constructor rather than a check of the constructor against itself. Through
    rc467 the same helper existed because the shipped cosine lived in a
    DIFFERENT field from the shipped sine and could not be added to it; it
    survives the consolidation for the better reason."""
    index = _lcm4(n)
    omega = Qalg.alpha(_phi(index))
    k = index // n
    return (omega ** k + omega ** (index - k)) * Q(1, 2)


# ── the pinned anchor ────────────────────────────────────────────────────────
def test_n8_cosine_anchor_is_exact():
    """n = 8 pinned coordinate-for-coordinate: ``cos(π/4) = √2/2`` is
    ``(ζ₈ − ζ₈³)/2`` over ``Φ₈ = x⁴ + 1``. ``lcm(8, 4) = 8``, so this is the
    same field and the same coordinates the removed ``cos_2pi_over_n(8)``
    returned — the removal moved no value here."""
    c = _cos(8)
    assert c.m == (1, 0, 0, 0, 1)
    assert c.coords == (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2))
    assert c.is_rational() is False
    assert c.as_rational() is None
    assert c.root is None            # no embedding attached — no FPU touched
    assert c == Qalg((1, 0, 0, 0, 1),
                     (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2)))


def test_n8_sine_shares_the_field_and_the_value():
    """At n = 8 the two values coincide, because ``sin(π/4) = cos(π/4)``. A
    real coincidence worth pinning: it is the one index where an implementation
    that returned the cosine for the sine slot would look right, so every
    other n below is what actually separates them."""
    c, s = cos_sin_2pi_k_over_n(8)
    assert s.m == (1, 0, 0, 0, 1)
    assert s.coords == (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2))
    assert s.is_rational() is False
    assert s == c


# ── defining algebraic relations, asserted on exact coordinates ──────────────
@pytest.mark.parametrize("n, constant", [(8, 2), (12, 3)])
def test_two_cos_is_a_root_of_x2_minus_constant(n, constant):
    """``2·cos(2π/8) = √2`` and ``2·cos(2π/12) = √3``: each is a root of
    ``x² − c``, so the exact field element ``(2c)² − c`` must be the ZERO
    element — every coordinate exactly ``Q(0, 1)``."""
    residual = (_cos(n) * 2) ** 2 - constant
    assert _is_exactly_zero(residual)
    assert residual == 0
    assert not residual                      # __bool__ agrees with the coords


def test_two_cos_2pi_over_5_is_a_root_of_x2_plus_x_minus_1():
    """``2·cos(2π/5) = (√5 − 1)/2`` is a root of ``x² + x − 1``. Asserted on
    the exact coordinates over ``Φ₂₀``, not on a float.

    ⚠️ The DEGREE is 8, not the 4 the removed ``cos_2pi_over_n`` gave: that op
    answered over ``Φ₅`` and this one over ``Φ_lcm(5,4) = Φ₂₀``. The value is
    the same algebraic number and the relation is the same relation; only the
    field it is expressed in is the larger one that also carries ``i``, which
    is exactly what buys the two values a common home."""
    two_c = _cos(5) * 2
    residual = two_c ** 2 + two_c - 1
    assert two_c.degree == 8
    assert _is_exactly_zero(residual)
    assert residual == 0


def test_two_sin_2pi_over_3_is_a_root_of_x2_minus_3():
    """``2·sin(2π/3) = √3`` ⇒ ``(2s)² − 3 = 0`` exactly.

    This is a factor-of-``i`` detector as well as an exactness check: the
    rejected ``(ζ − ζ⁻¹)/2 = i·sin`` construction squares to ``−3``, so it
    would fail here by a sign, not by a rounding."""
    residual = (_sin(3) * 2) ** 2 - 3
    assert _is_exactly_zero(residual)
    assert (_sin(3) * 2) ** 2 == 3


def test_sin_2pi_over_5_is_a_root_of_16x4_minus_20x2_plus_5():
    """``sin(2π/5)`` is a root of ``16x⁴ − 20x² + 5``, exactly, in ℚ(ζ₂₀).

    ``i·sin(2π/5)`` is a root of ``16x⁴ + 20x² + 5`` instead, so this relation
    also fails loudly for the rejected construction."""
    s = _sin(5)
    assert s.m == _phi(20)
    residual = (s ** 4) * 16 - (s ** 2) * 20 + 5
    assert _is_exactly_zero(residual)
    assert residual == 0


@pytest.mark.parametrize(
    "n", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 18, 20, 24, 30, 36])
def test_pythagorean_identity_holds_at_EVERY_n(n):
    """``cos² + sin² == 1`` on the SHIPPED pair, at every n — including the
    ``4 ∤ n`` indices where the two removed rc463 ops lived in different fields
    and ``Qalg`` correctly REFUSED to add them. That refusal is what this
    consolidation removed, and this row is the removal's whole content.

    Exact field equality — no tolerance exists here to hide in."""
    c, s = cos_sin_2pi_k_over_n(n)
    assert c.m == s.m == _phi(_lcm4(n))
    assert c * c + s * s == 1


@pytest.mark.parametrize(
    "n", [1, 2, 3, 5, 6, 7, 9, 10, 11, 12, 13, 15, 18, 20, 30, 36])
def test_pythagorean_identity_against_an_INDEPENDENT_cosine(n):
    """The same identity with the cosine rebuilt from ``Qalg.alpha`` rather
    than read off the op — so a constructor that returned two mutually
    consistent WRONG values could not pass both this and the row above.

    This is the load-bearing "it really is the sine" gate. ``i·sin`` would give
    ``cos² − sin² = cos(4π/n)``, which equals 1 only at n = 1 and n = 2."""
    c_shipped, s = cos_sin_2pi_k_over_n(n)
    c = _independent_cos(n)
    assert c.m == s.m
    assert c == c_shipped
    assert c * c + s * s == 1


# ── the general turn ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("n, k", [(8, 3), (12, 5), (5, 2), (16, 7), (7, 3)])
def test_the_general_turn_closes_on_the_root_of_unity(n, k):
    """``(cos(2πk/n) + i·sin(2πk/n))**n == 1`` exactly, with ``i = ζ_N^(N/4)``
    read out of the SAME field. The removed k = 1 ops could not state this at
    any turn but ``1/n``, which is the second thing this constructor adds."""
    index = _lcm4(n)
    c, s = cos_sin_2pi_k_over_n(n, k)
    i = Qalg.alpha(_phi(index)) ** (index // 4)
    assert (c + s * i) ** n == c.one()


@pytest.mark.parametrize("n", [3, 5, 8, 12])
def test_the_turn_numerator_is_reduced_in_Z_n_and_negated_by_chirality(n):
    """``k`` is reduced in ``Z_n`` FIRST (Class I, exactly), so ``k`` may be any
    int; and ``−k`` is the CONJUGATE turn — the cosine is even, the sine odd.
    The sign is a Class-K pin-slot through ``Qalg.__neg__``, never an ``abs``."""
    base_c, base_s = cos_sin_2pi_k_over_n(n, 1)
    assert cos_sin_2pi_k_over_n(n, 1 + n) == (base_c, base_s)
    assert cos_sin_2pi_k_over_n(n, 1 - 2 * n) == (base_c, base_s)
    conj_c, conj_s = cos_sin_2pi_k_over_n(n, -1)
    assert conj_c == base_c
    assert conj_s == -base_s


def test_k_defaults_to_the_plain_turn():
    """``k`` defaults to 1 — the ``2π/n`` turn the two removed rc463
    constructors answered at, and the reason they were duplicates of this op
    rather than peers of it."""
    for n in (3, 4, 5, 8, 12, 16):
        assert cos_sin_2pi_k_over_n(n) == cos_sin_2pi_k_over_n(n, 1)


# ── the field contract ───────────────────────────────────────────────────────
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 16, 20])
def test_field_is_phi_lcm_n_4_for_BOTH(n):
    """BOTH values live over ``Φ_lcm(n,4)``. Pinned against
    ``cyclotomic_polynomial`` directly, so a wrong field is a failure rather
    than a surprise at the call site."""
    c, s = cos_sin_2pi_k_over_n(n)
    expected = _phi(_lcm4(n))
    assert c.m == expected
    assert s.m == expected
    assert c.degree == cyclotomic_polynomial(_lcm4(n))["degree"]
    assert s.degree == c.degree


def test_the_two_values_now_share_ONE_field_at_every_n():
    """⚠️ THE INVERTED TEST. Through rc467 this file asserted that the cosine
    and the sine returned elements of DIFFERENT fields whenever ``4 ∤ n``, and
    that ``Qalg``'s cross-field guard REFUSED to combine them. That was true,
    and it was the defect: a cosine that could not be added to its own sine.

    The guard itself is unchanged and still fires — proved below against a
    genuinely foreign field, so this row is not asserting that a guard was
    weakened. What changed is that the two shipped values no longer trip it."""
    c, s = cos_sin_2pi_k_over_n(5)
    assert c.m == s.m
    assert (c + s).m == c.m
    assert (c * s).m == c.m
    # the guard is intact: a genuinely different field still refuses
    other = cos_sin_2pi_k_over_n(3)[0]
    assert other.m != c.m
    with pytest.raises(ValueError, match="requires equal m"):
        _ = c + other
    with pytest.raises(ValueError, match="requires equal m"):
        _ = c * other


# ── the rationality verdict (measured, then pinned) ──────────────────────────
def test_cosine_rationality_census_is_nivens_theorem():
    """The cosine half is rational over n = 1..24 for exactly ``{1, 2, 3, 4, 6}``
    — the classical rational-cosine set. Measured on this tree, and UNMOVED by
    the consolidation: rationality is a property of the VALUE, not of the field
    it is expressed in, so widening ``Φ_n`` to ``Φ_lcm(n,4)`` cannot change it.
    That invariance is itself the check."""
    rational = [n for n in range(1, 25) if _cos(n).is_rational()]
    assert rational == [1, 2, 3, 4, 6]


def test_sine_rationality_census_is_a_different_set():
    """The sine half is rational for exactly ``{1, 2, 4, 12}``. The two censuses
    genuinely differ — n = 12 is rational for the sine and irrational for the
    cosine, n = 3 and n = 6 the other way round — so the two halves of the pair
    cannot be quietly substituted for each other."""
    rational = [n for n in range(1, 25) if _sin(n).is_rational()]
    assert rational == [1, 2, 4, 12]
    assert _sin(12).is_rational() is True
    assert _cos(12).is_rational() is False
    assert _cos(3).is_rational() is True
    assert _sin(3).is_rational() is False


@pytest.mark.parametrize("n", [5, 8, 12])
def test_cosine_is_irrational_at_5_8_12(n):
    assert _cos(n).is_rational() is False
    assert _cos(n).as_rational() is None


@pytest.mark.parametrize("n, value", [
    (1, Q(1, 1)),           # cos(2π)   =  1
    (2, Q(-1, 1)),          # cos(π)    = -1
    (3, Q(-1, 2)),          # cos(2π/3) = -1/2
    (4, Q(0, 1)),           # cos(π/2)  =  0
    (6, Q(1, 2)),           # cos(π/3)  =  1/2
])
def test_degenerate_cosines_are_exact_rationals(n, value):
    """The five rational cosines, pinned to their exact ``Q`` values."""
    c = _cos(n)
    assert c.is_rational() is True
    assert c.as_rational() == value
    assert c == value


@pytest.mark.parametrize("n, value", [
    (1, Q(0, 1)),           # sin(2π)   = 0
    (2, Q(0, 1)),           # sin(π)    = 0
    (4, Q(1, 1)),           # sin(π/2)  = 1
    (12, Q(1, 2)),          # sin(π/6)  = 1/2
])
def test_degenerate_sines_are_exact_rationals(n, value):
    """The four rational sines. ``n = 4`` and ``n = 12`` are the sharpest
    factor-of-``i`` detectors in the file: ``i·sin`` would be ``i`` and
    ``i/2``, neither of which is rational at all, so ``is_rational()`` would
    read False rather than returning a wrong number."""
    s = _sin(n)
    assert s.is_rational() is True
    assert s.as_rational() == value
    assert s == value


# ── negative controls: every refusal is reachable ────────────────────────────
@pytest.mark.parametrize("bad", [0, -1, -8])
def test_refuses_indices_below_one(bad):
    with pytest.raises(ValueError, match="requires n >= 1"):
        cos_sin_2pi_k_over_n(bad)


@pytest.mark.parametrize("bad", [True, False, 2.0, "8", None, Q(8, 1), (8,)])
def test_refuses_non_int_indices(bad):
    """``bool`` is refused explicitly: ``True`` is not the index 1. A float is
    refused even when integral — ``2.0`` is the FPU's spelling of 2 and this
    op's whole contract is that no float enters."""
    with pytest.raises(TypeError, match="n must be a plain int"):
        cos_sin_2pi_k_over_n(bad)


@pytest.mark.parametrize("bad", [True, False, 2.0, "3", None, Q(3, 1), (3,)])
def test_refuses_a_non_int_turn_numerator(bad):
    """The SECOND operand gets the same treatment, and it needs its own row:
    ``k`` is reduced mod ``n`` and a float would be silently truncated by any
    modulus arithmetic that accepted it."""
    with pytest.raises(TypeError, match="k must be a plain int"):
        cos_sin_2pi_k_over_n(8, bad)


def test_refuses_above_the_measured_cap():
    """The degree cap is a REACHABLE refusal, and the last accepted index is
    accepted — an instrument that only ever raises is not a measurement."""
    assert MAX_CYCLOTOMIC_INDEX == 256
    with pytest.raises(ValueError, match="requires n <= 256"):
        cos_sin_2pi_k_over_n(MAX_CYCLOTOMIC_INDEX + 1)
    c, s = cos_sin_2pi_k_over_n(MAX_CYCLOTOMIC_INDEX)
    assert c.degree > 0
    assert s.degree == c.degree


# ── terminal projection (SANITY CHECK ONLY — not the exactness evidence) ─────
def test_projection_to_float_is_a_sanity_check_not_the_assertion():
    """A terminal-projection cross-check via ``Qalg.to_complex()``.

    THIS IS A PROJECTION CHECK, NOT THE EXACTNESS ASSERTION. Everything above
    asserts on exact ``Q`` coordinates; this one exists only to confirm the
    exact elements land where a reader's intuition says they should. It uses
    tolerances, which is exactly why it cannot be the evidence for anything.

    ``n = 4`` needs no transcendental at all — the field is ``Φ₄ = x² + 1`` and
    the embedding root is the literal ``1j``. ``n = 8`` uses a literal float
    for ``ζ₈``; no ``math`` module is imported anywhere in this file."""
    # n = 4: root is exactly 1j, so the projection is exact too.
    c4, s4 = cos_sin_2pi_k_over_n(4)
    assert c4.with_root(1j).to_complex() == 0j
    assert s4.with_root(1j).to_complex() == 1 + 0j

    # n = 8: ζ₈ = (√2/2)(1 + i), as a literal.
    half_root_two = 0.7071067811865476
    zeta8 = complex(half_root_two, half_root_two)
    c8, s8 = cos_sin_2pi_k_over_n(8)
    for projected in (c8.with_root(zeta8).to_complex(),
                      s8.with_root(zeta8).to_complex()):
        assert -1e-12 < projected.real - half_root_two < 1e-12
        assert -1e-12 < projected.imag < 1e-12


# ── the op stays inside the exact carrier ────────────────────────────────────
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20])
def test_no_embedding_root_is_attached_and_coords_are_all_Q(n):
    """No embedding root is attached, because computing ``e^(2πi/n)`` is
    precisely the FPU transcendental this op exists to avoid. Every coordinate
    is an exact ``Q``, never a float."""
    for element in cos_sin_2pi_k_over_n(n):
        assert element.root is None
        assert all(isinstance(c, Q) for c in element.coords)
        assert len(element.coords) == element.degree
        with pytest.raises(ValueError, match="requires an embedding root"):
            element.to_complex()


# ── the removal itself ───────────────────────────────────────────────────────
def test_the_two_absorbed_ops_are_GONE_with_no_alias():
    """rc468 (`#T1188`) — removal means removal. Neither absorbed name resolves
    as an attribute, neither is importable, and neither is in ``__all__``.

    A shim, an alias or a deprecation wrapper would have left the duplicate op
    in the tree under a quieter name, which is the thing the maintainer's
    ruling forbids: ONE op serves every carrier."""
    import srmech.math.qalg as qalg

    for gone in ("cos_2pi_over_n", "sin_2pi_over_n"):
        assert not hasattr(qalg, gone), gone
        assert gone not in qalg.__all__, gone
    assert "cos_sin_2pi_k_over_n" in qalg.__all__
    with pytest.raises(ImportError):
        from srmech.math.qalg import cos_2pi_over_n  # noqa: F401
    with pytest.raises(ImportError):
        from srmech.math.qalg import sin_2pi_over_n  # noqa: F401
