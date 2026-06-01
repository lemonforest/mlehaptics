"""runaway_partition_reading.py — the STRUCTURE of a "runaway" (framework-reading, 2026-06-02).

A framework-reading LENS, NOT a disease model and NOT a route to intervention. User
scope (honored): "not how to cure/reverse cancer/ALS/cerebral palsy -- how to understand
what is happening at the partitions that cause such run aways."

The reading: a healthy partition holds a cascade at its CODEWORD (the bounded/regulated
state) via an intrinsic correction -- the parity-check (F259/F260) / the Class-K pin-slot
boundary. A RUNAWAY = that correction FAILING, so the ordinary perturbations that are
always present stop being absorbed and instead ACCUMULATE UNBOUNDED. The structural point:
the runaway is the ABSENCE of the bounding correction, not an added force.

This toy shows ONLY that abstract structure: the SAME perturbations, with the correction
(bounded) vs without it (runs away). It says nothing about any disease's mechanism or
treatment -- those are medicine's (no-lineage; defensive scope). Class-K clean (syndrome^2
via inner product; the correction = the Class-K pin-slot toward the codeword; no abs()).
"""
import numpy as np

T = 200
BIAS = 0.15          # the runaway's directional tilt (growth-side or loss-side); same for both
SEED = 0


def main():
    rng = np.random.default_rng(SEED)
    pert = rng.standard_normal(T) + BIAS      # the SAME ordinary perturbations for both arms

    # arm 1 -- correction INTACT: each step, the Class-K pin-slot drives the syndrome back
    # toward the codeword (0). The healthy partition.
    s = 0.0
    corrected = np.empty(T)
    for t in range(T):
        s = s + pert[t]        # ordinary perturbation arrives
        s = s - 1.0 * s        # Class-K pin-slot correction: decode back to the codeword
        corrected[t] = s

    # arm 2 -- correction FAILED: same perturbations, no boundary. The runaway.
    runaway = np.cumsum(pert)

    print("=== the structure of a runaway: SAME perturbations, correction on vs off ===")
    print(f"  (T={T} steps, identical perturbation stream, directional tilt={BIAS})\n")
    print(f"  {'step':>5} | {'syndrome^2 CORRECTED':>22} | {'syndrome^2 RUNAWAY':>20}")
    for t in [9, 49, 99, 199]:
        print(f"  {t+1:>5} | {corrected[t]**2:>22.3f} | {runaway[t]**2:>20.1f}")
    print(f"\n  correction intact -> syndrome bounded (~one perturbation); held at the codeword.")
    print(f"  correction failed -> syndrome accumulates ~linearly with the tilt -> RUNS AWAY.")
    print(f"  ratio at t={T}: runaway/corrected syndrome^2 = {runaway[-1]**2 / max(corrected[-1]**2, 1e-9):.0f}x")
    print("\n  reading: the runaway is driven by ORDINARY perturbations the healthy partition")
    print("  silently absorbs. What changed at the partition is the LOSS of the correction")
    print("  (the parity-check / Class-K boundary), not the arrival of a new force.")
    print("  [STRUCTURAL LENS ONLY -- not a disease mechanism, not a treatment. Medicine owns that.]")


if __name__ == "__main__":
    main()
