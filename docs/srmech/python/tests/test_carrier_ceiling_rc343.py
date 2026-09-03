"""rc343 (`#T972`) — a ceiling is PER-CARRIER, and a stated reason must be a
mechanism a carrier row can CONTRADICT.

THE DEFECT rc339 SHIPPED
------------------------
rc339 fixed a real thing: ``describe()`` had been reporting ADDRESSING limits
with no capability attached. But the fix introduced two worse claims.

1. ``limits["capabilities"]["turn"]["bounded_by"] = "associativity"`` is a
   **RESTATEMENT OF THE DEFINITION**. The same payload DEFINES ``turn`` as
   ``x*(y*z) == (x*y)*z for every z`` — so turn composition IS associativity.
   Anything associative turns; anything that turns is associative. The field
   could not discriminate between two carriers and no measurement could falsify
   it — the same false-green shape rc339 was written to remove.

2. ``limits["capabilities"]["turn"]["max_dim"] = 4`` was published as a GLOBAL
   statement, and **it is false for any associative carrier at dimension.** Two
   rows in rc339's OWN payload contradict it:

   * ``Mat``'s product ``mat_matmul`` is associative at every dim. MEASURED over
     the matrix units of ``M_n(R)``: 81/81 turn-composing pairs at ``n=3``
     (algebra dim 9), 42 of them NON-commuting; 256/256 at ``n=4`` (dim 16), 108
     non-commuting. Both dims are above 4.
   * ``Poly`` (and ``BiPoly`` / ``TriPoly`` / ``QPoly`` / ``QBiPoly``) is an
     integral domain at unbounded degree, so ``compose: "full"`` holds
     arbitrarily far above the ``compose`` ceiling of 8.

   The turn ceiling of 4 is a **Cayley-Dickson** fact. Cayley-Dickson by
   contrast gives NON-COMMUTING turn 0/64 at dim 8 and 0/256 at dim 16 — the
   ceiling is real THERE. It is not a statement about every carrier srmech
   ships.

THE REPLACEMENT WITH ACTUAL CONTENT — the index/sign split
----------------------------------------------------------
The Cayley-Dickson product FACTORS, and the halves behave completely
differently. MEASURED over the shipped ``cd_basis_product``::

    dim | index == a XOR b | negative signs (C(d,2)) | SIGN COCYCLE associative
      2 |       4/4        |        1  (1)           |     8/8       100%
      4 |      16/16       |        6  (6)           |    64/64      100%
      8 |      64/64       |       28  (28)          |   344/512      67%
     16 |     256/256      |      120  (120)         |  2248/4096     55%
     32 |    1024/1024     |      496  (496)         | 16808/32768    51%

The INDEX lane is XOR, exact at every rung with no exceptions. The SIGN is a
cocycle over it, and the SIGN is what stops being associative — abruptly, at
dim 8. So **addressing is unbounded because XOR is associative at every dim
forever; turns and composition break because THE SIGN COCYCLE stops being
associative.** The wall was never in the addressing, which is also why rc298
(`#T933`) could lift ``CD_MAX_DIM`` 64 -> 256 by DECOUPLING the caps.

*Honest label:* ``index == XOR`` is close to DEFINITIONAL for a Cayley-Dickson
basis (the basis product IS ``+-e_{i^j}`` by construction), so that column is a
CHECK, not a discovery. What is NOT definitional is the READING — that the
ladder splits into a free index and a load-bearing sign, and that every ceiling
srmech publishes lives on one side of the split. The ``C(d,2)`` regularity and
the 100% -> 67% -> 55% cocycle drop are the support, and no more than that.

WHAT THIS MODULE HOLDS DOWN
---------------------------
The rc339 ratchet fails if a limit is reported without a capability dimension.
This one adds the check that would have caught rc339 itself:

1. **A ceiling a carrier BEATS must be scoped.** For every capability, MEASURE
   the capability above its published ceiling on every carrier whose row claims
   it in FULL. If a carrier really delivers it up there, the payload must say so
   — ``family`` naming what the number is a fact about, and the carrier named in
   the derived ``exceeded_by``. **This is the check that fires on rc339**, whose
   turn ceiling of 4 is beaten by a measured ``Mat`` and carries neither key.
2. **A reason must be a MECHANISM, not the definition restated.** ``bounded_by``
   must come from the closed :data:`CEILING_MECHANISMS` vocabulary, and the test
   measures each named mechanism SEPARATELY from the capability's own ``means``
   and checks that it predicts the ceiling. ``"associativity"`` is not in the
   vocabulary and cannot be measured apart from ``means`` — which is exactly
   why it is not admissible.
3. **The split is real** — the index lane and the sign cocycle are measurably
   DIFFERENT objects (the index stays exact precisely where the sign fails), so
   naming the sign cocycle is informative rather than circular.

No float, no numpy, no ``abs()``.
"""

