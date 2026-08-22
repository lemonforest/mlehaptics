"""v0.9.0rc452 (`#T1166`) — THE EMITTED-KIND GATE.

WHAT DEFECT CLASS THIS CLOSES, as distinct from the instance rc452 fixes.
``q`` was a DECLARED wire kind that the value-parity comparator had never once
seen. The bijection pin next door (``test_wire_kind_bijection_is_pinned_on_both
_sides``) was green throughout, because it parses SOURCE: the C writer names
``q`` and the Python reader branches on ``q``, so a kind can be declared on both
sides, emitted 39 times a run by two live attested catalogs, and still be
invisible to every instrument that judges values. rc451 closed that for ``t``
with a single hand-written assertion about one chain. This closes it for the
SET, so no kind can go dark again without a red.

THREE TRAPS THIS ARC HAS ALREADY FALLEN INTO, and how each is closed here:

1. **A CENSUS THAT PRINTS CLEAN HAVING PARSED NOTHING.** Every parse below
   asserts its own result is non-empty, and the declared set is cross-checked
   against a floor. An empty parse is a FAILURE, never agreement.
2. **THE FLAT WALK.** Two prior instruments in this arc walked the descriptor
   tree at the TOP LEVEL ONLY and reported coverage of 54% and 62.6% of what
   was actually there — one of them concluding a kind was dead while 39 of it
   were on the wire, nested one level down inside a container. The walk here is
   FULL DEPTH, and it reconciles its node count against the population so a
   walk that stops early is arithmetic that does not close.
3. **GREPPING.** The declared set comes from the same scoped source parse the
   rc450 bijection uses, not from a text search over the file.

WHAT IS ASSERTED:
  * ``q`` IS emitted by an executed proof case. (The instance.)
  * the UNEMITTED residual is pinned as a DOWN-ONLY ceiling. (The class.)
  * the walk's own totals reconcile, and every case that RAISES is classified
    rather than dropped — a population that silently shrinks is the quieter
    green this arc keeps finding.

⚠️ THE RESIDUAL IS MEASURED HERE, NOT INHERITED. rc452's plan predicted exactly
``{n, s}``. The workshops DISAGREED about ``s`` — one executed run reported it
emitted, another reported 0 of 98 — so the number is re-derived below and the
pin states what was actually seen. Every headline figure in this arc has been
wrong at least once.

numpy-free.
"""
from __future__ import annotations

import ctypes
import json
from pathlib import Path

import pytest

import srmech._native as _native
from srmech.cascade import compose as _compose
from srmech.dsl._cascade_chain import cascade_chain_specs
from srmech.math.q import Q as _Q

from _native_gate import require_native
# THE SAME POPULATION THE COMPARATOR USES, imported rather than re-derived.
# A census over its own private enumeration could report full coverage of a set
# the comparator never sees — which is the exact shape of the defect this file
# is named after, one level up.
#
# ``classify`` joins the import at rc452 for the VALUE axis added at the foot of
# this file. It is imported rather than reimplemented for the reason rc450
# states in its own docstring: that module makes ``_bits`` reachable only
# through ``classify`` so a strict-witness / lax-population split is
# inexpressible, and writing a second comparator here would re-open exactly that
# split one file over.
from test_c_cascade_value_parity_rc450 import (
    EXPECTED_WIRE_KINDS,
    _c_emitted_kinds,
    _chain_only,
    _population,
    classify,
)

# ── TWO POPULATIONS, AND THE GAP BETWEEN THEM IS THE FINDING ────────────────
#
# THE ARC OPENED ON A CLAIM THAT TURNED OUT TO BE ABOUT THE WRONG SET. "`q` is
# emitted by nothing" is FALSE tree-wide and TRUE of the comparator, and rc452
# measures both rather than picking the convenient one:
#
#   POPULATION A — the CASCADE-CATALOG proof cases. This is the set
#       tests/test_c_cascade_value_parity_rc450.py compares. Every executable
#       [cascade] descriptor x every [[cascade.chain.proof_cases]] row.
#   POPULATION B — the AMSC CATALOG operator_chains (pi_digits,
#       asymptotic_calculus, cosmos_validation). Real shipped apparatus, run
#       through the SHIPPED native runner, and the source of the "39 live q
#       emissions" figure this ruling inherited rather than re-derived.
#
# MEASURED at rc452: `q` is emitted by population B and by NO row of population
# A. That gap is exactly why the collapse survived — every value-level
# instrument in the tree judges A, and every exact rational crosses in B.

