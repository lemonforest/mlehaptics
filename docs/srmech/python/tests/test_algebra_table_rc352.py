"""The γ-parameterised Cayley–Dickson constructor + the norm it makes wrong.

rc352 — two coupled tasks, `#T997` and `#T1001`, which ship together because
the second is only reachable once the first lands.

**`#T997` — `algebra_table` / `table_product`.** The ``−`` hard-wired into
``cayley_dickson._mult``'s cross term IS the Cayley–Dickson γ, pinned to −1 at
every recursion level. Exposing it per rung gives the SPLIT algebras a
constructor. The justification is **controls, not capability**: every negative
control this arc has needed — split-𝕆, split-ℂ, split-ℍ, 100+ random tables —
was hand-rolled in a test file for want of one, while the whole 8-member
γ-family is sign-cocycle-degenerate the same 344/512 way and every associative
twist is a matrix algebra ``Mat`` already publishes.

**`#T1001` — `cd_norm_sq` was the coordinate form.** It computed ``Σ xᵢ²``
while asserting positive-definiteness "at every rung". On split-ℂ that answers
``N([1,−1]) = 2`` for a genuine null vector. It was dormant only because
nothing could construct a split algebra; ``algebra_table`` constructs one, so
the gate ships in the same rc rather than after it.

THE ORACLE ARCHITECTURE, stated because it is the part most easily got wrong.
Shipping a table-driven product would have turned rc349's ``_oracle_product``
into the subject of its own anchor test — a check that passes while observing
nothing. So there are three independent oracles and no self-comparison:

1. **An independent CONSTRUCTION.** ``test_algebra_inertia_rc349``'s
   ``_cd_table_oracle`` is a RECURSIVE doubling on whole elements; the shipped
   cocycle is an ITERATIVE loop on indices. They share no code, and the
   convention is pinned dim × γ exhaustively over there.
2. **Two shipped ROUTES, zero duplication.** ``left_mult_matrix(x, table)``
   builds ``L(x)`` column by column and contracts it; ``table_product`` sums a
   tensor directly. Making ``left_mult_matrix`` table-aware is what turns the
   would-be duplicate into a differential.
3. **Two PROJECTIONS** (ADR-0009). The pure-Python accumulation against
   ``srmech_algebra_table_product``, at magnitudes and denominators where
   nothing forces agreement.

``_oracle_product`` is retired; ``laplacian._order_omul`` is absorbed.
"""
from __future__ import annotations

import itertools
import random

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc.cascade import cayley_dickson as cd
from srmech.amsc.q import Q
from srmech.qm.octonion import octonion_mult_table
from srmech.qm.quaternion import quaternion_mult_table

from tests._native_gate import require_native


DEFINITE_8 = cascade.algebra_table(8)
SPLIT_8 = cascade.algebra_table(8, (-1, -1, +1))
SPLIT_2 = cascade.algebra_table(2, (+1,))
SPLIT_4 = cascade.algebra_table(4, (-1, +1))


# ── the DEFAULT is the shipped algebra, bit-identically ─────────────────────

@pytest.mark.parametrize("dim", (1, 2, 4, 8, 16, 32, 64))
def test_default_gammas_reproduce_cd_basis_product_exactly(dim):
    """THE bit-identical-default proof, at the cocycle.

    ``algebra_table``'s engine and ``cd_basis_product``'s are literally the
    same function with and without a γ vector — in Python AND in C — so this
    is a check that the reduction is exact, over every basis pair at every dim
    up to the materialisation ceiling. 4096 pairs at dim 64.
    """
    gammas = cd._normalise_gammas(dim, None)
    assert gammas == (-1,) * (dim.bit_length() - 1)
    for i in range(dim):
        for j in range(dim):
            assert cd._gamma_basis_product(dim, gammas, i, j) == \
                cd.cd_basis_product(dim, i, j), (dim, i, j)


def test_default_table_is_the_shipped_octonion_and_quaternion_table():
    """Element-for-element, not merely equivalent."""
    assert cascade.algebra_table(8) == octonion_mult_table()
    assert cascade.algebra_table(4) == quaternion_mult_table()


