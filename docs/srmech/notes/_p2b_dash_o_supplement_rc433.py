"""`#T1131` P2b — the input classes the SHIPPED tests do NOT cover.

P2 probed each site with the exact input its pinning test uses. This supplement
probes the NEIGHBOURING input classes in the same domain, because the rc431
``vec_add`` lesson is that a defect can be ASYMMETRIC: one orientation of a
length mismatch returned a silently truncated answer while the other leaked a
bare ``IndexError``, so a guard written against the noisy orientation would have
left the corrupting one intact.

Each row is executed in a fresh ``-O`` subprocess and its observable result is
recorded verbatim. No prediction is scored here — P2 carries the pre-registered
falsifiers; this file is the domain SWEEP around them.

Discipline: srmech ops only; no ``abs()``, no stdlib ``math``/``fractions``/
``decimal``, no numpy.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

PYPATH = "/mnt/d/GitHub/mlehaptics/docs/srmech/python"
OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p2b_dash_o_supplement_rc433.ndjson"

CASES = [
    dict(
        cid="mat_from_rows_long_first",
        op="srmech.math.mat.Mat.from_rows",
        note="ragged, LONG row first — the orientation the shipped test uses",
        body="""
from srmech.math.mat import Mat
try:
    m = Mat.from_rows([[1.0, 2.0], [3.0]])
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
else:
    try:
        tl = m.tolist()
    except BaseException as e:
        tl = "%s: %s" % (type(e).__name__, e)
    _out({"shape": list(m.shape), "buflen": len(m.buffer), "tolist": tl})
""",
    ),
    dict(
        cid="mat_from_rows_short_first",
        op="srmech.math.mat.Mat.from_rows",
        note="ragged, SHORT row first — the UNTESTED orientation",
        body="""
from srmech.math.mat import Mat
try:
    m = Mat.from_rows([[1.0], [2.0, 3.0]])
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
else:
    try:
        tl = m.tolist()
    except BaseException as e:
        tl = "%s: %s" % (type(e).__name__, e)
    flat = [x for r in (tl if isinstance(tl, list) else []) for x in r]
    _out({"shape": list(m.shape), "buflen": len(m.buffer), "tolist": tl,
          "dropped_value": 3.0 not in flat})
""",
    ),
    dict(
        cid="vec_getitem_neg_oor_complex",
        op="srmech.math.vec.Vec.__getitem__",
        note="complex Vec, index < -n — returns a WRONG element, no error",
        body="""
from srmech.math.vec import Vec
v = Vec.from_sequence([1 + 1j, 2 + 2j, 3 + 3j])
try:
    got = v[-5]
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
else:
    _out({"v_minus_5": str(got), "equals_v1": str(got) == str(v[1]),
          "n": 3, "asked_for": -5})
""",
    ),
    dict(
        cid="register_catalog_dir_alone",
        op="srmech.dsl.register_catalog_dir",
        note="registration ALONE (no catalog load) — does it mutate global state?",
        body="""
from srmech import dsl
from srmech.dsl import _catalog
try:
    dsl.register_catalog_dir("/nonexistent/t1131/probe")
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
else:
    _out({"returned_cleanly": True,
          "user_catalog_dirs": [str(p) for p in _catalog._USER_CATALOG_DIRS]})
""",
    ),
    dict(
        cid="register_catalog_dir_then_load",
        op="srmech.dsl.load_catalog",
        note="the DEFERRED rejection — how far downstream does it surface?",
        body="""
from srmech import dsl
try:
    dsl.register_catalog_dir("/nonexistent/t1131/probe")
except BaseException as e:
    _out({"raised_at_registration": type(e).__name__, "msg": str(e)[:160]})
else:
    try:
        dsl.list_cascade_ops()
        _out({"registration_ok": True, "deferred_raise": None})
    except BaseException as e:
        _out({"registration_ok": True, "deferred_raise": type(e).__name__,
              "msg": str(e)[:200]})