#: Kinds an executed row of EITHER population must put on the wire. `q` is the
#: rc452 entry and the reason this file exists.
REQUIRED_EMITTED_KINDS = frozenset({"f", "i", "l", "t", "q"})

#: DOWN-ONLY, over the UNION of both populations. A kind here is DECLARED by
#: both projections and emitted by NO executed row anywhere. Draining one is a
#: deliberate edit; ADDING one means a kind went dark and this gate names it.
#:
#: MEASURED at rc452, and the measurement CORRECTED THE PLAN. rc452's plan
#: predicted this residual would be ``{n, s}``, inherited from Config D's
#: census; Config B's executed run had reported ``s`` EMITTED, and the plan
#: chose between them rather than re-deriving. Both were right about different
#: sets, which is why the disagreement never resolved:
#:
#:   s  (CR_STR)   — EMITTED, by population B. ``pi_cascade_digits`` returns a
#:                   digit STRING and its rows run in C. D's "s = 0 of 98" was
#:                   true of population A, where no chain returns a string.
#:                   NOT in this pin. The union residual is {n} ALONE.
#:   n  (CR_NONE)  — genuinely unemitted by BOTH. Three workshops independently
#:                   failed to find any producer. Closable by auditing every
#:                   cr_op_* return path for a CR_NONE result; rc452 does not.
#:
#: Reported rather than reconciled: every headline figure in this arc has been
#: wrong at least once, and this one was wrong in the plan.
CEIL_UNEMITTED_KINDS = frozenset({"n"})

#: DOWN-ONLY, and NARROWER: kinds population A alone never emits. `q` is here
#: because rc452 does NOT close it, and the reason is structural rather than an
#: oversight: every [cascade] descriptor must name a real DSL-resolvable op
#: (tests/test_dsl.py pins the set), and there is no rational-family cascade
#: op — the Class-N rationals are catalogued as AMSC operator_chains, not as
#: [cascade] descriptors. Putting a `q` row into population A therefore costs a
#: NEW PUBLIC CALLABLE plus its descriptor, which ripples the tool-count axis
#: across ~73 test files. Priced, named, deferred — see the gap-ledger row
#: `value_parity_population_has_no_rational_terminal_chain`.
CEIL_UNEMITTED_IN_POPULATION_A = frozenset({"n", "s", "q"})

#: DOWN-ONLY. Proof cases that RAISE before the C projection is reached.
#:
#: MEASURED at rc452: **0**, with an empty ``raisers`` list. This pin stood at 8
#: on the strength of a "5 raise on a kuramoto ctx KeyError" figure that does not
#: reproduce — see :func:`test_every_raising_case_is_named_not_dropped`. Raising
#: it again is a deliberate edit that must name the raisers and say why they
#: cannot be fixed instead.
CEIL_CASES_RAISING_BEFORE_EXECUTION = 0


# ── the walk ────────────────────────────────────────────────────────────────

def _walk_kinds(desc, tally, depth=0, max_depth=64):
    """Tally every ``k`` in a descriptor tree, AT FULL DEPTH.

    Returns the number of descriptor NODES visited, which the caller
    reconciles. A flat walk is the documented trap: it sees only the outermost
    kind, so a container of rationals reads as one ``l`` and zero ``q``.
    """
    if depth > max_depth or not isinstance(desc, dict):
        return 0
    k = desc.get("k")
    if isinstance(k, str):
        tally[k] = tally.get(k, 0) + 1
    seen = 1
    payload = desc.get("v")
    if isinstance(payload, list):
        for item in payload:
            seen += _walk_kinds(item, tally, depth + 1, max_depth)
    return seen


