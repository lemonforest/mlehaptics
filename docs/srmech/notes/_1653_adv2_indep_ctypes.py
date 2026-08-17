"""ADVERSARIAL round-2 independent re-measurement of the adr0009-decline claims.

Written from the HEADER prototypes, not from the deliverable's own harness. Uses REAL
shipped descriptor chains (json.dumps of the live ChainSpec) wherever a real one exists,
so a synthetic-shape mistake in the deliverable's probes cannot be reproduced here.

Run:  cd docs/srmech/python && python3 ../notes/_1653_adv2_indep_ctypes.py
"""
import ctypes
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
WT = HERE.parent                      # docs/srmech
sys.path.insert(0, str(WT / "python"))

import srmech                                                   # noqa: E402
from srmech.cascade import compose as CO                        # noqa: E402

SO = WT / "python" / "srmech" / "_native" / "libsrmech.so"
lib = ctypes.CDLL(str(SO))

for fn, n_args in (("srmech_chain_spec_parse_arena_bytes", 1),
                   ("srmech_chain_catalog_parse_arena_bytes", 1),
                   ("srmech_chain_run_arena_bytes", 2)):
    getattr(lib, fn).restype = ctypes.c_size_t
    getattr(lib, fn).argtypes = [ctypes.c_size_t] * n_args

lib.srmech_chain_spec_parse.restype = ctypes.c_int
lib.srmech_chain_catalog_parse.restype = ctypes.c_int
lib.srmech_chain_run.restype = ctypes.c_int
lib.srmech_gcd.restype = ctypes.c_int
lib.srmech_gcd.argtypes = [ctypes.c_uint64, ctypes.c_uint64,
                           ctypes.POINTER(ctypes.c_uint64)]
lib.srmech_cascade_cyclic_gcd_u64.restype = ctypes.c_int
lib.srmech_cascade_cyclic_gcd_u64.argtypes = [ctypes.c_uint64, ctypes.c_uint64,
                                              ctypes.POINTER(ctypes.c_uint64)]

OUT_CAP = 1 << 20
FINDINGS = []


def _call3(fn, arena_fn, payload, extra=None):
    p = payload.encode("utf-8")
    if extra is None:
        nb = arena_fn(len(p))
        ws = (ctypes.c_char * nb)()
        out = (ctypes.c_char * OUT_CAP)()
        ol = ctypes.c_size_t()
        rc = fn(p, len(p), ws, nb, out, OUT_CAP, ctypes.byref(ol))
    else:
        q = extra.encode("utf-8")
        nb = arena_fn(len(p), len(q))
        ws = (ctypes.c_char * nb)()
        out = (ctypes.c_char * OUT_CAP)()
        ol = ctypes.c_size_t()
        rc = fn(p, len(p), q, len(q), ws, nb, out, OUT_CAP, ctypes.byref(ol))
    return rc, out.raw[:ol.value].decode("utf-8", "replace")


def c_parse(chain):
    return _call3(lib.srmech_chain_spec_parse,
                  lib.srmech_chain_spec_parse_arena_bytes, json.dumps(chain))


def c_run(chain, ctx):
    return _call3(lib.srmech_chain_run, lib.srmech_chain_run_arena_bytes,
                  json.dumps(chain), json.dumps(ctx))


def c_cat(version, chains):
    doc = {"chain_schema_version": version, "operator_chain": chains}
    return _call3(lib.srmech_chain_catalog_parse,
                  lib.srmech_chain_catalog_parse_arena_bytes, json.dumps(doc))


def check(label, got, want):
    ok = got == want
    FINDINGS.append((label, got, want, ok))
    print("%-4s %-58s got=%-28s want=%s" % ("ok" if ok else "FAIL", label,
                                            repr(got), repr(want)))
    return ok


PLAIN = {"name": "adv_plain", "summary": "s", "returns": "r",
         "steps": [{"class": "N", "op": "pi_cascade_digits",
                    "args": {"num_digits": 5}}]}


