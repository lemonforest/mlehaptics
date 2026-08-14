"""`#T1131` P2 — what each op ACTUALLY DOES under ``python -O``, executed.

Every probe runs the SHIPPED op on the SAME bad input the pinning test uses, once
in DEFAULT mode and once under ``-O``, each in a FRESH subprocess (``-O`` cannot be
toggled in-process — ``assert`` is erased at COMPILE time, so a module already
imported keeps whatever it was compiled with).

Outcome vocabulary, in descending severity (the brief's):

  1 SILENT_WRONG   — ``-O`` returns a value built from invalid input.
  2 CRASH_LATER    — ``-O`` raises, but a DIFFERENT exception, at some distance.
  3 CORRECT_REJECT — a real ``raise`` below the assert already covers the input,
                     so ``-O`` rejects it for the right reason.
  4 INVARIANT      — the two modes agree (neither rejects, or both reject
                     identically); the assert was not load-bearing for this input.

PRE-REGISTERED PREDICTIONS live in ``PROBES`` as ``predict=``. They are written
before the run and compared to the measured outcome, so a probe that cannot
surprise us is visible as such. A prediction MISS is the interesting result.

Discipline: srmech ops only; no ``abs()``, no stdlib ``math``/``fractions``/
``decimal``, no numpy. Sign handling where needed is Class-K pin-slot + Class-C
re-application via ``srmech.cascade``.

Run (WSL2, numpy ABSENT):
  PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python \
    python3 docs/srmech/notes/_p2_dash_o_probe_rc433.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

PYPATH = "/mnt/d/GitHub/mlehaptics/docs/srmech/python"
OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p2_dash_o_probe_rc433.ndjson"

# --------------------------------------------------------------------------
# The probe bodies. Each prints ONE json line: {"kind": ..., "detail": ...}
# "kind" is "returned" or "raised".
# --------------------------------------------------------------------------

_PREAMBLE = """
import json, sys
def _emit(kind, detail):
    print("@@RESULT@@" + json.dumps({"kind": kind, "detail": detail}, sort_keys=True))
def _run(fn):
    try:
        v = fn()
    except BaseException as exc:
        _emit("raised", {"type": type(exc).__name__, "msg": str(exc)[:400]})
        return
    _emit("returned", v)
"""

PROBES = [
    # ---- test_mat_carrier_rc69.py:72 — Mat.from_rows ragged ----------------
    dict(
        pid="mat_from_rows_ragged",
        site="tests/test_mat_carrier_rc69.py:72",
        op="srmech.math.mat.Mat.from_rows",
        input_class="ragged list-of-rows (row lengths differ)",
        predict=1,
        body="""
from srmech.math.mat import Mat
def go():
    m = Mat.from_rows([[1.0, 2.0], [3.0]])
    return {"shape": list(m.shape), "buflen": len(m.buffer),
            "tolist_ok": _tolist(m), "n_rows*n_cols": m.n_rows * m.n_cols}
def _tolist(m):
    try:
        return m.tolist()
    except BaseException as exc:
        return "tolist raised " + type(exc).__name__ + ": " + str(exc)[:120]
_run(go)
""",
    ),
    # ---- test_vec_carrier_rc129.py:90 — Vec[i] out of range (POSITIVE) -----
    dict(
        pid="vec_getitem_pos_oor",
        site="tests/test_vec_carrier_rc129.py:90",
        op="srmech.math.vec.Vec.__getitem__",
        input_class="index >= n (the input class the test uses)",
        predict=2,
        body="""
from srmech.math.vec import Vec
v = Vec.from_sequence([10.0, 20.0, 30.0])
_run(lambda: v[3])
""",
    ),
    # ---- the SAME op, the input class the test does NOT use ----------------
    dict(
        pid="vec_getitem_neg_oor",
        site="tests/test_vec_carrier_rc129.py:90 (input class NOT covered)",
        op="srmech.math.vec.Vec.__getitem__",
        input_class="index < -n (out-of-range NEGATIVE) — untested class",
        predict=1,
        body="""