from __future__ import annotations

import pytest

from srmech.introspect.carrier_schema import (
    CEILING_MECHANISMS,
    _CAPABILITY,
    _CARRIERS,
)
from srmech.cascade.cayley_dickson import (
    CD_COMPOSE_MAX_DIM,
    CD_MAX_DIM,
    CD_TURN_MAX_DIM,
    cd_basis_product,
)
from srmech.math.mat import Mat
from srmech.math.poly import Poly
from srmech.introspect import describe

#: The three capability axes (same set the rc339 ratchet walks).
CAPABILITIES = ("address", "compose", "turn")

#: The verdict that counts as "this capability holds in FULL" on a carrier row.
#: Must agree with ``srmech.introspect._FULL_VERDICT``; pinned below.
FULL_VERDICT = {"address": "exact", "compose": "full", "turn": "non_commuting"}

#: Reasons that merely RESTATE what the capability already means. rc339 shipped
#: the first one. Kept as an explicit blocklist ON TOP of the closed vocabulary
#: so the specific regression has a named, greppable guard and cannot come back
#: by someone widening CEILING_MECHANISMS without reading why it is closed.
_DEFINITIONAL_NON_REASONS = {
    "turn": ("associativity", "associative", "non_associativity"),
    "compose": ("zero_divisors", "composition", "no_zero_divisors"),
    "address": ("addressing", "addressability", "exactness"),
}


# ──────────────────────────────────────────────────────────────────────
# measurement helpers — each mechanism gets measured on its OWN terms
# ──────────────────────────────────────────────────────────────────────

def _mat_unit(n: int, r: int, c: int) -> Mat:
    """The matrix unit ``E_rc`` of ``M_n``, as the shipped carrier."""
    rows = [[0] * n for _ in range(n)]
    rows[r][c] = 1
    return Mat.from_rows(rows)


def _mat_turn_report(n: int):
    """Over the ``n**2`` matrix units of ``M_n``: how many ordered pairs COMPOSE
    a turn (``L_x o L_y == L_(x*y)`` against every third unit), and how many of
    those are NON-COMMUTING. Exhaustive, not sampled."""
    units = [_mat_unit(n, r, c) for r in range(n) for c in range(n)]
    compose = 0
    non_commuting = 0
    for x in units:
        for y in units:
            xy = x @ y
            if all((x @ (y @ z)) == (xy @ z) for z in units):
                compose += 1
                if xy != (y @ x):
                    non_commuting += 1
    return compose, non_commuting, len(units) ** 2


def _cd_index_lane_exact(dim: int):
    """Is the INDEX half exactly ``i XOR j``? Returns (matches, total)."""
    ok = 0
    total = 0
    for i in range(dim):
        for j in range(dim):
            _, idx = _sign_index(dim, i, j)
            total += 1
            if idx == (i ^ j):
                ok += 1
    return ok, total


def _sign_index(dim: int, i: int, j: int):
    """``e_i * e_j = sign * e_index`` as (sign_bit, index). ``sign_bit`` is a
    Class-K pin-slot read of the sign — 0 for +, 1 for - — never ``abs()``."""
    index, sign = cd_basis_product(dim, i, j)
    return (0 if sign > 0 else 1), index


