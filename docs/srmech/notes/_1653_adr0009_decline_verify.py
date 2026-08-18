#!/usr/bin/env python3
"""ADR-0009 §5 FILED-DECLINE list — the verification pass behind every row.

gh #1653, pre-rcN research round 2, definition-of-done item 7.  srmech 0.9.0rc444.

WHY THIS EXISTS.  ADR-0009 §5 requires that every clean decline file a tracked
gap naming (a) the capability, (b) the declining implementation, (c) the
boundary.  A decline list whose boundaries are ASSERTED rather than MEASURED is
the same failure mode §5 exists to stop — a comment where a ledger row belongs.
So each row of `notes/_1653_adr0009_decline_list.md` carries a probe id here,
and this script prints and NDJSONs the measurement for it.

Every C boundary is measured by a real ctypes call on the shipped
``libsrmech.so``; every source anchor is re-read from disk and its line content
recorded, so a stale line number is caught rather than quoted.

Discipline: no ALU-magnitude idiom (the Class-K pin-slot op is named where a
magnitude is meant), no numpy, no RNG, no stdlib fractions, exact integers.
Hashing routes through ``srmech.amsc.format.sha256_bytes`` per the monorepo C
discipline (no direct hashlib).  Writes only under docs/srmech/notes/.  Edits no
shipped source.
"""
import ctypes
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRMECH = _HERE.parent                      # docs/srmech
_PY = _SRMECH / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

import srmech                                                    # noqa: E402
from srmech import _native                                       # noqa: E402
from srmech.amsc.format import sha256_bytes                      # noqa: E402
from srmech.cascade import compose as CO                         # noqa: E402
from srmech.dsl import _cascade_chain as CC                      # noqa: E402
from srmech.dsl import _catalog as DCAT                          # noqa: E402
from srmech.dsl import chain as dsl_chain                        # noqa: E402

OUT = _HERE / "_1653_adr0009_decline_verify.ndjson"
ADR = _SRMECH / "adr" / "0009-multi-implementation-parity-capability-is-the-invariant.md"
C_SRC = _SRMECH / "c" / "src"
C_INC = _SRMECH / "c" / "include" / "srmech.h"
CAT_DIR = _PY / "srmech" / "cascade" / "catalogs" / "cascade_catalog"

STATUS = {0: "OK", 1: "NULL_ARG", 2: "BAD_INPUT", 3: "IO", 4: "OVERFLOW",
          5: "NOT_IMPL", 6: "INTERNAL", 7: "UNSUPPORTED", 8: "LIMIT"}
RECS = []


def rec(**kw):
    RECS.append(kw)
    return kw


def sname(rc):
    return "%s=%d" % (STATUS.get(rc, "?"), rc)


# ══════════════════════════════════════════════════════════════════════
# raw C callers (marshalling mirrors the shipped dispatcher)
# ══════════════════════════════════════════════════════════════════════

def _dumps(o):
    return json.dumps(o, ensure_ascii=False).encode("utf-8")


