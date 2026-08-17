#!/usr/bin/env python3
"""gh #1653 round-2 — GENERATOR for `_1653_proto_map_data.h`.

The map-arm C prototype's positive case is klein4_from_one's own map step: 19
body steps, 8 binds, one of them a 55-entry table and one a 64-entry table.
Hand-transcribing that into a C string literal would be a provenance hole and a
transcription risk, so it is GENERATED here, straight out of the shipped
descriptor TOML, and the header records the file + sha256 it came from.

Emits:
  PM_K4_CHAIN    the chain JSON: nine `null` placeholders (steps 0..8, which
                 the map arm does not claim) then the map step VERBATIM
  PM_K4_CTX      the run context, whose "pre" array carries the MEASURED
                 outputs of steps 7 and 8 (from _1653_map_groundtruth_rc444.py)
  PM_K4_EXPECT   the 64 crumbs the shipped Python projection returns

No numpy, no RNG, no floats.
"""

import hashlib
import json
import pathlib
import sys
import tomllib

HERE = pathlib.Path(__file__).resolve().parent
CAT = (HERE.parents[0] / "python" / "srmech" / "cascade" / "catalogs"
       / "cascade_catalog")
TOML = CAT / "klein4_from_one.toml"
GT = HERE / "_1653_map_groundtruth_rc444.ndjson"
OUT = HERE / "_1653_proto_map_data.h"


def c_chunks(s, per=64):
    """`s` as adjacent C string literals, `per` source bytes each."""
    esc = s.replace("\\", "\\\\").replace('"', '\\"')
    parts, cur, n = [], [], 0
    i = 0
    while i < len(esc):
        ch = esc[i]
        if ch == "\\":                      # never split an escape pair
            cur.append(esc[i:i + 2])
            n += 2
            i += 2
        else:
            cur.append(ch)
            n += 1
            i += 1
        if n >= per:
            parts.append("".join(cur))
            cur, n = [], 0
    if cur:
        parts.append("".join(cur))
    return parts


def main():
    raw = TOML.read_bytes()
    doc = tomllib.loads(raw.decode("utf-8"))
    chains = doc["cascade"]["chain"]
    rest = [c for c in chains if c.get("variant") == "rest"]
    assert len(rest) == 1, f"expected 1 rest variant, got {len(rest)}"
    steps = rest[0]["steps"]
    map_steps = [(i, s) for i, s in enumerate(steps) if "map_over" in s]
    assert len(map_steps) == 1, f"expected 1 map step, got {len(map_steps)}"
    mi, mstep = map_steps[0]
    assert mi == 9, f"map step index moved: {mi}"

    gt = None
    for line in GT.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("record") == "klein4_rest_case":
            gt = rec
    assert gt is not None, "ground-truth record missing; run the gt script"
    assert gt["shipped_op_cross_check"] is True, gt["shipped_op_cross_check"]

    jdiv4 = steps[8]["args"]["seq"][0]
    assert len(jdiv4) == 64, len(jdiv4)

    chain = {"name": "klein4_from_one", "variant": "rest",
             "steps": [None] * mi + [mstep]}
    ctx = {"row": None, "inputs": {},
           "pre": [None] * 7 + [gt["hexb"], jdiv4]}
    assert len(ctx["pre"]) == mi, len(ctx["pre"])

    chain_j = json.dumps(chain, sort_keys=True, separators=(",", ":"))
    ctx_j = json.dumps(ctx, sort_keys=True, separators=(",", ":"))
    crumbs = gt["crumbs"]
    assert len(crumbs) == 64, len(crumbs)

    lines = [
        "/* _1653_proto_map_data.h — GENERATED, do not hand-edit.",
        " *",
        " * Produced by docs/srmech/notes/_1653_map_emit_data_rc444.py from:",
        f" *   {TOML.relative_to(HERE.parents[2])}",
        f" *   sha256 {hashlib.sha256(raw).hexdigest()}",
        f" *   ground truth: {GT.name} (srmech {gt['srmech_version']},",
        " *   shipped-op cross-check True)",
        " *",
        " * PM_K4_CHAIN carries klein4_from_one's variant-\"rest\" map step"
        " VERBATIM",
        f" * (step index {mi}; {len(mstep['body'])} body steps,"
        f" {len(mstep.get('bind', {}))} binds), preceded by",
        " * nine JSON nulls standing for steps 0..8 — the render / sha256 /"
        " concat",
        " * stages this map arm does not claim. PM_K4_CTX pre-seeds those"
        " steps'",
        " * MEASURED outputs (step[7] = the block-0 digest as ASCII bytes,",
        " * step[8] = the 64-entry j-div-4 table) so the root frame RESUMES"
        " the",
        " * shipped chain at its map step.",
        " */",
        "",
        "static const char PM_K4_CHAIN[] =",
    ]
    for c in c_chunks(chain_j):
        lines.append(f'    "{c}"')
    lines.append("    ;")
    lines.append("")
    lines.append("static const char PM_K4_CTX[] =")
    for c in c_chunks(ctx_j):
        lines.append(f'    "{c}"')
    lines.append("    ;")
    lines.append("")
    lines.append("/* The value the SHIPPED Python projection returns for"
                 f" inputs {json.dumps(gt['inputs'], sort_keys=True)}. */")
    lines.append("static const int64_t PM_K4_EXPECT[64] = {")
    for r in range(0, 64, 16):
        lines.append("    " + ", ".join(str(v) for v in crumbs[r:r + 16])
                     + ("," if r + 16 < 64 else ""))
    lines.append("};")
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")

    print(f"map step: index {mi}, body {len(mstep['body'])} steps, "
          f"binds {len(mstep.get('bind', {}))}")
    print(f"chain JSON {len(chain_j)} bytes, ctx JSON {len(ctx_j)} bytes")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