def _cd_negative_signs(dim: int) -> int:
    return sum(1 for i in range(dim) for j in range(dim)
               if _sign_index(dim, i, j)[0])


def _cd_sign_cocycle_associative(dim: int):
    """Is the SIGN half associative, with the index half factored OUT?

    The index lane is XOR on BOTH bracketings by construction, so it cancels and
    every failure counted here is purely the sign cocycle. This is the whole
    point: it measures the named mechanism WITHOUT measuring the capability's
    own definition."""
    sign = {(a, b): _sign_index(dim, a, b)[0]
            for a in range(dim) for b in range(dim)}
    ok = 0
    total = 0
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                left = sign[(a, b)] ^ sign[(a ^ b, c)]
                right = sign[(b, c)] ^ sign[(a, b ^ c)]
                total += 1
                if left == right:
                    ok += 1
    return ok, total


#: Carriers this module can CONSTRUCT and measure above a ceiling. A carrier
#: absent here is not exempt — it is simply not the one that falsifies a
#: ceiling, and the scoping check below still requires the payload to name it.
_MEASURABLE_ABOVE_CEILING = {
    # carrier -> (capability, algebra dim to test at, measurement)
    "Mat": ("turn", 9, lambda: _mat_turn_report(3)),
    "Poly": ("compose", 12, None),  # degree law, measured in its own test
}


# ──────────────────────────────────────────────────────────────────────
# 1. THE NEW RATCHET — a ceiling a carrier BEATS must be scoped
# ──────────────────────────────────────────────────────────────────────

def test_a_ceiling_a_carrier_beats_must_be_scoped_to_its_family():
    """**THE rc343 RATCHET, and the check that fires on the rc339 payload.**

    For each capability: take every carrier whose row claims the capability in
    FULL, and ask whether it delivers it ABOVE the published ceiling. A carrier
    row is allowed to beat a ceiling — ``Mat`` genuinely does — but then the
    ceiling is NOT a universal statement, and the payload has to say which
    family it is a fact about (``family``) and which carriers outrun it
    (``exceeded_by``).

    Run against rc339/rc342 this fails twice over: ``turn`` has ``max_dim`` 4,
    ``Mat`` beats it, and neither ``family`` nor ``exceeded_by`` exists."""
    caps = describe()["limits"]["capabilities"]
    for name in CAPABILITIES:
        cap = caps[name]
        ceiling = cap.get("max_dim")
        full = FULL_VERDICT[name]

        beaters = sorted(
            cname for cname, row in _CAPABILITY.items()
            if row.get(name) == full
            and (ceiling is None or row.get("max_dim") is None
                 or row["max_dim"] > ceiling)
        )
        if not beaters:
            continue

        # A ceiling with counterexamples MUST be scoped. This is the rc339 gap.
        assert cap.get("family"), (
            f"limits.capabilities[{name!r}].max_dim == {ceiling} is beaten by "
            f"carrier row(s) {beaters} in this same payload, so it is NOT a "
            f"universal ceiling — it must carry `family` naming the carrier "
            f"family it IS a fact about. Publishing it unscoped is how a "
            f"Cayley-Dickson fact comes to read as a statement about every "
            f"carrier srmech ships.")
        assert cap.get("exceeded_by") == beaters, (
            f"limits.capabilities[{name!r}].exceeded_by must name every carrier "
            f"row that outruns the ceiling; expected {beaters}, got "
            f"{cap.get('exceeded_by')!r}. It is DERIVED from the carrier table "
            f"— a mismatch means the derivation drifted from the rows.")


def test_the_turn_ceiling_is_beaten_by_a_MEASURED_carrier_not_a_declared_one():
    """The scoping check above would be worth little if the beating row were
    merely ASSERTED. ``Mat`` is measured here: at ``n=3`` the algebra dim is 9,
    which is above the published turn ceiling of 4, and its turns compose
    EXHAUSTIVELY with the which-way intact."""
    compose, non_commuting, total = _mat_turn_report(3)
    assert (compose, non_commuting, total) == (81, 42, 81), (
        "M_3(R) turn report changed; the rc343 counterexample rests on it")
    assert 3 * 3 > CD_TURN_MAX_DIM, "n=3 must sit above the CD turn ceiling"
    assert non_commuting > 0, (
        "the whole point is that NON-COMMUTING turn composition survives here, "
        "which is precisely what dies at the octonion rung")

    caps = describe()["limits"]["capabilities"]
    assert "Mat" in caps["turn"]["exceeded_by"], (
        "Mat measurably composes non-commuting turns at algebra dim 9 > 4, so "
        "the published turn ceiling must name it as exceeding")