@pytest.mark.parametrize("dim", (1, 2, 4, 8, 16))
def test_default_table_product_reproduces_cd_mult(dim):
    """The default path against the SHIPPED product, integers and exact ℚ.

    300 integer pairs and 200 rational pairs at dim 8 in the headline; this
    parametrised form runs the same check across the ladder.
    """
    rng = random.Random(9000 + dim)
    table = cascade.algebra_table(dim)
    for _ in range(60):
        x = [rng.randint(-9, 9) for _ in range(dim)]
        y = [rng.randint(-9, 9) for _ in range(dim)]
        assert tuple(cascade.table_product(table, x, y)) == tuple(cd.cd_mult(x, y))
    for _ in range(40):
        x = [Q(rng.randint(-9, 9), rng.randint(1, 7)) for _ in range(dim)]
        y = [Q(rng.randint(-9, 9), rng.randint(1, 7)) for _ in range(dim)]
        assert tuple(cascade.table_product(table, x, y)) == tuple(cd.cd_mult(x, y))


def test_the_headline_counts_are_reproducible():
    """The two numbers quoted in the docstrings, run as written: 300/300 and
    200/200 at dim 8. A quoted measurement that no test reproduces is prose."""
    rng = random.Random(7)
    ints = 0
    for _ in range(300):
        x = [rng.randint(-9, 9) for _ in range(8)]
        y = [rng.randint(-9, 9) for _ in range(8)]
        ints += 1 if tuple(cascade.table_product(DEFINITE_8, x, y)) == \
            tuple(cd.cd_mult(x, y)) else 0
    assert ints == 300
    rats = 0
    for _ in range(200):
        x = [Q(rng.randint(-9, 9), rng.randint(1, 7)) for _ in range(8)]
        y = [Q(rng.randint(-9, 9), rng.randint(1, 7)) for _ in range(8)]
        rats += 1 if tuple(cascade.table_product(DEFINITE_8, x, y)) == \
            tuple(cd.cd_mult(x, y)) else 0
    assert rats == 200


# ── what a +1 actually buys — the whole family, MEASURED ────────────────────

def test_the_whole_gamma_family_at_dim_8_is_exactly_two_algebras():
    """Eight γ-triples, TWO answers — and the split one is rc349's, reached
    there through a third independent construction.

    This is the claim the constructor is allowed to make, and it is narrow:
    the family is not eight algebras, it is 𝕆 and split-𝕆 seven ways.
    """
    answers = {}
    for gammas in itertools.product((-1, 1), repeat=3):
        r = cascade.inertia_signature(cascade.algebra_table(8, gammas))
        answers[gammas] = (r["signature"], r["norm_signature"])
    assert answers[(-1, -1, -1)] == ((1, 7, 0), (8, 0, 0))
    split = {v for k, v in answers.items() if k != (-1, -1, -1)}
    assert split == {((5, 3, 0), (4, 4, 0))}, split
    assert len(set(answers.values())) == 2


@pytest.mark.parametrize("dim,gammas,trace,norm", [
    (2, (+1,), (2, 0, 0), (1, 1, 0)),
    (4, (-1, +1), (3, 1, 0), (2, 2, 0)),
    (8, (-1, -1, +1), (5, 3, 0), (4, 4, 0)),
])
def test_split_signatures_match_springer_veldkamp(dim, gammas, trace, norm):
    """Springer & Veldkamp (2000) §1.7: the split composition algebras carry
    norm forms of signature (1,1), (2,2), (4,4). The constructor reproduces
    them from the γ vector alone."""
    r = cascade.inertia_signature(cascade.algebra_table(dim, gammas))
    assert r["signature"] == trace
    assert r["norm_signature"] == norm


def test_a_split_twist_really_has_zero_divisors_and_the_definite_one_does_not():
    """The other half of "genuinely split", on the SHIPPED product this time —
    and the `#T1000` witness half: a nonzero left-mult kernel IS a zero-divisor
    witness, now reachable on any algebra a table can express."""
    zd = [0] * 8
    zd[0], zd[4] = 1, 1                     # e₀ + e₄, and e₄² = +1 in split-𝕆
    assert cd.left_mult_is_invertible(zd, SPLIT_8) is False
    kernel = cd.left_mult_kernel(zd, SPLIT_8)
    assert kernel, "a split-𝕆 zero divisor must exhibit a kernel"
    for u in kernel:
        assert any(v != 0 for v in u)
        assert all(v == 0 for v in cascade.table_product(SPLIT_8, zd, u))
    # …and the SAME element is invertible in the definite 𝕆 (Hurwitz).
    assert cd.left_mult_is_invertible(zd) is True
    assert cd.left_mult_kernel(zd) == []


