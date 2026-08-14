"""rc431 `#T1129` / `#T1094` -- the invocable OUTCOME set, and a floor under it.

THE JOIN
--------
Two rc431 scoping measurements each held half of one number and neither named
it:

  * SUPPLY side (`#T1129`): where the worked-example harvest covers ALL of an
    op's required parameters, **98.5%** of those ops RETURN; PARTIAL coverage
    gives 52.2% and NONE gives 46.9%. The whole value of the harvest is that
    ops actually RETURN.

  * CONSUMER side (`#T1094`): the shipped parametrized gate
    ``test_mcp.py::test_advertised_tool_invocable`` observes **473 returns**
    across the advertised registry -- and that number sits under **no floor
    whatsoever**. The scope proved it by mutation:

        CONTROL   (every op raises a binding TypeError):  617 failed,   0 passed
        MUTATION  (every op rejects every argument):        0 failed, 617 passed

    Every node returns early once the op has been *reached*; the gate measures
    binding + coercion, and is fully compatible with every op rejecting every
    argument. Nothing would notice if all 473 returns became rejections.

So the supply's entire value is a number the consumer does not measure, and the
consumer's one unmeasured number is exactly what the supply moves. This file
owns that number. The parametrized sibling keeps its per-op binding assertion;
this gate owns the OUTCOME set.

WHY A SET AND NOT A COUNT
-------------------------
``tests/invocable_returned_rc431.txt`` holds SORTED OP NAMES, not a cardinal.
*Counts are not sets; existence proves nothing, TOPICALITY decides.* A cardinal
floor cannot say WHICH op stopped returning, and it cannot see a swap that
leaves the total unchanged -- one op regressing to a rejection while another
starts returning reads as "still 473". The set detects both.

Direction: an op leaving the set FAILS (strict-zero on regressions); an op
newly returning is REPORTED and does not fail, because a gate that punishes
improvement gets improvements reverted. Refresh the file deliberately, in the
commit that earns the new members.

SELF-PROOF (mandatory -- see ``test_classifier_cannot_report_returns_when_every_op_raises``)
--------------------------------------------------------------------------------------------
The scope proved this gate's parametrized sibling passes under a mutation where
every op rejects every argument. A floor gate with the same blindness would be
worthless, so the classifier here is run against exactly that mutation and must
report ZERO returns. *An instrument that cannot return otherwise is not a
measurement.* Without that control this gate is not shippable.

MEASURED, NOT ADOPTED
---------------------
``harvest_op`` records the WHOLE bound argument map of a call that returned;
``_synth_args_for_entry`` then walks per-parameter and drops every optional.
Passing the recorded tuple whole flips 4 ops TOLERATED->RETURNED
(``run_catalog_chain``, ``op_provenance.carry``, ``dsl.run_cascade_chain``,
``laplacian.generalized_ngon``) and REGRESSES 1 (``klein4_holographic_decode``).
That is supply the consumer already holds and throws away. This gate does NOT
adopt it: it pins the outcome set of the SHIPPED consumer, because a gate that
fed different arguments than the tree feeds would be measuring something the
tree does not do. The whole-tuple result is recorded in
``docs/srmech/notes/_s2_synth_args_rc431.ndjson`` as a measurement awaiting its
own rc.
"""

from __future__ import annotations

import pathlib

import pytest

import srmech
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

FLOOR_PATH = pathlib.Path(__file__).with_name("invocable_returned_rc431.txt")

# Excluded on a RUNTIME axis, not a correctness one, and named rather than
# pattern-matched so the exclusion cannot silently widen.
#
# These five are the ops the rc431 `#T1094` scope recorded as INVOKE_TIMEOUT
# against a 20 s budget. Building this gate's floor set re-measured them without
# a budget and the run was still going after 25 MINUTES, so they are minutes-slow
# under synthetic arguments, not merely over 20 s. A gate that hangs is worse
# than no gate: it turns a CI failure into a CI timeout, which reads as
# infrastructure flake rather than as a regression.
#
# They are NOT in the floor set -- they never returned inside any budget -- so
# excluding them removes no assertion. What it does do is leave them
# UNADJUDICATED on the outcome axis, which is stated here rather than hidden:
# nothing in this gate can tell you whether they return, reject, or diverge.
# Closing that needs an op-level performance fix, not a bigger budget.
SLOW_OPS_UNADJUDICATED = frozenset({
    "srmech.physics.qm.potentials.hydrogen_radial",
    "srmech.physics.qm.so8.so7_subalgebra",
    "srmech.physics.qm.triality.triality_automorphism",
    "srmech.physics.qm.triality.triality_swap",
    "srmech.physics.qm.triality.lean_isa_seventh_primitive",
})


