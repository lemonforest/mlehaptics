"""`#T1141` / gh #1653 — the C-projection cascade-parity ratchet. DOWN-ONLY.

srmech is a MULTI-IMPLEMENTATION codebase (ADR-0009): the scripting-coherency
projection (``python/srmech``) and the compiled-coherency projection (``c/src``)
are CO-EQUAL. The config-driven cascade surface violates that today: of the 18
executable ``[cascade]`` descriptors, the C run loop accepts **0**.

This file exists so that gap can never again be invisible or silently deferred.
It lands BEFORE the fix on purpose — `#T1141`'s own finding is that the causal
variable is THE GATE, NOT INTENT: ungated surfaces trickle, gated ones race.

WHAT IS GATED HERE
------------------
1. ``test_every_c_rejected_chain_is_enumerated`` — the INVARIANT, and the one
   that matters. Every chain the C projection cannot run must appear in
   :data:`BLOCKED` with a named gate and a disposition. A chain rejected for an
   UNLISTED reason FAILS. This is an invariant, not a pinned integer, so it does
   not rot as the catalog grows — a new descriptor that C cannot run is caught on
   arrival rather than silently widening a count.
2. ``test_c_rejected_chain_count_is_tight`` — down-only, pinned TIGHT (``==``,
   not ``<=``), house style. Fixing a chain FORCES the literal down; you cannot
   silently improve either.
3. ``test_surface_a_unsupported_step_forms_is_tight`` — same, for step forms.
4. ``test_all_executable_chains_run_in_c`` — the TARGET. Marked
   ``xfail(strict=True)``, so it is RED-but-expected now and, the moment the work
   lands, XPASS makes it FAIL until the marker is deleted. That is the drain: the
   gate removes itself when it is satisfied, instead of quietly passing forever.

⚠️ WHAT A SEEDED CEILING CANNOT DETECT — stated because this project has been
bitten by prose claiming otherwise (srmech notebook §3.54). :data:`CEIL_*` below
is seeded at the MEASURED rc445 population. A ceiling seeded at the live
population is a claim about the FUTURE, not a detection of the PAST: it catches
the REGRESSION, never the original. It is also blind to a gap CLASS that does not
exist yet — a new step form nobody has written cannot be counted. Gate 1 is the
partial remedy (it is shaped as an invariant), and the gap ledger
(``notes/_1653_gap_ledger.py``) is the rest: it enumerates what the complete
surface required, including the rows this ratchet cannot see.

TWO GRAMMARS — do not conflate them (measured, gh #1653):
  SURFACE A  ``[[cascade.chain.steps]]``  ``srmech/cascade/compose.py``, ADR-0008.
             ALL 21 packaged descriptors use this one. C executes 1 of 3 forms.
  SURFACE B  ``[[stage]]``  ``srmech/dsl/_toml_chain.py``, peer
             ``srmech_dsl_chain_run``. C executes 5 of 6; only ``parallel_body``
             is deferred, deliberately, as a host-thread affordance.
This file gates SURFACE A, because that is the one the shipped catalog uses.
"""
from __future__ import annotations

import ctypes
import json

import pytest

import srmech
from srmech.cascade import compose as _compose
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat

# ── down-only ceilings, seeded at the MEASURED rc445 population ──────────────
# Re-measured at rc445 by notes/_1653_chain_census_rc444.py:
#   "CENSUS of 18 executable chains (20 chain-variants): ...
#    C srmech_chain_run ACCEPT=0 REJECT=18 ... UNATTRIBUTED=0"
CEIL_C_REJECTED_CHAINS = 18            # of 18 executable. Target 0.
CEIL_SURFACE_A_UNSUPPORTED_FORMS = 2   # map + fold. plain executes. Target 0.

SURFACE_A_STEP_FORMS = ("plain", "map", "fold")

# ── the four measured C-side gates (gh #1653, re-verified at rc445) ──────────
GATE_OP_TABLE = "op_table"          # srmech_compose_run.c:616 cr_dispatch -> NOT_IMPL
GATE_CARRIER = "carrier_width"      # srmech_compose_run.c:92  cr_value_t has no
#                                     double / byte-buffer / dense-matrix kind
GATE_REF_GRAMMAR = "ref_grammar"    # srmech_compose_run.c:285 "only bare .output"
GATE_REAL_ARG = "real_literal_arg"  # srmech_compose_run.c:215 cr_json_scalar
#                                     returns NULL for a JSON DOUBLE
GATE_STEP_FORM = "step_form"        # the map / fold arms do not exist on surface A

