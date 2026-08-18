#!/usr/bin/env python3
"""gh #1653 round-2 measurement 1 of 3 — the MAP-arm FRAME BUDGET, harvested
from the 21 shipped cascade descriptors.

WHY. Report section 6.2 sub-problem 1 states "max nesting depth 1 (two
levels), max body length 19, max binds 9 — a frame cap of 8 gives 4x
headroom". Those three numbers were carried in from the design session. This
script re-derives them from the descriptor TOML itself so the frame cap the
rcN picks is a MEASURED bound, and so the per-body op inventory that the
C body table must cover is enumerated rather than estimated.

WHAT IT MEASURES, per map step at every nesting depth:
  depth          0 = a top-level map step, 1 = a map inside a map body, ...
  body_len       number of steps in that map's body step list
  n_binds        size of the map's `bind` table
  index          the @idx name the body sees ("k" is compose.py's default)
  map_over_ns    the reference namespace of map_over (row/input/step/bind/idx)
  body_ops       every op named by the body's PLAIN steps
  body_forms     the step-form of each body step (plain / map / fold)
  carrier        the value kinds the body must carry, as the descriptor
                 declares them (int / float / list / str / bytes / unknown)

FRAME-STACK BOUND. A C map arm with an explicit frame stack needs
  1 (root step list) + max_depth + 1
frames live at once. Reported as `frames_needed`.

Writes docs/srmech/notes/_1653_map_frames_rc444.ndjson and exits 0.
No numpy, no RNG, no floats in any computation (counts are integers).
"""

import json
import pathlib
import sys
import tomllib

WT = pathlib.Path(__file__).resolve().parents[1]
CAT = WT / "python" / "srmech" / "cascade" / "catalogs" / "cascade_catalog"
OUT = pathlib.Path(__file__).resolve().parent / "_1653_map_frames_rc444.ndjson"

MAP_KEYS = ("map_over", "index", "bind", "body")
FOLD_KEYS = ("fold_class", "fold_op", "fold_init", "over", "fold_args")
PLAIN_KEYS = ("class", "op", "args")


def step_form(st):
    m = any(k in st for k in MAP_KEYS)
    f = any(k in st for k in FOLD_KEYS)
    p = any(k in st for k in PLAIN_KEYS)
    if (int(m) + int(f) + int(p)) > 1:
        return "MIXED"
    if m:
        return "map"
    if f:
        return "fold"
    if p:
        return "plain"
    return "NONE"


def ref_ns(v):
    if not isinstance(v, str) or not v.startswith("@"):
        return "literal"
    tail = v[1:]
    for ns in ("row", "input", "step", "catalog", "idx", "bind", "op"):
        if tail.startswith(ns + ".") or tail.startswith(ns + "["):
            return ns
    return "UNKNOWN"


def literal_kinds(obj, acc):
    """Value kinds the descriptor's own literals declare."""
    if isinstance(obj, bool):
        acc.add("bool")
    elif isinstance(obj, int):
        acc.add("int")
    elif isinstance(obj, float):
        acc.add("float")
    elif isinstance(obj, str):
        acc.add("ref" if obj.startswith("@") else "str")
    elif isinstance(obj, list):
        acc.add("list")
        for v in obj:
            literal_kinds(v, acc)
    elif isinstance(obj, dict):
        for v in obj.values():
            literal_kinds(v, acc)
    return acc


def walk(steps, depth, name, variant, rows, seen_ops, max_depth):
    """Iterative (NOT recursive at the C level either) map-step walk.

    Kept iterative on purpose: this script measures a design whose whole
    point is that the C side must not recurse, and a recursive harvester
    would hide how deep the work stack actually goes.
    """
    work = [(steps, depth)]
    guard = 0
    while work:
        guard += 1
        assert guard < 10000, "walk guard"
        cur, d = work.pop()
        for i, st in enumerate(cur):
            form = step_form(st)
            if form == "plain":
                op = st.get("op")
                if isinstance(op, str):
                    seen_ops.setdefault(d, set()).add(op)
                continue
            if form != "map":
                continue
            body = st.get("body") or []
            binds = st.get("bind") or {}
            kinds = set()
            for b in binds.values():
                literal_kinds(b, kinds)
            body_ops = [s.get("op") for s in body if step_form(s) == "plain"]
            body_forms = [step_form(s) for s in body]
            arg_kinds = set()
            for s in body:
                literal_kinds(s.get("args", {}), arg_kinds)
            rows.append({
                "record": "map_step",
                "descriptor": name,
                "variant": variant,
                "depth": d,
                "step_index": i,
                "body_len": len(body),
                "n_binds": len(binds),
                "index": st.get("index", "k (default)"),
                "map_over": st.get("map_over"),
                "map_over_ns": ref_ns(st.get("map_over")),
                "bind_names": sorted(binds),
                "bind_literal_kinds": sorted(kinds),
                "body_arg_kinds": sorted(arg_kinds),
                "body_forms": body_forms,
                "body_ops": [o for o in body_ops if o],
                "nested_maps_in_body": body_forms.count("map"),
                "folds_in_body": body_forms.count("fold"),
            })
            max_depth[0] = max(max_depth[0], d)
            work.append((body, d + 1))