def test_the_compose_ceiling_is_beaten_by_the_polynomial_ladder():
    """``Poly`` is an integral domain at unbounded degree — ``deg(p*q) ==
    deg p + deg q``, so a product of nonzero polynomials is nonzero however far
    up you go. Its row says ``compose: "full"``, and that is true well above the
    ``compose`` ceiling of 8."""
    for da in range(1, 8):
        for db in range(1, 8):
            product = Poly([0] * da + [1]) * Poly([0] * db + [1])
            assert product.degree == da + db, (
                f"deg law broke at ({da}, {db}) — the no-zero-divisor argument "
                f"for the polynomial ladder rests on it")
            assert product.coeffs, "a product of nonzero polys must be nonzero"
    assert 8 + 8 > CD_COMPOSE_MAX_DIM
    caps = describe()["limits"]["capabilities"]
    assert "Poly" in caps["compose"]["exceeded_by"]


# ──────────────────────────────────────────────────────────────────────
# 2. A REASON MUST BE A MECHANISM, NOT THE DEFINITION RESTATED
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", CAPABILITIES)
def test_bounded_by_is_a_mechanism_from_the_closed_vocabulary(name):
    """``bounded_by`` is not free text. A reason is admissible only if it names
    a mechanism the tests can measure SEPARATELY from the capability's own
    ``means`` — see :data:`CEILING_MECHANISMS`."""
    cap = describe()["limits"]["capabilities"][name]
    reason = cap.get("bounded_by")
    assert reason in CEILING_MECHANISMS, (
        f"limits.capabilities[{name!r}].bounded_by == {reason!r} is not in the "
        f"closed mechanism vocabulary {sorted(CEILING_MECHANISMS)}. A ceiling "
        f"reason must be measurable apart from the capability it bounds.")


@pytest.mark.parametrize("name", CAPABILITIES)
def test_bounded_by_does_not_merely_restate_the_definition(name):
    """**The anti-tautology gate — the rc339 defect stated directly.**

    ``turn`` is DEFINED in ``means`` as ``x*(y*z) == (x*y)*z``, so
    ``bounded_by: "associativity"`` says only "turn is bounded by turn". Such a
    field cannot discriminate and cannot be falsified. The blocklist is per
    capability because what counts as a restatement depends on what the
    capability already means."""
    cap = describe()["limits"]["capabilities"][name]
    reason = cap.get("bounded_by")
    banned = _DEFINITIONAL_NON_REASONS[name]
    assert reason not in banned, (
        f"limits.capabilities[{name!r}].bounded_by == {reason!r} RESTATES what "
        f"`means` already says ({cap.get('means')!r}). That is not an "
        f"explanation: anything satisfying it has the capability and anything "
        f"with the capability satisfies it, so no carrier row could ever "
        f"contradict it. Name the MECHANISM instead.")


def test_the_turn_mechanism_is_the_sign_cocycle_and_it_predicts_the_ceiling():
    """The named mechanism is measured on its own terms and must PRODUCE the
    ceiling it is claimed to explain.

    With the index half factored out (it is XOR on both bracketings, so it
    cancels), the sign cocycle is fully associative at dims 2 and 4 and BREAKS
    at dim 8 — which puts the ceiling at 4, independently of any statement
    about turns."""
    caps = describe()["limits"]["capabilities"]
    assert caps["turn"]["bounded_by"] == "sign_cocycle"

    measured = {}
    for dim in (2, 4, 8, 16):
        ok, total = _cd_sign_cocycle_associative(dim)
        measured[dim] = (ok, total)
    assert measured == {2: (8, 8), 4: (64, 64),
                        8: (344, 512), 16: (2248, 4096)}, measured

    # The mechanism predicts the ceiling: the largest dim whose sign cocycle is
    # FULLY associative is CD_TURN_MAX_DIM. Derived, not asserted beside it.
    fully = [d for d, (ok, total) in measured.items() if ok == total]
    assert max(fully) == CD_TURN_MAX_DIM == 4, (
        f"the sign cocycle is fully associative through dim {max(fully)}, but "
        f"CD_TURN_MAX_DIM is {CD_TURN_MAX_DIM} — the mechanism no longer "
        f"predicts the ceiling it is published as the reason for")