def test_the_walk_is_full_depth_not_flat():
    """SELF-CHECK on the instrument, before it is believed about anything.

    A flat walk over this fixture reports ``{"t": 1}`` and nothing else. The
    fixture is hand-built so the check does not depend on the population
    containing a nested case.
    """
    nested = {"k": "t", "v": [
        {"k": "i", "v": "3"},
        {"d": "6", "k": "q", "n": "5"},
        {"k": "l", "v": [{"k": "f", "v": 1.5}, {"d": "2", "k": "q", "n": "1"}]},
    ]}
    tally = {}
    nodes = _walk_kinds(nested, tally)
    assert tally == {"t": 1, "i": 1, "q": 2, "l": 1, "f": 1}, tally
    assert nodes == 6, nodes
    assert sum(tally.values()) == nodes, (tally, nodes)


# ── the executed population ─────────────────────────────────────────────────

def _c_run(chain_dict, ctx):
    lib = _compose._compose_lib("srmech_chain_run",
                                "srmech_chain_run_arena_bytes")
    assert lib is not None, (
        "the chain-run symbols are absent from a loaded library — a different "
        "failure, and it must not read as a skip")
    try:
        cj = json.dumps(chain_dict, ensure_ascii=False,
                        allow_nan=False).encode("utf-8")
        xj = json.dumps({"inputs": ctx}, ensure_ascii=False,
                        allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        return None, b"", False
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, ws_bytes,
                                  out, out_cap, ctypes.byref(out_len)))
    return rc, out.raw[:out_len.value], True


def _census(skip_chain: str | None = None):
    """Run every executable chain's every proof case and tally emitted kinds.

    Returns a dict with the tally AND the accounting: how many cases were
    declared, how many produced a wire, how many the C projection declined, how
    many could not be spelled as JSON, and how many RAISED. Every case lands in
    exactly one bucket — a case that vanished is the failure mode, not a
    smaller denominator.
    """
    tally: dict = {}
    acc = {"declared": 0, "emitted": 0, "declined": 0, "unserialisable": 0,
           "raised": 0, "nodes": 0}
    raisers = []
    for name, _variant, entry, _spec, j, inputs in _population():
        if skip_chain is not None and name == skip_chain:
            continue
        acc["declared"] += 1
        try:
            rc, wire, ok = _c_run(_chain_only(entry), inputs)
        except Exception as exc:                       # noqa: BLE001
            raisers.append((name, j, repr(exc)))
            acc["raised"] += 1
            continue
        if not ok:
            acc["unserialisable"] += 1
            continue
        if rc != 0 or not wire:
            acc["declined"] += 1
            continue
        desc = _compose._srmech_json.loads(wire.decode("utf-8"))
        acc["nodes"] += _walk_kinds(desc, tally)
        acc["emitted"] += 1
    acc["raisers"] = raisers
    return tally, acc


def _census_b():
    """POPULATION B — the AMSC catalog operator_chains, run through the SHIPPED
    native path and tallied by EMITTED KIND.

    The chain wire is re-run here rather than read off ``_run_chain_native``'s
    return, because that function hands back the RECONSTRUCTED value and the
    subject of this file is the kind on the wire. Its ctx shape is mirrored
    exactly — ``{"row": ..., "inputs": ...}`` — since these chains address their
    operands as ``@row.*`` and a ctx-only harness would decline every one of
    them and report a clean zero.
    """
    from srmech.amsc import catalog
    tally: dict = {}
    acc = {"declared": 0, "emitted": 0, "declined": 0, "nodes": 0}
    lib = _compose._compose_lib("srmech_chain_run",
                                "srmech_chain_run_arena_bytes")
    assert lib is not None, "chain-run symbols absent — not a skip"
    for src in ("pi_digits", "asymptotic_calculus", "cosmos_validation"):
        chains = {c.name: c for c in catalog._load_catalog_chains(src)}
        ds = catalog.get_attested_dataset(src)
        for row in ds.get("rows", []):
            data = dict(row.get("data") or {})
            spec = chains.get(data.get("chain_id"))
            if spec is None:
                continue
            acc["declared"] += 1
            chain_dict = _compose._spec_to_chain_dict(spec)
            ctx, ok = _compose._drop_oversized_ints({"row": data, "inputs": {}})
            if not ok:
                acc["declined"] += 1
                continue
            try:
                cj = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
                xj = json.dumps(ctx, ensure_ascii=False).encode("utf-8")
            except (TypeError, ValueError):
                acc["declined"] += 1
                continue
            n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
            ws = (ctypes.c_char * n)()
            cap = max(n // 2, 16384)
            out = (ctypes.c_char * cap)()
            ol = ctypes.c_size_t()
            rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                          out, cap, ctypes.byref(ol)))
            wire = out.raw[:ol.value]
            if rc != 0 or not wire:
                acc["declined"] += 1
                continue
            desc = _compose._srmech_json.loads(wire.decode("utf-8"))
            acc["nodes"] += _walk_kinds(desc, tally)
            acc["emitted"] += 1
    return tally, acc


