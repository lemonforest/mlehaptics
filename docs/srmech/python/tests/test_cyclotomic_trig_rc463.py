"""Gate for the rc463 cyclotomic trig constructors (`#T1188`).

``srmech.math.qalg.cos_2pi_over_n`` / ``sin_2pi_over_n`` return ``cos(2π/n)``
and ``sin(2π/n)`` as EXACT number-field elements. The whole point of the pair
is that the value is CONSTRUCTED in the field it already lives in rather than
floated and then rationalised, so every assertion here that carries the claim
is an assertion on exact ``Q`` coordinates or on an exact field identity.
Exactly one test projects to a float, and it is labelled as a projection
sanity check, not as the exactness evidence.

Three things this file is built to catch:

1. **A silently wrong field.** ``sin(2π/n)`` is generally NOT in ℚ(ζ_n) — the
   op works over ``Φ_lcm(n,4)``. :func:`test_field_is_phi_lcm_n_4` pins the
   minimal polynomial of both ops against ``cyclotomic_polynomial`` directly.
2. **A function named ``sin`` that answers ``i·sin``.** The rejected cheap
   construction ``(ζ − ζ⁻¹)/2`` differs from the shipped one by a factor of
   ``i``, which no float-free coordinate check would notice *unless* it is a
   check the factor of ``i`` breaks. Three do: the Pythagorean identity, the
   exact rational values at ``n = 4`` and ``n = 12``, and the minimal-
   polynomial relations (``i·sin`` satisfies the same polynomial with the
   sign of every odd-degree-in-``x²`` term flipped).
3. **A guard that cannot fire.** Every refusal asserted below is reachable.

No numpy. No ``fractions`` (the exact scalar is ``srmech.math.q.Q``). No
``abs``. No ``math``.
"""

import pytest

from srmech.math.poly import cyclotomic_polynomial
from srmech.math.q import Q
from srmech.math.qalg import (
    MAX_CYCLOTOMIC_INDEX,
    Qalg,
    cos_2pi_over_n,
    sin_2pi_over_n,
)

ZERO = Q(0, 1)


def _phi(index):
    """``Φ_index`` as the ascending int tuple ``Qalg`` uses for ``m``."""
    return tuple(cyclotomic_polynomial(index)["coefficients"])


def _is_exactly_zero(element):
    """True when EVERY coordinate is the exact rational zero. This is the
    exactness assertion the float-free relations below hang on: it reads the
    ``Q`` coordinates, never a magnitude and never a tolerance."""
    return element.coords == tuple(ZERO for _ in range(element.degree))


def _lcm4(n):
    """``lcm(n, 4)`` — the field index :func:`sin_2pi_over_n` works over."""
    a, b = n, 4
    while b:
        a, b = b, a % b
    return 4 * n // a


def _lifted_cos(n):
    """``cos(2π/n)`` rebuilt over ``Φ_lcm(n,4)`` from public parts only, so it
    shares a field with ``sin_2pi_over_n(n)`` for EVERY n (not just ``4 | n``).
    Deliberately built from ``Qalg.alpha`` + ``cyclotomic_polynomial`` rather
    than from ``cos_2pi_over_n``, so the Pythagorean gate below is a check ON
    the shipped sine rather than a check of the two shipped ops against each
    other."""
    index = _lcm4(n)
    omega = Qalg.alpha(_phi(index))
    k = index // n
    return (omega ** k + omega ** (index - k)) * Q(1, 2)


# ── the pinned anchor ────────────────────────────────────────────────────────
def test_n8_cosine_anchor_is_exact():
    """n = 8 pinned coordinate-for-coordinate: ``cos(π/4) = √2/2`` is
    ``(ζ₈ − ζ₈³)/2`` over ``Φ₈ = x⁴ + 1``."""
    c = cos_2pi_over_n(8)
    assert c.m == (1, 0, 0, 0, 1)
    assert c.coords == (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2))
    assert c.is_rational() is False
    assert c.as_rational() is None
    assert c.root is None            # no embedding attached — no FPU touched
    assert c == Qalg((1, 0, 0, 0, 1),
                     (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2)))


def test_n8_sine_shares_the_field_and_the_value():
    """``lcm(8, 4) = 8``, so the sine lands in the SAME ``Φ₈`` as the cosine —
    and at n = 8 the two values coincide, because ``sin(π/4) = cos(π/4)``. A
    real coincidence worth pinning: it is the one index where an implementation
    that returned the cosine from ``sin_2pi_over_n`` would look right, so every
    other n below is what actually separates them."""
    s = sin_2pi_over_n(8)
    assert s.m == (1, 0, 0, 0, 1)
    assert s.coords == (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2))
    assert s.is_rational() is False
    assert s == cos_2pi_over_n(8)


# ── defining algebraic relations, asserted on exact coordinates ──────────────
@pytest.mark.parametrize("n, constant", [(8, 2), (12, 3)])
def test_two_cos_is_a_root_of_x2_minus_constant(n, constant):
    """``2·cos(2π/8) = √2`` and ``2·cos(2π/12) = √3``: each is a root of
    ``x² − c``, so the exact field element ``(2c)² − c`` must be the ZERO
    element — every coordinate exactly ``Q(0, 1)``."""
    residual = (cos_2pi_over_n(n) * 2) ** 2 - constant
    assert _is_exactly_zero(residual)
    assert residual == 0
    assert not residual                      # __bool__ agrees with the coords


