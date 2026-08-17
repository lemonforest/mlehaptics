#!/usr/bin/env python3
"""ROUND-2 WEDGE JOIN (gh #1653) — the C<->Python comparison that was MISSING.

WHY THIS EXISTS. Round 2 shipped two halves that never met:
  * _1653_wedge_optable_rc444.c   -- the bare-C harness. It RUNS and prints `C_VALUE <json>`.
  * _1653_wedge_pycheck_rc444.py  -- the Python side. It writes the inputs and the ndjson.
The ndjson's C-side fields are ALL NULL (`byte_identical: null`, `c_value_spelling: null`) and
the python half reports `c_ran=0 byte_identical=0` on a fresh run, because NOTHING EVER
INGESTED THE C HARNESS'S STDOUT. So round 2's headline -- "48 of 52 byte-identical" -- was not
reproducible from its own committed artifacts. This file is that join, so the number is
measured rather than asserted.

RUN ORDER (undocumented in round 2, and it matters):
  1. python3 notes/_1653_wedge_pycheck_rc444.py      # writes notes/_1653_wedge_barec/*.json
  2. cc ... notes/_1653_wedge_optable_rc444.c c/build/libsrmech.a -o /tmp/wedge
  3. python3 notes/_1653_wedge_join_rc444.py         # this file: runs 2, joins against Python

Discipline: no ALU-magnitude idiom, no numpy, no RNG, no stdlib fractions. Read-only w.r.t.
shipped source; writes only under docs/srmech/notes/.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PYROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
SRMECH_ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, PYROOT)

NDJSON = os.path.join(HERE, "_1653_wedge_optable_rc444.ndjson")
BAREC = os.path.join(HERE, "_1653_wedge_barec")
OUT = os.path.join(HERE, "_1653_wedge_join_rc444.ndjson")
CSRC = os.path.join(HERE, "_1653_wedge_optable_rc444.c")
LIBA = os.path.join(SRMECH_ROOT, "c", "build", "libsrmech.a")
BIN = "/tmp/_1653_wedge_join_bin"

CASE_RE = re.compile(r"^\s*case(\d+)\s+(\S+)(?:\s+(.*))?$")
CHAIN_RE = re.compile(r"^\s*==\s+(\S+)\s+\((\d+) cases\)")


def build():
    cmd = ["cc", "-std=c99", "-Wall", "-Wextra", "-O2",
           "-I" + os.path.join(SRMECH_ROOT, "c", "include"),
           CSRC, LIBA, "-o", BIN]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stderr or "").strip()


def run_c():
    p = subprocess.run([BIN, BAREC], capture_output=True, text=True, cwd=HERE)
    out = {}
    chain = None
    for line in (p.stdout or "").splitlines():
        m = CHAIN_RE.match(line)
        if m:
            chain = m.group(1)
            out[chain] = {}
            continue
        m = CASE_RE.match(line)
        if m and chain:
            out[chain][int(m.group(1))] = (m.group(2), (m.group(3) or "").strip())
    return out


def norm(v):
    """Canonical JSON so a tuple/list or int/float spelling difference is not a false diff."""
    def _c(x):
        if isinstance(x, tuple):
            return [_c(i) for i in x]
        if isinstance(x, list):
            return [_c(i) for i in x]
        if isinstance(x, dict):
            return {k: _c(x[k]) for k in sorted(x)}
        if isinstance(x, (bytes, bytearray)):
            # match the C harness's spelling: it prints bytes as lowercase hex, so compare
            # hex-to-hex. A list-of-ints normalisation reports a false DIVERGENT (measured).
            return x.hex()
        if hasattr(x, "tolist"):
            try:
                return _c(x.tolist())           # Mat / Vec -> nested lists
            except Exception:
                pass
        if isinstance(x, float) and x == int(x) and abs(x) < 2**53:
            return int(x)
        return x
    return json.dumps(_c(v), sort_keys=True, separators=(",", ":"))


def main():
    rc, err = build()
    print("build rc=%d %s" % (rc, err[:200]))
    if rc != 0:
        return 1
    cvals = run_c()
    print("C harness reported %d chains" % len(cvals))

    from srmech.dsl import run_cascade_chain
    import srmech
    print("srmech %s native=%s" % (srmech.__version__, srmech.native_status()["dispatching"]))

    recs = []
    tot = ran = ident = diverge = pyfail = ingest_rej = 0
    per_chain = {}
    for line in open(NDJSON, encoding="utf-8"):
        d = json.loads(line)
        cases = d.get("cases")
        if not cases:
            continue
        key = d.get("chain") or d.get("name") or d.get("chain_key")
        if key is None:
            for k in cvals:
                if any(c.get("ctx_path", "").startswith(k.split("__")[0]) for c in cases):
                    key = k
                    break
        if key is None:
            continue
        desc = key.split("__")[0]
        per_chain.setdefault(key, {"ran": 0, "ident": 0, "div": 0, "n": 0})
        for c in cases:
            idx = c["case"]
            tot += 1
            per_chain[key]["n"] += 1
            cmap = cvals.get(key)
            if cmap is None:
                for suff in ("__0", "__default", "__1"):
                    if key + suff in cvals:
                        cmap = cvals[key + suff]
                        break
            if cmap is None:
                for ck in cvals:
                    if ck.split("__")[0] == desc:
                        cmap = cvals[ck]
                        break
            cv = (cmap or {}).get(idx)
            if cv is None:
                recs.append({"chain": key, "case": idx, "verdict": "NO_C_LINE"})
                continue
            kind, payload = cv
            if kind != "C_VALUE":
                ingest_rej += 1
                recs.append({"chain": key, "case": idx, "verdict": "C_" + kind,
                             "detail": payload})
                continue
            ran += 1
            per_chain[key]["ran"] += 1
            try:
                pv = run_cascade_chain(desc, **c.get("inputs", {}))
                pys = norm(pv)
            except Exception as e:
                pyfail += 1
                recs.append({"chain": key, "case": idx, "verdict": "PYTHON_RAISED",
                             "error": "%s: %s" % (type(e).__name__, str(e)[:120])})
                continue
            try:
                cs = norm(json.loads(payload))
            except Exception:
                cs = payload          # raw hex is not valid JSON on its own
            # The C harness prints a bare token; norm() JSON-quotes a python str. Compare
            # unquoted too, else a pure QUOTING difference reports a false DIVERGENT (measured
            # on all 4 encode_loe_content cases: identical 2048-char hex, quotes only).
            same = (cs == pys) or (cs.strip('"') == pys.strip('"'))
            if same:
                ident += 1
                per_chain[key]["ident"] += 1
            else:
                diverge += 1
                per_chain[key]["div"] += 1
            recs.append({"chain": key, "case": idx,
                         "verdict": "BYTE_IDENTICAL" if same else "DIVERGENT",
                         "c_value": payload, "python_value": pys})

    print()
    print("%-28s %5s %5s %5s %5s" % ("chain", "cases", "c_ran", "ident", "diverg"))
    print("-" * 56)
    for k in sorted(per_chain):
        v = per_chain[k]
        print("%-28s %5d %5d %5d %5d" % (k, v["n"], v["ran"], v["ident"], v["div"]))
    print()
    print("TOTALS  cases=%d  c_ran=%d  BYTE_IDENTICAL=%d  DIVERGENT=%d  ingest_rejected=%d  python_raised=%d"
          % (tot, ran, ident, diverge, ingest_rej, pyfail))
    chains_all = sum(1 for v in per_chain.values() if v["ran"] == v["n"] and v["n"])
    chains_any = sum(1 for v in per_chain.values() if v["ran"])
    print("chains: total=%d  every_case_ran=%d  any_case_ran=%d" % (len(per_chain), chains_all, chains_any))
    recs.append({"record": "summary", "cases": tot, "c_ran": ran,
                 "byte_identical": ident, "divergent": diverge,
                 "ingest_rejected": ingest_rej, "python_raised": pyfail,
                 "chains_total": len(per_chain), "chains_every_case": chains_all,
                 "chains_any_case": chains_any, "srmech": srmech.__version__})
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote %s (%d records)" % (OUT, len(recs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
