#!/usr/bin/env python3
"""gh #1653 — THE GAP LEDGER. Every capability the C projection lacks, enumerated.

ADR-0009 §5 forbids an UNFILED decline, and gh #1653 exists *because* one went
unfiled. This file is the record: one row per gap, each with measured evidence,
whether it blocked this rc, whether closing it is a NEW TYPE (which must close
its own projection gap in the same change), and exactly one disposition.

ZERO ROWS MAY BE SILENT — including gaps that ARE closed here. The ledger is the
record of what the complete surface required, not a to-do list of leftovers.

⚠️ A DECLINE IS NOT A BUG, AND THIS FILE KEEPS THEM APART.
   ``parallel_body`` returning NOT_IMPL is a DECLINE: a host-thread affordance
   the compiled projection deliberately does not offer.
   ``#T1146`` (C silently ACCEPTS what Python REJECTS) is a BUG. It must never be
   laundered into the decline list, because a decline is a capability the
   projection does not have, while that is a WRONG ANSWER the projection does
   give. Rows carry ``kind`` so the two can never be totalled together.

⚠️ WHAT A SEEDED CEILING CANNOT DETECT — stated per row in ``ceiling_blind_to``.
   A ratchet that counts today's population is blind to a CLASS that does not
   exist yet: a step form nobody has written, an op nobody has named, a carrier
   kind no descriptor yet produces. Those rows say so explicitly rather than
   implying the ratchet covers them.

Discipline: no ALU-magnitude idiom, no numpy, no RNG, no stdlib fractions.
Read-only over the tree; writes one NDJSON beside itself.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRM = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(SRM, "python"))

OUT = os.path.join(HERE, "_1653_gap_ledger.ndjson")

CLOSED = "CLOSED_IN_THIS_RC"
FILED = "FILED_AS_NEW_ITEM"
DECLINED = "DECLINED_WITH_REASON"

#: Which projection LACKS the capability the row describes.
#:
#: ⚠️ WIDENED AT rc450 (`#T1160`), and the reason is the whole point of this
#: file. Through rc449 this vocabulary was the three-value set
#: ``{"c", "python", "both"}`` — asserted in :func:`main` — while the SHIPPED
#: ``.ndjson`` beside it held thirteen rows outside that set: twelve spelling it
#: ``""`` and one ``"neither"``. They could coexist because the rows had been
#: APPENDED TO THE NDJSON BY HAND and never passed through this generator's
#: asserts at all (32 rows here against 51 on disk — see the ported block in
#: ``ROWS``). Two honest options existed: invent an attribution for each, or say
#: that none was ever stated. Inventing one is fabrication in a provenance
#: ledger, so the value is named and COUNTED DOWN instead.
LACKED_BY_VALUES = {
    "c":        "the compiled projection lacks it; Python has it",
    "python":   "the scripting projection lacks it; C has it",
    "both":     "neither projection has it, or both are equally lax",
    "neither":  "not a capability gap in either projection — e.g. a FALSE "
                "CLAIM in prose, which is a defect with no missing capability "
                "behind it",
    "unstated": "PLACEHOLDER. The row never named a projection. Ported "
                "verbatim at rc450 rather than guessed; drains under "
                "CEIL_UNSTATED_LACKED_BY.",
}

#: DOWN-ONLY. The number of ported rows that never stated which projection
#: lacked the capability. Seeded at the MEASURED rc450 population. Lower it when
#: a row is attributed; a row added ``unstated`` from here on fails.
CEIL_UNSTATED_LACKED_BY = 12

#: DOWN-ONLY, same shape: rows carrying the rc450 placeholder in
#: ``ceiling_blind_to`` because the hand-appended row never supplied one.
CEIL_UNSTATED_CEILING_BLIND_TO = 12

#: The exact placeholder text, so the count above is measured rather than
#: pattern-matched on prose that could be reworded.
UNSTATED_CEILING_BLIND_TO = (
    "NOT STATED when this row was appended to the ndjson by hand (pre-rc450). "
    "rc450 ports it VERBATIM rather than inventing a blindness claim the row "
    "never made; draining these placeholders is the `#T1159` bucket.")

ROWS = [
    # ── closed here ─────────────────────────────────────────────────────────
    dict(id="op_table_class_I", kind="gap",
         missing="The C run dispatch table had no Class-I cyclic ops, so every "
                 "cyclic chain fell to the pure runner.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="notes/_1653_gate_matrix_rc445.ndjson: op_table blocked 18 of "
                  "18, and ALONE blocked exactly the 6 cyclic chains.",
         probe="python3 notes/_1653_gate_matrix_rc445.py",
         disposition=CLOSED,
         note="Closed by a dispatch arm over EXISTING exports plus the bigint "
              "carrier. No new math was written.",
         ceiling_blind_to="A NEW cyclic op added to a descriptor later: the "
                          "ratchet counts chains, so a new op inside an already-"
                          "passing chain would not move the count."),
    dict(id="composite_map_op_key", kind="bug",
         missing="_COMPOSITE_OP_KEYS omitted map_op, lapsing BOTH composite "
                 "load-time guarantees (unknown-op validation AND cycle detection).",
         lacked_by="python", blocked_this_rc=True, new_type=False,
         evidence="Planted failure with covered-key controls: pre-fix the map_op "
                  "rows DID NOT RAISE while the fold_op controls did.",
         probe="pytest tests/test_composite_op_keys_closed_rc446.py",
         disposition=CLOSED,
         note="`#T1142`. Closed as a CLOSURE invariant against "
              "_RESERVED_STAGE_KEYS, not as a membership test, so the next "
              "op-naming discriminator cannot lapse the same way.",
         ceiling_blind_to="A discriminator added to the grammar WITHOUT being "
                          "put in _RESERVED_STAGE_KEYS is invisible to the "
                          "closure — the partition is only as complete as that tuple."),
    # ── open, filed ─────────────────────────────────────────────────────────
    dict(id="parity_tests_are_tautological_for_native_dispatched_ops", kind="bug",
         missing="The Python surface of autocorrelation / chiral_flip / reorient "
                 "/ gcd / mod_add / mod_mul / mod_pow / mod_inv / best_rational "
                 "ALL dispatch to the SAME C symbol when HAS_NATIVE. So the "
                 "obvious C-vs-Python parity test compares C AGAINST C.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="Measured rc447 by source inspection of the dispatch guards. "
                  "Consequences measured both ways: the 6 cyclic chains + "
                  "net_chirality are 30/30 identical against a FORCED-PURE "
                  "Python (so the tautology is harmless for EXACT ops), while "
                  "autocorrelation C-vs-forced-pure differs in 8 of 9 cases, "
                  "1.4e-17 (n=3) -> 1.0e-15 (n=64), and by 2.0 ABSOLUTE on a "
                  "mixed-magnitude input (~1 ulp relative at 1e16).",
         probe="pytest tests/test_c_real_carrier_rc447.py::"
               "test_autocorrelation_C_vs_FORCED_PURE_is_close_but_NOT_bit_identical",
         disposition=FILED,
         note="A BUG in the TEST METHOD, not in either projection — which is why "
              "it is filed rather than fixed by changing code. It splits cleanly: "
              "for EXACT (integer / rational) ops both paths compute an exact "
              "value, so agreement holds whatever the dispatch does and the "
              "tautology costs only test strength. For FLOAT ops it HIDES A REAL "
              "DIVERGENCE — C and pure-Python autocorrelation sum in different "
              "orders. The pure path is exactly what runs in Pyodide / WASM, "
              "where there is no .so at all, so the divergence is not "
              "hypothetical. Same shape as the earlier harness trap where both "
              "controls passed args as literals and never exercised the ref path.",
         ceiling_blind_to="EVERY parity ratchet in this issue. They all compare "
                          "C to the default Python path, so none of them can see "
                          "this at all — a chain can be 'byte-identical' and the "
                          "pure fallback still wrong. Only a forced-pure run "
                          "detects it, and nothing forces pure by default."),
    dict(id="t1145_descriptor_respelling_is_an_UNLANDED_prerequisite", kind="gap",
         missing="32 shipped descriptor step-spellings resolve to None while the "
                 "SAME object is registered under its published "
                 "srmech.cascade.<name> re-export. `#T1145` RULED on this and "
                 "flagged the fix as a follow-up; the follow-up is scheduled "
                 "NOWHERE.",
         lacked_by="python", blocked_this_rc=False, new_type=False,
         evidence="tests/test_dsl_op_naming_boundaries.py's "
                  "_INVISIBLE_WHILE_TARGET_REGISTERED_RC434 pins exactly 32, "
                  "down-only, with the remedy stated in its own comment: "
                  "'respelling descriptors to the published form, or "
                  "object-aware resolution — DRAINS this set'.",
         probe="python3 -c \"import tests.test_dsl_op_naming_boundaries as T; "
               "print(len(T._INVISIBLE_WHILE_TARGET_REGISTERED_RC434))\"",
         disposition=FILED,
         note="SLICE 3 (the map arm) IS SEQUENCED AFTER THIS OR IT UNLOCKS "
              "NOTHING END-TO-END, and the work exists on no plan. Filed here "
              "so the dependency is not discovered at implementation time.\n"
              "⚠️ MEASURED MITIGATION, so the blocker is not overstated: the C "
              "dispatch is SPELLING-AGNOSTIC — it matches the op-name SUFFIX, "
              "so srmech.cascade.atoms.chiral_flip, srmech.cascade.chiral_flip "
              "and bare chiral_flip all dispatch identically. Respelling the "
              "descriptors therefore does NOT break any C arm landed in this "
              "rc. The dependency is on the PYTHON resolution path, not the "
              "compiled one.",
         ceiling_blind_to="Nothing in gh #1653 reads that census; the two "
                          "ratchets share no constant, so slice 3 could be "
                          "declared done against a Python surface that cannot "
                          "resolve its own body ops."),
    dict(id="c_dispatch_suffix_match_is_over_permissive", kind="bug",
         missing="cr_dispatch matches the op-name SUFFIX, so a descriptor "
                 "naming a DIFFERENT module's op dispatches to srmech's.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="Measured: a step with op "
                  "'totally.different.prefix.chiral_flip' RUNS and returns "
                  "srmech's chiral_flip result.",
         probe="see the spelling table in this rc's notes",
         disposition=FILED,
         note="The permissiveness is what makes the arms survive `#T1145`'s "
              "respelling (a genuine benefit, measured), and it is ALSO how a "
              "foreign op name silently binds to a local implementation. Both "
              "are consequences of the same choice, so it is filed rather than "
              "tightened blind: narrowing it to an exact set of accepted "
              "prefixes would couple the C table to the very spellings `#T1145` "
              "is going to change. Sequence: respell first, then tighten.",
         ceiling_blind_to="Every parity gate feeds C the SHIPPED descriptors, "
                          "which never carry a foreign prefix, so no gate can "
                          "see this."),
    dict(id="jpl_scanner_blind_to_const_pointer_returns", kind="bug",
         missing="The JPL Rule 4/5 scanner skipped every line starting "
                 "`static const`, hiding all 24 functions that return a CONST "
                 "POINTER from the length and assert-count audits.",
         lacked_by="python", blocked_this_rc=True, new_type=False,
         evidence="Measured across c/src/*.c: 24 functions in 9 files were "
                  "invisible — cr_walk_json, cr_find_named_chain, "
                  "genome_find_chrom, json_emit_step, mc_method_spec and 19 "
                  "more. All 24 measured CLEAN on both rules when revealed, so "
                  "closing it cost zero violations.",
         probe="pytest tests/test_jpl_audit.py",
         disposition=CLOSED,
         note="The skip is meant for const DATA "
              "(static const char *const map_k[4] = {...}); an INITIALIZER is "
              "what distinguishes that from a function returning a const "
              "pointer. Closed NOW rather than later on purpose: the map arm "
              "adds ~45 functions to srmech_compose_run.c, which is one of the "
              "two files with a known blind function, so those would have "
              "landed unaudited. A blind spot is cheapest to fix while it is "
              "still empty — and this one was, by exactly one rc.",
         ceiling_blind_to="A function shape the regex still cannot see. The "
                          "scanner is documented as 'crude ... not a real C "
                          "parser', so the honest claim is that ONE known shape "
                          "was closed, not that the scan is now complete."),
    dict(id="wo_schur_over_the_jpl_line_in_notes", kind="bug",
         missing="notes/_1653_wedge_optable_rc444.c's wo_schur measured 61 "
                 "lines against JPL Rule 4's 60-line cap — by the ratchet's own "
                 "metric, while living where the ratchet does not run.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="J._scan_functions over the notes file: wo_schur = 61 lines. "
                  "Post-split: wo_schur 41 + wo_schur_correct 30, both clean; "
                  "the prototype still compiles under -Wall -Wextra -Wpedantic.",
         probe="cc -std=c99 -Wall -Wextra -Wpedantic -Iinclude "
               "notes/_1653_wedge_optable_rc444.c c/build/libsrmech.a",
         disposition=CLOSED,
         note="Split BEFORE being lifted from notes/ into c/src/, which is the "
              "cheap moment: after the lift it would red the ratchet, and the "
              "split would then look like a fix-under-pressure rather than "
              "prototype hygiene. Same reasoning as the scanner row above — "
              "both are cases where the gate does not yet reach the code, and "
              "the code is on its way to where the gate is.",
         ceiling_blind_to="Nothing audits notes/ at all. Every prototype in "
                          "that directory is unmeasured until the moment it is "
                          "lifted, which is the worst moment to find out."),
    dict(id="carrier_double", kind="gap",
         missing="cr_value_t has no DOUBLE kind, so a real-number literal in an "
                 "arg and a float-valued result are both unrepresentable in C.",
         lacked_by="c", blocked_this_rc=True, new_type=True,
         evidence="gate matrix: real_literal_arg blocked 9 chains, carrier_width "
                  "4. Now: chiral_dual runs in C, and a real literal round-trips "
                  "bit-exactly including -0.0 and 5e-324.",
         probe="pytest tests/test_c_real_carrier_rc447.py",
         disposition=CLOSED,
         note="NEW TYPE, and it closed its projection gap in the SAME change as "
              "the rule requires: CR_DBL + the {\"k\":\"f\"} descriptor in C, the "
              "matching `k == \"f\"` branch in Python's _reconstruct_value (which "
              "matches CLOSED and RAISES on an unknown kind, so the halves "
              "cannot ship apart), and ABI 17 -> 18. The bump is load-bearing in "
              "the reverse direction from the obvious one: a stale .so merely "
              "costs the native path, but a CURRENT .so emitting \"f\" into an "
              "OLDER Python would raise mid-run on a chain that used to work. "
              "The kind-bounds assert in cr_new_value caught CR_DBL on its first "
              "run — a discriminator set has more members than the switches that "
              "read it. Also emitted CR_LIST as {\"k\":\"l\"}, closing an "
              "asymmetry pointing the OTHER way: Python's reader had ALWAYS had "
              "that branch for a kind C could never produce.",
         ceiling_blind_to="A carrier kind no shipped descriptor produces yet "
                          "(complex, interval) — the count is over TODAY's chains."),
    dict(id="no_requested_return_type_mechanism", kind="gap",
         missing="There is NO way for a caller to REQUEST a carrier type. Every "
                 "surface is callee-declares: the callee decides the shape and "
                 "reports it.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="Searched the package for return_type / returntype / out_type "
                  "/ want_type / result_type: 0 hits. The three near-misses are "
                  "not it — `out_kind` is the REVERSE direction (the callee "
                  "reports which kind came back), `as_type` is genome type "
                  "aliasing, and `carrier=` is genome-scoped "
                  "(\"klein4\" / \"q8\").",
         probe="grep -rn 'return_type\\|out_type\\|result_type' srmech/",
         disposition=FILED,
         note="Recorded because the stated direction is that every NEW op should "
              "honour whichever carrier type is requested. That standard has no "
              "mechanism yet, and gh #1653 did not create one: this issue WIDENED "
              "one wire's kind set (adding f and l), which is a different thing "
              "from letting a caller choose. Worth separating so the widening is "
              "not mistaken for the standard.",
         ceiling_blind_to="Nothing measures request-ability at all; a 100%% "
                          "passing parity suite says nothing about whether a "
                          "caller could have asked for a different carrier."),
    dict(id="returns_field_is_unenforced_prose", kind="gap",
         missing="Every cascade descriptor MUST declare `returns`, and nothing "
                 "validates it against the value the chain actually produces.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="compose.py requires the key ('name','summary','returns',"
                  "'steps') and then only stores it as a string. The declared "
                  "values are prose with comments — \"int  # gcd(a, b) >= 0\", "
                  "\"Mat\", \"dict  # sectors / combined / ...\". No validator "
                  "found in tests/.",
         probe="python3 notes/_1653_return_types.py",
         disposition=FILED,
         note="This is the natural attachment point for a requested-return-type "
              "standard: the field is ALREADY MANDATORY on every descriptor, so "
              "the declaration exists and only the enforcement is missing. "
              "Measured across the 18 executable chains, every declared `returns` "
              "does match the actual Python type — so turning it into a gate "
              "would cost nothing today and would hold the line from here.",
         ceiling_blind_to="A descriptor whose `returns` drifts from its steps: "
                          "no gate reads the field, so it can say anything."),
    dict(id="two_divergent_value_kind_vocabularies", kind="bug",
         missing="TWO independent value-descriptor vocabularies exist, both "
                 "spelled {\"k\": ..., \"v\": ...}, with DIFFERENT kind sets. "
                 "The chain-run wire has `q` (rational) and no `t`; the DSL F1 "
                 "wire has `t` (tuple) and no `q`.",
         lacked_by="both", blocked_this_rc=True, new_type=False,
         evidence="cascade/compose.py _reconstruct_value: f i l n q s. "
                  "dsl/_chain.py _desc_to_value: f i l n s t. AND the payload "
                  "KEY diverges too: chain-run reads desc['v'] for `i`, "
                  "desc['n']/desc['d'] for `q`, desc['items'] for `l`, while "
                  "the DSL wire uses desc['v'] for its list.",
         probe="python3 notes/_1653_return_types.py",
         disposition=FILED,
         note="Neither wire is a superset of the other, so the SAME Python value "
              "has different expressibility depending on which surface runs it.\n"
              "⚠️ CORRECTED rc447, TWICE, by an adversarial review of this row. "
              "(a) This cited best_rational_signed as the exemplar of a value "
              "the chain-run wire CANNOT carry. It can: `(22, 7)` is a "
              "RATIONAL, carried natively as kind `q`. Only a non-rational "
              "tuple needs the absent `t`. The blocked set was over-stated by "
              "one chain, and it was this row's headline evidence. (b) The "
              "claim that both wires spell themselves {\"k\":...,\"v\":...} "
              "was never measured and is false — see the evidence field. The "
              "kind-set scan is a regex over `k == \"<x>\"`, which structurally "
              "cannot see key names, so it could not have caught it. If a requested-return-type contract is going to "
              "exist, these two have to become ONE vocabulary first; otherwise "
              "'the requested carrier' means different things per surface.",
         ceiling_blind_to="Each surface tests only its own wire, so no gate "
                          "compares the two kind sets. They can keep diverging "
                          "indefinitely."),
    dict(id="chain_run_list_is_flat_only", kind="gap",
         missing="The chain-run `l` (list) kind is FLAT BY CONSTRUCTION — "
                 "cr_desc_list calls cr_desc_scalar, never itself — so "
                 "list[list[float]] is not expressible even though `l` exists.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="octonion_dft and quaternion_dft both declare (and return) "
                  "list[list[float]]. cr_json_list / cr_desc_list are one level.",
         probe="python3 notes/_1653_return_types.py",
         disposition=FILED,
         note="DELIBERATE, not an oversight: JPL Rule 1 bans the recursive walk, "
              "so nesting needs an explicit frame stack exactly as the MAP step "
              "form does. Filed because 'CR_LIST ships' is easy to read as "
              "'lists work', and for these two chains it does not.",
         ceiling_blind_to="The carrier gate looks at a chain's TOP-LEVEL return "
                          "type; nesting depth is invisible to it — which is why "
                          "this predicate has now been wrong four times."),
    dict(id="carrier_bytes", kind="gap",
         missing="cr_value_t has no BYTE-BUFFER kind.",
         lacked_by="c", blocked_this_rc=True, new_type=True,
         evidence="encode_loe_content returns bytes; gate matrix marks it "
                  "carrier_width.",
         probe="python3 notes/_1653_gate_matrix_rc445.py",
         disposition=FILED, note="NEW TYPE; same ABI reasoning as carrier_double.",
         ceiling_blind_to="Same class blindness as carrier_double."),
    dict(id="carrier_matrix", kind="gap",
         missing="cr_value_t has no DENSE-MATRIX kind.",
         lacked_by="c", blocked_this_rc=True, new_type=True,
         evidence="schur_complement returns a Mat; gate matrix marks it "
                  "carrier_width.",
         probe="python3 notes/_1653_gate_matrix_rc445.py",
         disposition=FILED, note="NEW TYPE; same ABI reasoning as carrier_double.",
         ceiling_blind_to="Same class blindness as carrier_double."),
    dict(id="non_finite_doubles_cannot_cross_json", kind="decline",
         missing="nan / inf / -inf cannot reach the C runner: RFC 8259 has no "
                 "non-finite literal, srmech_json_parse is strict and refuses "
                 "them, and the writer DECLINES them for the matching reason.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="3 of magnitude's 8 proof cases are non-finite and return "
                  "BAD_INPUT at the parse, while all 5 finite cases are "
                  "bit-identical. Parser probed directly: {\"x\": NaN} -> rc=2, "
                  "{\"x\": Infinity} -> rc=2, {\"x\": 1.5} -> rc=0.",
         probe="pytest tests/test_c_ref_indexing_rc447.py::"
               "test_a_NON_FINITE_input_is_DECLINED_at_the_json_wire",
         disposition=DECLINED,
         note="ADJUDICATED, not overlooked — rc403 D4 chose option (c) DECLINE "
              "over emitting CPython's NaN / Infinity spellings, because a "
              "canonical writer whose bytes go behind a sha256 must not emit a "
              "document its own parser refuses: the attestation chain "
              "(write -> hash -> parse -> re-hash) would break at the re-read, "
              "and ADR-0003's bare-C host has no stdlib json to fall back to. So "
              "writer-output is a subset of parser-input UNCONDITIONALLY and the "
              "two halves agree. This bounds which INPUTS can cross the wire, "
              "not which chains exist — magnitude runs, on 5 of its 8 cases.",
         ceiling_blind_to="The chain-level ratchet sees a chain as RUNNING or "
                          "not; it has no notion of an input DOMAIN, so a chain "
                          "that runs on most inputs and is unreachable on some "
                          "scores identically to one that runs on all."),
    dict(id="proof_cases_were_fed_to_the_runner", kind="bug",
         missing="The parity harness passed the WHOLE catalog entry to "
                 "srmech_chain_run, coupling a chain's executability to its own "
                 "test data.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="magnitude declares non-finite proof cases; json.dumps spells "
                  "them as bare NaN / Infinity, which is not valid JSON, so the "
                  "strict parser rejected the DOCUMENT and the chain read as "
                  "BAD_INPUT — while every one of its steps ran correctly.",
         probe="pytest tests/test_c_cascade_parity_ratchet_rc446.py",
         disposition=CLOSED,
         note="proof_cases / summary / returns are DOCUMENTATION; the runner "
              "never reads them. Sending them was incidental and it made a "
              "TEST-DATA property look like a capability gap — the same class as "
              "the tautological-parity row, where the measuring apparatus rather "
              "than the code was wrong. Closed by _chain_only().",
         ceiling_blind_to="Nothing checks that the harness sends the runner only "
                          "what the runner reads; this was found by reading a "
                          "BAD_INPUT that should have been NOT_IMPL."),
    dict(id="ref_grammar_output_index", kind="gap",
         missing="cr_resolve_ref parses only a BARE `.output`; `@step[N].output[K]` "
                 "element indexing is rejected.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="Was 'only bare `.output` supported'. Now: magnitude runs, "
                  "reading @step[0].output[1] for the pin-slot magnitude half.",
         probe="pytest tests/test_c_ref_indexing_rc447.py",
         disposition=CLOSED,
         note="Closed by cr_index_value. NOT by reusing cr_walk_json as first "
              "assumed — the shapes differ: that walks a parsed JSON tree, this "
              "indexes an already-computed cr_value_t, however similar the "
              "syntax looks. Out-of-range and non-list both DEFER rather than "
              "wrap or coerce, since a wrong element is a wrong answer. A `.key` "
              "tail still declines because no MAPPING carrier exists.",
         ceiling_blind_to="A ref NAMESPACE nobody uses yet."),
    dict(id="ref_namespaces_bind_idx_op", kind="gap",
         missing="C resolves row/input/step/catalog; the shipped chains also use "
                 "@bind, @idx and @op.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="census: 'C-unknown in use: [bind, idx, op]'.",
         probe="python3 notes/_1653_chain_census_rc444.py",
         disposition=FILED,
         note="@bind and @idx exist only INSIDE a map body, so they are coupled to "
              "the map arm and cannot land before it.",
         ceiling_blind_to="A namespace introduced by a future step form."),
    dict(id="step_form_map", kind="gap",
         missing="Surface A's MAP form (map_over + body) is unrecognised by C "
                 "(BAD_INPUT=2).",
         lacked_by="c", blocked_this_rc=True, new_type=True,
         evidence="notes/_1653_step_forms_rc444.ndjson; gate matrix: 6 chains "
                  "carry a map or fold step.",
         probe="python3 notes/_1653_step_forms_rc444.py",
         disposition=FILED,
         note="PROTOTYPED AND MEASURED, not merely specified: notes/_1653_proto_map.c "
              "compiles under -Werror and reproduces klein4_from_one's 19-step / "
              "8-bind map step bit-identically (64/64 crumbs), with 12/12 negative "
              "probes declining. JPL measured with the shipped scanner: 45 "
              "functions, longest 37 lines, fewest 2 asserts, 0 recursion. It is "
              "an EXPLICIT FRAME STACK because JPL Rule 1 bans the recursive body "
              "walk. Integration is the remaining work, not feasibility.",
         ceiling_blind_to="A step form nobody has written. The ratchet's "
                          "CEIL_SURFACE_A_UNSUPPORTED_FORMS enumerates the THREE "
                          "forms that exist today; a fourth is invisible until "
                          "someone writes one."),
    dict(id="step_form_fold", kind="gap",
         missing="Surface A's FOLD form was unrecognised by C (BAD_INPUT=2) — "
                 "a fold step carries fold_op, and cr_run_steps demanded `op`.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="Was notes/_1653_step_forms_rc444.ndjson. Now: net_chirality "
                  "runs in C byte-identical on all 7 proof cases.",
         probe="pytest tests/test_c_fold_step_form_rc446.py",
         disposition=CLOSED,
         note="CLOSED as a FORM — cr_step_form + cr_run_fold ported from the "
              "prototype; net_chirality is the 7th chain (ratchet 12 -> 11). No "
              "frame stack needed: a fold has no body step list, so no re-entry "
              "into the step loop and JPL Rule 1 holds without one. NOT a new "
              "type — it adds no carrier kind. See fold_body_private_table for "
              "what this deliberately does NOT close.",
         ceiling_blind_to="Same as step_form_map — a fourth form nobody has "
                          "written yet is invisible."),
    dict(id="fold_body_private_table", kind="gap",
         missing="The fold BODY dispatches through a PRIVATE single-entry table "
                 "(cr_fold_body, orientation_compose only) rather than through "
                 "the shared cr_dispatch op table, so a fold over any other op "
                 "declines.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="A fold over `gcd` — an op the shared table DOES have — still "
                  "returns non-zero. Asserted as a REQUIRED decline in "
                  "test_c_fold_step_form_rc446.py so the limit cannot rot into "
                  "an accident.",
         probe="pytest tests/test_c_fold_step_form_rc446.py::"
               "test_a_fold_over_ANOTHER_op_still_DECLINES",
         disposition=FILED,
         note="THE HONEST EDGE OF THE FOLD WORK, filed the same day it was "
              "created. CEIL_SURFACE_A_UNSUPPORTED_FORMS deliberately still "
              "counts `fold` as unsupported: lowering it on the strength of one "
              "working chain would be the looks-done-isn't move — the form probe "
              "would go green while every fold body but one stayed unreachable. "
              "The real progress is recorded in the CHAIN count instead. The "
              "shapes differ (cr_dispatch takes a JSON args object; a fold body "
              "takes positional acc/elem), so unifying them is a real change.",
         ceiling_blind_to="The form ceiling counts FORMS, so it cannot express "
                          "'this form works for 1 of N body ops' at all — which "
                          "is exactly why this row exists in prose."),
    dict(id="symbol_gap_ABSENT_6", kind="gap",
         missing="6 ops used by shipped descriptors have NO C symbol at ANY "
                 "granularity: bind, compensated_sum, dead_band, f64_add, "
                 "scale_round_half_even, schur_complement.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="notes/_1653_symbol_gap.ndjson — all 47 ops classified per-op "
                  "against 805 exports, with every claimed symbol RE-VERIFIED at "
                  "run time.",
         probe="python3 notes/_1653_symbol_gap.py",
         disposition=FILED,
         note="THE REAL PARITY HOLES. Enumerated per-op, never as a count: an "
              "earlier draft of this ledger carried one lumped '29 missing' row, "
              "and that row WAS the skip — a missing symbol IS the parity gap, "
              "not a deferral note about one (user direction 2026-08-17).",
         ceiling_blind_to="An op added to a descriptor that already fails for "
                          "another reason — the chain count does not move. The "
                          "per-op file closes this: it asserts EVERY op used by a "
                          "shipped descriptor is classified, so a new op fails it."),
    dict(id="symbol_gap_COARSER_12", kind="gap",
         missing="12 ops where C ships the WHOLE op but not the cascade STEP — "
                 "the o/qDFT summands and mu-resolvers, the kuramoto per-term "
                 "and per-oscillator steps, correlation_product.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="notes/_1653_symbol_gap.ndjson: e.g. srmech_octonion_dft exists "
                  "while the descriptor decomposes it into odft_summand + "
                  "odft_resolve_mu + dft_scale + dft_sigma.",
         probe="python3 notes/_1653_symbol_gap.py",
         disposition=FILED,
         note="A GRANULARITY gap, not a capability gap — and the distinction is "
              "load-bearing. gh #1653 asks for config-driven cascade execution IN "
              "C, so calling the coarse symbol is NOT parity: it bypasses the "
              "grammar the issue exists to make executable. Closing these means "
              "exposing the STEP, not re-using the whole-op export.",
         ceiling_blind_to="Nothing measures granularity. A chain could be made to "
                          "'pass' by dispatching the coarse op, and every ratchet "
                          "here would go green while the descriptor was ignored."),
    dict(id="symbol_gap_FRAMING_7", kind="gap",
         missing="7 ops carry no math at all (pair, str_concat, byte_slice, "
                 "int_parse_le, utf8_encode, as_quat4, as_oct8).",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="notes/_1653_symbol_gap.ndjson.",
         probe="python3 notes/_1653_symbol_gap.py",
         disposition=FILED,
         note="These want an INTERPRETER PRIMITIVE inside the runner, NOT an "
              "exported symbol. Filed separately so they are never counted as "
              "missing exports — doing them as exports would be the wrong fix and "
              "would inflate the C surface with structure ops.",
         ceiling_blind_to="Same as the ABSENT row."),
    dict(id="claude_md_claims_schur_parity", kind="bug",
         missing="docs/srmech/CLAUDE.md lists 'the Schur-complement / "
                 "Dirichlet-to-Neumann Class-L op' among what SHIPPED in the "
                 "v0.7.x arc, against a stated commitment of 'full C parity for "
                 "every primitive class, no exceptions'. No such C symbol exists.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="nm over 805 exports: zero symbols matching schur / dirichlet / "
                  "neumann. The op is Python-only.",
         probe="nm -g --defined-only c/build/libsrmech.a | grep -iE 'schur|dirichlet|neumann'",
         disposition=FILED,
         note="A DOC bug on top of a parity gap, and the doc bug is the worse "
              "half: the orientation file every session reads asserts a parity "
              "that does not hold, so the hole is invisible to exactly the reader "
              "most likely to rely on it. That file is explicitly NOT "
              "hygiene-gated, so nothing but a reader catches it.",
         ceiling_blind_to="No ratchet reads CLAUDE.md. This class of defect — "
                          "orientation prose asserting a capability the library "
                          "lacks — has no mechanical detector at all."),
    dict(id="bigint_unreachable_from_a_json_literal", kind="gap",
         missing="rc447 put gcd / mod_add / mod_mul / mod_pow on the full bigint "
                 "carrier so no operand is narrowed — but an operand wider than "
                 "int64 cannot ARRIVE: srmech_json_parse returns "
                 "SRMECH_ERR_LIMIT for such a literal.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="Bare-C host proof: gcd(2^70, 18) returns status 8 "
                  "(ERR_LIMIT), not a value. Asserted as a required DECLINE in "
                  "test/test_srmech_chain_run.c.",
         probe="./build/test_srmech_chain_run",
         disposition=CLOSED,
         note="CLOSED by applying the rc176 DECIMAL-STRING bignum transport, "
              "which already shipped: srmech_carrier_marshal.c has read "
              "coefficients as 'a JSON int64 OR a decimal STRING' since rc176, "
              "and the chain runner was the ONE numeric surface not honouring "
              "it. So this was never an architectural wall — it was a missing "
              "arm on an existing convention, and the first framing "
              "('unreachable') was wrong. cr_widen_dec converts AT THE POINT OF "
              "USE, not at ingest, because args here are heterogeneous: "
              "combine=\"4\" is a mode name, and an ingest-time conversion "
              "would silently retype it. Measured: gcd(2^200, 2^100) returns "
              "the full 31-digit result in C, bit-equal to Python. The "
              "out-of-int64 LITERAL still declines — the transport is additive "
              "and does not weaken that contract, which stays correct because a "
              "clamped literal would be a silent wrong answer (rc402/rc404). "
              "Found ONLY by the bare-C proof: every ctypes test passes "
              "operands Python had already narrowed to int64.",
         ceiling_blind_to="Nothing measures operand WIDTH. A chain passes on "
                          "small operands and the ratchet cannot tell whether "
                          "the wide path was ever taken."),
    dict(id="arena_is_dominated_by_chain_length", kind="gap",
         missing="srmech_chain_run_arena_bytes is dominated by 4096 * chain_len, "
                 "so a ~400-byte 3-step descriptor already wants ~2.6 MiB.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="Bare-C host proof: a 1 MiB static arena returned "
                  "SRMECH_ERR_OVERFLOW for chiral_dual; 8 MiB passes.",
         probe="./build/test_srmech_chain_run",
         disposition=FILED,
         note="Not a defect — the formula is a generous static envelope and an "
              "op that outgrows it correctly takes the pure path. It is filed "
              "because it is a REAL CONSTRAINT ON THE ADR-0003 HOST: a firmware "
              "target must call arena_bytes and honour it, and must not assume "
              "a chain is small because its JSON is. Invisible to every ctypes "
              "test, which allocates exactly what the formula asks for and so "
              "never meets the ceiling.",
         ceiling_blind_to="No gate measures arena headroom on a fixed-memory "
                          "host; the pytest harness sizes to fit by "
                          "construction."),
    dict(id="bigint_modinv", kind="gap",
         missing="No bigint extended-Euclid / modular-inverse export, so mod_inv "
                 "alone keeps the uint64 wire while its five siblings went bigint.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="c/include/srmech.h exports srmech_mod_inv (uint64) only; "
                  "srmech_bigint_gcd exists but no extended form.",
         probe="grep -nE 'bigint.*(inv|egcd)' c/include/srmech.h",
         disposition=FILED,
         note="Did NOT block this rc — every shipped proof case is in range. "
              "Writing extended-Euclid on bigints is new math, not a dispatch arm, "
              "so it is filed rather than smuggled into a dispatch change.",
         ceiling_blind_to="Nothing counts out-of-range mod_inv calls; the ratchet "
                          "sees chains, not operand magnitudes."),
    dict(id="python_uint64_cap_on_cyclic", kind="gap",
         missing="srmech.math.cyclic._ensure_uint64 caps mod_add / mod_mul / "
                 "mod_pow at 2^64-1 in the PYTHON projection — a machine-word "
                 "contract on an algebra that has no machine words in it.",
         lacked_by="python", blocked_this_rc=False, new_type=False,
         evidence="cyclic.gcd(2**200, 2**100) returns 1267650600228229401496703205376, "
                  "while cyclic.mod_add(2**70, 3, 2**70+1) RAISES 'a exceeds uint64 "
                  "range; parity surface is bounded by 2^64 - 1'. Measured rc445.",
         probe="python3 -c \"from srmech.math import cyclic; cyclic.mod_add(2**70,3,2**70+1)\"",
         disposition=FILED,
         note="THE PROJECTION IS THE PYTHON ONE HERE, which is why this row exists. "
              "In Z/nZ every element is a residue bounded by n; 'exceeds 64 bits' "
              "is not a property the algebra has. The C arm now runs bigint and "
              "was deliberately held INSIDE Python's declared surface, because a "
              "compiled projection WIDER than the scripting one is a new asymmetry "
              "in the opposite direction. Closing this means lifting the Python "
              "cap, not widening C. Surfaced by user direction: 'we should prefer "
              "cyclic algebra with relational information, and then project'.",
         ceiling_blind_to="Nothing in this issue's ratchets looks at operand range "
                          "at all — this row would not exist if it had not been "
                          "asked for directly."),
    dict(id="rejection_parity", kind="bug",
         missing="C validates REQUIRED keys and never a CLOSED KEY SET, so it "
                 "silently ACCEPTS and COMPUTES declarations Python REJECTS.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="WAS 24 of 34 probes (pure raises, native returns a value; 5 ops). "
                  "NOW 0 of 34, with the valid-call control still nativizing — a "
                  "fix that deferred everything would also score zero and would "
                  "have silently deleted the native path.",
         probe="python3 notes/_1653_t1146_rejection_parity_rc444.py",
         disposition=CLOSED,
         note="`#T1146`. A BUG, NOT A DECLINE — it must never be totalled with the "
              "decline rows. Co-equal projections means REJECTION parity, not only "
              "acceptance parity, and a capability-only fix leaves this open while "
              "looking complete.",
         ceiling_blind_to="A down-only count of REJECTED chains cannot see a chain "
                          "that is wrongly ACCEPTED — this defect is invisible to "
                          "the parity ratchet by construction, which is why it "
                          "needs its own gate."),
    # ── declined, with reason ───────────────────────────────────────────────
    dict(id="parallel_body", kind="decline",
         missing="Surface B's parallel_body returns SRMECH_ERR_NOT_IMPL.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="notes/_1653_step_forms_rc444.ndjson: the C discriminator table "
                  "RECOGNISES parallel_body and rejects it deliberately.",
         probe="python3 notes/_1653_step_forms_rc444.py",
         disposition=DECLINED,
         note="A host-thread affordance. The compiled projection deliberately does "
              "not offer thread fan-out; it is RECOGNISED and refused, not "
              "unrecognised, which is the difference between a decline and a gap.",
         ceiling_blind_to="n/a — a deliberate decline needs no ceiling."),
    dict(id="descriptor_lookup_in_c", kind="gap",
         missing="C has NO descriptor lookup, so a composite op resolving to "
                 "another descriptor's chain, or a step referencing a descriptor, "
                 "cannot work in the compiled projection.",
         lacked_by="c", blocked_this_rc=False, new_type=True,
         evidence="gh #1653 sub-items `#T1143` / `#T1144`, both flagged in the "
                  "issue as widening a discriminator set on the exact surface "
                  "where C implements the fewest forms.",
         probe="n/a — a structural absence, not a runtime probe",
         disposition=FILED,
         note="BOTH `#T1143` and `#T1144` are blocked on this one thing. Either "
              "must close its projection gap in the SAME change per the standing "
              "rule, which means neither can land until C can look a descriptor up "
              "— they cannot be taken as small widenings.",
         ceiling_blind_to="A widening proposed in a future rc: nothing measures "
                          "'would this new type open a C hole' automatically."),
    # ── PORTED AT rc450 (`#T1160`) FROM THE NDJSON ────────────────────────
    # These 19 rows existed ONLY on disk: 51 rows in the .ndjson against 32
    # in this list. Running this generator would have DELETED them, and
    # nothing would have reported it — every BLOCKED-cited id survives the
    # deletion, so test_every_blocked_row_is_ACTUALLY_FILED stays green.
    # They are reproduced field-for-field. Two fields were EMPTY or outside
    # this file's own vocabulary and are marked "unstated" rather than
    # guessed; see LACKED_BY_VALUES and CEIL_UNSTATED_* below.
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='CLOSED_IN_THIS_RC',
        evidence=('rc449: refusal added, key set params[*], BAD_INPUT, plus the '
 '~20-entry op name index.'),
        id='F-1_compose_args_unknown_key',
        kind='gap',
        lacked_by='unstated',
        missing="cr_run_plain accepted unknown keys inside a Surface-A step's args",
        new_type=False,
        note=('Second half of the rc449 subject; same class as F6 on the other '
 'grammar. Defined in notes/_rc449_leaf_keyset_spec.md §5 '
 "(committed in rc449). Added to this ledger because PR #1659's "
 "body disposes these F-ids and the spec's own §5 says 'Each gets "
 "a ledger row in notes/_1653_gap_ledger.ndjson' — it did not, so "
 'the disposition pointed at a file no reader had. ADR-0009 §5 '
 'forbids the unfiled decline; a disposition resolving only '
 'against an untracked note IS that decline in a new costume, in '
 'the rc closing the issue that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence=('cr_run_plain; the C PARSE peer co_build_step:287 / '
 'co_class_valid:300 validates exactly this.'),
        id='F1_compose_class_key_never_read',
        kind='gap',
        lacked_by='unstated',
        missing=("compose 'class' key never read — not presence, not A-N validity, "
 'not op/class agreement'),
        new_type=False,
        note=("Different class (required-key + enum). C's compose parse peer is "
 'already STRICTER than Python in the reverse direction (rejects '
 'v2 fold/map forms) — untangling that is its own adjudication. '
 'Rides the same later ABI bump as F2. Defined in '
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence='srmech_genome.c:726, 9 exports.',
        id='F2_genome_attestation_overlay',
        kind='gap',
        lacked_by='unstated',
        missing=('genome attestation overlay accepts unknown keys / non-string '
 "values / a non-object root and silently writes srmech's DEFAULT "
 'provenance'),
        new_type=False,
        note=('HEAD ITEM FOR rc450 — highest stakes in the sweep: a durable '
 'WRONG PROVENANCE RECORD from the op whose purpose is provenance '
 'honesty. Must not trickle. Deferred because the mechanism '
 "differs and Python's behaviour on a non-string value for a KNOWN "
 'key is unmeasured; mirroring must be exact, not invented. Named '
 'cost: ABI 19 -> 20 later. Defined in '
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence='mc_build_fields:331.',
        id='F3_mc_build_fields_discards_unknown',
        kind='gap',
        lacked_by='unstated',
        missing=('a supplied [class] field name not in the declared table is '
 'silently discarded'),
        new_type=False,
        note=('TOML-table mechanism, not JSON-object; refuse-vs-defer semantics '
 'unadjudicated on this surface. Defined in '
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence='mc_resolve_binds:350; mc_run_chain.',
        id='F4_mc_resolve_binds_drops_args',
        kind='gap',
        lacked_by='unstated',
        missing=("non-'binds' args keys silently dropped; mc_run_chain "
 'additionally drops static kwargs that CHANGE the answer'),
        new_type=False,
        note=("Literally D1 on the class-method surface. mc_run_chain's variant "
 'is a CAPABILITY gap wearing an acceptance costume — do not '
 'conflate the two when scoping. Defined in '
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence=('dsl_stage_is_combinator:635, dsl_run_combinator:785. '
 "cr_step_form's CR_FORM_MIXED is the correct sibling and its own "
 'comment argues for it.'),
        id='F5_dsl_multi_discriminator_first_arm_wins',
        kind='gap',
        lacked_by='unstated',
        missing=('a DSL stage declaring two discriminators is silently read as '
 'whichever arm tests first'),
        new_type=False,
        note=('Different class (discriminator mutual exclusion). Python peer '
 '(_toml_chain.py:232) READ, NOT EXECUTED — so the divergence '
 'direction is unproven. Defined in '
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='CLOSED_IN_THIS_RC',
        evidence=("rc449: refusal added, key set {'op'} u params[1..], BAD_INPUT. "
 'Discrimination control: discarding the validator result turns '
 'exactly 7 rows red, clean twins green. Bare-C proven (no Python, '
 'no ctypes); ctest 18/18.'),
        id='F6_dsl_leaf_unknown_kwarg',
        kind='gap',
        lacked_by='unstated',
        missing='dsl_leaf_dispatch accepted any unknown stage key and computed',
        new_type=False,
        note=('THE SUBJECT of #T1158. Measured pre-fix: best_rational_signed '
 'fine_scale=10 -> 31/10, fine_scal=10 (one character) -> 22/7, '
 'both SRMECH_OK, through the full bare-C TOML path. Defined in '
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='10/10 malformed Surface-B declarations returned SRMECH_OK pre-fix',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence='mc_run_method:1747.',
        id='F7_mc_run_method_fixed_route_order',
        kind='gap',
        lacked_by='unstated',
        missing=('state routes tested in fixed order; a descriptor declaring two '
 'silently gets one'),
        new_type=False,
        note=('As F3; three lines beside F3/F4 when that surface is done. '
 'Defined in notes/_rc449_leaf_keyset_spec.md §5 (committed in '
 "rc449). Added to this ledger because PR #1659's body disposes "
 "these F-ids and the spec's own §5 says 'Each gets a ledger row "
 "in notes/_1653_gap_ledger.ndjson' — it did not, so the "
 'disposition pointed at a file no reader had. ADR-0009 §5 forbids '
 'the unfiled decline; a disposition resolving only against an '
 'untracked note IS that decline in a new costume, in the rc '
 'closing the issue that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence='cr_run_steps:1413, while co_chain_head:325 checks them.',
        id='F8_chain_head_fields_unchecked',
        kind='gap',
        lacked_by='unstated',
        missing='chain-head name/summary/returns unchecked',
        new_type=False,
        note=("Same class as F1; fold into F1's fix. Defined in "
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='DECLINED_WITH_REASON',
        evidence='cat_descriptor_kind:670.',
        id='F9_cat_descriptor_kind_reads_one_key',
        kind='decline',
        lacked_by='unstated',
        missing=('cat_descriptor_kind reads only [fetch].adapter of an AMSC '
 'descriptor'),
        new_type=False,
        note=("The Python peer's refusal is UNVERIFIED, and the two ops have "
 'different contracts (the C op audits a supplied blob rather than '
 'registering a source), so it may legitimately not refuse. It '
 'cannot be called a divergence until measured. Declined as a '
 'FINDING, not as work: promote to FILED the moment the Python '
 'peer is measured. Defined in notes/_rc449_leaf_keyset_spec.md §5 '
 "(committed in rc449). Added to this ledger because PR #1659's "
 "body disposes these F-ids and the spec's own §5 says 'Each gets "
 "a ledger row in notes/_1653_gap_ledger.ndjson' — it did not, so "
 'the disposition pointed at a file no reader had. ADR-0009 §5 '
 'forbids the unfiled decline; a disposition resolving only '
 'against an untracked note IS that decline in a new costume, in '
 'the rc closing the issue that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('The gate checks the ABI integer only; the surrounding rationale '
 'prose is deliberately unconstrained.'),
        disposition='CLOSED_IN_THIS_RC',
        evidence=('tests/test_abi_prose_currency_rc449.py, with a verbatim rc448 '
 'retro-check'),
        id='abi_prose_ungated_on_two_surfaces',
        kind='bug',
        lacked_by='both',
        missing=('docs/srmech/CLAUDE.md (the NARRATIVE ABI SSoT) and c/README.md '
 'had no gate. Both said 17 while the macro said 18.'),
        new_type=False,
        note=('Textbook ungated-surfaces-trickle. These were the last two ABI '
 'statements in the tree with no gate on them.'),
        probe=("CLAUDE.md's own parenthetical lists five prior lags; rc447 made "
 'a sixth and rc448 a seventh — the first ever TWO bumps behind. '
 'c/README.md read 3 for fourteen bumps, was repaired at rc442, '
 'and was stale again five rcs later.'),
        rc='0.9.0rc449',
        task='#T1158',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence="e.g. {'loop_n':..., 'sub_chain':..., 'bogus':1}.",
        id='combinator_stage_key_sets',
        kind='gap',
        lacked_by='unstated',
        missing='combinator-stage key sets unvalidated',
        new_type=False,
        note=('PYTHON SIDE UNMEASURED. Measure first; close in C only what '
 'Python refuses. If Python also accepts, this is SYMMETRIC '
 'LAXITY, which is not a divergence. Defined in '
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('Nothing measures whether a NEW cr_dispatch arm was added without '
 'a CR_OP_REG entry, except the closure test in '
 'test_t1158_registry_param_order_rc449.py.'),
        disposition='CLOSED_IN_THIS_RC',
        evidence=('notes/_t1158_planted_red_rc449.txt; '
 'c/test/test_srmech_chain_run.c rows A1-A4'),
        id='compose_args_unknown_key_silently_dropped',
        kind='bug',
        lacked_by='c',
        missing=('cr_run_plain handed `args` to cr_dispatch without comparing its '
 "keys to the op's params; every cr_op_* reads by pull, so an "
 'unknown key was ignored.'),
        new_type=False,
        note=("Legal set is params[*] here, NOT the DSL surface's params[1..] — "
 'operands arrive by name. Both directions pinned so the asymmetry '
 'is not unified later.'),
        probe=('bare-C: gcd{a:12,b:18,bogus:99} -> SRMECH_OK, 6; gcd{a,b,n:5} -> '
 'SRMECH_OK, 6 (`n` is real on mod_add, meaningless on gcd).'),
        rc='0.9.0rc449',
        task='#T1158',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('Combinator-stage key sets and step-level keys outside `args` — '
 'both still symmetric-lax, both FILED.'),
        disposition='CLOSED_IN_THIS_RC',
        evidence=('notes/_t1158_planted_red_rc449.{c,txt}; '
 'c/test/test_srmech_chain_run.c rows B1-B8'),
        id='dsl_leaf_unknown_kwarg_silently_dropped',
        kind='bug',
        lacked_by='c',
        missing=('dsl_leaf_dispatch had no leaf that validated its key set, so a '
 'stage kwarg the op does not have was silently DROPPED and the '
 'chain computed anyway.'),
        new_type=False,
        note=('rc447 closed this AT THE PYTHON IR BUILDER, which does not exist '
 'on a bare-C host. Divergence-only fix; rc449 adds the refusal '
 'itself (dsl_leaf_keyset_ok, BAD_INPUT).'),
        probe=('bare-C: {"op":"best_rational_signed","max_denominatr":2} on '
 '0.3333333333333333 -> SRMECH_OK, (1,3); the correctly-spelled '
 'stage gives (0,1). Python raises TypeError.'),
        rc='0.9.0rc449',
        task='#T1158',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('No gate compares the arg names C READS against the registry — '
 'only the names it DECLARES. A second cr_op_* reading an '
 'unregistered name would not be caught.'),
        disposition='CLOSED_IN_THIS_RC',
        evidence=('srmech/math/rational.py docstring (rc318: renamed from '
 'precision_bits); notes/_t1158_planted_red_rc449.txt rows P1-P3'),
        id='pi_cascade_digits_precision_bits_never_renamed',
        kind='bug',
        lacked_by='c',
        missing=('rc318 renamed the Python kwarg precision_bits -> precision (a '
 'pure rename, digits bit-identical). cr_op_pi was never carried, '
 'so for 131 rcs C read a key Python REFUSES and ignored the one '
 'Python accepts.'),
        new_type=False,
        note=('Forced into scope by the params[*] validator: the registry says '
 '`precision`, so leaving the C read alone would have made the '
 'validator refuse the very key C used. Found by rc449, not '
 'predicted by its brief.'),
        probe=('pi_cascade_digits(100, precision=64): Python -> '
 '3.1415926535897932370491360265507552185...; C at rc448 -> the '
 'fully correct expansion, because it never read the key. '
 'precision_bits=64: Python raises TypeError, C honoured it.'),
        rc='0.9.0rc449',
        task='#T1158',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('No gate compares pure-vs-C VALUES for pi_cascade_digits at '
 'non-default precision.'),
        disposition='FILED_AS_NEW_ITEM',
        evidence=("notes/_t1158_planted_red_rc449.c row P2, labelled 'read, but "
 "CLAMPED'"),
        id='pi_cascade_digits_precision_clamp',
        kind='gap',
        lacked_by='c',
        missing=('cr_op_pi clamps prec < 512 up to 512; Python honours any '
 'precision in [64, 32768]. The two projections still return '
 'DIFFERENT DIGITS for precision in roughly [64, 350).'),
        new_type=False,
        note=('A wrong-VALUE divergence, NOT the wrong-KEY class rc449 closes. '
 "Deliberately left open so this rc's refusal claim is not "
 'entangled with a numeric-semantics change — the same reason the '
 'autocorrelation value divergence is excluded from G3.'),
        probe=('pi_cascade_digits(100, precision=64) -> Python degrades after '
 '~19 places; C computes at 512 bits and returns the correct '
 'expansion.'),
        rc='0.9.0rc449',
        task='#T1158',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('Nothing gates prose claims of ABSENCE; they surface only when '
 'someone re-greps.'),
        disposition='CLOSED_IN_THIS_RC',
        evidence=('the repaired docstring in '
 'tests/test_t1146_rejection_parity_rc447.py'),
        id='rc447_confession_claimed_no_in_tree_pattern',
        kind='bug',
        lacked_by='neither',
        missing=('test_t1146_rejection_parity_rc447.py asserted there is NO '
 'key-set validator anywhere in the C leaf surface so there was no '
 'in-tree pattern to copy, and that it closes the gap. Both were '
 'false, and the module ships.'),
        new_type=False,
        note=('rc449 copied that WALK and deliberately not its DEFER '
 'disposition, which is correct only because its one bare-C '
 'consumer converts it to an explicit MCP error.'),
        probe=('iv_no_extra_keys (c/src/srmech_invoke.c:1580) already walked an '
 'args object against e->params[j].name. It simply did not match '
 'the greps behind the claim '
 '(key_set|keyset|unknown_key|validate_keys) — a grep artifact '
 'reported as an absence.'),
        rc='0.9.0rc449',
        task='#T1158',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('Order is pinned only where declared and live SETS already agree; '
 "a set-drifted entry remains the rc13/rc408 gates' finding."),
        disposition='CLOSED_IN_THIS_RC',
        evidence=('tests/test_t1158_registry_param_order_rc449.py, incl. the '
 'verbatim rc448 retro-check'),
        id='registry_declared_param_order_ungated',
        kind='bug',
        lacked_by='both',
        missing=('The rc13 and rc408 gates pin registry param SETS from both '
 "directions; nothing pinned ORDER, while rc449's params[1..] rule "
 'and every positional caller depend on it.'),
        new_type=False,
        note=('7 of the 8 drifted only among keyword-only params (contract '
 'misstated, binding unaffected). polar_random was the '
 'consequential one, and rc408 introduced it while fixing a '
 'different gap.'),
        probe=('8 of 609 set-equal entries were reordered at rc448. '
 'srmech.math.hdc.polar_random declared (D, seed, rng) against a '
 'live (D, rng, seed), all POSITIONALLY BINDABLE, so '
 'polar_random(8192, 42) binds rng and raises AttributeError about '
 'randrange.'),
        rc='0.9.0rc449',
        task='#T1158',
    ),
    dict(
        blocked_this_rc=False,
        ceiling_blind_to=('NOT STATED when this row was appended to the ndjson by hand '
 '(pre-rc450). rc450 ports it VERBATIM rather than inventing a '
 'blindness claim the row never made; draining these placeholders '
 'is the `#T1159` bucket.'),
        disposition='DECLINED_WITH_REASON',
        evidence='_parse_step accepts them; cr_step_form accepts them.',
        id='surface_a_step_level_unknown_keys',
        kind='decline',
        lacked_by='unstated',
        missing='step-level unknown keys on Surface A, outside args',
        new_type=False,
        note=('SYMMETRIC LAXITY. Closing only in C would MINT THE REVERSE '
 'DIVERGENCE — C refusing what Python accepts — and that direction '
 'is invisible to the whole output-parity corpus. Defined in '
 'notes/_rc449_leaf_keyset_spec.md §5 (committed in rc449). Added '
 "to this ledger because PR #1659's body disposes these F-ids and "
 "the spec's own §5 says 'Each gets a ledger row in "
 "notes/_1653_gap_ledger.ndjson' — it did not, so the disposition "
 'pointed at a file no reader had. ADR-0009 §5 forbids the unfiled '
 'decline; a disposition resolving only against an untracked note '
 'IS that decline in a new costume, in the rc closing the issue '
 'that forbids it.'),
        probe='',
    ),
    # -- rc450 (`#T1160`) -- CLOSED here -------------------------------------
    dict(id="chain_run_output_value_never_decoded", kind="gap",
         missing="The C-parity ratchet measured srmech_chain_run by rc == 0 "
                 "ALONE. It read out_len at the call site and never decoded "
                 "out.raw, so a chain that RAN in C and returned a DIFFERENT "
                 "VALUE than the Python projection was indistinguishable from "
                 "one that agreed. Nine chains were 'accepted' on that basis.",
         lacked_by="both", blocked_this_rc=True, new_type=False,
         evidence="tests/test_c_cascade_parity_ratchet_rc446.py::_c_runs "
                  "returns (rc, status) and discards `out`; _measure sets "
                  "ok_any on `rc == 0`. Verified by reading both at rc449 head "
                  "before writing the replacement.",
         probe="pytest tests/test_c_cascade_value_parity_rc450.py",
         disposition=CLOSED,
         note="Closed by tests/test_c_cascade_value_parity_rc450.py: the C wire "
              "is decoded with the SHIPPED _srmech_json.loads + "
              "_reconstruct_value and compared bit-exactly against the pure "
              "Python projection over every declared proof case. ONE HALF IS "
              "DISCHARGED BY CONSTRUCTION, NOT BY EXECUTION: gh #1653 item 5's "
              "shape 1 (bytes / Mat carriers have no JSON form) has no live "
              "witness at rc450, because every chain producing those carriers "
              "is C-REJECTED -- CARRIER_NOT_ON_WIRE is a typed reader branch "
              "with no population row to exercise it until items 3/4 land. "
              "Said plainly rather than counted as a measured closure.",
         ceiling_blind_to="A divergence on a chain the C loop does not yet run: "
                          "the comparator's population is the ACCEPTED set, so "
                          "every newly-unblocked chain arrives unmeasured until "
                          "it is accepted, and the count reconciliation is what "
                          "makes that arrival visible rather than silent."),

    # -- rc450 (`#T1160`) -- FILED --------------------------------------------
    dict(id="carrier_mapping", kind="gap",
         missing="cr_value_t has no MAPPING kind. parallel_sector_dispatch "
                 "returns a 7-key dict, which the chain-run wire cannot "
                 "express at all -- there is no {\"k\": ...} spelling for it.",
         lacked_by="c", blocked_this_rc=False, new_type=True,
         evidence="The descriptor's [cascade.signature] output and the chain's "
                  "`returns` both name a dict; measured keys: cap, "
                  "collapse_lattice, combined, framework_thread_ladder_reading, "
                  "independence, sectors, z4_dispatch_slots. The C writer "
                  "(srmech_compose_run.c) emits exactly n/i/s/q/f/l.",
         probe="python3 notes/_1653_rc450_measure.py",
         disposition=CLOSED,
         note="NEW TYPE. Split out of carrier_matrix at rc450 because that row "
              "says 'cr_value_t has no DENSE-MATRIX kind' and its evidence line "
              "is about schur_complement returning a Mat -- a different type. "
              "The ratchet's BLOCKED row for parallel_sector_dispatch cited "
              "carrier_matrix while the same file's GATE_CARRIER comment two "
              "screens up said MAPPING; rc450 repoints it here. "
              "CLOSED at rc452 (`#T1166`) and it took TWO letters, not one: "
              "`m` for the mapping and `o` for the bool, because the dict is "
              "full of bools and `True == 1` in Python makes an `i` spelling a "
              "right value of the wrong TYPE. Both projections moved in the "
              "same change (C is_map/is_bool carrier flags + cr_desc arms; "
              "Python `m`/`o` branches in _reconstruct_value; the "
              "EXPECTED_WIRE_KINDS bijection; REQUIRED_EMITTED_KINDS, which "
              "gained `b` and `x` in the same commit after a verifier found "
              "they were never added when those kinds landed) under ABI "
              "22 -> 23. "
              "THE KEY-ORDERING HAZARD IS DESIGNED OUT, NOT DOCUMENTED AROUND: "
              "the `sectors` sub-map is INT-KEYED, and measured on the "
              "canonical writer both projections share, json.dumps(sort_keys="
              "True) sorts key OBJECTS then coerces ('1','2','10') while the C "
              "writer sorts already-stringified keys BYTEWISE ('1','10','2'), "
              "so the two DISAGREE on exactly this dict. Bool keys also "
              "lowercase and collide with 1/0, and a tuple key raises "
              "TypeError. The payload is therefore a FLAT array of alternating "
              "key/value DESCRIPTORS in insertion order -- keys are never JSON "
              "object keys, so all three hazards become unreachable.",
         ceiling_blind_to="A second dict-returning descriptor: the chain ceiling "
                          "counts chains, so the SECOND one to need MAPPING "
                          "moves no literal at all. Still true after closure, "
                          "and now the ONLY residual on this row -- the kind "
                          "exists, so a second dict-returning chain would ride "
                          "it silently rather than being counted."),

    dict(id="wire_l_payload_key_divergence", kind="gap",
         missing="The two value-descriptor wires disagree on the PAYLOAD KEY "
                 "for kind `l`, not only on the kind set. The chain-run wire "
                 "writes and reads {\"k\": \"l\", \"items\": [...]}; the DSL wire "
                 "reads desc[\"v\"].",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="c/src/srmech_compose_run.c writes the `items` key; "
                  "srmech/cascade/compose.py::_reconstruct_value reads "
                  "desc[\"items\"] for k == \"l\"; srmech/dsl/_chain.py reads "
                  "desc[\"v\"]. Three artifacts, two spellings.",
         probe="grep the three sites named in `evidence`",
         disposition=CLOSED,
         note="CLOSED AT rc451 (`#T1164`) — unified on \"v\". The `t` kind FORCED the decision this row deferred to 'the rc that next changes a wire': spelling t with \"items\" would have grown a one-kind divergence into two. Rode the ABI bump the tuple kind already paid for. The THIRD divergence, which the two_divergent_value_kind_"
              "vocabularies row does not record -- that row says both wires are "
              "'spelled {k, v}', and for kind `l` on the chain-run wire that is "
              "false. The unify-or-decline decision belongs to the rc that next "
              "changes a wire, so that it is decided WITH a gate rather than on "
              "paper.",
         ceiling_blind_to="Nothing counts wire spellings; both ceilings count "
                          "chains and forms, so a third and fourth divergence "
                          "would arrive with no literal to move."),

    dict(id="carrier_hv_encode_loe", kind="gap",
         missing="encode_loe_content needs TWO carriers the C run loop lacks, "
                 "not one: a BYTE BUFFER (utf8_encode / byte_slice / "
                 "sha256_raw) AND a HYPERVECTOR (mint_vector / permute / bind).",
         lacked_by="c", blocked_this_rc=False, new_type=True,
         evidence="The carrier_bytes row names only the byte buffer, so costing "
                  "the chain from that row alone under-scopes it by a whole "
                  "type; `bind` is additionally absent in C at ANY granularity "
                  "per the gh #1653 symbol-gap census.",
         probe="read the encode_loe_content descriptor's step ops against "
               "CR_OP_REG (notes/_1653_rc450_measure.py section 2)",
         disposition=FILED,
         note="NEW TYPE. Filed as its own row rather than as a sentence inside "
              "carrier_bytes, because a row is what a costing exercise reads "
              "and a sentence inside another row is what it misses.",
         ceiling_blind_to="The chain ceiling records ONE blocked chain for what "
                          "is two independent carrier gaps; closing either alone "
                          "moves nothing."),

    dict(id="wire_tuple_kind_absent", kind="gap",
         missing="The chain-run wire has no TUPLE kind. A Class-N pair rides "
                 "CR_LIST, so C would return [n, d] where Python returns "
                 "(n, d) -- equal under any collapsing comparator and different "
                 "under a typed one.",
         lacked_by="c", blocked_this_rc=False, new_type=True,
         evidence="The C writer emits n/i/s/q/f/l only. `q` spells a RATIONAL "
                  "(n/d fields), not a general pair, so a 2-tuple that is not a "
                  "rational has no spelling. Today this is unobservable: every "
                  "accepted chain's tuple output IS a rational.",
         probe="pytest tests/test_c_cascade_value_parity_rc450.py -k tuple",
         disposition=CLOSED,
         note="CLOSED AT rc451 (`#T1164`) — the wire carries {\"k\":\"t\"}, _reconstruct_value returns a tuple, ABI 19 -> 20, and an EXECUTED shipped proof case is asserted on the KIND STRING (not on reconstruction succeeding, which the q-dodge also satisfies). NEW TYPE, and the reason best_rational_signed's BLOCKED row keeps "
              "new_type=True. rc450 files this row because the row that BLOCKED "
              "cited (two_divergent_value_kind_vocabularies) is new_type=false "
              "and describes a DIFFERENT gap -- syncing the chain flag to it "
              "would have written new_type=False onto the one chain whose "
              "closure is definitionally a new wire kind, disarming the "
              "same-change rule exactly where the next rc needs it.",
         ceiling_blind_to="No current chain distinguishes tuple from list "
                          "end-to-end, so a comparator that collapses them is "
                          "GREEN over the whole rc450 population and stays green "
                          "until the first non-rational pair crosses the wire."),

    dict(id="ripple_manifest_no_growth_obligation", kind="gap",
         missing="tools/ripple_gates.txt cannot self-heal. FROZEN_KNOWN_GATES is "
                 "a FLOOR (an entry may not be dropped) and nothing enumerates "
                 "tests/*.py to notice a gate that was never added.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="Measured at rc449 head: all 21 cascade/chain/dispatch "
                  "C-parity gates were absent from the manifest, including "
                  "every gate gh #1653 items 3/4/5 move. rc449 itself added "
                  "three gates and listed zero of them.",
         probe="python3 tools/ripple_check.py --list",
         disposition=FILED,
         note="rc450 closes THIS arc's blind spot by hand (23 targets added, the "
              "load-bearing subset frozen) but does NOT invent the general "
              "mechanism: the predicate must neither over-capture (most test "
              "files are legitimately unlisted -- the manifest is a deliberate "
              "fast subset) nor under-capture, and designing it inside a "
              "gate-landing rc is how a bad predicate becomes permanent.",
         ceiling_blind_to="A gate added after rc450 and not listed: the manifest "
                          "floor forbids REMOVAL, and silence about ADDITION is "
                          "precisely the state this row files."),

    dict(id="dsl_wire_value_parity_unmeasured", kind="gap",
         missing="The rc450 value comparator covers SURFACE A "
                 "(srmech_chain_run) only. srmech_dsl_chain_run's wire is "
                 "unmeasured for value parity, and the comparator does not "
                 "transfer unchanged.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="The DSL wire carries a `t` kind the chain-run wire does not "
                  "and lacks `q`, and reads desc[\"v\"] where the chain-run wire "
                  "reads desc[\"items\"] for `l` (see "
                  "wire_l_payload_key_divergence).",
         probe="n/a -- filed BEFORE a probe exists, which is the point",
         disposition=FILED,
         note="Stated in-file in the rc450 comparator as well, so the scope "
              "limit is visible to a reader of the gate and not only to a "
              "reader of this ledger. An untested assumption gets a row, not a "
              "silence.",
         ceiling_blind_to="Surface B has no chain ceiling at all; its coverage "
                          "is asserted in the ratchet's docstring ('C executes 5 "
                          "of 6') and measured by nothing in this arc."),

    dict(id="native_parity_gates_use_bare_skip", kind="gap",
         missing="The rc446/rc447 cascade C-parity family gates itself with "
                 "bare pytest.skip when the library is absent, instead of "
                 "tests/_native_gate.require_native.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="tests/test_c_cascade_parity_ratchet_rc446.py::_c_runs and "
                  "tests/test_step_mutation_witness_rc447.py both call "
                  "pytest.skip directly; tests/_native_gate.py (rc351, `#T843`) "
                  "fails instead unless SRMECH_EXPECT_PURE=1, AND its skips are "
                  "COUNTED by the CI pure-cell audit against the set of files "
                  "calling require_native -- so a bare skip evades the audit "
                  "too.",
         probe="pytest tests/test_c_cascade_parity_ratchet_rc446.py on a host "
               "with no libsrmech: it reports skipped, not failed",
         disposition=FILED,
         note="Consequence, stated: on a stale-or-absent .so the whole cascade "
              "C-parity family reports GREEN with nothing executed -- and rc450 "
              "adds those gates to the ripple manifest, so the runner would "
              "inherit the same vacuous green. BOTH rc450 gates therefore call "
              "require_native; the retrofit of the rc446/447 family is filed "
              "rather than done, because converting them is a behaviour change "
              "to gates this rc is already changing for other reasons and the "
              "two should not be entangled in one diff.",
         ceiling_blind_to="A ceiling reads a number the gate produced; it cannot "
                          "see that the gate did not run."),

    # -- rc450 (`#T1160`) -- the ITEM-11 FALSEHOOD HARVEST -------------------
    #
    # gh #1653 item 11 (`#T1159`) is the DELIBERATE last-position bucket: every
    # falsehood found while working items 3/4/5 is FILED here with file:line,
    # the claimed text, the measured live value and the PREDICATE used to
    # measure it -- and NOT fixed, unless the file was already being edited for
    # a scoped reason. Opportunistic inline fixes outside scoped files are the
    # defect this sequencing exists to prevent.
    #
    # FIXED INLINE at rc450 instead of filed, because their files WERE edited
    # for a scoped reason (version bump / BLOCKED sync / manifest growth), and
    # each is named here so the harvest is complete rather than convenient:
    #   python/README.md:324  "63 plain and 9 map steps, and no fold"
    #   python/README.md:328  "1 of the 3 step forms" / "10-op Class-N table" /
    #                         "0 of the 18"
    #   tests/test_c_cascade_parity_ratchet_rc446.py  docstring "accepts 0",
    #                         GATE_OP_TABLE "10 of 18", the 18->12->11 ceiling
    #                         narrative, 3 gate sets, 6 new_type flags, and
    #                         parallel_sector_dispatch's carrier_matrix citation
    #   tests/RIPPLE_GATES.md "~55 files" and "~10k-test suite"
    dict(id="T1159_claude_md_count_pin_paragraph", kind="bug",
         missing="docs/srmech/CLAUDE.md's count-pin warning paragraph says "
                 "'73 lines across 66 test files' and names EXPECTED_N as THE "
                 "singular blind spot of its own predicate.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Measured at rc450, same predicate the paragraph states "
                  "(`git grep -c \"== 663\" -- tests/`, 663 being the live "
                  "describe()[\"tools\"][\"total\"]): 74 lines across 67 files. "
                  "And the invisible class is THREE shapes plus a data-file "
                  "field, not one: (1) the bare EXPECTED_N assignment, "
                  "tests/test_op_name_set_witness_rc361.py; (2) DERIVED "
                  "arithmetic, '692 frames (663 ops + 29 carriers)' in "
                  "tests/test_search_glyph_tokenizer_rc416.py; (3) PERCENTAGE "
                  "prose, '8.7% of 663' in tests/test_exact_return_carrier_"
                  "rc444.py; plus '\"n\": 663' in "
                  "tests/example_args_ledger.ndjson. A bare-word search finds "
                  "81 files against the stated predicate's 67 -- a ~14-file "
                  "gap, not a one-file one.",
         probe="git grep -c '== 663' -- tests/  (stated in the paragraph "
               "itself, which is why it is reproducible at all)",
         disposition=FILED,
         note="Owned by `#T1159`. NOT fixed at rc450: docs/srmech/CLAUDE.md is "
              "not edited in this rc for any scoped reason. Note the paragraph "
              "is self-aware about staleness and STILL went stale, which is "
              "the argument for the gate rather than for another warning.",
         ceiling_blind_to="This file is explicitly NOT hygiene-gated and no "
                          "ratchet reads it, so nothing but a reader catches "
                          "it -- and it is what a session reads FIRST."),

    dict(id="T1159_compose_run_c_wire_doc_omits_f", kind="bug",
         missing="c/src/srmech_compose_run.c:19 documents the value descriptor "
                 "as {\"k\":\"s\"/\"q\"/\"i\"/\"n\"/\"l\", ...} -- omitting "
                 "\"f\" -- and :21-22 still says 'any float / unsupported arg "
                 "... the peer returns non-OK'.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Both halves went stale when CR_DBL shipped at rc447. The "
                  "same file emits srmech_json_new_string(bd, \"f\", 1u) at "
                  "cr_desc_scalar, and `magnitude` returns "
                  "{\"k\": \"f\", \"v\": 3.5} with rc=0 -- measured at rc450.",
         probe="pytest tests/test_c_cascade_value_parity_rc450.py -k bijection",
         disposition=FILED,
         note="Owned by `#T1159`. THE MOST ON-TOPIC ONE: this is the canonical "
              "in-file description of the very wire the rc450 value-parity "
              "gate decodes, so a reader who follows the gate to the wire's "
              "own documentation is told the wire cannot carry a float. NOT "
              "fixed here because rc450 ships ZERO C source changes by design "
              "and a comment-only .c edit would break that claim.",
         ceiling_blind_to="No gate reads C comments; the rc450 bijection pin "
                          "reads the CODE (the emitted kind strings), which is "
                          "why it is right while the comment beside it is "
                          "wrong."),

    dict(id="T1159_tool_docs_17_executable_vs_live_18", kind="bug",
         missing="The run_cascade_chain explanation says describe()"
                 "['cascade_catalog'] counts the catalog '(17 executable / 3 "
                 "leaf)' while the live value is 18 executable / 3 leaf.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Live at rc450: describe()['cascade_catalog'] == {'total': "
                  "21, 'executable': 18, 'leaf': 3} (klein4_from_one joined at "
                  "rc438). The claim is in srmech/introspect/_tool_docs.py and "
                  "in the compiled c/src/srmech_tool_registry.c, whose own "
                  "adjacent example says 18.",
         probe="python3 -c \"import srmech; "
               "print(srmech.describe()['cascade_catalog'])\"",
         disposition=FILED,
         note="Owned by `#T1159`, and ALREADY KNOWN before rc450 -- carried "
              "here so the bucket is one list rather than two. This one SHIPS: "
              "_tool_docs.py is emitted into the wheel and the C registry is "
              "compiled in, so it reaches users through describe() and the MCP "
              "tool list.",
         ceiling_blind_to="Generated-artifact prose has no currency gate; the "
                          "regen reproduces whatever the source says."),

    dict(id="T1159_abi_prose_22_files_vs_22_lines", kind="bug",
         missing="tests/test_abi_prose_currency_rc449.py:5 says 'twenty-two "
                 "test files pin the literal'.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="PLAUSIBLE, not CONFIRMED, and the predicate is stated so it "
                  "can be refuted: `git grep -nE "
                  "'(EXPECTED_ABI_VERSION|abi_version|ABI_VERSION|ABI)"
                  "[^0-9]{0,40}\\b19\\b' -- tests/` yields 22 LINES across 18 "
                  "FILES. The gate's own prose appears to have counted lines "
                  "and written 'files'. A different predicate could reach 22 "
                  "files; mine is written out rather than implied.",
         probe="the git grep above",
         disposition=FILED,
         note="Owned by `#T1159`. Filed rather than fixed BECAUSE it is "
              "predicate-sensitive: correcting a number whose predicate is "
              "unstated would just mint a second unstated number.",
         ceiling_blind_to="The gate pins the ABI VALUE across surfaces; it "
                          "does not pin its own prose about how many surfaces "
                          "there are."),

    dict(id="T1159_example_args_ledger_stale_version_stamp", kind="bug",
         missing="tests/example_args_ledger.ndjson's meta record stamps "
                 "\"srmech_version\": \"0.9.0rc442\" beside a CURRENT payload "
                 "(\"n\": 663).",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Live version is 0.9.0rc450; n=663 is current. So the stamp "
                  "is eight releases behind while the data it stamps is not, "
                  "and a reader judging currency BY the stamp would wrongly "
                  "discard a live figure -- the failure direction that is "
                  "worse than a stale number, because it discredits good data.",
         probe="head -1 tests/example_args_ledger.ndjson",
         disposition=FILED,
         note="Owned by `#T1159`. The real fix is not a newer stamp but a "
              "regen-time stamp that cannot lag the payload -- the same shape "
              "as the rc450 gap-ledger summary re-read.",
         ceiling_blind_to="Nothing compares a data file's version stamp to the "
                          "tree's version."),

    dict(id="T1159_notes_ripple_gates_filename_collision", kind="bug",
         missing="docs/srmech/notes/ripple_gates.txt is a TRACKED file wearing "
                 "the manifest's name while being a gh #1653 ABI 17->18 "
                 "blast-radius NOTE (59 non-comment lines).",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="The real manifest is python/tools/ripple_gates.txt (101 "
                  "targets at rc450). The two bodies are wholly disjoint. A "
                  "brief citing 'docs/srmech/tools/ripple_gates.txt' resolves "
                  "to NEITHER path and lands a reader on the decoy -- which "
                  "happened to this rc's own briefing.",
         probe="diff docs/srmech/notes/ripple_gates.txt "
               "docs/srmech/python/tools/ripple_gates.txt",
         disposition=FILED,
         note="Owned by `#T1159`. RENAME, do not delete -- the note is a "
              "useful ABI-ripple precedent and the defect is only its name.",
         ceiling_blind_to="No gate reads notes/ filenames."),

    dict(id="T1159_wedge_join_row51_self_contradiction", kind="bug",
         missing="notes/_1653_wedge_join_rc444.ndjson row 51 stores a c_value "
                 "and a python_value that differ VISIBLY as strings, under "
                 "verdict BYTE_IDENTICAL, with nothing in the row saying the "
                 "verdict was computed on NORMALISED forms.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="The join script computes norm(json.loads(payload)) vs "
                  "norm(py) while the record stores the RAW C payload. To any "
                  "reader of the artifact ALONE -- which is what an ndjson is "
                  "for -- the row contradicts itself.",
         probe="sed -n 51p notes/_1653_wedge_join_rc444.ndjson",
         disposition=FILED,
         note="Owned by `#T1159`. Low stakes (a committed notes artifact), but "
              "it is the exact reason the rc450 comparator refuses a "
              "normalising encoder AND stores no normalised form: a verdict "
              "whose inputs are not the stored fields is not reproducible from "
              "the record.",
         ceiling_blind_to="Nothing re-derives a notes ndjson's verdicts from "
                          "its own stored fields."),

    dict(id="T1159_cr_op_reg_length_is_a_bare_literal_x3", kind="gap",
         missing="CR_OP_REG's length is the bare literal 20, written in three "
                 "places (the array declaration and two loop bounds in "
                 "cr_args_keyset_ok) with no sizeof-derived bound.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="Correct today -- 20 entries, 20 arms, symmetric difference "
                  "against the arms empty, self-checked by "
                  "notes/_1653_rc450_measure.py, which prints declared vs "
                  "parsed and says AGREE. But every op this arc adds must edit "
                  "all three, and a declared-20 against a loop-bound-19 would "
                  "SILENTLY DISABLE the key-set validator for the tail of the "
                  "table -- the exact failure the function's own comment says "
                  "it refuses to permit.",
         probe="python3 notes/_1653_rc450_measure.py  (section 2)",
         disposition=FILED,
         note="Owned by `#T1159`. Filed rather than fixed because rc450 ships "
              "zero C source changes; the fix is a sizeof-derived bound and it "
              "belongs to the next rc that touches the table, which is rc451.",
         ceiling_blind_to="A short loop bound produces NO symptom: the "
                          "validator simply stops validating the tail, and "
                          "every existing test still passes."),

    dict(id="T1159_two_divergent_row_says_both_wires_spell_k_v", kind="bug",
         missing="The two_divergent_value_kind_vocabularies ledger row says "
                 "the two wires are 'both spelled {\"k\": ..., \"v\": ...}'.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="False for kind `l` on the chain-run wire, which is spelled "
                  "{\"k\": \"l\", \"items\": [...]}. Measured in three "
                  "artifacts; recorded in full as the separate row "
                  "wire_l_payload_key_divergence.",
         probe="see the wire_l_payload_key_divergence row's evidence",
         disposition=FILED,
         note="Owned by `#T1159`. The ROW ITSELF is not edited at rc450, "
              "because rewriting a filed row's text in place erases what it "
              "said when it was filed; the correction is carried as its own "
              "row instead, which is what an append-only ledger is for.",
         ceiling_blind_to="Nothing checks a ledger row's prose against the "
                          "code it describes."),

    dict(id="T1159_ripple_check_suite_size_is_stale", kind="bug",
         missing="tools/ripple_check.py:49 and :148 both say the suite holds "
                 "'~14.5k tests'.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Measured at rc450 by the runner's OWN collect-only sweep, "
                  "printed in the run this rc executed: '15500 tests collected "
                  "in 58.81s'. The ~14.5k is an rc421-era figure and is now "
                  "~6% low.",
         probe="python3 -m pytest tests/ --collect-only -q --no-header",
         disposition=FILED,
         note="Owned by `#T1159`. WORTH THE ROW FOR HOW IT WAS FOUND: rc450 "
              "corrected tests/RIPPLE_GATES.md's '~10k' by copying THIS "
              "number, and so replaced one stale figure with another. Caught "
              "only because the ripple run printed the live count in the same "
              "session. The lesson is the arc's own: a figure taken from "
              "another file in the tree is a CITATION, not a measurement, and "
              "the tree stating three different sizes for one suite is what "
              "citations-of-citations produce. RIPPLE_GATES.md now carries the "
              "measured 15.5k; ripple_check.py is not edited because rc450 has "
              "no scoped reason to touch it.",
         ceiling_blind_to="Nothing measures the suite size, so all three "
                          "figures were free to drift independently."),


    # ══ rc451 (`#T1164`, gh #1653 item 4 — the RC-A slice) ═══════════════════
    dict(id="symbol_gap_ABSENT_6_partial_drain_rc451", kind="gap",
         missing="TWO of the six ABSENT-6 ops gained C symbols at OP "
                 "granularity: srmech_cascade_dead_band_f64 and "
                 "srmech_cascade_scale_round_half_even_i64. The row "
                 "symbol_gap_ABSENT_6 enumerated six; it is drained "
                 "APPEND-ONLY rather than rewritten, so what remains is "
                 "stated by its own row rather than by an edit to a claim "
                 "that was true when it was made.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="c/include/srmech.h now declares both; c/test/"
                  "test_srmech_chain_run.c calls them with no Python present "
                  "(42 passed, 0 failed). scale_round SHARES the fused chain "
                  "symbol's banker's-rounding kernel, so coarse-vs-fine "
                  "parity is by construction rather than by test.",
         probe="cc -Iinclude test/test_srmech_chain_run.c build/libsrmech.a",
         disposition=CLOSED,
         note="Neither is a new TYPE — an added symbol never bumps ABI. The "
              "rc451 bump is the wire's, not theirs.",
         ceiling_blind_to="Nothing counts the ABSENT set, so a seventh absent "
                          "op could join without any figure moving."),
    dict(id="symbol_gap_ABSENT_4_residual_rc451", kind="gap",
         missing="FOUR ops still have no C symbol at any granularity: bind, "
                 "compensated_sum, f64_add, schur_complement.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="gh #1653 symbol census notes/_1653_symbol_gap.ndjson, "
                  "resolution=ABSENT, minus the two rc451 closed.",
         probe="python3 notes/_1653_gate_matrix_rc445.py",
         disposition=FILED,
         note="schur_complement is additionally the one op the subtree "
              "CLAUDE.md advertised a C peer for and never had. Filed, not "
              "attempted: each is new MATH in C, not a discriminator widening.",
         ceiling_blind_to="Same as the row above — the ABSENT set is "
                          "enumerated, never counted by a gate."),
    dict(id="symbol_gap_FRAMING_pair_closed_rc451", kind="gap",
         missing="`pair` is dispatched as a C interpreter primitive "
                 "(cr_op_pair) and its result crosses the wire as the new "
                 "TUPLE kind. It was one of the FRAMING-7.",
         lacked_by="c", blocked_this_rc=True, new_type=True,
         evidence="notes/_1653_rca_probe_rc451.py block A: the shipped 6-step "
                  "descriptor's final value carries kind 't' and a 'v' "
                  "payload, reconstructing to a Python tuple.",
         probe="pytest tests/test_c_cascade_value_parity_rc450.py -k tuple_kind_itself",
         disposition=CLOSED,
         note="⚠️ THIS ROW RESOLVES THE `pair` new_type CONTRADICTION, AND IT "
              "RESOLVES IT AGAINST THE LEDGER. notes/_1653_symbol_gap.ndjson "
              "carried is_new_type=true for pair; the ledger's "
              "symbol_gap_FRAMING_7 row, which ENUMERATES pair, carried "
              "new_type=false. Two artifacts, one fact, nothing comparing "
              "them. rc451 settled it by DOING the work: closing pair "
              "required a cr_value_t tuple flag, a new wire kind, a new "
              "reader branch and an ABI bump — the census was right and the "
              "ledger row was wrong. Recorded here rather than by editing "
              "either artifact's history.",
         ceiling_blind_to="Nothing cross-checks the census's is_new_type "
                          "against the ledger's new_type; that comparison is "
                          "the deferred derivation gate below."),
    dict(id="symbol_gap_FRAMING_6_residual_rc451", kind="gap",
         missing="SIX framing ops remain with no C dispatch: str_concat, "
                 "byte_slice, int_parse_le, utf8_encode, as_quat4, as_oct8.",
         lacked_by="c", blocked_this_rc=False, new_type=True,
         evidence="Census is_new_type=true for byte_slice, utf8_encode, "
                  "as_quat4 and as_oct8 — four of the six.",
         probe="python3 notes/_1653_gate_matrix_rc445.py",
         disposition=FILED,
         note="new_type=TRUE for the row as a whole, on rc451's own measured "
              "precedent: `pair` looked like pure framing and still cost a "
              "carrier flag, a wire kind and a bump. as_quat4 / as_oct8 are "
              "the carrier VIEWS the adjudication says are unfiled — this "
              "row files them, so octonion_dft / quaternion_dft no longer "
              "rest their chain flag on a reason string alone.",
         ceiling_blind_to="The FRAMING tally is prose in a census file; no "
                          "gate reads it (grep of tests/ and tools/ for "
                          "'symbol_gap' returns zero)."),
    dict(id="interpreter_reorient_was_type_lossy_rc451", kind="bug",
         missing="cr_op_reorient read EVERY operand through cr_arg_dbl and "
                 "answered CR_DBL unconditionally, so reorient(22, "
                 "orientation=+1) returned 22.0 where the Python op's stated "
                 "contract is 'int in -> int out'. A WRONG ANSWER, "
                 "dispatchable since rc447.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="MEASURED the first time best_rational_signed ran in C at "
                  "rc451: the wire carried a float 22.0 in the first slot "
                  "against Python's int 22 — 9 of 9 comparable proof cases "
                  "DIVERGENT under the rc450 typed comparator.",
         probe="python3 ../notes/_1653_rca_probe_rc451.py",
         disposition=CLOSED,
         note="⚠️ THE FINDING IS HOW IT WAS FOUND. It was invisible because no "
              "ACCEPTED chain had ever handed reorient an integer — every "
              "shipped variant fed it a pin-slot magnitude, a double. It "
              "surfaced in the same run that first decoded a newly-accepted "
              "chain's VALUE, i.e. on the first decrement this ratchet has "
              "made with the value channel open. Under the pre-rc450 "
              "'accepted == rc 0' rule the decrement would have been "
              "recorded as a clean win. Fixed at root (a kind-branched arm "
              "calling srmech_cascade_reorient_i64), not routed around.",
         ceiling_blind_to="An op whose C arm is type-lossy stays invisible "
                          "until a chain both REACHES it with the other type "
                          "AND ends somewhere the wire can carry."),
    dict(id="c_arm_declines_narrower_than_python_rc451", kind="gap",
         missing="Three rc451 arms REFUSE inputs their Python twins accept: "
                 "dead_band declines a non-CR_DBL `value` (Python is "
                 "type-preserving over int, and widening would answer 5.0 "
                 "where Python answers 5); scale_round_half_even declines a "
                 "non-CR_DBL `value` and any |product| >= 2^63 (Python "
                 "returns an exact bignum); best_rational declines an "
                 "out-of-uint64 operand and any `with_path` key.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="notes/_1653_rca_probe_rc451.py block F: "
                  "scale_round_half_even(1e30, 10**6) is C status 2 against a "
                  "Python 2^119-scale int; best_rational(2**64, 10, 10) is "
                  "(9223372036854775808, 5) in Python and outside the C wire.",
         probe="python3 ../notes/_1653_rca_probe_rc451.py",
         disposition=FILED,
         note="EVERY one is a DECLINE, never a narrowed answer — the chain "
              "then runs on the pure projection and is correct. That is the "
              "Class-I convention applied uniformly: a narrower projection "
              "must REFUSE, never silently answer. Filed rather than closed "
              "because a decline is still a capability the C host lacks.",
         ceiling_blind_to="The value-parity population runs DESCRIPTOR proof "
                          "cases only, and this chain feeds every arm inside "
                          "its domain — so none of these declines is "
                          "reachable from the shipped population at all."),
    dict(id="blocked_row_derivation_gate_deferred_rc451", kind="decline",
         missing="The adjudicated replacement for BLOCKED's new_type rule — a "
                 "ledger_rows LIST schema, deletion of new_type_reason, a "
                 "`gate` field on ledger rows, and three assertions "
                 "(citations-open / OR-derivation / gate-coverage) — is NOT "
                 "shipped in rc451.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="MEASURED at rc451: the gap ledger has NO chain-attribution "
                  "field. Its key union is [blocked_this_rc, "
                  "ceiling_blind_to, disposition, evidence, id, kind, "
                  "lacked_by, missing, new_type, note, probe, rc, task] and "
                  "blocked_this_rc is a plain bool on all 69 pre-rc451 rows. "
                  "So the proposed COVERAGE assertion cannot range over its "
                  "own stated subject (a chain's COMPLETE citation set), and "
                  "the value-level rows it was designed for are explicitly "
                  "exempted from it by carrying gate=null.",
         probe="see the reconciliation block in notes/_1653_rca_gate_provenance_rc451.py",
         disposition=DECLINED,
         note="DECLINED WITH REASON, not skipped. Shipping a completeness "
              "gate that cannot check completeness would be an instrument "
              "unable to return otherwise — the exact class this arc exists "
              "to close. The data the mechanism needs ALREADY EXISTS with "
              "per-chain attribution in notes/_1653_symbol_gap.ndjson's "
              "`used_by` field (47 op rows), which no test or tool reads. "
              "Re-key the check on that, then adopt. rc451 does the half "
              "that does not depend on the mechanism: it RESOLVES the pair "
              "contradiction by measurement and FILES the as_quat4 / as_oct8 "
              "carrier-view rows the adjudication says are unfiled.",
         ceiling_blind_to="Nothing compares the census's is_new_type to the "
                          "ledger's new_type today, which is precisely the "
                          "hole the deferred gate would close."),
    dict(id="T1163_readme_c_coverage_figures_rc451", kind="bug",
         missing="python/README.md carried TWO undated, ungated cardinals in "
                 "one shipped sentence — 'CR_OP_REG holds 20 op spellings' "
                 "and 'a bare-C host runs 9 of the 18 chains'. Both were TRUE "
                 "at rc450 and both went FALSE the moment rc451 landed.",
         lacked_by="neither", blocked_this_rc=True, new_type=False,
         evidence="Live at rc451: 24 rows parsed from the CR_OP_REG "
                  "initialiser, and 18 executable minus CEIL_C_REJECTED_CHAINS "
                  "8 = 10 running.",
         probe="pytest tests/test_readme_c_coverage_figures_rc451.py",
         disposition=CLOSED,
         note="`#T1163` named the second half only; the first was filed "
              "nowhere. Closed by a GATE rather than by an edit — both are "
              "now keyed to the artifacts that own them (the C initialiser, "
              "parsed; and the rc446 ceiling), with a retro-check replaying "
              "the rc450 strings verbatim so loosening either predicate "
              "fails. Editing the numbers alone would have left rc452 free "
              "to repeat it.",
         ceiling_blind_to="The gate reads TWO sentences. Any third undated "
                          "cardinal in the same paragraph is still ungated."),
    dict(id="brs_proof_case_could_not_return_otherwise_rc451", kind="bug",
         missing="best_rational_signed.toml's rc420 'dead-band corner' proof "
                 "case documented a divergence its own inputs could not "
                 "produce: at max_denominator = 10^12 the chain WITHOUT the "
                 "Class-K dead_band step returns (0, 1), identical to the "
                 "shipped op. The inputs had lost a zero.",
         lacked_by="neither", blocked_this_rc=True, new_type=False,
         evidence="MEASURED: best_rational(5, 10**13, 10**12) = (0, 1) — the "
                  "1/(2*10^12) convergent's denominator EXCEEDS the cap, so "
                  "the walk keeps (0,1). At 10^13 the no-dead_band chain "
                  "returns (1, 2000000000000), the value the comment names.",
         probe="python3 ../notes/_1653_rca_probe_rc451.py",
         disposition=CLOSED,
         note="A proof case labelled 'covers = sub_dead_band' that cannot "
              "distinguish the chain WITH the step from the chain WITHOUT it "
              "is a census asserted, not measured. Fixed rather than filed "
              "because rc451 is already editing this file's adjacent "
              "MUTATIONS surface. It mattered directly: a band-literal "
              "mutation witness built on those inputs is VACUOUS (baseline "
              "== mutant == (0,1)), so the rc451 witness carries an "
              "inputs_override and the vacuous case is kept beside it as a "
              "control.",
         ceiling_blind_to="Nothing checks that a proof case labelled for a "
                          "corner actually EXERCISES it — a covers= string is "
                          "a claim, not a measurement."),
    dict(id="ledger_divergence_alarm_was_a_regex_artifact_rc451", kind="bug",
         missing="A pre-build audit reported the ledger generator holding 50 "
                 "rows against 69 on disk and warned that a regen would "
                 "DELETE 19 hand-appended rows including the one rc451 "
                 "closes. It is FALSE, and the false measurement is worth a "
                 "row because of how it was produced.",
         lacked_by="neither", blocked_this_rc=True, new_type=False,
         evidence="Re-measured BY EXECUTION at rc451: runpy over "
                  "_1653_gap_ledger.py yields 69 rows, disk holds 69 "
                  "id-bearing rows plus 1 summary, set difference empty in "
                  "BOTH directions, and full dict comparison over all 69 "
                  "shared ids differs on ZERO. The alarm's instrument was a "
                  "DOUBLE-QUOTE-ONLY regex over `id=`, which reproduces "
                  "exactly 50 here; 19 rows spell it with single quotes.",
         probe="python3 ../notes/_1653_rca_gate_provenance_rc451.py",
         disposition=CLOSED,
         note="THE WRONG OPERATOR AGAIN, inside an audit written to catch "
              "that very defect. rc450 really did close a 32-vs-51 "
              "divergence; the residual hazard is only that any regen must "
              "read universal-newline and must not commit the CRLF no-op "
              "churn. Recorded so the phantom precondition is not "
              "re-inherited — and so the DISCIPLINE survives the "
              "correction: reconcile before editing, but do it by "
              "execution, never by regex.",
         ceiling_blind_to="Nothing gates the generator against its own "
                          "output; the agreement is re-established by hand "
                          "each rc."),

    # ── item 11 / `#T1159` bucket: falsehoods found while building rc451.
    #    EVERY live value below was RE-MEASURED here, never inherited from the
    #    report that surfaced it — a filed row carrying a citation is a
    #    citation, not a measurement, which is the defect these rows are about.
    dict(id="T1159_count_pin_radius_claude_md_rc451", kind="bug",
         missing="docs/srmech/CLAUDE.md:234 states the count-pin blast radius "
                 "as '73 lines across 66 test files'.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Re-measured at rc451 with the file's OWN stated predicate, "
                  "`git grep -c \"== 663\" -- tests/`: 68 paths, of which one "
                  "is tests/RIPPLE_GATES.md matching its own predicate string "
                  "— so 67 .py files / 74 lines.",
         probe="cd python && git grep -c '== 663' -- tests/",
         disposition=FILED,
         note="Owned by `#T1159`. HONEST-BUT-STALE rather than a bare "
              "falsehood — it is explicitly dated to rc414 and the prose "
              "beside it says 'Re-measure before quoting a number here'. "
              "Filed anyway because tests/RIPPLE_GATES.md already names this "
              "exact divergence ('the tree stated two different numbers for "
              "one quantity and neither was current') and the CLAUDE.md side "
              "was never updated, so a reader landing here first still "
              "mis-scopes a count-bumping change.",
         ceiling_blind_to="This file is explicitly NOT hygiene-gated and no "
                          "ratchet reads it, so nothing but a reader catches "
                          "it going stale again."),
    dict(id="T1159_ripple_gates_md_55_rc451", kind="bug",
         missing="python/tests/RIPPLE_GATES.md:103 says 'Running all 55 here "
                 "would blur into the full suite', using 55 as the live "
                 "count-pin blast radius.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Re-measured at rc451: 67 .py files / 74 lines. The SAME "
                  "paragraph, two lines earlier, explicitly corrects 55 and "
                  "calls it 'an rc362-era figure [that] had gone ~22% low' — "
                  "and then the next sentence uses 55 again.",
         probe="cd python && git grep -c '== 663' -- tests/",
         disposition=FILED,
         note="Owned by `#T1159`. A self-correcting note that did not correct "
              "its own next sentence — worth the row for the shape: fixing a "
              "figure where it is DEFINED does not fix it where it is USED, "
              "and only a gate keyed to the live value covers both.",
         ceiling_blind_to="No gate reads RIPPLE_GATES.md's prose; the "
                          "manifest meta-test reads the .txt beside it."),
    dict(id="T1159_catalog_cardinal_three_more_surfaces_rc451", kind="bug",
         missing="The stale '17 executable / 3 leaf' catalog cardinal lives "
                 "on THREE surfaces the existing filing does not name: "
                 "docs/srmech/CLAUDE.md:325 ('20 = 17 executable + 3 explicit "
                 "leaves', BOTH cardinals wrong), "
                 "adr/0012-introspect-as-the-api-contract.md:348 ('the "
                 "section counts 17 executable / 3 leaf'), and — the "
                 "load-bearing one — "
                 "srmech/introspect/_tool_docs_curated.py:3834, which is the "
                 "SOURCE the two already-filed generated artifacts are "
                 "generated FROM.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Live at rc451: describe()['cascade_catalog'] == "
                  "{'total': 21, 'executable': 18, 'leaf': 3, "
                  "'c_runnable': 10}. klein4_from_one joined at rc438.",
         probe="python3 -c \"import srmech.introspect as I; print(I.describe()['cascade_catalog'])\"",
         disposition=FILED,
         note="Owned by `#T1159`. THE SOURCE LOCATION IS WHAT MAKES THIS "
              "ACTIONABLE. The existing row "
              "T1159_tool_docs_17_executable_vs_live_18 scopes to "
              "srmech/introspect/_tool_docs.py and the compiled "
              "c/src/srmech_tool_registry.c — both GENERATED — and its own "
              "ceiling_blind_to says 'the regen reproduces whatever the "
              "source says' without ever naming the source. A fix applied to "
              "the generated pair alone is reverted by the next "
              "tools/regen_all.py run. The ADR surface is a fourth copy and "
              "is read by test_adr_citation_integrity_rc415 / "
              "test_adr_clause_instrument_rc417. python/README.md, by "
              "contrast, already says 21 correctly.",
         ceiling_blind_to="No currency gate covers generated-artifact prose, "
                          "the ADR clause table's cardinals, or either "
                          "CLAUDE.md."),
    dict(id="T1159_symbol_census_seq_ops_resolution_rc451", kind="bug",
         missing="notes/_1653_symbol_gap.ndjson's seq_len and seq_get rows "
                 "carry resolution='DIRECT' — an assertion of AT-GRANULARITY "
                 "C coverage — while the SAME rows' own note fields say 'Vec "
                 "carrier only' and 'Vec carrier only; generic seq is "
                 "FRAMING'. A row cannot both assert and deny its own "
                 "resolution.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Re-parsed at rc451: both rows are resolution='DIRECT' with "
                  "c_symbol srmech_vec_buf_len / srmech_vec_get. Those "
                  "symbols exist, but they are typed accessors on "
                  "srmech_vec_t, while the OPS are generic-sequence framing "
                  "ops used by klein4_from_one / octonion_dft / "
                  "quaternion_dft / autocorrelation / kuramoto_step over "
                  "CR_LIST. Census tallies at rc451: DIRECT 22, COARSER 12, "
                  "FRAMING 7, ABSENT 6, summing to 47 op rows (+1 summary).",
         probe="python3 -c \"read notes/_1653_symbol_gap.ndjson and compare each row's resolution to its own note\"",
         disposition=FILED,
         note="Owned by `#T1159`. Correcting it moves two members from the "
              "DIRECT-22 tally into FRAMING-7, so it is a census edit and not "
              "a prose edit — which is why rc451 files it rather than fixing "
              "it in passing while editing the ledger next door. NOTE for "
              "whoever takes it: the rc451 brief's FRAMING-7 list named "
              "seq_len / seq_get and omitted as_quat4 / as_oct8, i.e. it "
              "described the corrected census rather than the shipped one; "
              "the shipped FRAMING-7 is as_oct8, as_quat4, byte_slice, "
              "int_parse_le, pair, str_concat, utf8_encode (re-measured).",
         ceiling_blind_to="grep of tests/ and tools/ for 'symbol_gap' returns "
                          "ZERO — nothing in the tree reads this census at "
                          "all, so no internal contradiction in it can fire."),
    dict(id="T1159_gate_matrix_c_table_counts_a_different_set_rc451", kind="bug",
         missing="notes/_1653_gate_matrix_rc445.ndjson's summary record lists "
                 "a c_table that does not equal CR_OP_REG, and says nothing "
                 "about why — inviting a future reader to 'correct' one to "
                 "match the other.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="Re-measured at rc451: the matrix c_table holds 25 "
                  "spellings; CR_OP_REG's initialiser holds 24. The delta is "
                  "exactly `orientation_compose`, which lives in the PRIVATE "
                  "single-entry fold-body table (_RUN_C_FOLD_OPS / "
                  "cr_fold_body), not in the shared dispatch table.",
         probe="python3 notes/_1653_gate_matrix_rc445.py",
         disposition=FILED,
         note="Owned by `#T1159`. NOT a contradiction — the two artifacts "
              "count different sets — but the keeping-them-separate is the "
              "whole point of the rc446 ratchet's fold-body distinction, and "
              "an artifact that states a number without stating its "
              "population is one reader away from a wrong 'fix'. Filed for a "
              "one-line population note on the summary record, not for a "
              "number change.",
         ceiling_blind_to="The agreement gate pins BLOCKED against the "
                          "matrix's per-chain rows; nothing reads the summary "
                          "record's c_table."),
    dict(id="T1159_value_parity_population_cannot_reach_ad_hoc_chains_rc451",
         kind="gap",
         missing="The rc450 value-parity comparator's population is derived "
                 "from the live ACCEPTED CATALOG set, so any chain that is not "
                 "a catalog descriptor sits outside it BY CONSTRUCTION — every "
                 "chain a user authors, and every ad-hoc chain a test builds "
                 "inline. A live C-vs-Python divergence reachable only from "
                 "such a chain is uncomparable, not merely uncompared.",
         lacked_by="neither", blocked_this_rc=False, new_type=False,
         evidence="PREDICATE, at tests/test_c_cascade_value_parity_rc450.py:375 "
                  "(_population): names = sorted(n for n, d in "
                  "_cat.load_catalog().items() if _cc.descriptor_status(d) == "
                  "'executable'), then cascade_chain_specs(name) x each entry's "
                  "declared proof_cases. MEASURED at rc451: 18 executable "
                  "descriptors -> 20 chain variants; exactly 2 of the 20 use "
                  "pin_slot_at_zero (best_rational_signed, magnitude) and ZERO "
                  "END at it, so the comparator has never once seen pin_slot's "
                  "own emitted carrier kind — both uses are INTERMEDIATE and "
                  "are consumed by @step[N].output[K], which is flag-blind. "
                  "DEMONSTRATED LIVE: rc451 flags cr_op_pin_slot's CR_LIST as a "
                  "tuple (c/src/srmech_compose_run.c:1070), moving the emitted "
                  "wire of a chain ENDING at pin_slot from {'k':'l',...} to "
                  "{'k':'t',...}; the only thing in the tree that noticed was "
                  "an AD-HOC single-step chain at "
                  "tests/test_c_ref_indexing_rc447.py:95. The divergence it "
                  "then exposed — C answering a list where "
                  "srmech.cascade.pin_slot_at_zero declares -> Tuple[int, "
                  "'Real'] and returns (-1, 3.5) — was live from rc447 through "
                  "rc450 and the comparator could not have reached it in any "
                  "of those four rcs.",
         probe="python3 -c \"from srmech.dsl import _cascade_chain as cc, "
               "_catalog as cat; from srmech.dsl._cascade_chain import "
               "cascade_chain_specs; print([(n,v) for n,d in "
               "cat.load_catalog().items() if cc.descriptor_status(d)=="
               "'executable' for v,_s,e in cascade_chain_specs(n) if "
               "(e.get('steps') or [{}])[-1].get('op','').split('.')[-1]=="
               "'pin_slot_at_zero'])\" -> [] . RUN, not asserted; the .get "
               "spellings are load-bearing because some catalog steps carry no "
               "'op' key at all (the loop / fold / parallel special forms), and "
               "an indexing probe raises KeyError before it measures anything. "
               "The NEGATIVE control is the same expression with the two "
               "pin_slot uses read at ANY position rather than the last, which "
               "returns [('best_rational_signed','default'), "
               "('magnitude','default')] — so the empty result is a measured "
               "absence and not a broken query.",
         disposition=FILED,
         note="Owned by `#T1159` (item 11). NOT a defect in the comparator's "
              "own terms — _population's docstring is explicit that it takes "
              "every EXECUTABLE chain, and the reason is sound (scoping to the "
              "ACCEPTED set would make C_REJECTED_<status> unreachable). "
              "Widening it to arbitrary chains is not a population, it is a "
              "fuzzer. Filed because the CONSEQUENCE is written down nowhere: "
              "'value parity is measured' reads as a claim about the "
              "projection, while what is measured is the projection ON THE "
              "CATALOG, in the step POSITIONS the catalog's own descriptors "
              "happen to use. The cheap half is a sentence saying so. The real "
              "question is whether carrier KIND parity deserves a population "
              "of its own: a kind divergence is reachable from a ONE-STEP "
              "chain over any op, and one-step chains are exactly what the "
              "catalog does not contain.",
         ceiling_blind_to="Every ratchet in this family counts over the same "
                          "catalog-derived population, so none of them can "
                          "detect a divergence only an off-catalog chain "
                          "reaches — the blindness is shared, not per-gate. "
                          "What caught this one was a hand-written test file, "
                          "not a ratchet, and nothing guarantees the next such "
                          "chain will have been written."),

    # ── rc452 (`#T1166`) — the exact-ℚ arc. What it closed, and what it did
    #    not. Every row below is NAMED because rc452 met it, not inherited.

    dict(id="reorient_declines_exact_rational", kind="gap",
         missing="cr_op_reorient had no CR_RATIONAL arm: handed an exact "
                 "rational it fell through to the double arm, failed to read "
                 "it, and returned SRMECH_ERR_NOT_IMPL. rational_add -> "
                 "reorient therefore threaded in NEITHER projection.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="Executed against the shipped .so at ABI 20: the two-step "
                  "chain returned rc=5 with an empty wire. At ABI 21 it "
                  "returns rc=0 and {\"d\": \"6\", \"k\": \"q\", \"n\": \"-5\"}.",
         probe="PYTHONPATH=. python3 ../notes/_rc452_c_probe.py",
         disposition=CLOSED,
         note="Zero new dispatch arms; the arm carves a FRESH carrier from the "
              "arena and aliases the write-once limbs, never negating in "
              "place. ABI 20 -> 21, and the bump's argument is new: an rc452 "
              ".so against rc451 Python produces no error at all, just a "
              "well-formed 2-tuple a Class-K consumer reads wrongly.",
         ceiling_blind_to="A rational reaching reorient through a step form "
                          "the chain runner does not yet parse. The pin is on "
                          "the op's arm, not on every route into it."),

    dict(id="python_rational_family_not_closed_under_its_return", kind="bug",
         missing="rational_add/_mul/_div/_pow_uint REJECTED a Q operand while "
                 "C's cr_as_rational accepted CR_RATIONAL directly, so the "
                 "Python family could not consume its own output.",
         lacked_by="python", blocked_this_rc=True, new_type=False,
         evidence="Measured at the rc452-s2 commit: 31 reds across five test "
                  "files, all carrying one error class -- 'TypeError: a|b must "
                  "be 2-tuple (num, den); got Q(...)'. All 31 go green on the "
                  "acceptance-widening with ZERO edits to any failing file.",
         probe="PYTHONPATH=. python3 ../notes/_rc452_red_experiment.py --expect-red",
         disposition=CLOSED,
         note="kind='bug', not 'gap': C ANSWERED where Python RAISED on the "
              "same shape, so this was a divergence, not a capability the "
              "projection declined to offer. The co-equality is the oracle -- "
              "the contract named C correct and Python widened to match.",
         ceiling_blind_to="An op OUTSIDE the four binary ones growing a pair "
                          "operand later. The boundary is derived from "
                          "cr_as_rational's two call sites, so a third call "
                          "site added in C without the Python peer is not "
                          "counted by anything here."),

    dict(id="value_parity_population_has_no_rational_terminal_chain",
         kind="gap",
         missing="The value-parity comparator's population (the [cascade] "
                 "catalog's proof cases) contains NO chain whose final value "
                 "is an exact rational, so the comparator has never judged a "
                 "`q` even though the wire carries 39 of them per run.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="rc452's emitted-kind gate, executed: population A (98 "
                  "declared proof cases, 48 emitting) tallies {f:13, i:48, "
                  "l:4, t:9} and NO q. Population B (51 AMSC operator_chain "
                  "rows, 51 emitting) tallies {q:39, s:12}. The two sets do "
                  "not overlap on q, which is exactly why the collapse "
                  "survived every value-level instrument in the tree.",
         probe="PYTHONPATH=. python3 -m pytest "
               "tests/test_wire_kind_emission_rc452.py -s",
         disposition=FILED,
         note="rc452's PLAN called for a proof-case chain to close this and it "
              "is NOT buildable as specified: every [cascade] descriptor must "
              "name a real DSL-resolvable op (tests/test_dsl.py pins the set) "
              "and there is no rational-family cascade op -- the Class-N "
              "rationals are catalogued as AMSC operator_chains instead. A `q` "
              "row in population A therefore costs a NEW PUBLIC CALLABLE plus "
              "its descriptor, which moves the tool-count axis across ~73 test "
              "files. Priced, named, deferred -- and PINNED down-only as "
              "CEIL_UNEMITTED_IN_POPULATION_A so it cannot widen quietly.",
         ceiling_blind_to="The pin is on which KINDS population A emits, not "
                          "on whether population A is the right population. A "
                          "kind emitted by neither set is caught by the union "
                          "ceiling; a kind emitted only by B stays a named "
                          "gap and nothing forces it shut."),

    dict(id="wire_kind_n_emitted_by_nothing", kind="gap",
         missing="CR_NONE (`n`) is declared by the C writer and branched on by "
                 "the Python reader, and no executed row of EITHER population "
                 "emits it. No producer has ever been found.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="rc452's emitted-kind gate over both populations: the union "
                  "residual is exactly {n}. THE PLAN PREDICTED {n, s} AND WAS "
                  "WRONG ABOUT s -- `s` IS emitted, 12 times, by pi_digits. "
                  "The two workshops that disagreed were each right about a "
                  "different population, which is why it never resolved.",
         probe="PYTHONPATH=. python3 -m pytest "
               "tests/test_wire_kind_emission_rc452.py -s",
         disposition=FILED,
         note="Closable by auditing every cr_op_* return path for a CR_NONE "
              "result. rc452 does not; it pins the residual DOWN-ONLY so a "
              "second dark kind cannot join it silently.",
         ceiling_blind_to="A kind that is emitted but never REACHES a "
                          "comparator -- the census walks wires that a chain "
                          "actually returned, so a kind produced only inside a "
                          "step and consumed before the final value is "
                          "invisible to it."),

    dict(id="dead_band_and_scale_round_accept_q_in_python_only", kind="gap",
         missing="dead_band and scale_round_half_even accept a Q in Python and "
                 "DECLINE a non-CR_DBL operand in C, so the two projections "
                 "disagree on what they accept even though neither is wrong.",
         lacked_by="c", blocked_this_rc=False, new_type=False,
         evidence="cr_op_dead_band's own comment states the decline and its "
                  "reason (reading an int through cr_arg_dbl would answer 5.0 "
                  "where Python answers 5 -- a silent wrong answer, not a "
                  "capability gap). The rc452 workshop priced the repair at "
                  "one q arm each, zero new dispatch arms.",
         probe="grep -n cr_op_dead_band c/src/srmech_compose_run.c",
         disposition=FILED,
         note="NAMED rather than inherited, per the ruling's own open-questions "
              "list. Ops that diverge on what they ACCEPT are not at parity "
              "even when neither projection gives a wrong answer. Contrast the "
              "measured PARITY-LEGAL decline this rc pins: reorient refuses a "
              "bare [num, den] list on BOTH sides, deliberately.",
         ceiling_blind_to="Nothing counts acceptance-set divergence. This row "
                          "is prose because the tree has no instrument that "
                          "enumerates, per op, what each projection takes."),

    dict(id="mcp_wire_spells_a_rational_as_a_pair", kind="gap",
         missing="The rc414 MCP envelope deliberately excludes Q, so the same "
                 "rational is spelled [num, den] on the MCP wire and `q` on "
                 "the chain wire. rc452 WIDENS that divergence: the "
                 "Q-returning tool population grows 27 -> 36.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="Re-derived at rc452 by execution rather than inherited: the "
                  "carrier back-index (a token scan over the ToolEntry types) "
                  "now lists 36 ops under Q.produces, up from 27. No MCP "
                  "round-trip was executed under the change.",
         probe="PYTHONPATH=. python3 -c \"from srmech.introspect."
               "carrier_schema import _pure_carrier_schema as S; "
               "print(len(S()['Q']['ops']['produces']))\"",
         disposition=FILED,
         note="rc452 DID have to repair the C half of this surface: respelling "
              "the four binary ops' param type dropped SIX ops off the native "
              "invoke_tool surface silently, because mm_action_for is an exact "
              "strcmp. Fixed in both projections string-for-string. The "
              "SPELLING divergence itself is not reconciled here.",
         ceiling_blind_to="Nothing executes an MCP round-trip over the widened "
                          "population, so a coercion that is wrong rather than "
                          "merely absent would not show up as a red."),

    dict(id="exact_q_cannot_enter_a_chain", kind="gap",
         missing="json.dumps(Q) raises TypeError, so an exact rational can "
                 "only ENTER a chain spelled [num, den]. rc452 closes the "
                 "RETURN direction only; the wire is asymmetric.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="Executed and PINNED, not asserted: "
                  "tests/test_exact_q_pipeline_rc452.py::"
                  "test_json_dumps_of_a_q_still_raises_so_the_input_direction_"
                  "is_open. The ruling's open-questions list is single-sourced "
                  "on this fact, so it is given a test rather than a sentence.",
         probe="PYTHONPATH=. python3 -m pytest "
               "tests/test_exact_q_pipeline_rc452.py -k json_dumps",
         disposition=FILED,
         note="This is WHY the (num, den) pair survives ADJ-4 as a legitimate "
              "INPUT spelling on both projections. It is not deprecated and "
              "must not be 'cleaned up'.",
         ceiling_blind_to="The row is about the ctx wire's JSON encoder. A "
                          "future encoder that serialised Q would close it "
                          "without anything here noticing the row went stale."),

    dict(id="mat_vec_coerce_exact_q_to_float_at_construction", kind="bug",
         missing="Mat and Vec are array('d') float64 and SILENTLY coerce a Q "
                 "to float at construction, so exact ℚ dies BELOW every wire "
                 "rc452 touches.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="Two independent workshop executions. rc452 does not "
                  "re-derive it and does not claim to have measured it.",
         probe="n/a -- inherited from the rc452 workshop, NOT re-executed here",
         disposition=FILED,
         note="A live 'returning to float is the default' violation at the "
              "CARRIER layer that no wire configuration can touch. rc452 reads "
              "the mandate's 'Mat/Vec/HV are carriers too' as exact-ℚ reach "
              "via Q, depth-1 containers, and the exact peers (QMat / Poly / "
              "BiPoly, deferred). THAT REINTERPRETATION NEEDS EXPLICIT USER "
              "SIGN-OFF and rc452 flags it as PENDING rather than assuming it.",
         ceiling_blind_to="Everything. There is no instrument in this family "
                          "that looks below the wire at carrier storage."),

    dict(id="depth_ge_2_exact_carriers_do_not_cross", kind="gap",
         missing="Exact carriers nested two or more levels deep (QMat, Poly, "
                 "BiPoly) do not cross the chain wire. rc452's q spelling "
                 "banks ONE nesting level; the next costs an explicit "
                 "non-recursive loop.",
         lacked_by="both", blocked_this_rc=False, new_type=False,
         evidence="Three independent workshop counts agree at ~22-24 "
                  "non-recursive lines per level; JPL Rule 1 forbids the "
                  "recursive shortcut. rc452 PINS the depth-1 boundary from "
                  "both sides: a q inside a t rebuilds as a Q, and pair(Q, Q) "
                  "marshals -- both executed against the real library.",
         probe="PYTHONPATH=. python3 -m pytest "
               "tests/test_c_cascade_value_parity_rc450.py "
               "-k 'pair_of_rationals or rational_inside_a_tuple'",
         disposition=FILED,
         note="Deferred to a follow-on arc with a measured price attached, "
              "which is the difference between a deferral and a silence.",
         ceiling_blind_to="Nothing enumerates the depth of the carriers a "
                          "descriptor could produce, so a descriptor authored "
                          "at depth 2 would decline rather than red."),
]


def scan_op_exports():
    """Live: which of the remaining chains' ops have a C symbol."""
    lib = os.path.join(SRM, "c", "build", "libsrmech.a")
    if not os.path.exists(lib):
        return None
    syms = subprocess.run(["nm", "-g", "--defined-only", lib],
                          capture_output=True, text=True).stdout
    return sorted(set(re.findall(r"\bT (srmech_[A-Za-z0-9_]+)", syms)))


