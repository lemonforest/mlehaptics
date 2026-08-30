"""rc461 (`#T1181`) — ``cyclic_laplacian_spectrum``: the cycle spectrum, EXACT.

WHAT THIS OP IS, AND WHAT IT REPLACES
=====================================
``srmech.math.laplacian`` already reads a cycle's spectrum: ``generalized_ngon
(example="ordinary_k")`` builds the incidence graph of the thin ordinary
k-gon — which IS ``C_2k`` — and routes it through ``dense_adjacency`` +
``jacobi_eigvals``, i.e. through FLOAT. For this one graph family the float is
a projection of an object the ALU can hold exactly: ``L = 2I − A`` is a
circulant, circulants are diagonalised by the characters of ``ℤ/n``, and

    ``λ_k = 2 − ζ^k − ζ^{−k}``   lives in   ``ℚ[x]/Φ_n(x)``.

The new op returns it there. No float is constructed in the body and no
embedding root is attached, so ``[[feedback_alu_all_the_way_fpu_last_mile]]``
is satisfied structurally rather than by inspection.

THE CO-EQUAL DUAL CONSTRUCTION, WHICH IS WHY THIS FILE IS NOT SELF-CHECKING
===========================================================================
``[[user_stance_co_equal_dual_construction_is_a_consistency_oracle]]``. The two
routes to the same graph are INDEPENDENT — one is a Jacobi eigensolve over
float64 on a 2k-vertex adjacency matrix, the other is exact ℚ arithmetic in a
cyclotomic field — so their agreement under ``λ_L = 2 − λ_A`` is evidence, and
their disagreement would be the finding. Both are executed below.

THE RECONCILIATIONS ARE EXECUTED, NOT ASSERTED
==============================================
``[[feedback_an_asserted_algebraic_property_is_not_a_measured_one]]``. Sums and
products of algebraic numbers over a whole ``ℤ/n`` orbit fall back into ``ℚ``,
and the op runs those falls as guards that RAISE:

* ``Σ λ_k = 2n`` (``n ≥ 2``; ``n = 1`` is the self-loop case and is named);
* ``Σ λ_k² = 6n`` (``n ≥ 3``; ``C_1`` / ``C_2`` are degenerate multigraphs);
* ``∏_{k≥1} λ_k = n²`` ⇒ ``spanning_trees = n``, whose value is independently
  obvious — delete any one of the ``n`` edges.

THE CRYSTALLOGRAPHIC READING, MEASURED
======================================
``all_rational`` is True exactly on ``n ∈ {1, 2, 3, 4, 6}`` over ``1..30``,
which is exactly ``{n : φ(n) ≤ 2}``. The op does not cite the crystallographic
restriction; it returns the datum the restriction is about, and the agreement
of the two sets is re-derived here from ``srmech.math.primes.factor`` rather
than from a table.

⚠️ NUMPY IS ABSENT FROM THIS FILE, including the oracle: the float comparison
is against ``generalized_ngon``'s own ``jacobi_eigvals`` output, i.e. against
an srmech op, which is the one exemption the standing rule allows.
"""

from __future__ import annotations

import pytest

from srmech.math.laplacian import (
    MAX_CYCLIC_SPECTRUM_DEEP_N,
    MAX_CYCLIC_SPECTRUM_N,
    cyclic_laplacian_spectrum,
    generalized_ngon,
)
from srmech.math.poly import cyclotomic_polynomial
from srmech.math.primes import factor


def _totient(n: int) -> int:
    t = n
    for p, _e in factor(n):
        t = t // p * (p - 1)
    return t


# ══════════════════════════════════════════════════════════════════════
# 1. The exact spectrum itself
# ══════════════════════════════════════════════════════════════════════

def test_c6_is_the_integer_spectrum_0_1_3_4_3_1_exactly() -> None:
    """``C_6``'s Laplacian eigenvalues are integers, and the op returns them as
    integers — denominator 1 on every coordinate, no rounding step anywhere."""
    got = cyclic_laplacian_spectrum(6)
    assert got["all_rational"] is True
    assert got["rational_spectrum"] == (
        (0, 1), (1, 1), (3, 1), (4, 1), (3, 1), (1, 1))
    assert got["graph"] == "C_6"
    assert got["field_degree"] == 2 == _totient(6)
    assert got["minimal_polynomial"] == tuple(
        cyclotomic_polynomial(6)["coefficients"])


