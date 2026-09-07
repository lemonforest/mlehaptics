"""rc469 (`#T1188`) — the generating code for every number the frame-probe
leaf-addressing repair quotes in shipped prose.

Per the computational-provenance discipline: the figures in
``tools/frame_probe.py``'s ``MOD_LEAF_BUDGET`` docstring, in
``tools/frame_scope_census.py``'s revision-11 trail entry, and in the
rc469 arms of ``tests/test_frame_scope_rc430.py`` are all produced here.
The ones a GATE can re-execute (exactly one verdict moves; both negative
controls hold; the summands keep their frame) live in that test file and are
run on every CI pass — what is here is the rest: the capped-vs-uncapped
comparison that licenses the budget, the blast-radius population, and the
HALF-REPAIR control, which cannot be a gate because it requires shipping the
defect.

Run (WSL2, numpy-absent)::

    cd docs/srmech/python
    python3 ../notes/_frame_leaf_addressing_rc469.py

MEASURED at srmech 0.9.0rc469, pure + native, WSL2 py3.10:

  A  capped(4) 38,622 probe calls; uncapped 100,193. IDENTICAL by_verdict,
     admissible set and findings. 55,386 of the 61,571 extra calls (90%) are
     normalized_cut_bisect alone, whose harvested `edges` is 69 vertex pairs.
     THE CALL COUNT IS THE MEASUREMENT and it is deterministic — identical
     across runs. Wall clock is NOT usable at this size: 41.5-42.7 s capped
     against 48.9-59.5 s uncapped over two runs, a spread wider than some of
     the effect.
  B  the HALF repair (leaf-addressed moduli(), rc468 whole-parameter
     coordinate assignment) reproduces the rc468 by_verdict BYTE FOR BYTE:
     ADMISSIBLE 22, NOT_ADMISSIBLE 196, nothing red anywhere. A silent no-op
     that reads as a repair.
  C  221 ops carry a frame coordinate; 123 of them had an EMPTY rc468
     moduli(); 46 of those 123 hold a candidate modulus leaf that was
     unreachable. EXACTLY ONE (hypercomplex_exp) becomes newly ADMISSIBLE;
     three more (interval_vector / normal_order / prime_form) gain candidate
     leaves and were already admissible on the FIXED branch.
  D  probe-free: hypercomplex_exp(turn=(k, n)) is periodic in k with period
     exactly n at every n in NS, n distinct values per period, and no
     constant period in 2..24 survives the sweep.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_PY = Path(__file__).resolve().parents[1] / "srmech" / "python"
if not _PY.exists():                        # running from the python root
    _PY = Path(__file__).resolve().parents[2] / "srmech" / "python"
for _p in (str(_PY), str(_PY / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import srmech                                          # noqa: E402
import example_args as ea                              # noqa: E402
import frame_probe as fp                               # noqa: E402
from srmech.cascade import hypercomplex_exp            # noqa: E402
from srmech.introspect.tool_schema import (            # noqa: E402
    get_tool_schema, warmup_all)

CENSUS = (Path(fp.__file__).resolve().parents[1] / "tests"
          / "frame_scope_census.ndjson")


def _sweep(rows, tools, budget):
    """One whole-registry census at the given MOD_LEAF_BUDGET."""
    keep, fp.MOD_LEAF_BUDGET = fp.MOD_LEAF_BUDGET, budget
    try:
        t0 = time.monotonic()
        out, calls = {}, 0
        for e in tools:
            r = fp.probe_from_ledger(e.name, rows)
            calls += r.get("calls") or 0
            out[e.name] = {"verdict": r["verdict"],
                           "findings": r.get("findings") or []}
        secs = time.monotonic() - t0
    finally:
        fp.MOD_LEAF_BUDGET = keep
    by = {}
    for r in out.values():
        by[r["verdict"]] = by.get(r["verdict"], 0) + 1
    return {"ops": out, "seconds": round(secs, 1), "calls": calls,
            "by_verdict": dict(sorted(by.items()))}


def _rc468_moduli(base, exclude):
    """The rc468 rule: a top-level bare int > 1, excluded by parameter NAME."""
    return [k for k, v in base.items()
            if k != exclude and fp.is_int(v) and v > 1]


def main() -> int:
    print("srmech.__version__ =", srmech.__version__)
    warmup_all()
    rows = ea.load_ledger()
    tools = get_tool_schema().tools

    # ── A. the measurement that licenses MOD_LEAF_BUDGET ──────────────
    cap = _sweep(rows, tools, 4)
    unc = _sweep(rows, tools, 10 ** 9)
    print("\n=== A. CAPPED(4) vs UNCAPPED ===")
    print("  by_verdict identical:", cap["by_verdict"] == unc["by_verdict"])
    print("  findings   identical:",
          {n: r["findings"] for n, r in cap["ops"].items()}
          == {n: r["findings"] for n, r in unc["ops"].items()})
    print("  capped   %.1f s / %d calls" % (cap["seconds"], cap["calls"]))
    print("  uncapped %.1f s / %d calls" % (unc["seconds"], unc["calls"]))
    print("  by_verdict:", json.dumps(cap["by_verdict"], sort_keys=True))

    # ── B. the HALF repair — a no-op that reads as a repair ───────────
    # Computed FIRST because it reproduces the rc468 verdicts exactly, which
    # makes it the baseline the blast radius is measured against. There is no
    # other honest baseline available in-process: the committed census is the
    # REPAIRED one.
    print("\n=== B. HALF REPAIR (moduli() leaf-addressed, _step NOT) ===")
    real_step = fp.Driver._step

    def rc468_step(self, coord, d, over):
        kw = self._kwargs(over)
        kw[coord] = fp.translate(self.base[coord], d)
        return self._call(kw)

    fp.Driver._step = rc468_step
    try:
        half = _sweep(rows, tools, 4)
    finally:
        fp.Driver._step = real_step
    print("  by_verdict:", json.dumps(half["by_verdict"], sort_keys=True))
    print("  hypercomplex_exp:",
          half["ops"]["srmech.cascade.hypercomplex_exp"]["verdict"])
    moved = sorted(n for n in cap["ops"]
                   if cap["ops"][n]["verdict"] != half["ops"][n]["verdict"])
    print("  verdicts the OTHER half of the repair moves:", moved)

    # ── C. the blast-radius population ────────────────────────────────
    print("\n=== C. BLAST RADIUS ===")
    with_coord = empty_before = 0
    gains = []
    for e in tools:
        if e.name in fp.CONTRACT_SKIP or e.name in fp.SLOW_SKIP:
            continue
        base = dict((rows.get(e.name) or {}).get("args") or {})
        res = ea.resolve(e.name)
        if not base or res is None or fp.binding_gap(res[2], base):
            continue
        drv = fp.Driver(e.name, base, res[2])
        coords = drv.coordinates()
        if not coords:
            continue
        with_coord += 1
        if any(_rc468_moduli(base, c) for c in coords):
            continue
        empty_before += 1
        if any(drv.moduli(c) for c in coords):
            gains.append(e.name)
    print("  ops with a frame coordinate            :", with_coord)
    print("  ... rc468 moduli() EMPTY               :", empty_before)
    print("  ... rc469 finds a candidate modulus    :", len(gains))
    newly = sorted(n for n in gains
                   if cap["ops"][n]["verdict"] == "ADMISSIBLE"
                   and half["ops"][n]["verdict"] != "ADMISSIBLE")
    print("  ... of those, NEWLY ADMISSIBLE         :", newly)
    already = sorted(n for n in gains
                     if half["ops"][n]["verdict"] == "ADMISSIBLE")
    print("  (already admissible before, gained a leaf:", already, ")")

    committed = None
    for line in CENSUS.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("record") == "meta":
            committed = row
            break
    print("  committed artefact by_verdict matches this run:",
          committed["by_verdict"] == cap["by_verdict"])

    # ── D. the same claim WITHOUT the probe ───────────────────────────
    print("\n=== D. hypercomplex_exp PERIODICITY, PROBE-FREE ===")
    def val(k, n):
        return json.dumps(hypercomplex_exp(turn=(k, n), k_axes=1), default=str)
    for n in fp.NS:
        vs = [val(k, n) for k in range(1, 1 + 3 * n)]
        print("  n=%2d period-%d holds: %s   distinct per period: %d"
              % (n, n, all(vs[i] == vs[i + n] for i in range(len(vs) - n)),
                 len(set(vs))))
    survivors = [m for m in range(2, 25)
                 if all(val(k, n) == val(k + m, n)
                        for n in fp.NS for k in range(1, 1 + 2 * n))]
    print("  constant periods in 2..24 surviving the NS sweep:", survivors,
          "(empty => parametric, not fixed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
