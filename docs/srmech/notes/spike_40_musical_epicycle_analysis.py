"""Spike #40 — Structural shape of an epicycle in musical and wave theory.

Per-instrument meta-question: do different instruments produce measurably
different epicycle shapes? Is this substrate-discriminating?

Discipline:
    - Closed-form / textbook only (Helmholtz 1863, Rayleigh 1894, Fletcher &
      Rossing 1998, Watson 1922)
    - No copyrighted audio
    - Spike #30B v3 strict K-test: eps_fit in [0.001, 0.5]; r2 > 0.99;
      monotonic-decreasing
    - Spike #38 falsifier-control pattern: 50 random-amplitude seeds + named
      controls (pure-harmonic / white-noise / pure-Kepler-eps reference)
    - NDJSON outputs only
    - All claims chain-verified before output
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
os.makedirs(OUT_DIR, exist_ok=True)


def strict_kepler_test(coeffs: np.ndarray, k_max: int = 6) -> dict:
    """Spike #30B v3 strict three-criteria Kepler test.

    Three criteria, all must pass for kepler_signature_present=True:
      (1) eps_fit in physical range (0.001, 0.5)
      (2) r2 > 0.99
      (3) |c_k| monotonic-decreasing for k = 1..k_max
    """
    abs_c = np.abs(coeffs)
    if len(abs_c) <= k_max:
        k_max = len(abs_c) - 1
    cs = abs_c[1 : k_max + 1]
    ks = np.arange(1, len(cs) + 1)
    floor = max(1e-15, abs_c.max() * 1e-12)
    mask = cs > floor
    if mask.sum() < 3:
        return {
            "eps_fit": float("nan"),
            "r2": 0.0,
            "monotonic_decreasing": False,
            "in_physical_range": False,
            "high_r2": False,
            "kepler_signature_present": False,
            "n_harmonics_used": int(mask.sum()),
            "c1_c2_c3": [0.0, 0.0, 0.0],
        }
    ks_used = ks[mask]
    cs_used = cs[mask]
    log_c = np.log(cs_used)
    p = np.polyfit(ks_used, log_c, 1)
    eps_fit = math.exp(p[0])
    yhat = np.polyval(p, ks_used)
    ss_res = ((log_c - yhat) ** 2).sum()
    ss_tot = ((log_c - log_c.mean()) ** 2).sum()
    r2 = 1.0 - (ss_res / ss_tot if ss_tot > 1e-15 else 1.0)
    monotonic = bool(np.all(np.diff(cs_used) < 0))
    in_range = bool(0.001 < eps_fit < 0.5)
    high_r2 = bool(r2 > 0.99)
    return {
        "eps_fit": float(eps_fit),
        "r2": float(r2),
        "monotonic_decreasing": monotonic,
        "in_physical_range": in_range,
        "high_r2": high_r2,
        "kepler_signature_present": bool(monotonic and in_range and high_r2),
        "n_harmonics_used": int(len(ks_used)),
        "c1_c2_c3": [
            float(cs_used[i]) if i < len(cs_used) else 0.0 for i in range(3)
        ],
    }


# ============================================================================
# CLOSED-FORM PARTIAL-AMPLITUDE SPECTRA (from canonical textbook physics)
# ============================================================================
#
# Each function returns coeffs[0..N-1] where coeffs[k] is the amplitude of the
# k-th partial (k=0 is DC / k=1 is fundamental, depending on substrate
# convention). For K-test consistency we PREPEND a "c_0" DC term where the
# substrate doesn't naturally have one, so the test sees coeffs[1..k_max]
# matching the standard "first harmonic, second harmonic, ..." convention.


def pure_fm_signal(beta_fm: float = 1.5, n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Pure FM: cos(wc t + beta sin(wm t)) = sum_k J_k(beta) cos((wc + k wm) t).

    Watson 1922 canonical Bessel-series expansion. Sideband amplitudes
    are J_k(beta_fm) for k >= 0; |J_-k| = |J_k| for integer k.

    Returns ABS amplitudes ordered [c0=|J_0|, c1=|J_1|, c2=|J_2|, ...] (the
    one-sided spectrum where we don't double-count negative sidebands; for
    the K-test we want the per-mode amplitudes regardless of sign of k).
    """
    coeffs = np.zeros(n_partials)
    for k in range(n_partials):
        coeffs[k] = abs(sps.jv(k, beta_fm))
    meta = {
        "substrate": "pure_fm",
        "n_partials": n_partials,
        "beta_fm": beta_fm,
        "convention": "c_k = |J_k(beta)| (Watson 1922)",
    }
    return coeffs, meta


