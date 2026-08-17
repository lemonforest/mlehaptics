"""#1653 — SURFACE-A (``[[cascade.chain]]``) step-grammar IMPLEMENTATION-PATH
measurement, rc444.

Sibling to _1653_step_forms_rc444.py / _1653_chain_census_rc444.py (which
census WHAT is missing). This one measures the facts an rcN needs to BUILD
the missing forms in C:

  P0  positive controls — the harness itself parses + runs a plain chain in C
      (so every rejection below is the C grammar, never my marshalling).
  P1  the fold / map step form gates, with the C status + source line.
  P2  the CARRIER gate: surface A's cr_value_t has no FLOAT kind. Measured,
      not read — a float literal in a plain in-table step's args, vs the same
      chain with an int.
  P3  the VALUE-DESCRIPTOR vocabulary Python can already reconstruct
      (compose._reconstruct_value) vs what C's cr_desc emits. This decides
      whether a LIST-returning form needs a Python-side change.
  P4  the shapes the shipped descriptors actually need (nesting depth, bind
      arity, body length, fold seed kinds, body op names) — the work sizing.
  P5  the C-symbol availability of every fold/map body op the descriptors
      name (does a kernel exist to dispatch to, or is new math required?).

Run:  cd docs/srmech/python && python3 ../notes/_1653_path_measure_rc444.py

Writes _1653_path_measure_rc444.ndjson next to this file. Exit 0 iff every
positive control passed; nothing is attributed if a control fails.

No abs(), no numpy, no RNG, no fractions. Reads only; edits nothing.
"""
from __future__ import annotations

import ctypes
import glob
import json
import os
import sys
import tomllib

sys.path.insert(0, ".")

import srmech  # noqa: E402
from srmech import _native  # noqa: E402
from srmech.cascade import compose  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_1653_path_measure_rc444.ndjson")
CAT = "srmech/cascade/catalogs/cascade_catalog"

RECS = []
FAILED_CONTROLS = []


def rec(**kw):
    RECS.append(kw)
    return kw


# ── the C driver (lifted verbatim from compose.py's own native callers) ──

LIB = _native.LIB
assert LIB is not None, "no native lib — this script measures the C peer"


