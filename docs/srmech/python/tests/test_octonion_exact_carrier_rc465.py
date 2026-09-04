"""rc465 (`#T1188`) — the R2-SHIELDED carrier demotions, fixed and gated.

WHAT WAS WRONG
==============
Nine ops across ``srmech.physics.qm.octonion``, ``.quaternion`` and
``.triality`` coerced with ``[float(c) for c in v]`` **at the entry, before any
arithmetic**, and returned the rounded value with no exception, no warning, no
status and no accuracy statement — while a carrier that computes the same
object exactly ships one import away (``cascade.cd_conjugate`` → the C peer
``srmech_cd_qconjugate``; ``cascade.left_mult_matrix`` → ``srmech_cd_mult`` /
``srmech_cd_qbasis``; ``cascade.cd_norm_sq`` → ``srmech_cd_qnorm_sq``).

Measured on the shipped rc464 tree, ``x = [2**53+1, 0, …]``:

    octonion_left_mult(x)[0, 0]   9007199254740992.0   exact 9007199254740993
    octonion_right_mult(x)[0, 0]  9007199254740992.0   exact 9007199254740993
    octonion_conjugate(x)[0]      9007199254740992.0   exact 9007199254740993
    octonion_norm(x)              9007199254740992.0   exact 9007199254740993
    triality_apply(x, 'v', 'v')[0] 9007199254740992.0  exact 9007199254740993

and the same five at rung 4. ``octonion_conjugate`` is the sharpest of them:
the op performs NO ARITHMETIC — it negates seven components — and changed the
value it was handed. That is ``einsum("ij->ji")``'s witness in another module.

WHY rc463's GATE COULD NOT SEE IT — R2 SHIELDING
=================================================
``tests/test_silent_carrier_demotion_rc463.py`` states five conjuncts, and its
ADMISSION conjunct is decided **by the SIGNATURE**. All nine ops declare
``Sequence[float]``, so they were excluded BY CONSTRUCTION however exact the
operand actually handed over. rc463's own honesty ladder rates a float
parameter ANNOTATION at rung **R2 — "WEAK … nothing enforces it"**, and then
let exactly that rung decide membership. A type annotation stood in for an
accuracy contract.

The detector half of the repair is ``tools/demotion_probe.py``, which admits by
MEASUREMENT over every sequence-shaped REGISTRY parameter. This file is the
op half.

THE FIX, AND THE ONE THING IT IS NOT
=====================================
Operand-typed dispatch, exactly as rc463 gave ``einsum`` and ``kron``: an
operand whose every component is exact (``int`` / ``Q`` / a
``numerator``-``denominator`` pair) rides the exact carrier; ONE float
component anywhere sends the whole call down the f64 route; ``QMat.to_mat()``
is the on-demand projection. **There is no new ``exact=`` keyword.** rc463
established that ``exact=`` already means two different things in this package
(an exact CARRIER vs an exact ROUTE with a declared float lift); a third sense
on a third surface is not a fix.

``*_norm`` is the one op where the distinction bites, and it is stated rather
than smoothed over: its radicand is exact, its Class-N root is exact when the
root is rational and otherwise carries a declared ``2**-54`` relative bound.
That is an exact ROUTE, and the docstring says so.

numpy-free. No ``abs()`` — the significand read is a Class-K pin-slot branch.
"""

import pytest

from srmech.cascade import (
    cd_conjugate,
    cd_norm_sq,
    left_mult_matrix,
    right_mult_matrix,
)
from srmech.math.mat import Mat
from srmech.math.q import Q
from srmech.math.qmat import QMat
from srmech.mcp import invoke_tool
from srmech.physics.qm.octonion import (
    octonion_conjugate,
    octonion_left_mult,
    octonion_norm,
    octonion_right_mult,
)
from srmech.physics.qm.quaternion import (
    quaternion_conjugate,
    quaternion_left_mult,
    quaternion_norm,
    quaternion_right_mult,
)
from srmech.physics.qm.triality import triality_apply

#: ``2**53 + 1`` — the smallest positive integer float64 cannot represent.
P = 2 ** 53 + 1
#: The reported witness: float64 spacing at ``2**59`` is 64, so ``+24`` rounds
#: DOWN and the first component comes back 24 low. Kept because it is the one
#: the audit quoted, and a gate should be able to reproduce the number that
#: raised it.
P59 = 2 ** 59 + 24
P59_ROUNDED = 2 ** 59