VALID_GATES = frozenset({GATE_OP_TABLE, GATE_CARRIER, GATE_REF_GRAMMAR,
                         GATE_REAL_ARG, GATE_STEP_FORM})
VALID_DISPOSITIONS = frozenset({"CLOSED_IN_THIS_RC", "FILED_AS_NEW_ITEM",
                                "DECLINED_WITH_REASON", "OPEN"})

#: Every executable chain the C run loop cannot run, with its gate set.
#: ZERO ROWS MAY BE SILENT (ADR-0009 §5 forbids an unfiled decline, and this
#: issue exists *because* one went unfiled). Delete a row only when C runs it.
BLOCKED = {
    "autocorrelation":        {"gates": [GATE_STEP_FORM, GATE_OP_TABLE], "disposition": "OPEN"},
    "best_rational_signed":   {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "chiral_dual":            {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "cyclic_gcd":             {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "cyclic_mod_add":         {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "cyclic_mod_inv":         {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "cyclic_mod_mul":         {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "cyclic_mod_mul_wide":    {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "cyclic_mod_pow":         {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "encode_loe_content":     {"gates": [GATE_OP_TABLE, GATE_CARRIER], "disposition": "OPEN"},
    "klein4_from_one":        {"gates": [GATE_STEP_FORM, GATE_OP_TABLE, GATE_CARRIER],
                               "disposition": "OPEN"},
    "kuramoto_step":          {"gates": [GATE_STEP_FORM, GATE_OP_TABLE, GATE_CARRIER],
                               "disposition": "OPEN"},
    "magnitude":              {"gates": [GATE_OP_TABLE, GATE_REF_GRAMMAR], "disposition": "OPEN"},
    "net_chirality":          {"gates": [GATE_STEP_FORM, GATE_OP_TABLE], "disposition": "OPEN"},
    "octonion_dft":           {"gates": [GATE_STEP_FORM, GATE_OP_TABLE, GATE_CARRIER],
                               "disposition": "OPEN"},
    "parallel_sector_dispatch": {"gates": [GATE_OP_TABLE], "disposition": "OPEN"},
    "quaternion_dft":         {"gates": [GATE_STEP_FORM, GATE_OP_TABLE, GATE_CARRIER],
                               "disposition": "OPEN"},
    "schur_complement":       {"gates": [GATE_OP_TABLE, GATE_CARRIER, GATE_REF_GRAMMAR,
                                         GATE_REAL_ARG], "disposition": "OPEN"},
}

_STATUS = {0: "SRMECH_OK", 2: "SRMECH_ERR_BAD_INPUT", 5: "SRMECH_ERR_NOT_IMPL"}


def _executable_chains():
    """The executable descriptors, read LIVE — never a hard-coded list."""
    catalog = _cat.load_catalog()
    return sorted(n for n, d in catalog.items()
                  if _cc.descriptor_status(d) == "executable"), catalog


def _c_runs(chain_dict, ctx):
    """Drive the shipped ``srmech_chain_run``. Returns (rc, status).

    Same call convention the gh #1653 census used, whose harness is PROVEN: two
    positive controls are C-accepted AND byte-identical to the Python projection,
    so a rejection here is the C grammar, not this harness.
    """
    lib = _compose._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        pytest.skip("no native library — this gate measures the C projection")
    try:
        cj = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
        xj = json.dumps(ctx, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError):
        return None, "PY_JSON_DUMPS_FAILED"
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, ws_bytes,
                                  out, out_cap, ctypes.byref(out_len)))
    return rc, _STATUS.get(rc, "rc=%d" % rc)


def _measure():
    """(rejected, accepted) chain-name sets, measured against the C run loop."""
    names, catalog = _executable_chains()
    rejected, accepted = set(), set()
    for name in names:
        entries = _cc._chain_entries(catalog[name])
        ok_any = False
        for entry in entries:
            cases = entry.get("proof_cases") or [{}]
            ctx = dict((cases[0] or {}).get("inputs") or {})
            rc, _ = _c_runs(entry, ctx)
            if rc == 0:
                ok_any = True
        (accepted if ok_any else rejected).add(name)
    return rejected, accepted


def test_every_c_rejected_chain_is_enumerated():
    """THE INVARIANT: no silent row. An unlisted rejection fails.

    This is deliberately NOT a count. A count rots as the catalog grows; an
    invariant does not. ADR-0009 §5 forbids an unfiled decline, and gh #1653
    exists precisely because one went unfiled.
    """
    rejected, accepted = _measure()

    unenumerated = sorted(rejected - set(BLOCKED))
    assert not unenumerated, (
        "C cannot run these chains and they are NOT enumerated in BLOCKED: %s\n"
        "Add a row with its gate(s) %s and a disposition %s, or fix the chain. "
        "Zero rows may be silent." % (unenumerated, sorted(VALID_GATES),
                                      sorted(VALID_DISPOSITIONS)))

    stale = sorted(set(BLOCKED) & accepted)
    assert not stale, (
        "these chains now RUN in C but are still listed as BLOCKED: %s\n"
        "Delete their rows — a stale block-list hides a closed gap." % stale)

    for name, row in sorted(BLOCKED.items()):
        bad = sorted(set(row["gates"]) - VALID_GATES)
        assert not bad, "%s names unknown gate(s) %s" % (name, bad)
        assert row["gates"], "%s must name at least one gate" % name
        assert row["disposition"] in VALID_DISPOSITIONS, (
            "%s has disposition %r, not one of %s"
            % (name, row["disposition"], sorted(VALID_DISPOSITIONS)))


def test_c_rejected_chain_count_is_tight():
    """Down-only, pinned TIGHT — fixing a chain FORCES this literal down."""
    rejected, _ = _measure()
    assert len(rejected) == CEIL_C_REJECTED_CHAINS, (
        "C-rejected chain count is %d, ceiling is %d. If you FIXED chains, lower "
        "CEIL_C_REJECTED_CHAINS to %d and delete their BLOCKED rows. If this grew, "
        "a chain regressed."
        % (len(rejected), CEIL_C_REJECTED_CHAINS, len(rejected)))


def test_surface_a_unsupported_step_forms_is_tight():
    """Surface A has 3 step forms; C executes only ``plain``. Down-only."""
    supported = set()
    for form, chain in (
        ("plain", {"name": "p", "steps": [
            {"class": "N", "op": "rational_add",
             "args": {"a": [1, 2], "b": [1, 3]}}]}),
        ("map", {"name": "m", "steps": [
            {"map_over": "@input.xs", "index": "i", "body": [
                {"class": "I", "op": "mod_add",
                 "args": {"a": "@idx.i", "b": 0, "n": 2}}]}]}),
        ("fold", {"name": "f", "steps": [
            {"fold_class": "I", "fold_op": "gcd", "fold_init": 0,
             "over": "@input.xs"}]}),
    ):
        rc, _ = _c_runs(chain, {"xs": [1, 2, 3]})
        if rc == 0:
            supported.add(form)
    unsupported = sorted(set(SURFACE_A_STEP_FORMS) - supported)
    assert len(unsupported) == CEIL_SURFACE_A_UNSUPPORTED_FORMS, (
        "surface-A step forms C cannot execute: %s (%d); ceiling %d. Lower the "
        "ceiling when you implement one."
        % (unsupported, len(unsupported), CEIL_SURFACE_A_UNSUPPORTED_FORMS))


@pytest.mark.xfail(strict=True, reason=(
    "gh #1653: the C projection runs 0 of 18 executable cascade chains at rc445. "
    "STRICT on purpose — when the work lands this XPASSes, which FAILS, which "
    "forces this marker to be deleted. The gate removes itself when satisfied "
    "rather than quietly passing forever."))
def test_all_executable_chains_run_in_c():
    """THE TARGET. Co-equal projections means every declared chain runs in C."""
    rejected, _ = _measure()
    assert not rejected, (
        "%d executable chains do not run in the C projection: %s"
        % (len(rejected), sorted(rejected)))


def test_ratchet_reports_the_full_state(capsys):
    """Visibility: print the per-chain state every run, so it is never invisible."""
    rejected, accepted = _measure()
    with capsys.disabled():
        print("\n  C-projection cascade parity @ srmech %s (ABI %s)"
              % (srmech.__version__, srmech.native_status()["abi_version"]))
        print("  accepted by srmech_chain_run : %d" % len(accepted))
        print("  rejected                     : %d" % len(rejected))
        for name in sorted(rejected):
            row = BLOCKED.get(name, {})
            print("    %-26s gates=%-46s %s"
                  % (name, ",".join(row.get("gates", ["UNENUMERATED"])),
                     row.get("disposition", "!!")))
    assert len(accepted) + len(rejected) == len(_executable_chains()[0])