def main():
    ids = [r["id"] for r in ROWS]
    assert len(ids) == len(set(ids)), (
        "duplicate row id(s): %s"
        % sorted({i for i in ids if ids.count(i) > 1}))
    for r in ROWS:
        assert r["disposition"] in (CLOSED, FILED, DECLINED), r["id"]
        assert r["kind"] in ("gap", "bug", "decline"), r["id"]
        assert r["lacked_by"] in LACKED_BY_VALUES, (
            "%s: lacked_by=%r is outside the documented vocabulary %s"
            % (r["id"], r["lacked_by"], sorted(LACKED_BY_VALUES)))
        assert r["ceiling_blind_to"], "%s: every row must say what a seeded " \
                                      "ceiling cannot detect" % r["id"]
    # Down-only on the two rc450 placeholders. A ceiling that only forbids
    # GROWTH would let the placeholders sit forever; `==` forces the number to
    # be lowered consciously when a row is attributed.
    n_unstated_lacked = sum(1 for r in ROWS if r["lacked_by"] == "unstated")
    assert n_unstated_lacked == CEIL_UNSTATED_LACKED_BY, (
        "%d row(s) carry lacked_by='unstated'; the ceiling is %d. If you "
        "ATTRIBUTED one, lower CEIL_UNSTATED_LACKED_BY to %d. If this grew, a "
        "new row was written without naming a projection, which is the state "
        "the placeholder exists to drain rather than to normalise."
        % (n_unstated_lacked, CEIL_UNSTATED_LACKED_BY, n_unstated_lacked))
    n_unstated_cbt = sum(1 for r in ROWS
                         if r["ceiling_blind_to"] == UNSTATED_CEILING_BLIND_TO)
    assert n_unstated_cbt == CEIL_UNSTATED_CEILING_BLIND_TO, (
        "%d row(s) carry the rc450 ceiling_blind_to placeholder; the ceiling "
        "is %d. Same rule as above."
        % (n_unstated_cbt, CEIL_UNSTATED_CEILING_BLIND_TO))
    by = {}
    for r in ROWS:
        by[r["disposition"]] = by.get(r["disposition"], 0) + 1
    kinds = {}
    for r in ROWS:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1

    print("gh #1653 GAP LEDGER — %d rows" % len(ROWS))
    print()
    print("%-32s %-8s %-7s %-9s %s" % ("id", "kind", "lacks", "new_type", "disposition"))
    print("-" * 84)
    for r in sorted(ROWS, key=lambda x: (x["disposition"], x["id"])):
        print("%-32s %-8s %-7s %-9s %s"
              % (r["id"], r["kind"], r["lacked_by"],
                 "YES" if r["new_type"] else "no", r["disposition"]))
    print()
    print("by disposition:", json.dumps(by, sort_keys=True))
    print("by kind       :", json.dumps(kinds, sort_keys=True),
          "  <- gaps/bugs/declines are NEVER totalled together")
    print("blocked this rc:", sum(1 for r in ROWS if r["blocked_this_rc"]))
    print("NEW TYPE (must close its projection gap in the same change):",
          sum(1 for r in ROWS if r["new_type"]))
    syms = scan_op_exports()
    if syms:
        print("live C export count:", len(syms))
    try:
        from srmech.version import __version__ as _rc
    except Exception:                                   # pragma: no cover
        _rc = None
    summary = {"record": "summary", "rows": len(ROWS), "rc": _rc,
               "by_disposition": by, "by_kind": kinds,
               "c_exports": len(syms) if syms else None}
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in ROWS:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
        fh.write(json.dumps(summary, sort_keys=True) + "\n")

    # ── THE SUMMARY CANNOT DISAGREE WITH WHAT IT SUMMARISES ─────────────────
    # rc450 (`#T1160`). The shipped .ndjson said {"rows": 39} beside 51 rows,
    # with 16/2/21 by disposition against a real 18/4/29 — and it carried an
    # "rc" key this writer never emitted. That is not a stale count: it is
    # proof the file had been written by something other than this function
    # and never re-checked. The fix is not a bigger number, it is a RE-READ:
    # parse back what was just written and assert the summary against it. A
    # summary computed from ROWS and checked against ROWS would agree with
    # itself; this one is checked against the BYTES ON DISK.
    disk_rows, disk_summary = [], None
    with open(OUT, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            (disk_rows.append(rec) if rec.get("record") != "summary"
             else None)
            if rec.get("record") == "summary":
                disk_summary = rec
    assert disk_summary is not None, "no summary record was written"
    assert len(disk_rows) == disk_summary["rows"] == len(ROWS), (
        "the summary says rows=%s, the file holds %d parsed rows, and ROWS "
        "holds %d — this is the rc449 defect, live again."
        % (disk_summary.get("rows"), len(disk_rows), len(ROWS)))
    disk_by = {}
    for rec in disk_rows:
        disk_by[rec["disposition"]] = disk_by.get(rec["disposition"], 0) + 1
    assert disk_by == disk_summary["by_disposition"] == by, (
        "by_disposition disagrees: on disk %s, in summary %s, from ROWS %s"
        % (disk_by, disk_summary["by_disposition"], by))
    assert set(disk_by) <= {CLOSED, FILED, DECLINED}, (
        "a FOURTH disposition reached disk: %s" % sorted(disk_by))
    print("re-read %d rows from disk; summary agrees on rows and dispositions"
          % len(disk_rows))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