def main():
    print("srmech %s  ABI %s (expected %s)  so=%s\n"
          % (srmech.__version__, srmech._native.ABI_VERSION,
             srmech._native.EXPECTED_ABI_VERSION, SO.name))

    # ---- 1. Surface-A step forms: positive control + map + fold -------------
    rc, o = c_parse(PLAIN)
    check("A/plain parse", rc, 0)
    rc, o = c_run(PLAIN, {"row": None, "inputs": {}})
    check("A/plain run", rc, 0)
    check("A/plain run value", json.loads(o) if rc == 0 else o,
          {"k": "s", "v": "3.14159"})

    mp = dict(PLAIN, name="adv_map", steps=[
        {"map_over": "@input.xs", "index": "i", "bind": "x",
         "body": [{"class": "N", "op": "pi_cascade_digits",
                   "args": {"num_digits": "@bind.x"}}]}])
    check("A/map parse", c_parse(mp)[0], 2)
    check("A/map run", c_run(mp, {"row": None, "inputs": {"xs": [1, 2]}})[0], 2)

    fd = dict(PLAIN, name="adv_fold", steps=[
        {"fold_class": "C",
         "fold_op": "srmech.cascade.leaves.orientation_compose",
         "fold_init": 1, "over": "@input.xs"}])
    check("A/fold parse", c_parse(fd)[0], 2)
    check("A/fold run", c_run(fd, {"row": None, "inputs": {"xs": [1, 2]}})[0], 2)

    # ---- 2. reference namespaces -------------------------------------------
    def ref_chain(ref):
        return dict(PLAIN, name="adv_ref", steps=[
            {"class": "N", "op": "pi_cascade_digits", "args": {"num_digits": ref}}])
    ctx = {"row": {"x": 5}, "inputs": {"a": 5}}
    for ref, wp, wr in (("@input.a", 0, 0), ("@row.x", 0, 0),
                        ("@catalog.row.x", 0, 2), ("@idx.i", 2, 2),
                        ("@bind.x", 2, 2), ("@op.srmech.cascade.magnitude", 2, 2)):
        check("ns %-28s parse" % ref, c_parse(ref_chain(ref))[0], wp)
        check("ns %-28s run" % ref, c_run(ref_chain(ref), ctx)[0], wr)

    # ---- 3. single-scalar carrier attribution ------------------------------
    for lit, wp, wr in ((5, 0, 0), (5.0, 0, 2), (True, 0, 2), ("5", 0, 2)):
        ch = dict(PLAIN, steps=[{"class": "N", "op": "pi_cascade_digits",
                                 "args": {"num_digits": lit}}])
        check("carrier %-6r parse" % (lit,), c_parse(ch)[0], wp)
        check("carrier %-6r run" % (lit,), c_run(ch, {"row": None, "inputs": {}})[0], wr)

    # ---- 4. catalog chain_schema_version ------------------------------------
    check("catalog v1", c_cat(1, [PLAIN])[0], 0)
    check("catalog v2", c_cat(2, [PLAIN])[0], 2)
    check("python SUPPORTED_SCHEMA_VERSIONS", CO.SUPPORTED_SCHEMA_VERSIONS, (1, 2))

    # ---- 5. the D-3 "gap is the table not the math" claim -------------------
    o1 = ctypes.c_uint64()
    o2 = ctypes.c_uint64()
    check("srmech_gcd(12,18) rc", lib.srmech_gcd(12, 18, ctypes.byref(o1)), 0)
    check("srmech_gcd(12,18) out", o1.value, 6)
    check("cyclic_gcd_u64(12,18) rc",
          lib.srmech_cascade_cyclic_gcd_u64(12, 18, ctypes.byref(o2)), 0)
    check("cyclic_gcd_u64(12,18) out", o2.value, 6)

    # ---- 6. arena decline is CLEAN under an undersized workspace ------------
    p = json.dumps(PLAIN).encode()
    q = json.dumps({"row": None, "inputs": {}}).encode()
    demand = lib.srmech_chain_run_arena_bytes(len(p), len(q))
    for frac, want in ((1.0, 0), (0.1, 0), (0.01, 4), (0.001, 4)):
        nb = max(1, int(demand * frac))
        ws = (ctypes.c_char * nb)()
        out = (ctypes.c_char * OUT_CAP)()
        ol = ctypes.c_size_t()
        rc = lib.srmech_chain_run(p, len(p), q, len(q), ws, nb, out, OUT_CAP,
                                  ctypes.byref(ol))
        check("arena %.3f of demand" % frac, rc, want)

    # ---- 7. #T1146 silent accept: is it a BUG or a decline? ----------------
    import srmech.cascade as SC
    from srmech.dsl import chain as dsl_chain
    native_val = dsl_chain().then("magnitude", bogus=1).run(-3.5)
    try:
        SC.magnitude(-3.5, bogus=1)
        pure_val = "ACCEPTED"
    except TypeError as exc:
        pure_val = "TypeError"
    check("T1146 dsl native magnitude(bogus)", native_val, 3.5)
    check("T1146 pure magnitude(bogus)", pure_val, "TypeError")
    check("T1146 direction is C-accepts-more (a BUG, not a capability gap)",
          (native_val == 3.5 and pure_val == "TypeError"), True)

    # ---- 8. reverse-direction: seq_get ------------------------------------
    check("seq_get in srmech.cascade", hasattr(SC, "seq_get"), True)

    print("\n%d checks, %d FAIL" % (len(FINDINGS), sum(1 for f in FINDINGS if not f[3])))
    return 0 if all(f[3] for f in FINDINGS) else 1


if __name__ == "__main__":
    sys.exit(main())