from srmech.math.vec import Vec
v = Vec.from_sequence([10.0, 20.0, 30.0])
_run(lambda: v[-5])
""",
    ),
    dict(
        pid="vec_getitem_neg_oor_complex",
        site="tests/test_vec_carrier_rc129.py:90 (input class NOT covered)",
        op="srmech.math.vec.Vec.__getitem__",
        input_class="complex Vec, index < -n — untested class",
        predict=1,
        body="""
from srmech.math.vec import Vec
v = Vec.from_sequence([1 + 1j, 2 + 2j, 3 + 3j])
_run(lambda: v[-5])
""",
    ),
    # ---- test_loop_bind_hd.py:115 / :117 — _as_hd non-multiple-of-8 --------
    dict(
        pid="loop_bind_hd_bad_len",
        site="tests/test_loop_bind_hd.py:115",
        op="srmech.math.hdc.loop_bind_hd",
        input_class="length 25 (not a positive multiple of 8)",
        predict=1,
        body="""
from srmech.math import hdc
bad = [1.0] * 25
def go():
    out = hdc.loop_bind_hd(bad, bad)
    return {"in_len": len(bad), "out_len": len(out), "truncated": len(bad) - len(out)}
_run(go)
""",
    ),
    dict(
        pid="loop_unbind_hd_bad_len",
        site="tests/test_loop_bind_hd.py:117",
        op="srmech.math.hdc.loop_unbind_hd",
        input_class="length 25 (not a positive multiple of 8)",
        predict=1,
        body="""
from srmech.math import hdc
bad = [1.0] * 25
def go():
    out = hdc.loop_unbind_hd(bad, bad)
    return {"in_len": len(bad), "out_len": len(out), "truncated": len(bad) - len(out)}
_run(go)
""",
    ),
    dict(
        pid="loop_bind_hd_empty",
        site="tests/test_loop_bind_hd.py:115 (input class NOT covered)",
        op="srmech.math.hdc.loop_bind_hd",
        input_class="EMPTY sequence — the `n and` half of the assert",
        predict=1,
        body="""
from srmech.math import hdc
def go():
    out = hdc.loop_bind_hd([], [])
    return {"out": out, "out_len": len(out)}
_run(go)
""",
    ),
    # ---- test_loop_hd_division.py:186 — loop_conj_hd / loop_inv_hd --------
    dict(
        pid="loop_conj_hd_bad_len",
        site="tests/test_loop_hd_division.py:186",
        op="srmech.math.hdc.loop_conj_hd",
        input_class="length 25 (not a positive multiple of 8)",
        predict=1,
        body="""
from srmech.math import hdc
bad = [1.0] * 25
def go():
    out = hdc.loop_conj_hd(bad)
    return {"in_len": 25, "out_len": len(out), "truncated": 25 - len(out)}
_run(go)
""",
    ),
    dict(
        pid="loop_inv_hd_bad_len",
        site="tests/test_loop_hd_division.py:186",
        op="srmech.math.hdc.loop_inv_hd",
        input_class="length 25 (not a positive multiple of 8)",
        predict=1,
        body="""
from srmech.math import hdc
bad = [1.0] * 25
def go():
    out = hdc.loop_inv_hd(bad)
    return {"in_len": 25, "out_len": len(out), "truncated": 25 - len(out)}
_run(go)
""",
    ),
    # ---- test_loop_hd_division.py:192 / :195 — loop_runbind_hd -------------
    dict(
        pid="loop_runbind_hd_bad_len",
        site="tests/test_loop_hd_division.py:192",
        op="srmech.math.hdc.loop_runbind_hd",
        input_class="length 25 (not a positive multiple of 8)",
        predict=1,
        body="""
from srmech.math import hdc
bad = [1.0] * 25
def go():
    out = hdc.loop_runbind_hd(bad, bad)
    return {"in_len": 25, "out_len": len(out), "truncated": 25 - len(out)}
_run(go)
""",
    ),
    dict(
        pid="loop_runbind_hd_unequal",
        site="tests/test_loop_hd_division.py:195",
        op="srmech.math.hdc.loop_runbind_hd",
        input_class="both multiples of 8 but UNEQUAL length (56 vs 48)",
        predict=2,
        body="""
from srmech.math import hdc
a = [1.0] + [0.0] * 55          # 56 = 7 blocks
b = a[:48]                      # 48 = 6 blocks
def go():
    out = hdc.loop_runbind_hd(a, b)
    return {"out_len": len(out)}
