"""v0.9.0rc444 (`#T1152`) — ``triality_companions`` computed exact ℚ and threw it
away, and nothing could ask for it back.

THE DEFECT, in one line. ``_solve_companions`` ends::

    sol = _exact_solve_normal_equations(g, c, nvar)   # exact ℚ  -> List[Q]
    b_companion = [[float(sol[i * _DIM + j]) ...]]    # discarded HERE

The exact rational was already computed. ``exact=True`` is ``return sol``
instead of ``[float(x) for x in sol]`` — no new computation, no new type
(:class:`~srmech.math.q.Q` ships with 12 ``srmech_qmat_*`` C peers, so the
projection gap `#T1141` cares about is already closed), no new C symbol, ABI
unchanged at 17.

WHY THIS IS NOT A NEW CONTRACT. ``exact=`` is a SHIPPED convention on four ops,
three of them Class-L linear algebra — the same family as the companion solve:
``dense_solve(A, B, *, exact=False)`` → ``list[list[Q]]`` (or ``list[Q]`` for a
vector RHS), ``schur_complement(L, idx, *, exact=False)`` → ``list[list[Q]]``,
``dirichlet_to_neumann`` (its alias) → the same, and
``jacobi_eigvals(matrix, ..., *, exact=False)`` → the exact-arithmetic route.
Over the live 663-entry registry, **57 ops (~9%) already carry a carrier/regime
selector** (``element_type`` 22, ``table`` 19, ``mode`` 9, ``exact`` 4,
``gammas`` 2, ``with_path`` 1).

THE CENSUS THAT SET THE SCOPE (rc444, structural AST pass over the package —
"produces exact ℚ, narrows to float/complex at the return boundary, declares no
``exact=``"). 218 functions carry an exact-production signal; 4 declare
``exact=``; **5 direct hits + 12 propagating callers**, of which exactly ONE
family is a genuine candidate:

* **(a) exactness available and discarded** — ``_solve_companions`` →
  ``triality_companions``. THIS rc.
* **(b) float inherent to the contract** — ``mat_solve`` (+ ``mat_lstsq`` /
  ``construct_eta_from_eigendecomposition`` / ``lmmse`` / ``map_ml``): its input
  is ALREADY a float64 ``Mat`` and its ``_solve_exact`` call is the no-native
  COMPLETE implementation of a float problem; the caller-facing exact escape
  already exists one level up as ``dense_solve(exact=True)``. ``Poly.from_floats``
  / ``QPoly.from_floats``: the ``float()`` is an INPUT promotion (float → exact
  ℚ), the opposite direction. ``_recover_op_spectral``: snaps a FLOAT eigenvalue
  to ℚ for a threshold test and returns bools. ``_decanon``: deserialisation.
* **(c) precedent** — the four ``exact=`` ops above.

**``so8.py`` was checked explicitly and is NOT a candidate** (it was the brief's
prime suspect, as ``triality``'s direct sibling sharing ``_epq_basis`` /
``_epq_coords``). Measured: so8's only exact-ℚ use is ``_rank_exact``, which
takes FLOAT columns, snaps them to ℚ, and returns an ``int`` rank — there is no
rational to preserve. ``g2_subalgebra()`` entries are the 5 integers
``{-4,-2,0,2,4}`` (float64-exact, nothing lost); ``so7_subalgebra()`` entries are
genuinely irrational (``±√3/2``, ``±1/√6``, ``±1/√2``, from an orthonormalisation
/ SVD nullspace), so no exact ℚ exists to return. And so8 never consumes the
companion solve — ``triality`` imports FROM so8, not the reverse.

WHERE THE FLOAT PATH ACTUALLY LOSES — measured over 13 operator families
(``[[feedback_an_asserted_algebraic_property_is_not_a_measured_one]]``):

* **Consistent (skew, ``A ∈ so(8)``) operands lose NOTHING.** Exact denominators
  come back in ``{1, 2}`` × the operand's own — over a single ``E_pq``, a
  6-generator sum, an integer-weighted sum, all 28 slots at distinct primes, the
  op's own ``±1/2`` output fed back in, and ``/3`` / ``/10`` float scalings:
  **0 of 128** entries non-representable in every case. So on the whole in-tree
  path ``exact=True`` returns the SAME VALUES — an honest carrier, not new
  information. That is itself worth pinning, and leg 2 does.
* **Inconsistent (non-skew) operands DO lose.** Off ``so(8)`` Cartan's relation
  has no solution, the gauge-pinned least-squares MIXES right-hand-side entries
  through the integer Gram's rational RREF, and denominators grow past ``{1, 2}``
  (measured ``{1, 4}`` / ``{1, 8}``). Compose with a non-dyadic float operand and
  the numerator outruns the 53-bit significand: on ``(1/7)·M`` for a dense
  non-skew integer ``M``, **8 of 128** entries were not float64-representable.
* **THE REAL PRIZE IS THE EXACT ℚ *INPUT*.** ``_as_8x8`` ends in ``float(x)``, so
  it NARROWS at the input boundary too: a caller's ``Q(1, 3)`` became
  ``0.3333333333333333`` before the solve ran. An ``exact=`` that still floated
  its own operand would be exact about a DIFFERENT operator, so the exact path
  routes through the new :func:`~srmech.physics.qm.triality._as_8x8_exact` and
  stays exact end-to-end. Cartan's relation is LINEAR in ``(A, B, C)``, so
  ``Q(1,3)·E_01`` has companions exactly ``±1/6`` — and NEITHER ``1/6`` nor
  ``1/3`` is a float64, so **rc443's linearity law
  ``companions(k·A) = k·companions(A)`` now holds EXACTLY** where the float path
  can only approach it. This is the assertion rc443 could not make.

A REAL FIND ALONG THE WAY — the ``fractions.Fraction`` prose was stale, in the
SHIPPED registry. Three precedent docstrings said the exact solve happens "in
:class:`fractions.Fraction`" while promising a ``Q`` return in the same sentence,
and FIVE ``ToolEntry`` prose sites said "exact-rational Fraction solve" / "force
the exact Fraction solve" — text that reaches users through ``describe()``, the
MCP ``tools/list`` catalog and the compiled-in C registry. #845 moved the carrier
to srmech's own ``Q`` and the prose did not follow. Measured by execution (leg 4
re-measures it, so it cannot rot again): the leaves are ``srmech.math.q.Q`` and
``isinstance(leaf, fractions.Fraction)`` is ``False``. A ``Fraction`` INPUT is
still accepted (``to_q`` coerces it), which is why the stale claim stayed
plausible — but "accepts" and "computes in / returns" are different claims and
only the first was ever true. `#T1077` tracks the broader ``fractions``
adjudication; this rc fixed only the claim it measured false.

Discipline: numpy-free; **never** Python ``abs()`` — the Class-K pin-slot
:func:`srmech.cascade.magnitude` (which is ``Q``-preserving) wherever a deviation
magnitude is taken (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``);
no stdlib ``fractions`` / ``math`` / ``decimal``.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import pytest

from srmech.cascade import magnitude
from srmech.introspect.tool_schema import get_tool_schema
from srmech.math.laplacian import (dense_laplacian, dense_solve,
                                   dirichlet_to_neumann, schur_complement)
from srmech.math.mat import Mat
from srmech.math.q import Q, to_q
from srmech.physics.qm.octonion import octonion_mult_table
from srmech.physics.qm.so8 import _epq_basis
from srmech.physics.qm.triality import triality_companions

_DIM = 8
_OP = "srmech.physics.qm.triality.triality_companions"


# ─────────────────────────────────────────────────────────────────────────────
# fixtures / helpers — exact ℚ octonion algebra, no float anywhere
# ─────────────────────────────────────────────────────────────────────────────

def _e01() -> List[List[float]]:
    """The ``E_01`` generator — the operand ``_companion_maps`` iterates."""
    return _epq_basis()[0]


def _scaled_exact(rows, k: Q) -> List[List[Q]]:
    """``k · rows`` with EXACT ℚ entries (never floated)."""
    return [[to_q(rows[i][j]) * k for j in range(_DIM)] for i in range(_DIM)]


def _cartan_deviations(g_v, g_s, g_c) -> List[Q]:
    """Every nonzero EXACT-ℚ deviation from Cartan's relation
    ``g_v(x·y) = g_s(x)·y + x·g_c(y)`` over the 64 octonion basis pairs.

    Exact arithmetic end to end: ``octonion_mult_table()`` is INTEGER (the
    ``{-1, 0, +1}`` structure constants), the operator entries are promoted by
    the Class-N :func:`srmech.math.q.to_q`, and every product/sum below is ``Q``.
    No float tolerance, so an empty return means the relation holds EXACTLY —
    not "to 4e-14".

    Contractions, with ``C = octonion_mult_table()``:
        ``(e_i · e_j)_k = C[i][j][k]``
        ``g_v(e_i·e_j)_m = Σ_k g_v[m][k] · C[i][j][k]``
        ``(g_s(e_i) · e_j)_m = Σ_a g_s[a][i] · C[a][j][m]``
        ``(e_i · g_c(e_j))_m = Σ_b g_c[b][j] · C[i][b][m]``
    """
    tbl = octonion_mult_table()
    gv = [[to_q(x) for x in row] for row in _rows_of(g_v)]
    gs = [[to_q(x) for x in row] for row in _rows_of(g_s)]
    gc = [[to_q(x) for x in row] for row in _rows_of(g_c)]
    out: List[Q] = []
    for i in range(_DIM):
        for j in range(_DIM):
            for m in range(_DIM):
                lhs = Q(0)
                for k in range(_DIM):
                    cijk = tbl[i][j][k]
                    if cijk:
                        lhs = lhs + gv[m][k] * cijk
                rhs = Q(0)
                for a in range(_DIM):
                    cajm = tbl[a][j][m]
                    if cajm:
                        rhs = rhs + gs[a][i] * cajm
                for b in range(_DIM):
                    cibm = tbl[i][b][m]
                    if cibm:
                        rhs = rhs + gc[b][j] * cibm
                dev = lhs - rhs
                if dev != 0:
                    # Class-K pin-slot magnitude, never abs().
                    out.append(magnitude(dev))
    return out


def _rows_of(m) -> List[List]:
    """Nested rows of a ``Mat`` or of an already-nested ``list[list[Q]]``."""
    if isinstance(m, Mat):
        return [[m[i, j] for j in range(m.n_cols)] for i in range(m.n_rows)]
    return [list(r) for r in m]


# The rc443 float companions of ``E_01``, captured from pristine ``origin/main``
# at 3982ef4bf. Sparse ``{(row, col): value}``; every other entry is 0.0.
_RC443_B_E01: Dict[Tuple[int, int], float] = {
    (0, 1): 0.5, (2, 3): 0.5, (4, 5): 0.5, (7, 6): 0.5,
    (1, 0): -0.5, (3, 2): -0.5, (5, 4): -0.5, (6, 7): -0.5,
}
_RC443_C_E01: Dict[Tuple[int, int], float] = {
    (0, 1): 0.5, (3, 2): 0.5, (5, 4): 0.5, (6, 7): 0.5,
    (1, 0): -0.5, (2, 3): -0.5, (4, 5): -0.5, (7, 6): -0.5,
}
#: rc443's float companions of the FRACTIONAL operand ``(1/3)·E_01`` — same
#: support, value ``±0.16666666666666666``. Written as the float64 literal
#: rc443 actually returned, NOT as ``0.5 / 3`` (which is a different float).
_RC443_THIRD = 0.16666666666666666


def _sparse_equal(got, pins: Dict[Tuple[int, int], float], scale: float) -> None:
    """Assert ``got`` equals the pinned sparse pattern EXACTLY (``==``, not
    ``pytest.approx``) — a byte-identity pin, not a tolerance."""
    rows = _rows_of(got)
    for i in range(_DIM):
        for j in range(_DIM):
            expect = pins.get((i, j), 0.0)
            if expect:
                expect = scale if expect > 0 else -scale
            assert rows[i][j] == expect, (
                f"entry [{i}][{j}] moved: rc443 pinned {expect!r}, got "
                f"{rows[i][j]!r} — exact=False must be byte-identical")


# ─────────────────────────────────────────────────────────────────────────────
# LEG 1 — exactness SURVIVES exact=True and is DEMONSTRABLY LOST at exact=False
# ─────────────────────────────────────────────────────────────────────────────

def test_exactness_survives_exact_true_and_is_lost_at_exact_false() -> None:
    """``Q(1,3)·E_01`` has companions ``±1/6`` — NOT float64-representable.

    The assertion rc443 could not make. ``exact=True`` returns them with ZERO
    error; ``exact=False`` returns a float whose exact re-promotion is a
    DIFFERENT rational.
    """
    third = _scaled_exact(_e01(), Q(1, 3))

    b_exact, c_exact = triality_companions(third, exact=True)
    alphabet = {b_exact[i][j] for i in range(_DIM) for j in range(_DIM)}
    assert alphabet == {Q(0), Q(1, 6), Q(-1, 6)}, (
        f"expected the exact companions of (1/3)·E_01 to be ±1/6 by the "
        f"linearity of Cartan's relation; got {sorted(map(str, alphabet))}")

    # NOT float64-representable: promoting float(x) back gives a DIFFERENT ℚ.
    unrepresentable = [
        b_exact[i][j] for i in range(_DIM) for j in range(_DIM)
        if Q.from_float(float(b_exact[i][j])) != b_exact[i][j]
    ]
    assert len(unrepresentable) == 8, (
        f"expected 8 of 64 exact entries to be outside float64 (the ±1/6 "
        f"support of E_01's companions); got {len(unrepresentable)} — if this "
        f"is 0 the operand is no longer exercising the lossy case and leg 1 "
        f"has become vacuous")

    # exact=False on the SAME operand: information is gone.
    b_float, _c_float = triality_companions(third)
    lost = [
        (i, j) for i in range(_DIM) for j in range(_DIM)
        if to_q(b_float[i, j]) != b_exact[i][j]
    ]
    assert len(lost) == 8, (
        f"exact=False was expected to LOSE the 8 ±1/6 entries on this operand; "
        f"{len(lost)} differ. If 0, exact= is not buying anything here and the "
        f"whole rc needs re-justifying")
    i, j = lost[0]
    assert to_q(b_float[i, j]) != Q(1, 6) and magnitude(
        to_q(b_float[i, j]) - b_exact[i][j]) > 0, (
        "the float entry must differ from 1/6 by a nonzero exact amount")

    # And the exact carrier round-trips through its OWN pair with zero error.
    for i in range(_DIM):
        for j in range(_DIM):
            num, den = b_exact[i][j].as_pair()
            assert Q(num, den) == b_exact[i][j]


def test_linearity_law_holds_EXACTLY_on_the_exact_path() -> None:
    """rc443's law ``companions(k·A) = k·companions(A)`` in EXACT arithmetic.

    rc443 could only assert it to float tolerance, because both sides were
    float64. On the exact path it is an equality of rationals.
    """
    gen = _e01()
    b_unit, c_unit = triality_companions(gen, exact=True)
    for k in (Q(1, 3), Q(1, 5), Q(1, 7), Q(2, 9), Q(-1, 6)):
        b_k, c_k = triality_companions(_scaled_exact(gen, k), exact=True)
        for i in range(_DIM):
            for j in range(_DIM):
                assert b_k[i][j] == b_unit[i][j] * k, (
                    f"k={k}: g_s[{i}][{j}] is {b_k[i][j]}, expected "
                    f"{b_unit[i][j] * k} — Cartan's relation is LINEAR")
                assert c_k[i][j] == c_unit[i][j] * k


# ─────────────────────────────────────────────────────────────────────────────
# LEG 2 — the DEFAULT is byte-identical to rc443
# ─────────────────────────────────────────────────────────────────────────────

def test_default_is_byte_identical_to_rc443_integer_operand() -> None:
    """``exact=False`` on the in-tree operand: pinned to rc443's literals.

    ``E_01`` is what ``_companion_maps`` iterates, so this is the value ``S_B`` /
    ``S_C`` / ``tau`` / ``Fix(tau) = g2`` are assembled from. If it moves, the
    shipped theorems moved.
    """
    b, c = triality_companions(_e01())
    assert isinstance(b, Mat) and isinstance(c, Mat)
    assert b.shape == (_DIM, _DIM) and c.shape == (_DIM, _DIM)
    _sparse_equal(b, _RC443_B_E01, 0.5)
    _sparse_equal(c, _RC443_C_E01, 0.5)


def test_default_is_byte_identical_to_rc443_fractional_operand() -> None:
    """``exact=False`` on a FRACTIONAL operand: also pinned.

    An integer-only pin would not catch a regression on the arm rc443 fixed, so
    the ``(1/3)·E_01`` float operand is pinned at the float64 literal rc443
    returned — ``0.16666666666666666``.
    """
    gen = _e01()
    third_float = [[gen[i][j] / 3.0 for j in range(_DIM)] for i in range(_DIM)]
    b, c = triality_companions(third_float)
    _sparse_equal(b, _RC443_B_E01, _RC443_THIRD)
    _sparse_equal(c, _RC443_C_E01, _RC443_THIRD)


def test_exact_true_agrees_with_the_default_on_a_CONSISTENT_operand() -> None:
    """On a skew (consistent) operand the two paths agree VALUE-for-value.

    The measured census fact, pinned so it cannot be quietly mis-stated later:
    ``exact=True`` is an honest CARRIER change there, not new information. Only
    the inconsistent / exact-ℚ-input arms carry extra content.
    """
    b_f, c_f = triality_companions(_e01())
    b_q, c_q = triality_companions(_e01(), exact=True)
    for i in range(_DIM):
        for j in range(_DIM):
            assert float(b_q[i][j]) == b_f[i, j]
            assert float(c_q[i][j]) == c_f[i, j]
            assert Q.from_float(b_f[i, j]) == b_q[i][j], (
                "dyadic ±1/2 companions are float64-exact, so the promotion "
                "must be lossless in BOTH directions here")


def test_shape_error_is_identical_on_both_paths() -> None:
    """The declared ``ValueError`` (gated by rc434) must not depend on ``exact``."""
    for kwargs in ({}, {"exact": True}):
        with pytest.raises(ValueError, match=r"triality_companions: must be 8x8"):
            triality_companions([[1, 0], [0, 1]], **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# LEG 3 — Cartan's relation holds on the exact path IN EXACT ARITHMETIC
# ─────────────────────────────────────────────────────────────────────────────

def test_cartan_relation_holds_exactly_on_the_exact_path() -> None:
    """Zero deviations over all 64 basis pairs × 8 components, in ℚ.

    Not ``< 4e-14`` — exactly zero, for an operand whose companions are outside
    float64. The float path CANNOT make this assertion on this operand, which
    the companion test below measures.
    """
    for k in (Q(1), Q(1, 3), Q(1, 7), Q(-2, 5)):
        operand = _scaled_exact(_e01(), k)
        g_s, g_c = triality_companions(operand, exact=True)
        devs = _cartan_deviations(operand, g_s, g_c)
        assert devs == [], (
            f"k={k}: Cartan's relation must close EXACTLY on the exact path; "
            f"{len(devs)} nonzero ℚ deviations, largest "
            f"{max(devs) if devs else 0}")


def test_float_path_does_NOT_close_cartan_exactly_on_a_fractional_operand() -> None:
    """The negative control that makes leg 3 a measurement, not a tautology.

    Ask the float path for the companions of the EXACT operand ``Q(1,3)·E_01``
    and check its answer against that operand in exact arithmetic: it does not
    close. So "Cartan closes exactly" is a property of the exact path
    specifically, and the instrument can return otherwise
    (``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``).
    """
    operand = _scaled_exact(_e01(), Q(1, 3))
    g_s, g_c = triality_companions(operand)          # float path
    devs = _cartan_deviations(operand, g_s, g_c)
    assert devs, (
        "the float path was expected NOT to close Cartan's relation exactly on "
        "a non-dyadic operand; it closed with zero exact deviation, which would "
        "mean leg 3 proves nothing about exact= specifically")
    assert all(d > 0 for d in devs)

    # ... while the INTEGER operand closes exactly on BOTH paths (dyadic
    # companions are float64-exact), which is why nothing in-tree ever noticed.
    gen = _e01()
    b_f, c_f = triality_companions(gen)
    assert _cartan_deviations(gen, b_f, c_f) == []


# ─────────────────────────────────────────────────────────────────────────────
# LEG 4 — PRECEDENT CONSISTENCY: same carrier shape as dense_solve / schur
# ─────────────────────────────────────────────────────────────────────────────

def _leaf_type_of_nested(x):
    return type(x[0][0])


def test_exact_return_shape_matches_the_shipped_precedent_ops() -> None:
    """``exact=True`` returns ``list[list[Q]]`` — the precedent's matrix shape.

    Pins the convention so the NEXT ``exact=`` cannot drift: a matrix result is
    a nested ``list`` of ``Q``, a vector result is a flat ``list`` of ``Q``, and
    the float default returns the ``Mat`` / ``Vec`` carrier.
    """
    A = [[2, 1], [1, 3]]
    B = [[1, 0], [0, 1]]
    L = dense_laplacian(4, [(0, 1), (1, 2), (2, 3), (3, 0)], [1.0] * 4)

    prec_matrix = dense_solve(A, B, exact=True)
    prec_schur = schur_complement(L, [0, 2], exact=True)
    prec_dtn = dirichlet_to_neumann(L, [0, 2], exact=True)
    prec_vector = dense_solve(A, [1, 1], exact=True)

    # The precedent, MEASURED rather than quoted.
    for name, got in (("dense_solve", prec_matrix),
                      ("schur_complement", prec_schur),
                      ("dirichlet_to_neumann", prec_dtn)):
        assert isinstance(got, list) and isinstance(got[0], list), (
            f"{name}(exact=True) is expected to return a nested list; got "
            f"{type(got).__name__}")
        assert _leaf_type_of_nested(got) is Q, (
            f"{name}(exact=True) leaf is {_leaf_type_of_nested(got).__name__}, "
            f"not srmech.math.q.Q")
    assert isinstance(prec_vector, list) and type(prec_vector[0]) is Q

    # The NEW op must match the matrix shape exactly.
    g_s, g_c = triality_companions(_e01(), exact=True)
    for name, got in (("g_s", g_s), ("g_c", g_c)):
        assert isinstance(got, list), f"{name} must be a list, got {type(got)}"
        assert all(isinstance(r, list) for r in got), f"{name} rows must be lists"
        assert len(got) == _DIM and all(len(r) == _DIM for r in got)
        assert _leaf_type_of_nested(got) is Q, (
            f"{name} leaf is {_leaf_type_of_nested(got).__name__}; the "
            f"precedent ships Q")

    # And the float defaults agree on the carrier side too.
    assert isinstance(dense_solve(A, B), Mat)
    assert isinstance(schur_complement(L, [0, 2]), Mat)
    assert all(isinstance(m, Mat) for m in triality_companions(_e01()))


def test_the_exact_leaf_is_srmech_Q_not_stdlib_Fraction() -> None:
    """The rc444 docstring find, re-measured so it cannot rot again.

    Three precedent docstrings and five ``ToolEntry`` prose sites claimed the
    exact solve happens "in ``fractions.Fraction``". Post-#845 the carrier is
    srmech's own ``Q``. This asserts the fact the prose now states.
    """
    import fractions  # noqa: S403 — imported ONLY to prove a negative

    leaves = [
        dense_solve([[2, 1], [1, 3]], [[1, 0], [0, 1]], exact=True)[0][0],
        schur_complement(
            dense_laplacian(4, [(0, 1), (1, 2), (2, 3), (3, 0)], [1.0] * 4),
            [0, 2], exact=True)[0][0],
        triality_companions(_e01(), exact=True)[0][0][1],
    ]
    for leaf in leaves:
        assert isinstance(leaf, Q), f"{leaf!r} is not a srmech Q"
        assert not isinstance(leaf, fractions.Fraction), (
            f"{leaf!r} IS a stdlib Fraction — the pre-rc444 prose would be "
            f"right and this rc's docstring correction wrong")


# ─────────────────────────────────────────────────────────────────────────────
# LEG 5 — NON-VACUITY: the parameter is REACHED and is not inert
# ─────────────────────────────────────────────────────────────────────────────

def test_the_exact_parameter_is_not_inert() -> None:
    """Three independent ways the parameter demonstrably changes behaviour."""
    gen = _e01()

    # 1. the RETURN TYPE differs — the exact branch is entered.
    assert isinstance(triality_companions(gen)[0], Mat)
    assert isinstance(triality_companions(gen, exact=True)[0], list)

    # 2. the VALUES differ on an operand where float64 cannot hold them.
    third = _scaled_exact(gen, Q(1, 3))
    as_q_from_float = [[to_q(x) for x in row]
                       for row in _rows_of(triality_companions(third)[0])]
    assert as_q_from_float != _rows_of(triality_companions(third, exact=True)[0])

    # 3. the INPUT is not floated on the exact path — Q(1,3) stays 1/3, so the
    #    companions land on 1/6 rather than on float(1/3)/2's rational.
    b_exact = triality_companions(third, exact=True)[0]
    assert b_exact[0][1] == Q(1, 6)
    assert b_exact[0][1] != Q.from_float(0.16666666666666666)


def test_exact_is_declared_keyword_only_and_defaults_false() -> None:
    """A positional third argument would be a different (breaking) contract."""
    import inspect

    sig = inspect.signature(triality_companions)
    param = sig.parameters["exact"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY, (
        "exact must be KEYWORD_ONLY, matching dense_solve / schur_complement / "
        "dirichlet_to_neumann / jacobi_eigvals")
    assert param.default is False, "the default must keep every caller unchanged"


def test_tool_entry_declares_exact_and_the_union_return() -> None:
    """rc408's declared ⊇ live-signature gate is strict-zero; declare or go red.

    Also pins that the declared RETURN names both arms — an ``exact=`` whose
    return type only names the float carrier tells a registry consumer the
    opposite of what the op does.
    """
    entry = get_tool_schema().lookup(_OP)
    assert entry is not None, f"{_OP} is not registered"
    names = {p.name for p in entry.parameters}
    assert "exact" in names, (
        f"{_OP} accepts exact= but declares {sorted(names)} — rc408's converse "
        f"ratchet is strict-zero")
    exact_param = next(p for p in entry.parameters if p.name == "exact")
    assert exact_param.type == "bool"
    assert exact_param.required is False
    assert entry.returns is not None
    assert "Q" in entry.returns.type and "Mat" in entry.returns.type, (
        f"the declared return {entry.returns.type!r} must name BOTH carriers")


def test_the_four_precedent_ops_are_still_exactly_four() -> None:
    """The census cardinal, pinned.

    If a fifth ``exact=`` op appears without this list moving, the next reader
    inherits a stale precedent count — the exact failure mode `#T1152`'s own
    brief hit when it described ``jacobi_eigvals`` as returning "an exact
    spectrum" (measured: it returns a ``Vec`` of FLOATS; ``exact=`` there selects
    the exact-arithmetic ROUTE with one terminal float lift, not an exact
    carrier). Two co-valid meanings of ``exact=`` ship, and that is worth
    recording rather than smoothing over.
    """
    import inspect

    from srmech.math import laplacian
    from srmech.physics.qm import triality as _tri

    declaring = []
    for mod in (laplacian, _tri):
        for name in dir(mod):
            if name.startswith("_"):
                continue
            obj = getattr(mod, name)
            if not callable(obj) or isinstance(obj, type):
                continue
            try:
                sig = inspect.signature(obj)
            except (TypeError, ValueError):
                continue
            p = sig.parameters.get("exact")
            if p is not None and p.kind is inspect.Parameter.KEYWORD_ONLY:
                declaring.append(f"{mod.__name__}.{name}")
    assert sorted(declaring) == [
        "srmech.math.laplacian.dense_solve",
        "srmech.math.laplacian.dirichlet_to_neumann",
        "srmech.math.laplacian.jacobi_eigvals",
        "srmech.math.laplacian.schur_complement",
        "srmech.physics.qm.triality.triality_companions",
    ], f"the exact= population moved: {sorted(declaring)}"


def test_jacobi_eigvals_exact_returns_a_FLOAT_vec_not_a_Q_carrier() -> None:
    """The one precedent that means something DIFFERENT by ``exact=``.

    Pinned because the difference is easy to mis-cite: ``jacobi_eigvals``
    validates its input as exact and keeps the ARITHMETIC exact, then performs a
    single terminal float lift, so the return contract is unchanged (``Vec`` of
    floats). The three Class-L solves instead hand back the ``Q`` carrier. Both
    readings are legitimate; ``triality_companions`` follows the Class-L one
    because its result is a MATRIX with an exact carrier that ships.
    """
    from srmech.math.laplacian import jacobi_eigvals
    from srmech.math.vec import Vec

    ev = jacobi_eigvals([[2, 0], [0, 3]], exact=True)
    assert isinstance(ev, Vec)
    assert type(ev[0]) is float, (
        f"jacobi_eigvals(exact=True) leaf is {type(ev[0]).__name__}; if this "
        f"became Q the two exact= readings have converged and the docstrings "
        f"describing them must be revisited")