""",
    ),
    dict(
        cid="operator_norm_genuine_1d",
        op="srmech.physics.qm.bell.operator_norm",
        note="a GENUINE 1-D iterable of scalars (ndim==1, yields floats)",
        body="""
from srmech.physics.qm import bell
class R1:
    ndim = 1
    def __iter__(self): return iter([1.0, 2.0, 3.0])
try:
    _out({"returned": bell.operator_norm(R1())})
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
""",
    ),
    dict(
        cid="operator_norm_lying_ndim",
        op="srmech.physics.qm.bell.operator_norm",
        note="an object that LIES about ndim while yielding 2-D rows",
        body="""
from srmech.physics.qm import bell
class L2:
    ndim = 1
    def __iter__(self): return iter([[1.0, 0.0], [0.0, 1.0]])
try:
    _out({"returned": bell.operator_norm(L2())})
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
""",
    ),
    dict(
        cid="loop_bind_hd_unequal_both_multiples",
        op="srmech.math.hdc.loop_bind_hd",
        note="both operands multiples of 8 but UNEQUAL (the equal-length assert)",
        body="""
from srmech.math import hdc
a = [1.0] + [0.0] * 55
b = a[:48]
try:
    out = hdc.loop_bind_hd(a, b)
    _out({"returned_len": len(out), "a_len": 56, "b_len": 48})
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
""",
    ),
    dict(
        cid="loop_unbind_hd_unequal_both_multiples",
        op="srmech.math.hdc.loop_unbind_hd",
        note="both operands multiples of 8 but UNEQUAL",
        body="""
from srmech.math import hdc
a = [1.0] + [0.0] * 55
b = a[:48]
try:
    out = hdc.loop_unbind_hd(a, b)
    _out({"returned_len": len(out), "a_len": 56, "b_len": 48})
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
""",
    ),
    dict(
        cid="loop_inv_single_zero_vector",
        op="srmech.math.hdc.loop_inv",
        note="the single-element peer of the zero-block guard",
        body="""
from srmech.math import hdc
try:
    _out({"returned": hdc.loop_inv([0.0] * 8)})
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
""",
    ),
    dict(
        cid="mat_matmul_mat_and_list",
        op="srmech.math.laplacian.mat_matmul",
        note="ONE Mat and one plain list — the mixed orientation",
        body="""
from srmech.math.laplacian import mat_matmul
from srmech.math.mat import Mat
A = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
try:
    out = mat_matmul(A, [[1.0, 0.0], [0.0, 1.0]])
    _out({"returned": str(out)[:120]})
except BaseException as e:
    _out({"raised": type(e).__name__, "msg": str(e)[:160]})
""",
    ),
]

_PRE = """
import json
def _out(d):
    print("@@R@@" + json.dumps(d, sort_keys=True, default=str))
"""


def run(body, optimize):
    env = dict(os.environ)
    env["PYTHONPATH"] = PYPATH
    env.pop("PYTHONOPTIMIZE", None)
    cmd = [sys.executable] + (["-O"] if optimize else []) + ["-c", _PRE + body]
    p = subprocess.run(cmd, cwd=PYPATH, env=env, capture_output=True,
                       text=True, timeout=300)
    for ln in p.stdout.splitlines():
        if ln.startswith("@@R@@"):
            return json.loads(ln[5:])
    return {"harness_error": {"rc": p.returncode, "stderr": p.stderr[-500:]}}


def main():
    recs = []
    for c in CASES:
        d = run(c["body"], False)
        o = run(c["body"], True)
        rec = {"case_id": c["cid"], "op": c["op"], "note": c["note"],
               "default_mode": d, "optimized_mode": o,
               "modes_agree": d == o}
        recs.append(rec)
        print("== %s (%s)" % (c["cid"], "AGREE" if d == o else "DIVERGE"))
        print("   default: %s" % json.dumps(d, sort_keys=True)[:230])
        print("   -O     : %s" % json.dumps(o, sort_keys=True)[:230])
        sys.stdout.flush()
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "supplement_meta", "n_cases": len(recs),
                             "python": sys.version.split()[0]},
                            sort_keys=True) + "\n")
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
