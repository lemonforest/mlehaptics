"""rc107 — SAFE-REGION PUSH-DOWN: the sparse safe-support gate internals of the
genus-axis theta carriers (the #707 dive's Deliverable B1).

THE NO-SHELL GATES (bit-identity). Every ``*_holds`` / ``*_is_distinct_*`` gate on
RiemannTheta / RiemannThetaG3 / RiemannThetaG4 / RiemannThetaG5 now enumerates each
theta factor DIRECTLY on its safe support {u : dc·u² ≤ safe} (the exact safe region
of the INFINITE theta series — box-parameter-free) and convolves with a
diagonal-additivity guard, instead of enumerating the full (2·box+1)^g boxes densely
and restricting afterwards. The claim shipped here is BIT-IDENTITY on the compared
region: for every gate, the sparse side equals the OLD dense path's side restricted
to the safe region — exactly, not approximately. These tests recompute the dense
sides through the UNTOUCHED public dense surfaces (``duplication_lhs/rhs``,
``addition_lhs/rhs``, ``goepel_lhs/rhs``, the eighth-nome builders) and compare.

Distinctness gates: the old bodies compared FULL lattices; the sparse bodies compare
the safe region (the same region as the matching ``*_holds`` gate — the sound ≠
direction). The bit-identity tests here ALSO verify the verdicts agree, i.e. the
≠-WITNESS lives INSIDE the safe region for every comparison the gates make. The
g3/g4 Göpel-distinctness gates used ``_diag_restrict`` comparisons — their sparse
diag-only mode (``crosses=False``) is bit-identical to the dense diag-restricted
lattices (the diagonal-additivity argument), asserted exactly.

CI runs the fast subset below; the FULL sweep at the maximum SHIPPED boxes (every
box the test suite exercises — the dense g4 addition sides at its shipped box 2
alone are the #707 headline's 137.8 s) is gated behind
``SRMECH_THETA_SPARSE_FULL=1`` and is run + reported at least once locally per the
rc107 gate. THE HONEST DENSE-FEASIBILITY BOUNDARY: three gate DEFAULT boxes are
INFEASIBLE-DENSE (g3 addition box 6 ≈ 8 min + a 12-million-key rhs dict PER PAIR;
g4 addition box 3 and g5 duplication box 2 are worse) — which is exactly WHY the
sparse push-down was built; no test ever exercised them densely. For those boxes
the sweep verifies the VERDICT through both sparse paths (native == pure — the
kernel parity tests) and the bit-identity is proven at every densely-feasible box
(the diagonal-additivity argument is box-independent).

Native: the whole decision dispatches to ``srmech_riemann_theta_gate_decide`` in
ONE call when loaded (no per-lattice dict marshaling — the rc106 finding); the
parity tests here assert native decide == pure decide per gate spec, and the
forced-pure verdict tests (the rc106 ``pure_riemann_theta`` sentinel fixture) prove
the pure sparse bodies alone still decide every gate.
"""

from __future__ import annotations

import os

import pytest

from srmech.amsc import _native
from srmech.amsc import riemann_theta as rt
from srmech.amsc.riemann_theta import (RiemannTheta, RiemannThetaG3,
                                       RiemannThetaG4, RiemannThetaG5)

FULL = os.environ.get("SRMECH_THETA_SPARSE_FULL", "") == "1"

G2_ADD_PAIRS = [((0, 0), (0, 0)), ((1, 0), (0, 0)), ((1, 1), (0, 0)),
                ((1, 0), (0, 1)), ((1, 1), (1, 0)), ((0, 1), (1, 1))]
G3_ADD_PAIRS = [((0, 0, 0), (0, 0, 0)), ((1, 0, 0), (0, 0, 0)),
                ((0, 0, 1), (0, 0, 0)), ((1, 0, 1), (0, 0, 0)),
                ((1, 1, 0), (0, 0, 1)), ((0, 1, 1), (1, 0, 0)),
                ((1, 1, 1), (0, 1, 1))]