def _significand_bits(n: int) -> int:
    """Width of ``n``'s significand. Sign is a **Class-K pin-slot** branch,
    never an ALU ``abs()`` (lifted from the rc463 gate, same reason)."""
    if n < 0:
        n = -n
    if n == 0:
        return 0
    while n % 2 == 0:
        n //= 2
    return n.bit_length()


def _o(w):
    return [w] + [0] * 7


def _q4(w):
    return [w] + [0] * 3


# ── LAYER 0 — the witnesses could have failed ────────────────────────────────
def test_the_witnesses_are_discriminating() -> None:
    """An instrument that cannot return otherwise is not a measurement."""
    assert _significand_bits(P) == 54
    assert float(P) != P and int(float(P)) == 2 ** 53
    assert _significand_bits(P59) == 57
    assert int(float(P59)) == P59_ROUNDED, (
        "the 2**59+24 witness stopped rounding; it is no longer the reported one")


# ── (1) EXACT IN, EXACT OUT — strict zero on all nine ops ────────────────────
def test_octonion_left_mult_is_exact_on_an_exact_operand() -> None:
    m = octonion_left_mult(_o(P))
    assert isinstance(m, QMat), f"exact operand returned {type(m).__name__}"
    assert m[0, 0] == Q(P, 1), f"L_a[0,0] = {m[0, 0]!r}"


def test_octonion_right_mult_is_exact_on_an_exact_operand() -> None:
    m = octonion_right_mult(_o(P))
    assert isinstance(m, QMat)
    assert m[0, 0] == Q(P, 1)


def test_octonion_conjugate_is_exact_on_an_exact_operand() -> None:
    """THE witness for the class: no arithmetic happens here at all."""
    got = octonion_conjugate([P, 1, 0, 0, 0, 0, 0, 0])
    assert got[0] == Q(P, 1), f"a sign flip changed the value: {got[0]!r}"
    assert got[1] == Q(-1, 1)
    assert all(isinstance(c, Q) for c in got)


def test_octonion_norm_is_exact_on_an_exact_operand() -> None:
    """``√(P²) = P`` — a perfect square, so the Class-N root lands on the nose
    and the declared ``2**-54`` bound is not being leaned on here."""
    n = octonion_norm(_o(P))
    assert isinstance(n, Q), f"exact operand returned {type(n).__name__}"
    assert n == Q(P, 1), f"‖x‖ = {n!r}"


def test_triality_apply_is_exact_on_an_exact_operand() -> None:
    got = triality_apply([P, 1, 0, 0, 0, 0, 0, 0], "v", "s")
    assert got[0] == Q(P, 1)
    assert all(isinstance(c, Q) for c in got)


def test_quaternion_quad_is_exact_on_an_exact_operand() -> None:
    assert octonion_left_mult is not quaternion_left_mult      # rung 4, same rule
    assert quaternion_left_mult(_q4(P))[0, 0] == Q(P, 1)
    assert quaternion_right_mult(_q4(P))[0, 0] == Q(P, 1)
    assert quaternion_conjugate(_q4(P))[0] == Q(P, 1)
    assert quaternion_norm(_q4(P)) == Q(P, 1)


@pytest.mark.parametrize("label,call", [
    ("octonion_left_mult", lambda w: octonion_left_mult(_o(w))[0, 0]),
    ("octonion_right_mult", lambda w: octonion_right_mult(_o(w))[0, 0]),
    ("octonion_conjugate", lambda w: octonion_conjugate(_o(w))[0]),
    ("octonion_norm", lambda w: octonion_norm(_o(w))),
    ("triality_apply", lambda w: triality_apply(_o(w), "v", "v")[0]),
    ("quaternion_left_mult", lambda w: quaternion_left_mult(_q4(w))[0, 0]),
    ("quaternion_right_mult", lambda w: quaternion_right_mult(_q4(w))[0, 0]),
    ("quaternion_conjugate", lambda w: quaternion_conjugate(_q4(w))[0]),
    ("quaternion_norm", lambda w: quaternion_norm(_q4(w))),
])
def test_the_reported_minus_24_is_gone(label, call) -> None:
    """The audit's own witness, on every one of the nine ops.

    Through rc464 each of these returned ``576460752303423488`` — the operand
    minus 24 — because float64's spacing at ``2**59`` is 64.
    """
    got = call(P59)
    assert got == Q(P59, 1), (
        f"{label} returned {got!r}; the exact value is {P59}. Through rc464 it "
        f"returned {P59_ROUNDED} (the reported −24).")