def _advertised_entries():
    warmup_all()
    schema = get_tool_schema()
    return [e for e in schema.tools
            if getattr(e, "advertised", True)
            and e.name not in SLOW_OPS_UNADJUDICATED]


def _classify(entries, invoke, synth_for):
    """Partition entries into RETURNED / TOLERATED / SKIPPED.

    RETURNED  -- the op was called and handed back a value.
    TOLERATED -- the op was reached and rejected the synthetic argument (any
                 exception that is not a binding failure).
    SKIPPED   -- at least one required param had no justifiable value.

    The SKIPPED rule mirrors the SHIPPED consumer's, deliberately.
    ``_synth_args_for_entry`` never returns ``None`` -- it returns a dict whose
    unfillable entries are the ``UNSYNTHESIZABLE`` sentinel -- so an earlier
    draft of this classifier tested ``synth is None`` and reported SKIPPED = 0
    on every run. A bucket that cannot be populated is not a partition, it is
    decoration, and it would have quietly filed 34 unsynthesizable ops as
    "reached and rejected" when the harness never built an argument for them.
    """
    unsynthesizable = _unsynthesizable_sentinel()
    returned, tolerated, skipped = set(), set(), set()
    for entry in entries:
        try:
            synth = synth_for(entry)
        except Exception:                                   # noqa: BLE001
            skipped.add(entry.name)
            continue
        if synth is None or any(v is unsynthesizable for v in synth.values()):
            skipped.add(entry.name)
            continue
        try:
            invoke(entry.name, synth)
        except Exception:                                   # noqa: BLE001
            tolerated.add(entry.name)
            continue
        returned.add(entry.name)
    return returned, tolerated, skipped


def _synth_source():
    """The SHIPPED consumer. Imported rather than hoisted: measured 2.03 s to
    import ``tests/test_mcp.py`` (the rc431 spec's decision threshold was 5 s),
    so hoisting ``_synth_args_for_entry`` into ``tests/synth_args.py`` and
    repointing its three consumers would be churn bought for nothing."""
    import test_mcp

    return test_mcp._synth_args_for_entry


def _unsynthesizable_sentinel():
    """The UNSYNTHESIZABLE sentinel **as the consumer sees it**.

    Do NOT replace this with ``from tools.example_args import UNSYNTHESIZABLE``.
    ``tools/example_args.py`` is reachable under two different module names on
    the test path -- ``tools.example_args`` and bare ``example_args`` -- and
    Python builds a SEPARATE module object for each, so the two sentinels are
    distinct objects and ``is`` between them is always False. An earlier draft
    of this file imported the wrong one and reported SKIPPED = 0 on every run
    while 34 entries genuinely carried the sentinel: a silent false zero, from
    an identity check that could not succeed. Taking the sentinel off the
    consumer guarantees both sides mean the same object."""
    import test_mcp

    return test_mcp._ea.UNSYNTHESIZABLE


def _safe_synth(entry):
    synth_for = _synth_source()
    try:
        return synth_for(entry)
    except Exception:                                       # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# THE SELF-PROOF -- runs first, and the floor test below is meaningless without it
# ---------------------------------------------------------------------------

def test_classifier_cannot_report_returns_when_every_op_raises():
    """MANDATORY CONTROL. Under a mutation where every op rejects every
    argument, the classifier MUST report zero RETURNED.

    This is the exact mutation under which the shipped parametrized gate stays
    green (0 failed, 617 passed). If this gate shared that blindness its floor
    would be decorative. The control makes the floor a measurement."""
    entries = _advertised_entries()
    assert entries, "no advertised entries -- the harness itself is broken"

    def always_rejects(_name, _args):
        raise ValueError("mutation: this op rejects every argument")

    returned, tolerated, skipped = _classify(entries, always_rejects, _safe_synth)
    assert not returned, (
        f"CLASSIFIER IS BLIND: it reported {len(returned)} RETURNED ops while "
        f"every op was mutated to reject every argument. Examples: "
        f"{sorted(returned)[:5]}"
    )
    assert tolerated, (
        "the mutation produced no TOLERATED ops either -- the classifier is "
        "not reaching the invoke path at all, so its zero above is vacuous"
    )


