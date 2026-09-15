"""instr round item 5(b): which kepler rows see a C-only revert, and a one-text row that would.
Native cell, from docs/srmech/python. Usage: python m_kep_partition.py <python root>
Uses the test module's own _outcome / _force_pure / _pre_repair_outcome. Prints; asserts nothing.
"""
import importlib.util
import sys
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("kslots", root / "tests" / "test_kepler_non_finite_slots_rc473.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
from srmech import _native  # noqa: E402
from srmech.math import kepler  # noqa: E402

print("HAS_NATIVE", _native.HAS_NATIVE)
assert _native.HAS_NATIVE


def cmp(m_rad, e, kw):
    native = t._outcome(lambda: kepler.kepler_solve(m_rad, e, **kw))
    pure = t._force_pure(lambda: t._outcome(lambda: kepler.kepler_solve(m_rad, e, **kw)))
    return native, pure


frontier = [(m, e, {"tolerance": tol, "max_iter": 30})
            for m in t._FRONTIER_MS for e in t._FRONTIER_ES for tol in t._FRONTIER_TOLS]
slot = [(t.PI_2, 0.0549, kw) for kw in t._TEXT_AND_TINY_ROWS]
big = [(2.0 ** 53, 0.999, {})]
for name, rows in (("frontier", frontier), ("slot", slot), ("2**53", big)):
    d = 0
    for m, e, kw in rows:
        n, p = cmp(m, e, kw)
        d += n != p
    print(f"part {name}: {d} of {len(rows)} rows differ native vs pure")
one_text = [(t.PI_2, 0.0549, kw) for kw in t._TEXT_AND_TINY_ROWS[:6] + t._TEXT_AND_TINY_ROWS[-2:]]
bad = sum(1 for m, e, kw in one_text if cmp(m, e, kw)[0] != cmp(m, e, kw)[1])
print(f"one-text rows (8) whose native and pure texts differ: {bad}")
print("golden rows differing from the pinned text:",
      [i for i, (a, kw, want) in enumerate(t._GOLDEN) if t._outcome(lambda: kepler.kepler_solve(*a, **kw)) != want])

# Candidate one-text rows, predicted LIBRARY-FREE: both iterations refuse, and the texts differ.
cands = []
for m, e in ((t.PI_2, 0.0549), (0.1, 0.99), (1.0, 0.5), (3.0, 0.9), (t.PI_2, 0.9), (100.0, 0.9)):
    for tol in (1e-12, 1e-15, 0.0):
        for k in (1, 2, 3, 4, 5):
            old = t._pre_repair_outcome(m, e, tol, k)
            new = t._force_pure(lambda: t._outcome(
                lambda: kepler.kepler_solve(m, e, tolerance=tol, max_iter=k)))
            if old.startswith("refuse RuntimeError: kepler_solve: did not converge") and \
               new.startswith("refuse RuntimeError: kepler_solve: did not converge") and old != new:
                cands.append((m, e, {"tolerance": tol, "max_iter": k}, old[-40:], new[-40:]))
print(f"predicted one-text rows where the double and Q61 non-convergence texts differ: {len(cands)}")
for c in cands[:12]:
    print("   ", c)
seen, pick = set(), []
for m, e, kw, _o, _n in cands:
    if (m, e) not in seen:
        seen.add((m, e))
        pick.append((m, e, kw))
print("picked (one per (M, e)):", pick)
ext_bad = 0
for m, e, kw in one_text + pick:
    n, p = cmp(m, e, kw)
    ok = n.startswith("refuse RuntimeError: kepler_solve: did not converge") and n == p
    if ok:
        best = n.rsplit("best_E=", 1)[1].rstrip(")")
        ok = repr(float(best)) == best
    ext_bad += not ok
print(f"EXTENDED one-text check ({len(one_text)} + {len(pick)} rows): rows failing {ext_bad}")