G4_ADD_PAIRS = [((0, 0, 0, 0), (0, 0, 0, 0)), ((1, 0, 0, 0), (0, 0, 0, 0)),
                ((0, 0, 0, 1), (0, 0, 0, 0)), ((1, 0, 0, 1), (0, 0, 0, 0)),
                ((1, 1, 0, 0), (0, 0, 1, 1)), ((0, 0, 1, 1), (1, 1, 0, 0)),
                ((1, 1, 1, 1), (0, 0, 1, 1))]


def _restrict_full(lat, safe, g):
    """The gates' OLD dense-path safe-region restriction (diagonals AND cross
    magnitudes ≤ safe; Class-K magnitude, no abs()) — the bit-identity target."""
    kept = {}
    for k, v in lat.items():
        ok = all(k[i] <= safe for i in range(g))
        if ok:
            for c in k[g:]:
                m = c if c >= 0 else -c
                if m > safe:
                    ok = False
                    break
        if ok:
            kept[k] = v
    return kept


def _sparse_side(g, safe, prods, crosses=True):
    return rt._sparse_sum(g, safe, prods, crosses)


# ──────────────────────────────────────────────────────────────────────
# bit-identity: DUPLICATION (all four genera)
# ──────────────────────────────────────────────────────────────────────

DUP_CASES_FAST = [(2, 4), (2, 6), (3, 2), (3, 3), (4, 2), (5, 1)]
# FULL: the max shipped boxes (g2 default 8; g3 default 4). g5 box 2 is
# infeasible-dense (a ~10M-key rhs across 32 summands) — its verdict is
# covered sparse-native == sparse-pure; box 1 is the only test-exercised box.
DUP_CASES_FULL = [(2, 8), (3, 4)]


def _dup_cls(g):
    return {2: RiemannTheta, 3: RiemannThetaG3,
            4: RiemannThetaG4, 5: RiemannThetaG5}[g]


def _assert_dup_bit_identity(g, box):
    safe = 4 * box * box
    cls = _dup_cls(g)
    lhs_prods, rhs_prods = rt._spec_duplication(g)
    assert _sparse_side(g, safe, lhs_prods) == _restrict_full(
        cls.duplication_lhs(box), safe, g)
    assert _sparse_side(g, safe, rhs_prods) == _restrict_full(
        cls.duplication_rhs(box), safe, g)


@pytest.mark.parametrize("g,box", DUP_CASES_FAST)
def test_bit_identity_duplication(g, box):
    """Sparse duplication sides == restrict(dense duplication_lhs/rhs) — exact."""
    _assert_dup_bit_identity(g, box)


@pytest.mark.skipif(not FULL, reason="SRMECH_THETA_SPARSE_FULL=1 full sweep only")
@pytest.mark.parametrize("g,box", DUP_CASES_FULL)
def test_bit_identity_duplication_full(g, box):
    """FULL sweep: the max shipped duplication boxes (g2:8, g3:4)."""
    _assert_dup_bit_identity(g, box)


# ──────────────────────────────────────────────────────────────────────
# bit-identity: ADDITION (g2/g3/g4, every gate pair)
# ──────────────────────────────────────────────────────────────────────

# FAST: g4 rides box 1 (cheap; the full 16-summand pipeline) — its shipped
# box 2 is the 137.8 s dense pass, FULL-sweep only.
ADD_CASES_FAST = [(2, 4, G2_ADD_PAIRS), (3, 2, G3_ADD_PAIRS),
                  (4, 1, G4_ADD_PAIRS)]
# FULL: every densely-feasible shipped box. The g3 box-6 / g4 box-3 gate
# DEFAULTS are infeasible-dense (see the module docstring) — verdicts are
# covered sparse-native == sparse-pure instead.
ADD_CASES_FULL = [(2, 6, G2_ADD_PAIRS), (2, 8, G2_ADD_PAIRS),
                  (3, 3, G3_ADD_PAIRS), (3, 4, G3_ADD_PAIRS),
                  (4, 2, G4_ADD_PAIRS)]


def _add_cls(g):
    return {2: RiemannTheta, 3: RiemannThetaG3, 4: RiemannThetaG4}[g]