@pytest.fixture(scope="module")
def census():
    """POPULATION A — the comparator's."""
    require_native("the emitted-kind census (it measures the C wire)")
    return _census()


@pytest.fixture(scope="module")
def census_b():
    """POPULATION B — the shipped AMSC catalog apparatus."""
    require_native("the emitted-kind census (it measures the C wire)")
    return _census_b()


def test_the_census_accounts_for_every_declared_case(census):
    """Arithmetic that closes, or the tally means nothing.

    ``declared == emitted + declined + unserialisable + raised``, and the node
    count equals the summed tally. A population that silently shrank would
    otherwise raise the emitted FRACTION while measuring less.
    """
    tally, acc = census
    assert acc["declared"] > 0, "the census ran zero cases — it measured nothing"
    total = (acc["emitted"] + acc["declined"] + acc["unserialisable"]
             + acc["raised"])
    assert total == acc["declared"], (acc,)
    assert sum(tally.values()) == acc["nodes"], (tally, acc["nodes"])
    print("\n  emitted-kind census @ ABI %s: %s" % (_native.NATIVE_ABI_VERSION, acc))
    print("  kinds: %s" % (dict(sorted(tally.items())),))


def test_every_raising_case_is_named_not_dropped(census):
    """A raise is a CLASSIFIED outcome with a name attached.

    ⚠️ THE FIGURE THIS DOCSTRING CARRIED DOES NOT REPRODUCE, and the pin it
    justified was slack by eight. Through rc452-s5 this read "5 of the
    value-parity population's proof cases raise before execution on an unrelated
    kuramoto ctx KeyError" and pinned ``raised <= 8``. RE-MEASURED on the shipped
    tree at ABI 21, printed by the sibling census test:

        {'declared': 98, 'emitted': 48, 'declined': 46,
         'unserialisable': 4, 'raised': 0, 'raisers': []}

    ``raised`` is **0** and ``raisers`` is **empty**. A decline and an
    unserialisable ctx are classified outcomes with their own buckets and
    neither is a raise, so the "5 kuramoto KeyErrors" were a figure carried
    across from a differently-shaped harness, not a property of this population.
    It is corrected here rather than left to drift, because this file's own
    header says every headline figure in this arc has been wrong at least once
    and this one was.

    THE CEILING DRAINS 8 -> 0 in the same edit that corrects the prose. That is
    the point of the correction rather than a bonus: a pin eight above a measured
    zero cannot report the drift it exists to report — eight proof cases could
    start raising, the emitted FRACTION would climb because the denominator
    shrank, and this gate would stay green through all of it.
    """
    _tally, acc = census
    assert acc["raised"] <= CEIL_CASES_RAISING_BEFORE_EXECUTION, (
        "%d case(s) now RAISE before execution where the pinned ceiling is %d. "
        "That is not this gate's defect to fix, but it is this gate's job to "
        "say it moved — and a raising case is one the kind census never sees, "
        "so every tally in this file loses a row to it: %r"
        % (acc["raised"], CEIL_CASES_RAISING_BEFORE_EXECUTION, acc["raisers"]))


def test_the_declared_kind_set_is_read_from_source_and_is_not_empty():
    """The floor under every claim below."""
    declared = _c_emitted_kinds()
    assert declared == set(EXPECTED_WIRE_KINDS), (sorted(declared),)
    assert len(declared) >= 7, (
        "the C writer declares %d kinds; the floor is 7. A parse that found "
        "fewer has stopped matching, and an under-parse makes the residual "
        "look smaller than it is." % len(declared))