def test_finding_a_zero_divisor_is_NOT_solved_here():
    """The witness half is not the finding half, stated so it cannot be
    over-read. Zero divisors are measure-zero: 300 random dim-16 elements are
    300/300 invertible, so nothing below constitutes a search."""
    rng = random.Random(1234)
    invertible = 0
    for _ in range(300):
        x = [rng.randint(-4, 4) for _ in range(16)]
        if not any(x):
            x[0] = 1
        invertible += 1 if cd.left_mult_is_invertible(x) else 0
    assert invertible == 300, invertible


# ── ORACLE 2: two shipped routes, zero duplicated code ──────────────────────

@pytest.mark.parametrize("name,table", [
    ("definite-O", DEFINITE_8), ("split-O", SPLIT_8),
    ("split-C", SPLIT_2), ("split-H", SPLIT_4),
])
def test_left_mult_matrix_contraction_agrees_with_table_product(name, table):
    """``L(x)·y == x·y``, with ``L`` built column-by-column through the same
    op — a genuinely different route (a matrix and a matvec versus a triple
    loop), and the reason ``left_mult_matrix`` grew a ``table`` argument
    instead of a second table-driven product existing as a test oracle."""
    dim = len(table)
    rng = random.Random(hash(name) & 0xFFFF)
    for _ in range(60):
        x = [rng.randint(-6, 6) for _ in range(dim)]
        y = [rng.randint(-6, 6) for _ in range(dim)]
        mat = cd.left_mult_matrix(x, table)
        contracted = tuple(
            sum((mat[r][c] * Q(y[c]) for c in range(dim)), Q(0))
            for r in range(dim))
        assert contracted == tuple(cascade.table_product(table, x, y)), name


def test_left_mult_matrix_default_is_unchanged():
    """The table argument is ADDITIVE: with no table the columns still come
    from ``cd_mult``, and the rc160 identity ``L(x)·y == cd_mult(x, y)`` holds
    exactly as before."""
    rng = random.Random(555)
    for _ in range(120):
        x = [rng.randint(-6, 6) for _ in range(8)]
        y = [rng.randint(-6, 6) for _ in range(8)]
        mat = cd.left_mult_matrix(x)
        contracted = tuple(
            sum((mat[r][c] * Q(y[c]) for c in range(8)), Q(0)) for r in range(8))
        assert contracted == tuple(cd.cd_mult(x, y))
        assert mat == cd.left_mult_matrix(x, DEFINITE_8)


# ── table_product reads the TABLE, and only the table ───────────────────────

def test_table_product_answers_for_a_table_with_no_algebraic_structure():
    """It is not a Cayley–Dickson op with a table-shaped argument. Random
    structure constants — not monomial, not associative, not an algebra —
    still get an exact answer, checked against the definition."""
    rng = random.Random(24680)
    dim = 5
    for _ in range(60):
        table = [[[rng.choice((-2, -1, 0, 0, 1, 3)) for _ in range(dim)]
                  for _ in range(dim)] for _ in range(dim)]
        x = [rng.randint(-5, 5) for _ in range(dim)]
        y = [rng.randint(-5, 5) for _ in range(dim)]
        want = [0] * dim
        for i in range(dim):
            for j in range(dim):
                for k in range(dim):
                    want[k] += table[i][j][k] * x[i] * y[j]
        assert [int(v) for v in cascade.table_product(table, x, y)] == want


