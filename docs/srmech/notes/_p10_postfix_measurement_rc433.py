"""`#T1131` P10 — the POST-FIX re-measurement, so every shipped number is a
measurement rather than a claim.

P1–P9 measured the rc432 tree. This file re-runs the three load-bearing
measurements against the REPAIRED tree, so the flip in each is an execution and
not an assertion:

  1. the per-site ``-O`` before/after table          (12 promoted + 8 siblings)
  2. the static-gate population                       (19 sites: 12 -> 0 defects)
  3. the input-shaped package-assert CEIL             (49 -> 41)

Every number quoted in the rc433 CHANGELOG entry, the notebook §3.55 entry and
the gate docstrings comes from here. Per
``[[feedback_computational_provenance_discipline]]``, load-bearing numbers ship
their generating code.

Run (WSL2, numpy ABSENT, from the repo or a worktree):

  cd <tree>/docs/srmech/python
  PYTHONPATH=$PWD python3 ../notes/_p10_postfix_measurement_rc433.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY_ROOT = HERE.parent / "python"
PKG_DIR = PY_ROOT / "srmech"
TESTS_DIR = PY_ROOT / "tests"
OUT = HERE / "_p10_postfix_measurement_rc433.ndjson"

# SELF-LOCATING, and not merely tidiness. Run as a script from this directory,
# ``sys.path[0]`` is ``notes/`` and a bare ``import srmech`` resolves to a
# NAMESPACE package (``__file__ is None``, no ``__version__``) rather than the
# real one — measured, twice, while writing this file. Pinning PY_ROOT at the
# front makes the module under measurement the one that lives beside this
# script, which is also the only correct subject: a provenance file that
# measured whatever ``PYTHONPATH`` happened to point at would be worthless.
sys.path.insert(0, str(PY_ROOT))

import srmech  # noqa: E402  (deliberately after the sys.path pin above)

assert srmech.__file__ and Path(srmech.__file__).resolve().is_relative_to(
    PKG_DIR.resolve()), (
    f"measuring the wrong srmech: {srmech.__file__} is not under {PKG_DIR}")

# ══════════════════════════════════════════════════════════════════════════
# 1. the per-site -O table
# ══════════════════════════════════════════════════════════════════════════
#: ``(site_id, op, import_stmt, call_expr)``. Each call is the exact input
#: class P2 executed at rc432. The rc432 column of the shipped table is P2's
#: measurement; this re-runs the same calls against the repaired tree.
SITES = [
    ("1a", "Mat.from_rows ragged short-first",
     "from srmech.math.mat import Mat",
     "Mat.from_rows([[1.0], [2.0, 3.0]])"),
    ("1b", "Mat.from_rows ragged long-first",
     "from srmech.math.mat import Mat",
     "Mat.from_rows([[1.0, 2.0], [3.0]])"),
    ("2a", "Vec[-5] on n=3",
     "from srmech.math.vec import Vec",
     "Vec.from_sequence([10.0, 20.0, 30.0])[-5]"),
    ("2b", "Vec[3] on n=3",
     "from srmech.math.vec import Vec",
     "Vec.from_sequence([10.0, 20.0, 30.0])[3]"),
    ("3", "loop_bind_hd len 25",
     "from srmech.math import hdc", "hdc.loop_bind_hd([1.0]*25, [1.0]*25)"),
    ("4", "loop_unbind_hd len 25",
     "from srmech.math import hdc", "hdc.loop_unbind_hd([1.0]*25, [1.0]*25)"),
    ("5a", "loop_conj_hd len 25",
     "from srmech.math import hdc", "hdc.loop_conj_hd([1.0]*25)"),
    ("5b", "loop_inv_hd len 25",
     "from srmech.math import hdc", "hdc.loop_inv_hd([1.0]*25)"),
    ("6", "loop_runbind_hd len 25",
     "from srmech.math import hdc", "hdc.loop_runbind_hd([1.0]*25, [1.0]*25)"),
    ("7a", "loop_runbind_hd 56 vs 48",
     "from srmech.math import hdc", "hdc.loop_runbind_hd([1.0]*56, [1.0]*48)"),
    ("7b", "loop_bind_hd 56 vs 48 (SIBLING, unpinned)",
     "from srmech.math import hdc", "hdc.loop_bind_hd([1.0]*56, [1.0]*48)"),
    ("7c", "loop_unbind_hd 56 vs 48 (SIBLING, unpinned)",
     "from srmech.math import hdc", "hdc.loop_unbind_hd([1.0]*56, [1.0]*48)"),
    ("8", "register_catalog_dir missing path",
     "from srmech import dsl",
     "dsl.register_catalog_dir('/definitely/not/a/real/path/t1131')"),
    ("9", "mat_matmul non-Mat",
     "from srmech.math import laplacian as L", "L.mat_matmul([[1.0]], [[1.0]])"),
    ("10", "operator_norm non-square",
     "from srmech.physics.qm import bell\nfrom srmech.math.mat import Mat",
     "bell.operator_norm(Mat.from_rows([[1.0,2.0,3.0],[4.0,5.0,6.0]]))"),
    ("11", "operator_norm lying ndim",
     "from srmech.physics.qm import bell\n"
     "class _L:\n"
     "    ndim = 1\n"
     "    def __iter__(self):\n"
     "        return iter([[1.0, 0.0], [0.0, 1.0]])",
     "bell.operator_norm(_L())"),
    ("12a", "loop_inv_hd zero block",
     "from srmech.math import hdc", "hdc.loop_inv_hd([0.0]*24)"),
    ("12b", "loop_inv zero (SIBLING, unpinned)",
     "from srmech.math import hdc", "hdc.loop_inv([0.0]*8)"),
    ("S1", "mat_solve non-Mat (SIBLING, unpinned)",
     "from srmech.math import laplacian as L", "L.mat_solve([[1.0]], [[1.0]])"),
    ("S2", "mat_lstsq non-Mat (SIBLING, unpinned)",
     "from srmech.math import laplacian as L", "L.mat_lstsq([[1.0]], [[1.0]])"),
    ("S3", "mat_hermitian_eigendecompose non-Mat (SIBLING, unpinned)",
     "from srmech.math import laplacian as L",
     "L.mat_hermitian_eigendecompose([[1.0]])"),
    ("S4", "mat_eigvals non-Mat (SIBLING, unpinned)",
     "from srmech.math import laplacian as L", "L.mat_eigvals([[1.0]])"),
    ("S5", "mat_svd non-Mat (SIBLING, unpinned)",
     "from srmech.math import laplacian as L", "L.mat_svd([[1.0]])"),
    ("S6", "bigq_reduce_c den=0 (SIBLING, unpinned)",
     "from srmech import _native", "_native.bigq_reduce_c(5, 0)"),
    ("S7", "bigq_div_c b_num=0 (SIBLING, unpinned)",
     "from srmech import _native", "_native.bigq_div_c(1, 2, 0, 1)"),
]

#: POSITIVE CONTROLS — correct input that must keep working. A gate that fires
#: on correct code is a broken gate, and a promotion that broke the happy path
#: would otherwise be invisible in a table of expected failures.
CONTROLS = [
    ("C1", "Mat.from_rows well-formed",
     "from srmech.math.mat import Mat",
     "Mat.from_rows([[1.0, 2.0], [3.0, 4.0]]).shape"),
    ("C2", "Vec[-1] in range",
     "from srmech.math.vec import Vec",
     "Vec.from_sequence([10.0, 20.0, 30.0])[-1]"),
    ("C3", "loop_bind_hd len 24",
     "from srmech.math import hdc", "len(hdc.loop_bind_hd([1.0]*24, [1.0]*24))"),
    ("C4", "mat_matmul(Mat, Mat)",
     "from srmech.math import laplacian as L\nfrom srmech.math.mat import Mat",
     "L.mat_matmul(Mat.from_rows([[1.0]]), Mat.from_rows([[1.0]])).shape"),
    ("C5", "operator_norm square",
     "from srmech.physics.qm import bell\nfrom srmech.math.mat import Mat",
     "bell.operator_norm(Mat.from_rows([[2.0, 0.0], [0.0, 1.0]]))"),
    ("C6", "bigq_reduce_c valid args",
     "from srmech import _native", "_native.bigq_reduce_c(4, 6)"),
]


def _outcome(imp, call, optimized):
    """Run ``call`` in a FRESH interpreter; report the outcome.

    A subprocess is not ceremony: ``-O`` is a startup flag and ``assert`` is
    stripped at COMPILE time, so an in-process probe cannot observe the
    optimized behaviour of an already-imported module at all.
    """
    src = "\n".join([
        imp,
        "try:",
        f"    _r = {call}",
        "except BaseException as e:",
        "    print('RAISED', type(e).__name__)",
        "else:",
        "    print('RETURNED', repr(_r)[:60])",
    ])
    argv = [sys.executable] + (["-O"] if optimized else []) + ["-c", src]
    p = subprocess.run(argv, capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        return "PROBE_CRASH: " + p.stderr.strip()[-120:]
    return p.stdout.strip().splitlines()[-1]


# ══════════════════════════════════════════════════════════════════════════
# 2. the static-gate population (re-uses the SHIPPED gate, not a copy)
# ══════════════════════════════════════════════════════════════════════════
def gate_population():
    """Import the SHIPPED gate module and run its own classifier.

    Deliberately NOT a re-implementation: measuring with a copy would let the
    copy and the gate drift, and the number here would stop describing what
    CI enforces (``[[feedback_scratch_measurements_must_use_srmech_or_gaps_
    stay_invisible]]`` — the subject must be the shipped instrument).
    """
    sys.path.insert(0, str(TESTS_DIR))
    import test_assert_contract_gate_rc433 as gate  # noqa: E402

    hits = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        hits.extend(gate.classify_source(
            path.read_text(encoding="utf-8"), label=path.name))
    counts = {}
    for h in hits:
        counts[h["gate_verdict"]] = counts.get(h["gate_verdict"], 0) + 1
    return hits, counts, gate


# ══════════════════════════════════════════════════════════════════════════
# 3. the CEIL census (again, the SHIPPED predicate)
# ══════════════════════════════════════════════════════════════════════════
def ceil_census(gate):
    rows = []
    for path in sorted(PKG_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rows.extend(gate._input_shaped_asserts(path))
    return rows


def main():
    recs = []

    print("=== 1. per-site -O table (POST-FIX) ===")
    print(f"{'ID':<5} {'SITE':<48} {'default':<26} {'-O':<26} {'INVARIANT'}")
    n_invariant = 0
    for sid, name, imp, call in SITES:
        plain = _outcome(imp, call, False)
        opt = _outcome(imp, call, True)
        inv = plain == opt
        n_invariant += bool(inv)
        print(f"{sid:<5} {name:<48} {plain:<26} {opt:<26} {'YES' if inv else '*** NO ***'}")
        recs.append({"record": "site_postfix", "id": sid, "site": name,
                     "call": call, "default": plain, "dash_o": opt,
                     "o_invariant": inv})

    print("\n=== 1b. positive controls (correct input must still work) ===")
    n_ctrl_ok = 0
    for sid, name, imp, call in CONTROLS:
        plain = _outcome(imp, call, False)
        opt = _outcome(imp, call, True)
        ok = plain == opt and plain.startswith("RETURNED")
        n_ctrl_ok += bool(ok)
        print(f"{sid:<5} {name:<48} {plain:<26} {opt:<26} {'OK' if ok else '*** BROKEN ***'}")
        recs.append({"record": "control_postfix", "id": sid, "site": name,
                     "call": call, "default": plain, "dash_o": opt, "ok": ok})

    print("\n=== 2. static-gate population ===")
    hits, counts, gate = gate_population()
    print(f"  total guarded sites : {len(hits)}")
    for k in sorted(counts):
        print(f"  {k:<18}: {counts[k]}")
    recs.append({"record": "gate_population_postfix", "n_sites": len(hits),
                 "counts": counts,
                 "survivors": sorted((h["file"], h["line"]) for h in hits)})

    print("\n=== 3. CEIL census ===")
    rows = ceil_census(gate)
    print(f"  input-shaped package asserts : {len(rows)}")
    print(f"  shipped CEIL constant        : "
          f"{gate.CEIL_INPUT_SHAPED_PACKAGE_ASSERTS}")
    recs.append({"record": "ceil_postfix", "n_input_shaped": len(rows),
                 "ceil_constant": gate.CEIL_INPUT_SHAPED_PACKAGE_ASSERTS,
                 "rc432_baseline": 49,
                 "rows": sorted(rows)})

    meta = {
        "record": "meta", "task": "#T1131", "target_rc": "0.9.0rc433",
        "srmech_version": srmech.__version__,
        "srmech_file": srmech.__file__,
        "python": sys.version.split()[0],
        "n_sites": len(SITES), "n_o_invariant": n_invariant,
        "n_controls": len(CONTROLS), "n_controls_ok": n_ctrl_ok,
        "gate_candidate_defects": counts.get("CANDIDATE_DEFECT", 0),
        "ceil_rc432": 49, "ceil_rc433": len(rows),
    }
    recs.insert(0, meta)

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")

    print("\n" + "=" * 70)
    print(f"-O invariant           : {n_invariant}/{len(SITES)}")
    print(f"positive controls OK   : {n_ctrl_ok}/{len(CONTROLS)}")
    print(f"gate CANDIDATE_DEFECT  : {counts.get('CANDIDATE_DEFECT', 0)}")
    print(f"CEIL 49 -> {len(rows)}")
    print("wrote", OUT)
    return 0 if (n_invariant == len(SITES)
                 and n_ctrl_ok == len(CONTROLS)
                 and counts.get("CANDIDATE_DEFECT", 0) == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
