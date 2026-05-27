"""R-RBS-LM-102 — BCI chirality-native patient encoding smoke test (F132 §8)

Path 6/6 of the wishlist-gated research resume. The last wishlist-gated path.

F132 §8 framework prediction:
  "BCI native chirality matching: patient's neural substrate IS chiral
  (DNA is RH; biological molecules show overwhelming homochirality).
  Klein-4 HDC can natively encode chirality-aware patient data;
  bipolar HDC has no chirality slot."

This smoke test creates SYNTHETIC chiral neural-style signals — pairs of
signal trains that differ ONLY in chirality (mirror-image asymmetry) and
asks:

  1. Can Klein-4 HDC encode-and-retrieve the two chirality variants such
     that the variants are DISCRIMINABLE at the encoded level?
  2. Can bipolar HDC do the same, or does it conflate the two variants
     (no chirality slot)?

Per [[feedback_trauma_informed_defensive_scope]]: framework reading
only. NO patient-targeting, NO medical-device claims, NO surgical
implications. Smoke test of substrate encoding capacity ONLY.

Cross-references:
  - F132 §8 (BCI applications enabled by chirality-native encoding)
  - F135 (substrate vs shadow; substrate-side chirality measurement)
  - F139 (chirality axis operational at scale)
  - F141 (polar plasticity; relevant for noisy patient data)
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def generate_chiral_signal_pair(D: int, signal_type: str, rng):
    """Generate a pair of chirality-mirrored synthetic signals.

    Returns (signal_RH, signal_LH) where the two are structurally identical
    except for one chirality axis being flipped.

    NOT real BCI data. This is a substrate-encoding smoke test with synthetic
    signals that have the SHAPE of chirality-asymmetric neural patterns.
    """
    if signal_type == "asymmetric_oscillation":
        # Right-handed: positive lead at first half, negative trail at second half
        t = np.arange(D)
        signal_RH = np.sin(2 * np.pi * t / 1000) * np.exp(-t / D) + 0.3 * rng.standard_normal(D)
        # Left-handed: time-reversed -> negative lead at first half, positive trail
        signal_LH = -signal_RH[::-1]
    elif signal_type == "spiral_pattern":
        # Spiral with handedness: angle ramps one direction
        t = np.arange(D)
        phase_RH = 2 * np.pi * t / 1000
        phase_LH = -2 * np.pi * t / 1000
        signal_RH = np.cos(phase_RH) + 0.1 * rng.standard_normal(D)
        signal_LH = np.cos(phase_LH) + 0.1 * rng.standard_normal(D)
    elif signal_type == "random_chiral":
        # Two random signals, then make them chirality-mirrors
        base = rng.standard_normal(D)
        signal_RH = base.copy()
        signal_LH = base[::-1].copy()  # Mirror = chirality flip
    else:
        raise ValueError(f"Unknown signal type: {signal_type}")
    return signal_RH, signal_LH


def encode_signal_klein4(signal: np.ndarray, chirality_sector: int, rng) -> np.ndarray:
    """Encode a signal as Klein-4 HV with chirality-axis tag.

    1. Quantise signal magnitudes into 2-bit Gray-like states (sign + magnitude)
    2. Apply chirality sector mask
    """
    D = len(signal)
    # Quantise into 4 states: (sign, magnitude > median_abs)
    median_abs = float(np.median(np.abs(signal)))
    sign_bit = (signal > 0).astype(np.uint8)
    mag_bit = (np.abs(signal) > median_abs).astype(np.uint8)
    states = (sign_bit << 1) | mag_bit
    states = states.astype(np.uint8)
    # Tag with chirality sector
    sector_mask = np.full(D, chirality_sector, dtype=np.uint8)
    return hdc.klein4_bind(states, sector_mask)


def encode_signal_bipolar(signal: np.ndarray, rng) -> np.ndarray:
    """Encode signal as bipolar HV — no chirality slot available."""
    D = len(signal)
    # Bipolar quantisation: sign only
    return np.where(signal >= 0, 1, -1).astype(np.int8)


def sim_klein4(a, b):
    return float(hdc.klein4_similarity(a, b))


def sim_bipolar(a, b):
    return float(np.mean(a == b) * 2 - 1)


def test_chirality_discrimination(D: int, N_pairs: int, signal_type: str, rng):
    """Run chirality discrimination test for both variants."""
    klein4_self_sims, klein4_cross_sims = [], []
    bipolar_self_sims, bipolar_cross_sims = [], []

    for i in range(N_pairs):
        # Generate one chirality-mirrored pair
        rh_signal, lh_signal = generate_chiral_signal_pair(D, signal_type, rng)

        # Klein-4 encoding (with chirality-axis tag)
        rh_k4 = encode_signal_klein4(rh_signal, chirality_sector=0, rng=rng)  # RH = sector 0
        lh_k4 = encode_signal_klein4(lh_signal, chirality_sector=2, rng=rng)  # LH = sector 2 (γ₅ flip)

        # Bipolar encoding (no chirality slot)
        rh_bp = encode_signal_bipolar(rh_signal, rng=rng)
        lh_bp = encode_signal_bipolar(lh_signal, rng=rng)

        # Test: similarity of RH to RH (self) vs RH to LH (cross-chirality)
        klein4_self_sims.append(sim_klein4(rh_k4, rh_k4))
        klein4_cross_sims.append(sim_klein4(rh_k4, lh_k4))

        bipolar_self_sims.append(sim_bipolar(rh_bp, rh_bp))
        bipolar_cross_sims.append(sim_bipolar(rh_bp, lh_bp))

    return {
        "klein4_self_mean": float(np.mean(klein4_self_sims)),
        "klein4_self_std": float(np.std(klein4_self_sims)),
        "klein4_cross_mean": float(np.mean(klein4_cross_sims)),
        "klein4_cross_std": float(np.std(klein4_cross_sims)),
        "bipolar_self_mean": float(np.mean(bipolar_self_sims)),
        "bipolar_self_std": float(np.std(bipolar_self_sims)),
        "bipolar_cross_mean": float(np.mean(bipolar_cross_sims)),
        "bipolar_cross_std": float(np.std(bipolar_cross_sims)),
    }


def main():
    rng = np.random.default_rng(42)
    D = 8192
    N_pairs = 50
    signal_types = ["asymmetric_oscillation", "spiral_pattern", "random_chiral"]

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"D={D}, N_pairs={N_pairs}")
    print(f"Signal types: {signal_types}")
    print()

    # Random baselines
    k4_random_sims = []
    bp_random_sims = []
    for _ in range(100):
        k4_random_sims.append(sim_klein4(hdc.klein4_random(D, rng), hdc.klein4_random(D, rng)))
        bp_random_sims.append(
            sim_bipolar(
                rng.choice([-1, 1], size=D).astype(np.int8),
                rng.choice([-1, 1], size=D).astype(np.int8),
            )
        )
    k4_baseline = float(np.mean(k4_random_sims))
    bp_baseline = float(np.mean(bp_random_sims))
    print(f"Random baselines: klein4={k4_baseline:.4f}, bipolar={bp_baseline:.4f}")
    print()

    all_results = {}
    for sig_type in signal_types:
        print(f"=== Signal type: {sig_type} ===")
        res = test_chirality_discrimination(D, N_pairs, sig_type, rng)
        all_results[sig_type] = res

        k4_self_above = (res["klein4_self_mean"] - k4_baseline) / (1 - k4_baseline)
        k4_cross_above = (res["klein4_cross_mean"] - k4_baseline) / (1 - k4_baseline)
        bp_self_above = (res["bipolar_self_mean"] - bp_baseline) / (1 - bp_baseline)
        bp_cross_above = (res["bipolar_cross_mean"] - bp_baseline) / (1 - bp_baseline)

        print(f"  Klein-4:")
        print(f"    self (RH vs RH):      {res['klein4_self_mean']:+0.4f} ± {res['klein4_self_std']:.4f}  (above-rand: {k4_self_above:+0.4f})")
        print(f"    cross (RH vs LH):     {res['klein4_cross_mean']:+0.4f} ± {res['klein4_cross_std']:.4f}  (above-rand: {k4_cross_above:+0.4f})")
        print(f"    discrimination gap:   {res['klein4_self_mean'] - res['klein4_cross_mean']:+0.4f}")
        print(f"  Bipolar:")
        print(f"    self (RH vs RH):      {res['bipolar_self_mean']:+0.4f} ± {res['bipolar_self_std']:.4f}  (above-rand: {bp_self_above:+0.4f})")
        print(f"    cross (RH vs LH):     {res['bipolar_cross_mean']:+0.4f} ± {res['bipolar_cross_std']:.4f}  (above-rand: {bp_cross_above:+0.4f})")
        print(f"    discrimination gap:   {res['bipolar_self_mean'] - res['bipolar_cross_mean']:+0.4f}")
        print()

    # Headline: does Klein-4 have a LARGER chirality-discrimination gap than bipolar?
    print("=== Headline: chirality discrimination gap (self - cross) ===")
    print(f"{'signal type':<28} | {'klein4 gap':>12} | {'bipolar gap':>12} | {'k4 > bp?':>10}")
    print("-" * 80)
    for sig_type in signal_types:
        res = all_results[sig_type]
        k4_gap = res["klein4_self_mean"] - res["klein4_cross_mean"]
        bp_gap = res["bipolar_self_mean"] - res["bipolar_cross_mean"]
        verdict = "YES" if k4_gap > bp_gap + 0.05 else "NO"
        print(f"{sig_type:<28} | {k4_gap:>+0.4f}     | {bp_gap:>+0.4f}     | {verdict:>10}")

    # F132 §8 prediction: Klein-4 has chirality slot; bipolar does not
    # Therefore: Klein-4 should consistently produce LARGER discrimination gap than bipolar
    print()
    print("=== F132 §8 BCI prediction verdict ===")
    print("PREDICTION: Klein-4 has chirality slot; bipolar does not.")
    print("Therefore: Klein-4 should produce LARGER chirality discrimination gap.")
    klein4_consistently_wins = all(
        (all_results[sig]["klein4_self_mean"] - all_results[sig]["klein4_cross_mean"]) >
        (all_results[sig]["bipolar_self_mean"] - all_results[sig]["bipolar_cross_mean"]) + 0.02
        for sig in signal_types
    )
    print(f"Klein-4 consistently wins (gap > bipolar + 0.02): {klein4_consistently_wins}")

    # Trauma-informed scope check
    print()
    print("=== Trauma-informed defensive scope confirmation ===")
    print("This smoke test:")
    print("  - Uses SYNTHETIC signals (not real BCI data)")
    print("  - Tests SUBSTRATE-LEVEL encoding capacity ONLY")
    print("  - Makes NO patient-targeting / medical-device / surgical claims")
    print("  - Per [[feedback_trauma_informed_defensive_scope]]: framework reading only")

    out_path = Path(__file__).parent / "R-RBS-LM-102_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D,
        "N_pairs": N_pairs,
        "signal_types": signal_types,
        "seed": 42,
        "baselines": {"klein4": k4_baseline, "bipolar": bp_baseline},
        "results": all_results,
        "klein4_consistently_wins": klein4_consistently_wins,
        "scope": "synthetic substrate encoding smoke test only; no medical/patient claims",
    }, indent=2))
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