def test_skipped_bucket_is_populated_not_decorative():
    """CONTROL for the SKIPPED partition.

    A bucket that cannot be populated is decoration, not a partition. An earlier
    draft compared against the sentinel imported as ``tools.example_args``
    while the consumer holds the one from bare ``example_args`` -- two distinct
    module objects for one file -- so the identity test could never succeed and
    SKIPPED read 0 on every run while 34 entries genuinely carried it. This
    pins the population as non-empty, so the same false zero cannot return
    silently."""
    entries = _advertised_entries()
    synth_for = _synth_source()
    sentinel = _unsynthesizable_sentinel()
    carrying = [
        e.name for e in entries
        if any(v is sentinel for v in (synth_for(e) or {}).values())
    ]
    assert carrying, (
        "no advertised entry carries the UNSYNTHESIZABLE sentinel. Either the "
        "34-op unsynthesizable population really went to zero -- in which case "
        "CEIL_UNSYNTHESIZABLE_PARAMS in test_synth_args_provenance_rc430.py "
        "should have moved too -- or this file is again comparing against a "
        "sentinel from a different module object than the consumer's."
    )


def test_invocable_returned_floor_holds():
    """Every op in the committed set must still RETURN.

    Strict-zero on regressions; newly-returning ops are reported, not failed."""
    from srmech.mcp._tools import invoke_tool

    entries = _advertised_entries()
    returned, tolerated, skipped = _classify(entries, invoke_tool, _safe_synth)

    assert FLOOR_PATH.exists(), (
        # rc431 repair (`#T1129`): this said `pytest ... --regen-floor`, which
        # is not a pytest option -- the advertised recovery command ERRORS with
        # "unrecognized arguments". The real regeneration path is this file's
        # own __main__ block. An error message that hands the reader a command
        # that fails is worse than one that hands them nothing.
        f"{FLOOR_PATH.name} is missing -- regenerate it by running this file "
        f"directly (`python3 tests/{pathlib.Path(__file__).name}`, the "
        f"__main__ block writes the floor), then commit it"
    )
    floor = {
        line.strip()
        for line in FLOOR_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert floor, "the committed floor set is empty -- it would assert nothing"

    live_names = {e.name for e in entries}
    stale = floor - live_names
    regressed = (floor & live_names) - returned
    gained = returned - floor

    assert not regressed, (
        f"{len(regressed)} op(s) in the committed RETURNED set no longer "
        f"return under the shipped synth-args consumer:\n  "
        + "\n  ".join(sorted(regressed))
        + "\n\nThis is the failure the rc431 join exists to catch: the "
          "parametrized sibling stays GREEN when an op stops returning, "
          "because it only asserts the op was REACHED."
    )
    assert not stale, (
        f"{len(stale)} op(s) in the committed set are no longer advertised: "
        f"{sorted(stale)} -- refresh {FLOOR_PATH.name} in the commit that "
        f"removed them"
    )
    if gained:
        print(
            f"\n[rc431 floor] {len(gained)} newly-RETURNING op(s) not yet in "
            f"the committed set (reported, not failed): {sorted(gained)[:10]}"
            f"{' ...' if len(gained) > 10 else ''}"
        )
    print(
        f"\n[rc431 floor] srmech {srmech.__version__}  advertised={len(entries)}  "
        f"RETURNED={len(returned)}  TOLERATED={len(tolerated)}  "
        f"SKIPPED={len(skipped)}  floor={len(floor)}"
    )


if __name__ == "__main__":                                   # regeneration path
    from srmech.mcp._tools import invoke_tool

    ents = _advertised_entries()
    ret, tol, skp = _classify(ents, invoke_tool, _safe_synth)
    FLOOR_PATH.write_text(
        "# rc431 `#T1129` -- ops that RETURN under the shipped synth-args\n"
        "# consumer. A SET, not a count: a cardinal cannot name which op\n"
        "# regressed, and cannot see a swap that leaves the total unchanged.\n"
        "# Regenerate with:\n"
        "#   PYTHONPATH=docs/srmech/python:docs/srmech/python/tests \\\n"
        "#   python3 docs/srmech/python/tests/test_invocable_returned_floor_rc431.py\n"
        + "".join(f"{n}\n" for n in sorted(ret)),
        encoding="utf-8", newline="\n",
    )
    print(f"advertised={len(ents)} RETURNED={len(ret)} TOLERATED={len(tol)} "
          f"SKIPPED={len(skp)} -> wrote {FLOOR_PATH}")