def test_population_b_accounts_for_every_row(census_b):
    """The AMSC census closes its own arithmetic too, and is not empty.

    An earlier shape of this probe passed the row payload as ``inputs`` instead
    of as ``row``. Every one of the 51 rows declined, the tally came back ``{}``,
    and the honest-looking conclusion was "q is emitted by nothing" — the
    instrument's own defect wearing the finding's clothes. The non-empty floor
    below is what refuses that reading.
    """
    tally, acc = census_b
    assert acc["declared"] > 0, "population B is empty — it measured nothing"
    assert acc["emitted"] + acc["declined"] == acc["declared"], acc
    assert acc["emitted"] > 0, (
        "not a single AMSC catalog chain ran in C (%r). A zero tally here is "
        "an instrument failure, not a finding about the wire." % (acc,))
    assert sum(tally.values()) == acc["nodes"], (tally, acc["nodes"])
    print("\n  population B (AMSC operator_chains): %s" % (acc,))
    print("  kinds: %s" % (dict(sorted(tally.items())),))


def test_q_is_emitted_by_an_executed_shipped_chain(census_b):
    """THE INSTANCE. ``q`` must appear on a wire an executed chain produced.

    Not "the reader can read it", not "the writer names it", not "classify
    returned BYTE_IDENTICAL". All three were TRUE through rc451 while the kind
    was, for every value-level instrument in this tree, invisible.

    HOW IT RETURNS OTHERWISE: it already did. Run at the start of rc452-s5,
    before population B was added, this file's census covered population A only
    and FAILED here with ``residual ['n', 'q', 's']`` — the recorded red that
    proves the gate is a measurement.
    """
    tally, _acc = census_b
    assert tally.get("q", 0) > 0, (
        "no executed shipped chain emitted the `q` kind anywhere. Emitted: %s"
        % (dict(sorted(tally.items())),))


def test_every_required_kind_is_emitted_somewhere(census, census_b):
    """The SET, over the union of both populations."""
    emitted = set(census[0]) | set(census_b[0])
    missing = sorted(REQUIRED_EMITTED_KINDS - emitted)
    assert not missing, (
        "declared-and-required kinds emitted by NOTHING in either population: "
        "%s. A: %s  B: %s"
        % (missing, dict(sorted(census[0].items())),
           dict(sorted(census_b[0].items()))))


def test_the_unemitted_residual_is_pinned_down_only(census, census_b):
    """THE CLASS, over the UNION. Which declared kinds nothing produces.

    DOWN-ONLY: draining an entry is a deliberate edit that lands with the row
    that drains it. ADDING one means a kind went dark, which is the condition
    this file exists to make impossible to ship quietly.
    """
    emitted = set(census[0]) | set(census_b[0])
    declared = _c_emitted_kinds()
    residual = frozenset(declared) - emitted
    assert residual <= CEIL_UNEMITTED_KINDS, (
        "a DECLARED wire kind is emitted by NOTHING and is not in the pinned "
        "residual: %s. Residual %s, pin %s, emitted %s."
        % (sorted(residual - CEIL_UNEMITTED_KINDS), sorted(residual),
           sorted(CEIL_UNEMITTED_KINDS), sorted(emitted)))
    drained = sorted(CEIL_UNEMITTED_KINDS - residual)
    assert not drained, (
        "kinds %s are now emitted but still pinned as unemitted. Down-only "
        "means the pin drains in the same commit as the row that drains it: "
        "remove them and say which row did it." % (drained,))


def test_the_comparators_own_blind_spot_is_pinned_and_named(census):
    """THE GAP rc452 does NOT close, pinned so it cannot widen quietly.

    Population A — the set the value-parity comparator actually judges — emits
    no ``q`` at all, and rc452 leaves it that way. The reason is structural,
    not an oversight: every ``[cascade]`` descriptor must name a real
    DSL-resolvable op (``tests/test_dsl.py`` pins that set), and there is no
    rational-family cascade op — the Class-N rationals are catalogued as AMSC
    operator_chains instead. A ``q`` row in population A therefore costs a new
    public callable plus its descriptor, which moves the tool-count axis across
    ~73 test files. Priced, named, deferred.

    ⚠️ rc452's plan called for exactly that row ("a proof-case chain puts q into
    the value-parity population"). It is not buildable as specified, and this
    pin is the honest form of that: the gap is a ratchet with a stated closing
    condition rather than a sentence in a report.
    """
    tally, _acc = census
    declared = _c_emitted_kinds()
    residual = frozenset(declared) - set(tally)
    assert residual <= CEIL_UNEMITTED_IN_POPULATION_A, (
        "population A stopped emitting a kind it used to: %s"
        % (sorted(residual - CEIL_UNEMITTED_IN_POPULATION_A),))
    drained = sorted(CEIL_UNEMITTED_IN_POPULATION_A - residual)
    assert not drained, (
        "population A now emits %s. Drain the pin in the same commit as the "
        "descriptor that did it, and close the gap-ledger row "
        "`value_parity_population_has_no_rational_terminal_chain`." % (drained,))

