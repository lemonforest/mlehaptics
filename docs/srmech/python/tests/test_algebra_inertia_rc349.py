"""The ℝ→ℂ rung instrument — orderability read off a multiplication table.

rc349 (`#T987`, consolidating `#T968`). The Hurwitz loss ladder drops one
capability per doubling: **ℝ→ℂ ordering**, ℂ→ℍ commutativity, ℍ→𝕆
associativity, 𝕆→𝕊 composition. The last three already had instruments in this
tree; the FIRST rung had none, and ``inertia_signature`` is it.

**The ladder itself is not the claim.** ℝ→ℂ→ℍ→𝕆 is the classical Hurwitz
result: definitional, textbook, forced — and on the shipped ladder ``n₋`` is
exactly ``dim − 1``, so reading those rows is reading the dimension. Nothing
below discovers it; the ladder rows are a CHECK. What this file actually tests
is the INSTRUMENT, on inputs the theorem does not cover:

* **C1 — split octonions.** The discriminating pin. Split-𝕆 must answer
  ``(5, 3, 0)`` and **not** 𝕆's ``(1, 7, 0)``. An audit this rc found a shipped
  float read getting split-𝕆 demonstrably wrong, and found a *different*
  mechanism scoring 200/200 on 𝕆, split-𝕆 AND a random table alike — because it
  took no algebra input at all. **An instrument that cannot separate those three
  is not reading the algebra**, so separating them is the pass condition.
* **C2 — ≥100 random structure-constant tables** of matched shape, monomial and
  general, each with its witness verified against the table it came from.
* **C3 — a NO-NEGATIVE-DIRECTION control.** ℝ must return "no witness exists".
  A witness-finder that can never return "none" is not measuring anything. It
  is NOT allowed to get there by special-casing dim 1: split-ℂ (dim 2) also
  has no negative direction, and the ladder's own ℂ (dim 2) does.

Plus three guards on what must NOT be claimed, each of which caught a real
defect in the first cut of this rc:

* the op reads the TABLE, never a declared dimension **and never the
  coordinate form** ``a² − |v|²`` (input-blind: it stays wrong at infinite
  precision, so it is a substitution error and not a precision one);
* ``n₋ == 0`` must NOT be reported as "ordered" — split-ℂ answers
  ``(2, 0, 0)`` and has zero divisors ``(1+j)(1−j) = 0``, so it is provably
  **not** orderable;
* the measured CEILING: a table with the diagonal pinned and the off-diagonal
  scrambled answers exactly as 𝕆 does, so the op certifies nothing about
  associativity, alternativity, composition or division.
"""
import io
import itertools
import os
import random
import re

import pytest

from srmech import _native
from srmech import cascade
from srmech._native import HAS_NATIVE
from srmech.cascade import cayley_dickson as cd
from srmech.cascade import (
    ASSOCIATIVE_ALGEBRA_DIMS,
    DIVISION_ALGEBRA_DIMS,
    cd_add,
    cd_conjugate,
    cd_mult,
    cd_norm_sq,
)
from srmech.cascade.cayley_dickson import INERTIA_FORMS
from srmech.physics.qm.octonion import octonion_mult_table
from srmech.physics.qm.quaternion import quaternion_mult_table


_INERTIA_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_algebra_inertia_signature")
)

SKIP_IF_NO_NATIVE = pytest.mark.skipif(
    not _INERTIA_NATIVE,
    reason="installed libsrmech predates the v0.9.0rc349 inertia symbol",
)


# ── fixtures: the GENERALIZED Cayley–Dickson doubling, as a LABELLED ORACLE ──
#
# (a, b)(c, d) = (a c + γ d̄ b, d a + b c̄) with a per-level γ ∈ {−1, +1}.
# γ = −1 is the standard (definite) doubling srmech ships; γ = +1 at a level
# makes that level SPLIT. Ladder order: γ[0] is ℝ→ℂ, γ[1] is ℂ→ℍ, γ[2] is ℍ→𝕆,
# so ℝ →(−1) ℂ →(−1) ℍ →(+1) split-𝕆 is ``[-1, -1, +1]``.
#
# rc352 (`#T997`) SHIPPED this constructor as ``cascade.algebra_table``. This
# body stays as the **independent oracle** it always was — a RECURSIVE doubling
# that shares no code with the shipped ITERATIVE cocycle — and
# ``test_shipped_algebra_table_matches_the_independent_oracle`` below pins the
# two against each other at every dim × every γ. Keeping it is not duplication
# debt: it is the only thing in the tree that can contradict the shipped
# cocycle's sign convention, and the fixtures below are controls precisely
# because they do not come from the code under test.

def _cd_table_oracle(dim, gammas):
    """ORACLE ONLY — the recursive generalised doubling, in LADDER γ order.
    Deliberately NOT the subject of any test; it is what
    ``cascade.algebra_table`` is checked against."""
    def conj(a):
        n = len(a)
        if n == 1:
            return a
        m = n >> 1
        return conj(a[:m]) + tuple(-x for x in a[m:])

    def mul(a, b):
        n = len(a)
        if n == 1:
            return (a[0] * b[0],)
        m = n >> 1
        gamma = gammas[n.bit_length() - 2]      # ladder index of THIS doubling
        a1, a2 = a[:m], a[m:]
        b1, b2 = b[:m], b[m:]
        left = tuple(p + gamma * q for p, q in zip(mul(a1, b1), mul(conj(b2), a2)))
        right = tuple(p + q for p, q in zip(mul(b2, a1), mul(a2, conj(b1))))
        return left + right

    def basis(i):
        return tuple(1 if k == i else 0 for k in range(dim))

    return [[list(mul(basis(i), basis(j))) for j in range(dim)]
            for i in range(dim)]


def _random_monomial_table(dim, rng):
    """A random table of MATCHED SHAPE: e_i·e_j = ±e_k, k and the sign random."""
    out = []
    for _ in range(dim):
        row = []
        for _ in range(dim):
            cell = [0] * dim
            cell[rng.randrange(dim)] = rng.choice((1, -1))
            row.append(cell)
        out.append(row)
    return out


