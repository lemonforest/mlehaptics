#!/usr/bin/env python3
"""ADVERSARIAL independent re-measurement of the adr0009-decline deliverable.

Written from `c/include/srmech.h` prototypes only — it deliberately does NOT
import or reuse `_1653_adr0009_decline_verify.py`.  Every boundary is a live
ctypes call on the shipped `libsrmech.so`, each with its own positive control.

Run:  cd docs/srmech/python && python3 ../notes/_1653_adv_declineaudit_recheck.py
"""
import ctypes
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import srmech                                        # noqa: E402
import srmech._native as _native                     # noqa: E402

LIB = ctypes.CDLL(str(_native._LIB_PATH))
STATUS = {0: "OK=0", 1: "ERR=1", 2: "BAD_INPUT=2", 3: "NOT_FOUND=3", 4: "OVERFLOW=4",
          5: "NOT_IMPL=5", 6: "6", 7: "7", 8: "LIMIT=8"}

CAT = (Path(__file__).resolve().parents[1] / "python" / "srmech" / "cascade"
       / "catalogs" / "cascade_catalog")


def _decl(name, argtypes, restype=ctypes.c_int):
    f = getattr(LIB, name)
    f.argtypes = argtypes
    f.restype = restype
    return f


CCP, SZ, VP, CP, SZP = (ctypes.c_char_p, ctypes.c_size_t, ctypes.c_void_p,
                        ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t))
parse_ab = _decl("srmech_chain_spec_parse_arena_bytes", [SZ], SZ)
parse = _decl("srmech_chain_spec_parse", [CCP, SZ, VP, SZ, CP, SZ, SZP])
run_ab = _decl("srmech_chain_run_arena_bytes", [SZ, SZ], SZ)
run = _decl("srmech_chain_run", [CCP, SZ, CCP, SZ, VP, SZ, CP, SZ, SZP])
cat_ab = _decl("srmech_chain_catalog_parse_arena_bytes", [SZ], SZ)
cat_parse = _decl("srmech_chain_catalog_parse", [CCP, SZ, VP, SZ, CP, SZ, SZP])
dsl_ab = _decl("srmech_dsl_chain_run_arena_bytes", [SZ, SZ], SZ)
dsl_run = _decl("srmech_dsl_chain_run", [CCP, SZ, CCP, SZ, VP, SZ, CP, SZ, SZP])
toml_ab = _decl("srmech_dsl_toml_chain_to_json_arena_bytes", [SZ], SZ)
toml_j = _decl("srmech_dsl_toml_chain_to_json", [CCP, SZ, VP, SZ, CP, SZ, SZP])


def c_parse(chain):
    cj = json.dumps(chain, separators=(",", ":")).encode()
    ws = ctypes.create_string_buffer(parse_ab(len(cj)))
    out = ctypes.create_string_buffer(65536)
    n = ctypes.c_size_t(0)
    st = parse(cj, len(cj), ctypes.cast(ws, VP), len(ws), out, 65536, ctypes.byref(n))
    return STATUS.get(st, st), out.raw[:n.value].decode(errors="replace")


def c_run(chain, ctx, scale=1.0):
    cj = json.dumps(chain, separators=(",", ":")).encode()
    xj = json.dumps(ctx, separators=(",", ":")).encode()
    need = run_ab(len(cj), len(xj))
    ws = ctypes.create_string_buffer(max(64, int(need * scale)))
    out = ctypes.create_string_buffer(65536)
    n = ctypes.c_size_t(0)
    st = run(cj, len(cj), xj, len(xj), ctypes.cast(ws, VP), len(ws),
             out, 65536, ctypes.byref(n))
    return STATUS.get(st, st), out.raw[:n.value].decode(errors="replace"), need


def c_cat_parse(doc):
    dj = json.dumps(doc, separators=(",", ":")).encode()
    ws = ctypes.create_string_buffer(cat_ab(len(dj)))
    out = ctypes.create_string_buffer(65536)
    n = ctypes.c_size_t(0)
    st = cat_parse(dj, len(dj), ctypes.cast(ws, VP), len(ws), out, 65536,
                   ctypes.byref(n))
    return STATUS.get(st, st)