# ══════════════════════════════════════════════════════════════════════════════
# rc452 (`#T1166`) — POPULATION B, BY VALUE AND BY TYPE.
#
# WHAT THIS FILE ALREADY MEASURED, AND WHAT IT DID NOT
# ----------------------------------------------------
# Everything above judges population B by EMITTED KIND: it reads `k` off the
# wire and tallies. That is a statement about what C WROTE. It is not a
# statement about what either projection BUILT from it — `_walk_kinds` never
# calls `_reconstruct_value`, so a reader-side collapse is invisible to every
# assertion above.
#
# rc452 moved exactly that seam: `_reconstruct_value` now rebuilds kind `q` as
# `Q` where it used to return a `(num, den)` tuple. All 39 live `q` rows are in
# THIS population and none are in population A (CEIL_UNEMITTED_IN_POPULATION_A
# pins that). So the one axis rc452 changed had no value-level gate over the
# rows it changed.
#
# ⚠️ TWO INDEPENDENT REASONS THE EXISTING GATE CANNOT SEE THIS, and the second
# is the one that matters more.
#
#   (1) `==` IS COERCIVE. tests/test_chain_run_c_rc174 compares these same rows
#       with `assert native == pure`. `Q.__eq__` goes through `_as_pair` and
#       cross-multiplies, so ALL of these are True:
#
#           Q(5, 6) == (5, 6)      Q(5, 6) == [5, 6]
#           Q(5, 6) == Q(10, 12)   Q(3, 1) == 3        Q(3, 1) == 3.0
#
#   (2) ⚠️ THE TWO PROJECTIONS SHARE THE READER, so on this population a
#       C-vs-Python value comparison CANNOT detect a reader-side collapse AT
#       ALL — not with `==`, and not with the typed comparator either. The pure
#       Class-N ops dispatch to native per-op and rebuild through the SAME
#       `_reconstruct_value`. MEASURED: with the `q` arm reverted to a tuple for
#       denominators > 1000, the C side returns tuples AND `run_chain` returns
#       tuples for the same rows, so `classify` reports 51/51 BYTE_IDENTICAL.
#       The collapse is SYMMETRIC. A parity gate compares a thing to itself
#       here, which is this arc's named defect wearing the shape of a
#       cross-projection check.
#
# Therefore the load-bearing assertion below is NOT the divergence one — it is
# `test_the_q_rows_are_present_and_are_the_exact_carrier`, which checks the
# rebuilt TYPE against the CONTRACT rather than against the other projection.
# An independent expectation is the only instrument that can still return
# otherwise when both projections move together.
#
# MEASURED COST OF NOT HAVING THIS: the d > 1000 revert corrupts 32 of the 39
# live rows and leaves tests/test_chain_run_c_rc174 (72 passed), this file's
# kind census, the rc450 comparator and the rc452 pipeline test ALL GREEN —
# 633 tests across the entire chain-run surface, zero failures.
#
# WHY `classify` AND NOT A LOCAL COMPARATOR. rc450 makes `_bits` reachable only
# through `classify` inside its own module so a strict-witness / lax-population
# split is inexpressible. Importing `classify` here keeps ONE comparator across
# both populations; writing a second one is the split that discipline forbids,
# one file over.

#: DOWN-ONLY FLOOR, not a fixed count. Population B's row count grows when a
#: catalog gains rows, and pinning equality would red on a legitimate addition
#: while a DISAPPEARING row is the actual failure mode. MEASURED at rc452: 39.
FLOOR_Q_ROWS_POPULATION_B = 39

#: Population-B rows where the C projection and the pure projection disagree.
#: ⚠️ Read the scope note above before trusting a green here: this axis is real
#: (a C-SIDE fault does move it — reverting the C writer's `q` emission reds 50
#: of 72 in test_chain_run_c_rc174) but it is BLIND to a shared-reader collapse.
CEIL_POPULATION_B_DIVERGENT = 0