def _random_general_table(dim, rng):
    """Arbitrary structure constants — not monomial, not an algebra at all."""
    return [[[rng.choice((-1, 0, 0, 1)) for _ in range(dim)]
             for _ in range(dim)] for _ in range(dim)]


def _integer_product(table, x, y):
    """The SHIPPED ``cascade.table_product``, read back as exact ints.

    rc352 (`#T997`) RETIRED this file's hand-rolled ``_oracle_product``. That
    oracle existed for exactly one reason — its own docstring said so — namely
    that no shipped op took a table, so the split and random tables had no
    product at all. ``cascade.table_product`` is that op, so the subject of
    every check below is now the shipped code and this is a one-line type
    adapter (``table_product`` returns exact ``Q``; these fixtures are
    integers), NOT a second implementation.
    """
    return [int(v) for v in cascade.table_product(table, x, y)]


def _definite(dim):
    """The standard (γ = −1 everywhere) table at a division-algebra rung, from
    the independent ORACLE — deliberately not from ``cascade.algebra_table``,
    so the split fixtures below stay controls on the shipped constructor."""
    return _cd_table_oracle(dim, [-1] * (dim.bit_length() - 1))


REAL = _definite(1)
COMPLEX = _definite(2)
QUATERNION = _definite(4)
OCTONION = _definite(8)
SEDENION = _cd_table_oracle(16, [-1] * 4)
SPLIT_COMPLEX = _cd_table_oracle(2, [+1])
SPLIT_QUATERNION = _cd_table_oracle(4, [-1, +1])
SPLIT_OCTONION = _cd_table_oracle(8, [-1, -1, +1])
#: ℚ(√2) as a 2-dim ℚ-algebra: e₁·e₁ = 2e₀. A genuinely ORDERED field, and the
#: measured limit of what a signature can separate (see the test below).
Q_SQRT2 = [[[1, 0], [0, 1]], [[0, 1], [2, 0]]]


# ── the fixture builder is honest, and anchored to the SHIPPED ops ──────────

def test_generalised_doubling_reproduces_the_shipped_tables():
    """γ = −1 at every level IS the standard construction srmech already ships."""
    assert OCTONION == octonion_mult_table()
    assert QUATERNION == quaternion_mult_table()


def test_shipped_algebra_table_matches_the_independent_oracle():
    """THE convention anchor (rc352, `#T997`).

    ``cascade.algebra_table`` computes the γ-parameterised cocycle
    ITERATIVELY (one bounded loop, JPL Rule 1, the same engine the C peer
    runs); ``_cd_table_oracle`` above computes it by RECURSIVE doubling on
    whole elements. They share no code. Every dim on the ladder, every γ
    assignment — this is the check that could contradict the shipped sign
    convention, and the reason the recursive body is kept rather than deleted
    now that a constructor ships.
    """
    checked = 0
    for dim in (1, 2, 4, 8, 16):
        n_levels = dim.bit_length() - 1
        combos = list(itertools.product((-1, 1), repeat=n_levels))
        for gammas in combos:
            assert cascade.algebra_table(dim, gammas) == \
                _cd_table_oracle(dim, list(gammas)), (dim, gammas)
            checked += 1
    assert checked == 1 + 2 + 4 + 8 + 16, checked
    # …and the DEFAULT is the definite ladder, not merely equal to some member.
    for dim in (1, 2, 4, 8, 16):
        assert cascade.algebra_table(dim) == \
            _cd_table_oracle(dim, [-1] * (dim.bit_length() - 1))


@pytest.mark.parametrize("dim", DIVISION_ALGEBRA_DIMS)
def test_shipped_table_product_agrees_with_the_shipped_cd_mult(dim):
    """TWO SHIPPED ROUTES to one product — no oracle on either side.

    Before rc352 this test anchored a hand-rolled ``_oracle_product`` to
    ``cd_mult``. Now both sides are shipped ops that reach the same bilinear
    form by different routes: ``cd_mult`` recurses / calls the cocycle per
    ``(i, j)``; ``table_product`` accumulates over a MATERIALISED rank-3
    tensor.

    **What this differential does and does not cover, stated so it cannot be
    over-read.** The SIGN CONVENTION is shared — one cocycle engine serves
    ``cd_basis_product`` and ``algebra_table`` alike, deliberately, because the
    1:1-mirror discipline forbids two copies of one algebra. So a convention
    error would pass here. What it covers is the accumulation, the tensor
    materialisation and the exact-ℚ arithmetic path, on inputs from the
    module's own ``DIVISION_ALGEBRA_DIMS``. The convention itself is pinned
    against the INDEPENDENT recursive oracle by
    ``test_shipped_algebra_table_matches_the_independent_oracle``.
    """
    rng = random.Random(1000 + dim)
    table = _definite(dim)
    for _ in range(40):
        x = [rng.randint(-3, 3) for _ in range(dim)]
        y = [rng.randint(-3, 3) for _ in range(dim)]
        assert [int(v) for v in cd_mult(x, y)] == _integer_product(table, x, y)


@pytest.mark.parametrize("dim", DIVISION_ALGEBRA_DIMS)
def test_fixture_tables_agree_with_shipped_cd_mult_conjugate_and_add(dim):
    """Every shipped CD op the fixtures could disagree with, exercised."""
    rng = random.Random(2000 + dim)
    table = _definite(dim)
    for _ in range(25):
        x = [rng.randint(-3, 3) for _ in range(dim)]
        y = [rng.randint(-3, 3) for _ in range(dim)]
        assert [int(v) for v in cd_add(x, y)] == [a + b for a, b in zip(x, y)]
        conj = [int(v) for v in cd_conjugate(x)]
        assert conj == [x[0]] + [-v for v in x[1:]]
        # x·x̄ = N(x)·1 on the definite ladder, via the SHIPPED ops throughout.
        assert [int(v) for v in cd_mult(x, conj)] == \
            [int(cd_norm_sq(x))] + [0] * (dim - 1)


