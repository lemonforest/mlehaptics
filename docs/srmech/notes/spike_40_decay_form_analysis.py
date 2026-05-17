"""Spike #40 supplementary — substrate-discrimination via decay-form fitting.

The bare K-test cannot discriminate piano/violin/drum amplitude envelopes
because they all share the canonical 1/n envelope (Helmholtz sawtooth /
Fletcher struck-string / drum-mode-baseline). Substrate fingerprint lives at:

  (a) DECAY FORM: 1/n^p with p in {0.5, 1, 2}, or geometric eps^n, or Bessel J_k
  (b) PARTIAL FREQUENCY-AXIS structure (inharmonicity, missing modes, formant peaks)
  (c) SUSTAINED vs DECAY envelope (ring-up vs ring-down per
      [[user_stance_string_theory_instrument_first]])

This script adds dimension (a) directly: fit each substrate's amplitude
spectrum to FOUR candidate decay models and report the BEST-FIT model +
goodness-of-fit. The model with min residual IS the substrate signature.
"""

from __future__ import annotations

import json
import math
import os

import numpy as np
import scipy.linalg as sla
import scipy.special as sps

from pathlib import Path as _Path
OUT_DIR = str(_Path(__file__).resolve().parent)


def fit_decay_models(coeffs: np.ndarray, n_max: int = 8) -> dict:
    """Fit four decay models to coeffs[1..n_max] and return BIC-like goodness.

    Models:
      M1: power-law a_n = A / n^p          (Fletcher / sawtooth family)
      M2: geometric a_n = A * eps^n         (Kepler / FM-small-beta family)
      M3: Bessel    a_n = |J_n(beta)|       (FM-canonical, NOT Kepler)
      M4: kepler    a_n = A * eps^n / n     (Kepler-canonical EOC)

    For each model, fit on log-scale where possible, then RMS residual on
    linear scale; the model with min RMS log-residual wins.
    """
    abs_c = np.abs(coeffs)
    if len(abs_c) <= n_max:
        n_max = len(abs_c) - 1
    cs = abs_c[1 : n_max + 1]
    ns = np.arange(1, len(cs) + 1)
    floor = max(1e-15, abs_c.max() * 1e-12)
    mask = cs > floor
    if mask.sum() < 3:
        return {"best_model": "INSUFFICIENT", "n_used": int(mask.sum())}
    ks = ns[mask]
    cs = cs[mask]
    log_c = np.log(cs)

    results = {}

    # M1: power-law log(a_n) = log(A) - p log(n)
    p1 = np.polyfit(np.log(ks), log_c, 1)
    p_pow = -p1[0]
    A_pow = math.exp(p1[1])
    pred1 = np.log(A_pow) - p_pow * np.log(ks)
    res1 = float(np.sqrt(np.mean((log_c - pred1) ** 2)))
    results["M1_power_law"] = {
        "p": float(p_pow),
        "A": A_pow,
        "log_rms_residual": res1,
    }

    # M2: geometric log(a_n) = log(A) + n log(eps)
    p2 = np.polyfit(ks, log_c, 1)
    eps_geo = math.exp(p2[0])
    A_geo = math.exp(p2[1])
    pred2 = np.log(A_geo) + ks * np.log(eps_geo)
    res2 = float(np.sqrt(np.mean((log_c - pred2) ** 2)))
    results["M2_geometric"] = {
        "eps": float(eps_geo),
        "A": A_geo,
        "log_rms_residual": res2,
    }

    # M3: Bessel — find best beta by grid search over [0.1, 5.0]
    betas = np.linspace(0.1, 5.0, 100)
    best_res3 = float("inf")
    best_beta = float("nan")
    best_A3 = float("nan")
    for beta in betas:
        Jk = np.array([abs(sps.jv(int(k), beta)) for k in ks])
        Jk_safe = np.where(Jk > 1e-15, Jk, 1e-15)
        # Fit log(A) on log scale
        diff = log_c - np.log(Jk_safe)
        logA = float(diff.mean())
        pred3 = logA + np.log(Jk_safe)
        res3 = float(np.sqrt(np.mean((log_c - pred3) ** 2)))
        if res3 < best_res3:
            best_res3 = res3
            best_beta = float(beta)
            best_A3 = math.exp(logA)
    results["M3_bessel"] = {
        "beta": best_beta,
        "A": best_A3,
        "log_rms_residual": best_res3,
    }

    # M4: kepler log(a_n) = log(A) + n log(eps) - log(n)
    # Fit log(A) + n log(eps) = log(a_n) + log(n)
    y4 = log_c + np.log(ks)
    p4 = np.polyfit(ks, y4, 1)
    eps_kep = math.exp(p4[0])
    A_kep = math.exp(p4[1])
    pred4 = np.log(A_kep) + ks * np.log(eps_kep) - np.log(ks)
    res4 = float(np.sqrt(np.mean((log_c - pred4) ** 2)))
    results["M4_kepler"] = {
        "eps": float(eps_kep),
        "A": A_kep,
        "log_rms_residual": res4,
    }

    # Pick best
    model_names = ["M1_power_law", "M2_geometric", "M3_bessel", "M4_kepler"]
    res_vals = [results[m]["log_rms_residual"] for m in model_names]
    best_idx = int(np.argmin(res_vals))
    best_model = model_names[best_idx]
    second_idx = int(np.argsort(res_vals)[1])
    second_model = model_names[second_idx]
    margin = res_vals[second_idx] - res_vals[best_idx]
    return {
        "best_model": best_model,
        "second_model": second_model,
        "margin_log_rms": float(margin),
        "models": results,
        "n_used": int(len(ks)),
    }


