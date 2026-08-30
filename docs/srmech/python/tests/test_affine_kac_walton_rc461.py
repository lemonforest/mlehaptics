"""rc461 (`#T1183`) — the AFFINE / KAC-WALTON acceptance gate.

EVERY assertion here is HAND-WRITTEN and EXECUTED.  Nothing in this file
leans on ``tests/test_preserves_taxonomy_rc423.py``: that gate declares
eight of ten property kinds "executable" and its
``test_the_population_is_stated`` (at :431 on this tip) executes NONE of
them, so a property can be declared, classified machine-checkable, and
never run.  A declared property is not a measured one.  (Cited by NAME
rather than by line alone — the earlier ``:371-377`` form was made stale
by rc461's own commits, which added 61 lines above that function.)

EVERY PREDICATE HERE CARRIES A CONTROL THAT COMES BACK NEGATIVE, and the
control is executed rather than described.  An instrument that cannot
return otherwise is not a measurement.

THE FIVE ACCEPTANCE TESTS, and what each is worth:

  1. su(2)_k  — against a truncated Clebsch-Gordan rule DERIVED in the
     test.  The weakest of the five: a second implementation living
     test-side.  Its control is the UNtruncated rule, which differs.
  2. su(3)_1 == Z3 — the fusion ring is a group.  Control: a wrong group
     law disagrees.
  3. su(3)_2, 8 (x) 8 = 1 + 8 — checked against the SHIPPED classical op,
     so it is an equality between two shipped instruments.  Control: the
     classical answer itself, which differs.
  4. sqrt(|Z|)·S(D4_1) == character_table(centre) — the strongest,
     because BOTH sides are shipped instruments and they share no
     machinery: a 192-term Weyl sum over Z[zeta_14] against a
     finite-group character table over Z[zeta_2].  ⚠️ It is NOT a raw
     bit-for-bit equality and this gate pins that too — see G7.
  5. A_00 == 49 with every A entry +-49 — rides test 4's matrix.
     Control: su(2)_2, whose numerator is NOT rational.

Exact integers and exact Q only.  NO numpy — not in the package and not
here.  No ``abs()``: the one magnitude read is written out as the named
Class-K pin.
"""
from fractions import Fraction

import pytest

from srmech.math.groups import (character_table, cyclic_group,
                                semidirect_product, zeta_mul)
from srmech.math import weight_lattice as wl
from srmech.math.weight_lattice import (AFFINE_ALGEBRAS,
                                        AFFINE_FOLD_ALGEBRAS,
                                        affine_fusion_multiplicities,
                                        affine_modular_s_matrix, alcove_fold,
                                        integrable_weights,
                                        tensor_product_multiplicities,
                                        verlinde_fusion_multiplicities)


def _pin(value):
    """The Class-K pin-slot magnitude — never ``abs()``, in the tests as
    much as in the package."""
    return value if value >= 0 else -value


def _fuse_map(algebra, a, b, level):
    return dict(affine_fusion_multiplicities(algebra, a, b, level)
                ["constituents"])


def _verlinde_map(algebra, a, b, level):
    return dict(verlinde_fusion_multiplicities(algebra, a, b, level)
                ["constituents"])


def _primaries(algebra, level):
    return integrable_weights(algebra, level)["weights"]


# ══ G1 — the stratum is DERIVED, and the derivation cross-checks ══════

def test_g1_stratum_data_is_derived_and_cross_checked():
    """Marks, h^vee, the Cartan matrix and the centre all come off the
    simple roots.  h^vee is derived TWICE — from the marks and from
    ``|Delta| / rank`` — and the module raises if they disagree, so the
    agreement below is a real cross-check rather than one number read
    twice."""
    expected = {
        "A1": {"marks": (1,), "h_vee": 2, "centre": (2,), "rank": 1},
        "A2": {"marks": (1, 1), "h_vee": 3, "centre": (3,), "rank": 2},
        "D4": {"marks": (1, 2, 1, 1), "h_vee": 6, "centre": (2, 2),
               "rank": 4},
    }
    assert set(AFFINE_ALGEBRAS) == set(expected)
    for algebra, want in expected.items():
        payload = integrable_weights(algebra, 1)
        assert payload["marks"] == want["marks"], algebra
        assert payload["h_vee"] == want["h_vee"], algebra
        assert payload["rank"] == want["rank"], algebra
        assert payload["centre_invariant_factors"] == want["centre"], algebra
        stratum = wl._AFFINE_STRATA[algebra]
        # h^vee, the SECOND way: |Delta| / rank for a simply-laced algebra
        assert stratum["n_roots"] % want["rank"] == 0
        assert stratum["n_roots"] // want["rank"] == want["h_vee"], algebra
        # every simple root has norm 2 — the simply-laced premise
        for root in stratum["roots"]:
            assert wl._ambient_dot(root, root) == 2, (algebra, root)

    # D4's centre is the KLEIN four-group, not C4 — the whole of test 4
    # rests on this, so it is derived (Smith normal form) not recalled.
    assert wl._AFFINE_STRATA["D4"]["centre_invariant_factors"] == (2, 2)
    assert wl._smith_diagonal(wl._AFFINE_STRATA["D4"]["cartan"]) == (1, 1, 2, 2)

    # CONTROL: the Smith routine is not a constant function.
    assert wl._smith_diagonal(((2, -1), (-1, 2))) == (1, 3)      # A2
    assert wl._smith_diagonal(((2,),)) == (2,)                   # A1
    # and the divisibility REPAIR pass is live: elimination alone leaves
    # this one as (4, 6), a diagonal form that is not a Smith form.
    assert wl._smith_diagonal(((6, 0), (0, 4))) == (2, 12)
    assert wl._smith_diagonal(((4, 0), (0, 6))) == (2, 12)
    assert wl._smith_diagonal(((9, 0), (0, 6))) == (3, 18)


