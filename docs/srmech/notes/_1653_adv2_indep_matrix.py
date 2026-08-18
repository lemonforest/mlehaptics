"""ADVERSARIAL round-2 independent re-measurement, part 3: the 20-variant residual matrix
and the arena-demand min/max, built straight from the TOML with my own ctypes host.

Run:  cd docs/srmech/python && python3 ../notes/_1653_adv2_indep_matrix.py
"""
import ctypes
import json
import pathlib
import sys
import tomllib

HERE = pathlib.Path(__file__).resolve().parent
WT = HERE.parent
sys.path.insert(0, str(WT / "python"))
from srmech.cascade import compose as CO   # noqa: E402  (only for _RUN_C_OPS)

SO = WT / "python" / "srmech" / "_native" / "libsrmech.so"
CAT = WT / "python" / "srmech" / "cascade" / "catalogs" / "cascade_catalog"
lib = ctypes.CDLL(str(SO))
lib.srmech_chain_spec_parse_arena_bytes.restype = ctypes.c_size_t
lib.srmech_chain_spec_parse_arena_bytes.argtypes = [ctypes.c_size_t]
lib.srmech_chain_run_arena_bytes.restype = ctypes.c_size_t
lib.srmech_chain_run_arena_bytes.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
lib.srmech_chain_spec_parse.restype = ctypes.c_int
lib.srmech_chain_run.restype = ctypes.c_int
CAP = 1 << 21


def parse(ch):
    p = json.dumps(ch, ensure_ascii=False).encode()
    nb = lib.srmech_chain_spec_parse_arena_bytes(len(p))
    ws = (ctypes.c_char * nb)()
    out = (ctypes.c_char * CAP)()
    ol = ctypes.c_size_t()
    return lib.srmech_chain_spec_parse(p, len(p), ws, nb, out, CAP, ctypes.byref(ol))


def run(ch, ctx):
    p = json.dumps(ch, ensure_ascii=False).encode()
    q = json.dumps(ctx, ensure_ascii=False).encode()
    nb = lib.srmech_chain_run_arena_bytes(len(p), len(q))
    ws = (ctypes.c_char * nb)()
    out = (ctypes.c_char * CAP)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_chain_run(p, len(p), q, len(q), ws, nb, out, CAP, ctypes.byref(ol))
    return rc, nb


def hf(o):
    if isinstance(o, float):
        return True
    if isinstance(o, dict):
        return any(hf(v) for v in o.values())
    if isinstance(o, (list, tuple)):
        return any(hf(v) for v in o)
    return False


def has_v2_form(steps):
    for st in steps or []:
        if not isinstance(st, dict):
            continue
        if "map_over" in st or "fold_op" in st or "fold_init" in st:
            return True
        if isinstance(st.get("body"), list) and has_v2_form(st["body"]):
            return True
    return False


def refs(o, acc):
    if isinstance(o, str) and o.startswith("@"):
        acc.add(o.split(".")[0].split("[")[0])
    elif isinstance(o, dict):
        for v in o.values():
            refs(v, acc)
    elif isinstance(o, (list, tuple)):
        for v in o:
            refs(v, acc)


def ops_of(steps, acc):
    for st in steps or []:
        if not isinstance(st, dict):
            continue
        if isinstance(st.get("op"), str):
            acc.add(st["op"])
        if isinstance(st.get("fold_op"), str):
            acc.add(st["fold_op"])
        if isinstance(st.get("body"), list):
            ops_of(st["body"], acc)


rows = []
for f in sorted(CAT.glob("*.toml")):
    cas = tomllib.loads(f.read_text()).get("cascade") or {}
    ch = cas.get("chain")
    if ch is None:
        continue
    for c in (ch if isinstance(ch, list) else [ch]):
        vn = "%s.%s" % (cas["name"], c.get("variant", "default"))
        pc = (c.get("proof_cases") or [{}])[0]
        ctx = {"row": pc.get("row"), "inputs": pc.get("inputs") or {}}
        cd = {"name": vn, "summary": str(c.get("summary", "")),
              "returns": str(c.get("returns", "")),
              "on_error": c.get("on_error", "raise"), "steps": c.get("steps", [])}
        prc = parse(cd)
        # run twice: with the REAL proof-case ctx (stronger) and with an empty one
        rrc, nb = run(cd, ctx)
        rrc_empty, _ = run(cd, {"row": None, "inputs": {}})
        if rrc == 0 or rrc_empty == 0:
            print("  RUN ACCEPTED: %s real=%d empty=%d" % (vn, rrc, rrc_empty))
        if c.get("on_error") not in (None, "raise"):
            print("  NON-RAISE on_error: %s -> %r" % (vn, c.get("on_error")))
        o = set()
        ops_of(c.get("steps"), o)
        r = set()
        refs(c.get("steps"), r)
        rows.append({
            "variant": vn, "parse": prc, "run": rrc, "arena": nb,
            "v2form": has_v2_form(c.get("steps")),
            "float": hf(c.get("steps")) or hf([p.get("inputs") for p in
                                               c.get("proof_cases", []) or []]),
            "bad_ns": sorted(r - {"@row", "@input", "@step", "@catalog"}),
            "ops_outside": sorted(x for x in o
                                  if x.split(".")[-1] not in CO._RUN_C_OPS),
        })

n = len(rows)
pa = [r for r in rows if r["parse"] == 0]
pr = [r for r in rows if r["parse"] != 0]
ra = [r for r in rows if r["run"] == 0]
only_table = [r for r in pa if not r["v2form"] and not r["bad_ns"]
              and not r["float"] and r["ops_outside"]]
pa_float = [r for r in pa if r["float"]]
print("variants                              : %d   (want 20)" % n)
print("parse ACCEPT / REJECT                 : %d / %d   (want 11 / 9)" % (len(pa), len(pr)))
print("run ACCEPT                            : %d   (want 0)" % len(ra))
print("parse-accepting, op table only blocker: %d %s" % (len(only_table),
                                                         [r["variant"] for r in only_table]))
print("parse-accepting that carry a float    : %d %s" % (len(pa_float),
                                                         [r["variant"] for r in pa_float]))
mn = min(rows, key=lambda r: r["arena"])
mx = max(rows, key=lambda r: r["arena"])
print("arena min : %-28s %.2f MB" % (mn["variant"], mn["arena"] / 1e6))
print("arena max : %-28s %.2f MB" % (mx["variant"], mx["arena"] / 1e6))
print("descriptors (files with a [cascade.chain]) :",
      len({r["variant"].split(".")[0] for r in rows}))
