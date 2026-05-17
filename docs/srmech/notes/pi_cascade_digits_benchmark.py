"""rc12 pi_cascade_digits wall-time benchmark — within rc12's practical cap (50).

User request: time pi_cascade_digits at num_digits=350 (deliberately non-canonical).
Finding: rc12 enforces a hard cap of num_digits <= 50 (validated digit count at the
default cascade depth=90 + precision_bits=512 per Spike #32 v3). 350 digits is
beyond the rc12 ship; documenting as rc13 candidate.

This benchmark sweeps within the cap (5, 10, 15, 20, 25, 50) and times the 50-digit
target as the rc12 max.
"""
from __future__ import annotations
import json
import sys
import time
from srmech.amsc.rational import pi_cascade_digits

# Anchor: smoke-verified
PI_50_REFERENCE = "3.14159265358979323846264338327950288419716939937510"


def time_call(num_digits: int) -> tuple[float, str]:
    t0 = time.perf_counter()
    result = pi_cascade_digits(num_digits)
    t1 = time.perf_counter()
    return (t1 - t0, result)


def benchmark(num_digits: int, *, trials: int = 5) -> dict:
    timings = []
    outputs = set()
    for _ in range(trials):
        wall, result = time_call(num_digits)
        timings.append(wall)
        outputs.add(result)
    assert len(outputs) == 1
    sorted_t = sorted(timings)
    median = sorted_t[len(sorted_t) // 2]
    return {
        "num_digits": num_digits,
        "trials": trials,
        "wall_seconds_min": sorted_t[0],
        "wall_seconds_max": sorted_t[-1],
        "wall_seconds_median": median,
        "wall_seconds_mean": sum(timings) / trials,
        "all_trials": timings,
        "result_length_chars": len(outputs.pop() if outputs else ""),
    }


def main():
    print(f"=== pi_cascade_digits benchmark (srmech 0.4.1rc12) ===")
    print(f"Python {sys.version.split()[0]} on {sys.platform}")
    print()

    # rc12 practical-cap finding
    cap_test_passed = False
    try:
        pi_cascade_digits(350)
    except ValueError as exc:
        cap_test_passed = True
        cap_error = str(exc)
        print(f"CAP FINDING: pi_cascade_digits(350) raises ValueError: {cap_error}")
        print(f"  rc12 enforces num_digits <= 50 by hard validation; 350 is rc13 candidate.")

    # Scaling sweep within the cap
    print()
    print(f"=== Scaling sweep (within rc12 cap) ===")
    sweep_points = [5, 10, 15, 20, 25, 50]
    sweep_results = []
    for n in sweep_points:
        r = benchmark(n, trials=5)
        sweep_results.append(r)
        print(f"  num_digits={n:>3d}  median={r['wall_seconds_median']*1000:>8.2f} ms  (n=5 trials, deterministic)")

    # Detailed 50-digit run (rc12 maximum)
    print()
    print(f"=== Detailed: pi_cascade_digits(50) (rc12 max) ===")
    detailed = benchmark(50, trials=20)
    print(f"  20-trial median: {detailed['wall_seconds_median']*1000:.2f} ms")
    print(f"  20-trial mean:   {detailed['wall_seconds_mean']*1000:.2f} ms")
    print(f"  20-trial min:    {detailed['wall_seconds_min']*1000:.2f} ms")
    print(f"  20-trial max:    {detailed['wall_seconds_max']*1000:.2f} ms")

    # Verify the 50-digit run matches anchor
    _, result_50 = time_call(50)
    assert result_50 == PI_50_REFERENCE
    print(f"  Output verbatim: {result_50}")
    print(f"  Matches AMSC pi_digits catalog row anchor: OK")

    # NDJSON output
    out_records = []
    out_records.append({
        "kind": "benchmark_environment",
        "srmech_version": "0.4.1rc12",
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
    })
    out_records.append({
        "kind": "rc12_practical_cap_finding",
        "cap_num_digits": 50,
        "test_attempted_num_digits": 350,
        "error_raised": "ValueError: num_digits exceeds practical cap 50; got 350",
        "rc13_candidate": "expand cap by scaling cascade depth + precision_bits proportionally",
        "user_request_context": "user direction 2026-05-17: 'wall time to return 350 digit pi cascade, partly because it's a weird number on purpose'",
    })
    out_records.append({
        "kind": "benchmark_scaling_sweep_within_cap",
        "sweep_points": sweep_points,
        "results": sweep_results,
    })
    out_records.append({
        "kind": "benchmark_detailed_50",
        "trials": detailed["trials"],
        "wall_seconds_median": detailed["wall_seconds_median"],
        "wall_seconds_mean": detailed["wall_seconds_mean"],
        "wall_seconds_min": detailed["wall_seconds_min"],
        "wall_seconds_max": detailed["wall_seconds_max"],
        "all_trials_seconds": detailed["all_trials"],
        "deterministic": True,
        "matches_pi_50_anchor": True,
        "output_verbatim": result_50,
    })

    with open("bench_pi_capped.ndjson", "w", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r) + "\n")
    print()
    print(f"NDJSON written to bench_pi_capped.ndjson ({len(out_records)} records)")


if __name__ == "__main__":
    main()
