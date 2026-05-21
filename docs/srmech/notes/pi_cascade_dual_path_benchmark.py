"""Spike #184 — pi_cascade dual-path dogfood benchmark (2026-05-19).

Re-runs the existing pi_cascade_digits algebra-based benchmark via the
srmech.signal_processing dual-path infrastructure (Phase 1-4 shipped on
the feat branch; v0.4.2rc4). Compares Path A (closed-form algebra) vs.
Path B (RBS-HDC instrument substrate-identity verification) and
exercises the cascade dispatcher's default routing + begin_cascade
context-manager preferential routing.

Per ``[[user_stance_pi_as_projection]]`` (pi is cascade-emergent
projection from integer-cyclic substrate per Spike #32) +
``[[user_stance_identity_not_implementation_discipline]]`` (both paths
INSTANTIATE the same algebra; D1 algebra-content bit-exact identity).

Discipline anchors
------------------
- 14 A-N intact per ``[[feedback_no_privileged_primitive_classes]]`` —
  no new class promotion; Path B composes Class K (rotation) + Class M
  (HDC bind) over the same Class N/I/C cascade composition.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]`` — D1
  algebra-identity bit-exact across paths.
- Trauma-informed defensive scope — math methodology research only.
- NDJSON output per ``[[feedback_ndjson_over_bloated_json]]``.
- Computational provenance per
  ``[[feedback_computational_provenance_discipline]]`` — committed
  reproducible code.

Coverage
--------
- num_digits ∈ {10, 50, 100, 500, 1000} (rc13 cap = 1000).
- 5 dispatch modes per cell:
    1. Path A only (``dispatch(... path='A')``).
    2. Path B only (``dispatch(... path='B')``).
    3. Default routing (``dispatch(...)``); records picked-path.
    4. Cascade-hint routing (``with begin_cascade(): dispatch(...)``);
       records picked-path.
    5. D1 equivalence check (Path A output == Path B output).

Per-cell wall-time captured at 5-trial median per
``pi_cascade_digits_benchmark.py`` (2026-05-17) convention.

Reference π digits (first 1000 places) for accuracy verification:
sourced from the canonical AMSC ``pi_digits`` catalog row at
num_digits=1000 (rc13 anchor).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure we use the in-worktree srmech (not whatever's installed).
# This file lives at docs/srmech/notes/...; parents[1] = docs/srmech,
# so docs/srmech/python is the package root.
_WORKTREE_PYTHON = Path(__file__).resolve().parents[1] / "python"
if str(_WORKTREE_PYTHON) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_PYTHON))

import srmech  # noqa: E402
from srmech.signal_processing import (  # noqa: E402
    DEFAULT_PATH_PER_CLASS,
    begin_cascade,
    current_cascade,
    dispatch,
    lookup,
    resolve_path,
)
from srmech.signal_processing._paths import PATH_A, PATH_B  # noqa: E402

# Reference π to 1000 digits (sourced from canonical math; verified via
# srmech's existing pi_cascade_digits at 1000 digits with rc13 auto-
# scaling — used here ONLY as a Path-independent reference for digit-
# accuracy comparison. The 1000-digit Path A output is itself the
# reference at lower num_digits, and we cross-check both paths against
# it for D1 algebra identity.)
#
# Reference is computed once at script-startup using Path A pi_cascade_digits
# directly (NOT via dispatch — we want a clean ground-truth anchor
# independent of the dispatcher).
from srmech.amsc.rational import pi_cascade_digits as _amsc_pi_cascade  # noqa: E402

NUM_DIGIT_CELLS: Tuple[int, ...] = (10, 50, 100, 500, 1000)
TRIALS_PER_CELL: int = 5


def time_call(fn, *args, **kwargs) -> Tuple[float, str]:
    """Run fn once; return (wall_seconds, result)."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    t1 = time.perf_counter()
    return (t1 - t0, result)