def test_the_index_lane_and_the_sign_are_measurably_different_objects():
    """What makes "bounded by the sign cocycle, not by the index" informative
    rather than circular: the two halves are measured SEPARATELY and they
    disagree. The index lane stays exact at exactly the dims where the sign
    cocycle fails.

    Honest label: ``index == XOR`` is close to DEFINITIONAL for a CD basis, so
    this column is a CHECK. The READING it supports — a free index and a
    load-bearing sign — is what is not definitional."""
    for dim in (2, 4, 8, 16, 32):
        ok, total = _cd_index_lane_exact(dim)
        assert ok == total == dim * dim, (
            f"the index lane is not exactly XOR at dim {dim} ({ok}/{total})")
        # The sign's negative count is the C(dim, 2) regularity.
        assert _cd_negative_signs(dim) == dim * (dim - 1) // 2, (
            f"negative-sign count off C(dim,2) at dim {dim}")

    # The separation itself: at dim 8 the index is perfect and the sign is not.
    idx_ok, idx_total = _cd_index_lane_exact(8)
    sign_ok, sign_total = _cd_sign_cocycle_associative(8)
    assert idx_ok == idx_total, "index half must be exact at dim 8"
    assert sign_ok < sign_total, "sign half must FAIL at dim 8"


def test_addressing_is_unbounded_because_the_free_half_is_the_index():
    """The positive half of the same reading. ``address`` is ``bounded_by:
    "tooling"`` — a build constant, not a wall — and the mechanism check is that
    the index lane is exact at every rung measured, including above
    ``CD_DENSE_MAX_DIM``. rc298 (`#T933`) lifting the cap 64 -> 256 is the
    historical corroboration."""
    caps = describe()["limits"]["capabilities"]
    assert caps["address"]["bounded_by"] == "tooling"
    assert caps["address"]["beyond_ceiling"] is None, (
        "nothing lies past a tooling ceiling — that is what makes it tooling")
    ok, total = _cd_index_lane_exact(32)
    assert ok == total, "the index lane must be exact above CD_DENSE_MAX_DIM"
    assert caps["address"]["max_dim"] == CD_MAX_DIM


# ──────────────────────────────────────────────────────────────────────
# 3. THE PER-CARRIER SHAPE
# ──────────────────────────────────────────────────────────────────────

def test_every_carrier_declares_its_own_ceiling_and_a_valid_reason():
    """Additive to the rc339 row: each carrier now carries ``max_dim`` (``None``
    == unbounded in dim) and ``bounded_by`` from the closed vocabulary. A new
    carrier cannot inherit silence on either."""
    for name in sorted(_CARRIERS):
        row = _CAPABILITY[name]
        assert "max_dim" in row, f"{name}: no per-carrier ceiling"
        assert "bounded_by" in row, f"{name}: no ceiling reason"
        max_dim = row["max_dim"]
        assert max_dim is None or (isinstance(max_dim, int) and max_dim >= 1), (
            f"{name}: max_dim must be a dim or None (unbounded), got {max_dim!r}")
        reason = row["bounded_by"]
        assert reason is None or reason in CEILING_MECHANISMS, (
            f"{name}: bounded_by {reason!r} not in {sorted(CEILING_MECHANISMS)}")
        # An unbounded carrier has no wall, so it may not name a mechanism for
        # one; a bounded carrier must say why it stops.
        if max_dim is None:
            assert reason is None, (
                f"{name}: max_dim None means UNBOUNDED — naming a mechanism "
                f"({reason!r}) for a wall that is not there is a false green")
        else:
            assert reason is not None, (
                f"{name}: declares a ceiling of {max_dim} with no mechanism")


