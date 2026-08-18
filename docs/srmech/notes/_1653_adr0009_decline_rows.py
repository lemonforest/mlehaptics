#!/usr/bin/env python3
"""The ADR-0009 §5 decline rows, in the §6a machine-readable shape.

gh #1653 definition-of-done item 7.  This is the SEED for option (ii) in
`notes/_1653_adr0009_decline_list.md` §2 — a committed ledger the rcN can assert
against, rather than prose that nothing checks.

Each row carries exactly what §5 mandates — the CAPABILITY, the DECLINING
IMPLEMENTATION, and the BOUNDARY — in the §6a shape
``capability -> {implementations present} / {missing}``, plus the four fields a
filing needs to be actionable: why (a technical reason, never "hard"), whether
the decline is PERMANENT or TIME-BOXED, what would close it, and the probe id
whose measurement backs the boundary.

It also emits the NOT-A-DECLINE exclusions, so a reader cannot mistake the
`#T1146` silent-accept BUG for a filed gap.

Run:  cd docs/srmech/python && python3 ../notes/_1653_adr0009_decline_rows.py
Reads `_1653_adr0009_decline_verify.ndjson` and FAILS if a row's measured
boundary is missing from it — a row whose boundary cannot be re-measured is
exactly the unfiled decline ADR-0009 §5 forbids.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PY = _HERE.parent / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

import srmech                                                    # noqa: E402
from srmech.amsc.format import sha256_bytes                      # noqa: E402

VERIFY = _HERE / "_1653_adr0009_decline_verify.ndjson"
OUT = _HERE / "_1653_adr0009_decline_rows.ndjson"

SC = "scripting_coherency"      # python/srmech
CC = "compiled_coherency"       # c/src + c/include

ROWS = [
    {
        "id": "D-1",
        "capability": "run a Surface-A [[cascade.chain.steps]] step of the MAP "
                      "form (map_over / body / index / bind)",
        "surface": "A_cascade_chain_steps",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("srmech_chain_spec_parse and srmech_chain_run both return "
                     "SRMECH_ERR_BAD_INPUT=2; co_build_step "
                     "(c/src/srmech_compose.c:299) hard-requires class+op+args "
                     "and cr_run_steps (c/src/srmech_compose_run.c:722) demands "
                     "a STRING op"),
        "why_declined": ["jpl_rule_1_no_new_recursion_cycle_needs_a_frame_stack",
                         "run_carrier_has_no_float_kind_forces_abi_17_to_18",
                         "arena_formula_is_linear_a_nested_map_is_quadratic"],
        "permanence": "TIME_BOXED",
        "closes_in_slice": "S3",
        "to_close": ["explicit frame stack (cap 8 vs measured depth 2)",
                     "CR_FLOAT in cr_kind_t / cr_json_scalar / cr_desc",
                     "@idx + @bind in co_match_namespace AND cr_resolve_ref",
                     "ABI 17 -> 18", "an arena decision (see D-9)"],
        "probe": "P3",
    },
    {
        "id": "D-2",
        "capability": "run a Surface-A step of the FOLD form (fold_class / "
                      "fold_op / fold_init / over)",
        "surface": "A_cascade_chain_steps",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("parse and run both SRMECH_ERR_BAD_INPUT=2, same two "
                     "anchors as D-1; net_chirality.default is the only shipped "
                     "variant whose step 0 is a fold"),
        "why_declined": ["no_c_symbol_for_the_orientation_compose_body_op"],
        "permanence": "TIME_BOXED",
        "closes_in_slice": "S1",
        "to_close": ["co_build_fold_step + normalized fold node",
                     "cr_run_fold + the orientation_compose body entry "
                     "(Class-K pin-slot absorbing zero, then Class C reorient)",
                     "fold-aware _spec_to_chain_dict / _run_ints_fit_i64",
                     "_chain_c_eligible LAST"],
        "probe": "P3",
        "prototype": "notes/_1653_proto_fold.c (rebuilt + re-run: 7/7 positive, "
                     "5/5 negative, 0 failures)",
    },
    {
        "id": "D-3",
        "capability": "run a chain step whose named op has a compiled kernel",
        "surface": "A_cascade_chain_steps + B_stage",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("cr_dispatch's table holds 10 Class-N ops; the 18 "
                     "executable descriptors name 47 distinct ops, 47 of 47 "
                     "outside the table, 32 of 47 with no attributable C "
                     "symbol; 16 of 20 map/fold body ops have no C symbol; "
                     "13 of 21 catalog names are absent from the C DSL tables"),
        "why_declined": ["the_kernel_genuinely_does_not_exist_in_c_per_op"],
        "permanence": "TIME_BOXED_PER_OP",
        "closes_in_slice": "S4+",
        "to_close": ["one C kernel + one differential parity test per op; "
                     "cheapest first: the 7 variants whose ONLY blocker is the "
                     "table (cyclic_gcd, cyclic_mod_add, cyclic_mod_inv, "
                     "cyclic_mod_mul, cyclic_mod_mul_wide, cyclic_mod_pow, "
                     "encode_loe_content)"],
        "probe": "P10",
    },
    {
        "id": "D-4",
        "capability": "resolve a step-argument reference in the @idx / @bind / "
                      "@op namespaces",
        "surface": "A_cascade_chain_steps",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("co_match_namespace knows 4 of Python's 7; cr_resolve_ref "
                     "knows 3; @idx / @bind / @op each BAD_INPUT=2 at parse AND "
                     "run, against @input and @row controls that return OK=0"),
        "why_declined": ["idx_and_bind_are_only_legal_inside_a_map_body_so_they_"
                         "cannot_land_ahead_of_D-1",
                         "op_is_independent_and_is_the_single_cheapest_row"],
        "permanence": "TIME_BOXED",
        "closes_in_slice": "S2 (@op) + S3 (@idx, @bind)",
        "to_close": ["parse matcher 4 -> 6/7 AND run resolver 3 -> 5/6; do not "
                     "size run-side work off the parse count of 4"],
        "probe": "P4",
    },
    {
        "id": "D-5",
        "capability": "thread a non-integer scalar (float / bool) through a "
                      "chain step",
        "surface": "A_cascade_chain_steps",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("cr_json_scalar (c/src/srmech_compose_run.c:215) returns "
                     "NULL for ARRAY/OBJECT/DOUBLE/BOOL; single-scalar "
                     "attribution on pi_cascade_digits: 5 -> OK=0, 5.0 -> "
                     "BAD_INPUT=2, true -> BAD_INPUT=2; a float via the ctx "
                     "declines identically"),
        "why_declined": ["same_CR_FLOAT_and_ABI_18_coupling_as_D-1"],
        "permanence": "TIME_BOXED",
        "closes_in_slice": "S3",
        "to_close": ["CR_FLOAT end to end", "a NAMED python error for an "
                     "unknown carrier kind", "ABI 17 -> 18"],
        "probe": "P5",
        "sizing": "10 of 20 shipped variants carry a float; 4 of the 11 "
                  "parse-accepting variants do, so this row SURVIVES S4",
    },
    {
        "id": "D-6",
        "capability": "resolve @catalog.* while EXECUTING a chain",
        "surface": "A_cascade_chain_steps",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("@catalog.row.x: C parse OK=0 but C run BAD_INPUT=2 — "
                     "cr_resolve_ref ends `return NULL; /* @catalog or unknown "
                     "-> defer */`"),
        "why_declined": ["an_internal_inconsistency_inside_one_projection:_the_"
                         "parser_accepts_what_its_own_run_loop_cannot_execute",
                         "no_shipped_descriptor_exercises_it"],
        "permanence": "TIME_BOXED",
        "closes_in_slice": None,
        "to_close": ["resolve @catalog at run, OR reject it at parse so the two "
                     "halves of the compiled projection agree (cheaper, and "
                     "needs no new capability)"],
        "probe": "P4",
    },
    {
        "id": "D-7",
        "capability": "ingest a catalog-level chain document declaring "
                      "chain_schema_version = 2",
        "surface": "A_cascade_chain_catalog_wrappers",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("srmech_chain_catalog_parse: v1 -> OK=0, v2 -> "
                     "BAD_INPUT=2. The `ver->u.i != 1` gate is at "
                     "c/src/srmech_compose.c:512, :674 and "
                     "c/src/srmech_compose_run.c:867. All 18 executable "
                     "descriptors declare 2. SCOPE: the gate is in the CATALOG "
                     "wrappers only; co_chain_head does not read the field, so "
                     "v2 is NOT a blocker on the chain-level entry points"),
        "why_declined": ["accepting_the_version_before_the_v2_step_forms_exist_"
                         "would_accept_a_document_class_then_decline_it_a_step_"
                         "at_a_time"],
        "permanence": "TIME_BOXED",
        "closes_in_slice": "after D-1 / D-2 / D-4",
        "to_close": ["widen all three sites once the v2 step forms exist, in "
                     "the same rc"],
        "probe": "P6",
    },
    {
        "id": "D-8",
        "capability": "read a shipped descriptor carrying a non-finite TOML "
                      "float, with no scripting runtime present",
        "surface": "bare_c_host_toml_front_end",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("srmech_dsl_toml_chain_to_json accepts 19 of 21 "
                     "descriptors and returns BAD_INPUT=2 on magnitude.toml and "
                     "best_rational_signed.toml; 3-document attribution: "
                     "x=1.5 OK=0, x=nan BAD_INPUT=2, x=inf BAD_INPUT=2. "
                     "Python tomllib reads 21 of 21"),
        "why_declined": ["no_non_finite_representation_in_the_toml_front_end",
                         "and_no_float_kind_in_the_run_carrier_to_thread_it_"
                         "into_(see_D-5)"],
        "permanence": "TIME_BOXED",
        "closes_in_slice": None,
        "open_flag": "whether this is ALSO a TOML-1.0 conformance shortfall is "
                     "a spec question this filing does not answer",
        "to_close": ["a non-finite representation in both the front end and the "
                     "carrier, OR a decision that nan/inf proof cases do not "
                     "belong in a descriptor (closes it from the data side)"],
        "probe": "P7",
    },
    {
        "id": "D-9",
        "capability": "run a declared chain on a host that must pre-allocate "
                      "the whole workspace",
        "surface": "A_cascade_chain_run_arena",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("srmech_chain_run_arena_bytes is dominated by 4096 * "
                     "chain_json_bytes: measured demand 2.13 MB "
                     "(cyclic_gcd.default) to 17.58 MB "
                     "(klein4_from_one.wound). Over the bound the decline is "
                     "CLEAN: at 1% and 0.1% of demand srmech_chain_run returns "
                     "SRMECH_ERR_OVERFLOW=4 with empty output and no crash, "
                     "while the control still ran at 10% of demand"),
        "why_declined": ["jpl_rule_3_bans_malloc_so_the_envelope_must_be_static_"
                         "and_therefore_conservative",
                         "this_is_the_rc280_section_counts_shape_that_ADR-0009_"
                         "1.2_names_as_the_instance_5_exists_for"],
        "permanence": "PERMANENT_BY_DESIGN_BOUNDARY_MOVABLE",
        "closes_in_slice": None,
        "to_close": ["a data-aware srmech_chain_run_arena_bytes (signature "
                     "change, its own ABI bump, caller must know the mapped "
                     "length) — the only parity option; otherwise the row "
                     "stays filed permanently"],
        "sub_claims": {"runs_without_python": "MET (7 of 7 AMSC operator "
                                              "chains on a bare-C host)",
                       "runs_on_a_microcontroller": "NOT MET (a 3.5 KB chain "
                                                    "demands ~16 MB)"},
        "probe": "P11+P17",
    },
    {
        "id": "D-10",
        "capability": "resolve a step or composite op by DESCRIPTOR LOOKUP "
                      "(#T1143 composite -> descriptor chain; #T1144 step -> "
                      "descriptor)",
        "surface": "descriptor_name_resolution",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("both need a descriptor-directory load, and the compiled "
                     "projection has none: c/include/srmech.h declares ZERO "
                     "descriptor-directory loader symbols; the whole "
                     "srmech_catalog_* public surface is 13 symbols; the "
                     "header's own state model (c/include/srmech.h:3178) is "
                     "caller-owned — the registry state is OWNED BY THE HOST "
                     "and passed in per call. MEASURED CORRECTION: "
                     "srmech_plat_* is in the LIBRARY but NOT in the public "
                     "header (1 occurrence, inside a comment); it is declared "
                     "only in the internal c/src/srmech_platform.h"),
        "why_declined": ["it_inverts_the_caller_owned_state_model_the_rc172_"
                         "catalog_surface_rests_on_an_ADR_level_decision",
                         "it_is_name_resolution_orthogonal_to_the_step_grammar_"
                         "capability_1653_is_about",
                         "the_cycle_semantics_it_must_mirror_are_defective_"
                         "today_(a_map_op_cycle_reaches_RecursionError;_the_C_"
                         "equivalent_is_a_stack_overflow_i.e._a_crash_not_a_"
                         "decline)_and_the_ROSETTA_LEDGER_do-not-mirror_gate_"
                         "already_forbids_copying_a_defect"],
        "permanence": "PERMANENT_PENDING_ADR",
        "closes_in_slice": None,
        "to_close": ["an ADR amendment on the state model",
                     "a public platform/filesystem surface in srmech.h",
                     "a descriptor loader",
                     "a non-crashing cycle policy, fixed on the scripting side "
                     "FIRST"],
        "probe": "P9+P8",
    },
    {
        "id": "D-11",
        "capability": "run a Surface-B parallel_body Klein-4 sector fan-out and "
                      "recombine",
        "surface": "B_stage",
        "implementations_present": [SC],
        "implementations_missing": [CC],
        "boundary": ("dsl_run_combinator returns SRMECH_ERR_NOT_IMPL=5 on the "
                     "parallel_body key (c/src/srmech_dsl_chain_run.c:792), "
                     "against two live controls that return OK=0 (a leaf stage "
                     "and a loop_n combinator). It is RECOGNISED by the "
                     "7-entry discriminator array, then declined"),
        "why_declined": ["not_that_c_cannot_thread:_srmech_cascade_parallel_"
                         "sector_dispatch_is_public_AND_loadable_and_srmech_"
                         "plat_has_threads()_returns_1",
                         "the_dsl_bump_arena_is_not_thread_safe:_four_sectors_"
                         "bump_carving_one_arena_would_race"],
        "adr_0009_section_4": "NOT EXEMPT — §4 exempts only host-integration / "
                              "protocol-adapter layers (srmech.mcp / "
                              "srmech.llm / host_glue); Klein-4 sector "
                              "dispatch is neither, so 'declines by design' is "
                              "not a valid terminal status",
        "permanence": "TIME_BOXED_WHERE_THREADS_EXIST__PERMANENT_WHERE_"
                      "srmech_plat_has_threads_IS_0",
        "closes_in_slice": None,
        "to_close": ["four disjoint sub-arenas (the dispatch function's own "
                     "disjoint-slice contract already models them) + the "
                     "recombine (bundle/mean/sector0/concat); the thread-less "
                     "platform arm remains filed"],
        "probe": "P8",
    },
]

EXCLUSIONS = [
    {
        "id": "X-1",
        "item": "#T1146 silent-accept divergence (magnitude / reorient / "
                "net_chirality / chiral_flip / autocorrelation)",
        "classification": "BUG",
        "is_a_decline": False,
        "why_not_a_decline": ("nothing declines — the compiled path ACCEPTS an "
                             "input the scripting path REFUSES and returns a "
                             "value, so §5's 'declines an input the other "
                             "implementation serves' predicate is unsatisfied "
                             "in both directions and §5 cannot be used to "
                             "defer it"),
        "measured": ("chain().then('magnitude', bogus=1).run(-3.5) -> 3.5 "
                     "while srmech.cascade.magnitude(-3.5, bogus=1) -> "
                     "TypeError; 24 defect probes / 10 parity_ok_both_reject / "
                     "0 capability_gap, across 5 ops"),
        "root_cause": ("dsl/_chain.py:111-124 _then_native_desc gates on VALUE "
                       "TYPE (_is_c_scalar), never on KEY NAME; "
                       "srmech_dsl_chain_run.c:537-565 dsl_leaf_dispatch has no "
                       "leaf validating its key set; the 2 apparently clean ops "
                       "reject only INCIDENTALLY (they fall back to Python), so "
                       "there is NO key-set validator anywhere in the C leaf "
                       "surface and no in-tree pattern to copy"),
        "must_not": "be filed as a decline row — a filed decline may persist "
                    "across rcs under a tracked row, and this must not",
        "sequencing": "a closed-key-set check must land in the SAME COMMIT as "
                      "any C grammar widening; gates G1-G5 all measure what C "
                      "ACCEPTS and none measures what it should REFUSE",
        "probe": "P13",
    },
    {
        "id": "X-2",
        "item": "the compose._chain_c_eligible routing gate (class-N AND "
                "_RUN_C_OPS AND an isinstance guard)",
        "classification": "ROUTING_HAZARD",
        "is_a_decline": False,
        "why_not_a_decline": ("both projections would hold the capability; the "
                             "ROUTER declines to use the compiled one. "
                             "ADR-0009 §3 restricts 'native dispatch' to "
                             "routing language precisely so a routing fact is "
                             "never read as a capability fact"),
        "measured": "_chain_c_eligible True for 0/18; _run_chain_native "
                    "NATIVE_RAN 0/18 — so widening C alone changes nothing "
                    "observable",
        "belongs_in": "the rcN plan, not the decline ledger",
        "probe": "P15",
    },
    {
        "id": "X-3",
        "item": "the seq_get naming asymmetry",
        "classification": "REGISTRATION_ASYMMETRY",
        "is_a_decline": False,
        "why_not_a_decline": ("srmech.cascade.seq_get EXISTS in Python "
                             "(hasattr -> True); only the DSL catalog lacks the "
                             "name (lookup_cascade_op('seq_get') -> "
                             "ValueError). The C map-body recogniser names it. "
                             "So the projections disagree on whether the NAME "
                             "is addressable, not on whether the capability "
                             "exists"),
        "corrects": "a round-1 framing that would have filed this as a "
                    "compiled-only capability",
        "probe": "P12",
    },
    {
        "id": "X-4",
        "item": "kuramoto_step.general's undeclared inputs",
        "classification": "DESCRIPTOR_DECLARATION_GAP",
        "is_a_decline": False,
        "why_not_a_decline": ("the capability is missing from NEITHER "
                             "projection and from the DESCRIPTOR: all 5 proof "
                             "cases raise KeyError through the public "
                             "callable, and CI passes only because "
                             "tests/test_cascade_catalog_executable_rc420.py:"
                             "253-258 CASE_DEFAULTS merges {adjacency: None, "
                             "alpha: 0.0, pin_anchor: None, pin_strength: 1.0} "
                             "under the case (TOML cannot spell None)"),
        "probe": None,
    },
    {
        "id": "X-5",
        "item": "srmech.mcp / srmech.llm / the 21 host_glue rows",
        "classification": "EXEMPT_BY_ADR_0009_SECTION_4",
        "is_a_decline": False,
        "why_not_a_decline": "host-integration and protocol-adapter layers, "
                             "with no language-independent capability "
                             "underneath to project. Nothing else is exempt "
                             "and a new exemption requires an ADR amendment",
        "probe": None,
    },
    {
        "id": "X-6",
        "item": "the bare-C host demo's POSIX dirent.h dependency",
        "classification": "RESEARCH_ARTIFACT_NOT_SHIPPED_SOURCE",
        "is_a_decline": False,
        "why_not_a_decline": "notes/_1653_barec_host_rc444.c lives under "
                             "notes/; it becomes a portability row only if the "
                             "rcN promotes it to c/test/test_srmech_*.c",
        "probe": None,
    },
    {
        "id": "X-7",
        "item": "the 22 UNVERIFIABLE_CLAIMS in srmech/introspect/_c_claims.py "
                "(271 claim rows at rc444)",
        "classification": "PRE_EXISTING_ALREADY_TRACKED",
        "is_a_decline": False,
        "why_not_a_decline": "already under a down-only ceiling and produced by "
                             "a different mechanism (static symbol "
                             "attribution); named only so it is not "
                             "double-filed",
        "probe": "P14",
    },
    {
        "id": "X-8",
        "item": "a filesystem-less host (srmech_plat_has_filesystem() == 0)",
        "classification": "SYMMETRIC_NO_PROJECTION_ADVANTAGE",
        "is_a_decline": False,
        "why_not_a_decline": "the scripting projection cannot load descriptors "
                             "without a filesystem either",
        "probe": None,
    },
]

CEILINGS = [
    ("surface_a_variants_c_run_declines", 20, 20, "P18"),
    ("surface_a_variants_c_parse_declines", 9, 20, "P18"),
    ("variants_blocked_only_by_the_op_table", 7, 20, "P18"),
    ("parse_accepting_variants_carrying_a_float", 4, 11, "P18"),
    ("distinct_chain_ops_outside_cr_dispatch", 47, 47, "P10"),
    ("distinct_chain_ops_with_no_c_symbol", 32, 47, "P10"),
    ("map_fold_body_ops_with_no_c_symbol", 16, 20, "P16"),
    ("catalog_names_absent_from_the_c_dsl_tables", 13, 21, "P16"),
    ("descriptors_the_c_toml_front_end_cannot_read", 2, 21, "P7"),
    ("reference_namespaces_the_c_run_resolver_lacks", 4, 7, "P4"),
]
STRICT_ZERO = [
    ("unledgered_declines", 0, "every decline has a row in this file"),
    ("t1146_silent_accept_probes", 0, "24 today — this is a BUG ceiling that "
                                      "must reach 0, not a decline"),
]


def main():
    if not VERIFY.exists():
        print("MISSING %s — run _1653_adr0009_decline_verify.py first" % VERIFY)
        return 1
    probes = set()
    for line in VERIFY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            p = json.loads(line).get("probe")
            if p:
                probes.add(p)
    recs = []
    missing = []
    for r in ROWS:
        for tok in str(r.get("probe") or "").split("+"):
            tok = tok.strip()
            if tok and tok not in probes:
                missing.append((r["id"], tok))
        assert r["implementations_present"] and r["implementations_missing"], r["id"]
        assert r["permanence"], r["id"]
        assert r["why_declined"], r["id"]
        assert r["to_close"], r["id"]
        recs.append({"record": "decline_row", "adr": "ADR-0009 §5",
                     "measured_at": srmech.__version__, **r})
    for x in EXCLUSIONS:
        assert x["is_a_decline"] is False, x["id"]
        recs.append({"record": "not_a_decline", "measured_at": srmech.__version__, **x})
    for name, val, denom, probe in CEILINGS:
        recs.append({"record": "ceiling", "name": name, "value": val,
                     "denominator": denom, "direction": "DOWN_ONLY",
                     "probe": probe, "measured_at": srmech.__version__})
    for name, val, note in STRICT_ZERO:
        recs.append({"record": "strict_zero", "name": name, "value": val,
                     "note": note, "measured_at": srmech.__version__})
    body = "".join(json.dumps(r, sort_keys=True) + "\n" for r in recs)
    OUT.write_text(body, encoding="utf-8")
    h = sha256_bytes(body.encode("utf-8"))
    hh = h.hex() if isinstance(h, (bytes, bytearray)) else str(h)
    print("decline rows      : %d" % len(ROWS))
    print("  TIME_BOXED      : %d" % sum(1 for r in ROWS
                                         if r["permanence"].startswith("TIME")))
    print("  PERMANENT-ish    : %d" % sum(1 for r in ROWS
                                          if r["permanence"].startswith("PERMANENT")))
    print("not-a-decline rows: %d" % len(EXCLUSIONS))
    print("down-only ceilings: %d ; strict-zero: %d" % (len(CEILINGS), len(STRICT_ZERO)))
    print("probes referenced but NOT in the verify NDJSON: %s" % (missing or "NONE"))
    print("wrote %s (%d records) sha256=%s" % (OUT, len(recs), hh))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
