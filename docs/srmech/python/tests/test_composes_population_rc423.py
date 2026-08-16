"""composes — the POPULATION (rc423, `#T1113`).

User direction 2026-08-08: *"every operation should also have its cascade
composition still as part of its identity."* Everything needed already
shipped. The FIELD landed rc305 (``ToolEntry.composes``, C-mirrored, riding
``tool_schema_sha256``). The READER landed rc412 (``ToolSchema.composition()``
plus the reverse edge). The GATES landed rc305 / rc412 (registry membership,
AST call-reachability, acyclicity). **What was missing is POPULATION**, and
this file is that.

THE DEFECT THIS FILE FIXES IS A MISSING DISTINCTION, NOT A MISSING NUMBER
========================================================================
``composes`` correctness was gated three ways; its POPULATION was gated zero
ways. Measured across the arc: 9 rows at rc412, 16 at rc422 — seven rows in
roughly forty-five rcs, every gate green the whole time. Six of those seven
arrived in a single rc because that author happened to look.

The reason a ratchet was refused (``test_composes_grain_rc412.py``, and see
the ⚠️ amendment now standing there) is real but was aimed one set to the
left. It said a down-only ceiling on **unpopulated** rows presumes the
residual should reach zero, "and here it must not" — correct, because a leaf
is permanently and correctly empty. But **unpopulated** and **UNADJUDICATED**
are different sets, and the field cannot tell them apart: a row nobody has
ever examined and a row measured to compose nothing are both ``()``. Every
"is the population complete?" question therefore had no answer, and an
unanswerable question is what let the number sit still.

So this file makes the distinction the field cannot, and puts the ceiling on
the half that can honestly drain.

FOUR TIERS, AND EACH TAKES THE READING THAT CAN FALSIFY IT
===========================================================
Every one of the 612 registered ops lands in exactly one tier. The ledger
(``tests/composes_adjudication_rc423.ndjson``, produced by the committed
census script ``docs/srmech/notes/_composes_population_census_rc423.py``)
enumerates the first three; RESIDUAL is the complement and is deliberately
NOT enumerated, so the ceiling cannot become a second copy of a list that
then drifts from the first.

  ``DECLARED``  a hand-traced multi-op composition. Pinned row-by-row in
                ``test_composes_grain_rc412.py::ROSTER``; that file gates it
                and this one does not re-gate it.
  ``LEAF``      ``derived(name, depth=3)`` is EMPTY. "This op composes nothing
                registered" becomes a MEASURED statement instead of an
                absence. Depth **3** — the most generous reach available —
                because for an emptiness claim an under-reading is the
                PERMISSIVE direction (see ``composes_derive``'s docstring).
  ``SINGLE``    ``derived(name, depth=1)`` is a SINGLETON: the op's own body
                directly calls exactly one registered op. Depth **1**,
                because a depth-3 singleton could be a private helper's
                internal that the parent never calls itself — the
                over-attribution ``klein4_compose``'s ROSTER note refuses.
  ``REFUSED``   tier-eligible, and a prior rc read the implementation and
                declined. One row: ``covering_catalog`` (rc422). Recorded as
                DATA so the carve-out is visible rather than a silent skip.

**The ORDER problem does not arise here, and that is the point.** rc412
measured that lexical first-call order matches ground truth on **0 of 2**
rows — so a derived SET is trustworthy and a derived SEQUENCE is not. (The
brief for this rc had that measurement inverted, claiming order matched on
all 7; it does not, and nothing here relies on it.) This file never orders
anything: a LEAF has no sequence, and a SINGLE has exactly one element, which
has exactly one ordering. Order stays a human act, performed in ROSTER. That
is why the mechanical tiers stop at one sub-op instead of reaching for the
156 rows with two or more.

THE TRUTH TIER OF EVERY ROW IS LABELLED, BECAUSE ASSERTION IS NOT PROOF
=======================================================================
This tree has shipped declarations no instrument checked. Each population
here therefore names what proved it, and the proofs are of different
strengths — recorded honestly rather than levelled up:

  ============  ==========================  ============================
  tier          proved by                   shape
  ============  ==========================  ============================
  LEAF          AST reachability, depth 3   EQUALITY: derived == ∅
  SINGLE        AST reachability, depth 1   EQUALITY: derived == {declared}
  REFUSED       human review, recorded      the rationale is in the census
  DECLARED      AST reachability, depth 3   SUBSET: declared ⊆ derived
  ============  ==========================  ============================

The mechanical tiers are gated by EQUALITY and the hand-traced tier by
SUBSET, and that asymmetry is not an oversight: a subset check is all that is
available once a human selects which of several reachable ops to name, while
a mechanically-derived row has nothing to select and so must match exactly.
Equality is the stronger claim, and the rows that can bear it do.

**What no tier here claims is EXECUTION.** Value-threading equivalence — the
chain actually runs and returns bit-identical output — is a real and stronger
proof, and it already exists for a different population: ADR-0008's
``tests/test_cascade_catalog_executable_rc420.py`` executes 98 proof cases
over the 21 cascade descriptors. :func:`test_execution_proved_rows_are_named`
below records the overlap rather than claiming it, so "AST-reachable" is
never read as "executed".

numpy-free; stdlib only. The derivation is imported from
``tests/composes_derive.py`` and is the SAME instrument rc412's clause 2 uses
— a second copy would drift.
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from composes_derive import (BY_NAME, SCHEMA, derived, load_ledger,
                             ledger_names)

_LEDGER = load_ledger()
_DECLARING: Dict[str, Tuple[str, ...]] = {
    t.name: tuple(t.composes) for t in SCHEMA.tools if t.composes}


# ──────────────────────────────────────────────────────────────────────
# THE RATCHET.
#
# ⚠️ DOWN-ONLY. This is the number the rc exists to move, and it may only
# ever fall. It counts ops that are NOT adjudicated: not declared, not
# measured to be a leaf, not measured to be a forced-order singleton, not
# deliberately refused. Every one of them is a row whose body calls TWO OR
# MORE registered ops, i.e. exactly the rows where ORDER is a human act.
#
# SEEDED at rc423 = 182, measured over a registry of 605 by
# docs/srmech/notes/_composes_population_census_rc423.py. The full census at
# that measurement:
#
#     DECLARED  16   SINGLE 148   LEAF 258   REFUSED 1   RESIDUAL 182
#     adjudicated 423 / 605        composes population 164 / 605
#
# rc424 (`#T1113`) re-ran the same census over a registry of 612:
#
#     DECLARED  23   SINGLE 148   LEAF 258   REFUSED 1   RESIDUAL 182
#     adjudicated 430 / 612        composes population 171 / 612
#
# The CEILING DOES NOT MOVE, and that is the wanted outcome rather than a
# missed drain: rc424 registered seven ops and authored `composes` for all
# seven AT BIRTH, so all seven landed in DECLARED and none passed through the
# residual. A registry that grows by 7 with an unchanged residual is the
# ratchet doing precisely what it was seeded to do. (Had even one arrived
# undeclared, RESIDUAL would read 183 and this gate would be red — which is
# the whole design.)
#
# A row leaves this residual by being TRACED — read the implementation, work
# out the call order, add it to test_composes_grain_rc412.py::ROSTER — and
# then this ceiling is LOWERED in the same commit. That is the only sanctioned
# way it falls.
#
# NEVER raise it. A new op arriving with two-plus call edges and no traced
# order is precisely the drift this ratchet exists to catch; raising the
# ceiling to admit it converts the ratchet into a comment, which is what the
# `preserves` HOLD became (ADR-0013 §1.7.1) before rc423 adjudicated it.
#
# rc437 (local task T1142) re-ran the same census over a registry of 661, and
# the ceiling comes DOWN to 181 — LOWERED by a trace, which the paragraph above
# names as the only sanctioned way it moves:
#
#     DECLARED  45   SINGLE 164   LEAF 270   REFUSED 1   RESIDUAL 181
#     adjudicated 480 / 661        composes population 209 / 661
#
# Worth recording because the first attempt WOULD have needed a raise, and the
# fix was structural rather than numeric. rc437 registered five ops. Three
# landed adjudicated at birth (walsh_hadamard_transform is a measured LEAF;
# cd_left_divide / cd_right_divide are SINGLE). The other two — the left/right
# REGULAR REPRESENTATIONS — each reach `cd_mult` and `table_product` on
# MUTUALLY EXCLUSIVE branches, which is not ROSTER-eligible as a sequence and
# has no tier of its own, so they arrived RESIDUAL and took the count to 183.
#
# Two things drained it, and neither was a ceiling bump. (a) Registering
# `left_mult_matrix` / `right_mult_matrix` — which had carried an
# OPEN_REGISTRATION gap row since rc160 — gave the two DIVISION ops a
# registered sub-op at depth 1, moving them from RESIDUAL to SINGLE. (b) Both
# representations were then TRACED and declared with a ONE-element tuple:
# `table` SUBSTITUTES the product rather than adding a call, so declaring both
# would assert a sequence that never occurs, and the selected branch is left
# undeclared exactly as `dispatch` leaves its selected implementation
# undeclared. See the rc437 block in test_composes_grain_rc412.py::ROSTER.
# ──────────────────────────────────────────────────────────────────────
CEIL_UNADJUDICATED = 181

#: How far the residual may drain below the ceiling before the ceiling itself
#: must come down. Small on purpose — a ratchet with slack ratchets nothing.
_CEIL_SLACK = 4


def _unadjudicated() -> List[str]:
    """Registered ops in no ledger tier and carrying no declaration."""
    return sorted(n for n in BY_NAME
                  if n not in _LEDGER and n not in _DECLARING)


def test_unadjudicated_population_is_down_only() -> None:
    """THE RATCHET. The unadjudicated residual may only ever shrink.

    This is the clause that makes ``composes`` population a gated property
    rather than a hope. Correctness had three gates and population had none,
    and a surface with no population gate does not trickle — it stalls, and
    then reads as finished because nothing is red.
    """
    residual = _unadjudicated()
    assert len(residual) <= CEIL_UNADJUDICATED, (
        f"{len(residual)} registered ops carry no composes adjudication, "
        f"ceiling {CEIL_UNADJUDICATED}. This ratchet is DOWN-ONLY. "
        f"A new op with two or more call edges must have its ORDER TRACED "
        f"and go into test_composes_grain_rc412.py::ROSTER — do not raise "
        f"the ceiling, and do not hand-write a row into the ledger to make "
        f"this pass.\nUnadjudicated: {residual[:20]}"
        + (f" ... (+{len(residual) - 20} more)" if len(residual) > 20 else ""))


def test_the_ceiling_is_not_slack() -> None:
    """A ceiling far above the count is a ratchet that ratchets nothing."""
    residual = _unadjudicated()
    assert len(residual) >= CEIL_UNADJUDICATED - _CEIL_SLACK, (
        f"the unadjudicated residual has drained to {len(residual)} against "
        f"a ceiling of {CEIL_UNADJUDICATED}. Lower CEIL_UNADJUDICATED to "
        f"{len(residual)} in the same commit — that is what makes this "
        f"down-only rather than decorative.")


def test_every_registered_op_lands_in_exactly_one_tier() -> None:
    """PARTITION. The four tiers plus the residual cover the registry with no
    overlap.

    Without this, a row could sit in two tiers and be counted as adjudicated
    twice while a third population quietly hid inside the second — the
    bucket-hopping failure a split ceiling exists to prevent.
    """
    for name, rec in _LEDGER.items():
        assert name in BY_NAME, (
            f"the ledger names an op that is not registered: {name}. Either "
            f"the op was removed and the ledger is stale, or the name is "
            f"wrong; regenerate the census rather than editing by hand.")
        assert rec["tier"] in ("LEAF", "SINGLE", "REFUSED"), (
            f"{name}: unknown tier {rec['tier']!r}")

    declared = set(_DECLARING)
    single = ledger_names("SINGLE")
    leaf = ledger_names("LEAF")
    refused = ledger_names("REFUSED")
    residual = set(_unadjudicated())

    # SINGLE rows DO declare — they are the seeded population — so they are
    # expected to intersect `declared`. The other three must not.
    assert single <= declared, (
        f"SINGLE-tier rows that do not actually declare a composes tuple: "
        f"{sorted(single - declared)}. The ledger says they were seeded; the "
        f"registry disagrees. Regenerate _tool_docs.py.")
    for label, group in (("LEAF", leaf), ("REFUSED", refused),
                         ("RESIDUAL", residual)):
        assert not (group & declared), (
            f"{label} rows that nevertheless declare a composes tuple: "
            f"{sorted(group & declared)}")

    total = len(declared | single | leaf | refused | residual)
    assert total == len(BY_NAME), (
        f"the tiers cover {total} ops but the registry holds {len(BY_NAME)} "
        f"— the partition leaks.")


def test_the_two_populations_do_not_overlap() -> None:
    """ROSTER (hand-traced) and SINGLE (forced-order) are disjoint.

    rc412's clause 1 now asserts the declaring set equals the UNION of the
    two ledgers. A union is only an exact pin if the parts cannot absorb each
    other — otherwise a row could move from the reviewed-by-hand population
    into the reviewed-by-rule one to escape having its order traced.
    """
    from test_composes_grain_rc412 import ROSTER

    overlap = set(ROSTER) & ledger_names("SINGLE")
    assert not overlap, (
        f"rows in BOTH the hand-traced ROSTER and the forced-order SINGLE "
        f"tier: {sorted(overlap)}. A hand-traced row must not be re-admitted "
        f"under the mechanical rule — that would retire its traced order "
        f"without review.")


# ──────────────────────────────────────────────────────────────────────
# TIER PROOFS. Each population is re-derived from source, every run.
# ──────────────────────────────────────────────────────────────────────


def test_every_leaf_row_reaches_nothing() -> None:
    """LEAF, proved by EQUALITY against the empty set at depth 3.

    "This op composes nothing registered" is a claim about the code, so it is
    checked against the code rather than believed. Depth 3 is deliberate: it
    is the most generous reach the instrument offers, so a row that passes
    here composes nothing under the reading MOST likely to find something.
    """
    offenders: Dict[str, List[str]] = {}
    for name in sorted(ledger_names("LEAF")):
        reach = derived(name, 3)
        if reach:
            offenders[name] = sorted(reach)
    assert not offenders, (
        f"{len(offenders)} row(s) are declared LEAF but DO reach registered "
        f"ops: {dict(list(offenders.items())[:10])}. The code grew a "
        f"composition after the row was adjudicated. Re-run "
        f"docs/srmech/notes/_composes_population_census_rc423.py — do not "
        f"delete the row to make this pass.")


def _single_tier_offence(name: str, claimed: Tuple[str, ...]) -> str:
    """THE SINGLE-tier predicate, factored out so the negative control can run
    the REAL one.

    Returns an offence description, or ``""`` when ``claimed`` is a truthful
    forced-order composition for ``name``. Factoring matters: a negative
    control that re-states the predicate instead of calling it proves only
    that the test author can write the same expression twice.
    """
    direct = derived(name, 1)
    if len(direct) != 1:
        return (f"not a forced-order singleton: direct call set is "
                f"{sorted(direct)}")
    if set(claimed) != direct:
        return f"claims {claimed} but directly calls {sorted(direct)}"
    return ""


def test_every_single_row_declares_exactly_what_it_calls() -> None:
    """SINGLE, proved by EQUALITY at depth 1 — the strongest shape here.

    The declared tuple must be exactly the op's direct call set, and that set
    must hold exactly one element. Equality (not subset) is what makes the
    tier mechanical: there was no human choice about WHICH op to name, so
    there is nothing for a subset check to be lenient about.
    """
    offenders: Dict[str, str] = {}
    for name in sorted(ledger_names("SINGLE")):
        want = tuple(_LEDGER[name]["composes"])
        live = tuple(BY_NAME[name].composes)
        if live != want:
            offenders[name] = f"registry says {live}, ledger says {want}"
            continue
        offence = _single_tier_offence(name, want)
        if offence:
            offenders[name] = offence
    assert not offenders, (
        f"{len(offenders)} forced-order SINGLE row(s) no longer match the "
        f"code: {dict(list(offenders.items())[:10])}. A row that grew a "
        f"second call edge is no longer forced-order — it must be TRACED "
        f"into ROSTER, not silently re-derived.")


def test_refused_rows_are_tier_eligible_and_stay_undeclared() -> None:
    """REFUSED, proved by showing the refusal is still LOAD-BEARING.

    A refusal only means something while the mechanical rule would otherwise
    admit the row. If the code changed so that ``covering_catalog`` no longer
    calls exactly one registered op, the carve-out has become a dead entry
    that would quietly outlive its reason — so this asserts eligibility, not
    just absence.
    """
    refused = ledger_names("REFUSED")
    assert refused, (
        "the REFUSED tier is empty — either the carve-out was dropped "
        "without recording why, or the ledger is stale")
    for name in sorted(refused):
        assert not BY_NAME[name].composes, (
            f"{name} is recorded as deliberately REFUSED but now declares "
            f"{BY_NAME[name].composes}. If the refusal was reversed, move the "
            f"row to ROSTER with its traced order and say so.")
        direct = derived(name, 1)
        assert len(direct) == 1, (
            f"{name} is recorded REFUSED as a tier-eligible singleton, but "
            f"its direct call set is now {sorted(direct)}. The refusal no "
            f"longer refuses anything — re-run the census and drop or "
            f"re-justify the entry.")


# ──────────────────────────────────────────────────────────────────────
# ⚠️ NEGATIVE CONTROLS. A gate that passes on invented rows is not a gate.
# ──────────────────────────────────────────────────────────────────────


def test_a_fabricated_single_row_is_rejected() -> None:
    """⚠️ NEGATIVE CONTROL — the load-bearing one.

    The SINGLE tier is machine-generated, so the question a reader should ask
    is whether its gate could pass on a row somebody simply made up. This
    answers by making three up and running the REAL predicate
    (:func:`_single_tier_offence`) over them — the same function
    :func:`test_every_single_row_declares_exactly_what_it_calls` uses, not a
    restatement of it.

    Three distinct fabrications, because they fail for three different
    reasons and a control that only exercises one of them would leave the
    other two unproven:

    1. a plausible-but-wrong sub-op on a real SINGLE row (the likely
       hand-edit),
    2. a two-element tuple on a real SINGLE row (smuggling an untraced order
       past the mechanical rule),
    3. a claim on a row that is a genuine LEAF (inventing an edge that does
       not exist at all).
    """
    victim = sorted(ledger_names("SINGLE"))[0]
    truth = tuple(_LEDGER[victim]["composes"])
    assert not _single_tier_offence(victim, truth), (
        f"the control's baseline is broken: {victim}'s TRUE row is already "
        f"being rejected, so a rejection below would prove nothing")

    wrong = ("srmech.amsc.format.sha256_bytes",)
    assert set(wrong) != set(truth), (
        f"the fabrication is accidentally TRUE of {victim} — pick another")
    assert _single_tier_offence(victim, wrong), (
        f"a FABRICATED sub-op survived the SINGLE-tier predicate on {victim}. "
        f"The tier would then be unverified and every one of its rows "
        f"unproven.")

    smuggled = truth + ("srmech.amsc.format.sha256_bytes",)
    assert _single_tier_offence(victim, smuggled), (
        f"a two-element tuple survived the forced-order predicate on "
        f"{victim} — untraced ORDER could be smuggled in under a rule that "
        f"only ever justified one element")

    leaf = sorted(ledger_names("LEAF"))[0]
    assert _single_tier_offence(leaf, ("srmech.amsc.format.sha256_bytes",)), (
        f"an invented edge survived on {leaf}, which reaches nothing at all")


def test_a_fabricated_leaf_row_is_rejected() -> None:
    """⚠️ NEGATIVE CONTROL for the other mechanical tier.

    Declaring a leaf on an op that demonstrably composes something is the
    cheapest way to shrink the residual dishonestly — it costs nothing, needs
    no code, and moves the ceiling. So the leaf predicate is run against a row
    known to compose three things.
    """
    liar = "srmech.math.modular_linalg.gf_rref"
    reach = derived(liar, 3)
    assert reach, (
        f"{liar} was chosen because it reaches registered ops; it no longer "
        f"does, so this control proves nothing as written")
    # the exact predicate test_every_leaf_row_reaches_nothing applies:
    assert bool(reach), (
        f"a fabricated LEAF row on {liar} survived — the leaf tier would be "
        f"an assertion rather than a measurement, and the ceiling could be "
        f"drained by typing rather than by tracing")


def test_the_instrument_still_discriminates_at_depth_one() -> None:
    """⚠️ NON-VACUITY of the depth-1 reading the SINGLE tier rests on.

    rc412 proved the depth-3 instrument discriminates. The SINGLE tier uses
    depth 1, which is a DIFFERENT reading and needs its own proof: a depth-1
    derivation that returned nothing would make every op look like a leaf and
    a depth-1 derivation that returned everything would make no op forced-
    order. Both failure modes are silent.
    """
    seen = derived("srmech.math.kepler.pin_slot", 1)
    assert "srmech.math.rational.atan2" in seen, (
        "the depth-1 instrument cannot see a direct call it must see")
    assert "srmech.amsc.format.sha256_bytes" not in seen, (
        "the depth-1 instrument attributes an op that is never called")
    assert derived("srmech.amsc.format.sha256_bytes", 1) == set(), (
        "sha256_bytes is the registry's canonical leaf (pinned empty since "
        "rc305) and the depth-1 instrument disagrees")


def test_the_ledger_is_not_empty_and_covers_all_three_tiers() -> None:
    """GUARDS THE GUARD. Every clause above sweeps a ledger-derived set, and
    a strict sweep over an empty set passes."""
    assert len(_LEDGER) > 300, (
        f"the adjudication ledger holds only {len(_LEDGER)} rows; every "
        f"population clause in this file is near-vacuous")
    for tier in ("LEAF", "SINGLE", "REFUSED"):
        assert ledger_names(tier), f"the {tier} tier is empty — clauses over "\
            f"it are vacuously true"


# ──────────────────────────────────────────────────────────────────────
# The population, STATED. ADR-0012 §12: declaring an arc complete requires
# stating the population, and a count gate over an empty selected set is not
# evidence.
# ──────────────────────────────────────────────────────────────────────


def test_the_shipped_population_matches_the_ledger() -> None:
    """The registry's declaring set is exactly ROSTER ∪ SINGLE, and the
    number is the one the CHANGELOG claims."""
    from test_composes_grain_rc412 import ROSTER

    assert set(_DECLARING) == set(ROSTER) | ledger_names("SINGLE")
    assert len(_DECLARING) == len(ROSTER) + len(ledger_names("SINGLE")), (
        "ROSTER and SINGLE overlap, so the population count double-counts")


def test_execution_proved_rows_are_named() -> None:
    """Which rows carry the STRONGER proof, printed. Never a failure.

    AST reachability says a call edge exists in the source. EXECUTION
    equivalence says the declared chain runs and returns bit-identical output
    — a strictly stronger claim, held by ADR-0008's cascade-descriptor
    population (``test_cascade_catalog_executable_rc420.py``, 98 proof cases)
    and NOT by the tiers in this file.

    This prints the overlap so the difference stays visible. Without it,
    "gated" flattens into one word and the weaker proof inherits the
    reputation of the stronger — the exact levelling-up ADR-0012 §12 warns
    about.
    """
    from composes_derive import LEDGER_PATH  # noqa: F401  (path provenance)

    catalog = (LEDGER_PATH.parent.parent / "srmech" / "cascade" / "catalogs"
               / "cascade_catalog")
    descriptor_leaves = {p.stem for p in catalog.glob("*.toml")} \
        if catalog.is_dir() else set()
    execution_proved = sorted(
        n for n in _DECLARING if n.rsplit(".", 1)[-1] in descriptor_leaves)
    print(f"\n[rc423] composes rows ALSO carrying ADR-0008 execution-"
          f"equivalence proof (a cascade descriptor with an executable "
          f"chain): {execution_proved or 'none'}")
    print(f"[rc423] population by proof tier — "
          f"AST-equality(depth1) SINGLE={len(ledger_names('SINGLE'))}, "
          f"AST-equality(depth3) LEAF={len(ledger_names('LEAF'))}, "
          f"AST-subset(depth3) DECLARED={len(_DECLARING) - len(ledger_names('SINGLE'))}, "
          f"human-review REFUSED={len(ledger_names('REFUSED'))}, "
          f"UNADJUDICATED={len(_unadjudicated())}\n")
    assert True