def c_dsl(stages, inp):
    cj = json.dumps(stages, separators=(",", ":")).encode()
    ij = json.dumps(inp, separators=(",", ":")).encode()
    ws = ctypes.create_string_buffer(dsl_ab(len(cj), len(ij)))
    out = ctypes.create_string_buffer(65536)
    n = ctypes.c_size_t(0)
    st = dsl_run(cj, len(cj), ij, len(ij), ctypes.cast(ws, VP), len(ws),
                 out, 65536, ctypes.byref(n))
    return STATUS.get(st, st), out.raw[:n.value].decode(errors="replace")


def c_toml(src: bytes):
    ws = ctypes.create_string_buffer(toml_ab(len(src)))
    out = ctypes.create_string_buffer(1 << 20)
    n = ctypes.c_size_t(0)
    st = toml_j(src, len(src), ctypes.cast(ws, VP), len(ws), out, 1 << 20,
                ctypes.byref(n))
    return STATUS.get(st, st)


def chain(steps, name="probe"):
    return {"name": name, "summary": "s", "returns": "r", "on_error": "raise",
            "steps": steps}


PLAIN = [{"class": "N", "op": "srmech.math.rational.best_rational",
          "args": {"numerator": 5, "denominator": 6, "max_denominator": 100}}]
MAP = [{"map_over": "@input.xs", "index": "i", "bind": {"x": "@idx.i"},
        "body": [{"class": "C", "op": "srmech.cascade.reorient",
                  "args": {"orientation": 1}}]}]
FOLD = [{"fold_class": "C", "fold_op": "srmech.cascade.leaves.orientation_compose",
         "fold_init": 1, "over": "@input.orientations"}]

print("srmech %s  ABI %s  has_native=%s  lib=%s"
      % (srmech.__version__, _native.NATIVE_ABI_VERSION, _native.HAS_NATIVE,
         Path(_native._LIB_PATH).name))
print()
print("A. SURFACE-A STEP FORMS (plain = the positive control)")
for label, steps, ctx in (("plain (CONTROL)", PLAIN, {"row": {}, "inputs": {}}),
                          ("map", MAP, {"row": {}, "inputs": {"xs": [1, -1]}}),
                          ("fold", FOLD, {"row": {},
                                          "inputs": {"orientations": [-1, -1]}})):
    ps, _ = c_parse(chain(steps))
    rs, rv, _ = c_run(chain(steps), ctx)
    print("   %-16s parse %-12s run %-12s %s" % (label, ps, rs, rv[:48]))

print()
print("B. SINGLE-SCALAR ATTRIBUTION on an in-table op (pi_cascade_digits)")
for label, v in (("5 (CONTROL int)", 5), ("5.0 float", 5.0), ("true bool", True),
                 ('"5" str', "5")):
    st = [{"class": "N", "op": "srmech.math.rational.pi_cascade_digits",
           "args": {"num_digits": v}}]
    ps, _ = c_parse(chain(st))
    rs, rv, _ = c_run(chain(st), {"row": {}, "inputs": {}})
    print("   %-18s parse %-12s run %-12s %s" % (label, ps, rs, rv[:48]))

print()
print("C. CATALOG chain_schema_version GATE")
for v in (1, 2):
    doc = {"chain_schema_version": v, "operator_chain": [chain(PLAIN)]}
    print("   catalog v%d -> %s" % (v, c_cat_parse(doc)))
print("   python SUPPORTED_SCHEMA_VERSIONS =",
      __import__("srmech.cascade.compose", fromlist=["x"]).SUPPORTED_SCHEMA_VERSIONS)

print()
print("D. REFERENCE NAMESPACES (@input / @row are the controls)")
NS = [("@input.a (CONTROL)", "@input.a"), ("@row.x (CONTROL)", "@row.x"),
      ("@catalog.row.x", "@catalog.row.x"), ("@idx.i", "@idx.i"),
      ("@bind.x", "@bind.x"), ("@op.a.b.c", "@op.a.b.c")]
