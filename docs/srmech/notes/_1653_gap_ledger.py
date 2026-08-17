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
    dict(id="carrier_double", kind="gap",
         missing="cr_value_t has no DOUBLE kind, so a real-number literal in an "
                 "arg and a float-valued result are both unrepresentable in C.",
         lacked_by="c", blocked_this_rc=True, new_type=True,
         evidence="gate matrix: real_literal_arg blocks 9 chains, carrier_width 4.",
         probe="python3 notes/_1653_gate_matrix_rc445.py",
         disposition=FILED,
         note="NEW TYPE. Widening cr_value_t is exactly the 'a new type widens a "
              "discriminator set and must close its projection gap in the SAME "
              "change' rule. It very likely bumps ABI 17->18: the output value "
              "descriptor gains a kind, which is a wire-format change, and a "
              "stale .so would then mis-read a descriptor it still believes it "
              "understands. Cost: every op that consumes or produces a value.",
         ceiling_blind_to="A carrier kind no shipped descriptor produces yet "
                          "(complex, interval) — the count is over TODAY's chains."),
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
    dict(id="ref_grammar_output_index", kind="gap",
         missing="cr_resolve_ref parses only a BARE `.output`; `@step[N].output[K]` "
                 "element indexing is rejected.",
         lacked_by="c", blocked_this_rc=True, new_type=False,
         evidence="srmech_compose_run.c cr_resolve_ref: 'only bare `.output` "
                  "supported'. Gate matrix: 2 chains.",
         probe="python3 notes/_1653_gate_matrix_rc445.py",
         disposition=FILED,
         note="Not a new type — the walker already handles `.key`/`[N]` paths for "
              "@row and @input; the step arm just does not call it.",
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
         missing="Surface A's FOLD form is unrecognised by C (BAD_INPUT=2).",
         lacked_by="c", blocked_this_rc=True, new_type=True,
         evidence="notes/_1653_step_forms_rc444.ndjson.",
         probe="python3 notes/_1653_step_forms_rc444.py",
         disposition=FILED,
         note="PROTOTYPED: notes/_1653_proto_fold.c compiles and runs, 4/4 "
              "negative-shape probes correct.",
         ceiling_blind_to="Same as step_form_map."),
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
         evidence="24 of 34 probes: pure raises, native returns a value; 0 of 34 in "
                  "the 'C lacks a capability' cell. 5 ops affected. And there is NO "
                  "key-set validator anywhere in the C leaf surface to copy — the 2 "
                  "apparently clean ops reject via a PYTHON TypeError on both paths.",
         probe="python3 notes/_1653_t1146_rejection_parity_rc444.py",
         disposition=FILED,
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