def test_split_octonion_fixture_is_genuinely_split():
    """4 imaginary units square to +1 and 3 to −1 — the (4,4) norm form.

    Stated as the classical fact (Springer & Veldkamp §1.7) and checked against
    the fixture, so a broken fixture cannot quietly make C1 pass.
    """
    squares = [SPLIT_OCTONION[i][i][0] for i in range(8)]
    assert squares[0] == 1                      # the identity
    imaginary = squares[1:]
    assert imaginary.count(1) == 4
    assert imaginary.count(-1) == 3
    # 𝕆 by contrast: every imaginary unit squares to −1.
    assert [OCTONION[i][i][0] for i in range(8)] == [1] + [-1] * 7


def test_split_octonion_has_zero_divisors_and_the_octonions_do_not():
    """The other half of "genuinely split": 𝕆 is a division algebra, split-𝕆 is
    not. A deterministic sweep over ±1 two-term elements."""
    def find_zero_divisor(table):
        dim = len(table)
        for i in range(dim):
            for j in range(i + 1, dim):
                for k in range(dim):
                    for m in range(k + 1, dim):
                        for s in (1, -1):
                            x = [0] * dim
                            x[i], x[j] = 1, 1
                            y = [0] * dim
                            y[k], y[m] = 1, s
                            if not any(_integer_product(table, x, y)):
                                return x, y
        return None

    assert find_zero_divisor(OCTONION) is None
    assert find_zero_divisor(SPLIT_OCTONION) is not None


# ── the ladder (a CHECK — this part is textbook, not a finding) ──────────────

@pytest.mark.parametrize("dim", DIVISION_ALGEBRA_DIMS)
def test_hurwitz_ladder_signature_is_DEFINITIONAL(dim):
    """Stated declaratively over the module's own ``DIVISION_ALGEBRA_DIMS``,
    and graded: on the shipped ladder ``n₋`` is exactly ``dim − 1``, so this
    row is reading the dimension. It is a CHECK, not a finding."""
    r = cascade.inertia_signature(_definite(dim))
    assert r["signature"] == (1, dim - 1, 0)
    assert r["n_minus"] == r["dim"] - 1


def test_the_definitional_pattern_breaks_off_the_shipped_ladder():
    """…and that is the whole reason the split rows carry the evidence."""
    for table in (SPLIT_COMPLEX, SPLIT_QUATERNION, SPLIT_OCTONION,
                  Q_SQRT2, DUAL_NUMBERS):
        r = cascade.inertia_signature(table)
        assert r["n_minus"] != r["dim"] - 1, r["signature"]


def test_sedenion_continues_the_ladder_past_the_division_algebras():
    """Dim 16 is outside DIVISION_ALGEBRA_DIMS but still on CD_DIMS."""
    assert 16 not in DIVISION_ALGEBRA_DIMS and 16 in cd.CD_DIMS
    assert cascade.inertia_signature(SEDENION)["signature"] == (1, 15, 0)


def test_associativity_fence_is_read_from_the_module_not_hard_coded():
    """``ASSOCIATIVE_ALGEBRA_DIMS`` is where the ℍ→𝕆 fence lives; the ceiling
    test below relies on it being strictly inside the division-algebra dims."""
    assert set(ASSOCIATIVE_ALGEBRA_DIMS) < set(DIVISION_ALGEBRA_DIMS)
    assert max(ASSOCIATIVE_ALGEBRA_DIMS) == 4


def test_shipped_tables_answer_the_same_as_the_fixtures():
    """The op on srmech's OWN shipped tables, not only on the test's."""
    assert cascade.inertia_signature(octonion_mult_table())["signature"] == (1, 7, 0)
    assert cascade.inertia_signature(quaternion_mult_table())["signature"] == (1, 3, 0)


# ── C3: the NO-NEGATIVE-DIRECTION control ───────────────────────────────────

def test_real_numbers_have_no_negative_direction_and_no_witness():
    r = cascade.inertia_signature(REAL)
    assert r["has_negative_direction"] is False
    assert r["n_minus"] == 0
    assert r["witness"] is None
    assert r["witness_real_square"] is None
    assert r["witness_certifies_nonorderable"] is False


def test_no_negative_direction_is_not_a_dim_1_special_case():
    """split-ℂ (dim 2) has none; ℂ (dim 2) has one. Same dimension, opposite
    verdicts — so the answer cannot be coming from the dimension."""
    split = cascade.inertia_signature(SPLIT_COMPLEX)
    definite = cascade.inertia_signature(COMPLEX)
    assert split["dim"] == definite["dim"] == 2
    assert split["has_negative_direction"] is False and split["witness"] is None
    assert definite["has_negative_direction"] is True
    assert definite["witness"] is not None


# ── the correction that matters most: n₋ == 0 is NOT "orderable" ────────────

def test_the_op_never_claims_an_algebra_is_ORDERED():
    """No key of the result may assert orderability.

    ``n₋ == 0`` means "no negative-square direction in the trace form". Reading
    it as "ordered" produces a FALSE NEGATIVE one rung above ℝ (see the next
    test), so the claim is simply not emitted — there is no ``ordered`` key and
    adding one back must fail here.
    """
    r = cascade.inertia_signature(SPLIT_COMPLEX)
    assert "ordered" not in r
    assert "orderable" not in r
    assert "is_ordered" not in r
    assert r["has_negative_direction"] is False


def test_split_complex_has_no_negative_direction_yet_is_NOT_orderable():
    """The measured false negative. split-ℂ answers (2, 0, 0) — no negative
    direction — but ``(1+j)(1−j) = 1 − j² = 0`` with both factors nonzero.

    In an ordered ring a product of two nonzero elements is nonzero (each of
    ``a>0,b>0`` / ``a>0,b<0`` / ``a<0,b<0`` forces ``ab ≠ 0``), so split-ℂ
    carries no compatible total order. Anything that read this result as
    "ORDERED" would be certifying the opposite of the truth.
    """
    r = cascade.inertia_signature(SPLIT_COMPLEX)
    assert r["signature"] == (2, 0, 0)
    assert r["has_negative_direction"] is False
    one_plus_j = [1, 1]
    one_minus_j = [1, -1]
    assert any(one_plus_j) and any(one_minus_j)
    assert not any(_integer_product(SPLIT_COMPLEX, one_plus_j, one_minus_j))   # == 0
    # …and the instrument does NOT claim otherwise.
    assert "ordered" not in r


