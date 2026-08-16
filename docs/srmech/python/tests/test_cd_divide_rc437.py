"""rc437 (`#T1142`) — the Cayley–Dickson division PAIR, and the wrong
implementation it exists to keep out of the tree.

THE GATE THAT MATTERS IS :func:`test_the_dim16_zero_divisor_is_REFUSED`.
Everything else here is round-trip hygiene. That one test is the reason the ops
are built on the operator rather than on the conjugate closed form, because the
closed form gets exactly that case silently wrong: it divides by a perfectly
good norm (``N(e₁+e₁₀) = 2``) and RETURNS a value which is not a solution. If
anyone later "simplifies" ``cd_left_divide`` back to ``conj(a)·c/N(a)``, this
file must go red, and :func:`test_the_conjugate_closed_form_control` proves it
would by executing the rival right here.

WHY THE OBVIOUS PROBE CANNOT SEE ANY OF THIS. A probe built from ``a = 1 + eᵢ``
scores ZERO failures for the rival at every dim including 32 — those elements
are near-unit, and the rival's error is a norm factor. Every generative test
below therefore draws GENERIC elements, and
:func:`test_the_near_unit_probe_is_non_discriminating` pins that the naive probe
is blind, so nobody re-derives it later and concludes the rival is fine.
"""
from __future__ import annotations

import random

import pytest

from srmech.cascade.cayley_dickson import (
    algebra_table,
    cd_conjugate,
    cd_left_divide,
    cd_mult,
    cd_norm_sq,
    cd_right_divide,
    cd_zero_divisor_witness,
    left_mult_matrix,
    right_mult_matrix,
)
from srmech.math.q import Q

DIMS = (2, 4, 8, 16, 32)


def _rand(dim: int, rng: random.Random, lo: int = -3, hi: int = 3):
    """A GENERIC element — deliberately not near-unit (see the module docstring)."""
    while True:
        v = tuple(Q(rng.randint(lo, hi)) for _ in range(dim))
        if any(x != 0 for x in v):
            return v


def _conj_left_divide(a, c):
    """THE RIVAL, executed rather than described: ``conj(a)·c / N(a)``."""
    n = cd_norm_sq(a)
    return tuple(v / n for v in cd_mult(cd_conjugate(a), c))


# ──────────────────────────────────────────────────────────────────────
# 1. The refusal — the case the rival gets silently wrong.
# ──────────────────────────────────────────────────────────────────────

def test_the_dim16_zero_divisor_is_REFUSED() -> None:
    """⚠️ THE LOAD-BEARING GATE. ``x = e₁+e₁₀`` has ``N(x) = 2 ≠ 0`` and a
    left-multiplication kernel of dimension 4, so it is invertible-looking to
    anything that only inspects the norm. Both halves must RAISE."""
    w = cd_zero_divisor_witness(16)
    x, y = w["x"], w["y"]
    assert cd_norm_sq(x) != 0, "the witness must have a NONZERO norm, or the gate is trivial"
    c = tuple(Q(i % 5) for i in range(16))

    with pytest.raises(ValueError, match="zero divisor"):
        cd_left_divide(x, c)
    with pytest.raises(ValueError, match="zero divisor"):
        cd_right_divide(c, y)


def test_the_conjugate_closed_form_control() -> None:
    """⚠️ NON-VACUITY for the gate above: prove the rival really does answer
    where the shipped op refuses, so the refusal is a CHOICE and not an accident
    of the input being degenerate."""
    w = cd_zero_divisor_witness(16)
    x = w["x"]
    c = tuple(Q(i % 5) for i in range(16))

    rival = _conj_left_divide(x, c)          # returns; no raise
    assert tuple(cd_mult(x, rival)) != tuple(c), (
        "the rival must return a NON-solution here — that is the whole defect")


def test_zero_divisor_at_dim8_on_a_SPLIT_table() -> None:
    """The ``table`` argument reaches algebras whose wall arrives earlier than
    the ladder's own: split-𝕆 has a zero divisor at dim 8."""
    split8 = algebra_table(8, gammas=[1, 1, 1])
    zd = tuple(Q(1) if k in (0, 1) else Q(0) for k in range(8))
    c = tuple(Q(1) for _ in range(8))
    with pytest.raises(ValueError, match="zero divisor"):
        cd_left_divide(zd, c, table=split8)


def test_zero_operand_is_refused_not_answered() -> None:
    zero = tuple(Q(0) for _ in range(8))
    c = tuple(Q(1) for _ in range(8))
    with pytest.raises(ValueError):
        cd_left_divide(zero, c)
    with pytest.raises(ValueError):
        cd_right_divide(c, zero)


def test_mismatched_dimensions_are_refused() -> None:
    with pytest.raises(ValueError, match="same algebra"):
        cd_left_divide([1, 0, 0, 0], [1, 0])
    with pytest.raises(ValueError, match="same algebra"):
        cd_right_divide([1, 0, 0, 0], [1, 0])


# ──────────────────────────────────────────────────────────────────────
# 2. Round-trip on GENERIC elements.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", DIMS)
def test_left_divide_round_trip(dim: int) -> None:
    rng = random.Random(1142 + dim)
    for _ in range(12):
        a, b = _rand(dim, rng), _rand(dim, rng)
        try:
            q = cd_left_divide(a, cd_mult(a, b))
        except ValueError:
            continue                          # a is a zero divisor: refusal is correct
        assert q == tuple(b)
        assert tuple(cd_mult(a, q)) == tuple(cd_mult(a, b))