# ── (2) FLOAT IS THE CALLER'S OWN REQUEST, and it is byte-identical ──────────
_SMALL = [1, 2, -3, 4, 0, 1, -1, 2]
_SMALL4 = [1, 2, -3, 4]


@pytest.mark.parametrize("op,vec", [
    (octonion_left_mult, _SMALL), (octonion_right_mult, _SMALL),
    (quaternion_left_mult, _SMALL4), (quaternion_right_mult, _SMALL4),
])
def test_the_exact_result_projects_onto_the_float_route(op, vec) -> None:
    """``QMat.to_mat()`` is the "float on request" boundary, and it lands on the
    SAME matrix the f64 route produces. If these ever differ, one of the two
    routes has drifted — which is the co-equal-dual consistency oracle."""
    exact = op(vec)
    assert isinstance(exact, QMat)
    floated = op([float(c) for c in vec])
    assert isinstance(floated, Mat), (
        f"a float operand must stay on the float carrier; got "
        f"{type(floated).__name__}")
    assert exact.to_mat().tolist() == floated.tolist()


def test_one_float_component_sends_the_whole_call_to_the_float_route() -> None:
    """WHOLE-OPERAND admission (the rc463 ``_exact_nd`` rule). Mixing carriers
    mid-computation is the defect, not the cure — and it is why
    ``[3.0, 4, 0, …]``, which several shipped tests pass, keeps its float
    answer rather than silently changing carrier under them."""
    mixed = [P, 0, 0, 0, 0, 0, 0, 0.0]           # one float, seven exact
    assert isinstance(octonion_left_mult(mixed), Mat)
    assert isinstance(octonion_conjugate(mixed)[0], float)
    assert isinstance(octonion_norm([3.0, 4, 0, 0, 0, 0, 0, 0]), float)
    assert isinstance(quaternion_norm([3.0, 4, 0, 0]), float)