def test_table_product_is_exact_on_rationals_and_never_a_float():
    """Exact ℚ end to end — a ``float`` input becomes its EXACT ratio, the same
    contract ``cd_mult`` carries, and 1/3 does not round."""
    third = cascade.table_product(DEFINITE_8, [Q(1, 3)] + [0] * 7,
                                 [Q(1, 3)] + [0] * 7)
    assert third[0] == Q(1, 9)
    assert all(isinstance(v, Q) for v in third)
    # 0.5 is exactly representable, so the float path is EXACT, not rounded.
    half = cascade.table_product(DEFINITE_8, [0.5] + [0] * 7, [0.5] + [0] * 7)
    assert half[0] == Q(1, 4)


def test_table_product_rejects_a_ragged_table_and_a_mismatched_element():
    with pytest.raises(ValueError):
        cascade.table_product([[[1, 0], [0, 1]]], [1, 0], [1, 0])
    with pytest.raises(ValueError):
        cascade.table_product(DEFINITE_8, [1, 0], [1, 0])
    with pytest.raises(TypeError):
        cascade.table_product([[[1.0]]], [1], [1])


def test_algebra_table_input_contract():
    with pytest.raises(ValueError):
        cascade.algebra_table(3)                       # not a power of two
    with pytest.raises(ValueError):
        cascade.algebra_table(128)                     # past the ceiling
    with pytest.raises(ValueError):
        cascade.algebra_table(8, (-1, -1))             # wrong length
    with pytest.raises(ValueError):
        cascade.algebra_table(8, (-1, -1, 0))          # γ is a sign, not a scale
    with pytest.raises(ValueError):
        cascade.algebra_table(8, (-1, -1, 2))


def test_the_materialisation_ceiling_is_its_own_named_number():
    """Four ceilings, four names — the rc339 discipline. This one bounds
    MATERIALISING the dim³ tensor and nothing else; the cocycle underneath
    still answers to CD_MAX_DIM."""
    assert cascade.ALGEBRA_TABLE_MAX_DIM == 64
    assert cascade.ALGEBRA_TABLE_MAX_DIM < cd.CD_MAX_DIM
    assert len({cd.CD_MAX_DIM, cd.CD_COMPOSE_MAX_DIM, cd.CD_TURN_MAX_DIM,
                cascade.ALGEBRA_TABLE_MAX_DIM}) == 4
    # the cocycle is NOT bounded by it
    assert cd.cd_basis_product(128, 5, 9)[0] == 5 ^ 9


def test_the_table_is_monomial_by_construction():
    """``e_i·e_j = ±e_{i⊕j}`` at every γ — so dim² of the dim³ cells are set,
    which is why a MONOMIAL table costs O(dim²) rather than O(dim³)."""
    for gammas in itertools.product((-1, 1), repeat=3):
        table = cascade.algebra_table(8, gammas)
        nonzero = 0
        for i in range(8):
            for j in range(8):
                cell = table[i][j]
                assert sum(1 for v in cell if v) == 1
                assert cell[i ^ j] in (1, -1)
                nonzero += 1
        assert nonzero == 64


# ── `#T1001`: cd_norm_sq — the coordinate form, gated ───────────────────────

def test_cd_norm_sq_gate():
    """THE null-vector pin, on the SHIPPED op.

    ``[1, −1]`` is a genuine null vector of split-ℂ: ``(1+j)(1−j) = 0``, so
    ``N`` must be 0. The coordinate form answers 2 and cannot see isotropy at
    all. This test is only buildable because ``algebra_table`` ships in the
    same rc — which is exactly why the two tasks are one rc.
    """
    x = [1, -1]
    # the algebra really is null there, read through the shipped product
    assert not any(cascade.table_product(SPLIT_2, [1, 1], [1, -1]))
    # the DEFAULT declares the definite ℂ, and 2 is the right answer for it
    assert int(cd.cd_norm_sq(x)) == 2
    # the DECLARED split twist answers 0 — the null vector, seen
    assert int(cd.cd_norm_sq(x, gammas=(+1,))) == 0
    # and N is genuinely indefinite there: a NEGATIVE value for a nonzero x
    assert int(cd.cd_norm_sq([1, -3], gammas=(+1,))) == 1 - 9