def test_the_pentagon_leaves_q_and_says_so_rather_than_rounding() -> None:
    """``λ_1 = 3 + α² + α³`` in ``ℚ[x]/Φ_5``, i.e. ``(5 − √5)/2``. A float route
    would hand back 1.3819660112501051 and a tolerance would then have to
    decide whether that is rational — which is the defect, not the method."""
    got = cyclic_laplacian_spectrum(5)
    assert got["all_rational"] is False
    assert got["rational_spectrum"] is None
    assert got["field_degree"] == 4
    assert got["eigenvalues"][1] == ((3, 1), (0, 1), (1, 1), (1, 1))
    # λ_1 and λ_4 are the same field element (the k ↦ n−k pairing)
    assert got["eigenvalues"][1] == got["eigenvalues"][4]
    assert got["multiplicities"] == (1, 2, 2)


def test_the_field_degree_is_the_totient_over_the_whole_range() -> None:
    for n in range(1, 41):
        got = cyclic_laplacian_spectrum(n)
        assert got["field_degree"] == _totient(n), n
        assert len(got["eigenvalues"]) == n
        assert all(len(e) == got["field_degree"] for e in got["eigenvalues"])


def test_the_structural_guards_hold_and_are_reported() -> None:
    for n in (1, 2, 3, 5, 7, 12, 16):
        got = cyclic_laplacian_spectrum(n)
        assert got["alpha_order_closes"] is True, n
        assert got["chirality_paired"] is True, n
        assert got["degenerate"] is (n < 3), n