def clean_for_json(x):
    if isinstance(x, dict):
        return {k: clean_for_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean_for_json(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if x is None or isinstance(x, (str, int, float)):
        return x
    return str(x)


# Import substrate generators from primary script
import sys
sys.path.insert(0, OUT_DIR)
from spike_40_musical_epicycle_analysis import (
    pure_fm_signal,
    pure_am_signal,
    beat_pattern,
    piano_inharmonic_partials,
    violin_helmholtz,
    clarinet_open_closed,
    drum_membrane_2d,
    bell_modes_3_mode,
    voice_glottal_source_filter,
    flute_open_open,
    trumpet_lip_buzz,
    pure_kepler_reference,
    pure_harmonic_1over_n,
    white_noise_flat_amplitude,
    random_amplitude_spectrum,
)


def main():
    print("=" * 78)
    print("Spike #40 supplementary — decay-form-best-fit per substrate")
    print("=" * 78)

    substrates = []
    for beta in [0.5, 1.5, 3.0]:
        c, m = pure_fm_signal(beta_fm=beta)
        substrates.append((f"pure_fm_beta_{beta}", c, m))
    c, m = pure_am_signal()
    substrates.append(("pure_am", c, m))
    c, m = beat_pattern()
    substrates.append(("beat_pattern", c, m))
    for B in [1e-4, 5e-4, 1e-3]:
        c, m = piano_inharmonic_partials(B_stiff=B)
        substrates.append((f"piano_B_{B}", c, m))
    c, m = violin_helmholtz()
    substrates.append(("violin_helmholtz", c, m))
    c, m = clarinet_open_closed()
    substrates.append(("clarinet_open_closed", c, m))
    c_d, m_d, _ = drum_membrane_2d()
    substrates.append(("drum_membrane_2d_amp_baseline", c_d, m_d))
    c, m = bell_modes_3_mode()
    substrates.append(("bell_5mode", c, m))
    c, m = voice_glottal_source_filter()
    substrates.append(("voice_vowel_a", c, m))
    c, m = flute_open_open()
    substrates.append(("flute_open_open", c, m))
    c, m = trumpet_lip_buzz()
    substrates.append(("trumpet_lip_buzz", c, m))
    for eps in [0.01, 0.05, 0.1, 0.2, 0.4]:
        c, m = pure_kepler_reference(eps=eps)
        substrates.append((f"REF_pure_kepler_eps_{eps}", c, m))
    c, m = pure_harmonic_1over_n()
    substrates.append(("REF_pure_harmonic_1_over_n", c, m))
    c, m = white_noise_flat_amplitude()
    substrates.append(("REF_white_noise_flat", c, m))

    print(
        f"\n  {'INSTRUMENT':32s} {'best':>18s} {'second':>18s} {'margin':>8s} "
        f"{'M1.p':>7s} {'M2.eps':>7s} {'M3.beta':>8s} {'M4.eps':>7s}"
    )
    print("  " + "-" * 110)

    records = []
    for name, c, m in substrates:
        f = fit_decay_models(c)
        if f["best_model"] == "INSUFFICIENT":
            print(f"  {name:32s} INSUFFICIENT (sparse spectrum)")
            records.append({
                "kind": "decay_form_fit",
                "substrate": name,
                "best_model": "INSUFFICIENT",
                "n_used": f["n_used"],
            })
            continue
        M1p = f["models"]["M1_power_law"]["p"]
        M2eps = f["models"]["M2_geometric"]["eps"]
        M3beta = f["models"]["M3_bessel"]["beta"]
        M4eps = f["models"]["M4_kepler"]["eps"]
        print(
            f"  {name:32s} {f['best_model']:>18s} {f['second_model']:>18s} "
            f"{f['margin_log_rms']:8.3f} {M1p:7.3f} {M2eps:7.3f} {M3beta:8.3f} {M4eps:7.3f}"
        )
        records.append({
            "kind": "decay_form_fit",
            "substrate": name,
            "best_model": f["best_model"],
            "second_model": f["second_model"],
            "margin_log_rms": f["margin_log_rms"],
            "M1_power_law_p": M1p,
            "M1_log_rms_resid": f["models"]["M1_power_law"]["log_rms_residual"],
            "M2_geometric_eps": M2eps,
            "M2_log_rms_resid": f["models"]["M2_geometric"]["log_rms_residual"],
            "M3_bessel_beta": M3beta,
            "M3_log_rms_resid": f["models"]["M3_bessel"]["log_rms_residual"],
            "M4_kepler_eps": M4eps,
            "M4_log_rms_resid": f["models"]["M4_kepler"]["log_rms_residual"],
            "n_used": f["n_used"],
        })

    out = os.path.join(OUT_DIR, "spike_40_decay_form_records.ndjson")
    with open(out, "w") as fh:
        for r in records:
            fh.write(json.dumps(clean_for_json(r)) + "\n")
    print(f"\nWrote {len(records)} decay-form records to {out}")


if __name__ == "__main__":
    main()