def _census_b_valued():
    """POPULATION B again — but carrying the VALUE from BOTH projections.

    Mirrors :func:`_census_b`'s row derivation exactly (same sources, same ctx
    shape, same spec lookup) and additionally runs the PURE projection and
    classifies the pair. Rows are not re-derived by a second predicate: a
    population that disagreed with the one three tests above it would make both
    unfalsifiable.
    """
    from srmech.amsc import catalog

    rows = []
    acc = {"declared": 0, "compared": 0, "declined": 0, "pure_raised": 0}
    lib = _compose._compose_lib("srmech_chain_run",
                                "srmech_chain_run_arena_bytes")
    assert lib is not None, "chain-run symbols absent — not a skip"
    for src in ("pi_digits", "asymptotic_calculus", "cosmos_validation"):
        chains = {c.name: c for c in catalog._load_catalog_chains(src)}
        ds = catalog.get_attested_dataset(src)
        for row in ds.get("rows", []):
            data = dict(row.get("data") or {})
            spec = chains.get(data.get("chain_id"))
            if spec is None:
                continue
            acc["declared"] += 1
            chain_dict = _compose._spec_to_chain_dict(spec)
            ctx, ok = _compose._drop_oversized_ints({"row": data, "inputs": {}})
            if not ok:
                acc["declined"] += 1
                continue
            try:
                cj = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
                xj = json.dumps(ctx, ensure_ascii=False).encode("utf-8")
            except (TypeError, ValueError):
                acc["declined"] += 1
                continue
            n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
            ws = (ctypes.c_char * n)()
            cap = max(n // 2, 16384)
            out = (ctypes.c_char * cap)()
            ol = ctypes.c_size_t()
            rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                          out, cap, ctypes.byref(ol)))
            wire = out.raw[:ol.value]
            if rc != 0 or not wire:
                acc["declined"] += 1
                continue
            desc = _compose._srmech_json.loads(wire.decode("utf-8"))
            kind = desc.get("k") if isinstance(desc, dict) else None
            try:
                pure = _compose.run_chain(spec, row=data, inputs={})
            except Exception as exc:                    # noqa: BLE001
                acc["pure_raised"] += 1
                rows.append({"src": src, "chain": spec.name, "kind": kind,
                             "verdict": "PURE_RAISED_%s" % type(exc).__name__,
                             "native": None, "pure": None, "wire": wire})
                continue
            acc["compared"] += 1
            # THE SAME comparator population A uses. rc == 0 by construction here.
            verdict = classify(0, wire, pure, py_serialisable=True)
            rows.append({"src": src, "chain": spec.name, "kind": kind,
                         "verdict": verdict,
                         "native": _compose._reconstruct_value(desc),
                         "pure": pure, "wire": wire})
    return rows, acc


@pytest.fixture(scope="module")
def census_b_valued():
    require_native("population-B VALUE parity (it runs the C projection)")
    return _census_b_valued()


def test_population_b_value_rows_reconcile(census_b_valued):
    """Every declared row lands in exactly one bucket, and the buckets sum.

    A shrinking compared-set is the quiet failure this reconciliation refuses:
    without it, a population that stopped producing rows would report a cleaner
    result than one that produced them and agreed.
    """
    rows, acc = census_b_valued
    assert acc["declared"] > 0, "population B derived NO rows — nothing measured"
    assert len(rows) == acc["compared"] + acc["pure_raised"], (
        "row list and accounting disagree: %d rows vs compared=%d + raised=%d"
        % (len(rows), acc["compared"], acc["pure_raised"]))
    assert acc["declared"] == acc["compared"] + acc["pure_raised"] + acc["declined"], (
        "a declared row vanished: %r" % (acc,))
    assert acc["pure_raised"] == 0, (
        "the PURE projection raised on rows the C projection ran: %s"
        % [r["chain"] for r in rows if r["verdict"].startswith("PURE_RAISED")])