def test_the_multiplicity_partition_sums_to_n() -> None:
    """``Σ multiplicities == n`` and ``n_distinct == len(distinct)``: the
    distinct/multiplicity split must reconstruct the whole spectrum, or the
    payload is describing a different object from the one it returned."""
    for n in range(1, 31):
        got = cyclic_laplacian_spectrum(n)
        assert sum(got["multiplicities"]) == n, n
        assert got["n_distinct"] == len(got["distinct"]) \
            == len(got["multiplicities"]), n
        assert got["n_distinct"] == (n // 2) + 1, n


# ══════════════════════════════════════════════════════════════════════
# 2. The reconciliations — algebraic numbers falling back into ℤ
# ══════════════════════════════════════════════════════════════════════

def test_the_trace_is_2n_and_n_equals_1_is_named_not_tolerated() -> None:
    for n in range(2, 41):
        assert cyclic_laplacian_spectrum(n)["trace"] == 2 * n, n
    # the ONE exception, and it is a different number rather than a wider band
    assert cyclic_laplacian_spectrum(1)["trace"] == 0


def test_the_deep_reconciliations_are_the_integers_6n_and_n_squared() -> None:
    for n in range(3, 25):
        got = cyclic_laplacian_spectrum(n, deep=True)
        assert got["deep"] is True
        assert got["sum_of_squares"] == 6 * n, n
        assert got["kirchhoff_product"] == n * n, n
        assert got["spanning_trees"] == n, n


def test_the_degenerate_multigraph_cases_are_excluded_by_name() -> None:
    """``C_2`` is a DOUBLED EDGE: ``Σλ² = 16``, not ``6·2 = 12``. The op reports
    16 and does not raise, because the law is scoped to ``n ≥ 3`` explicitly —
    a guard that accepted both would be checking nothing."""
    two = cyclic_laplacian_spectrum(2, deep=True)
    assert two["sum_of_squares"] == 16 != 6 * 2
    assert two["kirchhoff_product"] == 4 == 2 * 2
    assert two["degenerate"] is True
    one = cyclic_laplacian_spectrum(1, deep=True)
    assert one["kirchhoff_product"] is None      # the k≥1 product is empty
    assert one["spanning_trees"] is None


def test_the_deep_fields_are_present_and_null_when_deep_is_false() -> None:
    """Present-and-null, never absent: a consumer must never have to ask
    whether the key exists."""
    got = cyclic_laplacian_spectrum(9)
    for key in ("sum_of_squares", "kirchhoff_product", "spanning_trees"):
        assert key in got and got[key] is None, key
    assert got["deep"] is False


# ══════════════════════════════════════════════════════════════════════
# 3. THE CO-EQUAL DUAL CONSTRUCTION — exact ℚ vs the float Jacobi route
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("k", [2, 3, 4, 5, 6, 7])
def test_the_exact_spectrum_projects_onto_the_float_ngon_spectrum(k: int) -> None:
    """``generalized_ngon(example="ordinary_k")``'s incidence graph IS ``C_2k``,
    read through ``dense_adjacency`` + ``jacobi_eigvals``. ``C_2k`` is 2-regular
    so ``L = 2I − A`` and ``λ_L = 2 − λ_A`` exactly. Two independent routes,
    one object.

    The projection direction is deliberate: the EXACT value is rendered to
    float for the comparison, never the reverse. Reading the float back into ℚ
    would be a rotation the ALU did not do, which is the whole thing the op
    exists to avoid.
    """
    ngon = generalized_ngon(example="ordinary_%d" % k)
    assert ngon["n_vertices"] == 2 * k
    assert ngon["girth"] == 2 * k
    exact = cyclic_laplacian_spectrum(2 * k)

    from_float = sorted({round(2.0 - a, 6)
                         for a in ngon["distinct_eigenvalues"]})
    # THE FPU LAST MILE, and it is the only float in this file: evaluate each
    # exact coordinate vector at the embedding ζ = exp(2πi/n). Both π and cos
    # come from srmech's own Class-N cascade (`atan` at 1 gives π/4; `cos` is
    # the rational series), never from `math` — which the self-hosting import
    # ban forbids here anyway.
    from srmech.math.rational import atan as _atan, cos as _cos
    pi = 4.0 * float(_atan(1.0))
    n = 2 * k
    from_exact = set()
    for coords in exact["distinct"]:
        acc = 0.0
        for j, (num, den) in enumerate(coords):
            if num == 0:
                continue
            acc += (num / den) * float(_cos(2.0 * pi * j / n))
        from_exact.add(round(acc, 6))
    assert sorted(from_exact) == from_float, (sorted(from_exact), from_float)
    assert exact["n_distinct"] == len(ngon["distinct_eigenvalues"])


def test_the_float_route_cannot_answer_the_question_the_exact_one_does() -> None:
    """WHY the exact op exists at all, stated as a measurement rather than a
    preference. ``C_10``'s eigenvalue ``2 − 2cos(2π/10)`` is irrational; the
    float route returns 0.381966, from which no tolerance can decide
    rationality. The exact route returns a coordinate vector with a nonzero
    non-constant coefficient, which decides it outright."""
    exact = cyclic_laplacian_spectrum(10)
    assert exact["all_rational"] is False
    non_constant = [e for e in exact["eigenvalues"]
                    if any(num != 0 for num, _d in e[1:])]
    assert non_constant, "no eigenvalue left ℚ — the discriminator is blind"
    # ...and the sibling that IS rational, so the predicate is not constant
    assert cyclic_laplacian_spectrum(12)["all_rational"] is False
    assert cyclic_laplacian_spectrum(6)["all_rational"] is True


# ══════════════════════════════════════════════════════════════════════
# 4. THE CRYSTALLOGRAPHIC READING — measured, both directions
# ══════════════════════════════════════════════════════════════════════

def test_all_rational_holds_exactly_where_the_totient_is_at_most_two() -> None:
    """Set equality in BOTH directions over 1..30
    (``[[feedback_always_check_both_directions_including_time]]``). The right
    side is re-derived from ``srmech.math.primes.factor``, not from a table, so
    neither side is a restatement of the other."""
    rational = {n for n in range(1, 31)
                if cyclic_laplacian_spectrum(n)["all_rational"]}
    small_totient = {n for n in range(1, 31) if _totient(n) <= 2}
    assert rational == small_totient, (sorted(rational),
                                       sorted(small_totient))
    assert rational == {1, 2, 3, 4, 6}, sorted(rational)


def test_the_pentagon_is_the_first_failure_and_it_is_the_golden_one() -> None:
    """``n = 5`` is the smallest ``n`` whose cycle spectrum leaves ℚ, and the
    field it lands in has degree 4 — the reason 5-fold symmetry is absent from
    a lattice, arriving here as a returned datum."""
    assert min(n for n in range(1, 31)
               if not cyclic_laplacian_spectrum(n)["all_rational"]) == 5
    assert cyclic_laplacian_spectrum(5)["field_degree"] == 4


# ══════════════════════════════════════════════════════════════════════
# 5. Contracts, bounds and refusals
# ══════════════════════════════════════════════════════════════════════

def test_the_measured_bounds_are_enforced_at_both_ends() -> None:
    with pytest.raises(ValueError, match="requires 1 <= n <="):
        cyclic_laplacian_spectrum(0)
    with pytest.raises(ValueError, match="requires 1 <= n <="):
        cyclic_laplacian_spectrum(MAX_CYCLIC_SPECTRUM_N + 1)
    # and the boundary itself is REACHABLE, so the bound is a bound and not a
    # ceiling nothing can touch
    assert cyclic_laplacian_spectrum(MAX_CYCLIC_SPECTRUM_N)["n"] \
        == MAX_CYCLIC_SPECTRUM_N


def test_the_deep_bound_refuses_above_its_own_measured_limit() -> None:
    assert cyclic_laplacian_spectrum(
        MAX_CYCLIC_SPECTRUM_DEEP_N, deep=True)["deep"] is True
    with pytest.raises(ValueError, match="deep=True requires n <="):
        cyclic_laplacian_spectrum(MAX_CYCLIC_SPECTRUM_DEEP_N + 1, deep=True)
    # ...while the BASE path at the same n is fine — the two bounds are
    # genuinely different, not one bound written twice
    assert cyclic_laplacian_spectrum(
        MAX_CYCLIC_SPECTRUM_DEEP_N + 1)["n"] == MAX_CYCLIC_SPECTRUM_DEEP_N + 1
    assert MAX_CYCLIC_SPECTRUM_DEEP_N < MAX_CYCLIC_SPECTRUM_N


def test_a_bool_is_not_an_int_here() -> None:
    """``True == 1`` in Python, so an unguarded ``isinstance(n, int)`` would
    accept ``cyclic_laplacian_spectrum(True)`` and silently answer for
    ``C_1``."""
    with pytest.raises(TypeError, match="n must be int"):
        cyclic_laplacian_spectrum(True)
    with pytest.raises(TypeError, match="n must be int"):
        cyclic_laplacian_spectrum(6.0)


def test_the_content_addresses_discriminate_the_spectrum_not_the_call() -> None:
    a = cyclic_laplacian_spectrum(7)
    b = cyclic_laplacian_spectrum(7, deep=True)
    c = cyclic_laplacian_spectrum(8)
    assert a["spectrum_sha256"] == b["spectrum_sha256"]   # same spectrum
    assert a["spectrum_sha256"] != c["spectrum_sha256"]
    assert a["procedure_sha256"] == c["procedure_sha256"]
    assert len(a["spectrum_sha256"]) == 64


def test_the_op_ships_on_every_declared_surface() -> None:
    from srmech.math import laplacian
    from srmech.introspect.tool_schema import get_tool_schema
    assert "cyclic_laplacian_spectrum" in laplacian.__all__
    assert "cyclic_laplacian_spectrum" in laplacian.LAPLACIAN_OPS
    entry = next(t for t in get_tool_schema().tools
                 if t.name == "srmech.math.laplacian.cyclic_laplacian_spectrum")
    assert entry.composes == ("srmech.math.poly.cyclotomic_polynomial",
                              "srmech.amsc.format.sha256_bytes")
