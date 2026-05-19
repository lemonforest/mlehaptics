"""Spike #138.1 — Depth-4 / Depth-5 closure verification of {B, D, E, F, L}
identity-attractor subgroup.

Method extends spike138_explorer.py:
  - Depth-4 EXHAUSTIVE: all 5^4 = 625 ordered tuples drawn from {B, D, E, F, L}
  - Depth-5 EXHAUSTIVE: all 5^5 = 3,125 ordered tuples drawn from {B, D, E, F, L}
  - 5 substrates x 5 inspection orderings per tuple = 25 cells per tuple
  - External falsifier: 100 random d2 + 100 random d3 tuples touching {A,C,G,H,I,J,K,M,N}

Per the spike brief, "closure" requires every tuple to yield identity_attractor
on every (substrate, inspection_ordering) combination.

Outputs:
  spike138_1_d4_closure.ndjson    -- per-cell records for d4 (15,625 cells)
  spike138_1_d5_closure.ndjson    -- per-cell records for d5 (78,125 cells)
  spike138_1_external_falsifier.ndjson
  spike138_1_summary.ndjson       -- aggregate verdicts

Run:
  python notes/spike138_1_closure_verifier.py [--skip-d5] [--stack-id python+c]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(HERE))

import spike138_explorer as ex


SPIKE_NUMBER = "138.1"
SPIKE_DATE = "2026-05-18"

# Subgroup under test.
SUBGROUP = ("B", "D", "E", "F", "L")
# Complement classes for external falsifier.
COMPLEMENT = tuple(c for c in ex.CLASSES if c not in SUBGROUP)  # A, C, G, H, I, J, K, M, N

# Reuse exploration infrastructure.
INSPECTION_ORDERINGS = ex.INSPECTION_ORDERINGS
N_SUBSTRATES = 5
N_ORDERINGS = 5
N_CELLS_PER_TUPLE = N_SUBSTRATES * N_ORDERINGS  # 25


def enumerate_subgroup_at_depth(depth: int, subgroup: Sequence[str]) -> List[Tuple[str, ...]]:
    """All ordered N-tuples drawn from subgroup."""
    return [t for t in product(subgroup, repeat=depth)]


def sample_external_falsifier(
    depth: int,
    n_samples: int,
    seed: int,
) -> List[Tuple[str, ...]]:
    """Random tuples that include at least one class from COMPLEMENT.

    These probe the subgroup boundary: hypothesis is that any tuple touching
    outside {B,D,E,F,L} breaks the identity-attractor outcome.
    """
    rng = random.Random(seed)
    out: List[Tuple[str, ...]] = []
    seen: set[Tuple[str, ...]] = set()
    while len(out) < n_samples:
        tup = tuple(rng.choice(ex.CLASSES) for _ in range(depth))
        # Reject if entirely inside SUBGROUP.
        if all(c in SUBGROUP for c in tup):
            continue
        if tup in seen:
            continue
        seen.add(tup)
        out.append(tup)
    return out


def evaluate_tuple_closure(
    tup: Tuple[str, ...],
    substrates: Dict[str, Dict[str, Any]],
    seed: int,
    stack_id: str,
) -> Tuple[List[Dict[str, Any]], int]:
    """Run all 25 (substrate, ordering) cells for a single tuple.

    Returns (per_cell_records, n_identity_cells).
    """
    records: List[Dict[str, Any]] = []
    n_identity = 0
    for sub_id, sub in substrates.items():
        for ins_name, ins_cas in INSPECTION_ORDERINGS.items():
            rec = ex.run_cell(tup, sub, ins_name, ins_cas, seed, stack_id)
            # Trim per-class timing to keep NDJSON compact (per #138 d4/d5 scale).
            rec.pop("per_class_timing_ns", None)
            rec.pop("total_elapsed_ns", None)
            records.append(rec)
            if rec["output_form_classification"] == "identity_attractor":
                n_identity += 1
    return records, n_identity


def write_cell_records(
    out_path: Path,
    framing: Dict[str, Any],
    records: List[Dict[str, Any]],
    summary: Dict[str, Any],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(framing) + "\n")
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
        fh.write(json.dumps(summary) + "\n")


def run_closure(
    depth: int,
    tuples: List[Tuple[str, ...]],
    substrates: Dict[str, Dict[str, Any]],
    seed: int,
    stack_id: str,
    out_path: Path,
    label: str,
) -> Dict[str, Any]:
    """Run closure verification for a set of tuples at given depth.

    Returns aggregate summary dict for the run.
    """
    total_cells = len(tuples) * N_CELLS_PER_TUPLE
    print(f"[{label}] depth={depth}, tuples={len(tuples)}, cells={total_cells}")

    framing = {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "kind": "framing",
        "stack_id": stack_id,
        "label": label,
        "depth": depth,
        "n_tuples": len(tuples),
        "n_cells": total_cells,
        "subgroup": list(SUBGROUP),
        "has_native": bool(ex._native.HAS_NATIVE),
        "native_abi": int(ex._native.NATIVE_ABI_VERSION or 0),
        "n_substrates": N_SUBSTRATES,
        "n_inspection_orderings": N_ORDERINGS,
        "fixed_point_threshold": ex.FIXED_POINT_THRESHOLD,
        "inspection_depth_cap": ex.INSPECTION_DEPTH_CAP,
        "anchor_citation": "Spike #138.1; closure verification of {B,D,E,F,L} subgroup",
    }

    all_records: List[Dict[str, Any]] = []
    tuple_outcomes: List[Dict[str, Any]] = []
    classify_counter: Counter[str] = Counter()
    failed_tuples: List[Tuple[str, ...]] = []
    fail_breakdown: Dict[Tuple[str, ...], List[Dict[str, str]]] = {}

    t0 = time.perf_counter()
    for i, tup in enumerate(tuples):
        records, n_identity = evaluate_tuple_closure(tup, substrates, seed, stack_id)
        all_records.extend(records)
        for rec in records:
            classify_counter[rec["output_form_classification"]] += 1

        # Closure verdict per tuple.
        closed = (n_identity == N_CELLS_PER_TUPLE)
        tuple_outcomes.append({
            "tuple": list(tup),
            "n_identity_cells": n_identity,
            "n_total_cells": N_CELLS_PER_TUPLE,
            "closed": closed,
        })
        if not closed:
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

        if (i + 1) % 100 == 0:
            elapsed = time.perf_counter() - t0
            rate = (i + 1) / max(elapsed, 1e-9)
            eta = (len(tuples) - (i + 1)) / max(rate, 1e-9)
            print(f"  [{label}] {i+1}/{len(tuples)} tuples, "
                  f"{elapsed:.1f}s, ETA {eta:.0f}s, "
                  f"failed={len(failed_tuples)}")

    wall = time.perf_counter() - t0

    # Closure rate.
    closed_count = sum(1 for o in tuple_outcomes if o["closed"])
    closure_rate = closed_count / max(1, len(tuples))

    summary = {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "kind": "summary",
        "label": label,
        "stack_id": stack_id,
        "depth": depth,
        "n_tuples": len(tuples),
        "n_cells_total": total_cells,
        "n_tuples_closed": closed_count,
        "n_tuples_failed": len(failed_tuples),
        "closure_rate": closure_rate,
        "wall_seconds": wall,
        "classification_counts": dict(classify_counter),
        "failed_tuples": [list(t) for t in failed_tuples[:50]],
        "fail_breakdown_sample": {
            "_".join(t): fail_breakdown[t][:5] for t in failed_tuples[:20]
        },
    }
    write_cell_records(out_path, framing, all_records, summary)
    print(f"[{label}] done: closure_rate={closure_rate:.4f} "
          f"({closed_count}/{len(tuples)}), wall={wall:.1f}s")
    print(f"  wrote {len(all_records)} cells to {out_path}")
    return summary


def run_external_falsifier(
    substrates: Dict[str, Dict[str, Any]],
    seed: int,
    stack_id: str,
    out_path: Path,
) -> Dict[str, Any]:
    """Test 100 d2 + 100 d3 tuples touching {A,C,G,H,I,J,K,M,N}.

    Hypothesis: any tuple touching outside the subgroup BREAKS identity-attractor.
    """
    d2_tuples = sample_external_falsifier(2, 100, seed)
    d3_tuples = sample_external_falsifier(3, 100, seed + 1)

    print(f"[external_falsifier] d2 tuples={len(d2_tuples)}, d3 tuples={len(d3_tuples)}")

    framing = {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "kind": "framing",
        "label": "external_falsifier",
        "stack_id": stack_id,
        "subgroup": list(SUBGROUP),
        "complement": list(COMPLEMENT),
        "n_d2": len(d2_tuples),
        "n_d3": len(d3_tuples),
        "anchor_citation": "Spike #138.1 external falsifier; mixed-subgroup tuples",
    }

    all_records: List[Dict[str, Any]] = []
    tuple_outcomes: List[Dict[str, Any]] = []
    # External-falsifier-positive: tuple touches COMPLEMENT AND still yields
    # identity_attractor on >=1 (substrate, ordering). Sharp-boundary hypothesis
    # predicts zero such cases (any complement-touching tuple disrupts identity).
    sharp_boundary_violations = []
    classify_counter: Counter[str] = Counter()

    t0 = time.perf_counter()
    for label, tuples in (("d2_falsifier", d2_tuples), ("d3_falsifier", d3_tuples)):
        for tup in tuples:
            records, n_identity = evaluate_tuple_closure(tup, substrates, seed, stack_id)
            all_records.extend(records)
            for rec in records:
                classify_counter[rec["output_form_classification"]] += 1
            tuple_outcomes.append({
                "label": label,
                "tuple": list(tup),
                "n_identity_cells": n_identity,
                "n_total_cells": N_CELLS_PER_TUPLE,
                "fully_identity": n_identity == N_CELLS_PER_TUPLE,
                "partial_identity": 0 < n_identity < N_CELLS_PER_TUPLE,
                "no_identity": n_identity == 0,
            })
            if n_identity > 0:
                # Any complement-touching tuple yielding ANY identity_attractor
                # cell is a sharp-boundary violation.
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

    wall = time.perf_counter() - t0
    total_tuples = len(d2_tuples) + len(d3_tuples)
    n_full_identity = sum(1 for o in tuple_outcomes if o["fully_identity"])
    n_partial_identity = sum(1 for o in tuple_outcomes if o["partial_identity"])
    n_no_identity = sum(1 for o in tuple_outcomes if o["no_identity"])

    summary = {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "kind": "summary",
        "label": "external_falsifier",
        "stack_id": stack_id,
        "n_tuples_total": total_tuples,
        "n_fully_identity": n_full_identity,
        "n_partial_identity": n_partial_identity,
        "n_no_identity": n_no_identity,
        "sharp_boundary_violations": len(sharp_boundary_violations),
        "wall_seconds": wall,
        "classification_counts": dict(classify_counter),
        "violations_sample": sharp_boundary_violations[:30],
    }
    write_cell_records(out_path, framing, all_records, summary)
    print(f"[external_falsifier] full_identity={n_full_identity}, "
          f"partial={n_partial_identity}, none={n_no_identity}, "
          f"wall={wall:.1f}s")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-d5", action="store_true", help="Run d4 only (skip d5)")
    ap.add_argument("--skip-falsifier", action="store_true", help="Run closure only")
    ap.add_argument("--stack-id", default="python+c")
    ap.add_argument("--seed", type=int, default=138)
    ap.add_argument("--d4-out", default=str(HERE / "spike138_1_d4_closure.ndjson"))
    ap.add_argument("--d5-out", default=str(HERE / "spike138_1_d5_closure.ndjson"))
    ap.add_argument("--falsifier-out",
                    default=str(HERE / "spike138_1_external_falsifier.ndjson"))
    ap.add_argument("--summary-out",
                    default=str(HERE / "spike138_1_summary.ndjson"))
    args = ap.parse_args()

    print(f"spike138.1: stack_id={args.stack_id}, seed={args.seed}")
    print(f"spike138.1: subgroup={SUBGROUP}, complement={COMPLEMENT}")
    print(f"spike138.1: HAS_NATIVE={ex._native.HAS_NATIVE}, ABI={ex._native.NATIVE_ABI_VERSION}")

    substrates = ex.build_substrates()

    # ----- Depth-4 exhaustive -----
    d4_tuples = enumerate_subgroup_at_depth(4, SUBGROUP)
    assert len(d4_tuples) == 5 ** 4 == 625
    d4_summary = run_closure(
        depth=4,
        tuples=d4_tuples,
        substrates=substrates,
        seed=args.seed,
        stack_id=args.stack_id,
        out_path=Path(args.d4_out),
        label="depth4_closure",
    )

    # Early-exit gate per brief: if d4 closure breaks >10%, STOP.
    if d4_summary["closure_rate"] < 0.90:
        print(f"\n*** EARLY EXIT: d4 closure rate = {d4_summary['closure_rate']:.4f} "
              f"(<0.90). Stopping per spike brief.")
        write_cell_records(
            Path(args.summary_out),
            framing={"spike": SPIKE_NUMBER, "date": SPIKE_DATE, "kind": "framing",
                     "verdict": "EARLY_EXIT_D4_BREAKS"},
            records=[],
            summary={
                "spike": SPIKE_NUMBER, "date": SPIKE_DATE, "kind": "summary",
                "verdict": "EARLY_EXIT_D4_BREAKS",
                "d4_summary": d4_summary,
            },
        )
        return 0

    # ----- Depth-5 exhaustive (unless skipped) -----
    d5_summary = None
    if not args.skip_d5:
        d5_tuples = enumerate_subgroup_at_depth(5, SUBGROUP)
        assert len(d5_tuples) == 5 ** 5 == 3125
        d5_summary = run_closure(
            depth=5,
            tuples=d5_tuples,
            substrates=substrates,
            seed=args.seed,
            stack_id=args.stack_id,
            out_path=Path(args.d5_out),
            label="depth5_closure",
        )

    # ----- External falsifier -----
    falsifier_summary = None
    if not args.skip_falsifier:
        falsifier_summary = run_external_falsifier(
            substrates=substrates,
            seed=args.seed,
            stack_id=args.stack_id,
            out_path=Path(args.falsifier_out),
        )

    # ----- Overall summary -----
    overall = {
        "spike": SPIKE_NUMBER,
        "date": SPIKE_DATE,
        "kind": "overall_summary",
        "stack_id": args.stack_id,
        "subgroup": list(SUBGROUP),
        "d4_summary": d4_summary,
        "d5_summary": d5_summary,
        "external_falsifier_summary": falsifier_summary,
    }
    # Verdict logic.
    d4_strong = d4_summary["closure_rate"] >= 0.999
    d5_strong = (d5_summary is not None
                 and d5_summary["closure_rate"] >= 0.999)
    boundary_sharp = (falsifier_summary is not None
                      and falsifier_summary["sharp_boundary_violations"] == 0)
    if d4_strong and d5_strong:
        verdict = "STRONG_CLOSURE"
    elif d4_strong and (d5_summary is None or d5_summary["closure_rate"] >= 0.90):
        verdict = "PARTIAL_CLOSURE"
    else:
        verdict = "CLOSURE_BREAKDOWN"
    overall["verdict"] = verdict
    overall["boundary_sharp"] = boundary_sharp

    write_cell_records(
        Path(args.summary_out),
        framing={"spike": SPIKE_NUMBER, "date": SPIKE_DATE, "kind": "framing",
                 "verdict_summary": verdict},
        records=[],
        summary=overall,
    )
    print(f"\nspike138.1 overall verdict: {verdict}")
    print(f"  boundary sharp: {boundary_sharp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