def test_the_cd_rungs_ceilings_are_their_own_dims():
    """A Cayley-Dickson rung IS its dimension, so its ``bounded_by`` is
    ``"definition"`` and not a wall. This keeps the per-carrier field from being
    read as "the quaternions run out at 4" — they ARE 4."""
    for name, dim in (("float", 1), ("complex", 2), ("quaternion", 4),
                      ("octonion", 8), ("sedenion", 16)):
        row = _CAPABILITY[name]
        assert row["max_dim"] == dim, f"{name}: expected dim {dim}"
        assert row["bounded_by"] == "definition", (
            f"{name}: a rung's dim is its identity, not a ceiling it hits")


def test_the_unbounded_carriers_are_the_ones_with_no_dimensional_wall():
    """The rows that make the global ceiling false, named explicitly so a change
    to any of them is a deliberate act."""
    unbounded = {n for n in _CARRIERS if _CAPABILITY[n]["max_dim"] is None}
    for expected in ("Mat", "Vec", "HV", "Poly", "BiPoly", "TriPoly",
                     "QPoly", "QBiPoly"):
        assert expected in unbounded, (
            f"{expected} has no dimensional wall and must publish max_dim None")
    # The registers and the CD rungs DO have one.
    for bounded in ("quaternion", "octonion", "sedenion", "CDRegister"):
        assert _CAPABILITY[bounded]["max_dim"] is not None, (
            f"{bounded} admits a bounded dim range and must publish it")


def test_cdregister_ceiling_is_the_addressing_cap_read_from_the_ssot():
    """``CDRegister`` admits any power-of-two dim up to the addressing cap, and
    that cap is TOOLING — so the register's own ceiling must track
    ``CD_MAX_DIM`` rather than being re-typed."""
    row = _CAPABILITY["CDRegister"]
    assert row["max_dim"] == CD_MAX_DIM == 256
    assert row["bounded_by"] == "tooling"


def test_the_full_verdict_map_agrees_with_introspect():
    """This module's ``FULL_VERDICT`` and ``introspect``'s ``_FULL_VERDICT``
    decide the same thing (which verdict means "holds in FULL"), so they must
    not drift — ``exceeded_by`` and ``holds_through`` are both derived from it."""
    import srmech.introspect as _intro
    import inspect
    src = inspect.getsource(_intro.describe)
    for cap_name, verdict in FULL_VERDICT.items():
        assert f'"{cap_name}": "{verdict}"' in src, (
            f"introspect._FULL_VERDICT no longer maps {cap_name} -> {verdict}; "
            f"this module's FULL_VERDICT has drifted from the derivation")


# ──────────────────────────────────────────────────────────────────────
# 4. ADR-0009 — the C host reads the same per-carrier ontology
# ──────────────────────────────────────────────────────────────────────

def test_the_c_carrier_registry_carries_the_per_carrier_ceiling():
    """Co-equal C per ADR-0009: the capability block is a public surface, so the
    compiled-in ``srmech_carrier_registry`` const table must carry the rc343
    fields too. The generated C table is byte-locked to the Python SSoT, so a
    regeneration miss shows up here rather than as a bare-C host reading an
    older ontology than the Python one."""
    from pathlib import Path
    registry = (Path(__file__).resolve().parents[2]
                / "c" / "src" / "srmech_carrier_registry.c")
    if not registry.exists():  # pragma: no cover — pure checkout
        pytest.skip("C carrier registry not present in this checkout")
    text = registry.read_text(encoding="utf-8", errors="replace")
    assert "max_dim" in text, (
        "the generated C carrier registry has no per-carrier max_dim — "
        "regenerate with c/tools/gen_carrier_registry.py")
    assert "bounded_by" in text, (
        "the generated C carrier registry has no per-carrier bounded_by — "
        "regenerate with c/tools/gen_carrier_registry.py")
