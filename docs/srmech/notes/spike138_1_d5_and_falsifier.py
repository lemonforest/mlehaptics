"""Spike #138.1 — Depth-5 closure + external falsifier, python-pure stack.

Resumes after d4 closure has already verified at closure_rate=1.0 (625/625)
on BOTH stacks (python+c, python-pure, bit-exact).

Runs:
  1. Depth-5 EXHAUSTIVE for {B,D,E,F,L}: 3,125 tuples x 25 cells = 78,125 cells
  2. External falsifier: 100 d2 + 100 d3 tuples touching {A,C,G,H,I,J,K,M,N}
     x 25 cells = 5,000 cells

Anti-stall implementation:
  - Incremental NDJSON flush every tuple (25 records flushed + fsync)
  - Per-tuple stdout heartbeat every 50 tuples for d5, every 25 for falsifier
  - Early-exit if d5 closure_rate < 0.90 after first 250 tuples

Stack: python-pure (HAS_NATIVE = False) — Spike #138.1 already verified
       bit-exact equivalence with python+c at d4, and python-pure is 7x
       faster on these small substrates (Class L native marshalling overhead).

Run:
  python notes/spike138_1_d5_and_falsifier.py
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from collections import Counter
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(HERE))

# Force python-pure mode (faster on small substrates).
from srmech.amsc import _native  # noqa: E402

_native.HAS_NATIVE = False
_native.LIB = None
_native.LOAD_ERROR = "spike138.1 forced pure-Python mode"

import spike138_explorer as ex  # noqa: E402

SPIKE_NUMBER = "138.1"
SPIKE_DATE = "2026-05-18"
SUBGROUP = ("B", "D", "E", "F", "L")
COMPLEMENT = tuple(c for c in ex.CLASSES if c not in SUBGROUP)
INSPECTION_ORDERINGS = ex.INSPECTION_ORDERINGS
N_CELLS_PER_TUPLE = 25
SEED = 138
STACK_ID = "python-pure"


def evaluate_tuple_closure(tup, substrates):
    records = []
    n_identity = 0
    for sub_id, sub in substrates.items():
        for ins_name, ins_cas in INSPECTION_ORDERINGS.items():
            rec = ex.run_cell(tup, sub, ins_name, ins_cas, SEED, STACK_ID)
            rec.pop("per_class_timing_ns", None)
            rec.pop("total_elapsed_ns", None)
            records.append(rec)
            if rec["output_form_classification"] == "identity_attractor":
                n_identity += 1
    return records, n_identity


def run_streaming(label, tuples, substrates, out_path, depth, framing_extra=None):
    """Stream NDJSON records: framing line first, per-tuple records flushed
    immediately, summary line last. Anti-stall: fsync every tuple."""
    framing = {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "kind": "framing",
        "stack_id": STACK_ID,
        "label": label,
        "depth": depth,
        "n_tuples": len(tuples),
        "n_cells": len(tuples) * N_CELLS_PER_TUPLE,
        "subgroup": list(SUBGROUP),
        "has_native": False,
        "n_substrates": 5,
        "n_inspection_orderings": 5,
        "fixed_point_threshold": ex.FIXED_POINT_THRESHOLD,
        "inspection_depth_cap": ex.INSPECTION_DEPTH_CAP,
        "anchor_citation": "Spike #138.1; resumed d5 + falsifier; python-pure stack",
    }
    if framing_extra:
        framing.update(framing_extra)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    classify_counter: Counter[str] = Counter()
    n_closed = 0
    failed_tuples: List[Tuple[str, ...]] = []
    fail_breakdown: Dict[Tuple[str, ...], List[Dict[str, str]]] = {}
    tuple_outcomes: List[Dict[str, Any]] = []

    t0 = time.perf_counter()
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(framing) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

        for i, tup in enumerate(tuples):
            records, n_identity = evaluate_tuple_closure(tup, substrates)
            for rec in records:
                classify_counter[rec["output_form_classification"]] += 1
                fh.write(json.dumps(rec) + "\n")
            closed = (n_identity == N_CELLS_PER_TUPLE)
            tuple_outcomes.append({
                "tuple": list(tup),
                "n_identity_cells": n_identity,
                "closed": closed,
            })
            if closed:
                n_closed += 1
            else:
                failed_tuples.append(tup)
                failures = []
                for rec in records:
                    if rec["output_form_classification"] != "identity_attractor":
                        failures.append({
                            "substrate": rec["substrate_id"],
                            "ordering": rec["inspection_cascade_ordering"],
                            "classification": rec["output_form_classification"],
                        })
                fail_breakdown[tup] = failures

            # Flush every tuple — anti-stall.
            fh.flush()
            if (i + 1) % 25 == 0:
                os.fsync(fh.fileno())

            # Heartbeat.
            if (i + 1) % 50 == 0 or i == len(tuples) - 1:
                elapsed = time.perf_counter() - t0
                rate = (i + 1) / max(elapsed, 1e-9)
                eta = (len(tuples) - (i + 1)) / max(rate, 1e-9)
                print(f"  [{label}] {i+1}/{len(tuples)} tuples, "
                      f"{elapsed:.1f}s, ETA {eta:.0f}s, "
                      f"failed={len(failed_tuples)}", flush=True)

            # Early-exit gate for d5: if closure_rate drops below 0.90 after
            # first 250 tuples, stop.
            if depth == 5 and (i + 1) == 250:
                early_rate = n_closed / (i + 1)
                if early_rate < 0.90:
                    print(f"  [{label}] EARLY EXIT: rate={early_rate:.4f} after 250 tuples")
                    break

        wall = time.perf_counter() - t0
        closure_rate = n_closed / max(1, len(tuples))
        summary = {
            "spike": SPIKE_NUMBER,
            "date": SPIKE_DATE,
            "kind": "summary",
            "label": label,
            "stack_id": STACK_ID,
            "depth": depth,
            "n_tuples": len(tuples),
            "n_cells_total": len(tuples) * N_CELLS_PER_TUPLE,
            "n_tuples_closed": n_closed,
            "n_tuples_failed": len(failed_tuples),
            "closure_rate": closure_rate,
            "wall_seconds": wall,
            "classification_counts": dict(classify_counter),
            "failed_tuples": [list(t) for t in failed_tuples[:50]],
            "fail_breakdown_sample": {
                "_".join(t): fail_breakdown[t][:5] for t in failed_tuples[:20]
            },
        }
        fh.write(json.dumps(summary) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    print(f"[{label}] done: closure_rate={closure_rate:.4f} "
          f"({n_closed}/{len(tuples)}), wall={wall:.1f}s", flush=True)
    return summary, tuple_outcomes


def sample_external_falsifier(depth, n_samples, seed):
    rng = random.Random(seed)
    out = []
    seen = set()
    while len(out) < n_samples:
        tup = tuple(rng.choice(ex.CLASSES) for _ in range(depth))
        if all(c in SUBGROUP for c in tup):
            continue
        if tup in seen:
            continue
        seen.add(tup)
        out.append(tup)
    return out


def run_falsifier(substrates, out_path):
    """100 d2 + 100 d3 tuples touching COMPLEMENT. Sharp-boundary hypothesis:
    every such tuple should break identity_attractor on at least one cell."""
    d2_tuples = sample_external_falsifier(2, 100, SEED)
    d3_tuples = sample_external_falsifier(3, 100, SEED + 1)

    framing = {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "kind": "framing",
        "label": "external_falsifier",
        "stack_id": STACK_ID,
        "subgroup": list(SUBGROUP),
        "complement": list(COMPLEMENT),
        "n_d2": len(d2_tuples),
        "n_d3": len(d3_tuples),
        "anchor_citation": "Spike #138.1 external falsifier; mixed-subgroup tuples",
    }

    classify_counter: Counter[str] = Counter()
    sharp_boundary_violations = []
    n_full_identity = 0
    n_partial_identity = 0
    n_no_identity = 0
    tuple_outcomes = []

    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(framing) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

        for label, tuples in (("d2_falsifier", d2_tuples), ("d3_falsifier", d3_tuples)):
            for i, tup in enumerate(tuples):
                records, n_identity = evaluate_tuple_closure(tup, substrates)
                for rec in records:
                    classify_counter[rec["output_form_classification"]] += 1
                    fh.write(json.dumps(rec) + "\n")
                fully = (n_identity == N_CELLS_PER_TUPLE)
                partial = 0 < n_identity < N_CELLS_PER_TUPLE
                none_ = (n_identity == 0)
                tuple_outcomes.append({
                    "label": label,
                    "tuple": list(tup),
                    "n_identity_cells": n_identity,
                    "fully_identity": fully,
                    "partial_identity": partial,
                    "no_identity": none_,
                })
                if fully:
                    n_full_identity += 1
                elif partial:
                    n_partial_identity += 1
                else:
                    n_no_identity += 1
                if n_identity > 0:
                    identity_cells = [
                        f"{rec['substrate_id']}/{rec['inspection_cascade_ordering']}"
                        for rec in records
                        if rec["output_form_classification"] == "identity_attractor"
                    ]
                    sharp_boundary_violations.append({
                        "label": label,
                        "tuple": list(tup),
                        "n_identity_cells": n_identity,
                        "identity_cells_sample": identity_cells[:5],
                    })
                fh.flush()
                if (i + 1) % 25 == 0:
                    os.fsync(fh.fileno())
                    elapsed = time.perf_counter() - t0
                    print(f"  [{label}] {i+1}/{len(tuples)} tuples, {elapsed:.1f}s, "
                          f"violations={len(sharp_boundary_violations)}", flush=True)

        wall = time.perf_counter() - t0
        total = len(d2_tuples) + len(d3_tuples)
        summary = {
            "spike": SPIKE_NUMBER,
            "date": SPIKE_DATE,
            "kind": "summary",
            "label": "external_falsifier",
            "stack_id": STACK_ID,
            "n_tuples_total": total,
            "n_fully_identity": n_full_identity,
            "n_partial_identity": n_partial_identity,
            "n_no_identity": n_no_identity,
            "sharp_boundary_violations": len(sharp_boundary_violations),
            "wall_seconds": wall,
            "classification_counts": dict(classify_counter),
            "violations_sample": sharp_boundary_violations[:30],
        }
        fh.write(json.dumps(summary) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    print(f"[external_falsifier] full={n_full_identity}, partial={n_partial_identity}, "
          f"none={n_no_identity}, wall={wall:.1f}s", flush=True)
    return summary, tuple_outcomes


def main():
    print(f"spike138.1 d5+falsifier: stack_id={STACK_ID}", flush=True)
    print(f"spike138.1 d5+falsifier: HAS_NATIVE={ex._native.HAS_NATIVE}", flush=True)

    substrates = ex.build_substrates()

    # -------- d5 exhaustive --------
    d5_tuples = [t for t in product(SUBGROUP, repeat=5)]
    assert len(d5_tuples) == 3125
    d5_out = HERE / "spike138_1_d5_closure.ndjson"
    print(f"d5: {len(d5_tuples)} tuples = {len(d5_tuples)*25} cells "
          f"@ ~9ms/cell (python-pure estimate) = ~5 min", flush=True)
    d5_summary, _ = run_streaming("depth5_closure", d5_tuples, substrates, d5_out, 5)

    # -------- External falsifier --------
    falsifier_out = HERE / "spike138_1_external_falsifier.ndjson"
    print(f"falsifier: 200 tuples = 5000 cells @ ~9ms/cell = ~45 sec", flush=True)
    falsifier_summary, _ = run_falsifier(substrates, falsifier_out)

    # -------- Overall summary --------
    overall = {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "kind": "overall_summary",
        "stack_id": STACK_ID,
        "subgroup": list(SUBGROUP),
        "d5_summary": d5_summary,
        "external_falsifier_summary": falsifier_summary,
        "d5_closure_rate": d5_summary["closure_rate"],
        "boundary_sharp": (falsifier_summary["sharp_boundary_violations"] == 0),
    }
    if d5_summary["closure_rate"] >= 0.999:
        verdict = "STRONG_CLOSURE_D5"
    elif d5_summary["closure_rate"] >= 0.90:
        verdict = "PARTIAL_CLOSURE_D5"
    else:
        verdict = "CLOSURE_BREAKDOWN_D5"
    overall["verdict"] = verdict

    summary_out = HERE / "spike138_1_d5_and_falsifier_summary.ndjson"
    with open(summary_out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps({"spike": SPIKE_NUMBER, "date": SPIKE_DATE,
                             "kind": "framing", "verdict_summary": verdict}) + "\n")
        fh.write(json.dumps(overall) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    print(f"\nspike138.1 verdict: {verdict}")
    print(f"  d5 closure_rate: {d5_summary['closure_rate']:.6f}")
    print(f"  falsifier sharp_boundary_violations: "
          f"{falsifier_summary['sharp_boundary_violations']}/200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