for label, ref in NS:
    st = [{"class": "N", "op": "srmech.math.rational.pi_cascade_digits",
           "args": {"num_digits": ref}}]
    ps, _ = c_parse(chain(st))
    rs, _, _ = c_run(chain(st), {"row": {"x": 5}, "inputs": {"a": 5}})
    print("   %-20s parse %-12s run %-12s" % (label, ps, rs))

print()
print("E. SURFACE-B parallel_body (two live controls)")
for label, stages in (
        ("leaf (CONTROL)", [{"op": "magnitude"}]),
        ("loop_n (CONTROL)", [{"loop_n": 3, "sub_chain": [{"op": "magnitude"}]}]),
        ("parallel_body", [{"parallel_body": "chiral_flip", "n_sectors": 4,
                            "combine": "bundle"}])):
    st, v = c_dsl(stages, {"k": "f", "v": -3.5})
    print("   %-18s %-12s %s" % (label, st, v[:40]))
print("   srmech_plat_has_threads() =", LIB.srmech_plat_has_threads())

print()
print("F. ARENA: the same chain at fractions of its own demand")
for frac in (1.0, 0.1, 0.01, 0.001):
    st, v, need = c_run(chain(PLAIN), {"row": {}, "inputs": {}}, scale=frac)
    print("   ws=%9d (%.3f of %d) -> %-12s %s"
          % (int(need * frac), frac, need, st, v[:32]))

print()
print("G. C TOML FRONT END over the 21 shipped descriptors")
bad = []
tot = 0
for p in sorted(CAT.glob("*.toml")):
    tot += 1
    st = c_toml(p.read_bytes())
    if st != "OK=0":
        bad.append((p.stem, st))
print("   descriptors=%d  C-rejected=%s" % (tot, bad))
for label, src in (("x = 1.5", b"x = 1.5\n"), ("x = nan", b"x = nan\n"),
                   ("x = inf", b"x = inf\n")):
    print("   %-10s -> %s" % (label, c_toml(src)))
import tomllib                                        # noqa: E402
pybad = []
for p in sorted(CAT.glob("*.toml")):
    try:
        tomllib.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:                           # noqa: BLE001
        pybad.append((p.stem, type(exc).__name__))
print("   tomllib-rejected =", pybad or "NONE")

print()
print("H. THE WEDGE: the gcd kernels the cyclic_gcd chain cannot reach")
g = _decl("srmech_gcd", [ctypes.c_uint64, ctypes.c_uint64,
                         ctypes.POINTER(ctypes.c_uint64)])
o = ctypes.c_uint64(0)
print("   srmech_gcd(12,18) -> rc=%d out=%d" % (g(12, 18, ctypes.byref(o)), o.value))
g2 = _decl("srmech_cascade_cyclic_gcd_u64", [ctypes.c_uint64, ctypes.c_uint64,
                                             ctypes.POINTER(ctypes.c_uint64)])
o2 = ctypes.c_uint64(0)
print("   srmech_cascade_cyclic_gcd_u64(12,18) -> rc=%d out=%d"
      % (g2(12, 18, ctypes.byref(o2)), o2.value))

print()
print("I. #T1146 silent accept, live")
from srmech.dsl import chain as dslchain                # noqa: E402
import srmech.cascade as SC                            # noqa: E402
try:
    native = dslchain().then("magnitude", bogus=1).run(-3.5)
except Exception as exc:                               # noqa: BLE001
    native = "%s: %s" % (type(exc).__name__, exc)
try:
    pure = SC.magnitude(-3.5, bogus=1)
except Exception as exc:                               # noqa: BLE001
    pure = "%s: %s" % (type(exc).__name__, exc)
print("   chain().then('magnitude', bogus=1).run(-3.5) ->", native)
print("   srmech.cascade.magnitude(-3.5, bogus=1)      ->", pure)