def test_two_cos_2pi_over_5_is_a_root_of_x2_plus_x_minus_1():
    """``2·cos(2π/5) = (√5 − 1)/2`` is a root of ``x² + x − 1``. Asserted on
    the exact quartic coordinates over ``Φ₅``, not on a float."""
    two_c = cos_2pi_over_n(5) * 2
    residual = two_c ** 2 + two_c - 1
    assert residual.degree == 4
    assert _is_exactly_zero(residual)
    assert residual == 0


def test_two_sin_2pi_over_3_is_a_root_of_x2_minus_3():
    """``2·sin(2π/3) = √3`` ⇒ ``(2s)² − 3 = 0`` exactly.

    This is a factor-of-``i`` detector as well as an exactness check: the
    rejected ``(ζ − ζ⁻¹)/2 = i·sin`` construction squares to ``−3``, so it
    would fail here by a sign, not by a rounding."""
    residual = (sin_2pi_over_n(3) * 2) ** 2 - 3
    assert _is_exactly_zero(residual)
    assert (sin_2pi_over_n(3) * 2) ** 2 == 3


def test_sin_2pi_over_5_is_a_root_of_16x4_minus_20x2_plus_5():
    """``sin(2π/5)`` is a root of ``16x⁴ − 20x² + 5``, exactly, in ℚ(ζ₂₀).

    ``i·sin(2π/5)`` is a root of ``16x⁴ + 20x² + 5`` instead, so this relation
    also fails loudly for the rejected construction."""
    s = sin_2pi_over_n(5)
    assert s.m == _phi(20)
    residual = (s ** 4) * 16 - (s ** 2) * 20 + 5
    assert _is_exactly_zero(residual)
    assert residual == 0


@pytest.mark.parametrize("n", [4, 8, 12, 16, 20, 24])
def test_pythagorean_identity_in_the_shared_field(n):
    """For ``4 | n`` the two shipped ops live in the SAME field, so
    ``cos² + sin² == 1`` composes directly on the shipped values. Exact field
    equality — no tolerance exists here to hide in."""
    c, s = cos_2pi_over_n(n), sin_2pi_over_n(n)
    assert c.m == s.m
    assert c * c + s * s == 1


@pytest.mark.parametrize(
    "n", [1, 2, 3, 5, 6, 7, 9, 10, 11, 12, 13, 15, 18, 20, 30, 36])
def test_pythagorean_identity_against_a_lifted_cosine(n):
    """The same identity for EVERY n, including ``4 ∤ n`` where the two ops do
    not share a field: the cosine is rebuilt over ``Φ_lcm(n,4)`` from
    ``Qalg.alpha`` and the identity is checked there.

    This is the load-bearing "it really is the sine" gate. ``i·sin`` would give
    ``cos² − sin² = cos(4π/n)``, which equals 1 only at n = 1 and n = 2."""
    s = sin_2pi_over_n(n)
    c = _lifted_cos(n)
    assert c.m == s.m
    assert c * c + s * s == 1


# ── the field contract ───────────────────────────────────────────────────────
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 16, 20])
def test_field_is_phi_lcm_n_4(n):
    """The cosine lives over ``Φ_n``; the sine over ``Φ_lcm(n,4)``. Pinned
    against ``cyclotomic_polynomial`` directly, so a wrong field is a failure
    rather than a surprise at the call site."""
    assert cos_2pi_over_n(n).m == _phi(n)
    assert sin_2pi_over_n(n).m == _phi(_lcm4(n))
    assert cos_2pi_over_n(n).degree == cyclotomic_polynomial(n)["degree"]


def test_fields_differ_when_four_does_not_divide_n():
    """When ``4 ∤ n`` the two ops return elements of DIFFERENT fields, and
    ``Qalg``'s cross-field guard refuses to combine them. Asserted rather than
    documented, because a caller who mixes them silently would be the whole
    hazard of this design."""
    c, s = cos_2pi_over_n(5), sin_2pi_over_n(5)
    assert c.m != s.m
    with pytest.raises(ValueError, match="requires equal m"):
        _ = c + s
    with pytest.raises(ValueError, match="requires equal m"):
        _ = c * s


# ── the rationality verdict (measured, then pinned) ──────────────────────────
def test_cosine_rationality_census_is_nivens_theorem():
    """``cos_2pi_over_n(n).is_rational()`` over n = 1..24 is True for exactly
    ``{1, 2, 3, 4, 6}`` — the classical rational-cosine set. Measured on this
    tree before it was written down."""
    rational = [n for n in range(1, 25) if cos_2pi_over_n(n).is_rational()]
    assert rational == [1, 2, 3, 4, 6]