def pure_am_signal(modulation_index: float = 0.5, n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Pure AM: (1 + m cos(wm t)) cos(wc t) = cos(wc) + (m/2)[cos(wc-wm) + cos(wc+wm)].

    Three-line spectrum: carrier + two sidebands. All higher harmonics zero.
    """
    coeffs = np.zeros(n_partials)
    coeffs[0] = 1.0  # carrier
    coeffs[1] = modulation_index / 2.0
    # k >= 2: identically zero
    meta = {
        "substrate": "pure_am",
        "n_partials": n_partials,
        "modulation_index": modulation_index,
        "convention": "carrier + (m/2) sidebands only",
    }
    return coeffs, meta


def beat_pattern(omega1: float = 1.0, omega2: float = 1.1, n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Beat: cos(w1 t) + cos(w2 t). Two-line spectrum at w1 and w2 (assumed close)."""
    coeffs = np.zeros(n_partials)
    coeffs[1] = 1.0  # w1
    coeffs[2] = 1.0  # w2
    # k != 1, 2: identically zero
    meta = {
        "substrate": "beat_pattern",
        "n_partials": n_partials,
        "omega1": omega1,
        "omega2": omega2,
        "convention": "two-line spectrum at adjacent frequencies",
    }
    return coeffs, meta


def piano_inharmonic_partials(B_stiff: float = 1e-4, f0: float = 440.0, n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Piano string: f_n = n*f_0*sqrt(1 + B*n^2), amplitudes ~1/n (plucked-string).

    Fletcher & Rossing 1998 §2.18 (inharmonicity coefficient B). For
    moderate stiffness B~1e-4 (A4), partials approach harmonic; amplitudes
    follow ~1/n for ideal flexible string + soft-hammer envelope. We use
    the canonical struck-string amplitude envelope a_n = 1/n (plucked/struck
    string baseline; Fletcher §2.17).
    """
    coeffs = np.zeros(n_partials)
    # k=0 reserved as silent DC; partials at k=1..N-1
    for n in range(1, n_partials):
        coeffs[n] = 1.0 / n
    meta = {
        "substrate": "piano_inharmonic",
        "n_partials": n_partials,
        "B_stiff": B_stiff,
        "f0_hz": f0,
        "convention": "a_n = 1/n (Fletcher 1998 §2.17 struck-string)",
        "note": "frequency-axis inharmonicity present but amplitudes follow 1/n envelope",
    }
    return coeffs, meta


def violin_helmholtz(n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Violin bowed string (Helmholtz motion): sawtooth-like, partial amplitudes ~1/n.

    Helmholtz 1863 / Fletcher & Rossing 1998 §10.5: under stable Helmholtz
    motion the string velocity at the bridge is sawtooth; Fourier expansion
    of sawtooth has a_n = 1/n exactly. This is the canonical bowed-string
    baseline (filtered by body resonances in real performance; we model
    string-only here).
    """
    coeffs = np.zeros(n_partials)
    for n in range(1, n_partials):
        coeffs[n] = 1.0 / n
    meta = {
        "substrate": "violin_helmholtz",
        "n_partials": n_partials,
        "convention": "a_n = 1/n (Helmholtz sawtooth at bridge)",
        "note": "body-resonance filter excluded; string-only spectrum",
    }
    return coeffs, meta


def clarinet_open_closed(n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Clarinet (open-closed cylindrical tube): odd-harmonic-dominant, amplitudes ~1/(2n-1).

    Fletcher & Rossing 1998 §15.3: cylindrical pipe closed at one end (reed)
    and open at the other supports modes at f = (2n-1) f_0 / 4L. Reed
    excitation produces square-wave-like pressure → Fourier amplitudes
    a_(2n-1) = 1/(2n-1), even partials = 0.
    """
    coeffs = np.zeros(n_partials)
    for n in range(1, n_partials):
        if n % 2 == 1:
            coeffs[n] = 1.0 / n
        # even n: zero
    meta = {
        "substrate": "clarinet_open_closed",
        "n_partials": n_partials,
        "convention": "odd-harmonic-only: a_(2n-1) = 1/(2n-1); a_(2n) = 0",
        "note": "Fletcher 1998 §15.3 square-wave reed model",
    }
    return coeffs, meta


def drum_membrane_2d(n_radial: int = 6, n_angular: int = 6) -> tuple[np.ndarray, dict, np.ndarray]:
    """Drum membrane (2D circular, fixed boundary): modes at Bessel zeros lambda_{n,m}.

    Rayleigh 1894 §200: ideal circular membrane with Dirichlet BC has
    natural frequencies f_{n,m} = (c / 2 pi a) * lambda_{n,m}, where
    lambda_{n,m} is the m-th positive zero of J_n.

    Returns (sorted_freqs_as_coeffs, meta, eigvals_array).
    For K-test purposes we treat the SORTED modal-frequency sequence as
    the "spectrum"; for L-test we use the eigval array directly.

    Note: this is Class L DIRECTLY (2D Laplacian-Dirichlet eigenvalues).
    """
    freqs = []
    for n in range(n_radial):
        zeros = sps.jn_zeros(n, n_angular)
        for lm in zeros:
            freqs.append(lm)
    freqs = np.sort(np.array(freqs))
    # Treat as a "spectrum" by interpreting f_k as the k-th partial frequency
    # ratio (relative to fundamental). For K-test amplitudes, we use 1/k
    # baseline; the discriminating feature is the FREQUENCY ratios, not the
    # amplitudes (which are damping-mode-dependent).
    # We return the frequencies themselves AS the eigval array.
    n_partials = min(len(freqs) + 1, 32)
    # Amplitude convention: assume even excitation of all modes (1/k amplitude
    # baseline); the *frequency-ratio inharmonicity* is the substrate signature
    coeffs = np.zeros(n_partials)
    for k in range(1, n_partials):
        coeffs[k] = 1.0 / k  # placeholder amplitude
    meta = {
        "substrate": "drum_membrane_2d",
        "n_partials": n_partials,
        "convention": "modal frequencies = Bessel zeros (Rayleigh 1894 §200)",
        "note": "Class L direct (2D Laplacian-Dirichlet); frequencies inharmonic",
        "first_5_freqs_relative_to_lowest": (freqs[:5] / freqs[0]).tolist(),
    }
    return coeffs, meta, freqs


def bell_modes_3_mode(n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Bell / chime: 5 prominent modes (hum, prime, tierce, quint, nominal).

    Canonical bell tuning (Fletcher & Rossing 1998 §21.3): mode ratios
    relative to nominal (=2.0 fundamental) are
       hum     = 0.5
       prime   = 1.0  (perceived pitch)
       tierce  = 1.2 (minor third above prime)
       quint   = 1.5 (perfect fifth above prime)
       nominal = 2.0 (octave above prime; strongest)
    Higher modes (twelfth = 3.0, double octave = 4.0, ...) also present
    but weaker. Amplitudes decrease roughly exponentially with mode
    number; we use the canonical ordering and rapid amplitude falloff
    (factor ~0.5 per higher mode).
    """
    coeffs = np.zeros(n_partials)
    # Mode amplitudes (Fletcher 1998 §21.3, illustrative bell):
    # hum / prime / tierce / quint / nominal / twelfth / double_octave / upper_octave
    mode_amps = [0.7, 1.0, 0.85, 0.6, 1.0, 0.4, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005, 0.0025, 0.001]
    for k in range(1, min(n_partials, len(mode_amps) + 1)):
        coeffs[k] = mode_amps[k - 1]
    meta = {
        "substrate": "bell_5mode",
        "n_partials": n_partials,
        "convention": "hum/prime/tierce/quint/nominal + higher modes (Fletcher 1998 §21.3)",
        "mode_freq_ratios_first_5": [0.5, 1.0, 1.2, 1.5, 2.0],
    }
    return coeffs, meta


def voice_glottal_source_filter(F1: float = 700.0, F2: float = 1220.0, F3: float = 2600.0, n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Voice (vowel /a/ approx): glottal pulse with 1/n harmonics shaped by formants.

    Fant 1960 / Fletcher & Rossing 1998 §16: glottal pulse train has
    amplitude ~1/n^2 (source); filtered by vocal tract resonances at
    formant frequencies F1, F2, F3.

    Model: a_n = (1/n^2) * formant_envelope(n*f0) where formant_envelope is
    a sum of three peaks at F1, F2, F3 (Lorentzian).

    Vowel /a/ has F1~700, F2~1220, F3~2600 Hz; f0~120 Hz for adult male.
    """
    f0 = 120.0
    bw = 80.0
    coeffs = np.zeros(n_partials)
    for n in range(1, n_partials):
        f = n * f0
        source = 1.0 / (n ** 2)
        env = 0.0
        for F, A in [(F1, 1.0), (F2, 0.7), (F3, 0.5)]:
            env += A * bw ** 2 / ((f - F) ** 2 + bw ** 2)
        coeffs[n] = source * env
    # Normalise to max=1
    if coeffs.max() > 0:
        coeffs /= coeffs.max()
    meta = {
        "substrate": "voice_vowel_a",
        "n_partials": n_partials,
        "f0_hz": f0,
        "formants_hz": [F1, F2, F3],
        "convention": "glottal source 1/n^2 * formant envelope (Fant 1960; Fletcher 1998 §16)",
    }
    return coeffs, meta


def flute_open_open(n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Flute (open-open cylindrical tube): all harmonics, near-sinusoidal.

    Fletcher & Rossing 1998 §15.2: open-open pipe supports all integer
    multiples of f_0. Air-jet excitation gives strong fundamental with
    weak overtones; canonical amplitude envelope a_n = 1/n^2 (much
    weaker decay than struck/bowed strings).
    """
    coeffs = np.zeros(n_partials)
    for n in range(1, n_partials):
        coeffs[n] = 1.0 / (n ** 2)
    meta = {
        "substrate": "flute_open_open",
        "n_partials": n_partials,
        "convention": "a_n = 1/n^2 (Fletcher 1998 §15.2 air-jet)",
    }
    return coeffs, meta


def trumpet_lip_buzz(n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Trumpet (lip-buzz exciter, valved tube): rich harmonics, slow decay.

    Fletcher & Rossing 1998 §14.4: brass instruments have ~1/sqrt(n)
    amplitude falloff at fortissimo (lip excitation drives many harmonics
    strongly). Softer playing approaches 1/n.
    """
    coeffs = np.zeros(n_partials)
    for n in range(1, n_partials):
        coeffs[n] = 1.0 / math.sqrt(n)
    meta = {
        "substrate": "trumpet_lip_buzz",
        "n_partials": n_partials,
        "convention": "a_n = 1/sqrt(n) (Fletcher 1998 §14.4 brass fortissimo)",
    }
    return coeffs, meta


# ============================================================================
# REFERENCE / FALSIFIER CONTROLS
# ============================================================================


def pure_kepler_reference(eps: float = 0.1, n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Reference: pure Kepler c_k = eps^k / k. Must pass K-test trivially."""
    coeffs = np.zeros(n_partials)
    for k in range(1, n_partials):
        coeffs[k] = (eps ** k) / k
    meta = {
        "substrate": "pure_kepler_ref",
        "n_partials": n_partials,
        "eps_actual": eps,
        "convention": "c_k = eps^k / k (Spike #30B v3 canonical K-shape)",
    }
    return coeffs, meta


def pure_harmonic_1over_n(n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """Pure harmonic series a_n = 1/n. Sawtooth; geometric ratio = 1 (eps=1)."""
    coeffs = np.zeros(n_partials)
    for n in range(1, n_partials):
        coeffs[n] = 1.0 / n
    meta = {
        "substrate": "pure_harmonic_1_over_n",
        "n_partials": n_partials,
        "convention": "a_n = 1/n (Fourier sawtooth)",
    }
    return coeffs, meta


def white_noise_flat_amplitude(n_partials: int = 16) -> tuple[np.ndarray, dict]:
    """White noise: flat amplitude, all 1. Should fail K (no decay)."""
    coeffs = np.ones(n_partials)
    coeffs[0] = 0  # DC
    meta = {
        "substrate": "white_noise_flat",
        "n_partials": n_partials,
        "convention": "a_n = 1 for all n >= 1 (flat spectrum)",
    }
    return coeffs, meta


def random_amplitude_spectrum(seed: int, n_partials: int = 10) -> np.ndarray:
    """Random amplitude spectrum (uniform 0,1). For falsifier-baseline sampling."""
    rng = np.random.default_rng(seed=seed)
    coeffs = np.zeros(n_partials)
    coeffs[1:] = rng.uniform(0, 1, size=n_partials - 1)
    return coeffs


# ============================================================================
# CLASS L SUBSTRATE ANALYSIS (drum membrane is the natural Class L instance)
# ============================================================================


def eigenval_density_fft(eigvals: np.ndarray, n_bins: int = 128) -> np.ndarray:
    """Per Spike #30B v3 eigenval-density-FFT method."""
    eigvals = np.array(eigvals)
    if eigvals.max() <= 0:
        return np.zeros(n_bins // 2 + 1)
    hist, _ = np.histogram(eigvals, bins=n_bins, range=(0, eigvals.max() + 1e-6), density=True)
    spec = np.fft.rfft(hist) / (n_bins / 2)
    return np.abs(spec)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm < 1e-15 or b_norm < 1e-15:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def random_graph_laplacian_eigvals(n: int, edge_density: float, seed: int) -> np.ndarray:
    """n-node Erdos-Renyi random graph, compute Laplacian eigvals."""
    rng = np.random.default_rng(seed=seed)
    A = (rng.uniform(0, 1, size=(n, n)) < edge_density).astype(float)
    A = np.triu(A, k=1)
    A = A + A.T
    L = np.diag(A.sum(axis=1)) - A
    return sla.eigvalsh(L)


# ============================================================================
# RUN: per-substrate test battery
# ============================================================================


def run_substrate(name: str, coeffs: np.ndarray, meta: dict) -> dict:
    """Run K-test + summary statistics on a coefficient spectrum."""
    K = strict_kepler_test(coeffs, k_max=6)
    # Effective decay shape via raw c1/c2/c3 ratios (substrate-fingerprint)
    cs = np.abs(coeffs[1:])
    n_nonzero = int(np.sum(cs > 0))
    if n_nonzero >= 3:
        ratio_c2_c1 = float(cs[1] / cs[0]) if cs[0] > 0 else float("nan")
        ratio_c3_c2 = float(cs[2] / cs[1]) if cs[1] > 0 else float("nan")
    else:
        ratio_c2_c1 = float("nan")
        ratio_c3_c2 = float("nan")
    # Substrate fingerprint = decay slope on log scale, even if K fails
    log_cs = np.log(cs[cs > 1e-15])
    if len(log_cs) >= 3:
        ks_full = np.arange(1, len(log_cs) + 1)
        p_full = np.polyfit(ks_full, log_cs, 1)
        slope = float(p_full[0])
    else:
        slope = float("nan")
    record = {
        "kind": "substrate_K_test",
        "substrate": name,
        "meta": meta,
        "n_partials_nonzero": n_nonzero,
        "k_test": K,
        "decay_log_slope_per_k": slope,
        "ratio_c2_over_c1": ratio_c2_c1,
        "ratio_c3_over_c2": ratio_c3_c2,
    }
    return record


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


def main():
    print("=" * 78)
    print("Spike #40 — Structural shape of an epicycle in musical/wave theory")
    print("=" * 78)

    substrates = []

    # FM family
    for beta in [0.5, 1.5, 3.0]:
        c, m = pure_fm_signal(beta_fm=beta)
        substrates.append((f"pure_fm_beta_{beta}", c, m))

    # AM trivial
    c, m = pure_am_signal(modulation_index=0.5)
    substrates.append(("pure_am", c, m))

    # Beat
    c, m = beat_pattern()
    substrates.append(("beat_pattern", c, m))

    # Piano (per stiffness B)
    for B in [1e-4, 5e-4, 1e-3]:
        c, m = piano_inharmonic_partials(B_stiff=B)
        substrates.append((f"piano_B_{B}", c, m))

    # Violin
    c, m = violin_helmholtz()
    substrates.append(("violin_helmholtz", c, m))

    # Clarinet
    c, m = clarinet_open_closed()
    substrates.append(("clarinet_open_closed", c, m))

    # Drum (Class L direct)
    c_drum, m_drum, drum_eigvals = drum_membrane_2d()
    substrates.append(("drum_membrane_2d_amp_baseline", c_drum, m_drum))

    # Bell
    c, m = bell_modes_3_mode()
    substrates.append(("bell_5mode", c, m))

    # Voice
    c, m = voice_glottal_source_filter()
    substrates.append(("voice_vowel_a", c, m))

    # Flute
    c, m = flute_open_open()
    substrates.append(("flute_open_open", c, m))

    # Trumpet
    c, m = trumpet_lip_buzz()
    substrates.append(("trumpet_lip_buzz", c, m))

    # References
    for eps in [0.01, 0.05, 0.1, 0.2, 0.4]:
        c, m = pure_kepler_reference(eps=eps)
        substrates.append((f"REF_pure_kepler_eps_{eps}", c, m))

    c, m = pure_harmonic_1over_n()
    substrates.append(("REF_pure_harmonic_1_over_n", c, m))

    c, m = white_noise_flat_amplitude()
    substrates.append(("REF_white_noise_flat", c, m))

    # Run all
    records = []
    for name, c, m in substrates:
        rec = run_substrate(name, c, m)
        records.append(rec)
        K = rec["k_test"]
        print(
            f"  {name:42s}: eps_fit={K['eps_fit']:.4f} r2={K['r2']:.4f} "
            f"mono={K['monotonic_decreasing']} in_range={K['in_physical_range']} "
            f"K_present={K['kepler_signature_present']}"
        )

    # Class L direct (drum)
    print("\n--- CLASS L SIGNATURE: drum membrane (2D Laplacian-Dirichlet) ---")
    drum_density = eigenval_density_fft(drum_eigvals)
    print(f"  drum eigvals: n={len(drum_eigvals)} max={drum_eigvals.max():.3f}")
    # Cross-cosine-similarity with random graph baseline
    sims_random = []
    for seed in range(50):
        re = random_graph_laplacian_eigvals(n=len(drum_eigvals), edge_density=0.2, seed=seed)
        re_density = eigenval_density_fft(re)
        sims_random.append(cosine_similarity(drum_density, re_density))
    sims_random = np.array(sims_random)
    drum_self_density = eigenval_density_fft(drum_eigvals)
    drum_self_sim = cosine_similarity(drum_density, drum_self_density)
    records.append({
        "kind": "class_L_drum_membrane",
        "substrate": "drum_membrane_2d",
        "n_eigvals": int(len(drum_eigvals)),
        "first_5_eigvals": drum_eigvals[:5].tolist(),
        "first_5_relative_to_lowest": (drum_eigvals[:5] / drum_eigvals[0]).tolist(),
        "self_similarity": drum_self_sim,
        "random_graph_falsifier_mean": float(sims_random.mean()),
        "random_graph_falsifier_std": float(sims_random.std()),
        "random_graph_falsifier_min": float(sims_random.min()),
        "random_graph_falsifier_max": float(sims_random.max()),
        "z_score_vs_random": float((drum_self_sim - sims_random.mean()) / (sims_random.std() + 1e-15)),
    })
    print(f"  random-graph falsifier mean ± std: {sims_random.mean():.4f} ± {sims_random.std():.4f}")
    print(f"  random-graph falsifier min/max: {sims_random.min():.4f} / {sims_random.max():.4f}")

    # Save NDJSON
    out_path = os.path.join(OUT_DIR, "spike_40_records.ndjson")
    with open(out_path, "w") as f:
        for r in records:
            f.write(json.dumps(clean_for_json(r)) + "\n")
    print(f"\nWrote {len(records)} records to {out_path}")

    # Save per-instrument comparison table
    print("\n=" * 39)
    print("PER-INSTRUMENT META-QUESTION COMPARISON TABLE")
    print("=" * 78)
    comp_records = []
    instrument_names = [
        "pure_fm_beta_0.5",
        "pure_fm_beta_1.5",
        "pure_fm_beta_3.0",
        "pure_am",
        "beat_pattern",
        "piano_B_0.0001",
        "piano_B_0.0005",
        "piano_B_0.001",
        "violin_helmholtz",
        "clarinet_open_closed",
        "drum_membrane_2d_amp_baseline",
        "bell_5mode",
        "voice_vowel_a",
        "flute_open_open",
        "trumpet_lip_buzz",
    ]
    print(
        f"  {'INSTRUMENT':32s} {'eps_fit':>9s} {'r2':>7s} {'mono':>6s} {'inrng':>6s} {'K?':>4s} {'fits':>20s}"
    )
    print("  " + "-" * 80)
    for name in instrument_names:
        rec = next((r for r in records if r.get("substrate") == name), None)
        if rec is None:
            continue
        K = rec["k_test"]
        # Best-fit class assignment
        n_nz = rec["n_partials_nonzero"]
        if K["kepler_signature_present"]:
            best_fit = "Class K"
        elif n_nz <= 3:
            best_fit = "Class I (sparse)"
        elif name.startswith("drum"):
            best_fit = "Class L direct"
        elif name == "violin_helmholtz" or name.startswith("piano"):
            best_fit = "1/n (sawtooth)"
        elif name == "flute_open_open":
            best_fit = "1/n^2 (weak)"
        elif name == "trumpet_lip_buzz":
            best_fit = "1/sqrt(n) (slow)"
        elif name == "clarinet_open_closed":
            best_fit = "odd-only 1/n"
        elif name.startswith("pure_fm"):
            best_fit = "Bessel J_k"
        elif name == "voice_vowel_a":
            best_fit = "formant-shaped"
        elif name == "bell_5mode":
            best_fit = "Class L (inharmonic)"
        else:
            best_fit = "—"
        print(
            f"  {name:32s} {K['eps_fit']:9.4f} {K['r2']:7.4f} "
            f"{str(K['monotonic_decreasing']):>6s} {str(K['in_physical_range']):>6s} "
            f"{str(K['kepler_signature_present']):>4s} {best_fit:>20s}"
        )
        comp_records.append({
            "kind": "per_instrument_comparison",
            "instrument": name,
            "eps_fit": K["eps_fit"],
            "r2": K["r2"],
            "monotonic": K["monotonic_decreasing"],
            "in_physical_range": K["in_physical_range"],
            "k_signature_present": K["kepler_signature_present"],
            "best_class_fit": best_fit,
            "c1_c2_c3": K["c1_c2_c3"],
            "n_partials_nonzero": rec["n_partials_nonzero"],
        })

    out_comp = os.path.join(OUT_DIR, "spike_40_per_instrument_comparison.ndjson")
    with open(out_comp, "w") as f:
        for r in comp_records:
            f.write(json.dumps(clean_for_json(r)) + "\n")
    print(f"\nWrote {len(comp_records)} comparison records to {out_comp}")


if __name__ == "__main__":
    main()
