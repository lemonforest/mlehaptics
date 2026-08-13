"""rc430 (`#T1127`) — a declared FRAME must be one a perturbation can CONTRADICT.

THE FALSE GREEN THIS EXISTS TO CATCH
------------------------------------
**A declared classification that nothing verifies.** rc339 shipped
``bounded_by = "associativity"`` on an op DEFINED as the associativity
condition — no carrier row could falsify it — and rc343 removed it. rc428
found ``row.schema.json`` declaring ``additionalProperties: false`` with
nothing validating against it, and three violating fields shipped green.

``ToolEntry.frame_scope`` is a claim of exactly that kind — "this op's frame is
welded in" — so it needs exactly that kind of rule. This module IS the rule,
and it is executable rather than documentary. It copies the shape of
``tests/test_op_lane_rc347.py`` section for section, because that field is the
one precedent in this tree that verifies its declaration instead of storing it.

WHAT IS PERTURBED
-----------------
The frame COORDINATE is translated and the output is watched::

    parametric   sweeping the named parameter MOVES the output; f(x + n) ==
                 f(x) for every swept n; and NO single constant period
                 survives the sweep.
    fixed        a least constant m > 1 with f(x + m) == f(x) across a dense
                 range, no parameter supplies m, and the op is not constant
                 along the coordinate.

SWEPT, NEVER SAMPLED — MEASURED, NOT ASSERTED
---------------------------------------------
The first draft of the instrument sampled six offsets and classified
``srmech.math.primes.is_prime`` as ``fixed`` with **period 6**. It is not
periodic; six draws agreed by chance. Had it shipped, this gate would have
been protecting a false declaration on a real op — the very defect the rc
exists to remove, reproduced by the tool built to remove it. §0 below
re-derives ``is_prime -> no period`` on every run, so that repair cannot
silently regress.

**Section 0 is not preamble.** Without it every verdict below is an artefact of
the instrument rather than a fact about the ops.

THE OPT-IN TRAP, AND WHY THIS FIELD DOES NOT FALL INTO IT
----------------------------------------------------------
``reads_lane`` reached **9 of 655 ops (1.4%) in 82 rcs**. A field nothing
computes the roster FOR is an ``__all__``-shaped escape hatch: the surfaces
that most need it are the least likely to opt in. So §4 does not ask which ops
declared. It DERIVES the admissible set behaviourally and asserts
``declared == admissible`` in BOTH directions. A declaration cannot escape by
staying silent.

No float, no numpy, no ``fractions``, no ``abs()`` — a sign is a Class-K
pin-slot read composed with Class C.

Instrument: ``tools/frame_probe.py``. Census + NDJSON:
``docs/srmech/notes/_frame_scope_census_rc430.py``.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT / "tools"))

import example_args as ea      # noqa: E402
import frame_probe as fp       # noqa: E402

from srmech.cascade import cyclic_mod_add  # noqa: E402
from srmech.introspect import describe  # noqa: E402
from srmech.introspect.tool_schema import (  # noqa: E402
    FRAME_AXES,
    FRAME_SCOPES,
    ToolEntry,
    ToolSchemaValidationError,
    get_tool_schema,
    warmup_all,
)
from srmech.math.cyclic import mod_mul  # noqa: E402
from srmech.math.primes import is_prime  # noqa: E402

#: The REVIEWED roster. §4 derives the admissible set and compares against the
#: live declarations, which is the real gate; this pins the set a human
#: actually looked at, for the reason rc412 exists — a strict-zero check over a
#: SHRINKING set is vacuously true, so a sweep alone cannot see a declaration
#: disappear. Measured at rc430 over the harvested argument corpus.
REVIEWED_ROSTER: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "srmech.biology.genome.modulator_constraint_satisfies": ("fixed", ("modulus",)),
    "srmech.cascade.cyclic_gcd": ("parametric", ("modulus",)),
    "srmech.cascade.cyclic_mod_add": ("parametric", ("modulus",)),
    "srmech.cascade.cyclic_mod_mul": ("parametric", ("modulus",)),
    "srmech.cascade.cyclic_mod_mul_wide": ("parametric", ("modulus",)),
    "srmech.cascade.cyclic_mod_pow": ("parametric", ("modulus",)),
    "srmech.cascade.odft_summand": ("parametric", ("modulus",)),
    "srmech.cascade.qdft_summand": ("parametric", ("modulus",)),
    "srmech.math.covering.center_parity": ("fixed", ("modulus",)),
    "srmech.math.covering.lift_fibre": ("parametric", ("modulus",)),
    # Added at the rc430 REPAIR, not at rc430: the probe's degeneracy screen
    # was foreclosing the parametric sweep whenever the base arguments made the
    # op constant along the swept coordinate, so `gcd` measured NOT_ADMISSIBLE
    # and the both-directions gate passed against a census short by one. Its
    # own delegating alias `srmech.cascade.cyclic_gcd` (below) had declared
    # parametric/modulus since rc430 — the primitive and the alias disagreed.
    "srmech.math.cyclic.gcd": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_add": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_mul": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_mul_arrow": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_mul_wide": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_pow": ("parametric", ("modulus",)),
    "srmech.math.cyclic.three_cycle": ("fixed", ("modulus",)),
    "srmech.math.rational.rational_reconstruct": ("parametric", ("modulus",)),
    "srmech.music.interval_vector": ("fixed", ("modulus",)),
    "srmech.music.normal_order": ("fixed", ("modulus",)),
    "srmech.music.prime_form": ("fixed", ("modulus",)),
}

#: Ops the driver cannot reach, by class, held DOWN-ONLY. An undrivable op is
#: not a pass — it is an unadjudicated one, and a ceiling is what stops the
#: unadjudicated class from quietly becoming the whole registry.
CEIL_FRAME_UNADJUDICATED = {
    "NO_ARG": 274,          # no harvested argument binding at all
    "NO_INT_INPUT": 152,    # nothing translatable along a frame axis
    "BASE_RAISES": 56,      # harvested binding does not execute
    "SLOW_SKIP": 15,        # measured-slow, skipped BY NAME with a number
    # rc430 repair (`#T1127`): ops whose parameter carries a documented domain
    # contract the sweep cannot honour (the three GF(p) ops need PRIME p). The
    # native peer asserts it and CI took SIGABRT; the pure body silently
    # computes a wrong answer instead, which is why no local run saw it.
    # Drains when the rc431 per-parameter domain field lands and the probe can
    # READ the contract instead of being told it by name.
    "CONTRACT_SKIP": 3,
}

_CENSUS_CACHE: Dict[str, Any] = {}


def _census() -> Dict[str, Dict[str, Any]]:
    """Classify every registered op once, from the harvested ledger."""
    if not _CENSUS_CACHE:
        warmup_all()
        rows = ea.load_ledger()
        for entry in get_tool_schema().tools:
            _CENSUS_CACHE[entry.name] = fp.probe_from_ledger(entry.name, rows)
    return _CENSUS_CACHE


def _declared() -> Dict[str, ToolEntry]:
    warmup_all()
    return {e.name: e for e in get_tool_schema().tools if e.frame_scope is not None}


# ══════════════════════════════════════════════════════════════════════
# 0. INSTRUMENT PRECONDITION — without this, nothing below is evidence
# ══════════════════════════════════════════════════════════════════════

def _leak_a(x: int, y: int) -> int:
    """Modulus 12 WELDED IN. Must classify `fixed`, period 12."""
    return cyclic_mod_add(x, y, 12)


def _leak_b(x: int, y: int, n: int) -> int:
    """Modulus parametric, GENERATOR 7 welded in — the rc426 F12b blind spot.

    F12b files this CLEAN: it takes a modulus, is total, yields many distinct
    answers as ``n`` moves, and contains no literal 12. The generator clause is
    the whole reason this control exists.
    """
    return mod_mul(7, cyclic_mod_add(x, y, n), n)


def _clean(x: int, y: int, n: int, g: int) -> int:
    """Nothing welded in — both the modulus and the generator are inputs."""
    return mod_mul(g, cyclic_mod_add(x, y, n), n)


def test_the_period_finder_rejects_a_coincidence() -> None:
    """``is_prime`` is not periodic, and a six-point sample said it was.

    This is the known-answer probe. It is asserted on every run because the
    repair it protects — dense sweep plus a confirmation floor — is the single
    thing standing between this gate and blessing a false declaration.
    """
    vals = [fp.okey(is_prime(101 + d)) for d in range(fp.R)]
    m, _ = fp.least_period(vals)
    assert m is None, (
        f"is_prime(101+d) reports least period {m}. It is not periodic; a "
        f"short sample said 6 at rc430. The dense sweep or the "
        f"MIN_CONFIRMATIONS floor has regressed, and every `fixed` verdict "
        f"below is now suspect.")

    # and the sweep must still be able to FIND a period, or it is rejecting
    # everything and the check above passes for the wrong reason.
    good = [fp.okey(cyclic_mod_add(x, 3, 12)) for x in range(fp.R)]
    m2, conf = fp.least_period(good)
    assert (m2, conf > 24) == (12, True), (m2, conf)


def test_a_constant_function_does_not_classify_fixed() -> None:
    """PF8. A constant map has EVERY period, so a period-finder alone would
    call it maximally frame-fixed. The non-degeneracy guard is the answer."""
    rec = fp.classify("CONST", {"x": 0}, lambda x: 7)
    assert rec["verdict"] == "NOT_ADMISSIBLE", rec
    assert not rec["findings"]


def test_the_instrument_separates_the_two_leaks_and_the_clean_control() -> None:
    """PF6. LEAK_A `fixed`(12); LEAK_B `parametric` AND generator 7; CLEAN
    neither. If LEAK_B reads clean, the instrument has reproduced the very
    blind spot it was built to narrow and MUST NOT SHIP."""
    a = fp.classify("LEAK_A", {"x": 0, "y": 3}, _leak_a)
    b = fp.classify("LEAK_B", {"x": 0, "y": 3, "n": 11}, _leak_b)
    c = fp.classify("CLEAN", {"x": 0, "y": 3, "n": 11, "g": 3}, _clean)

    assert fp.declared_scope(a["findings"]) == "fixed", a
    assert {f["period"] for f in a["findings"]} == {12}, a

    assert fp.declared_scope(b["findings"]) == "parametric", b
    gens = {f.get("generator") for f in b["findings"]}
    assert gens == {7}, (
        f"LEAK_B welds in the generator 7 and the instrument reports {gens}. "
        f"rc426's F12b calls this op CLEAN; an instrument that agrees with "
        f"F12b here has no reason to exist.")
    assert "generator" in fp.declared_axis(b["findings"]), b

    assert fp.declared_scope(c["findings"]) == "parametric", c
    assert all("generator" not in (f.get("axis") or []) for f in c["findings"]), (
        f"CLEAN welds in nothing, so declaring a generator for it would mean "
        f"the clause fires on everything: {c}")


def test_the_instrument_moves_one_axis_at_a_time() -> None:
    """Translating the frame coordinate must not move the modulus, and
    sweeping the modulus must not move the coordinate. A perturbation that
    moves both cannot attribute what it sees."""
    base = {"x": 5, "y": 3, "n": 11}
    drv = fp.Driver("LEAK_B", base, _leak_b)
    assert drv.base == base, "the driver mutated its own base binding"
    assert fp.translate(5, 7) == 12 and fp.translate([1, 2, 3], 7) == [8, 2, 3]
    # sequence() must not leak state between overrides
    s1 = drv.sequence("x", {"n": 5}, length=12)
    s2 = drv.sequence("x", {"n": 7}, length=12)
    assert s1 != s2, "two different moduli produced identical sequences"
    assert drv.base == base


# ══════════════════════════════════════════════════════════════════════
# 1. VOCABULARY CLOSURE — the field is closed only if something closes it
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("kw", [
    {"frame_scope": "free", "frame_axis": ("modulus",)},        # unknown scope
    {"frame_scope": "fixed", "frame_axis": ("chart",)},         # unknown axis
    {"frame_scope": "fixed", "frame_axis": ()},                 # half: no axis
    {"frame_scope": None, "frame_axis": ("modulus",)},          # half: no scope
])
def test_a_malformed_frame_declaration_is_rejected_at_registration(kw) -> None:
    with pytest.raises(ToolSchemaValidationError):
        ToolEntry(name="x", owner="srmech", category="c", summary="s", **kw)


def test_there_is_deliberately_no_free_scope() -> None:
    """An op with no frame datum cannot be contradicted on one, so it declares
    NOTHING. ``"free"`` would be a value no measurement could refute — which is
    the rc339 defect this whole family of fields is a reaction to."""
    assert "free" not in FRAME_SCOPES
    assert set(FRAME_SCOPES) == {"parametric", "fixed"}
    assert set(FRAME_AXES) == {"modulus", "generator"}


# ══════════════════════════════════════════════════════════════════════
# 2. THE RATCHET — declared matches measured
# ══════════════════════════════════════════════════════════════════════

def assert_declaration_matches(entry: ToolEntry, rec: Dict[str, Any]) -> None:
    """THE COMPARISON, as ONE callable — the whole ratchet and nothing else.

    §2 below is this function applied to the live registry. §6's falsifiers are
    this same function applied to a DELIBERATELY MIS-DECLARED copy of an entry,
    required to raise.

    That sharing is the point, and it is a repair (`#T1127`). At rc430 the two
    §6 falsifiers RE-SPELLED the comparison inline instead of calling it, which
    made both of them dominated by §2: each concluded `measured != lie` from
    premises §2 had already established (`measured == entry.frame_scope` and
    `entry.frame_scope != lie`), so neither could fail in any state where §2
    passed. They could only go red AFTER the suite was already red — which is
    not a falsifier, it is an echo. Weakening the body below now breaks §6
    directly, because §6 has no copy of it to keep passing.
    """
    measured = fp.declared_scope(rec["findings"])
    assert measured == entry.frame_scope, (
        f"{entry.name} declares frame_scope={entry.frame_scope!r} but measures "
        f"{measured!r}. findings={json.dumps(rec['findings'])}. MIS-DECLARED.")
    measured_axis = fp.declared_axis(rec["findings"])
    assert tuple(entry.frame_axis) == measured_axis, (
        f"{entry.name} declares frame_axis={tuple(entry.frame_axis)} but "
        f"measures {measured_axis}. MIS-DECLARED.")


@pytest.mark.parametrize("op_name", sorted(REVIEWED_ROSTER))
def test_declared_frame_matches_measured_response(op_name: str) -> None:
    """THE RATCHET. Drive the op over a dense translation sweep and assert the
    response matches what its ToolEntry declares."""
    entry = get_tool_schema().lookup(op_name)
    assert entry is not None, f"{op_name} is not registered"
    assert entry.frame_scope is not None, (
        f"{op_name} is in the rc430 reviewed roster but declares no frame — "
        f"either declare it or drop it from the roster; a driver with nothing "
        f"to check is the dead-seam failure mode.")

    rec = _census()[op_name]
    assert rec["verdict"] == "ADMISSIBLE", (
        f"{op_name} declares frame_scope={entry.frame_scope!r} but the "
        f"instrument cannot reach it: verdict={rec['verdict']}. A declaration "
        f"nothing can drive is exactly the false green this file removes.")

    assert_declaration_matches(entry, rec)


# ══════════════════════════════════════════════════════════════════════
# 3. THE GENERATOR CLAUSE — narrowed, and honest about it
# ══════════════════════════════════════════════════════════════════════

def test_the_generator_clause_is_narrow_and_says_so() -> None:
    """It decides AFFINE ops only, and the payload must admit that.

    A non-affine op that hard-wires a generator stays undeclarable. Claiming
    rc427's G3b is CLOSED would be false, so the blind spot ships as data in
    ``describe()["frames"]["cannot_express"]`` and is asserted here.
    """
    # affine: the difference IS the generator, read mod the frame
    assert fp.first_difference([9, 4, 11, 6, 1, 8], mod=12) == 7
    # over the integers the same sequence is NOT constant — the bug that made
    # LEAK_B read clean in the first draft
    assert fp.first_difference([9, 4, 11, 6, 1, 8]) is None
    # non-affine: undeclarable, and reported as such rather than guessed
    assert fp.first_difference([1, 2, 4, 8, 16], mod=64) is None
    # a generator of 1 is "no generator"; 0 is degeneracy, not an affine step
    f: Dict[str, Any] = {}
    fp._add_generator(f, {}, [0, 1, 2, 3, 4], 12)
    assert "generator" not in f
    f = {}
    fp._add_generator(f, {}, [5, 5, 5, 5], 12)
    assert "generator" not in f
    # and a generator the CALLER supplies is not welded in — tested up to
    # congruence, because mod_mul(a=19, n=12) advances by 7.
    f = {}
    fp._add_generator(f, {"a": 19, "n": 12}, [9, 4, 11, 6, 1, 8], 12)
    assert "generator" not in f, (
        "a caller-supplied generator was declared welded-in; that is the "
        "false-`fixed` error one axis over")

    cannot = describe()["frames"]["cannot_express"]
    assert "non_affine_generator" in cannot
    assert "frame_free_vs_no_frame" in cannot
    # rc430 repair (`#T1127`) — the THIRD blind spot, added because it was
    # MEASURED rather than reasoned: the roster is derived from one argument
    # set per op, and srmech.math.cyclic.gcd was missing from it for exactly
    # that reason. A payload that names two of three blind spots reads as a
    # complete list of them.
    assert "base_argument_dependence" in cannot


def test_the_generator_axis_population_is_EMPTY_not_absent() -> None:
    """NULL CLASSIFICATION — ``EMPTY``, and that is a result.

    Zero shipped ops declare the generator axis: every generator the census
    found is supplied by a parameter. The axis stays in the vocabulary because
    LEAK_B exercises it in-test and because absence of instances is not
    absence of the phenomenon — the same reason rc426's tier table keeps
    ``SECONDARY-OA`` with 0 instances.
    """
    declared = _declared()
    with_gen = sorted(n for n, e in declared.items() if "generator" in e.frame_axis)
    print(f"\n[rc430] generator-axis declarers: {len(with_gen)} — EMPTY, not "
          f"absent. The axis is exercised by the LEAK_B control in §0.")
    assert with_gen == [], (
        f"ops now declare the generator axis: {with_gen}. That is a GOOD "
        f"outcome — update this test and the CHANGELOG to record the first "
        f"instances rather than deleting the assertion.")
    assert "generator" in FRAME_AXES


# ══════════════════════════════════════════════════════════════════════
# 4. NO DECLARATION ESCAPES — both directions
# ══════════════════════════════════════════════════════════════════════

def test_declared_equals_admissible_in_both_directions() -> None:
    """The anti-opt-in mechanism, and the reason this field will not stall at
    1.4% the way ``reads_lane`` did.

    The admissible set is COMPUTED from behaviour over every op the provider
    can drive. An admissible op that declares nothing fails here; a declaring
    op the instrument does not admit fails here. Neither can be fixed by
    staying quiet.
    """
    census = _census()
    admissible = {n for n, r in census.items() if r["verdict"] == "ADMISSIBLE"}
    declared = set(_declared())

    undeclared = sorted(admissible - declared)
    unmeasured = sorted(declared - admissible)
    print(f"\n[rc430] admissible {len(admissible)} · declared {len(declared)}")
    assert not undeclared, (
        f"{len(undeclared)} op(s) are behaviourally admissible but declare no "
        f"frame:\n  " + "\n  ".join(undeclared[:20])
        + "\n\nDeclare them. Do NOT narrow the predicate to match the roster — "
          "the predicate is the measurement and the roster is the record of it.")
    assert not unmeasured, (
        f"{len(unmeasured)} op(s) declare a frame the instrument does not "
        f"admit:\n  " + "\n  ".join(unmeasured[:20]))
    assert declared == set(REVIEWED_ROSTER), (
        f"the live declaring set differs from the reviewed roster; "
        f"added {sorted(declared - set(REVIEWED_ROSTER))}, "
        f"removed {sorted(set(REVIEWED_ROSTER) - declared)}")


def test_unadjudicated_ops_are_counted_under_a_down_only_ceiling() -> None:
    """An op the driver cannot reach is UNADJUDICATED, not passing.

    Without this the previous test is trivially satisfiable by making the
    driver reach nothing: an empty admissible set equals an empty declared set.
    The ceiling is what keeps §4 from being green by ignorance.
    """
    census = _census()
    counts: Dict[str, int] = {}
    for rec in census.values():
        counts[rec["verdict"]] = counts.get(rec["verdict"], 0) + 1
    print(f"\n[rc430] frame census verdicts: {json.dumps(counts, sort_keys=True)}")

    for cls, ceil in CEIL_FRAME_UNADJUDICATED.items():
        got = counts.get(cls, 0)
        assert got <= ceil, (
            f"{cls} rose to {got}, above CEIL_FRAME_UNADJUDICATED[{cls!r}]="
            f"{ceil}. The unadjudicated class is growing, which means the "
            f"frame axis is going UNMEASURED on more of the registry, not "
            f"less. Drain NO_ARG by making the op's worked example bind its "
            f"arguments; drain BASE_RAISES the same way. Raising a CEIL needs "
            f"a reason in the same diff.")
    # CONTRACT_SKIP is the one residual class a future rc could quietly abuse
    # to make a red go away, so it is held to its stated reason: every entry
    # must be a REGISTERED op that really does document the contract claimed
    # for it. A name that is not in the registry, or one whose declaration says
    # nothing about primality, is a skip with no evidence behind it.
    for name, reason in fp.CONTRACT_SKIP.items():
        entry = get_tool_schema().lookup(name)
        assert entry is not None, f"CONTRACT_SKIP names an unregistered op: {name}"
        assert "PRIME" in reason.upper(), reason
        declared_text = " ".join(p.summary or "" for p in entry.parameters)
        assert "prime" in declared_text.lower(), (
            f"{name} is skipped for a primality contract, but no parameter of "
            f"its own declaration mentions one: {declared_text!r}. Either the "
            f"skip is wrong or the declaration is.")

    reached = counts.get("ADMISSIBLE", 0) + counts.get("NOT_ADMISSIBLE", 0)
    assert reached >= 130, (
        f"only {reached} ops were actually DRIVEN. §4 compares two sets the "
        f"instrument can see; if it can see almost nothing, both are empty and "
        f"agree for the wrong reason.")


# ══════════════════════════════════════════════════════════════════════
# 5. THE PAYLOAD SAYS WHAT THE MEASUREMENTS SAY
# ══════════════════════════════════════════════════════════════════════

def test_describe_frames_is_derived_from_the_tool_schema() -> None:
    d = describe()
    frames = d["frames"]
    declared = _declared()
    assert frames["total"] == len(declared)
    assert set(frames["ops"]) == set(declared)
    for name, row in frames["ops"].items():
        assert row["scope"] == declared[name].frame_scope
        assert row["axis"] == list(declared[name].frame_axis)
    assert sum(frames["by_scope"].values()) == frames["total"]
    assert set(frames["by_scope"]) <= set(FRAME_SCOPES)
    assert set(frames["by_axis"]) <= set(FRAME_AXES)
    assert frames["definitions"] == dict(FRAME_SCOPES)
    assert frames["axes"] == dict(FRAME_AXES)
    # the admission rule ships as DATA and NAMES the file that enforces it
    assert frames["verified_by"]["test"] == "tests/test_frame_scope_rc430.py"
    assert frames["verified_by"]["instrument"] == "tools/frame_probe.py"
    assert "never sampled" in frames["verified_by"]["rule"]


def test_the_frame_axis_is_orthogonal_to_the_lane_axis() -> None:
    """Two different questions about one op, asserted rather than narrated.

    Lane says WHAT an op reads of its operand; frame says what it reduces that
    read IN. If the two declaring sets coincided, one of the fields would be a
    re-spelling of the other.
    """
    d = describe()
    lane_ops, frame_ops = set(d["lanes"]["ops"]), set(d["frames"]["ops"])
    assert lane_ops and frame_ops
    assert not (lane_ops & frame_ops), (
        f"an op declares BOTH a lane and a frame: {sorted(lane_ops & frame_ops)}. "
        f"That is allowed in principle — but at rc430 the sets are disjoint, "
        f"and a change wants recording rather than silence.")


# ══════════════════════════════════════════════════════════════════════
# 6. HOW IT FAILS — the both-sides bite, pre-registered
# ══════════════════════════════════════════════════════════════════════

def _mutated(entry: ToolEntry, **kw: Any) -> ToolEntry:
    """A copy of ``entry`` with a DELIBERATELY WRONG declaration. ToolEntry is a
    frozen dataclass, so this is a real object the real gate can be run against
    — not a local restatement of what the gate would have said."""
    return dataclasses.replace(entry, **kw)


def test_every_false_scope_fails_the_ratchet() -> None:
    """FALSIFIER F-1, exhaustive. For each declaring op, substitute every OTHER
    value in ``FRAME_SCOPES`` into a real ToolEntry copy and run the REAL
    comparison (``assert_declaration_matches``). REFUTED if any false value
    still passes — a gate that accepts a wrong answer is not a gate.

    rc430-repair note (`#T1127`): this used to compute
    ``[s for s in FRAME_SCOPES if s != entry.frame_scope and s == measured]``
    and assert the list was empty. With §2 having already established
    ``measured == entry.frame_scope``, that list is empty for the same reason a
    thing cannot differ from itself — the check was DOMINATED by §2 and could
    not go red in any state where the suite was green. It now calls the shipped
    comparison, so weakening that comparison shows up HERE.
    """
    census = _census()
    rows: List[str] = []
    non_discriminating: List[str] = []
    for name, entry in sorted(_declared().items()):
        rec = census[name]
        accepted = []
        for false_scope in FRAME_SCOPES:
            if false_scope == entry.frame_scope:
                continue
            try:
                assert_declaration_matches(
                    _mutated(entry, frame_scope=false_scope), rec)
            except AssertionError:
                continue                   # the gate bit, as it must
            accepted.append(false_scope)   # the gate ACCEPTED a lie
        rows.append(f"  {name:60s} {entry.frame_scope:11s} "
                    f"false_that_PASS={accepted or 'NONE (discriminating)'}")
        if accepted:
            non_discriminating.append(f"{name}: {accepted}")
    print("\n[rc430] F-1 exhaustive false-scope sweep\n" + "\n".join(rows))
    print(f"declarers {len(rows)} | fully discriminating "
          f"{len(rows) - len(non_discriminating)}/{len(rows)}")
    assert rows, "no declarers — F-1 would pass vacuously"
    assert not non_discriminating, (
        "REFUTED — a false frame_scope passes the ratchet for:\n  "
        + "\n  ".join(non_discriminating))


@pytest.mark.parametrize("op_name,lie", [
    ("srmech.music.interval_vector", "parametric"),
    ("srmech.cascade.cyclic_mod_add", "fixed"),
])
def test_gate_fires_on_a_planted_defect(op_name: str, lie: str) -> None:
    """FALSIFIER F-2 — the LIVE gate function, driven with an injected lie.

    A mis-declared ToolEntry copy is passed to the SAME
    ``assert_declaration_matches`` §2 uses, and it must raise. Both directions
    are planted: a hard-wired op claiming to be parametric, and a parametric op
    claiming to be hard-wired.

    rc430-repair note (`#T1127`): this used to open
    ``with pytest.raises(AssertionError): assert measured == lie`` over
    locally-computed values, having just asserted both ``measured ==
    entry.frame_scope`` and ``entry.frame_scope != lie``. The raise was
    therefore guaranteed by the preconditions rather than by the gate, and the
    gate itself was never invoked — the test would have stayed green if the
    shipped comparison had been deleted outright.
    """
    entry = get_tool_schema().lookup(op_name)
    assert entry is not None and entry.frame_scope != lie
    rec = _census()[op_name]

    # Precondition: the TRUTH passes the real gate.
    assert_declaration_matches(entry, rec)

    # The LIE must fail that same real gate.
    with pytest.raises(AssertionError):
        assert_declaration_matches(_mutated(entry, frame_scope=lie), rec)


def test_the_planted_axis_also_fails_the_ratchet() -> None:
    """FALSIFIER F-2b. The scope is not the only declared field — ``frame_axis``
    is compared too, and a falsifier that only ever plants a bad SCOPE leaves
    the axis half of the comparison unproven.

    The planted axis is a VALID vocabulary term that is the WRONG one for the
    op, never a made-up token. That distinction is the whole test: a nonsense
    token is rejected by the registration TYPE-VALIDATOR at construction, so a
    falsifier built on one never reaches the declared-vs-measured comparison and
    proves the validator works instead of the ratchet. Only a well-formed lie
    reaches the gate under test.
    """
    census = _census()
    survived = []
    planted = 0
    for name, entry in sorted(_declared().items()):
        declared_axis = tuple(entry.frame_axis)
        for axis in sorted(FRAME_AXES):
            if (axis,) == declared_axis:
                continue
            planted += 1
            try:
                assert_declaration_matches(
                    _mutated(entry, frame_axis=(axis,)), census[name])
            except AssertionError:
                continue                   # the gate bit, as it must
            survived.append(f"{name}: declared {declared_axis} accepted ({axis},)")
    assert planted, "no lie was planted — F-2b would pass vacuously"
    print(f"\n[rc430 repair] F-2b planted {planted} well-formed false axes")
    assert not survived, (
        "REFUTED — a false frame_axis passes the ratchet for:\n  "
        + "\n  ".join(survived))


def test_no_control_in_this_module_is_computed_and_then_ignored() -> None:
    """FALSIFIER F-3 — the DEAD-SEAM check. rc428's D1 computed its controls
    and never read them: ``main()`` returned 0 while printing ``DEAD SEAM``.

    Every control this module builds must be CONSUMED by an assertion, and the
    cheapest way to prove that is to re-derive them here and require they are
    non-trivial. A control that cannot come out any other way is not a control.
    """
    a = fp.classify("LEAK_A", {"x": 0, "y": 3}, _leak_a)
    b = fp.classify("LEAK_B", {"x": 0, "y": 3, "n": 11}, _leak_b)
    c = fp.classify("CLEAN", {"x": 0, "y": 3, "n": 11, "g": 3}, _clean)
    verdicts = {fp.declared_scope(r["findings"]) for r in (a, b, c)}
    assert verdicts == {"fixed", "parametric"}, (
        f"the three controls collapsed to {verdicts}; an instrument that "
        f"returns one verdict for every input is not measuring anything")
    # 20 at rc430; 21 at the rc430 repair (`#T1127`), when the probe's
    # degeneracy screen stopped foreclosing the parametric sweep and
    # srmech.math.cyclic.gcd became measurable. The count moved because the
    # INSTRUMENT was repaired, not because an op was hand-added to the roster.
    assert len(_declared()) == len(REVIEWED_ROSTER) == 21
    assert set(_census()) == {e.name for e in get_tool_schema().tools}, (
        "the census does not cover the registry, so §4's set comparison is "
        "over a subset it chose itself")