def test_a_float_operand_is_bit_identical_to_rc464() -> None:
    """The float route did not move. Pinned by VALUE, not by "it should be the
    same code" — the whole class exists because a route changed under a
    docstring that said it had not."""
    m = octonion_left_mult([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert isinstance(m, Mat)
    assert m.tolist() == [[1.0 if r == c else 0.0 for c in range(8)]
                          for r in range(8)]
    assert octonion_conjugate([1.0, 2.0, -3.0, 4.0, 0.0, 0.0, 0.0, 0.0]) == \
        [1.0, -2.0, 3.0, -4.0, -0.0, -0.0, -0.0, -0.0]
    assert quaternion_conjugate([1.0, 2.0, -3.0, 4.0]) == [1.0, -2.0, 3.0, -4.0]


# ── (3) THE CONVENTION DIFFERENTIAL — never executed before rc465 ────────────
# ``octonion_left_mult``'s docstring has asserted since rc122 that its table
# path is "bit-identical to the per-basis binds ``loop_left_op`` column-stacks
# (same Cayley-Dickson-from-H convention)", and NOTHING executed the comparison
# against ``cascade.left_mult_matrix`` — which is now the exact route, so the
# claim became load-bearing. It holds; it is measured here rather than asserted.

def _int_vectors(dim, n=12, seed=1188):
    import random
    rnd = random.Random(seed)
    basis = [[1 if i == k else 0 for i in range(dim)] for k in range(dim)]
    return basis + [[rnd.randint(-9, 9) for _ in range(dim)] for _ in range(n)]


@pytest.mark.parametrize("op,cd_op,dim", [
    (octonion_left_mult, left_mult_matrix, 8),
    (octonion_right_mult, right_mult_matrix, 8),
    (quaternion_left_mult, left_mult_matrix, 4),
    (quaternion_right_mult, right_mult_matrix, 4),
])
def test_the_module_table_and_the_cd_product_are_the_same_operator(
        op, cd_op, dim) -> None:
    for v in _int_vectors(dim):
        assert op(v).to_lists() == cd_op(v), (
            f"{op.__name__} and cascade.{cd_op.__name__} disagree at dim {dim} "
            f"on {v} — the exact route is NOT the same operator as the shipped "
            f"table, and the rc122 convention claim is false")


@pytest.mark.parametrize("op,cd_op,dim", [
    (octonion_conjugate, cd_conjugate, 8),
    (quaternion_conjugate, cd_conjugate, 4),
])
def test_the_conjugate_exact_route_is_the_cd_conjugate(op, cd_op, dim) -> None:
    for v in _int_vectors(dim):
        assert op(v) == list(cd_op(v))


@pytest.mark.parametrize("op,dim", [(octonion_norm, 8), (quaternion_norm, 4)])
def test_the_norm_radicand_is_the_cd_norm_form(op, dim) -> None:
    """``N(x) = Re(x·x̄)`` is what is rooted — not a hand-rolled ``Σ x_i²``."""
    for v in _int_vectors(dim):
        n = op(v)
        assert isinstance(n, Q)
        # squaring the root recovers the exact norm form whenever the root is
        # rational; otherwise it is within the declared Class-N grid.
        radicand = cd_norm_sq(v)
        assert n * n == radicand or (n * n - radicand) * (n * n - radicand) \
            < Q(1, 2 ** 50) * radicand * radicand + Q(1, 2 ** 50)


# ── (4) triality_apply — its FIRST tests ─────────────────────────────────────
# Zero tests referenced this op before rc465, in the whole tree. Nothing would
# have caught a regression in it, which is a fair part of why it demoted for
# 340-odd releases with no one noticing.

def test_triality_apply_identity_returns_the_operand_unchanged() -> None:
    v = [1, -2, 3, -4, 5, -6, 7, -8]
    assert triality_apply(v, "v", "v") == [Q(c, 1) for c in v]
    fv = [float(c) for c in v]
    assert triality_apply(fv, "8v", "8v") == fv


def test_triality_apply_one_step_is_the_conjugation_companion() -> None:
    v = [1, -2, 3, -4, 5, -6, 7, -8]
    assert triality_apply(v, "v", "s") == list(cd_conjugate(v))


def test_the_v_s_c_v_round_trip_is_a_CONJUGATION_not_the_identity() -> None:
    """MEASURED, and it is not what the op's name suggests.

    Each elementary step is ONE octonion conjugation, and the cycle distance is
    read mod 3 (Class I), so ``v → s → c → v`` applies THREE conjugations —
    and ``conj² = id``, so three is one. The round trip therefore returns
    ``conj(x)``, not ``x``.

    That is what the code does; whether it is what the ``8_v → 8_s → 8_c``
    transport SHOULD do is an algebra question outside rc465's carrier scope,
    and the op's own docstring already hedges it ("an order-3-compatible
    reflection on the unit imaginary axes is unnecessary for the rep-label
    bookkeeping"). It is pinned here rather than left unmeasured, because this
    file is the op's FIRST test and an unpinned round trip is exactly the kind
    of thing a later change would silently alter. Recorded as an rc465
    observation; nothing is claimed about which behaviour is right.
    """
    v = [1, -2, 3, -4, 5, -6, 7, -8]
    once = triality_apply(v, "v", "s")
    twice = triality_apply(once, "s", "c")
    thrice = triality_apply(twice, "c", "v")
    assert thrice == list(cd_conjugate(v)), (
        "the v→s→c→v round trip stopped being a single conjugation")
    assert thrice != [Q(c, 1) for c in v], (
        "the round trip became the identity — a BEHAVIOUR change in an op that "
        "had no test at all before rc465; adjudicate it, do not adjust this line")
    # and the transport is order-3 in its own terms: four steps == one step.
    assert triality_apply(thrice, "v", "s") == [Q(c, 1) for c in v]


def test_triality_apply_rejects_a_wrong_length_on_both_carriers() -> None:
    with pytest.raises(ValueError, match="8-vector"):
        triality_apply([1, 2, 3], "v", "s")
    with pytest.raises(ValueError, match="8-vector"):
        triality_apply([1.0, 2.0, 3.0], "v", "s")


# ── (5) ARITY IS CARRIER-INDEPENDENT ────────────────────────────────────────
@pytest.mark.parametrize("op,short_exact,short_float", [
    (octonion_left_mult, [1, 2, 3], [1.0, 2.0, 3.0]),
    (octonion_right_mult, [1, 2, 3], [1.0, 2.0, 3.0]),
    (octonion_conjugate, [1, 2, 3], [1.0, 2.0, 3.0]),
    (octonion_norm, [1, 2, 3], [1.0, 2.0, 3.0]),
    (quaternion_left_mult, [1, 2], [1.0, 2.0]),
    (quaternion_right_mult, [1, 2], [1.0, 2.0]),
    (quaternion_conjugate, [1, 2], [1.0, 2.0]),
    (quaternion_norm, [1, 2], [1.0, 2.0]),
])
def test_a_short_vector_raises_on_both_routes(op, short_exact, short_float) -> None:
    """The exact route must NOT quietly accept an operand the float route
    rejects. ``tests/test_declared_raises_execution_rc434.py`` drives the float
    half; this is the exact half, and it is why the length check deliberately
    lives in the float coercer rather than in the admission gate."""
    with pytest.raises(ValueError):
        op(short_exact)
    with pytest.raises(ValueError):
        op(short_float)


# ── (6) THE WIRE — an exact result must survive the MCP boundary ────────────
def test_an_exact_operand_crosses_the_wire_as_the_exact_carrier() -> None:
    """``coerce_param`` already preserved an exact ``int`` through an ``HV``
    parameter; the OUTBOUND half is what a QMat return newly needs, and it
    already ships (``_CARRIER_WIRE["QMat"]``). Proven by call, not by reading
    the map."""
    out = invoke_tool("srmech.physics.qm.octonion.octonion_left_mult",
                      {"a": _o(P)})
    assert isinstance(out, QMat), (
        f"the wire returned {type(out).__name__}; an exact operand must not "
        f"lose its carrier crossing the MCP boundary")
    assert out[0, 0] == Q(P, 1)


def test_an_exact_conjugate_crosses_the_wire_as_exact_rationals() -> None:
    out = invoke_tool("srmech.physics.qm.octonion.octonion_conjugate",
                      {"x": _o(P)})
    assert out[0] == Q(P, 1) or out[0] == [P, 1], repr(out[0])


def test_the_float_route_still_crosses_as_a_float_matrix() -> None:
    out = invoke_tool("srmech.physics.qm.octonion.octonion_left_mult",
                      {"a": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]})
    assert isinstance(out, Mat)


# ── (7) the REGISTRY says both carriers ─────────────────────────────────────
@pytest.mark.parametrize("name,want", [
    ("srmech.physics.qm.octonion.octonion_left_mult", "Mat | QMat"),
    ("srmech.physics.qm.octonion.octonion_right_mult", "Mat | QMat"),
    ("srmech.physics.qm.octonion.octonion_conjugate", "list[float] | list[Q]"),
    ("srmech.physics.qm.octonion.octonion_norm", "float | Q"),
    ("srmech.physics.qm.triality.triality_apply", "list[float] | list[Q]"),
    ("srmech.physics.qm.quaternion.quaternion_left_mult", "Mat | QMat"),
    ("srmech.physics.qm.quaternion.quaternion_right_mult", "Mat | QMat"),
    ("srmech.physics.qm.quaternion.quaternion_conjugate", "list[float] | list[Q]"),
    ("srmech.physics.qm.quaternion.quaternion_norm", "float | Q"),
])
def test_the_declared_return_names_both_carriers(name, want) -> None:
    """A caller must be able to read which carrier comes back BEFORE calling.
    An R1 return-type declaration is not an accuracy contract — but a return
    type that names only ONE of two live carriers is simply FALSE, which is a
    rung below R1."""
    from srmech.introspect.tool_schema import get_tool_schema
    entry = get_tool_schema().lookup(name)
    assert entry is not None, name
    assert entry.returns.type == want, (
        f"{name} declares {entry.returns.type!r}, live carriers are {want!r}")
