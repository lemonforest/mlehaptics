#!/usr/bin/env python3
"""gh #1653 — the per-chain GATE MATRIX, measured at rc445.

Round 2 left two figures in conflict: its prose said "only 6 of 11 are
op-table-ONLY" while its own machine line printed ``op_table_ONLY=9``. Neither
is inherited here. This re-derives the matrix from the descriptors and the C
sources directly, so the build knows what it actually has to fix.

THE FOUR MEASURED C-SIDE GATES (gh #1653, source lines re-read at rc445):
  op_table          srmech_compose_run.c cr_dispatch -> SRMECH_ERR_NOT_IMPL
  carrier_width     srmech_compose_run.c cr_value_t has no double / bytes /
                    dense-matrix kind
  ref_grammar       srmech_compose_run.c only a BARE ``.output`` ref is parsed
  real_literal_arg  srmech_compose_run.c cr_json_scalar returns NULL for a
                    JSON double

Discipline: no ALU-magnitude idiom, no numpy, no RNG, no stdlib fractions.
Read-only: edits nothing, writes one NDJSON under notes/.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))

from srmech.dsl import _cascade_chain as _cc      # noqa: E402
from srmech.dsl import _catalog as _cat           # noqa: E402

C_SRC = os.path.join(HERE, "..", "c", "src", "srmech_compose_run.c")
OUT = os.path.join(HERE, "_1653_gate_matrix_rc445.ndjson")


def c_table_ops():
    """The ops the C dispatch actually handles — read from the C source, not a
    list, so this cannot drift from what is compiled.

    Spans cr_dispatch AND cr_dispatch_real: rc447 split the real-sequence arms
    into the second function purely to keep the first under JPL Rule 4, and a
    scanner anchored to one of them would silently under-report the table. It
    also matches the SUFFIX form ``memcmp(op + (opl - N), "name", N)`` used by
    ops whose descriptors write a dotted spelling — reading only the bare
    ``memcmp(op, ...)`` form would miss every one of those.
    """
    src = open(C_SRC, encoding="utf-8", errors="replace").read()
    start = src.index("static srmech_status_t cr_dispatch_real")
    body = src[start:]
    end = body.find("static srmech_status_t cr_run_steps")
    if end > 0:
        body = body[:end]
    ops = set(re.findall(r'memcmp\(op,\s*"([a-z0-9_]+)"', body))
    ops |= set(re.findall(r'memcmp\(op \+ \([^)]*\),\s*"([a-z0-9_]+)"', body))
    assert ops, "the C dispatch-table scan found NOTHING — the anchors have " \
                "drifted from the source and every gate below would be wrong"
    return sorted(ops)


def walk_steps(steps, depth=0):
    """Yield (step, depth) over a chain, descending into map/fold bodies."""
    for st in steps or []:
        if not isinstance(st, dict):
            continue
        yield st, depth
        for key in ("body", "sub_chain"):
            sub = st.get(key)
            if isinstance(sub, list):
                for pair in walk_steps(sub, depth + 1):
                    yield pair


def step_ops(st):
    out = []
    for k in ("op", "fold_op", "reduce_op", "parallel_body", "map_op"):
        v = st.get(k)
        if isinstance(v, str):
            out.append(v)
    return out


def has_real(node):
    """True if a real (non-integer) number appears anywhere in the args tree."""
    if isinstance(node, bool):
        return False
    if isinstance(node, float):
        return True
    if isinstance(node, dict):
        return any(has_real(v) for v in node.values())
    if isinstance(node, (list, tuple)):
        return any(has_real(v) for v in node)
    return False


INDEXED_REF = re.compile(r"@step\[\d+\]\.output\[")

#: Namespaces cr_resolve_ref does NOT know. @op is the sharpest: it names an OP
#: as a VALUE, which needs a callable registry in C, not a wider path walker.
UNKNOWN_NS = re.compile(r"@(op|bind|idx|catalog)[.\[]")


def has_indexed_ref(node):
    """Any reference form C cannot resolve — an INDEXED @step[N].output[K],
    or a namespace outside {row, input, step}.

    ⚠️ This checked ONLY the indexed form until rc447, which is why
    ``parallel_sector_dispatch`` scored as blocked by the op table ALONE and
    read as the cheapest remaining chain. It is not: it also passes
    ``@op.srmech.cascade.atoms.chiral_flip``, so it needs a namespace C has no
    resolver for at all. A predicate that under-reports gates makes the hardest
    chain look like the easiest.
    """
    if isinstance(node, str):
        # The INDEXED form @step[N].output[K] SHIPPED at rc447 (cr_index_value),
        # so it is no longer a gate. Only the unresolvable NAMESPACES remain.
        # INDEXED_REF is kept for the ndjson history and must score zero.
        return bool(UNKNOWN_NS.search(node))
    if isinstance(node, dict):
        return any(has_indexed_ref(v) for v in node.values())
    if isinstance(node, (list, tuple)):
        return any(has_indexed_ref(v) for v in node)
    return False


def main():
    table = c_table_ops()
    catalog = _cat.load_catalog()
    names = sorted(n for n, d in catalog.items()
                   if _cc.descriptor_status(d) == "executable")
    print("C cr_dispatch table: %d ops -> %s" % (len(table), table))
    print("executable descriptors: %d\n" % len(names))

    recs = []
    tally = {"op_table": 0, "carrier_width": 0, "ref_grammar": 0,
             "step_form": 0}
    only = {k: 0 for k in tally}
    hdr = "%-26s %-9s %-9s %-9s %-9s  %s"
    print(hdr % ("chain", "op_table", "carrier", "ref_gram", "stepform",
                 "n_gates"))
    print("-" * 92)
    for name in names:
        gates = set()
        ops_used = set()
        for entry in _cc._chain_entries(catalog[name]):
            for st, _d in walk_steps(entry.get("steps")):
                ops_used |= set(step_ops(st))
                if "map_over" in st or "body" in st:
                    gates.add("step_form")          # MAP: still unimplemented
                # FOLD executes since rc446 — but only for the ONE body op in
                # cr_fold_body. A fold over anything else is still a step_form
                # block, so the predicate tests the BODY OP, not the form.
                if "fold_op" in st or "fold_class" in st:
                    fop = str(st.get("fold_op") or "").rpartition(".")[2]
                    if fop != "orientation_compose":
                        gates.add("step_form")
                if has_indexed_ref(st.get("args")):
                    gates.add("ref_grammar")
                # real_literal_arg is GONE as of rc447 — CR_DBL ingests a JSON
                # double and marshals {"k":"f"} back, so a float in the args is
                # no longer a block. The predicate is deleted rather than left
                # scoring zero, so the column cannot quietly come back.
        outside = sorted(o for o in ops_used
                         if o.rpartition(".")[2] not in table and o not in table)
        if outside:
            gates.add("op_table")
        # carrier: does the Python projection return a non-int/str/rational?
        try:
            from srmech.dsl import run_cascade_chain
            e0 = _cc._chain_entries(catalog[name])[0]
            c0 = (e0.get("proof_cases") or [{}])[0]
            v = run_cascade_chain(name, **(c0.get("inputs") or {}))
            # CR_DBL + CR_LIST ship as of rc447, so a float / list-of-float
            # result is CARRIED now. Bytes and dense matrices are still
            # unrepresentable — those are the two carrier kinds left.
            # ⚠️ THIS PREDICATE HAS BEEN WRONG FOUR TIMES. It is the hardest
            # one to get right because it must enumerate what the WIRE can
            # express, and the wire's kind set is not written down in one place.
            # Missing entries found so far: dict (parallel_sector_dispatch),
            # tuple (best_rational_signed), nested list (o/qDFT).
            #
            # The chain-run value descriptor carries: n / i / q / s / f / l,
            # and its `l` is FLAT BY CONSTRUCTION (cr_desc_list calls
            # cr_desc_scalar, never itself — JPL Rule 1 bans the recursive
            # walk). So a list[list[...]] is NOT expressible even though `l` is.
            if isinstance(v, (bytes, bytearray, dict, tuple)) \
               or hasattr(v, "tolist"):
                gates.add("carrier_width")
            elif isinstance(v, list) and any(isinstance(e, (list, tuple, dict))
                                             for e in v):
                gates.add("carrier_width")     # nested — the wire's list is flat
        except Exception:
            pass
        for g in gates:
            tally[g] += 1
        if len(gates) == 1:
            only[next(iter(gates))] += 1
        print(hdr % (name,
                     "X" if "op_table" in gates else ".",
                     "X" if "carrier_width" in gates else ".",
                     "X" if "ref_grammar" in gates else ".",
                     "X" if "step_form" in gates else ".",
                     len(gates)))
        recs.append({"record": "chain", "chain": name, "gates": sorted(gates),
                     "n_gates": len(gates), "ops_outside_c_table": outside,
                     "n_ops_used": len(ops_used)})

    # ── CROSS-CHECK: the PREDICTION against what actually RUNS ──────────
    #
    # This whole table is a STATIC predictor, and a static predictor goes stale
    # the moment a gate is closed — measured: after rc447 shipped CR_DBL it
    # still scored `chiral_dual` as carrier+real_lit blocked while the chain
    # was executing fine. Silent staleness in a diagnostic is how a closed gap
    # keeps being reported as open, so the predictor now checks itself against
    # execution and FAILS on disagreement rather than printing a stale row.
    import ctypes as _ct, json as _json
    from srmech.cascade import compose as _cmp
    lib = _cmp._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    disagree = []
    if lib is not None:
        for r in recs:
            entry = _cc._chain_entries(catalog[r["chain"]])[0]
            case = (entry.get("proof_cases") or [{}])[0]
            # CHAIN-DEFINING KEYS ONLY. Sending proof_cases couples the probe to
            # test data: magnitude declares non-finite cases, json.dumps spells
            # them as bare NaN, and the strict parser then rejects the whole
            # DOCUMENT — so the probe reported a chain as not-running whose every
            # step ran. Both halves of this file were stale in the SAME
            # direction, which is exactly why the cross-check read 0
            # disagreements while disagreeing with the ratchet by one chain.
            chain_only = {k: v for k, v in entry.items()
                          if k in ("name", "steps", "on_error",
                                   "chain_schema_version")}
            cj = _json.dumps(chain_only).encode("utf-8")
            xj = _json.dumps({"inputs": case.get("inputs") or {}}).encode("utf-8")
            n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
            ws = (_ct.c_char * n)(); cap = max(n // 2, 65536)
            ob = (_ct.c_char * cap)(); ol = _ct.c_size_t()
            rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                          ob, cap, _ct.byref(ol)))
            runs = (rc == 0)
            r["c_runs"] = runs
            if runs != (r["n_gates"] == 0):
                disagree.append((r["chain"], r["gates"], rc))
        print("cross-check: %d chains RUN in C; prediction disagreements: %d"
              % (sum(1 for r in recs if r.get("c_runs")), len(disagree)))
        for name, gates, rc in disagree:
            print("   MISMATCH %-24s predicted gates=%s but C rc=%s"
                  % (name, gates or "[]", rc))
        # ⚠️ SELF-CONSISTENCY IS NOT ENOUGH, measured. Before this block existed
        # BOTH halves of this file were stale in the SAME direction (the
        # ref_grammar predicate still flagged an indexed ref that had shipped,
        # and the probe still sent proof_cases), so the internal cross-check
        # read 0 disagreements while the file disagreed with the RATCHET by one
        # whole chain. A diagnostic that only checks itself will agree with
        # itself. So tie it to the independent artifact:
        ratchet = os.path.join(HERE, "..", "python", "tests",
                               "test_c_cascade_parity_ratchet_rc446.py")
        if os.path.exists(ratchet):
            txt = open(ratchet, encoding="utf-8").read()
            m = re.search(r"CEIL_C_REJECTED_CHAINS\s*=\s*(\d+)", txt)
            if m:
                ceil = int(m.group(1))
                runs = sum(1 for r in recs if r.get("c_runs"))
                print("ratchet tie-in: %d executable - %d running = %d rejected; "
                      "ratchet ceiling %d" % (len(recs), runs, len(recs) - runs, ceil))
                assert len(recs) - runs == ceil, (
                    "this file measures %d rejected chains but the ratchet pins "
                    "%d. The two harnesses have drifted apart — they duplicate "
                    "the run setup, which is how they drift."
                    % (len(recs) - runs, ceil))
        assert not disagree, (
            "the gate predicates disagree with actual execution on %d chain(s) "
            "— a gate was closed (or opened) without updating this file, and "
            "every row above is therefore suspect" % len(disagree))

    print()
    print("chains blocked BY GATE      :", json.dumps(tally, sort_keys=True))
    print("chains blocked by that gate ALONE:", json.dumps(only, sort_keys=True))
    print("chains with NO gate (should run in C already):",
          sum(1 for r in recs if r["n_gates"] == 0))
    recs.append({"record": "summary", "c_table": table, "tally": tally,
                 "only": only, "n_chains": len(names)})
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