def test_g1_control_fold_scope_is_derived_not_transcribed():
    """``AFFINE_FOLD_ALGEBRAS`` is computed from the affine Cartan by
    :func:`_has_monovariant`, so the documented scope cannot drift from
    the proved one.  The predicate is executed here in BOTH directions."""
    assert AFFINE_FOLD_ALGEBRAS == ("A1", "A2")
    assert wl._has_monovariant(wl._AFFINE_STRATA["A1"]) is True
    assert wl._has_monovariant(wl._AFFINE_STRATA["A2"]) is True
    # the NEGATIVE half — without it this is a predicate that only says yes
    assert wl._has_monovariant(wl._AFFINE_STRATA["D4"]) is False
    assert tuple(name for name in AFFINE_ALGEBRAS
                 if wl._has_monovariant(wl._AFFINE_STRATA[name])) \
        == AFFINE_FOLD_ALGEBRAS


# ══ G2 — the termination certificate, per step and by fault injection ══

def test_g2_monovariant_law_holds_on_every_step():
    """The fold's drop is EXACTLY ``quantum·a_i`` per step.  Measured
    over a window rather than on one case, and the quantum itself is
    checked against its derivation (``2·kappa`` for A2, ``4·kappa`` for
    A1) — the A1/A2 difference is why A1 is in the suite at all: without
    it the fold could be A2-hardcoded and every other test would pass."""
    for algebra, kappa_off in (("A1", 2), ("A2", 3)):
        for level in range(0, 5):
            kappa = level + kappa_off
            want = (4 if algebra == "A1" else 2) * kappa
            rank = 1 if algebra == "A1" else 2
            probe = (0,) * rank
            assert alcove_fold(algebra, probe, level)[
                "monovariant_quantum"] == want, (algebra, level)

    # the worked case, pinned with its element
    got = alcove_fold("A2", (2, 2), 2)
    assert got["affine_labels"] == (-1, 3, 3)
    assert got["q_initial"] == 19 and got["q_final"] == 9
    assert got["monovariant_quantum"] == 10
    assert got["q_final"] - got["q_initial"] == -10 == 10 * -1
    assert got["steps"] == 1 and got["step_bound"] == 2
    assert got["folded"] == (1, 1) and got["sign"] == -1
    assert got["on_wall"] is False


def test_g2_termination_measured_over_a_window():
    """Steps never approach the pre-computed bound.  This is the
    MEASUREMENT that the certificate is not merely valid but slack."""
    worst_steps = 0
    worst_bound = 0
    folds = walls = 0
    for algebra, rank in (("A1", 1), ("A2", 2)):
        for level in range(0, 4):
            span = range(-12, 13)
            grid = ([(x,) for x in span] if rank == 1
                    else [(x, y) for x in span for y in span])
            for weight in grid:
                got = alcove_fold(algebra, weight, level)
                assert got["steps"] <= got["step_bound"]
                worst_steps = max(worst_steps, got["steps"])
                worst_bound = max(worst_bound, got["step_bound"])
                if got["on_wall"]:
                    walls += 1
                    assert got["sign"] == 0 and got["folded"] is None
                else:
                    folds += 1
                    assert got["sign"] in (1, -1)
                    assert all(v >= 0 for v in got["folded"])
    assert folds > 0 and walls > 0, (folds, walls)
    assert worst_steps < worst_bound, (worst_steps, worst_bound)


def test_g2_control_monovariant_guard_fires_under_fault_injection():
    """The per-step law is a LIVE detector, proved by corrupting the
    affine Cartan below the public surface.  Row 0 is left intact so
    :func:`_has_monovariant` still admits the stratum and the quantum
    still computes — only the STEP is wrong, which is exactly the
    regression the guard exists to catch."""
    good = wl._AFFINE_STRATA["A2"]
    broken = dict(good)
    rows = [list(r) for r in good["affine_cartan"]]
    rows[1] = [-1, 3, -1]                      # wrong diagonal at node 1
    broken["affine_cartan"] = tuple(tuple(r) for r in rows)
    assert wl._has_monovariant(broken) is True          # row 0 untouched
    with pytest.raises(ValueError) as excinfo:
        wl._fold_affine_labels("fault", broken, [3, -1, 3], 5)
    message = str(excinfo.value)
    assert "monovariant law" in message or "level law" in message, message

    # CONTROL for the control: the SAME call on the honest stratum does
    # not raise, so the raise above is the injection and not the input.
    clean = wl._fold_affine_labels("clean", good, [3, -1, 3], 5)
    assert clean["steps"] >= 1 and clean["sign"] in (1, -1)


def test_g2_control_step_bound_guard_fires_under_fault_injection():
    """The step-bound guard is a BACKSTOP: while the monovariant law
    holds it is mathematically unreachable, because ``Q >=
    kappa^2/(r+1)`` makes the bound a true upper bound.  Stated plainly
    rather than dressed up — and then PROVED firable by shrinking the
    bound at its own private seam, which is the only way an unreachable
    backstop can be shown to be wired up at all."""
    original = wl._exact_div_floor
    try:
        wl._exact_div_floor = lambda numerator, denominator: -1
        with pytest.raises(ValueError) as excinfo:
            alcove_fold("A2", (2, 2), 2)
        assert "step-bound law" in str(excinfo.value), str(excinfo.value)
    finally:
        wl._exact_div_floor = original
    # no-injection control: the same call comes back clean
    assert alcove_fold("A2", (2, 2), 2)["folded"] == (1, 1)


# ══ G3 — ACCEPTANCE TEST 1: su(2)_k ═══════════════════════════════════

def _su2_truncated_cg(p, q, level):
    """The level-truncated A1 rule, DERIVED here: the classical string
    ``|p-q| .. p+q`` in steps of 2, capped above by ``2k - p - q``."""
    low = _pin(p - q)
    high = min(p + q, 2 * level - p - q)
    return {(r,): 1 for r in range(low, high + 1, 2)} if high >= low else {}