def test_the_norm_signature_does_NOT_separate_split_complex_from_Q_sqrt2():
    """The prescribed repair, MEASURED — and it does not work.

    "Test isotropy of the norm to separate split-ℂ from ℚ(√2)" fails at this
    resolution: both answer trace ``(2, 0, 0)`` and norm ``(1, 1, 0)``,
    identically. A signature is a REAL-PLACE statement, and ``a² − 2b²`` is
    isotropic over ℝ while anisotropic over ℚ — so the split algebra (which has
    zero divisors) and the genuinely ordered field ℚ(√2) are indistinguishable
    to this op in BOTH forms. Separating them needs a RATIONAL zero of the norm
    form, which this op does not compute. **The gap is open, and this test
    pins it so a later reader cannot assume it was closed.**
    """
    split = cascade.inertia_signature(SPLIT_COMPLEX)
    ordered_field = cascade.inertia_signature(Q_SQRT2)
    assert split["signature"] == ordered_field["signature"] == (2, 0, 0)
    assert split["norm_signature"] == ordered_field["norm_signature"] == (1, 1, 0)
    # …yet they genuinely differ: split-ℂ has a rational null vector, ℚ(√2) does
    # not (a² = 2b² has no nonzero rational solution).
    assert not any(_integer_product(SPLIT_COMPLEX, [1, 1], [1, -1]))
    assert all(any(_integer_product(Q_SQRT2, [a, b], [a, -b]))
               for a in range(-6, 7) for b in range(-6, 7) if (a or b))


def test_the_shipped_cd_norm_sq_cannot_serve_as_the_isotropy_test():
    """Why the obvious reuse was rejected, measured on the SHIPPED op.

    ``cd_norm_sq()`` with no ``gammas`` is ``Σ xᵢ²`` in COORDINATES — it reads
    no table — so it reports ``N([1,−1]) = 2`` for an element that is genuinely
    a null vector of the SPLIT-ℂ norm. Reusing the default read as a general
    isotropy test would have reproduced exactly the input-blind substitution
    this rc exists to avoid.

    **rc352 (`#T1001`) closed the half of this that was a live trap.** The rc349
    note here said "not a live bug: the module builds no split algebra"; rc352's
    ``algebra_table`` builds one, so the default became a DECLARATION rather
    than an assumption and the twisted read ships beside it (see
    ``test_cd_norm_sq_gate`` in ``test_algebra_table_rc352.py``). What survives
    unchanged is the statement this test makes: the DEFAULT read is the
    definite one and must not be pressed into service as an isotropy oracle.
    """
    assert int(cd_norm_sq([1, -1])) == 2                    # coordinate form
    assert not any(_integer_product(SPLIT_COMPLEX, [1, 1], [1, -1]))
    # On the DEFINITE ladder it is correct, which is why it survives in scope.
    assert int(cd_norm_sq([3, 4])) == 25
    # …and the split read, declared, is 0 — the null vector the default misses.
    assert int(cd_norm_sq([1, -1], gammas=(+1,))) == 0


def test_sedenion_zero_divisor_witness_is_not_a_general_isotropy_surface():
    """The other prescribed reuse, checked rather than assumed: it takes no
    dimension argument, so it cannot be pointed at split-ℂ."""
    import inspect
    assert list(inspect.signature(cd.sedenion_zero_divisor_witness)
                .parameters) == []
    assert cd.sedenion_zero_divisor_witness()["dim"] == 16


def test_order_sense_is_named_in_the_payload():
    """"ordered" does three jobs; this op reads one. ℂ IS orderable as a set
    and as an additive group (lex order is compatible with ``cd_add``), and
    fails only as a FIELD. Reporting "not ordered" unqualified would repeat the
    split-ℂ error in a subtler form, so the sense is named in the payload."""
    r = cascade.inertia_signature(COMPLEX)
    assert r["order_sense"] == "field"
    assert "field" in cd.inertia_signature.__doc__
    # The additive sense really does hold, on the SHIPPED cd_add.
    rng = random.Random(99)
    for _ in range(200):
        a = [rng.randint(-4, 4) for _ in range(2)]
        b = [rng.randint(-4, 4) for _ in range(2)]
        c = [rng.randint(-4, 4) for _ in range(2)]
        if tuple(a) < tuple(b):
            assert tuple(int(v) for v in cd_add(a, c)) < \
                tuple(int(v) for v in cd_add(b, c))
    # …while the multiplicative sense fails: (0,1)·(0,1) = (−1,0) < (0,0).
    assert [int(v) for v in cd_mult([0, 1], [0, 1])] == [-1, 0]


def test_the_read_is_uncorrelated_with_being_a_division_algebra():
    """It flags 𝕊 (which IS flagged, n₋ = 15) and misses split-ℂ (n₋ = 0),
    while 𝕊 has zero divisors and split-ℂ has them too. The trace-form read
    simply is not a division-algebra test — ``left_mult_is_invertible`` and
    ``sedenion_zero_divisor_witness`` are."""
    assert cascade.inertia_signature(SEDENION)["has_negative_direction"] is True
    assert cascade.inertia_signature(SPLIT_COMPLEX)["has_negative_direction"] \
        is False
    assert cascade.inertia_signature(OCTONION)["has_negative_direction"] is True


# ── C1: the discriminating pin ──────────────────────────────────────────────

def test_split_octonions_do_not_answer_like_the_octonions():
    """THE control. Same dimension, same shape of table, different algebra."""
    plain = cascade.inertia_signature(OCTONION)
    split = cascade.inertia_signature(SPLIT_OCTONION)
    assert plain["signature"] == (1, 7, 0)
    assert split["signature"] == (5, 3, 0)
    assert split["signature"] != plain["signature"]


def test_split_quaternions_do_not_answer_like_the_quaternions():
    assert cascade.inertia_signature(SPLIT_QUATERNION)["signature"] == (3, 1, 0)
    assert cascade.inertia_signature(QUATERNION)["signature"] == (1, 3, 0)