def _assert_add_bit_identity(g, box, pairs):
    safe = 2 * box * box
    cls = _add_cls(g)
    for (a, b) in pairs:
        lhs_prods, rhs_prods = rt._spec_addition(g, a, b)
        assert _sparse_side(g, safe, lhs_prods) == _restrict_full(
            cls.addition_lhs(a, b, box), safe, g), (a, b, "lhs")
        assert _sparse_side(g, safe, rhs_prods) == _restrict_full(
            cls.addition_rhs(a, b, box), safe, g), (a, b, "rhs")


@pytest.mark.parametrize("g,box,pairs", ADD_CASES_FAST)
def test_bit_identity_addition(g, box, pairs):
    """Sparse addition sides == restrict(dense addition_lhs/rhs), every gate
    pair — exact."""
    _assert_add_bit_identity(g, box, pairs)


@pytest.mark.skipif(not FULL, reason="SRMECH_THETA_SPARSE_FULL=1 full sweep only")
@pytest.mark.parametrize("g,box,pairs", ADD_CASES_FULL)
def test_bit_identity_addition_full(g, box, pairs):
    """FULL sweep: the max densely-feasible shipped addition boxes — the g4
    box-2 dense pass IS the #707 headline's 137.8 s side."""
    _assert_add_bit_identity(g, box, pairs)


# ──────────────────────────────────────────────────────────────────────
# bit-identity: GÖPEL (g2 triple / g3 quad / g4 signed pairs)
# ──────────────────────────────────────────────────────────────────────

def _goepel_sides_specs(g):
    if g == 2:
        t = RiemannTheta.goepel_syzygy_triple()
        return ([(1, rt._spec_goepel_product(t[0]))],
                [(1, rt._spec_goepel_product(t[1])),
                 (-1, rt._spec_goepel_product(t[2]))])
    if g == 3:
        q = RiemannThetaG3.goepel_syzygy_quad()
        return ([(1, rt._spec_goepel_product(q[0]))],
                [(1, rt._spec_goepel_product(q[1])),
                 (1, rt._spec_goepel_product(q[2])),
                 (-1, rt._spec_goepel_product(q[3]))])
    q = RiemannThetaG4.goepel_syzygy_quad()
    return ([(1, rt._spec_goepel_product(pr)) for (pr, s) in q if s == 1],
            [(1, rt._spec_goepel_product(pr)) for (pr, s) in q if s == -1])


GOEPEL_CASES_FAST = [(2, 4), (3, 3), (4, 2)]
GOEPEL_CASES_FULL = [(2, 5), (2, 6), (3, 4), (4, 3)]


def _assert_goepel_bit_identity(g, box):
    safe = box * box
    cls = _dup_cls(g)
    lhs_prods, rhs_prods = _goepel_sides_specs(g)
    assert _sparse_side(g, safe, lhs_prods) == _restrict_full(
        cls.goepel_lhs(box), safe, g)
    assert _sparse_side(g, safe, rhs_prods) == _restrict_full(
        cls.goepel_rhs(box), safe, g)


@pytest.mark.parametrize("g,box", GOEPEL_CASES_FAST)
def test_bit_identity_goepel(g, box):
    """Sparse Göpel sides == restrict(dense goepel_lhs/rhs) — exact."""
    _assert_goepel_bit_identity(g, box)


@pytest.mark.skipif(not FULL, reason="SRMECH_THETA_SPARSE_FULL=1 full sweep only")
@pytest.mark.parametrize("g,box", GOEPEL_CASES_FULL)
def test_bit_identity_goepel_full(g, box):
    """FULL sweep: the max shipped Göpel boxes (g2:6, g3:4, g4:3)."""
    _assert_goepel_bit_identity(g, box)


# ──────────────────────────────────────────────────────────────────────
# bit-identity + witness-in-region: ADDITION DISTINCTNESS (g2/g3/g4)
# ──────────────────────────────────────────────────────────────────────

ADD_DIST_FAST = [(2, 6), (3, 3), (4, 2)]
ADD_DIST_FULL = [(2, 8), (3, 4)]

_GENUINE_A = {2: (1, 0), 3: (1, 0, 0), 4: (1, 0, 0, 0)}