def test_g3_acceptance_1_su2_level_k():
    checked = 0
    for level in range(1, 7):
        for p in range(level + 1):
            for q in range(level + 1):
                assert _fuse_map("A1", (p,), (q,), level) == \
                    _su2_truncated_cg(p, q, level), (level, p, q)
                checked += 1
    assert checked == sum((k + 1) ** 2 for k in range(1, 7)) == 139

    # the Ising table by name, read off the payload
    assert _fuse_map("A1", (1,), (1,), 2) == {(0,): 1, (2,): 1}   # s x s
    assert _fuse_map("A1", (2,), (2,), 2) == {(0,): 1}            # e x e
    assert _fuse_map("A1", (1,), (2,), 2) == {(1,): 1}            # s x e


def test_g3_control_untruncated_rule_disagrees():
    """CONTROL: drop the ``2k - p - q`` cap and the rule stops matching.
    Without this the acceptance test could be passing because BOTH sides
    ignore the level."""
    disagreements = 0
    for level in range(1, 5):
        for p in range(level + 1):
            for q in range(level + 1):
                low, high = _pin(p - q), p + q
                untruncated = {(r,): 1 for r in range(low, high + 1, 2)}
                if _fuse_map("A1", (p,), (q,), level) != untruncated:
                    disagreements += 1
    assert disagreements > 0, "the level cap is doing nothing"


# ══ G4 — ACCEPTANCE TEST 2: su(3)_1 == Z3 ════════════════════════════

def test_g4_acceptance_2_su3_level_1_is_z3():
    primaries = _primaries("A2", 1)
    assert primaries == ((0, 0), (0, 1), (1, 0))
    grading = {(0, 0): 0, (1, 0): 1, (0, 1): 2}
    inverse = {v: k for k, v in grading.items()}
    for a in primaries:
        for b in primaries:
            want = {inverse[(grading[a] + grading[b]) % 3]: 1}
            assert _fuse_map("A2", a, b, 1) == want, (a, b)


def test_g4_control_the_z3_identification_is_not_vacuous():
    """CONTROL, and the FIRST attempt at it was itself the lesson.

    Swapping the two non-trivial labels looked like a wrong group law
    and produced ZERO mismatches — because that swap is an AUTOMORPHISM
    of Z3, so it could never have failed.  A control that cannot come
    back negative is not a control.  Two that genuinely can:

      (a) DISPLACE THE IDENTITY.  Grade the vacuum as a non-identity and
          the match breaks, because the vacuum really is distinguished.
      (b) CHANGE THE LEVEL.  The same three labels at level 2 do NOT
          satisfy the Z3 law, so "is a group" is a level-1 FACT about
          this fusion ring and not something the primaries carry for
          free."""
    primaries = _primaries("A2", 1)

    displaced = {(0, 0): 1, (1, 0): 0, (0, 1): 2}
    inverse = {v: k for k, v in displaced.items()}
    mismatches = 0
    for a in primaries:
        for b in primaries:
            want = {inverse[(displaced[a] + displaced[b]) % 3]: 1}
            if _fuse_map("A2", a, b, 1) != want:
                mismatches += 1
    assert mismatches > 0, "displacing the identity must break the law"

    # (b) at level 2 the SAME labels stop being a group: 3 (x) 3-bar
    # gains the adjoint, so the product is no longer a single primary.
    assert _fuse_map("A2", (1, 0), (0, 1), 1) == {(0, 0): 1}
    assert _fuse_map("A2", (1, 0), (0, 1), 2) == {(0, 0): 1, (1, 1): 1}


# ══ G5 — ACCEPTANCE TEST 3: su(3)_2, 8 (x) 8 ═════════════════════════

def test_g5_acceptance_3_su3_level_2_adjoint_square():
    payload = affine_fusion_multiplicities("A2", (1, 1), (1, 1), 2)
    assert payload["route"] == "kac_walton"
    assert dict(payload["constituents"]) == {(0, 0): 1, (1, 1): 1}
    assert payload["singlet_multiplicity"] == 1
    # the CLASSICAL operand is on the payload face, from the SHIPPED op
    classical = dict(payload["classical_constituents"])
    shipped = {(p, q): m for p, q, m in
               tensor_product_multiplicities((1, 1), (1, 1))["constituents"]}
    assert classical == shipped
    assert classical == {(0, 0): 1, (0, 3): 1, (1, 1): 2, (2, 2): 1,
                         (3, 0): 1}
    # every constituent's fate, named individually
    fates = {}
    for label in classical:
        got = alcove_fold("A2", label, 2)
        fates[label] = (got["on_wall"], got["folded"], got["sign"],
                        got["steps"])
    assert fates[(0, 0)] == (False, (0, 0), 1, 0)
    assert fates[(1, 1)] == (False, (1, 1), 1, 0)
    assert fates[(0, 3)] == (True, None, 0, 0)        # wall
    assert fates[(3, 0)] == (True, None, 0, 0)        # wall
    assert fates[(2, 2)] == (False, (1, 1), -1, 1)    # folds back, MINUS
    assert payload["n_truncated"] == 3


def test_g5_control_the_classical_answer_differs():
    """CONTROL: the level-2 answer is not the classical one, and it is
    not the classical one with the non-integrable terms merely deleted
    either — the signed cancellation is doing real work."""
    affine = dict(affine_fusion_multiplicities(
        "A2", (1, 1), (1, 1), 2)["constituents"])
    classical = {(p, q): m for p, q, m in
                 tensor_product_multiplicities((1, 1), (1, 1))["constituents"]}
    assert affine != classical
    # deletion-only truncation would keep BOTH copies of the 8
    deletion_only = {label: m for label, m in classical.items()
                     if sum(label) <= 2}
    assert deletion_only == {(0, 0): 1, (1, 1): 2}
    assert affine != deletion_only, (
        "the 27 must fold back with a MINUS and cancel one 8")


# ══ G6 — ring laws ═══════════════════════════════════════════════════