def test_the_instrument_separates_octonion_split_octonion_and_random():
    """The audit's pass condition, written down as a test.

    A mechanism that takes no algebra input scores identically on all three.
    This one must return three DIFFERENT answers.
    """
    rng = random.Random(20260727)
    random_table = _random_monomial_table(8, rng)
    answers = {
        "octonion": cascade.inertia_signature(OCTONION)["signature"],
        "split_octonion": cascade.inertia_signature(SPLIT_OCTONION)["signature"],
        "random": cascade.inertia_signature(random_table)["signature"],
    }
    assert len(set(answers.values())) == 3, answers


# ── the witness is real, and it is checked against the table ────────────────

@pytest.mark.parametrize("name,table", [
    ("C", COMPLEX), ("H", QUATERNION), ("O", OCTONION), ("S", SEDENION),
    ("split-H", SPLIT_QUATERNION), ("split-O", SPLIT_OCTONION),
])
def test_witness_is_a_negative_direction_of_the_trace_form(name, table):
    r = cascade.inertia_signature(table)
    w = r["witness"]
    assert w is not None and any(v != 0 for v in w), name
    # w·w recomputed from the FULL product, not from the op's own Gram.
    square = _integer_product(table, w, w)
    assert square == r["witness_square"], name
    assert square[0] < 0, (name, w, square)
    assert square[0] == r["witness_real_square"]


@pytest.mark.parametrize("name,table", [
    ("C", COMPLEX), ("H", QUATERNION), ("O", OCTONION), ("S", SEDENION),
    ("split-H", SPLIT_QUATERNION), ("split-O", SPLIT_OCTONION),
])
def test_ladder_witnesses_carry_the_STRONG_certificate(name, table):
    """The negative pivot direction on every ladder rung is a basis element
    with ``e_i² = −1`` — a negative real MULTIPLE OF THE IDENTITY. That is the
    classical argument outright: ``−1`` is a square ⇒ no compatible order.

    A merely negative ``Re(w·w)`` is weaker and does NOT contradict
    orderability (``[3,−5]² = −16 − 30i`` in ℂ is a negative direction of the
    trace form and nothing more), so the two are reported separately.
    """
    r = cascade.inertia_signature(table)
    assert r["witness_certifies_nonorderable"] is True, name
    assert r["witness_square"][0] < 0
    assert all(v == 0 for v in r["witness_square"][1:]), name


def test_a_negative_trace_direction_need_not_be_a_strong_certificate():
    """Guard against re-conflating the two. [3,−5] in ℂ has Re(x·x) = −16 < 0
    yet x² = −16 − 30i is not a negative real, so it certifies nothing."""
    square = _integer_product(COMPLEX, [3, -5], [3, -5])
    assert square[0] == -16 and square[0] < 0
    assert square[1] != 0                       # NOT a real multiple of 1


def test_signature_components_sum_to_the_dimension():
    for table in (REAL, COMPLEX, QUATERNION, OCTONION, SEDENION,
                  SPLIT_COMPLEX, SPLIT_QUATERNION, SPLIT_OCTONION):
        r = cascade.inertia_signature(table)
        assert r["n_plus"] + r["n_minus"] + r["n_zero"] == r["dim"]
        assert r["signature"] == (r["n_plus"], r["n_minus"], r["n_zero"])
        assert r["has_negative_direction"] == (r["n_minus"] > 0)
        assert sum(r["norm_signature"]) == r["dim"]


# ── the NORM form, named — the literature's (4,4) for split-𝕆 ───────────────

@pytest.mark.parametrize("name,table,trace,norm", [
    ("R", REAL, (1, 0, 0), (1, 0, 0)),
    ("C", COMPLEX, (1, 1, 0), (2, 0, 0)),
    ("H", QUATERNION, (1, 3, 0), (4, 0, 0)),
    ("O", OCTONION, (1, 7, 0), (8, 0, 0)),
    ("split-C", SPLIT_COMPLEX, (2, 0, 0), (1, 1, 0)),
    ("split-H", SPLIT_QUATERNION, (3, 1, 0), (2, 2, 0)),
    ("split-O", SPLIT_OCTONION, (5, 3, 0), (4, 4, 0)),
])
def test_both_forms_are_reported_and_named(name, table, trace, norm):
    """Anyone checking (5,3,0) against a reference will think it failed, because
    the literature quotes split-𝕆 as (4,4) — the NORM form. Both ship, named,
    so the number can be matched to the read it belongs to."""
    r = cascade.inertia_signature(table)
    assert r["form"] == "trace"
    assert r["signature"] == trace, name
    assert r["norm_signature"] == norm, name


def test_norm_form_reproduces_the_classical_split_signatures():
    """Springer & Veldkamp §1.7: the split composition algebras carry norm
    forms of signature (1,1), (2,2), (4,4); the definite ones are definite."""
    assert cascade.inertia_signature(SPLIT_COMPLEX)["norm_signature"] == (1, 1, 0)
    assert cascade.inertia_signature(SPLIT_QUATERNION)["norm_signature"] == (2, 2, 0)
    assert cascade.inertia_signature(SPLIT_OCTONION)["norm_signature"] == (4, 4, 0)
    for table in (COMPLEX, QUATERNION, OCTONION):
        n_plus, n_minus, n_zero = cascade.inertia_signature(table)["norm_signature"]
        assert (n_minus, n_zero) == (0, 0) and n_plus == len(table)


# ── n₀ does real work: a genuinely degenerate algebra ───────────────────────

DUAL_NUMBERS = [
    [[1, 0], [0, 1]],       # e0·e0 = e0,  e0·e1 = e1
    [[0, 1], [0, 0]],       # e1·e0 = e1,  e1·e1 = 0   (ε² = 0)
]


def test_dual_numbers_exercise_the_degenerate_component():
    """ℝ[ε]/(ε²) — ε² = 0, so the trace form is degenerate and n₀ = 1. Without
    a case like this ``n₀`` is forced to 0 on the whole ladder and does no
    work; here it is the entire answer for the ε direction."""
    r = cascade.inertia_signature(DUAL_NUMBERS)
    assert r["signature"] == (1, 0, 1)
    assert r["n_zero"] == 1
    assert r["has_negative_direction"] is False
    assert r["witness"] is None
    assert _integer_product(DUAL_NUMBERS, [0, 1], [0, 1]) == [0, 0]     # ε² = 0