def benchmark_path(
    num_digits: int,
    *,
    path: str,
    trials: int = TRIALS_PER_CELL,
) -> Dict:
    """Run ``dispatch('pi_cascade', num_digits, path=path)`` n trials.

    Returns timing stats + the (deterministic) output string.
    """
    timings: List[float] = []
    outputs = set()
    for _ in range(trials):
        wall, result = time_call(dispatch, "pi_cascade", num_digits, path=path)
        timings.append(wall)
        outputs.add(result)
    assert len(outputs) == 1, (
        f"non-deterministic output on path={path} num_digits={num_digits}: "
        f"{len(outputs)} distinct results"
    )
    sorted_t = sorted(timings)
    median = sorted_t[len(sorted_t) // 2]
    return {
        "num_digits": num_digits,
        "path": path,
        "trials": trials,
        "wall_seconds_min": sorted_t[0],
        "wall_seconds_max": sorted_t[-1],
        "wall_seconds_median": median,
        "wall_seconds_mean": sum(timings) / trials,
        "all_trials_seconds": timings,
        "result": outputs.pop(),
        "deterministic": True,
    }


def benchmark_default(num_digits: int) -> Dict:
    """Default dispatch (no path= kwarg); record which path was chosen.

    Uses ``resolve_path`` directly to capture the routing decision; then
    calls ``dispatch`` once to record the wall-time on the chosen path.
    """
    chosen_path = resolve_path("pi_cascade", explicit_path=None)
    wall, result = time_call(dispatch, "pi_cascade", num_digits)
    return {
        "num_digits": num_digits,
        "dispatch_mode": "default",
        "picked_path": chosen_path,
        "wall_seconds": wall,
        "result": result,
    }


def benchmark_cascade(num_digits: int) -> Dict:
    """Cascade-hint dispatch (inside begin_cascade context).

    Per cascade_dispatcher.resolve_path: an active cascade context
    forces PATH_B regardless of class. Records both the resolved path
    AND the wall-time inside the context.
    """
    with begin_cascade(substrate=None) as ctx:
        chosen_path = resolve_path("pi_cascade", explicit_path=None)
        wall, result = time_call(dispatch, "pi_cascade", num_digits)
        cascade_active = ctx is current_cascade()
    return {
        "num_digits": num_digits,
        "dispatch_mode": "cascade",
        "picked_path": chosen_path,
        "cascade_active_during_call": cascade_active,
        "wall_seconds": wall,
        "result": result,
    }


def digit_accuracy(result: str, reference: str) -> int:
    """Return number of leading digits (after '3.') that match reference.

    Both strings start with "3." then the decimal expansion. We count
    characters matching from index 2 onward until first mismatch.
    """
    # Strip "3." prefix on both for comparison.
    assert result.startswith("3."), f"result missing '3.' prefix: {result[:20]!r}"
    assert reference.startswith("3."), (
        f"reference missing '3.' prefix: {reference[:20]!r}"
    )
    r = result[2:]
    g = reference[2:]
    n = min(len(r), len(g))
    matches = 0
    for i in range(n):
        if r[i] == g[i]:
            matches += 1
        else:
            break
    return matches


def main():
    print(f"=== Spike #184 pi_cascade dual-path benchmark ===")
    print(f"srmech: {srmech.__version__}")
    print(f"Python {sys.version.split()[0]} on {sys.platform}")
    print()

    # Reference computation (Path A direct, not via dispatch — clean anchor).
    print("Computing reference (Path A pi_cascade_digits at 1000 digits)...")
    t_ref0 = time.perf_counter()
    reference = _amsc_pi_cascade(1000)
    t_ref1 = time.perf_counter()
    print(
        f"Reference computed in {(t_ref1 - t_ref0) * 1000:.2f} ms "
        f"(length {len(reference)} chars, starts {reference[:32]}...)"
    )
    print()

    # Inspect the registered classes + default routing for pi_cascade.
    entry = lookup("pi_cascade")
    classes_str = "".join(entry.classes)
    default_path_for_class = DEFAULT_PATH_PER_CLASS.get(entry.classes[0], "A")
    print(f"pi_cascade registry entry:")
    print(f"  classes = {entry.classes} (composition string: {classes_str})")
    print(
        f"  primary class = {entry.classes[0]} -> default routes to path "
        f"{default_path_for_class}"
    )
    print(f"  Path A impl: {entry.path_a.__module__}.{entry.path_a.__name__}")
    print(f"  Path B impl: {entry.path_b.__module__}.{entry.path_b.__name__}")
    print()

    out_records: List[Dict] = []
    out_records.append({
        "kind": "benchmark_environment",
        "spike": "184",
        "date": "2026-05-19",
        "srmech_version": srmech.__version__,
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "branch": "research/spike-184-pi-cascade-dual-path-rerun",
        "num_digit_cells": list(NUM_DIGIT_CELLS),
        "trials_per_cell": TRIALS_PER_CELL,
    })
    out_records.append({
        "kind": "pi_cascade_registry_inspection",
        "op_name": entry.op_name,
        "classes": list(entry.classes),
        "primary_class": entry.classes[0],
        "default_path_per_primary_class": default_path_for_class,
        "path_a_impl_module": entry.path_a.__module__,
        "path_b_impl_module": entry.path_b.__module__,
        "ssot_citation": entry.ssot_citation,
    })

    # Per-cell sweep: Path A only, Path B only, default, cascade-hint.
    print("=== Per-cell dual-path sweep ===")
    print(
        f"{'num_digits':>10}  {'A median ms':>12}  {'B median ms':>12}  "
        f"{'default ms':>10}  {'cascade ms':>10}  {'D1=':>4}"
    )
    for nd in NUM_DIGIT_CELLS:
        a_stats = benchmark_path(nd, path="A")
        b_stats = benchmark_path(nd, path="B")
        default_stats = benchmark_default(nd)
        cascade_stats = benchmark_cascade(nd)
        # D1 algebra-identity equivalence: Path A bit-exact == Path B?
        d1_pass = a_stats["result"] == b_stats["result"]
        # Cross-check: both paths match reference to num_digits accuracy.
        a_acc = digit_accuracy(a_stats["result"], reference)
        b_acc = digit_accuracy(b_stats["result"], reference)
        # Default + cascade should agree with A path output:
        default_d1 = default_stats["result"] == a_stats["result"]
        cascade_d1 = cascade_stats["result"] == a_stats["result"]
        print(
            f"{nd:>10d}  {a_stats['wall_seconds_median']*1000:>12.2f}  "
            f"{b_stats['wall_seconds_median']*1000:>12.2f}  "
            f"{default_stats['wall_seconds']*1000:>10.2f}  "
            f"{cascade_stats['wall_seconds']*1000:>10.2f}  "
            f"{'PASS' if d1_pass else 'FAIL':>4}"
        )

        out_records.append({
            "kind": "cell_path_A",
            "num_digits": nd,
            **{k: v for k, v in a_stats.items() if k != "path"},
            "digit_accuracy_vs_reference": a_acc,
        })
        out_records.append({
            "kind": "cell_path_B",
            "num_digits": nd,
            **{k: v for k, v in b_stats.items() if k != "path"},
            "digit_accuracy_vs_reference": b_acc,
        })
        out_records.append({
            "kind": "cell_default_routing",
            **default_stats,
            "matches_path_A_output": default_d1,
        })
        out_records.append({
            "kind": "cell_cascade_routing",
            **cascade_stats,
            "matches_path_A_output": cascade_d1,
        })
        out_records.append({
            "kind": "cell_d1_equivalence",
            "num_digits": nd,
            "path_a_eq_path_b": d1_pass,
            "default_eq_path_a": default_d1,
            "cascade_eq_path_a": cascade_d1,
            "path_a_digit_accuracy": a_acc,
            "path_b_digit_accuracy": b_acc,
            "path_a_output_first_64": a_stats["result"][:64],
            "path_b_output_first_64": b_stats["result"][:64],
        })

    # Aggregate D1 verdict + performance comparison.
    print()
    print("=== Aggregate verdicts ===")
    d1_all_pass = all(
        r["path_a_eq_path_b"]
        for r in out_records
        if r.get("kind") == "cell_d1_equivalence"
    )
    print(f"D1 algebra-identity (Path A == Path B): {'PASS' if d1_all_pass else 'FAIL'}")

    # Path B/A timing ratio at largest cell.
    a_records = {r["num_digits"]: r for r in out_records if r.get("kind") == "cell_path_A"}
    b_records = {r["num_digits"]: r for r in out_records if r.get("kind") == "cell_path_B"}
    print()
    print(f"{'num_digits':>10}  {'B/A ratio':>10}  {'B-A delta ms':>14}")
    for nd in NUM_DIGIT_CELLS:
        a_med = a_records[nd]["wall_seconds_median"]
        b_med = b_records[nd]["wall_seconds_median"]
        ratio = b_med / a_med if a_med > 0 else float("inf")
        delta_ms = (b_med - a_med) * 1000
        print(f"{nd:>10d}  {ratio:>10.3f}  {delta_ms:>14.3f}")
        out_records.append({
            "kind": "ratio_path_b_over_path_a",
            "num_digits": nd,
            "path_a_median_seconds": a_med,
            "path_b_median_seconds": b_med,
            "ratio_b_over_a": ratio,
            "delta_ms_b_minus_a": delta_ms,
        })

    # Default-path picked verdicts.
    print()
    print("=== Default-path routing verdicts ===")
    default_picked = {
        r["num_digits"]: r["picked_path"]
        for r in out_records
        if r.get("kind") == "cell_default_routing"
    }
    cascade_picked = {
        r["num_digits"]: r["picked_path"]
        for r in out_records
        if r.get("kind") == "cell_cascade_routing"
    }
    print(
        f"Default routing: pi_cascade primary class {entry.classes[0]} -> "
        f"DEFAULT_PATH_PER_CLASS = {default_path_for_class}"
    )
    print(f"Default picked paths per cell: {default_picked}")
    print(f"Cascade-hint picked paths per cell: {cascade_picked}")
    out_records.append({
        "kind": "default_routing_verdict",
        "primary_class": entry.classes[0],
        "default_path_per_class_table_entry": default_path_for_class,
        "default_picked_per_cell": default_picked,
        "cascade_picked_per_cell": cascade_picked,
        "default_routing_consistent_with_table": all(
            p == default_path_for_class for p in default_picked.values()
        ),
        "cascade_routing_flips_to_path_B": all(
            p == PATH_B for p in cascade_picked.values()
        ),
    })

    # Final aggregate D1 + performance record.
    out_records.append({
        "kind": "aggregate_d1_verdict",
        "d1_path_a_eq_path_b_all_cells": d1_all_pass,
        "num_cells_passing": sum(
            1 for r in out_records
            if r.get("kind") == "cell_d1_equivalence" and r["path_a_eq_path_b"]
        ),
        "total_cells": len(NUM_DIGIT_CELLS),
        "discipline_anchor": "[[user_stance_identity_not_implementation_discipline]]",
        "spike_anchor": "184",
    })

    # Write NDJSON output.
    output_path = Path(__file__).resolve().parent / (
        "spike184_pi_cascade_dual_path_records_2026-05-19.ndjson"
    )
    with output_path.open("w", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r) + "\n")
    print()
    print(f"NDJSON written to {output_path.name} ({len(out_records)} records)")


if __name__ == "__main__":
    main()