def c_spec_parse(chain_dict):
    """srmech_chain_spec_parse(chain_json) -> (rc, text|None).

    Arena + out_cap exactly as compose._call_compose_native does it.
    """
    payload = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(LIB.srmech_chain_spec_parse_arena_bytes(len(payload)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = 2 * len(payload) + 8192
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = LIB.srmech_chain_spec_parse(
        payload, len(payload), ws, ws_bytes, out, out_cap,
        ctypes.byref(out_len))
    if rc != 0:
        return int(rc), None
    return 0, out.raw[:out_len.value].decode("utf-8")


def c_chain_run(chain_dict, ctx):
    """srmech_chain_run(chain_json, ctx_json) -> (rc, descriptor|None).

    Arena + out_cap exactly as compose._run_chain_native does it.
    """
    chain_json = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    ctx_json = json.dumps(ctx, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(LIB.srmech_chain_run_arena_bytes(
        len(chain_json), len(ctx_json)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = LIB.srmech_chain_run(
        chain_json, len(chain_json), ctx_json, len(ctx_json),
        ws, ws_bytes, out, out_cap, ctypes.byref(out_len))
    if rc != 0:
        return int(rc), None
    return 0, out.raw[:out_len.value].decode("utf-8")


def plain_chain(steps, name="probe"):
    return {"name": name, "summary": "s", "returns": "r",
            "on_error": "raise", "steps": steps}


# In-table Class-N step: the ONLY op family surface A's C run loop dispatches.
def rational_add_step(a=(1, 2), b=(1, 3)):
    return {"class": "N", "op": "rational_add",
            "args": {"a": list(a), "b": list(b)}}


# ─────────────────────────── P0 positive controls ───────────────────────

def p0_controls():
    ok_all = True

    # C0a: a one-step in-table chain, literal args -> parse OK + run OK.
    ch = plain_chain([rational_add_step()])
    prc, ptext = c_spec_parse(ch)
    rrc, rdesc = c_chain_run(ch, {"row": None, "inputs": {}})
    pure = srmech.math.rational.rational_add((1, 2), (1, 3))
    got = compose._reconstruct_value(json.loads(rdesc)) if rdesc else None
    ok = (prc == 0 and rrc == 0 and got == pure)
    ok_all &= ok
    rec(kind="control", id="C0a", what="plain in-table step, literal args",
        parse_rc=prc, run_rc=rrc, c_value=got, pure_value=list(pure),
        byte_identical=(got == pure), passed=ok)

    # C0b: the same via @input refs -> the ctx marshalling works.
    ch = plain_chain([{"class": "N", "op": "rational_add",
                       "args": {"a": "@input.a", "b": "@input.b"}}])
    prc, _ = c_spec_parse(ch)
    rrc, rdesc = c_chain_run(
        ch, {"row": None, "inputs": {"a": [1, 2], "b": [1, 3]}})
    got = compose._reconstruct_value(json.loads(rdesc)) if rdesc else None
    ok = (prc == 0 and rrc == 0 and got == pure)
    ok_all &= ok
    rec(kind="control", id="C0b", what="plain in-table step, @input refs",
        parse_rc=prc, run_rc=rrc, c_value=got, byte_identical=(got == pure),
        passed=ok)

    # C0c: a two-step chain threading @step[0].output -> step outputs persist.
    ch = plain_chain([
        rational_add_step(),
        {"class": "N", "op": "rational_mul",
         "args": {"a": "@step[0].output", "b": [2, 1]}},
    ])
    prc, _ = c_spec_parse(ch)
    rrc, rdesc = c_chain_run(ch, {"row": None, "inputs": {}})
    exp = srmech.math.rational.rational_mul(pure, (2, 1))
    got = compose._reconstruct_value(json.loads(rdesc)) if rdesc else None
    ok = (prc == 0 and rrc == 0 and got == exp)
    ok_all &= ok
    rec(kind="control", id="C0c", what="two steps, @step[0].output thread",
        parse_rc=prc, run_rc=rrc, c_value=got, byte_identical=(got == exp),
        passed=ok)

    if not ok_all:
        FAILED_CONTROLS.append("P0")
    return ok_all


# ─────────────────────── P1 the missing step forms ──────────────────────

def p1_forms():
    """The fold + map gates, each attributed to a C source line."""
    # FOLD, exactly net_chirality's shape but with an in-table body so the
    # ONLY thing under test is the step FORM, not the op table.
    fold_step = {"fold_class": "N", "fold_op": "rational_add",
                 "fold_init": 1, "over": "@input.xs"}
    ch = plain_chain([fold_step])
    prc, _ = c_spec_parse(ch)
    rrc, _ = c_chain_run(ch, {"row": None, "inputs": {"xs": [1, 2, 3]}})
    rec(kind="form", surface="A", form="fold", parse_rc=prc, run_rc=rrc,
        parse_attrib="srmech_compose.c:299-303 co_build_step requires "
                     "class+op+args (a fold step has none)",
        run_attrib="srmech_compose_run.c:722-724 cr_run_steps requires a "
                   "STRING \"op\"",
        verdict="unrecognised" if (prc == 2 and rrc == 2) else "CHECK")

    # MAP, autocorrelation's shape reduced to one in-table body step.
    map_step = {"map_over": "@input.xs", "index": "k", "bind": {},
                "body": [rational_add_step()]}
    ch = plain_chain([map_step])
    prc, _ = c_spec_parse(ch)
    rrc, _ = c_chain_run(ch, {"row": None, "inputs": {"xs": [1, 2, 3]}})
    rec(kind="form", surface="A", form="map", parse_rc=prc, run_rc=rrc,
        parse_attrib="srmech_compose.c:299-303 co_build_step requires "
                     "class+op+args (a map step has none)",
        run_attrib="srmech_compose_run.c:722-724 cr_run_steps requires a "
                   "STRING \"op\"",
        verdict="unrecognised" if (prc == 2 and rrc == 2) else "CHECK")

    # The three v2 reference namespaces, each on a PLAIN in-table step so the
    # step form is not the variable. co_match_namespace knows 4 of 7.
    for ns, ref in (("idx", "@idx.k"), ("bind", "@bind.x"),
                    ("op", "@op.srmech.math.cyclic.gcd"),
                    ("catalog", "@catalog.foo")):
        ch = plain_chain([{"class": "N", "op": "rational_add",
                           "args": {"a": ref, "b": [1, 3]}}])
        prc, _ = c_spec_parse(ch)
        rrc, _ = c_chain_run(ch, {"row": None, "inputs": {}})
        rec(kind="namespace", surface="A", namespace=ns, ref=ref,
            parse_rc=prc, run_rc=rrc,
            parse_attrib="srmech_compose.c:135-148 co_match_namespace knows "
                         "row|input|step|catalog only",
            run_attrib="srmech_compose_run.c:272-288 cr_resolve_ref knows "
                       "row.|input.|step[N] only (@catalog falls through)")

    # The mixed-form hazard the Python guard exists for (compose.py:419-474).
    mixed = dict(rational_add_step())
    mixed.update({"map_over": "@input.xs", "body": [rational_add_step()]})
    ch = plain_chain([mixed])
    prc, _ = c_spec_parse(ch)
    rrc, rdesc = c_chain_run(ch, {"row": None, "inputs": {"xs": [1, 2]}})
    got = compose._reconstruct_value(json.loads(rdesc)) if rdesc else None
    py_ok = True
    try:
        compose.parse_chain_spec(ch)
    except Exception as exc:                                  # noqa: BLE001
        py_ok = False
        py_err = f"{type(exc).__name__}"
    else:
        py_err = None
    rec(kind="hazard", id="mixed_v1_v2_step", parse_rc=prc, run_rc=rrc,
        c_value=got, python_accepts=py_ok, python_error=py_err,
        note="C is a REQUIRED-KEYS check, not a closed-key-set check: the "
             "map half is silently discarded. compose._chain_has_v2_forms "
             "is what keeps this unreachable today.")


# ────────────────────── P2 the carrier (float) gate ─────────────────────

def p2_carrier():
    """cr_value_t has kinds NONE/INT/STR/RATIONAL/LIST — no FLOAT."""
    int_ch = plain_chain([{"class": "N", "op": "rational_add",
                           "args": {"a": "@input.a", "b": [1, 3]}}])
    for label, val in (("int", [1, 2]), ("float_in_list", [1.5, 2]),
                       ("bare_float", 1.5)):
        rrc, rdesc = c_chain_run(int_ch, {"row": None,
                                          "inputs": {"a": val}})
        rec(kind="carrier", probe=label, arg=val, run_rc=rrc,
            ran=(rrc == 0),
            attrib="srmech_compose_run.c:207-220 cr_json_scalar returns NULL "
                   "for SRMECH_JSON_DOUBLE (array/obj/dbl/bool) -> defer")


# ───────────── P3 the value-descriptor vocabulary (wire format) ──────────

def p3_descriptor_vocab():
    py_kinds = ["s", "q", "i", "n", "l"]          # compose._reconstruct_value
    c_emits = ["n", "i", "s", "q"]                # cr_desc; CR_LIST -> NULL
    probe = {}
    for k in py_kinds:
        desc = {"k": k}
        if k in ("s", "i"):
            desc["v"] = "7" if k == "i" else "x"
        if k == "q":
            desc.update({"n": "5", "d": "6"})
        if k == "l":
            desc["items"] = [{"k": "i", "v": "1"}]
        try:
            probe[k] = repr(compose._reconstruct_value(desc))
        except Exception as exc:                              # noqa: BLE001
            probe[k] = f"RAISES {type(exc).__name__}"
    try:
        compose._reconstruct_value({"k": "f", "v": 1.5})
        f_ok = True
    except Exception:                                          # noqa: BLE001
        f_ok = False
    rec(kind="wire", python_reconstructs=py_kinds, c_emits=c_emits,
        python_round_trip=probe, python_accepts_float_kind=f_ok,
        list_key_python_expects="items",
        list_key_dsl_surface_uses="v",
        attrib_py="compose.py:1075-1090 _reconstruct_value",
        attrib_c="srmech_compose_run.c:639-671 cr_desc",
        note="k='l' is ALREADY reconstructible in Python (reads desc['items'])"
             " but C never emits it; k='f' is NOT reconstructible. So a "
             "LIST-returning C form is Python-compatible as-is; a "
             "FLOAT-returning one is not.")


# ───────────────────────── P4 the shapes to build ───────────────────────

MAPK = ("map_over", "index", "bind", "body")
FOLDK = ("fold_class", "fold_op", "fold_init", "over", "fold_args")


def _walk(steps, depth, acc, chain, fname):
    for i, st in enumerate(steps):
        if not isinstance(st, dict):
            continue
        if any(k in st for k in MAPK):
            acc["map"].append({
                "file": fname, "chain": chain, "depth": depth,
                "index": st.get("index", "k"),
                "map_over": st.get("map_over"),
                "n_bind": len(st.get("bind") or {}),
                "bind_refs": sorted((st.get("bind") or {}).values(),
                                    key=repr),
                "body_len": len(st.get("body") or []),
            })
            _walk(st.get("body") or [], depth + 1, acc, chain, fname)
        elif any(k in st for k in FOLDK):
            acc["fold"].append({
                "file": fname, "chain": chain, "depth": depth,
                "fold_class": st.get("fold_class"),
                "fold_op": st.get("fold_op"),
                "init_type": type(st.get("fold_init")).__name__,
                "init": st.get("fold_init"),
                "over": st.get("over"),
                "fold_args": st.get("fold_args"),
            })
        else:
            acc["plain"].append({"file": fname, "depth": depth,
                                 "class": st.get("class"),
                                 "op": st.get("op")})


def p4_shapes():
    acc = {"map": [], "fold": [], "plain": []}
    for f in sorted(glob.glob(os.path.join(CAT, "*.toml"))):
        doc = tomllib.loads(open(f, encoding="utf-8").read())
        for ch in (doc.get("cascade", {}).get("chain") or []):
            _walk(ch.get("steps") or [], 0, acc,
                  ch.get("summary", "")[:24], os.path.basename(f))
    for m in acc["map"]:
        rec(kind="map_instance", **m)
    for m in acc["fold"]:
        rec(kind="fold_instance", **m)
    rec(kind="shape_summary",
        steps_plain=len(acc["plain"]), steps_map=len(acc["map"]),
        steps_fold=len(acc["fold"]),
        map_max_depth=max((m["depth"] for m in acc["map"]), default=-1),
        fold_max_depth=max((m["depth"] for m in acc["fold"]), default=-1),
        map_max_binds=max((m["n_bind"] for m in acc["map"]), default=0),
        map_max_body_len=max((m["body_len"] for m in acc["map"]), default=0),
        fold_top_level=[m["file"] for m in acc["fold"] if m["depth"] == 0],
        fold_seed_types=sorted({m["init_type"] for m in acc["fold"]}),
        fold_ops=sorted({m["fold_op"] for m in acc["fold"]}),
        map_over_namespaces=sorted({str(m["map_over"]).split(".")[0]
                                    for m in acc["map"]}))
    return acc


# ──────────────── P5 do the body ops have a C kernel at all ─────────────

def p5_body_kernels(acc):
    """For every fold/map body op the descriptors name: does the Python op
    exist, does it route to native, and is there a plausible C symbol?"""
    names = sorted({m["fold_op"] for m in acc["fold"]})
    # the map bodies' own leaf ops (a map body is a step list)
    body_ops = sorted({p["op"] for p in acc["plain"] if p["depth"] > 0})
    for op in names + body_ops:
        leaf = str(op).rpartition(".")[2]
        # candidate C symbol spellings the tree uses
        cands = [f"srmech_cascade_{leaf}", f"srmech_{leaf}",
                 f"srmech_cascade_{leaf}_f64", f"srmech_{leaf}_f64",
                 f"srmech_cascade_{leaf}_i64", f"srmech_{leaf}_u64",
                 f"srmech_cascade_{leaf}_i8"]
        present = [c for c in cands if hasattr(LIB, c)]
        rec(kind="body_kernel", op=op, leaf=leaf,
            c_symbols_present=present,
            has_c_kernel=bool(present),
            in_run_c_ops=(leaf in compose._RUN_C_OPS))


# ───────── P6 arena feasibility of the map arm (the sizing question) ─────

def p6_arena():
    """srmech_chain_run_arena_bytes(chain_len, ctx_len) is LINEAR in the JSON
    lengths. A nested map is QUADRATIC in the data length. Measure where the
    two cross for autocorrelation, whose map-of-map is the worst shipped case.

    Carrier count per outer index k, for autocorrelation's declared body:
      inner map over x  -> n iterations x 2 plain steps  = 2n carriers
                        +  1 list carrier + 1 items array
      compensated_sum   -> 1 carrier
    so total ~= n*(2n + 3) + 1 = 2n^2 + 3n + 1 carriers.

    Bytes/carrier is bounded by the arena function's OWN assert
    (srmech_compose_run.c:686 ``assert(sizeof(cr_value_t) <= 128u)``), so 128
    is an upper bound and the crossover below is a LOWER bound on capacity.
    """
    doc = tomllib.loads(open(os.path.join(CAT, "autocorrelation.toml"),
                             encoding="utf-8").read())
    ch = doc["cascade"]["chain"][0]
    chain_dict = {"name": "autocorrelation", "summary": ch["summary"],
                  "returns": ch["returns"], "on_error": "raise",
                  "steps": ch["steps"]}
    chain_len = len(json.dumps(chain_dict, ensure_ascii=False)
                    .encode("utf-8"))
    rows = []
    for n in (1, 4, 5, 8, 16, 32, 64, 128, 256, 512):
        ctx = {"row": None, "inputs": {"x": [1.5] * n}}
        ctx_len = len(json.dumps(ctx, ensure_ascii=False).encode("utf-8"))
        arena = int(LIB.srmech_chain_run_arena_bytes(chain_len, ctx_len))
        # the arena function's own three terms (srmech_compose_run.c:677-688)
        run_term = 4096 * chain_len + (1 << 20)
        carriers = 2 * n * n + 3 * n + 1
        need = 128 * carriers
        rows.append({"n": n, "ctx_len": ctx_len, "arena_total": arena,
                     "run_term": run_term, "carriers": carriers,
                     "carrier_bytes_upper": need, "fits": need <= run_term})
    rec(kind="arena", op="autocorrelation", chain_len=chain_len,
        arena_fn="srmech_chain_run_arena_bytes(chain_len, ctx_len)",
        arena_is_linear_in="chain_len, ctx_len",
        map_carriers_grow_as="O(n^2) for a map-of-map",
        rows=rows,
        first_n_that_overflows=next((r["n"] for r in rows
                                     if not r["fits"]), None),
        note="the run term does not read n at all: 4096*chain_len + 1MiB "
             "(srmech_compose_run.c:683). A map arm therefore needs either a "
             "data-aware arena term or a DECLARED capacity boundary.")


def main():
    rec(kind="environment", srmech_version=srmech.__version__,
        native=srmech.native_status(),
        engine_schema_version=compose.ENGINE_SCHEMA_VERSION,
        supported_schema_versions=list(compose.SUPPORTED_SCHEMA_VERSIONS),
        run_c_ops=sorted(compose._RUN_C_OPS),
        run_c_ops_size=len(compose._RUN_C_OPS),
        describe_cascade_catalog=srmech.describe()["cascade_catalog"])
    ok = p0_controls()
    if not ok:
        print("POSITIVE CONTROLS FAILED — nothing attributed", file=sys.stderr)
    else:
        p1_forms()
        p2_carrier()
        p3_descriptor_vocab()
        acc = p4_shapes()
        p5_body_kernels(acc)
        p6_arena()
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in RECS:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    for r in RECS:
        print(json.dumps(r, sort_keys=True, ensure_ascii=False))
    print(f"\n[wrote {len(RECS)} records to {OUT}]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