def _dense_null_square_omega(g, c, box):
    cls = _add_cls(g)
    if g == 2:
        tc = cls._theta_omega_eighth(c[0], c[1], 0, 0, box)
    elif g == 3:
        tc = cls._theta_omega_eighth(c[0], c[1], c[2], 0, 0, 0, box)
    else:
        tc = cls._theta_omega_eighth(c[0], c[1], c[2], c[3], 0, 0, 0, 0, box)
    return cls._square_lattice_pair(tc, tc)


def _assert_add_distinct_bit_identity(g, box):
    safe = 2 * box * box
    cls = _add_cls(g)
    zero = tuple(0 for _ in range(g))
    a = _GENUINE_A[g]
    genuine_prods = [(1, ((2, 2, a, zero), (2, 2, zero, zero)))]
    sparse_genuine = _sparse_side(g, safe, genuine_prods)
    dense_genuine = cls.addition_lhs(a, zero, box)
    # bit-identity of the genuine LHS on the region
    assert sparse_genuine == _restrict_full(dense_genuine, safe, g)
    for bits in range(1 << g):
        c = tuple((bits >> i) & 1 for i in range(g))
        sparse_sq = _sparse_side(
            g, safe, [(1, rt._spec_null_square_omega(g, c))])
        dense_sq = _dense_null_square_omega(g, c, box)
        # bit-identity of the comparator on the region
        assert sparse_sq == _restrict_full(dense_sq, safe, g), c
        # verdict identity: the ≠-witness lives INSIDE the safe region — the
        # restricted comparison decides exactly what the full one decided
        assert (sparse_genuine == sparse_sq) == (dense_genuine == dense_sq), c
    assert cls.addition_is_distinct_from_duplication(box) is True


@pytest.mark.parametrize("g,box", ADD_DIST_FAST)
def test_bit_identity_addition_distinctness(g, box):
    """Sparse ≠-comparisons == restrict(dense), verdicts identical (the witness
    lives inside the safe region), gate verdict True."""
    _assert_add_distinct_bit_identity(g, box)


@pytest.mark.skipif(not FULL, reason="SRMECH_THETA_SPARSE_FULL=1 full sweep only")
@pytest.mark.parametrize("g,box", ADD_DIST_FULL)
def test_bit_identity_addition_distinctness_full(g, box):
    """FULL sweep: the max shipped addition-distinctness boxes."""
    _assert_add_distinct_bit_identity(g, box)


# ──────────────────────────────────────────────────────────────────────
# bit-identity + witness-in-region: g2 GÖPEL DISTINCTNESS (full-lattice mode)
# ──────────────────────────────────────────────────────────────────────

G2_GOEPEL_DIST_FAST = [4]
G2_GOEPEL_DIST_FULL = [5]


def _assert_g2_goepel_distinct_bit_identity(box):
    safe = box * box
    zero = (0, 0)
    goepel_prods = [(1, rt._spec_goepel_product(
        RiemannTheta.goepel_syzygy_triple()[0]))]
    sparse_goepel = _sparse_side(2, safe, goepel_prods)
    dense_goepel = RiemannTheta.goepel_lhs(box)
    assert sparse_goepel == _restrict_full(dense_goepel, safe, 2)
    # vs duplication LHS (quarter-nome θ[0;0]²)
    sparse_dup = _sparse_side(
        2, safe, [(1, ((1, 2, zero, zero), (1, 2, zero, zero)))])
    dense_dup = RiemannTheta.duplication_lhs(box)
    assert sparse_dup == _restrict_full(dense_dup, safe, 2)
    assert (sparse_goepel == sparse_dup) == (dense_goepel == dense_dup)
    # vs every addition LHS (eighth-nome θ[a]·θ[b])
    for a1 in (0, 1):
        for a2 in (0, 1):
            for b1 in (0, 1):
                for b2 in (0, 1):
                    sparse_add = _sparse_side(2, safe, [(1, (
                        (2, 2, (a1, a2), zero), (2, 2, (b1, b2), zero)))])
                    dense_add = RiemannTheta.addition_lhs(
                        (a1, a2), (b1, b2), box)
                    assert sparse_add == _restrict_full(dense_add, safe, 2)
                    assert ((sparse_goepel == sparse_add)
                            == (dense_goepel == dense_add)), (a1, a2, b1, b2)
    assert RiemannTheta.goepel_is_distinct_from_duplication_and_addition(
        box) is True


