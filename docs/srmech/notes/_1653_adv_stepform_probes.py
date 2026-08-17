#!/usr/bin/env python3
"""ADVERSARIAL step-form NEGATIVE CONTROLS — the gap the census left open.

The census reports ``step_forms_c_chain_run = 1`` (only the PLAIN form), but
that env field is HARDCODED from a source read, and only two thirds of it is
covered by a measurement on a real chain:

  * plain  ACCEPTED  — proven by the census's positive controls (and mine).
  * fold   REJECTED  — proven by ``net_chirality``, whose step 0 IS a fold.
  * map    ???       — NOT PROVEN.  No cascade-catalog chain carries a map step
                       at position 0, so the C run loop short-circuits on an
                       out-of-table plain op BEFORE it ever sees the map step.
                       The map verdict is a PREDICTION, not a measurement.

This script mints minimal synthetic chains that isolate each form, using ONLY
``rational_add`` — an op that IS in the C run loop's 10-entry table — so the op
table cannot be the thing doing the rejecting.  Every rejection here is
therefore attributable to the STEP FORM alone.

Emitted as plain JSON for the bare-C driver, so the verdict does not depend on
the ctypes harness under audit.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_1653_adv_barec")

PLAIN = {"class": "N", "op": "rational_add",
         "args": {"a": [1, 2], "b": [1, 3]}}

# Each probe: (base_name, steps, expectation, why)
PROBES = (
    # 1. plain only — the accept baseline, op IS in the C table.
    ("sf1_plain_only", [dict(PLAIN)], 0,
     "plain form + in-table op: the C run loop's ONLY supported shape"),

    # 2. map at step 0, body is a single in-table plain op.  If the C run loop
    #    implemented the map form this would run; the op table cannot be the
    #    blocker because rational_add is in it.
    ("sf2_map_at_step0", [
        {"map_over": "@input.xs", "index": "i", "bind": "x",
         "body": [{"class": "N", "op": "rational_add",
                   "args": {"a": "@bind.x", "b": [1, 3]}}]}], 2,
     "map form, in-table body op: isolates the STEP FORM from the op table"),

    # 3. map at step 1, AFTER an accepted in-table plain step.  Proves the run
    #    loop reaches the map step and still declines it — i.e. the decline is
    #    not an artifact of the map happening to be first.
    ("sf3_plain_then_map", [
        dict(PLAIN),
        {"map_over": "@input.xs", "index": "i", "bind": "x",
         "body": [{"class": "N", "op": "rational_add",
                   "args": {"a": "@bind.x", "b": [1, 3]}}]}], 2,
     "plain step 0 dispatches, then a map step 1: the loop REACHES the map"),

    # 4. fold at step 0 with an in-table fold_op — the fold twin of probe 2.
    ("sf4_fold_at_step0", [
        {"fold_class": "N", "fold_op": "rational_add",
         "fold_init": [0, 1], "over": "@input.xs"}], 2,
     "fold form, in-table fold_op: isolates the STEP FORM from the op table"),

    # 5. plain step whose op is OUT of the C table — isolates the OP TABLE from
    #    the step form (the mirror image of probes 2/4).  Must be 5, not 2.
    ("sf5_plain_out_of_table", [
        {"class": "I", "op": "gcd", "args": {"a": 12, "b": 18}}], 5,
     "plain form, OUT-of-table op: isolates the op table from the step form"),

    # 6. plain + in-table op, but an @idx reference C's namespace matcher does
    #    not know.  The RUN loop resolves args only inside cr_dispatch, so this
    #    distinguishes 'namespace unknown' (a PARSE gate) from a run gate.
    ("sf6_plain_unknown_ns", [
        {"class": "N", "op": "rational_add",
         "args": {"a": "@idx.i", "b": [1, 3]}}], None,
     "plain + in-table op + @idx ref: is @idx a RUN gate or only a PARSE gate?"),
)


def main():
    os.makedirs(OUT, exist_ok=True)
    ctx = {"row": None, "inputs": {"xs": [[1, 2], [1, 4]], "i": 0}}
    probe = {"row": None, "inputs": {}}
    names = []
    for base, steps, expect, why in PROBES:
        chain = {"name": "probe.%s" % base, "summary": why,
                 "returns": "value", "on_error": "raise", "steps": steps}
        for suffix, obj in (("chain", chain), ("ctx", ctx), ("probe", probe)):
            with open(os.path.join(OUT, "%s.%s.json" % (base, suffix)),
                      "w", encoding="utf-8") as fh:
                fh.write(json.dumps(obj, ensure_ascii=False))
        names.append(base)
        print("%-24s expect_run_rc=%-4s  %s" % (base, expect, why))
    with open(os.path.join(HERE, "_1653_adv_barec", "stepform_names.txt"),
              "w", encoding="utf-8") as fh:
        fh.write(" ".join(names) + "\n")
    print("\nnames: %s" % " ".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