def test_n_zero_is_exercised_by_the_random_families_too():
    """Not only by the hand-built degenerate case."""
    rng = random.Random(5150)
    seen = 0
    for _ in range(60):
        r = cascade.inertia_signature(_random_monomial_table(8, rng))
        seen += 1 if r["n_zero"] > 0 else 0
    assert seen > 0, "n_zero never fired — it would be doing no work"


# ── C2: ≥100 random structure-constant tables ───────────────────────────────

def test_random_monomial_tables_120_witnesses_all_verify():
    rng = random.Random(4242)
    signatures = set()
    for _ in range(120):
        table = _random_monomial_table(8, rng)
        r = cascade.inertia_signature(table)
        assert r["n_plus"] + r["n_minus"] + r["n_zero"] == 8
        signatures.add(r["signature"])
        if r["witness"] is None:
            assert r["n_minus"] == 0
        else:
            assert _integer_product(table, r["witness"], r["witness"])[0] < 0
    # The op is READING each table: a fixed-output mechanism would give one
    # answer for all 120.
    assert len(signatures) >= 5, signatures
    assert (1, 7, 0) not in signatures      # 𝕆's answer is not the default


def test_random_general_tables_120_witnesses_all_verify():
    """Not monomial, not associative, not composition algebras — arbitrary
    structure constants. The op still answers, and still certifies."""
    rng = random.Random(31337)
    for _ in range(120):
        table = _random_general_table(6, rng)
        r = cascade.inertia_signature(table)
        assert r["n_plus"] + r["n_minus"] + r["n_zero"] == 6
        if r["witness"] is not None:
            assert _integer_product(table, r["witness"], r["witness"])[0] < 0


# ── THE CEILING, made executable ────────────────────────────────────────────

def _diagonal_pinned_table(dim, rng, allow_real_offdiagonal=False):
    """𝕆's diagonal, everything else scrambled.

    ``e₀·e₀ = e₀``, ``e_i·e_i = −e₀`` for ``i > 0``, and every off-diagonal
    cell an independent random ``±e_k``. With ``allow_real_offdiagonal=False``
    the off-diagonal targets are drawn from the IMAGINARY directions only, so
    every off-diagonal real part is zero and the trace-form Gram is exactly
    𝕆's — the family the ceiling claim is about.
    """
    low = 0 if allow_real_offdiagonal else 1
    table = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            if i == j:
                table[i][j][0] = 1 if i == 0 else -1
            else:
                table[i][j][rng.randrange(low, dim)] = rng.choice((1, -1))
    return table


def _is_associative(table):
    """Scan every imaginary basis triple, stopping at the first failure.

    Lazy on purpose: a scrambled table fails within the first few triples, so
    the sweep is cheap, while a genuinely associative table (𝕆) pays the full
    scan exactly once. A fixed short probe list is NOT decisive — measured, 1
    of 200 scrambled tables associated on all of five hand-picked triples.
    """
    dim = len(table)
    for i in range(1, dim):
        for j in range(1, dim):
            for k in range(1, dim):
                a, b, c = ([0] * dim for _ in range(3))
                a[i], b[j], c[k] = 1, 1, 1
                if _integer_product(table, _integer_product(table, a, b), c) != \
                        _integer_product(table, a, _integer_product(table, b, c)):
                    return False
    return True


def test_the_op_cannot_tell_a_scrambled_table_from_the_octonions():
    """THE CEILING, stated as a test rather than as prose, and MEASURED.

    ``Re(x·x) = Σ_i ε_i x_i²`` exactly whenever the off-diagonal real parts
    vanish. So pinning the diagonal to 𝕆's and scrambling the off-diagonal
    among the IMAGINARY directions gives tables that answer ``(1, 7, 0)`` —
    bit-identical to 𝕆 — while being wildly non-associative. **The op reads the
    inertia of the trace form and nothing else**; it certifies nothing about
    associativity, alternativity, composition or division.
    """
    rng = random.Random(8675309)
    octonion = cascade.inertia_signature(OCTONION)["signature"]
    identical = 0
    non_associative = 0
    for _ in range(200):
        table = _diagonal_pinned_table(8, rng)
        if cascade.inertia_signature(table)["signature"] == octonion:
            identical += 1
        non_associative += 0 if _is_associative(table) else 1
    assert identical == 200, identical           # the ceiling, exactly
    assert non_associative == 200, non_associative
    # 𝕆 is of course not associative either (it is only ALTERNATIVE), so the
    # probe separates nothing on its own — which is precisely the point: the
    # signature is identical across a family the associator tells apart.
    assert cascade.inertia_signature(OCTONION)["signature"] == octonion


def test_the_op_is_not_blind_to_the_off_diagonal_REAL_slice():
    """The complement of the ceiling, and a sharper statement of it.

    Let the scramble put mass on ``e₀`` as well and the off-diagonal real parts
    no longer cancel — at which point the op DOES separate a good fraction of
    the family from 𝕆 (measured 130/200 still identical, so 70/200 separated).
    The precise scope is therefore not "blind to the off-diagonal" but **reads
    exactly the symmetric part of the real slice ``c_ij0 + c_ji0``, and nothing
    beyond it**.
    """
    rng = random.Random(8675309)
    octonion = cascade.inertia_signature(OCTONION)["signature"]
    identical = 0
    for _ in range(200):
        table = _diagonal_pinned_table(8, rng, allow_real_offdiagonal=True)
        if cascade.inertia_signature(table)["signature"] == octonion:
            identical += 1
    assert identical == 130, identical
    assert 0 < identical < 200


def test_the_ceiling_is_named_in_the_docstring():
    """A measured limitation that lives only in a test is one refactor from
    being lost. It must also be in the surface the user reads."""
    doc = cd.inertia_signature.__doc__
    assert "CEILING" in doc
    assert "nothing else" in doc
    assert "loop_associator" in doc


# ── an INDEPENDENT exact oracle for the signature ───────────────────────────

