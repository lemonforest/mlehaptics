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
                  "dsl/_chain.py _desc_to_value: f i l n s t. Consequence "
                  "measured: best_rational_signed returns tuple[int,int], which "
                  "the DSL wire can carry and the chain-run wire CANNOT.",
         probe="python3 notes/_1653_return_types.py",
         disposition=FILED,
         note="Neither wire is a superset of the other, so the SAME Python value "
              "has different expressibility depending on which surface runs it — "
              "and the identical {\"k\":...} spelling makes them look like one "
              "shared standard. If a requested-return-type contract is going to "
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
    for r in ROWS:
        assert r["disposition"] in (CLOSED, FILED, DECLINED), r["id"]
        assert r["kind"] in ("gap", "bug", "decline"), r["id"]
        assert r["lacked_by"] in ("c", "python", "both"), r["id"]
        assert r["ceiling_blind_to"], "%s: every row must say what a seeded " \
                                      "ceiling cannot detect" % r["id"]
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
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in ROWS:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
        fh.write(json.dumps({"record": "summary", "rows": len(ROWS),
                             "by_disposition": by, "by_kind": kinds,
                             "c_exports": len(syms) if syms else None},
                            sort_keys=True) + "\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