def main():
    rows = []
    seen_ops = {}
    max_depth = [-1]
    tomls = sorted(CAT.glob("*.toml"))
    n_chains = 0
    n_map_desc = 0
    for p in tomls:
        with p.open("rb") as fh:
            doc = tomllib.load(fh)
        casc = doc.get("cascade", {})
        chains = casc.get("chain") or []
        if isinstance(chains, dict):
            chains = [chains]
        before = len(rows)
        for ch in chains:
            n_chains += 1
            walk(ch.get("steps") or [], 0, p.stem,
                 ch.get("variant", "(single)"), rows, seen_ops, max_depth)
        if len(rows) > before:
            n_map_desc += 1

    # The FLOAT question is a DATA question, not a literal one: every map's
    # own bind/args literals are int/list/ref, so the carrier's missing FLOAT
    # kind bites through the chain's declared proof-case INPUTS. Measure that
    # separately rather than conflating the two.
    float_input_desc = set()
    for p in tomls:
        with p.open("rb") as fh:
            doc = tomllib.load(fh)
        for ch in (doc.get("cascade", {}).get("chain") or []):
            for pc in (ch.get("proof_cases") or []):
                if "float" in literal_kinds(pc.get("inputs", {}), set()):
                    float_input_desc.add(p.stem)
    map_desc = {r["descriptor"] for r in rows}

    body_ops_all = set()
    for r in rows:
        body_ops_all.update(r["body_ops"])
    summary = {
        "record": "summary",
        "srmech_worktree": str(WT),
        "descriptors_total": len(tomls),
        "chains_total": n_chains,
        "descriptors_with_a_map_step": n_map_desc,
        "map_steps_total": len(rows),
        "max_map_nesting_depth": max_depth[0],
        "frames_needed": (max_depth[0] + 2) if rows else 1,
        "max_body_len": max((r["body_len"] for r in rows), default=0),
        "max_n_binds": max((r["n_binds"] for r in rows), default=0),
        "index_names": sorted({r["index"] for r in rows}),
        "map_over_namespaces": sorted({r["map_over_ns"] for r in rows}),
        "distinct_body_ops": sorted(body_ops_all),
        "n_distinct_body_ops": len(body_ops_all),
        "maps_with_float_literals": sum(
            1 for r in rows
            if "float" in r["bind_literal_kinds"]
            or "float" in r["body_arg_kinds"]),
        "maps_int_or_list_only": sum(
            1 for r in rows
            if not ({"float"} & set(r["bind_literal_kinds"]))
            and not ({"float"} & set(r["body_arg_kinds"]))),
        "map_descriptors_with_float_proof_inputs":
            sorted(map_desc & float_input_desc),
        "map_descriptors_with_int_only_proof_inputs":
            sorted(map_desc - float_input_desc),
        "map_steps_in_float_input_descriptors": sum(
            1 for r in rows if r["descriptor"] in float_input_desc),
        "map_steps_in_int_only_descriptors": sum(
            1 for r in rows if r["descriptor"] not in float_input_desc),
    }
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
        fh.write(json.dumps(summary, sort_keys=True) + "\n")

    print("=== #1653 round-2: MAP frame budget, measured from the catalog ===")
    for k, v in summary.items():
        if k == "record":
            continue
        print(f"  {k:34s} {v}")
    print("\n--- per map step ---")
    for r in rows:
        print(f"  {r['descriptor']:22s} variant={r['variant']:9s} "
              f"depth={r['depth']} step={r['step_index']:2d} "
              f"body_len={r['body_len']:2d} binds={r['n_binds']} "
              f"idx=@idx.{r['index']:14s} over={r['map_over_ns']:6s} "
              f"nested_maps={r['nested_maps_in_body']} "
              f"folds={r['folds_in_body']}")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