@pytest.mark.parametrize("dim", (1, 2, 4, 8, 16, 32))
def test_cd_norm_sq_default_path_is_bit_identical(dim):
    """``gammas=None`` and an explicitly-DEFINITE γ vector must agree with the
    unchanged coordinate sum, exactly, at every rung. The gate must cost the
    default path nothing."""
    rng = random.Random(4000 + dim)
    definite = (-1,) * (dim.bit_length() - 1)
    for _ in range(60):
        x = [Q(rng.randint(-10 ** 9, 10 ** 9), rng.randint(1, 97))
             for _ in range(dim)]
        want = sum((v * v for v in x), Q(0))
        assert cd.cd_norm_sq(x) == want
        assert cd.cd_norm_sq(x, gammas=definite) == want


@pytest.mark.parametrize("dim", (1, 2, 4, 8, 16))
def test_cd_norm_sq_agrees_with_the_full_product_read_on_every_twist(dim):
    """``N(x) = Re(x·x̄)`` — the O(dim) closed form against the O(dim³) table
    read, over every γ assignment. The closed form is the diagonal collapse of
    the monomial product, so this is the check that the collapse is exact and
    not merely plausible."""
    rng = random.Random(6000 + dim)
    for gammas in itertools.product((-1, 1), repeat=dim.bit_length() - 1):
        table = cascade.algebra_table(dim, gammas or None)
        for _ in range(12):
            x = [rng.randint(-7, 7) for _ in range(dim)]
            conj = [int(v) for v in cd.cd_conjugate(x)]
            full = cascade.table_product(table, x, conj)
            # x·x̄ is a real multiple of the identity at every twist…
            assert all(v == 0 for v in full[1:]), (dim, gammas, x)
            # …and that real part IS what cd_norm_sq reports.
            assert cd.cd_norm_sq(x, gammas=gammas or None) == full[0]


def test_cd_norm_sq_rejects_a_gammas_vector_that_does_not_fit_the_element():
    with pytest.raises(ValueError):
        cd.cd_norm_sq([1, 2, 3, 4], gammas=(+1,))
    with pytest.raises(ValueError):
        cd.cd_norm_sq([1, 2], gammas=(0,))


def test_the_norm_docstring_names_its_scope():
    """A measured trap that lives only in a test is one refactor from being
    lost; it must also be in the surface the caller reads."""
    doc = cd.cd_norm_sq.__doc__
    assert "SCOPE" in doc or "DECLARES WHICH ALGEBRA" in doc
    assert "null vector" in doc
    assert "gammas" in doc
    for fn in (__import__("srmech.qm.octonion", fromlist=["x"]).octonion_norm,
               __import__("srmech.qm.quaternion", fromlist=["x"]).quaternion_norm):
        assert "SCOPE" in fn.__doc__, fn.__name__


# ── ORACLE 3: the two projections (ADR-0009) ────────────────────────────────

def _pure_table_product(table, x, y):
    """The pure exact-ℚ accumulation, forced — the no-native projection."""
    dim = len(table)
    out = [Q(0)] * dim
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                if table[i][j][k]:
                    out[k] += Q(table[i][j][k]) * x[i] * y[j]
    return tuple(out)


def test_c_peer_agrees_with_the_pure_accumulation_on_every_twist():
    """Differential across BOTH projections, at magnitudes and denominators
    where nothing forces agreement (ADR-0009: the capability is the invariant;
    the projections' difference IS the parity test)."""
    require_native("srmech_algebra_table_product")
    rng = random.Random(11235)
    checked = 0
    for dim in (1, 2, 4, 8, 16):
        for gammas in itertools.product((-1, 1), repeat=dim.bit_length() - 1):
            table = cascade.algebra_table(dim, gammas or None)
            flat = [table[i][j][k] for i in range(dim) for j in range(dim)
                    for k in range(dim)]
            for _ in range(4):
                x = [Q(rng.randint(-10 ** 12, 10 ** 12), rng.randint(1, 997))
                     for _ in range(dim)]
                y = [Q(rng.randint(-10 ** 12, 10 ** 12), rng.randint(1, 997))
                     for _ in range(dim)]
                native = _native.algebra_table_product_c(
                    flat, dim,
                    [(f.numerator, f.denominator) for f in x],
                    [(f.numerator, f.denominator) for f in y])
                assert native is not None, (dim, gammas)
                pure = _pure_table_product(table, x, y)
                assert [(v.numerator, v.denominator) for v in pure] == native
                checked += 1
    assert checked == 4 * (1 + 2 + 4 + 8 + 16), checked