def test_g6_fusion_ring_laws():
    triples = 0
    for algebra, levels in (("A1", (1, 2, 3, 4)), ("A2", (1, 2, 3))):
        for level in levels:
            primaries = _primaries(algebra, level)
            vacuum = tuple([0] * len(primaries[0]))
            for a in primaries:
                assert _fuse_map(algebra, vacuum, a, level) == {a: 1}
                for b in primaries:
                    left = _fuse_map(algebra, a, b, level)
                    assert left == _fuse_map(algebra, b, a, level)
                    assert set(left) <= set(primaries)
                    assert all(m > 0 for m in left.values())
            for a in primaries:
                for b in primaries:
                    ab = _fuse_map(algebra, a, b, level)
                    for c in primaries:
                        lhs = {}
                        for x, m in ab.items():
                            for y, n in _fuse_map(algebra, x, c,
                                                  level).items():
                                lhs[y] = lhs.get(y, 0) + m * n
                        rhs = {}
                        for x, m in _fuse_map(algebra, b, c, level).items():
                            for y, n in _fuse_map(algebra, a, x,
                                                  level).items():
                                rhs[y] = rhs.get(y, 0) + m * n
                        assert lhs == rhs, (algebra, level, a, b, c)
                        triples += 1
    # the exact count, DERIVED from |P_k| rather than eyeballed:
    # A1 k=1..4 gives 2^3+3^3+4^3+5^3, A2 k=1..3 gives 3^3+6^3+10^3.
    expected = (sum(len(_primaries("A1", k)) ** 3 for k in (1, 2, 3, 4))
                + sum(len(_primaries("A2", k)) ** 3 for k in (1, 2, 3)))
    assert expected == 1467, expected
    assert triples == expected, (triples, expected)


def test_g6_control_classical_limit_and_live_truncation():
    """Two controls in one, pointing opposite ways.  At HIGH level the
    affine answer must reproduce the SHIPPED classical op exactly — if
    it did not, the fold would be corrupting weights that need no fold.
    At LOW level it must DIFFER on a real number of pairs — if it did
    not, the truncation would be a no-op and every level test above
    would be vacuous."""
    same = 0
    for a in _primaries("A2", 3):
        for b in _primaries("A2", 3):
            classical = {(p, q): m for p, q, m in
                         tensor_product_multiplicities(a, b)["constituents"]}
            assert _fuse_map("A2", a, b, 40) == classical, (a, b)
            same += 1
    assert same == 100

    differ = identical = 0
    for level in (1, 2, 3):
        for a in _primaries("A2", level):
            for b in _primaries("A2", level):
                classical = {(p, q): m for p, q, m in
                             tensor_product_multiplicities(a, b)
                             ["constituents"]}
                if _fuse_map("A2", a, b, level) == classical:
                    identical += 1
                else:
                    differ += 1
    assert differ == 90 and identical == 55, (differ, identical)


# ══ G7 — ACCEPTANCE TEST 4: the D4 S-matrix vs the centre's table ═════

def _centre_cayley_table(invariant_factors):
    """The Cayley table of ``prod Z_d`` from SHIPPED group constructors —
    a trivial action makes ``semidirect_product`` the direct product."""
    table = cyclic_group(invariant_factors[0])["cayley_table"]
    for order in invariant_factors[1:]:
        other = cyclic_group(order)["cayley_table"]
        trivial = [list(range(len(table))) for _ in range(len(other))]
        table = semidirect_product(table, other, trivial)["cayley_table"]
    return table


