#!/usr/bin/env python3
"""ADVERSARIAL hunt for the issue's carried "11 of 18 chains rejected".

The census tested SEVEN candidate definitions and found 11 only as the C PARSE
ACCEPT count — polarity inverted.  If a definition exists under which 11 is a
genuine REJECT count, the census's provenance hypothesis is weaker than stated.
So: 20+ definitions, evaluated on TWO surfaces —

  * rc444  — the 18 executable chains as measured.
  * rc435* — the SAME data minus ``klein4_from_one``, which ``git log
             --diff-filter=A`` shows was ADDED at rc438 (commit aaa348f65,
             2026-08-16).  Before that the catalog was 20 descriptors = 17
             executable + 3 leaf, exactly what describe() reported at rc420.
             This reconstructs the surface the carried figure was measured on.

Read-only.  No numpy / RNG / abs() / fractions.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

NDJSON = os.path.join(HERE, "_1653_chain_census_rc444.ndjson")
ADDED_AT_RC438 = "klein4_from_one"


def build(recs, drop=()):
    env = [r for r in recs if r["record"] == "environment"][0]
    summary = [r for r in recs if r["record"] == "summary"][0]
    chains = [r for r in recs if r["record"] == "chain"
              and r["chain"] not in drop]
    return env, summary, chains


def defs(env, summary, chains):
    ros = summary["rosetta"]["per_op"]
    c_table = set(env["c_run_op_table"])
    c_ns = set(env["c_ref_namespaces"])
    vs = [v for c in chains for v in c["variants"]]

    def ops_of(c):
        o = set()
        for v in c["variants"]:
            o.update(v["profile"]["ops"])
        return o

    def bucket_of(op):
        return ros.get(op, {}).get("bucket")

    out = {}
    n = len(chains)
    out["[denominator] executable chains"] = n
    out["[denominator] chain-variants"] = len(vs)

    # ── REJECT-shaped definitions ────────────────────────────────────────
    out["REJ chains srmech_chain_run rejects"] = sum(
        1 for c in chains if not c["c_run_accepted"])
    out["REJ variants srmech_chain_run rejects"] = sum(
        1 for v in vs
        if v["c_chain_run_structure_probe"]["rc"] != 0
        or any(p["rc"] != 0 for p in v["c_chain_run_per_case"]))
    out["REJ chains srmech_chain_spec_parse rejects"] = sum(
        1 for c in chains if not c["c_parse_accepted"])
    out["REJ variants srmech_chain_spec_parse rejects"] = sum(
        1 for v in vs if v["c_spec_parse"]["rc"] != 0)
    out["REJ chains with a map or fold step"] = sum(
        1 for c in chains
        if any(v["profile"]["step_forms"]["map"]
               or v["profile"]["step_forms"]["fold"] for v in c["variants"]))
    out["REJ chains using a C-unknown ref namespace"] = sum(
        1 for c in chains
        if any(set(v["profile"]["ref_namespaces"]) - c_ns
               for v in c["variants"]))
    out["REJ chains whose TOML front end rejects"] = sum(
        1 for c in chains if c["c_toml_front_end"].get("rc") != 0)
    out["REJ chains with >1 step (top level)"] = sum(
        1 for c in chains
        if any(v["profile"]["n_steps_top"] > 1 for v in c["variants"]))
    out["REJ chains with >=2 total steps"] = sum(
        1 for c in chains
        if any(v["profile"]["n_steps_total"] > 1 for v in c["variants"]))
    out["REJ chains with a DOTTED op name"] = sum(
        1 for c in chains if any("." in o for o in ops_of(c)))
    out["REJ chains with ONLY bare op names"] = sum(
        1 for c in chains if ops_of(c) and all("." not in o
                                               for o in ops_of(c)))
    out["REJ chains with >=1 composition_of_c op"] = sum(
        1 for c in chains
        if any(bucket_of(o) == "composition_of_c" for o in ops_of(c)))
    out["REJ chains with NO c_dispatched op at all"] = sum(
        1 for c in chains
        if not any(bucket_of(o) == "c_dispatched" for o in ops_of(c)))
    out["REJ chains with >=1 c_dispatched op"] = sum(
        1 for c in chains
        if any(bucket_of(o) == "c_dispatched" for o in ops_of(c)))
    out["REJ chains whose every op is composition_of_c"] = sum(
        1 for c in chains
        if ops_of(c) and all(bucket_of(o) == "composition_of_c"
                             for o in ops_of(c)))
    out["REJ chains with >=2 distinct out-of-table ops"] = sum(
        1 for c in chains
        if len([o for o in ops_of(c) if o not in c_table]) >= 2)
    out["REJ chains with >=3 distinct out-of-table ops"] = sum(
        1 for c in chains
        if len([o for o in ops_of(c) if o not in c_table]) >= 3)
    out["REJ chains with a non-N declared class"] = sum(
        1 for c in chains
        if any(cl not in (None, "N")
               for cl in (c.get("class_composition") or []))
        or (isinstance(c.get("class_composition"), str)
            and c["class_composition"] not in ("N",)))
    out["REJ chains python-FAILS on descriptor-only inputs"] = sum(
        1 for c in chains if not c["python_ok"])
    out["REJ chains whose struct-probe rc == 2 (BAD_INPUT)"] = sum(
        1 for c in chains
        if any(v["c_chain_run_structure_probe"]["rc"] == 2
               for v in c["variants"]))
    out["REJ chains whose struct-probe rc == 5 (NOT_IMPL)"] = sum(
        1 for c in chains
        if all(v["c_chain_run_structure_probe"]["rc"] == 5
               for v in c["variants"]))
    out["REJ chains with a non-i64 literal"] = sum(
        1 for c in chains
        if any(v["profile"]["has_non_i64_literal"] for v in c["variants"]))

    # ── ACCEPT-shaped definitions (polarity check) ───────────────────────
    out["ACC chains srmech_chain_spec_parse accepts"] = sum(
        1 for c in chains if c["c_parse_accepted"])
    out["ACC variants srmech_chain_spec_parse accepts"] = sum(
        1 for v in vs if v["c_spec_parse"]["rc"] == 0)
    out["ACC chains whose every step is plain"] = sum(
        1 for c in chains
        if all(v["profile"]["step_forms"]["map"] == 0
               and v["profile"]["step_forms"]["fold"] == 0
               for v in c["variants"]))
    out["ACC chains whose TOML front end accepts"] = sum(
        1 for c in chains if c["c_toml_front_end"].get("rc") == 0)
    out["ACC chains with exactly 1 top-level step"] = sum(
        1 for c in chains
        if all(v["profile"]["n_steps_top"] == 1 for v in c["variants"]))
    return out


def main():
    recs = [json.loads(ln) for ln in open(NDJSON, encoding="utf-8")]
    surfaces = (("rc444 (18 executable, as measured)", ()),
                ("rc435* (17 executable, minus klein4_from_one)",
                 (ADDED_AT_RC438,)))
    hits = []
    for label, drop in surfaces:
        env, summary, chains = build(recs, drop)
        d = defs(env, summary, chains)
        print("=" * 78)
        print(label)
        print("=" * 78)
        for k in sorted(d):
            flag = ""
            if d[k] == 11:
                flag = "   <== ELEVEN"
                hits.append((label, k, d[k]))
            print("  %-56s %3d%s" % (k, d[k], flag))
        print()
    print("=" * 78)
    print("DEFINITIONS YIELDING 11 (%d total)" % len(hits))
    for label, k, _v in hits:
        kind = "REJECT-shaped" if k.startswith("REJ") else (
            "ACCEPT-shaped" if k.startswith("ACC") else "denominator")
        print("  [%s] %-13s %s  |  %s" % (label.split()[0], kind, k, ""))
    rej = [h for h in hits if h[1].startswith("REJ")]
    print()
    print("VERDICT: %d REJECT-shaped definition(s) yield 11."
          % len(rej))
    if not rej:
        print("  => The census's claim stands: on this data 11 is reachable "
              "ONLY as an ACCEPT count, never as a reject count, across "
              "%d definitions x 2 surfaces." % (len(defs(*build(recs))) ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