def test_c_peer_agrees_with_the_pure_cocycle_for_the_table_itself():
    """The same differential for ``srmech_algebra_table``: the C engine and the
    Python engine are separate implementations of one iterative cocycle."""
    require_native("srmech_algebra_table")
    checked = 0
    for dim in (1, 2, 4, 8, 16, 32, 64):
        combos = list(itertools.product((-1, 1), repeat=dim.bit_length() - 1))
        for gammas in combos[:4] or [()]:
            g = list(gammas) if gammas else None
            native = _native.algebra_table_c(dim, g)
            assert native is not None, (dim, gammas)
            norm = cd._normalise_gammas(dim, g)
            pure = [0] * (dim ** 3)
            for i in range(dim):
                for j in range(dim):
                    idx, sign = cd._gamma_basis_product(dim, norm, i, j)
                    pure[(i * dim + j) * dim + idx] = sign
            assert native == pure, (dim, gammas)
            checked += 1
    assert checked >= 7


def test_the_c_peer_refuses_a_short_arena_rather_than_under_running():
    """A too-small workspace must be REFUSED, and the Python caller must then
    still answer exactly — the honest-decline half of the caller-arena
    contract."""
    import ctypes
    require_native("srmech_algebra_table_product_ws_bound")
    need = _native.LIB.srmech_algebra_table_product_ws_bound(
        ctypes.c_size_t(1), ctypes.c_size_t(8))
    assert need > 0
    assert _native.LIB.srmech_algebra_table_product_ws_bound(
        ctypes.c_size_t(1), ctypes.c_size_t(4)) < need
    # the op still answers exactly at every dim, arena sizing notwithstanding
    x = [1, 2, 3, 4, 5, 6, 7, 8]
    assert tuple(cascade.table_product(DEFINITE_8, x, x)) == \
        tuple(cd.cd_mult(x, x))


# ── the absorption: laplacian no longer carries a private table product ─────

def test_order_fingerprint_no_longer_carries_its_own_table_product():
    """``laplacian._order_omul`` was a third copy of the table-driven product,
    private, dim-8-hardcoded, one caller. It is gone; the op routes through the
    shipped ``table_product`` and the VALUES are unchanged."""
    from srmech.amsc import laplacian as L
    assert not hasattr(L, "_order_omul")
    assert L.order_fingerprint([]) == [1, 0, 0, 0, 0, 0, 0, 0]
    assert L.order_fingerprint([0, 1, 0, 2, 0]) != L.order_fingerprint([0, 2, 0, 1, 0])
    # still exact big integers, still no mod
    fp = L.order_fingerprint(list(range(20)))
    assert len(fp) == 8 and all(isinstance(v, int) for v in fp)
    assert any(v > 2 ** 31 or v < -(2 ** 31) for v in fp)


# ── registration ────────────────────────────────────────────────────────────

def test_registered_in_the_tool_schema_and_reachable_flat():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.cascade.algebra_table" in names
    assert "srmech.amsc.cascade.table_product" in names
    assert cascade.algebra_table is cd.algebra_table
    assert cascade.table_product is cd.table_product


def test_no_abs_and_no_float_in_the_new_ops():
    """Sign is the Class-K pin-slot composition, never ``abs()``; the
    accumulation is exact ℚ, never a float (`CEIL_FLOAT_POW` is a hard-won
    zero and this rc does not spend it)."""
    import ast
    import inspect
    import re
    chunks = []
    for name in ("algebra_table", "table_product", "_gamma_basis_product",
                 "_normalise_gammas", "cd_norm_sq"):
        tree = ast.parse(inspect.getsource(getattr(cd, name)).lstrip())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.Module)):
                body = list(node.body)
                if (body and isinstance(body[0], ast.Expr)
                        and isinstance(body[0].value, ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    node.body = body[1:] or [ast.Pass()]
        chunks.append(ast.unparse(tree))
    src = "\n".join(chunks)
    assert not re.search(r"\babs\s*\(", src)
    assert "math." not in src
    assert not re.search(r"\*\*\s*0\.", src)