def test_sine_rationality_census_is_a_different_set():
    """``sin_2pi_over_n(n).is_rational()`` over n = 1..24 is True for exactly
    ``{1, 2, 4, 12}``. The two censuses genuinely differ — n = 12 is rational
    for the sine and irrational for the cosine, n = 3 and n = 6 the other way
    round — so neither op can be quietly substituted for the other."""
    rational = [n for n in range(1, 25) if sin_2pi_over_n(n).is_rational()]
    assert rational == [1, 2, 4, 12]
    assert sin_2pi_over_n(12).is_rational() is True
    assert cos_2pi_over_n(12).is_rational() is False
    assert cos_2pi_over_n(3).is_rational() is True
    assert sin_2pi_over_n(3).is_rational() is False


@pytest.mark.parametrize("n", [5, 8, 12])
def test_cosine_is_irrational_at_5_8_12(n):
    assert cos_2pi_over_n(n).is_rational() is False
    assert cos_2pi_over_n(n).as_rational() is None


@pytest.mark.parametrize("n, value", [
    (1, Q(1, 1)),           # cos(2π)   =  1
    (2, Q(-1, 1)),          # cos(π)    = -1
    (3, Q(-1, 2)),          # cos(2π/3) = -1/2
    (4, Q(0, 1)),           # cos(π/2)  =  0
    (6, Q(1, 2)),           # cos(π/3)  =  1/2
])
def test_degenerate_cosines_are_exact_rationals(n, value):
    """The five rational cosines, pinned to their exact ``Q`` values."""
    c = cos_2pi_over_n(n)
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
    s = sin_2pi_over_n(n)
    assert s.is_rational() is True
    assert s.as_rational() == value
    assert s == value


# ── negative controls: every refusal is reachable ────────────────────────────
@pytest.mark.parametrize("op", [cos_2pi_over_n, sin_2pi_over_n])
@pytest.mark.parametrize("bad", [0, -1, -8])
def test_refuses_indices_below_one(op, bad):
    with pytest.raises(ValueError, match="requires n >= 1"):
        op(bad)


@pytest.mark.parametrize("op", [cos_2pi_over_n, sin_2pi_over_n])
@pytest.mark.parametrize("bad", [True, False, 2.0, "8", None, Q(8, 1), (8,)])
def test_refuses_non_int_indices(op, bad):
    """``bool`` is refused explicitly: ``True`` is not the index 1. A float is
    refused even when integral — ``2.0`` is the FPU's spelling of 2 and this
    op's whole contract is that no float enters."""
    with pytest.raises(TypeError, match="must be a plain int"):
        op(bad)


@pytest.mark.parametrize("op", [cos_2pi_over_n, sin_2pi_over_n])
def test_refuses_above_the_measured_cap(op):
    """The degree cap is a REACHABLE refusal, and the last accepted index is
    accepted — an instrument that only ever raises is not a measurement."""
    assert MAX_CYCLOTOMIC_INDEX == 256
    with pytest.raises(ValueError, match="requires n <= 256"):
        op(MAX_CYCLOTOMIC_INDEX + 1)
    accepted = op(MAX_CYCLOTOMIC_INDEX)
    assert accepted.degree > 0


# ── terminal projection (SANITY CHECK ONLY — not the exactness evidence) ─────
def test_projection_to_float_is_a_sanity_check_not_the_assertion():
    """A terminal-projection cross-check via ``Qalg.to_complex()``.

    THIS IS A PROJECTION CHECK, NOT THE EXACTNESS ASSERTION. Everything above
    asserts on exact ``Q`` coordinates; this one exists only to confirm the
    exact elements land where a reader's intuition says they should. It uses
    tolerances, which is exactly why it cannot be the evidence for anything.

    ``n = 4`` needs no transcendental at all — the embedding root of
    ``Φ₄ = x² + 1`` is the literal ``1j``. ``n = 8`` uses a literal float for
    ``ζ₈``; no ``math`` module is imported anywhere in this file."""
    # n = 4: root is exactly 1j, so the projection is exact too.
    assert cos_2pi_over_n(4).with_root(1j).to_complex() == 0j
    assert sin_2pi_over_n(4).with_root(1j).to_complex() == 1 + 0j

    # n = 8: ζ₈ = (√2/2)(1 + i), as a literal.
    half_root_two = 0.7071067811865476
    zeta8 = complex(half_root_two, half_root_two)
    c = cos_2pi_over_n(8).with_root(zeta8).to_complex()
    s = sin_2pi_over_n(8).with_root(zeta8).to_complex()
    for projected in (c, s):
        assert -1e-12 < projected.real - half_root_two < 1e-12
        assert -1e-12 < projected.imag < 1e-12


# ── the ops stay inside the exact carrier ────────────────────────────────────
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20])
def test_no_embedding_root_is_attached_and_coords_are_all_Q(n):
    """Neither op attaches an embedding root, because computing ``e^(2πi/n)``
    is precisely the FPU transcendental the pair exists to avoid. Every
    coordinate is an exact ``Q``, never a float."""
    for element in (cos_2pi_over_n(n), sin_2pi_over_n(n)):
        assert element.root is None
        assert all(isinstance(c, Q) for c in element.coords)
        assert len(element.coords) == element.degree
        with pytest.raises(ValueError, match="requires an embedding root"):
            element.to_complex()
