r"""rc471 (`#T1188`) — THE SHAPE LEVER, AND THE COUNTER-CONTROL THAT MAKES IT
PER-OP RATHER THAN POLICY.

``tools/demotion_probe.py``'s :data:`~demotion_probe.SHAPE_LEVER` overrides ONE
harvested parameter of ONE op — ``srmech.math.laplacian.recover_check_spectral``
gets ``vocab_size=16`` in place of the ledger's 64 — so the census's slowest
three rows are measured at a smaller block. This file is the proof that it is a
CHANGE OF SHAPE and not a DELETION OF SIGNAL.

⚠️ **WHY THIS IS NOT ``SLOW_SKIP`` RETURNING.** ``08d80a037`` shipped a roster
of ops the census was told to avoid, and rc465 deleted it after measuring what
it had cost: four rows of real signal (pure DEMOTED 117 -> 121, undeclared
67 -> 71, decided 219 -> 223). The probe's own comment states the test — *"A
roster keyed by how fast the machine is measures the machine"* — and the lever
passes it for a reason about the OP: ``recover_check_spectral`` takes ``max_dim``
as a CALLER BOUND on a principal submatrix (*"the first ``min(vocab_size,
max_dim)`` nodes + the edges within that block"*), so a smaller ``vocab_size``
asks the SAME question of a smaller block. Its sibling ``recover_check`` does
not bound, it REFUSES, and the identical shrink destroys its measurement
outright. Both halves are asserted here, in one file, because the second is
what stops the first becoming a policy.

MEASURED (WSL2 py3.12.3, PURE cell, ``HAS_NATIVE=False``), whole probe records
— verdict, ``leaf``, ``shape``, ``reason``, ``declares``, ``base_source``:

    recover_check_spectral   {charges DEMOTED, edges INSENSITIVE, weights DEMOTED}
        vocab_size   8     2.96 s     16 edges over  8 nodes in the block
        vocab_size  16     8.49 s     48 edges over 16 nodes      <- SHIPPED
        vocab_size  24    27.16 s     72 edges over 24 nodes
        vocab_size  32    71.66 s    112 edges over 32 nodes
        vocab_size  64   504.98 s    288 edges over 64 nodes  (the harvest)

    recover_check            {charges RAISED,  edges RAISED,      weights RAISED}
        vocab_size   8      0.22 s   <- the measurement is DESTROYED
        vocab_size  16      0.02 s
        vocab_size  32      0.02 s
        vocab_size  64     44.78 s   {charges DEMOTED, edges RAISED,
                                      weights DEMOTED}  <- the real answer

The wall clocks are NOT constants and are not asserted anywhere below; the
STRUCTURAL counts are, and those reproduced exactly. *(The 504.98 s reading was
taken while a second measurement contended for the same host; the plan's own
W0 rule is that no wall clock in this arc is quotable as a constant.)*

numpy-free. No ``abs()``. No stdlib ``fractions``.
"""

import json
import os
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import demotion_probe as _dp        # noqa: E402  (tools/ path set above)
import example_args as _ea          # noqa: E402
from srmech.introspect.tool_schema import get_tool_schema  # noqa: E402

#: The levered op, and the sibling that PROVES the lever is not policy.
LEVERED = "srmech.math.laplacian.recover_check_spectral"
COUNTER = "srmech.math.laplacian.recover_check"

#: Values re-measured LIVE by this file on every run. The lever's own value is
#: always among them (asserted below), and at least one OTHER measured-invariant
#: value is too — because once the census is regenerated under the lever, the
#: lever's own value agrees with the committed column by construction, and a
#: second shape is what keeps the invariance claim from becoming a tautology.
LIVE_SHAPES = (8, 16)

#: The shrink that DESTROYS the counter-control's measurement. Cheap: the op
#: refuses out-of-block indices instead of bounding them, so nothing is
#: computed (0.02-0.22 s for all three params together).
COUNTER_SHAPES = (8, 16, 32)

#: The harvested shape. Re-measuring the levered op here costs ~505 s in the
#: pure cell, which is why it is OPT-IN — see
#: :func:`test_the_harvested_shape_is_the_positive_control`. The COUNTER-control
#: at 64 is NOT opt-in: it is 44.78 s and it is the arm that can go red.
HARVESTED = 64

