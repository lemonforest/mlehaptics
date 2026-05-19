"""Spike #138.1 — Python-pure cross-stack verification at depth-4.

Forces srmech native dispatch off (HAS_NATIVE = False) then runs the d4
closure pass. The result is bit-exact-compared to the Python+C d4 run for
the universal-identity set.

This is the cross-stack bit-exact requirement from the spike brief (the
Python+C and Python-pure stacks should produce byte-identical universal-
identity sets, per Spike #138 precedent).

Run:
  python notes/spike138_1_python_pure_d4.py
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(HERE))

# Disable native BEFORE importing the wrappers that capture _native.HAS_NATIVE.
from srmech.amsc import _native  # noqa: E402

_native.HAS_NATIVE = False
_native.LIB = None
_native.LOAD_ERROR = "spike138.1 forced pure-Python mode"

import spike138_explorer as ex  # noqa: E402 — must come after the _native flip
import spike138_1_closure_verifier as v  # noqa: E402

# Sanity-check that the flip stuck.
assert not ex._native.HAS_NATIVE, "HAS_NATIVE override failed"

print(f"spike138.1 python-pure: HAS_NATIVE={ex._native.HAS_NATIVE}")
print(f"spike138.1 python-pure: LIB={ex._native.LIB}")

substrates = ex.build_substrates()
d4_tuples = v.enumerate_subgroup_at_depth(4, v.SUBGROUP)
assert len(d4_tuples) == 625

out_path = HERE / "spike138_1_d4_python_pure.ndjson"
summary = v.run_closure(
    depth=4,
    tuples=d4_tuples,
    substrates=substrates,
    seed=138,
    stack_id="python-pure",
    out_path=out_path,
    label="depth4_closure_pure",
)
print(f"python-pure d4 closure_rate = {summary['closure_rate']:.4f}")