_run(go)
""",
    ),
    # ---- test_loop_hd_native_parity.py:178 — loop_inv_hd zero block --------
    dict(
        pid="loop_inv_hd_zero_block",
        site="tests/test_loop_hd_native_parity.py:178",
        op="srmech.math.hdc.loop_inv_hd",
        input_class="a whole 8-block of zeros (no Moufang inverse)",
        predict=3,
        body="""
from srmech.math import hdc
x = ([1.0] + [0.0] * 7) + ([0.0] * 8) + ([1.0] + [0.0] * 7)   # 24 = 3 blocks, mid zero
def go():
    out = hdc.loop_inv_hd(x)
    return {"out_len": len(out), "mid_block": out[8:16]}
_run(go)
""",
    ),
    # ---- test_bell_chsh.py:334 — operator_norm non-square ------------------
    dict(
        pid="operator_norm_non_square",
        site="tests/test_bell_chsh.py:334",
        op="srmech.physics.qm.bell.operator_norm",
        input_class="a 3x4 (non-square) Mat",
        predict=2,
        body="""
from srmech.math.mat import Mat
from srmech.physics.qm import bell
m = Mat.from_rows([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], is_complex=True)
_run(lambda: bell.operator_norm(m))
""",
    ),
    dict(
        pid="operator_norm_non_square_nonzero",
        site="tests/test_bell_chsh.py:334 (input class NOT covered: nonzero entries)",
        op="srmech.physics.qm.bell.operator_norm",
        input_class="a 2x3 non-square Mat with NONZERO entries",
        predict=1,
        body="""
from srmech.math.mat import Mat
from srmech.physics.qm import bell
m = Mat.from_rows([[1, 2, 3], [4, 5, 6]], is_complex=True)
_run(lambda: bell.operator_norm(m))
""",
    ),
    # ---- test_bell_chsh.py:344 — operator_norm non-2D ---------------------
    dict(
        pid="operator_norm_non_2d",
        site="tests/test_bell_chsh.py:344",
        op="srmech.physics.qm.bell.operator_norm",
        input_class="an object carrying ndim == 1",
        predict=3,
        body="""
from srmech.physics.qm import bell
class _Fake1D:
    ndim = 1
_run(lambda: bell.operator_norm(_Fake1D()))
""",
    ),
    dict(
        pid="operator_norm_non_2d_iterable",
        site="tests/test_bell_chsh.py:344 (input class NOT covered: ITERABLE ndim==1)",
        op="srmech.physics.qm.bell.operator_norm",
        input_class="an ITERABLE object carrying ndim == 1 (a 1-D array-like)",
        predict=1,
        body="""
from srmech.physics.qm import bell
class _Real1D:
    ndim = 1
    def __init__(self, xs): self._xs = list(xs)
    def __iter__(self): return iter(self._xs)
_run(lambda: bell.operator_norm(_Real1D([[1.0, 0.0], [0.0, 1.0]])))
""",
    ),
    # ---- test_mat_matmul_bridge_rc72.py:131 — mat_matmul non-Mat ----------
    dict(
        pid="mat_matmul_non_mat",
        site="tests/test_mat_matmul_bridge_rc72.py:131",
        op="srmech.math.laplacian.mat_matmul",
        input_class="plain nested lists instead of Mat",
        predict=2,
        body="""
from srmech.math.laplacian import mat_matmul
_run(lambda: mat_matmul([[1.0]], [[1.0]]))
""",
    ),
    # ---- test_byo_cascade_toml.py:156 — register_catalog_dir --------------
    dict(
        pid="register_catalog_dir_missing",
        site="tests/test_byo_cascade_toml.py:156",
        op="srmech.dsl.register_catalog_dir",
        input_class="a path that does not exist",
        predict=1,
        body="""
from srmech import dsl
from srmech.dsl import _catalog
def go():
    dsl.register_catalog_dir("/nonexistent/srmech/t1131/probe/dir")
    registered = [str(p) for p in _catalog._USER_CATALOG_DIRS]
    n_ops = len(dsl.list_cascade_ops())
    return {"registered": registered, "n_cascade_ops": n_ops}