def c_spec_parse(chain_dict):
    lib = _native.LIB
    p = _dumps(chain_dict)
    nb = int(lib.srmech_chain_spec_parse_arena_bytes(len(p)))
    ws = (ctypes.c_char * nb)()
    cap = 2 * len(p) + 8192
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_chain_spec_parse(p, len(p), ws, nb, out, cap, ctypes.byref(ol))
    return int(rc), (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_chain_run(chain_dict, ctx):
    lib = _native.LIB
    cj, xj = _dumps(chain_dict), _dumps(ctx)
    nb = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * nb)()
    cap = max(nb // 2, 16384)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, nb, out, cap,
                              ctypes.byref(ol))
    return int(rc), (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_catalog_parse(schema_version, chains):
    lib = _native.LIB
    p = _dumps({"chain_schema_version": schema_version, "operator_chain": chains})
    nb = int(lib.srmech_chain_catalog_parse_arena_bytes(len(p)))
    ws = (ctypes.c_char * nb)()
    cap = 2 * len(p) + 8192
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_chain_catalog_parse(p, len(p), ws, nb, out, cap, ctypes.byref(ol))
    return int(rc), (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_dsl_chain_run(stages, input_desc, name="probe"):
    lib = _native.LIB
    cj = _dumps({"chain": {"name": name}, "stage": stages})
    ij = _dumps(input_desc)
    nb = int(lib.srmech_dsl_chain_run_arena_bytes(len(cj), len(ij)))
    ws = (ctypes.c_char * nb)()
    cap = max(nb // 2, 16384)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_dsl_chain_run(cj, len(cj), ij, len(ij), ws, nb, out, cap,
                                  ctypes.byref(ol))
    return int(rc), (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_toml_to_json(src_bytes):
    lib = _native.LIB
    nb = int(lib.srmech_dsl_toml_chain_to_json_arena_bytes(len(src_bytes)))
    ws = (ctypes.c_char * nb)()
    cap = 8 * len(src_bytes) + 65536
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = lib.srmech_dsl_toml_chain_to_json(src_bytes, len(src_bytes), ws, nb,
                                           out, cap, ctypes.byref(ol))
    return int(rc), (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def c_arena_bytes(chain_dict, ctx):
    lib = _native.LIB
    cj, xj = _dumps(chain_dict), _dumps(ctx)
    return int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj))), len(cj)


# ══════════════════════════════════════════════════════════════════════
# helpers
# ══════════════════════════════════════════════════════════════════════

def anchor(path, line_1based, want_substr, probe):
    """Re-read a source anchor and record its ACTUAL content."""
    txt = Path(path).read_text(encoding="utf-8").splitlines()
    got = txt[line_1based - 1] if 0 < line_1based <= len(txt) else "<out of range>"
    ok = want_substr in got
    return rec(record="anchor", probe=probe,
               file=str(Path(path).relative_to(_SRMECH)), line=line_1based,
               want=want_substr, got=got.strip()[:160], anchor_live=bool(ok))


def grep_count(paths, needle):
    n, hits = 0, []
    for p in paths:
        for i, ln in enumerate(Path(p).read_text(encoding="utf-8",
                                                 errors="replace").splitlines(), 1):
            if needle in ln:
                n += 1
                if len(hits) < 6:
                    hits.append("%s:%d" % (Path(p).name, i))
    return n, hits


A_HEAD = {"name": "probe", "summary": "s", "returns": "r", "on_error": "raise"}


def chain_of(steps):
    d = dict(A_HEAD)
    d["steps"] = steps
    return d


# ══════════════════════════════════════════════════════════════════════
def p0_environment():
    ns = srmech.native_status()
    rec(record="environment", probe="P0", srmech=srmech.__version__,
        has_native=bool(ns.get("has_native")), abi=ns.get("abi_version"),
        expected_abi=getattr(_native, "EXPECTED_ABI_VERSION", None),
        dispatching=bool(ns.get("dispatching")),
        lib=str(getattr(_native, "_LIB_PATH", None)))
    print("P0  srmech %s  abi=%s/%s  has_native=%s" % (
        srmech.__version__, ns.get("abi_version"),
        getattr(_native, "EXPECTED_ABI_VERSION", None), ns.get("has_native")))


def p1_adr_section5():
    """Quote-fidelity: extract ADR-0009 §5 verbatim + content hash."""
    lines = ADR.read_text(encoding="utf-8").splitlines()
    s = e = None
    for i, ln in enumerate(lines):
        if ln.startswith("## 5. "):
            s = i
        elif s is not None and ln.startswith("## 6."):
            e = i
            break
    body = "\n".join(lines[s:e]).strip()
    flat = " ".join(body.split())
    h = sha256_bytes(body.encode("utf-8"))
    hh = h.hex() if isinstance(h, (bytes, bytearray)) else str(h)
    # the three fields §5 mandates for a ledger row
    mandated = {
        "capability": "recording the capability" in flat,
        "declining_implementation": "the declining implementation" in flat,
        "boundary": "and the boundary" in flat,
        "files_a_tracked_gap": "files a tracked gap" in flat,
        "not_a_comment": "ledger row (\u00a76a)" in flat,
        "disclosure_insufficient":
            "Disclosure is necessary and is not sufficient" in flat,
        "build_lever_not_parity": "a recompile could reach" in flat,
    }
    rec(record="adr_section5", probe="P1", heading=lines[s], span_lines=[s + 1, e],
        char_len=len(body), sha256=hh, mandated_fields=mandated,
        all_mandated_present=all(mandated.values()))
    print("P1  ADR-0009 §5 extracted: %d chars, sha256=%s, mandated-fields=%s"
          % (len(body), hh[:16], all(mandated.values())))
    return body


def p2_ledger_absence():
    """§6a authorizes a capability ledger. Does one exist to file into?"""
    roots = [_PY / "srmech", _SRMECH / "c", _PY / "tests"]
    toks = ["decline_ledger", "DECLINE_LEDGER", "capability_ledger",
            "CAPABILITY_LEDGER", "parity_ledger", "PARITY_LEDGER",
            "declines.ndjson", "decline_rows"]
    hits = {}
    files = []
    for r in roots:
        for p in r.rglob("*"):
            if not p.is_file() or p.suffix not in (".py", ".c", ".h", ".ndjson",
                                                   ".md", ".toml"):
                continue
            files.append(p)
    for t in toks:
        n, where = grep_count(files, t)
        if n:
            hits[t] = where
    named = sorted(str(p.relative_to(_SRMECH)) for p in files
                   if "ledger" in p.name.lower())
    rl = _SRMECH / "c" / "ROSETTA_LEDGER.md"
    rl_txt = rl.read_text(encoding="utf-8") if rl.exists() else ""
    rl_facts = {
        "exists": rl.exists(),
        "is_down_only_debt_ledger": "down-only" in rl_txt,
        "keyed_by": ("python op bucket" if "public Python op falls in one bucket"
                     in rl_txt else "unknown"),
        "has_documented_exclusion_precedent": "IO-exclusion" in rl_txt,
        "has_do_not_mirror_gate": "Do-not-mirror gate" in rl_txt,
        "mentions_ADR_0009": "ADR-0009" in rl_txt,
        "mentions_a_c_side_decline_row": "declining implementation" in rl_txt,
    }
    rec(record="ledger_absence", probe="P2", files_scanned=len(files),
        token_hits=hits, files_named_ledger=named,
        rosetta_ledger=rl_facts,
        ledger_exists_for_declines=bool(hits))
    print("P2  ledger tokens found=%s ; files named *ledger*=%s" % (hits or "NONE", named))
    print("P2  c/ROSETTA_LEDGER.md: %s" % rl_facts)


def p3_surface_a_forms():
    """The 3 Surface-A step forms at C parse and C run."""
    plain = {"class": "N", "op": "rational_add", "args": {"a": [1, 2], "b": [1, 3]}}
    mapstep = {"map_over": "@input.xs", "index": "i", "bind": "x",
               "body": [{"class": "N", "op": "rational_add",
                         "args": {"a": "@bind.x", "b": [0, 1]}}]}
    foldstep = {"fold_class": "C", "fold_op": "srmech.cascade.leaves.orientation_compose",
                "fold_init": 1, "over": "@input.xs"}
    for form, st in (("plain", plain), ("map", mapstep), ("fold", foldstep)):
        prc, _ = c_spec_parse(chain_of([st]))
        rrc, rv = c_chain_run(chain_of([st]),
                              {"row": None, "inputs": {"xs": [1, -1]}})
        rec(record="surface_a_form", probe="P3", form=form,
            c_parse=sname(prc), c_run=sname(rrc), c_run_value=rv,
            python_has_form=True)
        print("P3  A/%-5s  parse %-12s run %-12s" % (form, sname(prc), sname(rrc)))
    for ln, want in ((299, "class"), (722, "op")):
        pass
    anchor(C_SRC / "srmech_compose.c", 299, "class", "P3.parse_required_keys")
    anchor(C_SRC / "srmech_compose_run.c", 722, "op", "P3.run_required_op")


def p4_namespaces():
    """@catalog / @idx / @bind / @op at C parse and C run vs Python's 7."""
    py_ns = CO._REFERENCE_PATTERN.pattern.split("@(")[1].split(")")[0].split("|")
    src = (C_SRC / "srmech_compose.c").read_text(encoding="utf-8")
    run = (C_SRC / "srmech_compose_run.c").read_text(encoding="utf-8")
    fn_s = src.index("co_match_namespace(const char")
    fn_body = src[fn_s:fn_s + 900]
    parse_ns = [t for t in ("row", "input", "step", "catalog", "idx", "bind", "op")
                if ('"%s"' % t) in fn_body]
    r_s = run.index("cr_resolve_ref(cr_ctx_t")
    r_body = run[r_s:r_s + 1400]
    run_ns = [t for t in ("row", "input", "step", "catalog", "idx", "bind", "op")
              if ('"%s.' % t) in r_body or ('"%s["' % t) in r_body]
    probes = {}
    for ns_tok, ref in (("input_CONTROL", "@input.a"), ("row", "@row.x"),
                        ("catalog", "@catalog.row.x"), ("idx", "@idx.i"),
                        ("bind", "@bind.x"), ("op", "@op.name")):
        st = {"class": "N", "op": "rational_add", "args": {"a": ref, "b": [1, 3]}}
        prc, _ = c_spec_parse(chain_of([st]))
        rrc, _ = c_chain_run(chain_of([st]),
                             {"row": {"x": [1, 2]}, "inputs": {"a": [1, 2], "i": 0,
                                                              "x": [1, 2], "name": "n"},
                              "catalog": {"row": {"x": [1, 2]}}})
        probes[ns_tok] = {"c_parse": sname(prc), "c_run": sname(rrc)}
        print("P4  @%-8s parse %-12s run %-12s" % (ns_tok, sname(prc), sname(rrc)))
    rec(record="namespaces", probe="P4", python_namespaces=sorted(py_ns),
        c_parse_namespaces=parse_ns, c_run_namespaces=run_ns, probes=probes)
    print("P4  python=%d %s | c_parse=%d %s | c_run=%d %s"
          % (len(py_ns), sorted(py_ns), len(parse_ns), parse_ns, len(run_ns), run_ns))


def p5_carrier_kinds():
    """cr_value_t has no float kind; cr_json_scalar refuses DOUBLE/BOOL."""
    run = (C_SRC / "srmech_compose_run.c").read_text(encoding="utf-8")
    i = run.index("} cr_kind_t;")
    kinds = run[run.rindex("typedef enum", 0, i):i]
    have_float = ("CR_FLOAT" in kinds) or ("CR_DOUBLE" in kinds)
    # arg KINDS on the same in-table op, against a working control
    cells = {}
    for tag, args in (("CONTROL_int_pair", {"a": [1, 2], "b": [1, 3]}),
                      ("null_scalar", {"a": None, "b": [1, 3]}),
                      ("float_scalar", {"a": 0.5, "b": [1, 3]}),
                      ("float_in_list", {"a": [1, 2.0], "b": [1, 3]}),
                      ("bool_scalar", {"a": True, "b": [1, 3]})):
        st = {"class": "N", "op": "rational_add", "args": args}
        prc, _ = c_spec_parse(chain_of([st]))
        rrc, rv = c_chain_run(chain_of([st]), {"row": None, "inputs": {}})
        cells[tag] = {"c_parse": sname(prc), "c_run": sname(rrc), "value": rv}
        print("P5  arg %-16s parse %-12s run %-12s value=%s"
              % (tag, sname(prc), sname(rrc), str(rv)[:40]))
    # a FLOAT arriving through the ctx (the shipped schur_complement shape)
    st = {"class": "N", "op": "rational_add", "args": {"a": "@input.f", "b": [1, 3]}}
    prc, _ = c_spec_parse(chain_of([st]))
    rrc, rv = c_chain_run(chain_of([st]), {"row": None, "inputs": {"f": 0.5}})
    cells["float_via_ctx_ref"] = {"c_parse": sname(prc), "c_run": sname(rrc),
                                  "value": rv}
    print("P5  arg %-16s parse %-12s run %-12s"
          % ("float_via_ctx_ref", sname(prc), sname(rrc)))
    # how many shipped proof-case input sets carry a float at all
    fl = {}
    for name, st8 in CC.cascade_catalog_status().items():
        if st8 != "executable":
            continue
        for v, _spec, entry in CC.cascade_chain_specs(name):
            n = 0

            def _walk(o):
                global _NF
                return None
            def count(o):
                c = 0
                if isinstance(o, float):
                    c += 1
                elif isinstance(o, dict):
                    for x in o.values():
                        c += count(x)
                elif isinstance(o, list):
                    for x in o:
                        c += count(x)
                return c
            for case in entry.get("proof_cases", []) or []:
                n += count(case.get("inputs") or {})
            n += count(entry.get("steps", []))
            if n:
                fl["%s.%s" % (name, v)] = n
    print("P5  shipped variants carrying >=1 float (steps or proof-case inputs): %d %s"
          % (len(fl), sorted(fl)[:6]))
    rec(record="carrier_kinds", probe="P5", cr_kind_t=kinds.strip().splitlines()[-2:],
        has_float_kind=bool(have_float), cells=cells,
        variants_carrying_a_float=fl,
        n_variants_carrying_a_float=len(fl),
        python_reconstruct_kinds=sorted(["i", "q", "s", "n", "l"]))
    anchor(C_SRC / "srmech_compose_run.c", 215, "SRMECH_JSON_STRING", "P5.json_scalar")
    # single-scalar attribution: isolates the CARRIER from the op's own arity
    for tag, nd in (("CONTROL_int", 5), ("float", 5.0), ("bool", True),
                    ("string_int", "5")):
        st = {"class": "N", "op": "pi_cascade_digits", "args": {"num_digits": nd}}
        prc, _ = c_spec_parse(chain_of([st]))
        rrc, rv = c_chain_run(chain_of([st]), {"row": None, "inputs": {}})
        cells["single_scalar_" + tag] = {"c_parse": sname(prc), "c_run": sname(rrc),
                                        "value": rv}
        print("P5  single-scalar num_digits %-12s parse %-12s run %-12s value=%s"
              % (tag, sname(prc), sname(rrc), str(rv)[:30]))
    # the Python side of the ABI argument: kind "f" is unknown to _reconstruct_value
    try:
        CO._reconstruct_value({"k": "f", "v": "1.5"})
        pyf = "ACCEPTED"
    except Exception as exc:                                       # noqa: BLE001
        pyf = "%s: %s" % (type(exc).__name__, exc)
    rec(record="reconstruct_float", probe="P5b", kind_f_result=pyf)
    print("P5b python _reconstruct_value({'k':'f'}) -> %s" % pyf[:90])


def p6_schema_version():
    """chain_schema_version: Python accepts (1,2); the C catalog wrappers ==1."""
    ch = {"name": "probe", "summary": "s", "returns": "r",
          "steps": [{"class": "N", "op": "rational_add",
                     "args": {"a": [1, 2], "b": [1, 3]}}]}
    r1 = c_catalog_parse(1, [ch])
    r2 = c_catalog_parse(2, [ch])
    declared = {}
    for p in sorted(CAT_DIR.glob("*.toml")):
        txt = p.read_text(encoding="utf-8")
        for ln in txt.splitlines():
            if ln.strip().startswith("chain_schema_version"):
                declared[p.stem] = ln.split("=")[1].strip()
    rec(record="schema_version", probe="P6",
        python_supported=list(CO.SUPPORTED_SCHEMA_VERSIONS),
        c_catalog_parse_v1=sname(r1[0]), c_catalog_parse_v2=sname(r2[0]),
        descriptors_declaring=declared,
        n_declaring_2=sum(1 for v in declared.values() if v == "2"))
    print("P6  catalog_parse v1=%s v2=%s ; python=%s ; descriptors declaring 2 = %d/%d"
          % (sname(r1[0]), sname(r2[0]), list(CO.SUPPORTED_SCHEMA_VERSIONS),
             sum(1 for v in declared.values() if v == "2"), len(declared)))
    anchor(C_SRC / "srmech_compose.c", 512, "chain_schema_version", "P6.parse_gate_a")
    anchor(C_SRC / "srmech_compose.c", 674, "chain_schema_version", "P6.parse_gate_b")
    anchor(C_SRC / "srmech_compose_run.c", 867, "chain_schema_version", "P6.run_gate")


def p7_toml_front_end():
    """The bare-C-host TOML reader vs the two descriptors carrying nan/inf."""
    docs = {
        "finite": b'[chain]\nname="p"\n[[stage]]\nop="cyclic_gcd"\nx=1.5\n',
        "nan": b'[chain]\nname="p"\n[[stage]]\nop="cyclic_gcd"\nx=nan\n',
        "inf": b'[chain]\nname="p"\n[[stage]]\nop="cyclic_gcd"\nx=inf\n',
    }
    probes = {}
    for k, v in docs.items():
        rc, _ = c_toml_to_json(v)
        probes[k] = sname(rc)
        print("P7  synthetic %-7s -> %s" % (k, sname(rc)))
    per_desc = {}
    for p in sorted(CAT_DIR.glob("*.toml")):
        rc, _ = c_toml_to_json(p.read_bytes())
        per_desc[p.stem] = sname(rc)
    rejected = sorted(k for k, v in per_desc.items() if not v.startswith("OK"))
    py_ok = {}
    for p in sorted(CAT_DIR.glob("*.toml")):
        try:
            import tomllib
            tomllib.loads(p.read_text(encoding="utf-8"))
            py_ok[p.stem] = "OK"
        except Exception as exc:                                   # noqa: BLE001
            py_ok[p.stem] = type(exc).__name__
    rec(record="toml_front_end", probe="P7", synthetic=probes,
        per_descriptor=per_desc, c_rejected=rejected,
        c_ok_count=sum(1 for v in per_desc.values() if v.startswith("OK")),
        total=len(per_desc),
        python_tomllib_rejected=sorted(k for k, v in py_ok.items() if v != "OK"))
    print("P7  descriptors readable by the C front end: %d/%d ; rejected=%s ; tomllib rejects=%s"
          % (sum(1 for v in per_desc.values() if v.startswith("OK")), len(per_desc),
             rejected, sorted(k for k, v in py_ok.items() if v != "OK")))


def p8_parallel_body():
    """Surface-B parallel_body: recognised then declined; the peer op exists."""
    F35 = {"k": "f", "v": -3.5}
    L_ANY = {"k": "l", "v": [{"k": "i", "v": 1}, {"k": "i", "v": 2}]}
    ctl = c_dsl_chain_run([{"loop_n": 3, "sub_chain": [{"op": "magnitude"}]}], F35)
    leaf = c_dsl_chain_run([{"op": "magnitude"}], F35)
    par = c_dsl_chain_run([{"parallel_body": "chiral_flip", "n_sectors": 4,
                            "combine": "bundle"}], L_ANY)
    hdr = C_INC.read_text(encoding="utf-8")
    lib = _native.LIB
    sym = {}
    for s in ("srmech_cascade_parallel_sector_dispatch", "srmech_plat_has_threads",
              "srmech_plat_dir_open", "srmech_plat_file_read",
              "srmech_plat_has_filesystem", "srmech_toml_parse"):
        sym[s] = {"in_header": ("%s(" % s) in hdr, "in_lib": hasattr(lib, s)}
    try:
        thr = int(lib.srmech_plat_has_threads())
    except Exception as exc:                                       # noqa: BLE001
        thr = "ERR %s" % exc
    plat_h = (C_SRC / "srmech_platform.h")
    plat_in_public_header = "srmech_plat_dir_open" in C_INC.read_text(encoding="utf-8")
    plat_in_internal_header = (plat_h.exists()
                               and "srmech_plat_dir_open" in
                               plat_h.read_text(encoding="utf-8"))
    rec(record="parallel_body", probe="P8", control_leaf=sname(leaf[0]),
        control_loop_n=sname(ctl[0]), control_loop_value=ctl[1],
        parallel_body=sname(par[0]), symbols=sym, plat_has_threads=thr,
        plat_in_public_header=plat_in_public_header,
        plat_in_internal_header=plat_in_internal_header)
    print("P8  Surface-B leaf control=%s ; loop_n control=%s (%s) ; parallel_body=%s ; threads=%s"
          % (sname(leaf[0]), sname(ctl[0]), str(ctl[1])[:30], sname(par[0]), thr))
    print("P8  srmech_plat_* in PUBLIC header=%s ; in internal src header=%s"
          % (plat_in_public_header, plat_in_internal_header))
    for s, v in sym.items():
        print("      %-42s header=%s lib=%s" % (s, v["in_header"], v["in_lib"]))
    anchor(C_SRC / "srmech_dsl_chain_run.c", 792, "SRMECH_ERR_NOT_IMPL",
           "P8.parallel_decline")


def p9_descriptor_lookup():
    """#T1143 / #T1144 both need load_catalog(); C has no descriptor loader."""
    hdr = C_INC.read_text(encoding="utf-8")
    loaderish = [ln.strip() for ln in hdr.splitlines()
                 if ("srmech_" in ln and "(" in ln
                     and any(t in ln for t in ("cascade_catalog_load", "catalog_load",
                                              "load_catalog", "descriptor_load",
                                              "catalog_open", "catalog_scan")))]
    exports = sorted({ln.split("srmech_catalog_")[1].split("(")[0]
                      for ln in hdr.splitlines() if "srmech_catalog_" in ln
                      and "(" in ln and "srmech_catalog_" in ln.split("(")[0]})
    # the Python lookup sites
    cat_src = (_PY / "srmech" / "dsl" / "_catalog.py").read_text(encoding="utf-8")
    t1143 = "isinstance(desc.get(\"composite\"), dict)" in cat_src
    t1144 = "catalog = load_catalog()" in cat_src
    composite_keys = tuple(getattr(DCAT, "_COMPOSITE_OP_KEYS", ()))
    rec(record="descriptor_lookup", probe="P9",
        header_descriptor_loader_symbols=loaderish,
        srmech_catalog_exports=exports,
        python_t1143_site=t1143, python_t1144_site=t1144,
        composite_op_keys=list(composite_keys),
        map_op_in_composite_keys=("map_op" in composite_keys))
    print("P9  C header descriptor-directory loaders: %s" % (loaderish or "NONE"))
    print("P9  srmech_catalog_* exports: %s" % exports)
    print("P9  _COMPOSITE_OP_KEYS=%s ; map_op present=%s"
          % (list(composite_keys), "map_op" in composite_keys))
    anchor(C_INC, 3178, "caller-owned", "P9.state_model")


def p10_op_tables():
    """cr_dispatch's table vs the ops the 18 executable descriptors name."""
    run_ops = sorted(CO._RUN_C_OPS)
    status = CC.cascade_catalog_status()
    executable = sorted(n for n, s in status.items() if s == "executable")
    used = set()
    per_desc = {}

    def walk(steps, acc):
        for st in steps or []:
            if isinstance(st, dict):
                if "op" in st and isinstance(st["op"], str):
                    acc.add(st["op"])
                if "fold_op" in st and isinstance(st["fold_op"], str):
                    acc.add(st["fold_op"])
                if isinstance(st.get("body"), list):
                    walk(st["body"], acc)
    for name in executable:
        acc = set()
        for _v, spec, entry in CC.cascade_chain_specs(name):
            walk(entry.get("steps", []), acc)
        per_desc[name] = sorted(acc)
        used |= acc
    outside = sorted(o for o in used if o.split(".")[-1] not in run_ops
                     and o not in run_ops)
    # rosetta bucket for the bare tail of each op
    led = _PY / "tests" / "rosetta_classification.ndjson"
    buckets = {}
    if led.exists():
        for ln in led.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            row = json.loads(ln)
            key = str(row.get("exposed_as") or row.get("defined_at") or "")
            buckets[key.split(".")[-1]] = row.get("bucket") or row.get("class")
    have_c = sorted(o for o in used if buckets.get(o.split(".")[-1]) == "c_dispatched")
    rec(record="op_tables", probe="P10", c_run_table=run_ops,
        c_run_table_size=len(run_ops), distinct_ops_used=len(used),
        ops_outside_table=len(outside),
        ops_with_c_dispatched_row=len(have_c),
        ops_outside_and_c_dispatched=sorted(set(outside) & set(have_c)),
        executable_descriptors=len(executable))
    print("P10 cr_dispatch table=%d ; distinct ops used=%d ; outside=%d ; of those c_dispatched=%d"
          % (len(run_ops), len(used), len(outside), len(set(outside) & set(have_c))))


def p11_arena_demand():
    """The static arena the C run peer demands per shipped chain."""
    status = CC.cascade_catalog_status()
    executable = sorted(n for n, s in status.items() if s == "executable")
    rows = []
    for name in executable:
        for v, _spec, entry in CC.cascade_chain_specs(name):
            cd = {"name": "%s.%s" % (name, v), "summary": str(entry.get("summary", "")),
                  "returns": str(entry.get("returns", "")), "on_error": "raise",
                  "steps": entry.get("steps", [])}
            nb, cj = c_arena_bytes(cd, {})
            rows.append((cd["name"], cj, nb))
    rows.sort(key=lambda r: r[2])
    rec(record="arena_demand", probe="P11", n_variants=len(rows),
        min_bytes=rows[0][2], min_name=rows[0][0],
        max_bytes=rows[-1][2], max_name=rows[-1][0],
        formula="128*chain_len + 128*ctx_len + 65536 + 4096*chain_len + 1MiB + writer",
        top5=[{"variant": n, "chain_json_bytes": c, "arena_bytes": b}
              for n, c, b in rows[-5:]])
    print("P11 arena demand over %d variants: min %s = %.2f MB ; max %s = %.2f MB"
          % (len(rows), rows[0][0], rows[0][2] / 1048576.0,
             rows[-1][0], rows[-1][2] / 1048576.0))


def p12_reverse_direction():
    """Does the COMPILED projection hold anything the SCRIPTING one lacks?"""
    dsl_names = sorted(DCAT.load_catalog())
    src = (C_SRC / "srmech_dsl_chain_run.c").read_text(encoding="utf-8")
    # the C map-body recogniser
    i = src.index("dsl_map_body_is_seq_get")
    body = src[i:i + 500]
    import srmech.cascade as CASC
    seq_get_py = {
        "in_dsl_catalog": "seq_get" in dsl_names,
        "attr_on_srmech_cascade": hasattr(CASC, "seq_get"),
        "c_recogniser_present": "seq_get" in body,
    }
    from srmech.dsl import _catalog as _DC
    try:
        _DC.lookup_cascade_op("seq_get")
        lookup = "RESOLVES"
    except Exception as exc:                                       # noqa: BLE001
        lookup = "%s: %s" % (type(exc).__name__, str(exc)[:70])
    seq_get_py["dsl_lookup_cascade_op"] = lookup
    seq_get_py["reading"] = (
        "NOT a compiled-only capability: srmech.cascade.seq_get exists in Python. "
        "The asymmetry is REGISTRATION — the C map-body recogniser names it while "
        "the DSL catalog does not, so the two projections disagree on whether the "
        "NAME is addressable, not on whether the capability exists.")
    rec(record="reverse_direction", probe="P12", seq_get=seq_get_py,
        dsl_catalog_size=len(dsl_names))
    print("P12 dsl lookup_cascade_op('seq_get') -> %s" % lookup)
    print("P12 seq_get: C recogniser=%s ; python dsl catalog=%s ; srmech.cascade attr=%s"
          % (seq_get_py["c_recogniser_present"], seq_get_py["in_dsl_catalog"],
             seq_get_py["attr_on_srmech_cascade"]))


def p13_t1146_is_a_bug():
    """The silent-accept divergence: C RETURNS a value where Python RAISES."""
    cells = []
    for op, val, kw in (("magnitude", -3.5, {"bogus": 1}),
                        ("reorient", 5, {"orientation": -1, "bogus": 1}),
                        ("net_chirality", [1, -1, 1], {"bogus": 1})):
        try:
            nv = dsl_chain().then(op, **kw).run(val)
            n = ("ACCEPTED", repr(nv))
        except Exception as exc:                                   # noqa: BLE001
            n = ("REJECTED", "%s: %s" % (type(exc).__name__, exc))
        import srmech.cascade as CASC
        try:
            pv = getattr(CASC, op)(val, **kw)
            p = ("ACCEPTED", repr(pv))
        except Exception as exc:                                   # noqa: BLE001
            p = ("REJECTED", "%s: %s" % (type(exc).__name__, exc))
        cells.append({"op": op, "kwargs": sorted(kw), "native": n[0],
                      "native_value": n[1][:80], "pure": p[0],
                      "pure_value": p[1][:80],
                      "verdict": ("BUG_silent_accept" if n[0] == "ACCEPTED"
                                  and p[0] == "REJECTED" else "parity")})
        print("P13 %-14s native=%-8s pure=%-8s -> %s"
              % (op, n[0], p[0], cells[-1]["verdict"]))
    rec(record="t1146_bug", probe="P13", cells=cells,
        is_a_decline=False,
        why_not_a_decline=("nothing declines: the compiled path ACCEPTS an input the "
                           "scripting path REFUSES and returns a value, so §5's "
                           "'clean decline' predicate is not satisfied in either "
                           "direction"))


def p14_c_claims_state():
    """The pre-existing ADR-0009 §6(b) partial step, re-counted at rc444."""
    try:
        from srmech.introspect import _c_claims as CL
        unv = getattr(CL, "UNVERIFIABLE_CLAIMS", ())
        claims = getattr(CL, "C_CLAIMS", {}) or getattr(CL, "CLAIMS", {})
        rec(record="c_claims", probe="P14", unverifiable=len(unv),
            claim_rows=len(claims))
        print("P14 _c_claims: %d claim rows, %d UNVERIFIABLE" % (len(claims), len(unv)))
    except Exception as exc:                                       # noqa: BLE001
        rec(record="c_claims", probe="P14", error="%s: %s" % (type(exc).__name__, exc))
        print("P14 _c_claims: %s" % exc)


def p15_routing_gate():
    """The Python-side routing gate that makes any C widening unreachable."""
    src = (_PY / "srmech" / "cascade" / "compose.py").read_text(encoding="utf-8")
    i = src.index("def _chain_c_eligible")
    body = src[i:i + 1200]
    rec(record="routing_gate", probe="P15",
        requires_class_N=('class_id != "N"' in body or 'class_id == "N"' in body),
        requires_run_c_ops=("_RUN_C_OPS" in body),
        isinstance_guard=("isinstance" in body),
        excerpt=[ln.strip() for ln in body.splitlines()[:18] if ln.strip()][:12])
    print("P15 _chain_c_eligible: class-N gate=%s ; _RUN_C_OPS gate=%s ; isinstance guard=%s"
          % ('class_id != "N"' in body, "_RUN_C_OPS" in body, "isinstance" in body))


def p16_body_ops_and_bounds():
    """The map/fold BODY ops the descriptors name, and the shipped map bounds."""
    hdr = C_INC.read_text(encoding="utf-8")
    dslsrc = (C_SRC / "srmech_dsl_chain_run.c").read_text(encoding="utf-8")
    status = CC.cascade_catalog_status()
    executable = sorted(n for n, s2 in status.items() if s2 == "executable")
    body_ops, depth_max, body_len_max, binds_max = set(), 0, 0, 0

    def walk(steps, depth):
        nonlocal depth_max, body_len_max, binds_max
        for st in steps or []:
            if not isinstance(st, dict):
                continue
            if isinstance(st.get("body"), list):
                depth_max = max(depth_max, depth + 1)
                body_len_max = max(body_len_max, len(st["body"]))
                if st.get("bind"):
                    binds_max = max(binds_max, 1)
                for b in st["body"]:
                    if isinstance(b, dict) and isinstance(b.get("op"), str):
                        body_ops.add(b["op"])
                walk(st["body"], depth + 1)
            if isinstance(st.get("fold_op"), str):
                body_ops.add(st["fold_op"])
    for name in executable:
        for _v, _spec, entry in CC.cascade_chain_specs(name):
            walk(entry.get("steps", []), 0)
    have_sym = {}
    for op in sorted(body_ops):
        tail = op.split(".")[-1]
        cands = ["srmech_%s(" % tail, "srmech_cascade_%s(" % tail,
                 "srmech_vec_%s(" % tail, "srmech_mod_%s(" % tail,
                 "srmech_rational_%s(" % tail, "srmech_mat_%s(" % tail]
        have_sym[op] = next((c[:-1] for c in cands if c in hdr), None)
    covered = sorted(o for o, v in have_sym.items() if v)
    # Surface-B kernel coverage: which catalog names any C DSL table names
    cat = sorted(DCAT.load_catalog())
    dsl_covered = sorted(n for n in cat if ('"%s"' % n) in dslsrc)
    exec_covered = sorted(n for n in executable if ('"%s"' % n) in dslsrc)
    rec(record="body_ops_and_bounds", probe="P16",
        distinct_body_ops=len(body_ops), body_ops=sorted(body_ops),
        body_ops_with_a_c_symbol=covered, n_with_symbol=len(covered),
        n_without_symbol=len(body_ops) - len(covered),
        shipped_map_max_nesting_depth=depth_max,
        shipped_map_max_body_len=body_len_max,
        surfaceB_catalog_names_in_c_tables=dsl_covered,
        surfaceB_executable_in_c_tables=exec_covered,
        catalog_total=len(cat), executable_total=len(executable))
    print("P16 map/fold body ops: %d distinct ; %d have a C symbol, %d do NOT"
          % (len(body_ops), len(covered), len(body_ops) - len(covered)))
    print("P16 shipped map bounds: max nesting depth=%d ; max body length=%d"
          % (depth_max, body_len_max))
    print("P16 Surface-B: %d of %d catalog names appear in the C DSL tables ; "
          "%d of %d executable" % (len(dsl_covered), len(cat),
                                   len(exec_covered), len(executable)))


def p17_arena_decline_is_clean():
    """§5 requires the decline be CLEAN. Measure it under an undersized arena."""
    cd = {"name": "p", "summary": "s", "returns": "r", "on_error": "raise",
          "steps": [{"class": "N", "op": "rational_add",
                     "args": {"a": [1, 2], "b": [1, 3]}}]}
    cj, xj = _dumps(cd), _dumps({"row": None, "inputs": {}})
    lib = _native.LIB
    full = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    rows = []
    for frac in (1.0, 0.5, 0.1, 0.01, 0.001):
        nb = max(int(full * frac), 64)
        ws = (ctypes.c_char * nb)()
        out = (ctypes.c_char * 16384)()
        ol = ctypes.c_size_t()
        rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, nb, out,
                                     16384, ctypes.byref(ol)))
        rows.append({"ws_bytes": nb, "fraction_of_demand": frac,
                     "status": sname(rc), "out": out.raw[:ol.value].decode("utf-8")})
        print("P17 ws=%9d (%.3f of demand) -> %-12s %s"
              % (nb, frac, sname(rc), rows[-1]["out"][:34]))
    rec(record="arena_decline", probe="P17", demanded_bytes=full, cells=rows,
        decline_is_clean=all(r["status"] in ("OK=0", "OVERFLOW=4") for r in rows),
        headroom_note=("the demand is a generous static over-approximation: the "
                       "control chain still ran at 0.10 of it"))


