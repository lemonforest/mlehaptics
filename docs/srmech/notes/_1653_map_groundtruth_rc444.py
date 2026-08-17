#!/usr/bin/env python3
"""gh #1653 round-2 measurement 2 of 3 — GROUND TRUTH for the map-arm C
prototype, taken from the SHIPPED Python projection at 0.9.0rc444.

Nothing in `_1653_proto_map.c` is hand-derived. This script produces:

  A. the klein4_from_one "rest" chain's step[7] and step[8] outputs — the two
     values its map step binds (`hexb`, `jdiv4`) — computed by running the
     descriptor's OWN steps 0..8 through the shipped leaves;
  B. the 64 crumbs the shipped chain returns for the same inputs, i.e. the
     value the C prototype's positive case must reproduce EXACTLY;
  C. a cross-check of (B) against the shipped op `klein4_from_one(one, 64)`,
     so the expectation is anchored to the op and not only to the descriptor;
  D. the 4x4 mod-4 index table the nested-map positive case must reproduce,
     computed with srmech's own Class-I `mod_add` (not a Python `%`).

Emits the C literals ready to paste, and writes
docs/srmech/notes/_1653_map_groundtruth_rc444.ndjson.

No numpy, no RNG, no floats, no stdlib fractions.
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "python"))

import srmech                                     # noqa: E402
from srmech.amsc.descriptor import render_template  # noqa: E402
from srmech.amsc.format import sha256_bytes       # noqa: E402
from srmech.cascade import leaves                 # noqa: E402
from srmech.math.cyclic import mod_add            # noqa: E402
from srmech import dsl                            # noqa: E402

OUT = HERE / "_1653_map_groundtruth_rc444.ndjson"

JDIV4 = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3,
         4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7,
         8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 11,
         12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 15, 15, 15, 15]

CASE = {"sigma": 1, "theta_num": 1, "theta_den": 1, "terms": 24}


def steps_0_to_8(case):
    """The klein4_from_one 'rest' chain steps 0..8, run as the descriptor
    declares them (render_template / utf8_encode / sha256_bytes /
    str_concat / seq_get)."""
    s0 = render_template(
        '{"sigma":{sigma},"terms":{terms},"theta":[{tn},{td}]}',
        {"sigma": case["sigma"], "terms": case["terms"],
         "tn": case["theta_num"], "td": case["theta_den"]})
    s1 = leaves.utf8_encode(text=s0)
    s2 = sha256_bytes(s1)
    if isinstance(s2, bytes):                # sha256_bytes returns hex str
        raise SystemExit("unexpected: sha256_bytes returned bytes")
    s3 = leaves.str_concat(prefix=s2, text="|")
    s4 = leaves.str_concat(prefix=s3, text="0")
    s5 = leaves.utf8_encode(text=s4)
    s6 = sha256_bytes(s5)
    s7 = leaves.utf8_encode(text=s6)
    s8 = leaves.seq_get(seq=[JDIV4], i=0)
    return s0, s2, s6, s7, s8


def main():
    rec = []
    print(f"srmech {srmech.__version__}  "
          f"native={srmech.native_status()['has_native']}")

    s0, digest1, digest2, s7, s8 = steps_0_to_8(CASE)
    assert list(s8) == JDIV4, "step[8] must be the literal jdiv4 table"
    hexb = s7.decode("ascii") if isinstance(s7, bytes) else s7
    assert len(hexb) == 64, f"step[7] length {len(hexb)}"

    crumbs = dsl.run_cascade_chain("klein4_from_one", variant="rest", **CASE)
    if isinstance(crumbs, tuple):
        crumbs = list(crumbs)
    assert isinstance(crumbs, list) and len(crumbs) == 64, str(type(crumbs))

    # (C) anchor to the shipped op, not only the descriptor.
    op_match = None
    try:
        from srmech.cascade.one import the_one
        from srmech.math.hdc import klein4_from_one as k4
        one = the_one(sigma=CASE["sigma"],
                      theta_num=CASE["theta_num"],
                      theta_den=CASE["theta_den"],
                      terms=CASE["terms"])
        hv = k4(one, 64)
        got = list(getattr(hv, "data", hv))
        op_match = [int(v) for v in got] == [int(c) for c in crumbs]
    except Exception as exc:                  # report, never mask
        op_match = f"cross-check unavailable: {exc!r}"

    print(f"\nA. step[0] render  = {s0}")
    print(f"   stage-1 digest  = {digest1}")
    print(f"   stage-2 digest  = {digest2}")
    print(f"   step[7] hexb    = {hexb}")
    print(f"   step[8] jdiv4   = {len(list(s8))} entries")
    print(f"\nB. chain crumbs (64) = {list(crumbs)}")
    print(f"\nC. shipped-op cross-check = {op_match}")

    # (D) the nested-map table, via srmech's Class-I op.
    n = 4
    table = [[mod_add(i, k, n) for i in range(n)] for k in range(n)]
    print(f"\nD. nested-map mod_add table n={n} = {table}")

    rec.append({"record": "klein4_rest_case", "inputs": CASE,
                "render": s0, "digest_stage1": digest1,
                "digest_stage2": digest2, "hexb": hexb,
                "jdiv4_len": len(list(s8)),
                "crumbs": [int(c) for c in crumbs],
                "shipped_op_cross_check": op_match,
                "srmech_version": srmech.__version__})
    rec.append({"record": "nested_map_mod_add_table", "n": n,
                "table": table})
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rec:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    print("\n--- C literals ---")
    print('static const char HEXB[65] = "%s";' % hexb)
    print("static const int8_t EXPECT_CRUMBS[64] = {%s};"
          % ",".join(str(int(c)) for c in crumbs))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
