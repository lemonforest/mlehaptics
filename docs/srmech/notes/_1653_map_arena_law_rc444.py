#!/usr/bin/env python3
"""gh #1653 round-2 addendum — the map arm's ARENA LAW, and the measured
shortfall of the SHIPPED `srmech_chain_run_arena_bytes` sizing helper.

Report section 6.2 sub-problem 3 states the nested-map arena is quadratic and
reports a crossover figure it marks INHERITED and un-rerun. The C prototype
(_1653_proto_map.c, POSITIVE 4 / 4b) measures it directly by bisecting the
smallest total arena that runs the depth-2 nested map at each n. This script
takes those measured totals and answers the two questions the report leaves
open:

  1. Is the arena bound expressible as a COMPILE-TIME CONSTANT?
  2. Does the SHIPPED sizing helper `srmech_chain_run_arena_bytes(chain_len,
     ctx_len)` — which is LINEAR in the two JSON lengths — provision enough?

The shipped formula is transcribed verbatim from
c/src/srmech_compose_run.c srmech_chain_run_arena_bytes:
    parse = 128 * chain_len + 128 * ctx_len + 65536
(the per-step op scratch it adds on top is for the Class-N bignum ops and does
not scale with a map's iteration count, so `parse` is the term that would have
to carry the map carriers).

No numpy, no RNG, no floats in the accounting (the ratio is printed as a
rational reduced by srmech's own Class-N best_rational as well as a decimal,
so the ratio is exact and the decimal is display-only).
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "python"))

from srmech.math.rational import best_rational   # noqa: E402

OUT = HERE / "_1653_map_arena_law_rc444.ndjson"

# MEASURED by /tmp/proto_map (notes/_1653_proto_map.c POSITIVE 4b): the
# smallest TOTAL arena, found by bisection, for which the depth-2 nested map
# at outer n x inner n completes with SRMECH_OK.
MEASURED_MIN_TOTAL = {32: 447216, 64: 989936, 128: 3156720, 256: 11815664}

# The prototype's own fixed overhead, which is NOT part of the map carriers:
# sizeof(pm_state_t) plus two PM_JSON_WS (131072-byte) parse workspaces.
PROTO_FIXED = 264720

SIZEOF_CARRIER = 56          # sizeof(pm_value_t) on this target


def chain_ctx(n):
    """The exact two strings pm_build_n2 emits for this n."""
    chain = ('{"steps":[{"map_over":"@input.xs","index":"k",'
             '"bind":{"xs":"@input.xs","n":%d},'
             '"body":[{"map_over":"@bind.xs","index":"i",'
             '"body":[{"class":"I","op":"mod_add",'
             '"args":{"a":"@idx.i","b":"@idx.k","n":"@bind.n"}}]}]}]}') % n
    ctx = '{"row":null,"inputs":{"xs":[%s]}}' % ",".join(
        str(i) for i in range(n))
    return chain, ctx


def shipped_formula(chain_len, ctx_len):
    """srmech_chain_run_arena_bytes' `parse` term, verbatim."""
    return 128 * chain_len + 128 * ctx_len + 65536


def main():
    rows = []
    print("=== #1653 round-2: the map arm's arena law (MEASURED) ===\n")
    print(f"{'n':>5} {'cells':>7} {'carrier_bytes':>14} {'per_cell':>9} "
          f"{'ctx_len':>8} {'shipped':>10} {'shortfall':>10}")
    for n, total in sorted(MEASURED_MIN_TOTAL.items()):
        chain, ctx = chain_ctx(n)
        carrier = total - PROTO_FIXED
        cells = n * n
        shipped = shipped_formula(len(chain), len(ctx))
        num, den = best_rational(carrier, shipped, 10000)
        rows.append({
            "record": "arena_point",
            "n": n,
            "cells": cells,
            "measured_min_total_bytes": total,
            "proto_fixed_overhead_bytes": PROTO_FIXED,
            "carrier_bytes": carrier,
            "bytes_per_cell": carrier // cells,
            "chain_len": len(chain),
            "ctx_len": len(ctx),
            "shipped_arena_bytes_parse_term": shipped,
            "shortfall_exact_rational": [num, den],
        })
        print(f"{n:5d} {cells:7d} {carrier:14d} {carrier // cells:9d} "
              f"{len(ctx):8d} {shipped:10d} {num}/{den}")

    per = [r["bytes_per_cell"] for r in rows]
    verdict = {
        "record": "verdict",
        "bytes_per_cell_series": per,
        "bytes_per_cell_converges_to": per[-1],
        "carrier_struct_bytes": SIZEOF_CARRIER,
        "carriers_per_cell": per[-1] // SIZEOF_CARRIER,
        "law": ("carrier_bytes ~ PRODUCT(n_i over nested map levels) * "
                "(carriers_per_body_step * sizeof(carrier)) + "
                "SUM(accumulator pointer arrays)"),
        "compile_time_constant": False,
        "why_not": ("every n_i is len(resolve(map_over)) — a RUNTIME datum. A "
                    "compile-time cap would have to bound the PRODUCT of the "
                    "nested lengths, so a 2-level map over a 4096-element "
                    "input would need a 4096^2-cell arena reserved "
                    "unconditionally."),
        "shipped_helper_is_sufficient": False,
        "shipped_helper_defect": ("srmech_chain_run_arena_bytes is LINEAR in "
                                  "ctx_len; the map need is a PRODUCT of the "
                                  "nested map_over lengths, so the shortfall "
                                  "GROWS with n"),
        "shortfall_multiple_at_n": {str(r["n"]):
                                    r["carrier_bytes"] //
                                    r["shipped_arena_bytes_parse_term"]
                                    for r in rows},
    }
    rows.append(verdict)
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    print("\n--- verdict ---")
    for k, v in verdict.items():
        if k == "record":
            continue
        print(f"  {k}: {v}")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
