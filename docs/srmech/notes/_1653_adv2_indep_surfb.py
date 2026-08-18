"""ADVERSARIAL round-2 independent re-measurement, part 2: Surface B + the TOML front end.

Run:  cd docs/srmech/python && python3 ../notes/_1653_adv2_indep_surfb.py
"""
import ctypes
import json
import pathlib
import sys
import tomllib

HERE = pathlib.Path(__file__).resolve().parent
WT = HERE.parent
sys.path.insert(0, str(WT / "python"))
import srmech  # noqa: E402

SO = WT / "python" / "srmech" / "_native" / "libsrmech.so"
CAT = WT / "python" / "srmech" / "cascade" / "catalogs" / "cascade_catalog"
lib = ctypes.CDLL(str(SO))
for f in ("srmech_dsl_chain_run_arena_bytes",):
    getattr(lib, f).restype = ctypes.c_size_t
    getattr(lib, f).argtypes = [ctypes.c_size_t, ctypes.c_size_t]
lib.srmech_dsl_toml_chain_to_json_arena_bytes.restype = ctypes.c_size_t
lib.srmech_dsl_toml_chain_to_json_arena_bytes.argtypes = [ctypes.c_size_t]
lib.srmech_dsl_chain_run.restype = ctypes.c_int
lib.srmech_dsl_toml_chain_to_json.restype = ctypes.c_int
lib.srmech_plat_has_threads.restype = ctypes.c_int

CAP = 1 << 22


def dsl_run(chain, inp):
    p = json.dumps(chain).encode()
    q = json.dumps(inp).encode()
    nb = lib.srmech_dsl_chain_run_arena_bytes(len(p), len(q))
    ws = (ctypes.c_char * nb)()
    out = (ctypes.c_char * CAP)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_dsl_chain_run(p, len(p), q, len(q), ws, nb, out, CAP,
                                  ctypes.byref(ol))
    return rc, out.raw[:ol.value].decode("utf-8", "replace")


def toml_c(src_bytes):
    nb = lib.srmech_dsl_toml_chain_to_json_arena_bytes(len(src_bytes))
    ws = (ctypes.c_char * nb)()
    out = (ctypes.c_char * CAP)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_dsl_toml_chain_to_json(src_bytes, len(src_bytes), ws, nb,
                                           out, CAP, ctypes.byref(ol))
    return rc, out.raw[:ol.value].decode("utf-8", "replace")


F = []


def check(label, got, want):
    ok = got == want
    F.append(ok)
    print("%-4s %-52s got=%-22s want=%s" % ("ok" if ok else "FAIL", label,
                                            repr(got), repr(want)))


# ---- Surface B: leaf control / loop control / parallel_body ---------------
IN = {"k": "f", "v": -3.5}
leaf = {"chain": {"name": "p"}, "stage": [{"op": "magnitude"}]}
loop = {"chain": {"name": "p"},
        "stage": [{"loop_n": 3, "sub_chain": [{"op": "magnitude"}]}]}
par = {"chain": {"name": "p"},
       "stage": [{"parallel_body": "chiral_flip", "n_sectors": 4,
                  "combine": "bundle"}]}
for name, ch, want in (("leaf control", leaf, 0), ("loop_n control", loop, 0),
                       ("parallel_body", par, 5)):
    rc, o = dsl_run(ch, IN)
    check("surfB %s" % name, rc, want)
    if rc == 0:
        print("        value=%s" % o)

check("srmech_plat_has_threads()", lib.srmech_plat_has_threads(), 1)

# ---- TOML front end over the 21 real descriptors --------------------------
files = sorted(CAT.glob("*.toml"))
check("descriptor count", len(files), 21)
c_ok, c_bad, py_bad = [], [], []
for f in files:
    raw = f.read_bytes()
    rc, _ = toml_c(raw)
    (c_ok if rc == 0 else c_bad).append(f.name)
    try:
        tomllib.loads(raw.decode("utf-8"))
    except Exception:
        py_bad.append(f.name)
check("C TOML front end accepts", len(c_ok), 19)
check("C TOML front end rejects", sorted(c_bad),
      ["best_rational_signed.toml", "magnitude.toml"])
check("tomllib rejects", py_bad, [])

# ---- minimal nan/inf attribution -----------------------------------------
for lit, want in (("1.5", 0), ("nan", 2), ("inf", 2)):
    doc = ('[chain]\nname = "p"\n\n[[stage]]\nop = "magnitude"\nx = %s\n' % lit)
    rc, _ = toml_c(doc.encode())
    check("toml literal x = %-4s" % lit, rc, want)

print("\n%d checks, %d FAIL" % (len(F), sum(1 for x in F if not x)))
sys.exit(0 if all(F) else 1)
