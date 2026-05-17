"""Spike #40 — frequency-axis inharmonicity test.

For substrates with non-harmonic frequencies (piano with stiffness; drum 2D
membrane; bell modes), the substrate-discriminating signature may live in
the FREQUENCIES of partials (or their RATIOS), not the amplitudes.

Piano: f_n = n*f_0*sqrt(1 + B*n^2). The DEVIATION delta_n = f_n - n*f_0 is
the substrate fingerprint.

Drum 2D: f_n = lambda_{n,m} / (some normalisation). The ratios to lowest
mode are the substrate fingerprint.

Bell: f_n is given by canonical bell-tuning ratios (0.5, 1.0, 1.2, 1.5, 2.0).

Test whether these frequency sequences SHOW Kepler-shape in their deviations.
"""

from __future__ import annotations

import json
import math
import os

import numpy as np
import scipy.special as sps

from pathlib import Path as _Path
OUT_DIR = str(_Path(__file__).resolve().parent)

import sys
sys.path.insert(0, OUT_DIR)
from spike_40_musical_epicycle_analysis import strict_kepler_test, clean_for_json


def piano_freq_deviation(B_stiff: float, n_partials: int = 16) -> tuple[np.ndarray, np.ndarray]:
    """Piano stiff-string: f_n = n * f_0 * sqrt(1 + B*n^2).
    Returns (freqs_normalised_to_f0, deviations_from_n).
    """
    ns = np.arange(1, n_partials + 1)
    freqs = ns * np.sqrt(1.0 + B_stiff * ns ** 2)
    deviations = freqs - ns  # f_n - n*f_0 in units of f_0
    return freqs, deviations


def drum_freq_ratios(n_max_modes: int = 20) -> np.ndarray:
    """Drum 2D Bessel modes, sorted, ratios to lowest."""
    freqs = []
    for n in range(6):
        zeros = sps.jn_zeros(n, 5)
        for lm in zeros:
            freqs.append(lm)
    freqs = np.sort(np.array(freqs))
    if len(freqs) > n_max_modes:
        freqs = freqs[:n_max_modes]
    return freqs / freqs[0]


def bell_freq_ratios() -> np.ndarray:
    """Canonical bell modes (Fletcher 1998 §21.3)."""
    return np.array([0.5, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.4, 6.0])


def test_freq_sequence_for_K(freq_sequence: np.ndarray, name: str) -> dict:
    """Compute Fourier coefficients of the frequency-sequence-as-signal.

    The 'frequency-axis Kepler test' looks for K-shape in the partial-frequency
    sequence itself (rather than in the amplitudes). For a harmonic series
    f_n = n the sequence is linear; for inharmonic f_n = n*sqrt(1+B*n^2) it
    deviates upward.

    Method: form signal s[k] = f_k - k*f_1 (deviation from perfect harmonicity);
    compute power spectrum; run strict K-test.
    """
    f0 = freq_sequence[0]
    ns = np.arange(1, len(freq_sequence) + 1)
    deviations = freq_sequence / f0 - ns
    # Take coefficients-of-deviation directly
    coeffs = np.abs(deviations)
    coeffs_padded = np.zeros(len(freq_sequence) + 1)
    coeffs_padded[1:] = coeffs
    K = strict_kepler_test(coeffs_padded, k_max=6)
    return {
        "kind": "freq_inharmonicity_K_test",
        "substrate": name,
        "n_partials": int(len(freq_sequence)),
        "freq_ratios_first_5": (freq_sequence[:5] / freq_sequence[0]).tolist(),
        "deviations_first_5": deviations[:5].tolist(),
        "k_test_on_deviations": K,
    }


def main():
    print("=" * 78)
    print("Spike #40 — frequency-axis inharmonicity K-test")
    print("=" * 78)
    records = []

    # Piano stiffness sweep
    for B in [1e-5, 1e-4, 5e-4, 1e-3, 5e-3]:
        freqs, _ = piano_freq_deviation(B_stiff=B)
        rec = test_freq_sequence_for_K(freqs, f"piano_freq_axis_B_{B}")
        records.append(rec)
        K = rec["k_test_on_deviations"]
        print(
            f"  piano (B={B:.0e})       freq_axis K: eps_fit={K['eps_fit']:.4f} "
            f"r2={K['r2']:.4f} mono={K['monotonic_decreasing']} K_present={K['kepler_signature_present']}"
        )

    # Drum
    drum_ratios = drum_freq_ratios()
    rec = test_freq_sequence_for_K(drum_ratios, "drum_freq_axis")
    records.append(rec)
    K = rec["k_test_on_deviations"]
    print(
        f"  drum 2D                  freq_axis K: eps_fit={K['eps_fit']:.4f} "
        f"r2={K['r2']:.4f} mono={K['monotonic_decreasing']} K_present={K['kepler_signature_present']}"
    )

    # Bell
    bell_ratios = bell_freq_ratios()
    rec = test_freq_sequence_for_K(bell_ratios, "bell_freq_axis")
    records.append(rec)
    K = rec["k_test_on_deviations"]
    print(
        f"  bell 5-mode              freq_axis K: eps_fit={K['eps_fit']:.4f} "
        f"r2={K['r2']:.4f} mono={K['monotonic_decreasing']} K_present={K['kepler_signature_present']}"
    )

    # Pure harmonic reference (deviations all zero)
    harmonic_freqs = np.arange(1, 17, dtype=float)
    rec = test_freq_sequence_for_K(harmonic_freqs, "REF_pure_harmonic_freq_axis")
    records.append(rec)
    K = rec["k_test_on_deviations"]
    print(
        f"  pure harmonic            freq_axis K: eps_fit={K['eps_fit']:.4f} "
        f"r2={K['r2']:.4f} mono={K['monotonic_decreasing']} K_present={K['kepler_signature_present']}"
    )

    out = os.path.join(OUT_DIR, "spike_40_freq_inharmonicity_records.ndjson")
    with open(out, "w") as fh:
        for r in records:
            fh.write(json.dumps(clean_for_json(r)) + "\n")
    print(f"\nWrote {len(records)} records to {out}")


if __name__ == "__main__":
    main()