@pytest.mark.parametrize("box", G2_GOEPEL_DIST_FAST)
def test_bit_identity_g2_goepel_distinctness(box):
    """g2 Göpel-distinctness: sparse == restrict(dense) per comparison, verdicts
    identical (witness inside the region), gate verdict True."""
    _assert_g2_goepel_distinct_bit_identity(box)


@pytest.mark.skipif(not FULL, reason="SRMECH_THETA_SPARSE_FULL=1 full sweep only")
@pytest.mark.parametrize("box", G2_GOEPEL_DIST_FULL)
def test_bit_identity_g2_goepel_distinctness_full(box):
    _assert_g2_goepel_distinct_bit_identity(box)


# ──────────────────────────────────────────────────────────────────────
# bit-identity: g3/g4 GÖPEL DISTINCTNESS (the _diag_restrict / diag-only mode)
# ──────────────────────────────────────────────────────────────────────

def _assert_g3_goepel_dist_diagonly_bit_identity(box):
    bound = box * box
    zero = (0, 0, 0)
    q = RiemannThetaG3.goepel_syzygy_quad()
    goepel_prods = [(1, rt._spec_goepel_product(q[0]))]
    sparse_goepel = _sparse_side(3, bound, goepel_prods, crosses=False)
    # the sparse diag-only sum IS the dense diag-restricted lattice — exactly
    assert sparse_goepel == RiemannThetaG3._diag_restrict(
        RiemannThetaG3.goepel_lhs(box), bound)
    sparse_dup = _sparse_side(3, bound, [(1, (
        (1, 2, zero, zero), (1, 2, zero, zero)))], crosses=False)
    assert sparse_dup == RiemannThetaG3._diag_restrict(
        RiemannThetaG3.duplication_lhs(box), bound)
    assert sparse_goepel != sparse_dup          # the dense gate's own witness
    for (a, b) in (((0, 0, 0), (0, 0, 0)), ((1, 0, 0), (0, 0, 0)),
                   ((1, 1, 1), (0, 1, 1))):
        sparse_add = _sparse_side(3, bound, [(1, (
            (2, 2, a, zero), (2, 2, b, zero)))], crosses=False)
        assert sparse_add == RiemannThetaG3._diag_restrict(
            RiemannThetaG3.addition_lhs(a, b, box), bound), (a, b)
        assert sparse_goepel != sparse_add, (a, b)
    assert (RiemannThetaG3
            .goepel_is_distinct_from_duplication_addition_and_chi18(box)
            is True)


def test_bit_identity_g3_goepel_distinctness_diag_only():
    """g3 Göpel-distinctness (the ``_diag_restrict`` comparisons): the sparse
    diag-only mode is bit-identical to the dense diag-restricted lattices."""
    _assert_g3_goepel_dist_diagonly_bit_identity(3)


def _assert_g4_goepel_dist_diagonly_bit_identity(box):
    bound = box * box
    zero = (0, 0, 0, 0)
    q = RiemannThetaG4.goepel_syzygy_quad()
    goepel_prods = [(1, rt._spec_goepel_product(pr)) for (pr, s) in q if s == 1]
    sparse_goepel = _sparse_side(4, bound, goepel_prods, crosses=False)
    assert sparse_goepel == RiemannThetaG4._diag_restrict(
        RiemannThetaG4.goepel_lhs(box), bound)
    sparse_dup = _sparse_side(4, bound, [(1, (
        (1, 2, zero, zero), (1, 2, zero, zero)))], crosses=False)
    assert sparse_dup == RiemannThetaG4._diag_restrict(
        RiemannThetaG4.duplication_lhs(box), bound)
    assert sparse_goepel != sparse_dup
    ga, gb = q[0][0]
    for (a, b) in ((zero, zero), ((1, 0, 0, 0), zero),
                   ((1, 1, 1, 1), zero), (ga[0], gb[0])):
        sparse_add = _sparse_side(4, bound, [(1, (
            (2, 2, tuple(a), zero), (2, 2, tuple(b), zero)))], crosses=False)
        assert sparse_add == RiemannThetaG4._diag_restrict(
            RiemannThetaG4.addition_lhs(a, b, box), bound), (a, b)
        assert sparse_goepel != sparse_add, (a, b)
    assert (RiemannThetaG4.goepel_is_distinct_from_duplication_and_addition(box)
            is True)