def _char_poly(gram):
    """det(xI − G) over ℚ by Faddeev–LeVerrier; integral for an integer G."""
    from fractions import Fraction
    n = len(gram)
    a = [[Fraction(v) for v in row] for row in gram]
    coeffs = [Fraction(1)]
    m = [[Fraction(1) if i == j else Fraction(0) for j in range(n)]
         for i in range(n)]
    for k in range(1, n + 1):
        if k > 1:
            am = [[sum(a[i][t] * m[t][j] for t in range(n)) for j in range(n)]
                  for i in range(n)]
            m = [[am[i][j] + (coeffs[-1] if i == j else 0) for j in range(n)]
                 for i in range(n)]
        am = [[sum(a[i][t] * m[t][j] for t in range(n)) for j in range(n)]
              for i in range(n)]
        coeffs.append(-sum(am[i][i] for i in range(n)) / k)
    assert all(c.denominator == 1 for c in coeffs)
    return [int(c) for c in coeffs]


def _oracle_signature(table):
    """G is real SYMMETRIC, so every eigenvalue is real and Descartes' rule of
    signs is EXACT rather than an upper bound. Shares no code with the
    congruence elimination under test."""
    dim = len(table)
    gram = [[table[i][j][0] + table[j][i][0] for j in range(dim)]
            for i in range(dim)]
    c = _char_poly(gram)
    n_zero = 0
    while c and c[-1] == 0:
        c.pop()
        n_zero += 1
    if not c:
        return 0, 0, dim

    def changes(seq):
        nz = [v for v in seq if v != 0]
        return sum(1 for x, y in zip(nz, nz[1:]) if x * y < 0)

    alt = [v if (len(c) - 1 - i) % 2 == 0 else -v for i, v in enumerate(c)]
    return changes(c), changes(alt), n_zero


def test_signature_matches_an_independent_exact_oracle():
    for table in (REAL, COMPLEX, QUATERNION, OCTONION, SEDENION,
                  SPLIT_COMPLEX, SPLIT_QUATERNION, SPLIT_OCTONION):
        assert cascade.inertia_signature(table)["signature"] == \
            _oracle_signature(table), len(table)
    rng = random.Random(909)
    for _ in range(40):
        table = _random_general_table(5, rng)
        assert cascade.inertia_signature(table)["signature"] == \
            _oracle_signature(table)
    for _ in range(40):
        table = _random_monomial_table(6, rng)
        assert cascade.inertia_signature(table)["signature"] == \
            _oracle_signature(table)


# ── the structural guard the whole design rests on ──────────────────────────

_DIMENSION_CONSTANTS = (
    "CD_DIMS", "DIVISION_ALGEBRA_DIMS", "ASSOCIATIVE_ALGEBRA_DIMS",
    "CD_MAX_DIM", "CD_DENSE_MAX_DIM", "CD_TURN_MAX_DIM",
    "CD_COMPOSE_MAX_DIM", "CD_ADDRESS_VERIFIED_DIM", "IMAG_DIMS",
    "ALGEBRA_NAMES", "cd_basis_product", "cd_mult",
)

_OP_SOURCE_NAMES = (
    "inertia_signature", "_congruence_inertia", "_real_gram",
    "_structure_table", "_native_inertia", "_pin_magnitude",
    "_pin_orientation", "_strip_common_factor", "_primitive",
    "_hyperbolic_fold", "_first_nonzero_diagonal", "_first_nonzero_offdiagonal",
    "_full_square",
)


def _op_source():
    """The concatenated source of the op and every helper it reaches, minus
    docstrings — the executable surface, so prose cannot trip the guard."""
    import ast
    import inspect
    chunks = []
    for name in _OP_SOURCE_NAMES:
        fn = getattr(cd, name)
        tree = ast.parse(inspect.getsource(fn).lstrip())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.Module, ast.ClassDef)):
                body = list(node.body)
                if (body and isinstance(body[0], ast.Expr)
                        and isinstance(body[0].value, ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    node.body = body[1:] or [ast.Pass()]
        chunks.append(ast.unparse(tree))
    return "\n".join(chunks)


@pytest.mark.parametrize("constant", _DIMENSION_CONSTANTS)
def test_op_never_consults_a_declared_dimension(constant):
    """The load-bearing one. An implementation that reads ``IMAG_DIMS`` (or any
    other baked-in ladder constant) returns the textbook answer for split-𝕆 and
    is worthless. The dimension may come from ``len(table)`` and nowhere else.
    """
    assert constant not in _op_source(), (
        f"inertia_signature reaches {constant}; it must read the table only")


def test_op_never_calls_abs_or_compares_floats():
    """Sign is the Class K pin-slot ∘ Class C re-orientation, never ``abs()``
    (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``), and the
    verdict is a comparison of two integer sums — no epsilon, no tolerance,
    and deliberately no float fast path."""
    src = _op_source()
    assert not re.search(r"\babs\s*\(", src)
    assert "float(" not in src
    assert "math." not in src
    assert not re.search(r"\b1e-\d", src)


def test_re_x_squared_is_summed_from_the_table_not_the_coordinate_form():
    """The pathology guard. ``Re(x·x) = a² − |v|²`` is INPUT-BLIND: it agrees
    with the real read 4000/4000 on 𝕆 but only 854/4000 on split-𝕆, and stays
    wrong at infinite precision — a substitution error, not a precision one.

    Checked behaviourally rather than by grep, because the shortcut is
    identifiable by its answers: on split-𝕆, ``a² − |v|²`` and the true
    ``Re(x·x)`` disagree, so an implementation using it cannot match here.
    """
    dim = 8
    rng = random.Random(271828)
    disagreements = 0
    for _ in range(400):
        x = [rng.randint(-4, 4) for _ in range(dim)]
        true_real_square = _integer_product(SPLIT_OCTONION, x, x)[0]
        coordinate_form = x[0] * x[0] - sum(v * v for v in x[1:])
        if true_real_square != coordinate_form:
            disagreements += 1
    # They differ on split-𝕆 — which is exactly why the op must not use it.
    assert disagreements > 200, disagreements
    # And the op tracks the TRUE read: its Gram diagonal is 2·Re(e_i·e_i).
    gram = cd._real_gram(cd._structure_table(SPLIT_OCTONION), "trace")
    assert [gram[i][i] for i in range(dim)] == \
        [2 * SPLIT_OCTONION[i][i][0] for i in range(dim)]
    # …and it is NOT the definite pattern the coordinate form would produce.
    assert [gram[i][i] for i in range(dim)] != [2] + [-2] * 7


def test_c_peer_source_has_no_abs_and_no_float():
    """The same discipline on the C side."""
    path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))),
        "c", "src", "srmech_algebra_inertia.c")
    if not os.path.exists(path):        # sdist / wheel-only checkout
        pytest.skip("C sources not present in this checkout")
    with io.open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    code = "\n".join(ln for ln in text.splitlines()
                     if not ln.lstrip().startswith("*")
                     and not ln.lstrip().startswith("/*"))
    assert not re.search(r"\babs\s*\(", code)
    assert not re.search(r"\bllabs\s*\(", code)
    assert "double" not in code and "float" not in code


