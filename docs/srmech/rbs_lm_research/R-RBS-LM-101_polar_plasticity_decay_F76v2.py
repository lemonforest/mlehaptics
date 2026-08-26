"""R-RBS-LM-101 — Polar HDC plasticity/decay encoding (F76 v2 path)

Path 5/6 of the wishlist-gated research resume.

F76 v1 (R-RBS-LM-76) implemented Hebbian-style decay on bipolar HDC
bindings — but bipolar has no neutral state, so decayed bindings had
to be forced to ±1 (an artifact). Polar HDC's first-class 0 state lets
us encode "uncertain / decayed / dead-band" explicitly.

This test demonstrates plasticity-aware encoding with three regimes:

  R1. Encode-only (baseline):
        - bind N concepts; bundle; query all; measure retrieval

  R2. Decay-as-zero (polar):
        - bind N concepts; apply position-wise decay (move some positions to 0)
        - bundle; query; measure retrieval and density

  R3. Decay-as-noise (bipolar comparator):
        - bind N concepts (bipolar); apply position-wise sign-flip (50% of decay positions)
        - bundle; query; measure retrieval

Key prediction (F76 v2 framework):
  - Polar decay degrades GRACEFULLY: 0 positions stay neutral; retrievable
    fraction shrinks but signal quality on surviving positions stays high
  - Bipolar decay degrades CATASTROPHICALLY: forced sign-flips inject pure
    noise that interferes with retrieval

This tests whether the polar 0-as-uncertain state is operationally
distinct from bipolar's forced-±1 behavior under plasticity dynamics.

Cross-references:
  - F76 (plasticity-augmented cascade with Hebbian decay; v1 bipolar)
  - UPSTREAM_NOTES §5 (polar HDC LANDED in srmech v0.4.3)
  - F137 (capacity calibration; informs gain/loss interpretation)
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def encode_bipolar(D: int, rng) -> np.ndarray:
    return rng.choice([-1, 1], size=D).astype(np.int8)


def encode_polar(D: int, rng) -> np.ndarray:
    return hdc.polar_random(D, rng)


def apply_decay_polar(hv: np.ndarray, decay_fraction: float, rng) -> np.ndarray:
    """Polar decay: move decay_fraction of positions to 0 (the uncertain state)."""
    D = len(hv)
    n_decay = int(decay_fraction * D)
    if n_decay == 0:
        return hv.copy()
    decay_positions = rng.choice(D, size=n_decay, replace=False)
    out = hv.copy()
    out[decay_positions] = 0
    return out


def apply_decay_bipolar(hv: np.ndarray, decay_fraction: float, rng) -> np.ndarray:
    """Bipolar decay (v1 F76 style): force 50% of decayed positions to wrong sign.

    This simulates the F76 v1 problem: no neutral state, so decay must inject
    noise via random sign-flips at decayed positions.
    """
    D = len(hv)
    n_decay = int(decay_fraction * D)
    if n_decay == 0:
        return hv.copy()
    decay_positions = rng.choice(D, size=n_decay, replace=False)
    flip_mask = rng.random(n_decay) < 0.5
    out = hv.copy()
    out[decay_positions[flip_mask]] = -out[decay_positions[flip_mask]]
    return out


def bind_pair_polar(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return hdc.polar_bind(a, b)


def bind_pair_bipolar(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a * b).astype(np.int8)


def bundle_polar(*vecs: np.ndarray) -> np.ndarray:
    return hdc.polar_bundle(*vecs)


def bundle_bipolar(*vecs: np.ndarray) -> np.ndarray:
    s = np.sum(vecs, axis=0)
    return np.where(s >= 0, 1, -1).astype(np.int8)


def sim_polar(a: np.ndarray, b: np.ndarray) -> float:
    return float(hdc.polar_similarity(a, b))


def sim_polar_skip_zero(a: np.ndarray, b: np.ndarray) -> float:
    """Skip-zero similarity: only score positions where BOTH are non-zero."""
    nz_mask = (a != 0) & (b != 0)
    if not np.any(nz_mask):
        return 0.0
    return float(np.mean(a[nz_mask] == b[nz_mask]))


def sim_bipolar(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(a == b) * 2 - 1)


def run_plasticity_test(
    D: int, N_pairs: int, decay_fractions: list[float], rng, variant: str
):
    """Run plasticity test for a single variant."""
    results = []
    for decay in decay_fractions:
        if variant == "polar":
            A = [encode_polar(D, rng) for _ in range(N_pairs)]
            B = [encode_polar(D, rng) for _ in range(N_pairs)]
            bound = [bind_pair_polar(a, b) for a, b in zip(A, B)]
            # Apply decay to bound pairs (simulating binding decay over time)
            decayed = [apply_decay_polar(b, decay, rng) for b in bound]
            comp = bundle_polar(*decayed)
            sims = [sim_polar(hdc.polar_unbind(comp, A[i]), B[i]) for i in range(N_pairs)]
            sims_skip_zero = [sim_polar_skip_zero(hdc.polar_unbind(comp, A[i]), B[i]) for i in range(N_pairs)]
            density = float(hdc.polar_density(comp))
            results.append({
                "decay_fraction": decay,
                "mean_sim_default": float(np.mean(sims)),
                "std_sim_default": float(np.std(sims)),
                "mean_sim_skip_zero": float(np.mean(sims_skip_zero)),
                "std_sim_skip_zero": float(np.std(sims_skip_zero)),
                "composite_density": density,
            })
        elif variant == "bipolar":
            A = [encode_bipolar(D, rng) for _ in range(N_pairs)]
            B = [encode_bipolar(D, rng) for _ in range(N_pairs)]
            bound = [bind_pair_bipolar(a, b) for a, b in zip(A, B)]
            decayed = [apply_decay_bipolar(b, decay, rng) for b in bound]
            comp = bundle_bipolar(*decayed)
            sims = [sim_bipolar(comp * A[i], B[i]) for i in range(N_pairs)]
            results.append({
                "decay_fraction": decay,
                "mean_sim_default": float(np.mean(sims)),
                "std_sim_default": float(np.std(sims)),
                "mean_sim_skip_zero": None,
                "std_sim_skip_zero": None,
                "composite_density": None,
            })
    return results


def random_baselines(D: int, N_trials: int, rng):
    """Compute random-pair baselines for normalization."""
    bp = []
    po_def = []
    po_skip = []
    for _ in range(N_trials):
        a_bp = encode_bipolar(D, rng)
        b_bp = encode_bipolar(D, rng)
        bp.append(sim_bipolar(a_bp, b_bp))
        a_po = encode_polar(D, rng)
        b_po = encode_polar(D, rng)
        po_def.append(sim_polar(a_po, b_po))
        po_skip.append(sim_polar_skip_zero(a_po, b_po))
    return {
        "bipolar": float(np.mean(bp)),
        "polar_default": float(np.mean(po_def)),
        "polar_skip_zero": float(np.mean(po_skip)),
    }


def main():
    rng = np.random.default_rng(42)
    D = 10000
    N_pairs = 32
    decay_fractions = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"D={D}, N_pairs={N_pairs}, decay_fractions={decay_fractions}")
    print()

    # Random baselines
    baselines = random_baselines(D, 50, rng)
    print(f"Random baselines: {baselines}")
    print()

    # Run polar plasticity
    print("=== Polar HDC plasticity (decay -> 0 state) ===")
    print(f"{'decay':>6} | {'sim_default':>14} | {'sim_skip_zero':>14} | {'density':>10} | {'above-rand (def)':>16} | {'above-rand (skip)':>17}")
    print("-" * 100)
    polar_results = run_plasticity_test(D, N_pairs, decay_fractions, rng, "polar")
    for r in polar_results:
        ar_def = (r["mean_sim_default"] - baselines["polar_default"]) / (1 - baselines["polar_default"])
        ar_skip = (r["mean_sim_skip_zero"] - baselines["polar_skip_zero"]) / (1 - baselines["polar_skip_zero"])
        print(
            f"{r['decay_fraction']:>6.2f} | "
            f"{r['mean_sim_default']:>+0.4f}        | "
            f"{r['mean_sim_skip_zero']:>+0.4f}        | "
            f"{r['composite_density']:>10.4f} | "
            f"{ar_def:>+0.4f}           | "
            f"{ar_skip:>+0.4f}"
        )

    print()
    print("=== Bipolar HDC plasticity (decay -> noise via sign-flip) ===")
    print(f"{'decay':>6} | {'sim_default':>14} | {'above-rand':>14}")
    print("-" * 60)
    bipolar_results = run_plasticity_test(D, N_pairs, decay_fractions, rng, "bipolar")
    for r in bipolar_results:
        ar = (r["mean_sim_default"] - baselines["bipolar"]) / (1 - baselines["bipolar"])
        print(
            f"{r['decay_fraction']:>6.2f} | "
            f"{r['mean_sim_default']:>+0.4f}        | "
            f"{ar:>+0.4f}"
        )

    # Verdict per F76 v2 hypothesis
    print()
    print("=== F76 v2 hypothesis verdicts ===")
    print("H1: Polar decay degrades gracefully (skip-zero stays high; density drops):")
    polar_skip_at_0 = polar_results[0]["mean_sim_skip_zero"]
    polar_skip_at_high_decay = polar_results[-2]["mean_sim_skip_zero"]  # 0.6 decay
    polar_density_drop = polar_results[0]["composite_density"] - polar_results[-2]["composite_density"]
    h1 = polar_skip_at_high_decay > polar_skip_at_0 - 0.10 and polar_density_drop > 0.1
    print(f"     skip_zero @ 0.0 decay: {polar_skip_at_0:.4f}")
    print(f"     skip_zero @ 0.6 decay: {polar_skip_at_high_decay:.4f}")
    print(f"     density drop: {polar_density_drop:.4f}")
    print(f"     H1 -> {h1}")

    print("H2: Bipolar decay degrades catastrophically (signal collapse):")
    bp_at_0 = bipolar_results[0]["mean_sim_default"]
    bp_at_high_decay = bipolar_results[-2]["mean_sim_default"]
    bp_at_floor = bipolar_results[-1]["mean_sim_default"]  # 0.7
    h2 = bp_at_high_decay < bp_at_0 * 0.5  # signal halves or worse at 0.6 decay
    print(f"     bipolar sim @ 0.0 decay: {bp_at_0:.4f}")
    print(f"     bipolar sim @ 0.6 decay: {bp_at_high_decay:.4f}")
    print(f"     bipolar sim @ 0.7 decay: {bp_at_floor:.4f}")
    print(f"     H2 -> {h2}")

    print("H3: Polar (skip-zero) outperforms bipolar at high decay:")
    h3 = polar_skip_at_high_decay > bp_at_high_decay
    print(f"     polar skip_zero @ 0.6 decay: {polar_skip_at_high_decay:.4f}")
    print(f"     bipolar          @ 0.6 decay: {bp_at_high_decay:.4f}")
    print(f"     H3 -> {h3}")

    out_path = Path(__file__).parent / "R-RBS-LM-101_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D,
        "N_pairs": N_pairs,
        "decay_fractions": decay_fractions,
        "seed": 42,
        "baselines": baselines,
        "polar_results": polar_results,
        "bipolar_results": bipolar_results,
        "verdicts": {"H1_polar_graceful": bool(h1), "H2_bipolar_catastrophic": bool(h2), "H3_polar_beats_bipolar_at_high_decay": bool(h3)},
    }, indent=2))
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