def test_g7_acceptance_4_d4_level_1_s_matrix_is_the_centre_table():
    """THE STRONGEST TEST IN THE SUITE: two SHIPPED instruments that
    share no machinery, put side by side.

    ⚠️ It is NOT a raw bit-for-bit equality, and this gate pins both
    halves so the false half cannot creep back into prose.
    ``character_table`` SORTS its rows by ``(degree, lexicographic)`` and
    says in its own docstring to "locate rows by CONTENT, never by
    index"; this op orders its rows by PRIMARY.  Raw, they differ.  In
    the same documented order they are bit-for-bit identical, and the
    permutation between them is unique."""
    s = affine_modular_s_matrix("D4", 1)
    assert s["weyl_order"] == 192
    assert s["is_rational_numerator"] is True
    numerator = s["rational_numerator"]

    a00 = numerator[0][0]
    doubled = tuple(tuple(x // a00 for x in row) for row in numerator)

    centre = s["centre_invariant_factors"]
    assert centre == (2, 2)
    table = _centre_cayley_table(centre)
    payload = character_table(table)
    assert payload["exponent"] == 2 and payload["phi_e"] == (1, 1)
    assert payload["degrees"] == [1, 1, 1, 1]
    rows = tuple(tuple(cell[0] for cell in row) for row in payload["table"])

    # ── the FALSE half, pinned ────────────────────────────────────────
    assert doubled != rows, (
        "raw bit-for-bit equality is measurably FALSE and must stay pinned")

    # ── the TRUE half ─────────────────────────────────────────────────
    assert tuple(sorted(doubled)) == tuple(sorted(rows))

    # the permutation is a genuine one and it is UNIQUE (all rows differ)
    assert len(set(doubled)) == 4 and len(set(rows)) == 4
    assert tuple(rows.index(row) for row in doubled) == (3, 2, 1, 0)

    # the normalisation ties the two sides: sqrt(|Z|)·S is the +-1 matrix
    centre_order = 1
    for factor in centre:
        centre_order *= factor
    assert centre_order == 4
    assert a00 * a00 * centre_order == s["scale_squared_denominator"]

    # and S itself is symmetric where the sorted character table is not,
    # which is WHY the row gauge is real rather than a nuisance
    assert all(doubled[i][j] == doubled[j][i] for i in range(4)
               for j in range(4))
    assert any(rows[i][j] != rows[j][i] for i in range(4) for j in range(4))


def test_g7_control_the_other_order_four_group_fails():
    """CONTROL: C4 is the only other group of order 4, and it does NOT
    match — its character table is not even a rational matrix (exponent
    4, so ``Phi_4 = x^2 + 1`` and the values need ``i``).  Without this
    the test would only show "S looks like SOME order-4 character
    table"."""
    c4 = character_table(cyclic_group(4)["cayley_table"])
    assert c4["exponent"] == 4 and c4["phi_e"] == (1, 0, 1)
    rational = all(all(coefficient == 0 for coefficient in cell[1:])
                   for row in c4["table"] for cell in row)
    assert rational is False, "C4 must NOT be a +-1 rational table"

    # and the V4 side IS rational, so the two are genuinely separated
    v4 = character_table(_centre_cayley_table((2, 2)))
    assert all(len(cell) == 1 for row in v4["table"] for cell in row)


# ══ G8 — ACCEPTANCE TEST 5: the ring and the +-49 ════════════════════

def test_g8_acceptance_5_entries_are_pm_49_in_z_zeta_14():
    """The ring is ``Z[zeta_14]`` — MEASURED by gcd-reducing the
    exponents, not assumed.  It is neither ``zeta_28`` (the raw scaling)
    nor ``zeta_7`` (a reading of ``kappa`` alone): the D4 spinor weights
    are half-integral, and half-integer pairings need the doubled
    order."""
    s = affine_modular_s_matrix("D4", 1)
    assert s["kappa"] == 7
    assert s["zeta_order"] == 14
    assert s["phi_e"] == (1, -1, 1, -1, 1, -1, 1)      # Phi_14
    assert len(s["phi_e"]) - 1 == 6                     # phi(14) == 6

    numerator = s["rational_numerator"]
    a00 = numerator[0][0]
    assert a00 == 49
    entries = {value for row in numerator for value in row}
    assert entries == {49, -49}
    assert all(value in (a00, -a00) for row in numerator for value in row)
    assert s["scale_squared_denominator"] == 9604 == 98 * 98

    # every full zeta-vector really is rational: higher coordinates zero
    for row in s["numerator"]:
        for cell in row:
            assert len(cell) == 6
            assert all(coefficient == 0 for coefficient in cell[1:])


def test_g8_control_su2_level_2_numerator_is_not_rational():
    """CONTROL: ``is_rational_numerator`` is not a constant True.  su(2)_2
    lives in ``Z[zeta_8]`` and does not collapse to ``Z``."""
    s = affine_modular_s_matrix("A1", 2)
    assert s["zeta_order"] == 8
    assert s["phi_e"] == (1, 0, 0, 0, 1)               # Phi_8
    assert s["is_rational_numerator"] is False
    assert s["rational_numerator"] is None
    assert any(any(coefficient != 0 for coefficient in cell[1:])
               for row in s["numerator"] for cell in row)


# ══ G9 — the normalisation is DERIVED from unitarity ═════════════════

def _zeta_conj(vector, order, phi):
    accumulator = [0] * order
    for power, coefficient in enumerate(vector):
        accumulator[(-power) % order] += coefficient
    return zeta_mul(accumulator, (1,), phi)


def _gram(numerator, order, phi):
    """``A·A^dagger`` as a table of zeta-vectors."""
    size = len(numerator)
    width = len(phi) - 1
    out = []
    for i in range(size):
        row = []
        for j in range(size):
            accumulator = tuple([0] * width)
            for t in range(size):
                product = zeta_mul(numerator[i][t],
                                   _zeta_conj(numerator[j][t], order, phi),
                                   phi)
                accumulator = tuple(x + y
                                    for x, y in zip(accumulator, product))
            row.append(accumulator)
        out.append(row)
    return out


def test_g9_normalisation_is_read_off_unitarity_not_substituted():
    """``|c|^2 = 1/n`` with ``n`` READ from ``A·A^dagger = n·I``.  That
    it also equals ``kappa^rank·|P/Q|`` is then a CROSS-CHECK between two
    independent derivations rather than a formula substituted in."""
    for algebra, level in (("A1", 1), ("A1", 2), ("A2", 1), ("A2", 2),
                           ("D4", 1)):
        s = affine_modular_s_matrix(algebra, level)
        order, phi = s["zeta_order"], s["phi_e"]
        gram = _gram(s["numerator"], order, phi)
        size = len(gram)
        scale = s["scale_squared_denominator"]
        for i in range(size):
            for j in range(size):
                if i == j:
                    assert gram[i][j][0] == scale, (algebra, level, i)
                    assert all(c == 0 for c in gram[i][j][1:])
                else:
                    assert all(c == 0 for c in gram[i][j]), (algebra, level,
                                                             i, j)
        # the independent formula, as a cross-check
        centre_order = 1
        for factor in s["centre_invariant_factors"]:
            centre_order *= factor
        rank = integrable_weights(algebra, level)["rank"]
        assert scale == s["kappa"] ** rank * centre_order, (algebra, level)


def test_g9_control_a_perturbed_numerator_fails_unitarity():
    """CONTROL: flip the sign of ONE entry and ``A·A^dagger`` stops being
    ``n·I``.  Without this, the unitarity check could be passing on any
    matrix at all."""
    s = affine_modular_s_matrix("D4", 1)
    order, phi = s["zeta_order"], s["phi_e"]
    rows = [[tuple(cell) for cell in row] for row in s["numerator"]]
    rows[1][2] = tuple(-c for c in rows[1][2])          # one entry flipped
    gram = _gram(rows, order, phi)
    offenders = 0
    for i in range(len(gram)):
        for j in range(len(gram)):
            expected = s["scale_squared_denominator"] if i == j else 0
            if gram[i][j][0] != expected or any(c != 0 for c in gram[i][j][1:]):
                offenders += 1
    assert offenders > 0, "the unitarity check cannot return otherwise"


# ══ G10 — the co-equal dual construction ═════════════════════════════

def test_g10_verlinde_agrees_with_kac_walton():
    """Two instruments sharing NO machinery: an iterative integer
    reflection with a termination certificate, against a finite Weyl
    exponential sum followed by division in a number field.  A co-equal
    dual construction is a consistency oracle — a disagreement here
    would be the finding."""
    pairs = 0
    for algebra, levels in (("A1", (1, 2, 3, 4)), ("A2", (1, 2, 3))):
        for level in levels:
            for a in _primaries(algebra, level):
                for b in _primaries(algebra, level):
                    assert _verlinde_map(algebra, a, b, level) == \
                        _fuse_map(algebra, a, b, level), (algebra, level, a, b)
                    pairs += 1
    assert pairs == 199, pairs


def test_g10_control_verlinde_is_not_echoing_the_fold():
    """CONTROL: the Verlinde route reaches D4, where the fold RAISES.
    If it were quietly delegating to the fold it could not."""
    got = _verlinde_map("D4", (0, 0, 0, 1), (0, 0, 1, 0), 1)
    assert got == {(1, 0, 0, 0): 1}
    with pytest.raises(ValueError):
        affine_fusion_multiplicities("D4", (0, 0, 0, 1), (0, 0, 1, 0), 1)
    # and its payload carries fields the fold route does not have
    payload = verlinde_fusion_multiplicities("D4", (0, 0, 0, 1),
                                             (0, 0, 1, 0), 1)
    assert payload["route"] == "verlinde"
    assert payload["zeta_order"] == 14
    assert "classical_constituents" not in payload


def test_g10_d4_level_1_is_the_klein_four_group_ring():
    """An INDEPENDENT confirmation that ``P/Q`` is V4 and not C4, by a
    route that never looks at the Smith normal form: every product is a
    single primary at multiplicity one, and every primary is its own
    inverse — the defining property C4 fails."""
    primaries = _primaries("D4", 1)
    assert len(primaries) == 4
    vacuum = (0, 0, 0, 0)
    for a in primaries:
        for b in primaries:
            got = _verlinde_map("D4", a, b, 1)
            assert len(got) == 1 and list(got.values()) == [1], (a, b)
        assert _verlinde_map("D4", a, a, 1) == {vacuum: 1}, a
    # CONTROL: in C4 exactly two elements are self-inverse, not four —
    # so "every element self-inverse" genuinely separates V4 from C4.
    c4 = cyclic_group(4)["cayley_table"]
    self_inverse = sum(1 for x in range(4) if c4[x][x] == 0)
    assert self_inverse == 2


# ══ G11 — input-domain guards ════════════════════════════════════════

def test_g11_non_integrable_operands_raise_and_never_answer_silently():
    """The guard that exists because the downstream backstop was NOT
    sufficient: measured before it, two of four non-integrable pairs
    returned an empty constituent set SILENTLY."""
    cases = (((2, 2), (2, 1)), ((3, 0), (0, 0)), ((0, 3), (1, 1)),
             ((2, 2), (2, 2)), ((1, 1), (1, 1)))
    for a, b in cases:
        with pytest.raises(ValueError) as excinfo:
            affine_fusion_multiplicities("A2", a, b, 1)
        assert "integrability law" in str(excinfo.value) or \
            "dominance law" in str(excinfo.value), str(excinfo.value)
        with pytest.raises(ValueError):
            verlinde_fusion_multiplicities("A2", a, b, 1)
    # CONTROL: legal operands at the SAME level do not raise
    assert _fuse_map("A2", (1, 0), (0, 1), 1) == {(0, 0): 1}


def test_g11_scope_and_shape_guards():
    with pytest.raises(ValueError) as excinfo:
        alcove_fold("D4", (0, 0, 0, 1), 1)
    assert "termination-scope law" in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        affine_fusion_multiplicities("D4", (0, 0, 0, 1), (0, 0, 1, 0), 1)
    assert "termination-scope law" in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        integrable_weights("E8", 1)
    assert "algebra-scope law" in str(excinfo.value)
    with pytest.raises(ValueError):
        integrable_weights(2, 1)                       # not a str
    with pytest.raises(ValueError):
        integrable_weights("A2", -1)                   # negative level
    with pytest.raises(ValueError):
        integrable_weights("A2", True)                 # bool on the int lane
    with pytest.raises(ValueError):
        alcove_fold("A2", (1,), 2)                     # wrong rank
    with pytest.raises(ValueError):
        alcove_fold("A2", (1, True), 2)                # bool on the int lane
    # CONTROL: each of those shapes has a legal neighbour that passes
    assert integrable_weights("A2", 0)["n_weights"] == 1
    assert alcove_fold("A2", (1, 1), 2)["folded"] == (1, 1)


# ══ G12 — the carrier, and the zeta ruling ═══════════════════════════

def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_g12_no_float_reaches_any_payload():
    payloads = [
        integrable_weights("D4", 1),
        alcove_fold("A2", (2, 2), 2),
        affine_fusion_multiplicities("A2", (1, 1), (1, 1), 2),
        affine_modular_s_matrix("D4", 1),
        affine_modular_s_matrix("A1", 2),
        verlinde_fusion_multiplicities("D4", (0, 0, 0, 1), (0, 0, 1, 0), 1),
    ]
    for payload in payloads:
        for item in _walk(payload):
            assert not isinstance(item, float), (payload.get("algebra"), item)
            assert not isinstance(item, Fraction), (payload.get("algebra"),
                                                    item)


def test_g12_zeta_values_ride_the_shipped_character_table_dialect():
    """THE ZETA RULING, executed rather than asserted.  These ops mint
    the ``Z[zeta_e]`` INTEGER COORDINATE VECTOR form that
    ``character_table`` already produces and ``zeta_mul`` already
    consumes — a dialect with a live producer and a live reader today.
    They never mint a REP payload, which is the object the deferred
    ``Q(zeta_e)`` widening is about.  So the widening has no producer
    here and stays where it was scheduled."""
    s = affine_modular_s_matrix("D4", 1)
    phi = s["phi_e"]
    assert isinstance(phi, tuple) and all(isinstance(c, int) for c in phi)
    assert phi[-1] == 1 and len(phi) >= 2               # monic modulus

    # the SHIPPED reader accepts our vectors verbatim, in both directions
    left = s["numerator"][1][2]
    right = s["numerator"][2][1]
    product = zeta_mul(left, right, phi)
    assert isinstance(product, tuple)
    assert len(product) == len(phi) - 1
    assert all(isinstance(c, int) for c in product)

    # and character_table's own cells ride the identical shape
    cell = character_table(cyclic_group(3)["cayley_table"])["table"][1][1]
    assert all(isinstance(c, int) for c in cell)

    # NO rep-payload key appears anywhere in the new payloads: the rep
    # dialect is a different object and these ops do not speak it.
    rep_keys = {"kind", "matrices", "degree", "field"}
    for payload in (s,
                    integrable_weights("D4", 1),
                    alcove_fold("A2", (2, 2), 2),
                    affine_fusion_multiplicities("A2", (1, 1), (1, 1), 2),
                    verlinde_fusion_multiplicities("D4", (0, 0, 0, 1),
                                                   (0, 0, 1, 0), 1)):
        assert rep_keys.isdisjoint(payload.keys()), sorted(payload)


# ══ G13 — the registry ═══════════════════════════════════════════════

def test_g13_the_five_ops_are_registered_with_resolvable_composes():
    from srmech.introspect.tool_schema import get_tool_schema

    schema = get_tool_schema()
    names = {tool.name for tool in schema.tools}
    new = {
        "srmech.math.weight_lattice.integrable_weights",
        "srmech.math.weight_lattice.alcove_fold",
        "srmech.math.weight_lattice.affine_fusion_multiplicities",
        "srmech.math.weight_lattice.affine_modular_s_matrix",
        "srmech.math.weight_lattice.verlinde_fusion_multiplicities",
    }
    assert new <= names, sorted(new - names)
    for tool in schema.tools:
        if tool.name in new:
            for target in (tool.composes or ()):
                assert target in names, (tool.name, target)
            assert tool.category == "weight_lattice"
            assert tool.smoke_test_hint, tool.name

    # the name COLLISION this rc had to resolve: the finite-group op of
    # the near-same name is a DIFFERENT object and both still ship.
    assert "srmech.math.groups.fusion_multiplicities" in names
    assert "srmech.math.weight_lattice.fusion_multiplicities" not in names


# ── G12 — the TERMINATION-CERTIFICATE numbers the docstring MEASURES ──────

def test_g12_the_measured_step_and_bound_extremes_are_pinned():
    """rc461 (`#T1183`) — :func:`alcove_fold`'s docstring reports a
    MEASUREMENT over ``[-30,30]^rank`` at ``k = 0..8``. Through this rc it
    reported *"bounds up to 962"*, a value the shipped op NEVER PRODUCES
    anywhere in that domain — the true ceiling is 901.

    It survived because ``test_g2_termination_measured_over_a_window``
    asserts only ``worst_steps < worst_bound``, a strict inequality that
    pins no VALUE and so cannot see a wrong one. This gate pins both
    extremes and the witness that attains them, over exactly the domain
    the prose names, so the sentence and the code cannot drift apart
    again.
    """
    observed_bounds = set()
    worst_steps = (-1, None)
    worst_bound = (-1, None)
    folds = walls = 0
    for algebra, rank in (("A1", 1), ("A2", 2)):
        for level in range(0, 9):
            span = range(-30, 31)
            grid = ([(x,) for x in span] if rank == 1
                    else [(x, y) for x in span for y in span])
            for weight in grid:
                got = alcove_fold(algebra, weight, level)
                assert got["steps"] <= got["step_bound"]
                observed_bounds.add(got["step_bound"])
                if got["steps"] > worst_steps[0]:
                    worst_steps = (got["steps"], (algebra, weight, level))
                if got["step_bound"] > worst_bound[0]:
                    worst_bound = (got["step_bound"], (algebra, weight, level))
                walls, folds = ((walls + 1, folds) if got["on_wall"]
                                else (walls, folds + 1))

    assert folds + walls == 549 + 33489 == 34038
    assert worst_steps[0] == 40, worst_steps
    assert worst_bound[0] == 901, worst_bound
    # Both extremes are attained at the SAME corner — the docstring says so.
    assert worst_steps[1] == ("A2", (-30, -30), 0), worst_steps
    assert worst_bound[1] == ("A2", (-30, -30), 0), worst_bound
    # The number the prose used to carry is not merely un-hit, it is ABSENT.
    assert 962 not in observed_bounds
    # CONTROL: the collector is live — it saw many distinct bounds, and the
    # one it pins IS in the set it collected.
    assert len(observed_bounds) > 100, len(observed_bounds)
    assert 901 in observed_bounds


def test_g12_control_the_pinned_witness_is_reproducible_alone():
    """The extremal witness, read directly — so a failure in the sweep
    above is localisable without re-running 34,038 folds."""
    got = alcove_fold("A2", (-30, -30), 0)
    assert got["steps"] == 40
    assert got["step_bound"] == 901
    assert got["steps"] < got["step_bound"]


# ── G13 — the WORKED EXAMPLE's causation, per constituent ─────────────────

def test_g13_two_mechanisms_carry_8x8_down_to_the_level_2_answer():
    """rc461 (`#T1183`) — the docstring credited *"that single step and
    that single sign"* with turning ``1+8+8+10+10bar+27`` into ``1+8``.
    MEASURED per constituent, TWO different mechanisms are load-bearing:
    the ``10`` and ``10-bar`` are deleted by the WALL test having taken no
    step and carrying no sign, and the single signed step acts on ``27``
    alone. The prose is now corrected against this gate.
    """
    classical = tensor_product_multiplicities((1, 1), (1, 1))["constituents"]
    assert classical == ((0, 0, 1), (1, 1, 2), (0, 3, 1), (3, 0, 1), (2, 2, 1))

    walled, stepped, deletion_only = [], [], {}
    for entry in classical:
        weight, mult = tuple(entry[:-1]), entry[-1]
        got = alcove_fold("A2", weight, 2)
        if got["on_wall"]:
            walled.append(weight)
            assert got["sign"] == 0 and got["steps"] == 0, weight
        else:
            deletion_only[weight] = deletion_only.get(weight, 0) + mult
            if got["steps"] > 0:
                stepped.append((weight, got["folded"], got["sign"]))

    # The 10 and the 10-bar die at the WALL — no step, no sign.
    assert sorted(walled) == [(0, 3), (3, 0)]
    # Exactly ONE constituent takes a signed step, and it is the 27.
    assert stepped == [((2, 2), (1, 1), -1)], stepped
    # CONTROL: deleting the walls and stopping there is NOT the answer.
    assert deletion_only == {(0, 0): 1, (1, 1): 2, (2, 2): 1}
    answer = affine_fusion_multiplicities("A2", (1, 1), (1, 1), 2)
    assert answer["constituents"] == (((0, 0), 1), ((1, 1), 1))
    assert dict((w, m) for w, m in answer["constituents"]) != deletion_only


# ── G14 — the CONTENT ADDRESSES the five affine ops ship ──────────────────

def test_g14_affine_content_addresses_are_stable_and_distinguishing():
    """rc461 (`#T1183`) — the affine stratum was enrolled in the REGISTRY
    gate next door but NOT in the content-address gate 22 lines above it
    (``tests/test_weight_lattice_rc460.py``), so every Class-A digest these
    five ops ship could be replaced with a constant and the suite stayed
    green. This is the missing peer.

    ⚠️ ``fusion_sha256`` addresses the ANSWER — the constituent list — and
    not the payload, by design and in line with the rc460 classical op.
    MEASURED while writing this gate: ``8 (x) 8`` and ``3 (x) 3bar`` at
    level 2 BOTH give ``1 + 8``, so they share a digest, correctly. So
    "distinguishing" here means *different answers get different
    addresses*, and the operands below are chosen to have genuinely
    different answers rather than assumed to.
    """
    # weights_sha256 — varies with (algebra, level).
    assert (integrable_weights("A2", 1)["weights_sha256"]
            == integrable_weights("A2", 1)["weights_sha256"])
    assert (integrable_weights("A2", 1)["weights_sha256"]
            != integrable_weights("A2", 2)["weights_sha256"])
    assert (integrable_weights("A1", 1)["weights_sha256"]
            != integrable_weights("A2", 1)["weights_sha256"])

    # fusion_sha256 — varies with the ANSWER.
    base = affine_fusion_multiplicities("A2", (1, 1), (1, 1), 2)
    other = affine_fusion_multiplicities("A2", (1, 0), (1, 0), 2)
    assert base["fusion_sha256"] == \
        affine_fusion_multiplicities("A2", (1, 1), (1, 1), 2)["fusion_sha256"]
    assert base["constituents"] != other["constituents"], "operands collide"
    assert base["fusion_sha256"] != other["fusion_sha256"]
    # …and EQUAL answers share an address, which is the contract, not a bug:
    same = affine_fusion_multiplicities("A2", (1, 0), (0, 1), 2)
    assert same["constituents"] == base["constituents"]     # both are 1 + 8
    assert same["fusion_sha256"] == base["fusion_sha256"]

    # s_sha256 — varies with (algebra, level).
    s_a2_1 = affine_modular_s_matrix("A2", 1)["s_sha256"]
    assert s_a2_1 == affine_modular_s_matrix("A2", 1)["s_sha256"]
    assert s_a2_1 != affine_modular_s_matrix("A2", 2)["s_sha256"]
    assert s_a2_1 != affine_modular_s_matrix("A1", 1)["s_sha256"]

    # procedure_sha256 — a per-STRATUM address: identical ACROSS the ops of
    # one algebra (they run the same procedure) and different BETWEEN them.
    per_stratum = {
        "A2": {integrable_weights("A2", 1)["procedure_sha256"],
               alcove_fold("A2", (1, 1), 2)["procedure_sha256"],
               affine_modular_s_matrix("A2", 1)["procedure_sha256"],
               affine_fusion_multiplicities("A2", (0, 0), (0, 0),
                                            1)["procedure_sha256"]},
        "A1": {integrable_weights("A1", 1)["procedure_sha256"],
               alcove_fold("A1", (1,), 2)["procedure_sha256"],
               affine_modular_s_matrix("A1", 1)["procedure_sha256"]},
    }
    assert len(per_stratum["A2"]) == 1, per_stratum["A2"]
    assert len(per_stratum["A1"]) == 1, per_stratum["A1"]
    assert per_stratum["A1"] != per_stratum["A2"]

    for digest in (s_a2_1, base["fusion_sha256"],
                   next(iter(per_stratum["A2"]))):
        assert len(digest) == 64 and int(digest, 16) >= 0


# ── G15 — the S-matrix ROW LABELS really label the rows ───────────────────

def test_g15_primaries_index_the_rows_they_label():
    """``primaries[i]`` must name the primary that row ``i`` belongs to.
    Nothing re-derived that correspondence and nothing checked it — the
    tuple could be REVERSED and the suite stayed green, because the one
    shipped consumer (:func:`verlinde_fusion_multiplicities`) re-reads an
    internal dict rather than the public field.

    Re-derived here from the SHIPPED weight list, which is an independent
    route to the same ordering.
    """
    for algebra, level in (("A1", 3), ("A2", 2), ("D4", 1)):
        got = affine_modular_s_matrix(algebra, level)
        primaries = got["primaries"]
        rows = got["numerator"]
        assert len(primaries) == len(rows) == got["n_primaries"]
        assert len(set(primaries)) == len(primaries), algebra

        # INDEPENDENT ROUTE: the shipped integrable-weight list, same order.
        weights = integrable_weights(algebra, level)["weights"]
        assert tuple(primaries) == tuple(weights), (algebra, level)

        # The vacuum is index 0 and owns row 0.
        vacuum = tuple([0] * len(primaries[0]))
        assert tuple(primaries[0]) == vacuum, (algebra, primaries[0])

        # S is SYMMETRIC, so a row permutation that broke the labelling
        # would also break this — asserted as the structural cross-check.
        for i in range(len(rows)):
            for j in range(len(rows)):
                assert rows[i][j] == rows[j][i], (algebra, i, j)

    # CONTROL: the equality above is not vacuous — a REVERSED label tuple
    # genuinely disagrees with the shipped one, so the assertion has teeth.
    got = affine_modular_s_matrix("A2", 2)
    assert tuple(reversed(got["primaries"])) != tuple(got["primaries"])