# ── input contract ──────────────────────────────────────────────────────────

def test_rejects_a_ragged_table():
    with pytest.raises(ValueError):
        cascade.inertia_signature([[[1, 0], [0, 1]]])
    with pytest.raises(ValueError):
        cascade.inertia_signature([])


def test_rejects_inexact_structure_constants():
    with pytest.raises(TypeError):
        cascade.inertia_signature([[[1.0]]])
    with pytest.raises(TypeError):
        cascade.inertia_signature([[[True]]])


def test_accepts_tuples_as_well_as_lists():
    assert cascade.inertia_signature(
        tuple(tuple(tuple(c) for c in row) for row in OCTONION)
    )["signature"] == (1, 7, 0)


def test_flat_and_module_names_are_the_same_object():
    assert cascade.inertia_signature is cd.inertia_signature


# ── C/Python parity ─────────────────────────────────────────────────────────

def _assert_paths_agree(table, form):
    """C peer vs the pure bignum path: identical signature AND witness."""
    tbl = cd._structure_table(table)
    native = cd._native_inertia(tbl, form)
    pure = cd._congruence_inertia(cd._real_gram(tbl, form))
    assert native is not None, (len(table), form)
    assert tuple(native[:3]) == tuple(pure[:3]), (len(table), form)
    nw = cd._primitive(list(native[3])) if native[3] else None
    pw = cd._primitive(list(pure[3])) if pure[3] else None
    assert nw == pw, (len(table), form)


@SKIP_IF_NO_NATIVE
@pytest.mark.parametrize("form", INERTIA_FORMS)
@pytest.mark.parametrize("name,table", [
    ("R", REAL), ("C", COMPLEX), ("H", QUATERNION), ("O", OCTONION),
    ("S16", SEDENION), ("dual", DUAL_NUMBERS),
    ("split-C", SPLIT_COMPLEX), ("split-H", SPLIT_QUATERNION),
    ("split-O", SPLIT_OCTONION),
])
def test_c_peer_agrees_on_every_named_algebra(name, table, form):
    """Per ADR-0009 the capability is the invariant across projections, so the
    SPLIT algebras and the degenerate one are differential-tested against C
    explicitly — not only the shipped ladder, where the answer is forced."""
    _assert_paths_agree(table, form)


@SKIP_IF_NO_NATIVE
@pytest.mark.parametrize("form", INERTIA_FORMS)
def test_c_peer_agrees_on_300_random_tables(form):
    """Differential test on inputs where nothing forces the answer, including
    the diagonal-pinned family that sits exactly at the op's ceiling."""
    rng = random.Random(11235)
    for _ in range(100):
        _assert_paths_agree(_random_monomial_table(8, rng), form)
    for _ in range(100):
        _assert_paths_agree(_random_general_table(6, rng), form)
    for _ in range(100):
        _assert_paths_agree(_diagonal_pinned_table(8, rng), form)


@SKIP_IF_NO_NATIVE
def test_c_peer_rejects_an_unknown_form():
    import ctypes
    need = _native.LIB.srmech_algebra_inertia_ws_bound(ctypes.c_size_t(8))
    flat = [v for row in OCTONION for cell in row for v in cell]
    buf = (ctypes.c_int64 * len(flat))(*flat)
    outs = [ctypes.c_int() for _ in range(4)]
    wit = (ctypes.c_int64 * 8)()
    ws = ctypes.create_string_buffer(int(need))
    rc = _native.LIB.srmech_algebra_inertia_signature(
        buf, ctypes.c_size_t(8), ctypes.c_int(7), ws, ctypes.c_size_t(int(need)),
        ctypes.byref(outs[0]), ctypes.byref(outs[1]), ctypes.byref(outs[2]),
        ctypes.byref(outs[3]), wit)
    assert rc != 0


@SKIP_IF_NO_NATIVE
def test_c_ws_bound_is_honest():
    """A short arena must be REFUSED, not silently under-run."""
    import ctypes
    need = _native.LIB.srmech_algebra_inertia_ws_bound(ctypes.c_size_t(8))
    assert need > 0
    assert _native.LIB.srmech_algebra_inertia_ws_bound(ctypes.c_size_t(0)) == 0
    assert _native.LIB.srmech_algebra_inertia_ws_bound(
        ctypes.c_size_t(4096)) == 0            # past the documented max dim
    flat = [v for row in OCTONION for cell in row for v in cell]
    buf = (ctypes.c_int64 * len(flat))(*flat)
    outs = [ctypes.c_int() for _ in range(4)]
    wit = (ctypes.c_int64 * 8)()
    short = ctypes.create_string_buffer(int(need) - 1)
    rc = _native.LIB.srmech_algebra_inertia_signature(
        buf, ctypes.c_size_t(8), ctypes.c_int(0), short,
        ctypes.c_size_t(int(need) - 1),
        ctypes.byref(outs[0]), ctypes.byref(outs[1]), ctypes.byref(outs[2]),
        ctypes.byref(outs[3]), wit)
    assert rc != 0


def test_pure_path_is_exact_beyond_the_c_int64_ceiling():
    """The Python path carries no magnitude ceiling: an absurd table that would
    overflow int64 in C still answers exactly (C declines with OVERFLOW and the
    op falls through)."""
    big = 10 ** 30
    table = [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]
    table[0][0][0] = big
    table[1][1][0] = -big
    r = cascade.inertia_signature(table)
    assert r["signature"] == (1, 1, 0)
    assert r["witness_real_square"] < 0