def test_no_value_divergence_in_population_b(census_b_valued):
    """C and pure agree BY TYPED BITS on every population-B row.

    ⚠️ SCOPE, stated so a green here is not over-read. This catches a C-SIDE
    fault (the C writer emitting a different kind, a wrong numerator, a dropped
    step) — measured: reverting the C `q` emission reds 50 of 72 in
    test_chain_run_c_rc174 and this row set with it. It does NOT catch a
    READER-side collapse, because both projections rebuild through the same
    `_reconstruct_value` and move together. That case is the next test's, and
    the split is deliberate rather than a gap left open.
    """
    rows, _acc = census_b_valued
    bad = [(r["src"], r["chain"], r["verdict"], r["native"], r["pure"])
           for r in rows if r["verdict"] != "BYTE_IDENTICAL"]
    assert len(bad) <= CEIL_POPULATION_B_DIVERGENT, (
        "population-B rows where the two projections disagree: %r" % (bad,))


def test_the_q_rows_are_present_and_are_the_exact_carrier(census_b_valued):
    """⚠️ THE LOAD-BEARING ONE. `q` rows must EXIST and rebuild as `Q`.

    This is the ONLY assertion in either population that can fail when both
    projections collapse together, because it compares each rebuilt value to
    the CONTRACT rather than to the other projection.

    Two parts, deliberately separate:

      * the FLOOR — if these rows vanish, the population stopped exercising the
        exact-ℚ wire and every other assertion here goes vacuously green. Same
        failure `test_q_is_emitted_by_an_executed_shipped_chain` guards on the
        kind axis, restated on the value axis.
      * the TYPE — `type(...) is Q`, NOT `isinstance` and NOT `==`. A tuple
        subclass satisfies `isinstance`; EVERY value here satisfies `==`. Only
        identity of type separates the rc451 collapse from the rc452 contract.

    RED-PLANT that proves it fires: in `_reconstruct_value`, return
    `(int(desc["n"]), int(desc["d"]))` instead of `_Q(...)` — either wholesale
    or, harder, only when `int(desc["d"]) > 1000`. The partial form corrupts 32
    of 39 live rows, passes 633 tests elsewhere on the chain-run surface, and
    reds HERE.
    """
    rows, _acc = census_b_valued
    q_rows = [r for r in rows if r["kind"] == "q"]
    assert len(q_rows) >= FLOOR_Q_ROWS_POPULATION_B, (
        "population B emitted %d `q` rows, floor is %d. If this is a deliberate "
        "catalog change, LOWER the floor in the same commit and say why — a "
        "silently shrinking exact-ℚ population makes this whole section vacuous."
        % (len(q_rows), FLOOR_Q_ROWS_POPULATION_B))
    wrong = [(r["chain"], type(r["native"]).__name__, type(r["pure"]).__name__)
             for r in q_rows
             if type(r["native"]) is not _Q or type(r["pure"]) is not _Q]
    assert not wrong, (
        "wire kind `q` did not rebuild as the exact-ℚ carrier on both sides: %r. "
        "This is the rc451 collapse: a `q` rebuilt as a 2-tuple is "
        "indistinguishable from a Class-K pin pair or a Class-B `pair` step, and "
        "neither `==` nor a cross-projection comparison can see it." % (wrong,))


def test_an_equality_comparator_would_NOT_catch_the_collapse():
    """CONTROL — prove the typed comparator is stronger than the shipped `==`.

    A ratchet whose added strictness is never demonstrated is indistinguishable
    from a duplicate of the gate beside it. This asserts BOTH directions on the
    real carrier: `==` says same, typed `_bits` says different. If `Q.__eq__`
    ever tightened, this control FAILS and tells you the rc174 gate became
    sufficient on axis (1) — a real change worth being told about, not a silent
    relaxation.
    """
    collapses = [
        (_Q(5, 6), (5, 6), "tuple — what rc451 rebuilt"),
        (_Q(5, 6), [5, 6], "list — the CR_LIST spelling"),
        (_Q(3, 1), 3,      "int — an integral rational"),
    ]
    for exact, collapsed, why in collapses:
        assert exact == collapsed, (
            "premise failed for %s: `==` already separates these, so the rc174 "
            "gate is not blind on this pair and this control is stale" % why)
        assert classify(0, b'{"k": "q", "n": "%d", "d": "%d"}'
                        % (exact.numerator, exact.denominator),
                        collapsed) == "DIVERGENT", (
            "the TYPED comparator failed to reject the %s collapse" % why)