def p18_residual_matrix():
    """Per-variant residual: what still blocks each shipped chain, by feature."""
    status = CC.cascade_catalog_status()
    executable = sorted(n for n, s2 in status.items() if s2 == "executable")
    run_ops = set(CO._RUN_C_OPS)
    rows = []
    for name in executable:
        for v, _spec, entry in CC.cascade_chain_specs(name):
            steps = entry.get("steps", [])
            feats = {"map": 0, "fold": 0, "ns_idx": 0, "ns_bind": 0, "ns_op": 0,
                     "ns_catalog": 0, "float": 0, "ops_outside": 0}

            def scan(o):
                if isinstance(o, float):
                    feats["float"] += 1
                elif isinstance(o, str) and o.startswith("@"):
                    tok = o[1:].split(".")[0].split("[")[0]
                    if tok in ("idx", "bind", "op", "catalog"):
                        feats["ns_" + tok] += 1
                elif isinstance(o, dict):
                    for k2, x in o.items():
                        scan(x)
                elif isinstance(o, list):
                    for x in o:
                        scan(x)

            def walk(sl):
                for st in sl or []:
                    if not isinstance(st, dict):
                        continue
                    if "map_over" in st:
                        feats["map"] += 1
                    if "fold_op" in st or "fold_class" in st:
                        feats["fold"] += 1
                    op = st.get("op") or st.get("fold_op")
                    if isinstance(op, str) and op.split(".")[-1] not in run_ops:
                        feats["ops_outside"] += 1
                    scan(st)
                    if isinstance(st.get("body"), list):
                        walk(st["body"])
            walk(steps)
            for case in entry.get("proof_cases", []) or []:
                scan(case.get("inputs") or {})
            cd = {"name": "%s.%s" % (name, v),
                  "summary": str(entry.get("summary", "")),
                  "returns": str(entry.get("returns", "")),
                  "on_error": "raise", "steps": steps}
            prc, _ = c_spec_parse(cd)
            rrc, _ = c_chain_run(cd, {"row": None, "inputs": {}})
            rows.append({"variant": cd["name"], "c_parse": sname(prc),
                         "c_run": sname(rrc), **feats})
    acc = [r for r in rows if r["c_parse"] == "OK=0"]
    only_table = [r for r in acc if r["map"] == 0 and r["fold"] == 0
                  and r["float"] == 0 and r["ns_idx"] == 0 and r["ns_bind"] == 0
                  and r["ns_op"] == 0]
    acc_with_float = [r for r in acc if r["float"] > 0]
    rec(record="residual_matrix", probe="P18", variants=len(rows),
        parse_accept=len(acc), parse_reject=len(rows) - len(acc),
        run_accept=sum(1 for r in rows if r["c_run"] == "OK=0"),
        parse_accepting=[r["variant"] for r in acc],
        parse_accepting_with_a_float=[r["variant"] for r in acc_with_float],
        op_table_is_the_only_blocker=[r["variant"] for r in only_table],
        rows=rows)
    print("P18 variants=%d ; parse ACCEPT=%d REJECT=%d ; run ACCEPT=%d"
          % (len(rows), len(acc), len(rows) - len(acc),
             sum(1 for r in rows if r["c_run"] == "OK=0")))
    print("P18 parse-accepting whose ONLY blocker is the op table: %d %s"
          % (len(only_table), [r["variant"] for r in only_table]))
    print("P18 parse-accepting that ALSO carry a float: %d %s"
          % (len(acc_with_float), [r["variant"] for r in acc_with_float]))


def main():
    print("=" * 78)
    print("ADR-0009 §5 decline-list verification — gh #1653 round 2")
    print("=" * 78)
    p0_environment()
    p1_adr_section5()
    p2_ledger_absence()
    p3_surface_a_forms()
    p4_namespaces()
    p5_carrier_kinds()
    p6_schema_version()
    p7_toml_front_end()
    p8_parallel_body()
    p9_descriptor_lookup()
    p10_op_tables()
    p11_arena_demand()
    p12_reverse_direction()
    p13_t1146_is_a_bug()
    p14_c_claims_state()
    p15_routing_gate()
    p16_body_ops_and_bounds()
    p17_arena_decline_is_clean()
    p18_residual_matrix()
    stale = [r for r in RECS if r.get("record") == "anchor"
             and not r.get("anchor_live")]
    rec(record="summary", probe="PZ", records=len(RECS),
        stale_anchors=[(r["file"], r["line"], r["probe"]) for r in stale],
        stale_anchor_count=len(stale))
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in RECS:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    print("-" * 78)
    print("STALE ANCHORS: %d %s" % (len(stale),
                                    [(r["file"], r["line"]) for r in stale]))
    print("wrote %s (%d records)" % (OUT, len(RECS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