_ENV_FULL = "SRMECH_SHAPE_LEVER_FULL"

_CACHE: dict = {}


def _tools_by_name():
    if "t" not in _CACHE:
        _CACHE["t"] = {e.name: e for e in get_tool_schema().tools}
    return _CACHE["t"]


def _ledger():
    if "l" not in _CACHE:
        _CACHE["l"] = _ea.load_ledger()
    return _CACHE["l"]


def _manifest():
    if "m" not in _CACHE:
        _CACHE["m"] = _dp.load_manifest()
    return _CACHE["m"]


def _committed(op):
    """``{param: verdict}`` from THIS cell's committed column."""
    cel = _dp.cell()
    _meta, rows = _manifest()
    out = {}
    for r in rows:
        if r["op"] == op and r.get(cel):
            out[r["param"]] = r[cel]["verdict"]
    return out


def _probe_at(op, **overrides):
    """Run the SHIPPED probe on one op with the harvest overridden.

    ``lever={}`` disables :data:`demotion_probe.SHAPE_LEVER` so the override
    here is the only one in play — otherwise the lever would silently win and
    every shape below would measure 16.
    """
    rows = dict(_ledger())
    row = dict(rows.get(op) or {})
    args = dict(row.get("args") or {})
    args.update(overrides)
    row["args"] = args
    rows[op] = row
    recs = _dp.probe_op(_tools_by_name()[op], rows, lever={})
    return {r["param"]: r for r in recs}


# ── (1) the lever is DECLARED, and every claim it makes is checkable ──────────

def test_the_lever_names_one_op_and_a_parameter_that_exists() -> None:
    """Structural, milliseconds. A lever pointing at a name nobody binds is a
    constant that reads as a policy and does nothing."""
    lever = _dp.SHAPE_LEVER
    assert list(lever) == [LEVERED], (
        f"SHAPE_LEVER names {sorted(lever)}; this file proves the invariance "
        f"of exactly {LEVERED!r} and the DESTRUCTION of {COUNTER!r} by the "
        f"same shrink. Any further op needs its own measured invariance proof "
        f"— propagate_sparse::weights, relational_structure::weights and "
        f"ground_state_flux_response::fluxes are UNMEASURED on this axis, and "
        f"two of the eight slow rows that WERE tested came out opposite ways.")
    entry = _tools_by_name()[LEVERED]
    pnames = {p.name for p in (entry.parameters or ())}
    harvest = dict((_ledger().get(LEVERED) or {}).get("args") or {})
    for k, v in lever[LEVERED].items():
        assert k in pnames, f"{LEVERED} has no registry parameter {k!r}"
        assert k in harvest, (
            f"{k!r} is not in the harvested binding, so the lever would be "
            f"SYNTHESIS wearing a lever's name — and `base_source` would then "
            f"say 'ledger' about a value no ledger holds")
        measured = _dp.SHAPE_LEVER_MEASURED_INVARIANT[LEVERED][k]
        assert v in measured, (
            f"SHAPE_LEVER sets {k}={v}, which is not one of the measured "
            f"values {measured}. A lever value nobody measured is a shape "
            f"nobody proved verdict-preserving.")
    assert lever[LEVERED]["vocab_size"] in LIVE_SHAPES, (
        "the shipped lever value must be one of the shapes this file "
        "re-measures LIVE, or nothing here exercises it")
    assert COUNTER not in lever, (
        f"{COUNTER} is levered. It must not be: the same shrink collapses all "
        f"three of its params to RAISED — see the counter-control below.")


def test_the_lever_is_in_the_probe_signature() -> None:
    """A verdict-deciding knob outside :data:`demotion_probe.PROBE_SPEC` moves
    the instrument without moving its digest — the blind spot the probe
    signature exists to close, reproduced one level in."""
    members = dict(_dp.PROBE_SPEC)
    assert "shape_lever" in members, "SHAPE_LEVER is not in PROBE_SPEC"
    assert members["shape_lever"] is _dp.SHAPE_LEVER, (
        "PROBE_SPEC binds a COPY of SHAPE_LEVER, so the digest would move "
        "while the instrument did not")