@pytest.mark.parametrize("dim", DIMS)
def test_right_divide_round_trip(dim: int) -> None:
    rng = random.Random(9142 + dim)
    for _ in range(12):
        a, b = _rand(dim, rng), _rand(dim, rng)
        try:
            q = cd_right_divide(cd_mult(b, a), a)
        except ValueError:
            continue
        assert q == tuple(b)


# ──────────────────────────────────────────────────────────────────────
# 3. The rival's actual failure profile — measured, not asserted.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim,rival_is_right", [(2, True), (4, True), (8, True),
                                                (16, False), (32, False)])
def test_the_rival_is_right_below_the_wall_and_wrong_above_it(
        dim: int, rival_is_right: bool) -> None:
    """The NORMALISED conjugate form needs ALTERNATIVITY, which dies at 𝕊. So it
    is exactly right at dims ≤ 8 and exactly wrong at 16 and 32 — measured on
    GENERIC elements, which is the only draw that can tell."""
    rng = random.Random(4370 + dim)
    agree = 0
    trials = 12
    for _ in range(trials):
        a, b = _rand(dim, rng), _rand(dim, rng)
        if cd_norm_sq(a) == 0:
            continue
        if _conj_left_divide(a, cd_mult(a, b)) == tuple(b):
            agree += 1
    if rival_is_right:
        assert agree == trials, f"dim {dim}: expected the rival to agree everywhere"
    else:
        assert agree == 0, (
            f"dim {dim}: the rival agreed {agree}/{trials} times — it must fail "
            f"EVERYWHERE above the alternativity wall")


@pytest.mark.parametrize("dim", (8, 16, 32))
def test_the_near_unit_probe_is_non_discriminating(dim: int) -> None:
    """⚠️ THE METHOD GATE. ``a = 1 + eᵢ`` makes the rival look correct at EVERY
    dim, including the two where it is wrong. Pinned so that a later
    re-measurement built on this shape is recognisably blind rather than
    reassuring."""
    misses = 0
    for i in range(1, dim):
        a = tuple(Q(1) if k in (0, i) else Q(0) for k in range(dim))
        for j in range(dim):
            b = tuple(Q(1) if k == j else Q(0) for k in range(dim))
            if _conj_left_divide(a, cd_mult(a, b)) != tuple(b):
                misses += 1
    assert misses == 0, (
        f"dim {dim}: the near-unit probe caught {misses} rival failures — if "
        f"this ever becomes nonzero the probe stopped being non-discriminating "
        f"and this test's PURPOSE (documenting a blind probe) has changed")


# ──────────────────────────────────────────────────────────────────────
# 4. Why the pair is TWO ops (Class C), measured rather than asserted.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", (4, 8, 16, 32))
def test_R_is_not_L_and_not_L_transposed(dim: int) -> None:
    """The right-regular representation is a genuinely different operator. If it
    were ``L`` or ``Lᵀ`` the second op would be sugar and the Class-C reading
    would be decoration."""
    rng = random.Random(770 + dim)
    for _ in range(8):
        x = _rand(dim, rng)
        L, R = left_mult_matrix(x), right_mult_matrix(x)
        assert L != R
        assert [[L[c][r] for c in range(dim)] for r in range(dim)] != R


@pytest.mark.parametrize("dim", (2, 4, 8, 16))
def test_right_mult_matrix_really_is_right_multiplication(dim: int) -> None:
    """Contracting ``R(x)`` against ``y`` must reproduce ``y·x`` — building the
    matrix column-by-column and contracting is a different route from the
    product, so this is a real two-route check."""
    rng = random.Random(3310 + dim)
    for _ in range(6):
        x, y = _rand(dim, rng), _rand(dim, rng)
        R = right_mult_matrix(x)
        got = tuple(sum((R[r][c] * y[c] for c in range(dim)), Q(0))
                    for r in range(dim))
        assert got == tuple(cd_mult(y, x))


@pytest.mark.parametrize("dim", (4, 8, 16))
def test_the_two_halves_answer_DIFFERENT_questions(dim: int) -> None:
    """Feed the right op the LEFT question and it must be wrong every time —
    which is why a ``side=`` flag would be a defect, not a convenience."""
    rng = random.Random(5510 + dim)
    agreed = 0
    trials = 12
    for _ in range(trials):
        a, b = _rand(dim, rng), _rand(dim, rng)
        try:
            if cd_right_divide(cd_mult(a, b), a) == tuple(b):
                agreed += 1
        except ValueError:
            pass
    assert agreed == 0, (
        f"dim {dim}: right-divide answered the LEFT question {agreed}/{trials} "
        f"times; the two ops would then be interchangeable and the Class-C "
        f"vocabulary would be wrong")


def test_the_two_halves_DO_agree_where_the_algebra_commutes() -> None:
    """⚠️ NON-VACUITY for the test above: the disagreement must come from
    non-commutativity, not from one of the ops being broken. At dim 2 (ℂ, where
    the algebra commutes) they agree."""
    rng = random.Random(11)
    for _ in range(12):
        a, b = _rand(2, rng), _rand(2, rng)
        assert cd_right_divide(cd_mult(a, b), a) == tuple(b)
        assert cd_left_divide(a, cd_mult(a, b)) == tuple(b)