def test_bit_identity_g4_goepel_distinctness_diag_only():
    """g4 Göpel-distinctness (the ``_diag_restrict`` comparisons): the sparse
    diag-only mode is bit-identical to the dense diag-restricted lattices."""
    _assert_g4_goepel_dist_diagonly_bit_identity(2)


@pytest.mark.skipif(not FULL, reason="SRMECH_THETA_SPARSE_FULL=1 full sweep only")
def test_bit_identity_g4_goepel_distinctness_diag_only_full():
    _assert_g4_goepel_dist_diagonly_bit_identity(3)


# ──────────────────────────────────────────────────────────────────────
# gate verdicts on the FORCED-pure sparse path (the rc106 sentinel fixture:
# any native riemann-theta hit fails loudly — the pure sparse bodies alone)
# ──────────────────────────────────────────────────────────────────────

def test_gate_verdicts_forced_pure(pure_riemann_theta):
    """Every gate of every genus decides True through the PURE sparse body alone
    (validated minimal boxes; the sentinel teardown re-asserts zero native hits)."""
    assert RiemannTheta.duplication_holds(4)
    assert RiemannTheta.addition_holds(4)
    assert RiemannTheta.addition_is_distinct_from_duplication(4)
    assert RiemannTheta.goepel_holds(4)
    assert RiemannTheta.goepel_is_distinct_from_duplication_and_addition(4)
    assert RiemannThetaG3.duplication_holds(2)
    assert RiemannThetaG3.addition_holds(2)
    assert RiemannThetaG3.addition_is_distinct_from_duplication(2)
    assert RiemannThetaG3.goepel_holds(3)
    assert RiemannThetaG3.goepel_is_distinct_from_duplication_addition_and_chi18(3)
    assert RiemannThetaG4.duplication_holds(2)
    assert RiemannThetaG4.addition_holds(2)
    assert RiemannThetaG4.addition_is_distinct_from_duplication(2)
    assert RiemannThetaG4.goepel_holds(2)
    assert RiemannThetaG4.goepel_is_distinct_from_duplication_and_addition(2)
    assert RiemannThetaG5.duplication_holds(1)


def test_gate_rejects_bad_box_unchanged():
    """The gates' box validation contracts are UNCHANGED by the rc107 internals."""
    with pytest.raises(ValueError):
        RiemannTheta.duplication_holds(1)
    with pytest.raises(ValueError):
        RiemannTheta.goepel_holds(3)
    with pytest.raises(ValueError):
        RiemannThetaG3.goepel_holds(2)
    with pytest.raises(ValueError):
        RiemannThetaG4.addition_holds(1)
    with pytest.raises(ValueError):
        RiemannThetaG5.duplication_holds(0)


# ──────────────────────────────────────────────────────────────────────
# native parity: srmech_riemann_theta_gate_decide == the pure sparse decide
# ──────────────────────────────────────────────────────────────────────

def _pure_decide(g, safe, comps, crosses=True):
    out = []
    for (lhs_prods, rhs_prods) in comps:
        lhs = rt._sparse_sum(g, safe, lhs_prods, crosses)
        rhs = rt._sparse_sum(g, safe, rhs_prods, crosses)
        out.append((lhs == rhs, rt._sparse_has_genus_cross(g, lhs)))
    return out


@pytest.mark.skipif(not _native.has_native_riemann_theta_gate(),
                    reason="native srmech_riemann_theta_gate_decide not loaded")