_run(go)
""",
    ),
    dict(
        pid="register_catalog_dir_is_a_file",
        site="tests/test_byo_cascade_toml.py:156 (input class NOT covered: a FILE)",
        op="srmech.dsl.register_catalog_dir",
        input_class="an existing path that is a FILE, not a directory",
        predict=1,
        body="""
from srmech import dsl
from srmech.dsl import _catalog
import srmech
target = srmech.__file__          # a real file, not a dir
def go():
    dsl.register_catalog_dir(target)
    return {"registered": [str(p) for p in _catalog._USER_CATALOG_DIRS],
            "n_cascade_ops": len(dsl.list_cascade_ops())}
_run(go)
""",
    ),
    # ---- the SHIPPED genome couple guards (the tests use LOCAL copies) -----
    dict(
        pid="q8_couple_reachability",
        site="tests/test_genome_q8_coupling_rc311.py:233 (SHIPPED peer)",
        op="srmech.biology.genome._q8_couple",
        input_class="REACHABILITY: can any public input make _q8_side_ok False?",
        predict=4,
        body="""
from srmech.biology import genome as G
from srmech.math.hv import HV
from srmech.biology.genome import OCT
import random
rng = random.Random(1131)
def go():
    fired = 0
    trials = 0
    for dim in (1, 2, 8, 64):
        for _ in range(60):
            t = bytes(rng.randrange(8) for _ in range(dim))
            o = bytes(rng.randrange(8) for _ in range(dim))
            trials += 1
            try:
                G._q8_couple(HV.from_sequence(t, sectors=OCT),
                             HV.from_sequence(o, sectors=OCT))
            except AssertionError:
                fired += 1
    # now try to force it with OUT-OF-RANGE Q8 bytes via a wider-sector HV
    oor = None
    try:
        G._q8_couple(HV.from_sequence(bytes([200, 9]), sectors=256),
                     HV.from_sequence(bytes([201, 10]), sectors=256))
        oor = "returned (no exception)"
    except BaseException as exc:
        oor = type(exc).__name__ + ": " + str(exc)[:160]
    return {"in_range_trials": trials, "assert_fired": fired,
            "out_of_range_q8_bytes": oor}
_run(go)
""",
    ),
    dict(
        pid="oct_couple_reachability",
        site="tests/test_octonion_carrier_rc324.py:355 (SHIPPED peer)",
        op="srmech.biology.genome._oct_couple",
        input_class="REACHABILITY: can any public input make _oct_side_ok False?",
        predict=4,
        body="""
from srmech.biology import genome as G
from srmech.math.hv import HV
from srmech.biology.genome import OCTONION_SECTORS
import random
rng = random.Random(1131)
def go():
    fired = 0
    trials = 0
    for dim in (1, 2, 8, 64):
        for _ in range(60):
            t = bytes(rng.randrange(16) for _ in range(dim))
            o = bytes(rng.randrange(16) for _ in range(dim))
            trials += 1
            try:
                G._oct_couple(HV.from_sequence(t, sectors=OCTONION_SECTORS),
                              HV.from_sequence(o, sectors=OCTONION_SECTORS))
            except AssertionError:
                fired += 1
    oor = None
    try:
        G._oct_couple(HV.from_sequence(bytes([200, 17]), sectors=256),
                      HV.from_sequence(bytes([201, 18]), sectors=256))
        oor = "returned (no exception)"
    except BaseException as exc:
        oor = type(exc).__name__ + ": " + str(exc)[:160]
    return {"in_range_trials": trials, "assert_fired": fired,
            "out_of_range_oct_bytes": oor}
_run(go)
""",
    ),
    # ---- the two META-GATE sites (negative controls) -----------------------
    dict(
        pid="frame_scope_meta_gate",
        site="tests/test_frame_scope_rc430.py:587",
        op="tests.test_frame_scope_rc430.assert_declaration_matches (TEST-LOCAL)",
        input_class="NEGATIVE CONTROL — a test-local gate, not a shipped op",
        predict=4,
        body="""
import inspect, importlib
m = importlib.import_module("tests.test_frame_scope_rc430")
fn = getattr(m, "assert_declaration_matches")
_run(lambda: {"module": fn.__module__, "is_package_code": fn.__module__.startswith("srmech"),
              "n_asserts_compiled": _n(fn)})
