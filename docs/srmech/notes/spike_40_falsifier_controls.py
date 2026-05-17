"""Spike #40 — falsifier controls per Spike #38 / Spike #30B v3.

For each candidate substrate K-fit result, bound the "random amplitude
spectrum gives eps this big" baseline. 50 seeds at n=10 partials.

Also runs ring-up / ring-down framing: per
[[user_stance_string_theory_instrument_first]] struck/plucked instruments
RING DOWN (decay envelope visible); sustained instruments RING UP (steady
oscillation). Cascade-beta test (Spike #31 stretched-exp on decay envelope)
applies to RING-DOWN substrates only.
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from scipy.optimize import curve_fit

from pathlib import Path as _Path
OUT_DIR = str(_Path(__file__).resolve().parent)

sys.path.insert(0, OUT_DIR)
from spike_40_musical_epicycle_analysis import (
    strict_kepler_test,
    random_amplitude_spectrum,
    clean_for_json,
)


def cascade_beta_test(envelope: np.ndarray, t: np.ndarray) -> dict:
    """Spike #31 cascade-beta test on a ring-down envelope.

    Fits stretched-exponential E(t) = E_0 * exp(-(t/tau)^beta). The cascade
    composition stance predicts beta = d_S / (d_S + 2) where d_S is the
    spectral dimension of the substrate (1D string d_S=1 → beta=1/3; 2D
    membrane d_S=2 → beta=1/2; 3D bell d_S=3 → beta=3/5).
    """
    envelope = np.asarray(envelope, dtype=float)
    t = np.asarray(t, dtype=float)
    # Ensure envelope > 0
    if np.any(envelope <= 0) or np.any(t < 0):
        return {"fit_ok": False, "reason": "non-positive envelope"}
    try:
        def f(tt, E0, tau, beta):
            return E0 * np.exp(-((tt / tau) ** beta))
        # Initial guess: E_0 = envelope[0], tau = midpoint, beta = 0.5
        E0_guess = float(envelope[0])
        tau_guess = float(t[len(t) // 2])
        popt, _ = curve_fit(
            f, t, envelope, p0=[E0_guess, tau_guess, 0.5],
            bounds=([0, 1e-9, 0.1], [10 * E0_guess, 100 * tau_guess, 2.0]),
            maxfev=5000,
        )
        E0_fit, tau_fit, beta_fit = popt
        pred = f(t, *popt)
        ss_res = float(np.sum((envelope - pred) ** 2))
        ss_tot = float(np.sum((envelope - envelope.mean()) ** 2))
        r2 = 1.0 - (ss_res / ss_tot if ss_tot > 1e-15 else 1.0)
        return {
            "fit_ok": True,
            "E0": float(E0_fit),
            "tau": float(tau_fit),
            "beta": float(beta_fit),
            "r2": float(r2),
        }
    except Exception as e:
        return {"fit_ok": False, "reason": str(e)}


def main():
    print("=" * 78)
    print("Spike #40 — falsifier controls + cascade-beta ring-down")
    print("=" * 78)

    records = []

    # === Falsifier 1: 50 random amplitude spectra ===
    print("\n--- FALSIFIER: 50 random amplitude spectra (n=10) ---")
    eps_fits = []
    r2s = []
    monos = []
    Ks_present = []
    for seed in range(50):
        c = random_amplitude_spectrum(seed=seed, n_partials=10)
        K = strict_kepler_test(c)
        eps_fits.append(K["eps_fit"])
        r2s.append(K["r2"])
        monos.append(K["monotonic_decreasing"])
        Ks_present.append(K["kepler_signature_present"])

    eps_fits = np.array([x for x in eps_fits if not math.isnan(x)])
    print(
        f"  eps_fit: mean={eps_fits.mean():.4f} std={eps_fits.std():.4f} "
        f"min={eps_fits.min():.4f} max={eps_fits.max():.4f}"
    )
    print(
        f"  r2: mean={np.mean(r2s):.4f} std={np.std(r2s):.4f} "
        f"min={np.min(r2s):.4f} max={np.max(r2s):.4f}"
    )
    print(f"  monotonic-decreasing count: {sum(monos)}/50")
    print(f"  K-signature-present count: {sum(Ks_present)}/50 (HARD FALSIFIER)")
    records.append({
        "kind": "falsifier_random_amplitude_spectra",
        "n_seeds": 50,
        "n_partials": 10,
        "eps_fit_mean": float(eps_fits.mean()),
        "eps_fit_std": float(eps_fits.std()),
        "eps_fit_min": float(eps_fits.min()),
        "eps_fit_max": float(eps_fits.max()),
        "r2_mean": float(np.mean(r2s)),
        "r2_max": float(np.max(r2s)),
        "monotonic_count": int(sum(monos)),
        "K_present_count": int(sum(Ks_present)),
    })

    # === Falsifier 2: pure-harmonic 1/n ratchet — does the K-test correctly REJECT? ===
    print("\n--- FALSIFIER: pure-harmonic 1/n series (should fail K) ---")
    c = np.zeros(20)
    for n in range(1, 20):
        c[n] = 1.0 / n
    K = strict_kepler_test(c)
    print(f"  pure 1/n: eps_fit={K['eps_fit']:.4f} r2={K['r2']:.4f} "
          f"in_range={K['in_physical_range']} mono={K['monotonic_decreasing']} "
          f"K_present={K['kepler_signature_present']}")
    records.append({"kind": "falsifier_pure_harmonic", "k_test": K})

    # === Falsifier 3: white-noise flat ===
    print("\n--- FALSIFIER: white-noise flat spectrum (should fail K) ---")
    c = np.ones(20)
    c[0] = 0
    K = strict_kepler_test(c)
    print(f"  white noise: eps_fit={K['eps_fit']:.4f} r2={K['r2']:.4f} "
          f"in_range={K['in_physical_range']} mono={K['monotonic_decreasing']} "
          f"K_present={K['kepler_signature_present']}")
    records.append({"kind": "falsifier_white_noise", "k_test": K})

    # === Cascade-beta: ring-down envelopes for struck/plucked instruments ===
    print("\n--- CASCADE-BETA: ring-down envelopes for RING-DOWN instruments ---")
    # Synthesise canonical ring-down envelopes:
    #   piano (struck string, 1D substrate): E(t) ~ exp(-t/tau) but per
    #     cascade-beta the substrate's d_S=1 predicts beta=1/3 (stretched-exp).
    #     However, real piano decay is closer to simple exp; we model BOTH.
    # For this spike's scope, we test whether the AMSC SM-class signature
    # picks up cascade-beta in canonical decay envelopes.

    t = np.linspace(0.01, 5.0, 500)
    # Piano canonical decay: dual-rate (initial fast + slow tail; Fletcher §2.20)
    # Simple model: E(t) = 0.5 exp(-2t) + 0.5 exp(-t/3)
    piano_env = 0.5 * np.exp(-2.0 * t) + 0.5 * np.exp(-t / 3.0)
    res = cascade_beta_test(piano_env, t)
    if res["fit_ok"]:
        # Expected per cascade-beta: 1D string d_S=1 → beta = 1/(1+2) = 1/3 ≈ 0.333
        beta_expected_1D = 1.0 / 3.0
        print(
            f"  piano (1D substrate): beta_fit={res['beta']:.4f} "
            f"expected_1D={beta_expected_1D:.4f} "
            f"delta={res['beta']-beta_expected_1D:+.4f} r2={res['r2']:.4f}"
        )
        records.append({
            "kind": "cascade_beta_piano",
            "substrate": "piano_decay_envelope_dual_exp",
            "beta_fit": res["beta"],
            "beta_expected_d_S_1": beta_expected_1D,
            "delta_beta": res["beta"] - beta_expected_1D,
            "tau_fit": res["tau"],
            "r2": res["r2"],
        })

    # Drum 2D membrane: d_S=2 → beta = 2/(2+2) = 1/2 = 0.5
    drum_env = np.exp(-1.5 * t) * np.cos(2 * math.pi * 3.0 * t) ** 2
    # Use envelope (abs of the modulated decay); fit to underlying
    # exponential
    drum_env_smooth = np.exp(-1.5 * t)
    res = cascade_beta_test(drum_env_smooth, t)
    if res["fit_ok"]:
        beta_expected_2D = 2.0 / 4.0
        print(
            f"  drum 2D (d_S=2):     beta_fit={res['beta']:.4f} "
            f"expected_2D={beta_expected_2D:.4f} "
            f"delta={res['beta']-beta_expected_2D:+.4f} r2={res['r2']:.4f}"
        )
        records.append({
            "kind": "cascade_beta_drum",
            "substrate": "drum_2d_decay_envelope_simple_exp",
            "beta_fit": res["beta"],
            "beta_expected_d_S_2": beta_expected_2D,
            "delta_beta": res["beta"] - beta_expected_2D,
            "tau_fit": res["tau"],
            "r2": res["r2"],
        })

    # Bell 3D (assumed): d_S=3 → beta = 3/(3+2) = 3/5 = 0.6
    bell_env = np.exp(-0.5 * t)  # bells have long sustain; simple exp
    res = cascade_beta_test(bell_env, t)
    if res["fit_ok"]:
        beta_expected_3D = 3.0 / 5.0
        print(
            f"  bell (d_S=3):        beta_fit={res['beta']:.4f} "
            f"expected_3D={beta_expected_3D:.4f} "
            f"delta={res['beta']-beta_expected_3D:+.4f} r2={res['r2']:.4f}"
        )
        records.append({
            "kind": "cascade_beta_bell",
            "substrate": "bell_decay_envelope_simple_exp",
            "beta_fit": res["beta"],
            "beta_expected_d_S_3": beta_expected_3D,
            "delta_beta": res["beta"] - beta_expected_3D,
            "tau_fit": res["tau"],
            "r2": res["r2"],
        })

    # Ring-up (sustained) instruments don't have ring-down → cascade-beta N/A
    print("\n--- RING-UP / SUSTAINED instruments (cascade-beta N/A) ---")
    for ru in ["violin_bowed_steady", "flute_blown_steady", "clarinet_blown_steady", "voice_sung_steady", "trumpet_blown_steady"]:
        print(f"  {ru}: cascade-beta SKIPPED (no decay envelope; instrument-first ring-up)")
        records.append({
            "kind": "cascade_beta_ring_up_skipped",
            "substrate": ru,
            "note": "Sustained-mode substrate; ring-up not ring-down per "
                    "user_stance_string_theory_instrument_first; cascade-beta "
                    "is for ring-down envelopes only",
        })

    out = os.path.join(OUT_DIR, "spike_40_falsifier_records.ndjson")
    with open(out, "w") as fh:
        for r in records:
            fh.write(json.dumps(clean_for_json(r)) + "\n")
    print(f"\nWrote {len(records)} falsifier+cascade records to {out}")


if __name__ == "__main__":
    main()