def test_the_lever_is_applied_by_default_and_disablable() -> None:
    """The mechanism, not the verdict: ``_base_for`` overrides the harvest, and
    ``lever={}`` turns it off — which is what every measurement below needs."""
    entry = _tools_by_name()[LEVERED]
    on, _clean, src_on = _dp._base_for(entry, _ledger())
    off, _clean2, src_off = _dp._base_for(entry, _ledger(), lever={})
    assert on["vocab_size"] == _dp.SHAPE_LEVER[LEVERED]["vocab_size"]
    assert off["vocab_size"] == HARVESTED, (
        f"the raw harvest is {off['vocab_size']}, not {HARVESTED} — the "
        f"ledger moved and every figure in this file was taken against 64")
    assert src_on == src_off == "ledger", (
        "the lever must not change base_source: the OTHER parameters are still "
        "the ledger's")
    counter = _dp._base_for(_tools_by_name()[COUNTER], _ledger())[0]
    assert counter["vocab_size"] == HARVESTED, (
        f"{COUNTER} was levered; it must keep its harvested shape")


# ── (2) the invariance, LIVE, at two shapes ──────────────────────────────────

@pytest.mark.parametrize("vocab_size", LIVE_SHAPES)
def test_the_shape_lever_is_verdict_preserving(vocab_size) -> None:
    """THE CLAIM. Same verdicts, same leaf, same shape label, same declares.

    Measured against THIS cell's committed column rather than a literal, so it
    cannot drift away from the artefact it is a claim about. TWO shapes run,
    and that is deliberate: after the census is regenerated under the lever,
    the lever's own value agrees with the committed column by construction, and
    the other value is what keeps this from being a tautology.

    Cost, PURE cell: 2.96 s at 8, 8.49 s at 16. Native is far cheaper (the
    probe's own comment records 0.15-6.7 s for the whole recover_check family
    there against 53-526 s pure).
    """
    committed = _committed(LEVERED)
    assert committed, (
        f"{LEVERED} has no committed column in this cell; the census must be "
        f"measured before this can be a claim about it")
    got = _probe_at(LEVERED, vocab_size=vocab_size)
    assert set(got) == set(committed), (
        f"the probe returned params {sorted(got)} and the manifest holds "
        f"{sorted(committed)}")
    diffs = {p: (got[p]["verdict"], committed[p])
             for p in committed if got[p]["verdict"] != committed[p]}
    assert not diffs, (
        f"the shape lever is NOT verdict-preserving for {LEVERED} at "
        f"vocab_size={vocab_size}: {diffs}. That makes the saving a DELETED "
        f"MEASUREMENT — the rc465 SLOW_SKIP mistake in new clothes. Remove "
        f"the op from SHAPE_LEVER rather than moving this assertion.")


def test_the_levered_row_is_field_identical_not_merely_verdict_identical() -> None:
    """Stronger than the verdict, and it is what was MEASURED: at the levered
    shape the whole record — ``leaf``, ``shape``, ``reason``, ``declares``,
    ``base_source`` — matches the committed row byte for byte. A verdict that
    agreed while the deciding LEAF moved would be a different measurement
    wearing the same word."""
    cel = _dp.cell()
    _meta, rows = _manifest()
    committed = {r["param"]: r for r in rows
                 if r["op"] == LEVERED and r.get(cel)}
    got = _probe_at(LEVERED, **_dp.SHAPE_LEVER[LEVERED])
    fields = ("verdict", "reason", "leaf", "shape", "declares")
    for p, crow in sorted(committed.items()):
        live = {f: got[p][f] for f in fields if f in got[p]}
        comm = {f: crow[cel][f] for f in fields if f in crow[cel]}
        assert live == comm, (
            f"{LEVERED}::{p} at the levered shape differs from the committed "
            f"{cel} column in more than the verdict:\n"
            f"  live      {json.dumps(live, sort_keys=True)}\n"
            f"  committed {json.dumps(comm, sort_keys=True)}")
        assert crow.get("base_source") == "ledger"


# ── (3) THE COUNTER-CONTROL — this is what makes the lever per-op ────────────