def test_native_gate_decide_parity():
    """The ONE-call C gate kernel's verdicts == the pure sparse verdicts, per
    gate spec (both restriction modes, all genera)."""
    cases = []
    for (g, box) in ((2, 6), (3, 3), (4, 2), (5, 1)):
        cases.append((g, 4 * box * box, [rt._spec_duplication(g)], True))
    for (g, pairs, box) in ((2, G2_ADD_PAIRS, 6), (3, G3_ADD_PAIRS, 3),
                            (4, G4_ADD_PAIRS, 2)):
        cases.append((g, 2 * box * box,
                      [rt._spec_addition(g, a, b) for (a, b) in pairs], True))
    for (g, box) in ((2, 5), (3, 3), (4, 2)):
        cases.append((g, box * box, [_goepel_sides_specs(g)], True))
    # a diag-only (distinctness-mode) case
    zero = (0, 0, 0)
    q = RiemannThetaG3.goepel_syzygy_quad()
    cases.append((3, 9, [
        ([(1, rt._spec_goepel_product(q[0]))],
         [(1, ((1, 2, zero, zero), (1, 2, zero, zero)))]),
        ([(1, rt._spec_goepel_product(q[0]))],
         [(1, ((2, 2, (1, 0, 0), zero), (2, 2, zero, zero)))]),
    ], False))
    # an addition-distinctness case (unequal comparisons)
    z2 = (0, 0)
    cases.append((2, 72, [
        ([(1, ((2, 2, (1, 0), z2), (2, 2, z2, z2)))],
         [(1, rt._spec_null_square_omega(2, (c1, c2)))])
        for c1 in (0, 1) for c2 in (0, 1)], True))
    for (g, safe, comps, crosses) in cases:
        got_native = _native.riemann_theta_gate_decide_c(g, safe, crosses, comps)
        assert got_native is not None
        assert got_native == _pure_decide(g, safe, comps, crosses), (g, safe)


@pytest.mark.skipif(not _native.has_native_riemann_theta_gate(),
                    reason="native srmech_riemann_theta_gate_decide not loaded")
def test_native_gate_decide_rejects_bad_input():
    """The C kernel's input validation: bad genus raises before the call; a
    malformed factor char length raises in the marshaller."""
    with pytest.raises(ValueError):
        _native.riemann_theta_gate_decide_c(1, 4, True,
                                            [rt._spec_duplication(2)])
    with pytest.raises(ValueError):
        _native.riemann_theta_gate_decide_c(6, 4, True,
                                            [rt._spec_duplication(5)])
    with pytest.raises(ValueError):
        # g=3 call with g=2-shaped factor chars
        _native.riemann_theta_gate_decide_c(3, 4, True,
                                            [rt._spec_duplication(2)])


# ──────────────────────────────────────────────────────────────────────
# the sparse machinery's own contracts
# ──────────────────────────────────────────────────────────────────────

def test_sparse_factor_is_box_free_safe_support():
    """The sparse factor enumerator covers EXACTLY the safe support of the
    infinite theta series: it equals the box-enumerated factor restricted to
    the safe diagonal region for any box large enough — and needs no box."""
    # g2 quarter-nome trivial factor at safe=64 vs dense lattice(8) restricted
    fac = rt._sparse_factor(2, 64, 1, 2, (0, 0), (0, 0))
    dense = RiemannTheta.theta_constant((0, 0), (0, 0)).lattice(8)
    dense_r = {k: v for k, v in dense.items() if k[0] <= 64 and k[1] <= 64}
    assert fac == dense_r


def test_sparse_cross_slots_shape():
    """The genus-g cross slots are the pairs (i, g-1) — one for g2, two for g3,
    three for g4, four for g5 (the gates' own cross checks)."""
    assert rt._sparse_cross_slots(2) == (2,)
    assert rt._sparse_cross_slots(3) == (4, 5)
    assert rt._sparse_cross_slots(4) == (6, 8, 9)
    assert rt._sparse_cross_slots(5) == (8, 11, 13, 14)


def test_tools_total_unchanged():
    """Gate internals, not new ops: tools.total stays 362."""
    import srmech
    assert srmech.describe()["tools"]["total"] == 376