def _n(f):
    import dis
    return sum(1 for i in dis.get_instructions(f) if i.opname == "LOAD_ASSERTION_ERROR")
""",
    ),
    dict(
        pid="owner_axis_meta_gate",
        site="tests/test_owner_axis_rc410.py:659",
        op="tests.test_tool_schema.test_unregister_profile_tools_removes_all (A TEST)",
        input_class="NEGATIVE CONTROL — drives another TEST through its failure path",
        predict=4,
        body="""
import importlib, dis
m = importlib.import_module("tests.test_tool_schema")
fn = getattr(m, "test_unregister_profile_tools_removes_all")
n = sum(1 for i in dis.get_instructions(fn) if i.opname == "LOAD_ASSERTION_ERROR")
_run(lambda: {"module": fn.__module__, "is_package_code": fn.__module__.startswith("srmech"),
              "n_asserts_compiled": n})
""",
    ),
]


def _run_one(body, optimize):
    src = _PREAMBLE + body
    env = dict(os.environ)
    env["PYTHONPATH"] = PYPATH
    env.pop("PYTHONOPTIMIZE", None)
    cmd = [sys.executable]
    if optimize:
        cmd.append("-O")
    cmd += ["-c", src]
    try:
        p = subprocess.run(cmd, cwd=PYPATH, env=env, capture_output=True,
                           text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return {"kind": "timeout", "detail": None, "rc": None}
    line = None
    for ln in p.stdout.splitlines():
        if ln.startswith("@@RESULT@@"):
            line = json.loads(ln[len("@@RESULT@@"):])
    if line is None:
        return {"kind": "harness_error", "detail": {
            "rc": p.returncode, "stdout": p.stdout[-800:], "stderr": p.stderr[-800:]}}
    line["rc"] = p.returncode
    return line


def classify(default, opt):
    """Map the (default, -O) pair onto the outcome vocabulary."""
    d_kind, o_kind = default.get("kind"), opt.get("kind")
    if "harness_error" in (d_kind, o_kind) or "timeout" in (d_kind, o_kind):
        return 0, "HARNESS_ERROR"
    if d_kind == "returned" and o_kind == "returned":
        if default.get("detail") == opt.get("detail"):
            return 4, "INVARIANT (both return, identical)"
        return 4, "INVARIANT-ish (both return, DIFFERENT values)"
    if o_kind == "returned":
        return 1, "SILENT_WRONG (-O returns a value from invalid input)"
    d_t = default.get("detail", {}).get("type") if d_kind == "raised" else None
    o_t = opt.get("detail", {}).get("type") if o_kind == "raised" else None
    if d_t == o_t:
        return 4, "INVARIANT (both raise %s)" % o_t
    if d_t == "AssertionError" and o_t in ("ValueError", "TypeError", "ZeroDivisionError"):
        return 3, "CORRECT_REJECT (-O raises %s — a real raise below the assert)" % o_t
    return 2, "CRASH_LATER (default %s, -O %s)" % (d_t, o_t)


def main():
    recs = []
    for pr in PROBES:
        d = _run_one(pr["body"], optimize=False)
        o = _run_one(pr["body"], optimize=True)
        code, label = classify(d, o)
        rec = {
            "probe_id": pr["pid"],
            "site": pr["site"],
            "op": pr["op"],
            "input_class": pr["input_class"],
            "predicted_outcome": pr["predict"],
            "measured_outcome": code,
            "outcome_label": label,
            "prediction_hit": code == pr["predict"],
            "default_mode": d,
            "optimized_mode": o,
        }
        recs.append(rec)
        print("%-34s pred=%d meas=%d %-6s %s" % (
            pr["pid"], pr["predict"], code,
            "HIT" if code == pr["predict"] else "MISS", label))
        sys.stdout.flush()

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({
            "record": "probe_meta",
            "python": sys.version.split()[0],
            "pythonpath": PYPATH,
            "n_probes": len(recs),
            "n_prediction_misses": sum(1 for r in recs if not r["prediction_hit"]),
        }, sort_keys=True) + "\n")
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("\nmisses:", [r["probe_id"] for r in recs if not r["prediction_hit"]])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