@pytest.mark.parametrize("vocab_size", COUNTER_SHAPES)
def test_the_same_shrink_DESTROYS_the_counter_control(vocab_size) -> None:
    """``recover_check`` is not levered, and this is why.

    All three of its params collapse to ``RAISED`` under the identical shrink —
    it refuses an edge naming a node outside the block instead of bounding the
    block, so nothing is computed and no carrier question is asked. Total cost
    0.02-0.22 s for all three, which is itself the tell: a shrink that makes a
    row FAST by making it answer nothing is the deletion this lever must not be.

    ⚠️ If this goes GREEN in the other direction — ``recover_check`` becoming
    shape-invariant — the test is doing its job and someone must re-read the
    rule. It is not an assertion to relax.
    """
    got = _probe_at(COUNTER, vocab_size=vocab_size)
    verdicts = {p: r["verdict"] for p, r in got.items()}
    assert set(verdicts.values()) == {"RAISED"}, (
        f"{COUNTER} at vocab_size={vocab_size} reads {verdicts}; MEASURED at "
        f"rc471 it is RAISED on all three. If it now ANSWERS at a reduced "
        f"shape, the lever's per-op argument needs re-reading — do not widen "
        f"SHAPE_LEVER on the strength of this test turning green.")


def test_the_counter_control_ANSWERS_at_its_harvested_shape() -> None:
    """The other half of the pair, and the one that makes it a control rather
    than a claim that an op is broken.

    At the harvested 64 the same op reproduces its committed column —
    ``{charges DEMOTED, edges RAISED, weights DEMOTED}`` — in 44.78 s (PURE).
    So the all-RAISED reading above is a fact about the SHRINK, not about the
    op. This arm is NOT opt-in: an instrument that cannot return otherwise is
    not a measurement, and this is the otherwise.
    """
    committed = _committed(COUNTER)
    assert committed, f"{COUNTER} has no committed column in this cell"
    got = _probe_at(COUNTER, vocab_size=HARVESTED)
    verdicts = {p: r["verdict"] for p, r in got.items()}
    assert verdicts == committed, (
        f"{COUNTER} at its harvested vocab_size={HARVESTED} reads {verdicts} "
        f"and the committed {_dp.cell()} column holds {committed}")
    assert set(verdicts.values()) != {"RAISED"}, (
        "the counter-control is vacuous: it reads all-RAISED at the harvested "
        "shape too, so the shrink destroyed nothing")


# ── (4) the harvested-shape positive control — OPT-IN, and said so ──────────

def test_the_harvested_shape_is_the_positive_control() -> None:
    """The levered op at its ORIGINAL 64. MEASURED: 504.98 s in the pure cell,
    ``{charges DEMOTED, edges INSENSITIVE, weights DEMOTED}`` — the committed
    triple, unchanged.

    ⚠️ **OPT-IN, AND DISCLOSED RATHER THAN QUIETLY SKIPPED.** Eight and a half
    minutes of a CI job for one assertion is the cost that made the census a
    deliberate tool run in the first place (rc465), and the same argument
    applies one level down. What runs on every CI run instead is: TWO live
    shapes for the levered op, and BOTH directions of the counter-control
    including its 44.78 s harvested arm. Run this one deliberately::

        SRMECH_SHAPE_LEVER_FULL=1 python3 -m pytest \\
            tests/test_shape_lever_rc471.py -k harvested

    It is named in the rc471 CHANGELOG entry as the one arm this file does not
    pay for on every run.
    """
    if os.environ.get(_ENV_FULL) != "1":
        pytest.skip(
            f"{_ENV_FULL}!=1 — the harvested-64 arm costs 504.98 s in the "
            f"pure cell (MEASURED). The two live shapes and both counter-"
            f"control arms ran; this is the only arm skipped, and it is "
            f"disclosed in the rc471 CHANGELOG entry rather than absorbed.")
    committed = _committed(LEVERED)
    got = _probe_at(LEVERED, vocab_size=HARVESTED)
    verdicts = {p: r["verdict"] for p, r in got.items()}
    assert verdicts == committed, (
        f"at the HARVESTED vocab_size={HARVESTED} {LEVERED} reads {verdicts} "
        f"and the committed {_dp.cell()} column holds {committed}. The lever's "
        f"whole argument is that these agree.")
