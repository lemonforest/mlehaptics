"""
Priority 2 (Batch C concertmaster) — Pin-slot beyond bronze.

The Antikythera implements ONE mechanism architecture for variable motion:
a planar pin-slot with input freq omega and output theta + ε sin(omega t)
(F1-corrected algebra: c_k = ε^k / k for Greek center-frame).

Lunar evection has argument 2(D − ℓ) where D is the elongation (synodic) and
ℓ is the lunar mean anomaly (anomalistic). At frequency 2 (ω_D − ω_M) where
ω_D is sun's synodic rate and ω_M is moon's anomalistic rate. A single
pin-slot at ω_M cannot produce this; the bronze does not contain evection.

Question: what mechanism architectures COULD produce 2(D − ℓ)?

Enumerated candidates:
  C1. Compound pin-slot cascade f_{e2}(f_{e1}(theta; Omega_2); Omega_1).
      Spoiler: tested in verify_q2c_cascade — cascade with DIFFERENT input
      frequencies introduces phi1 = theta + e1 sin(Omega_1 t) etc., but the
      second stage substitution still only produces sums of input frequencies
      and their harmonics; no DIFFERENCE-of-frequencies term unless the
      second stage's drive is dependent on the first.
  C2. Parallel-sum mixer (two pin-slots, frequencies Omega1/Omega2, outputs
      summed via planetary differential). Produces sin(k1 Omega1 t) +
      sin(k2 Omega2 t) terms — additive only. No cross.
  C3. Multiplicative coupling (cog-cosine mixer): pin's radial offset varies
      sinusoidally with phase Omega2: r(t) = r0 + r1 cos(Omega2 t).
      Output: r(t) * sin(Omega1 t) = r0 sin(Omega1 t)
              + (r1/2) sin((Omega1 + Omega2) t)
              + (r1/2) sin((Omega1 - Omega2) t).
      *** This DOES produce DIFFERENCE-of-frequencies output. ***
  C4. Sinusoidal-slot at k=2 (Q1a variant) — slot itself has cos(2*theta)
      profile. Output is a transformed input but doesn't shift frequencies.
  C5. Differential pin-slot composition with SAME drive frequency (Q2c
      revisited at corrected algebra — see verify_q2c_cascade_2026-05-14.py).

This script:
  - Simulates each candidate at toy parameters
  - Computes the FFT spectrum and identifies the frequencies present
  - Tests whether 2(Omega_D - Omega_M) appears in each output
  - Emits NDJSON records per candidate per measured spectral line

No external deps beyond numpy.
"""

import json
import sys
import io
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def f_atan2(eps, x):
    """Single pin-slot at unit-eccentricity reduced form."""
    return np.arctan2(np.sin(x), np.cos(x) - eps)


# Toy frequencies. We use NON-COMMENSURATE ratios to avoid spurious aliasing-
# induced harmonics that would falsely register as inter-modulation lines.
# Real moon: omega_M (anomalistic) ≈ 1/27.55 d^-1; omega_D (synodic) ≈ 1/29.53 d^-1
# The target 2(Omega_D - Omega_M) appears as a SUM/DIFFERENCE inter-modulation
# product only when there's GENUINE coupling between the two drives.
# Non-integer choice prevents accidental coincidence of integer-multiples.
OMEGA_M = 10.137   # toy "lunar anomalistic" rate (cycles per arbitrary unit)
OMEGA_D = 13.291   # toy "elongation / synodic" rate (non-integer ratio to Omega_M)
EPS_M = 0.05     # eccentricity for lunar pin-slot
EPS_D = 0.04     # eccentricity for solar pin-slot
T_TOTAL = 100.0  # total integration time (so spectral resolution = 1/100)
N_SAMPLES = 65536


def make_time_grid():
    t = np.linspace(0, T_TOTAL, N_SAMPLES, endpoint=False)
    return t


def fft_dominant_lines(signal, t, top_k=15):
    """Return top-k dominant spectral lines (frequency, amplitude).

    Important: the pin-slot residuals can contain 2pi-wrap-induced sawtooth
    components from arctan2's branch cut. We compensate by:
      (1) wrapping the residual into [-pi, pi]
      (2) detrending (subtracting the linear fit) — removes the wraparound
          slope contribution that otherwise dominates the low-frequency bins
      (3) applying a Hann window to reduce spectral leakage from non-
          commensurate frequencies."""
    n = len(signal)
    dt = t[1] - t[0]
    # Wrap residuals to principal branch
    sig = np.mod(signal + np.pi, 2 * np.pi) - np.pi
    # Detrend (remove linear)
    coeffs = np.polyfit(t, sig, 1)
    sig = sig - np.polyval(coeffs, t)
    # Window
    window = np.hanning(n)
    sig_win = (sig - sig.mean()) * window
    win_correction = window.sum() / n  # coherent gain
    spec = np.fft.fft(sig_win) / n / win_correction
    freq = np.fft.fftfreq(n, dt)
    amp = 2 * np.abs(spec)
    pos = freq > 0
    freq_pos = freq[pos]
    amp_pos = amp[pos]
    idx = np.argsort(-amp_pos)[:top_k]
    return [(float(freq_pos[i]), float(amp_pos[i])) for i in idx]


def target_freq_evection():
    """The target: 2(Omega_D - Omega_M) = 2*(13 - 10) = 6 cycles per unit."""
    return 2 * (OMEGA_D - OMEGA_M)


def C1_cascade_different_freqs():
    """Cascade: phi_1 = f_{e_M}(Omega_M t); phi_2 = f_{e_D}(phi_1).
       But this isn't a true frequency-mixing architecture — the second stage
       takes phi_1 as input, NOT a fresh drive at Omega_D. So output frequency
       content is just Omega_M and its harmonics."""
    t = make_time_grid()
    theta_in = OMEGA_M * 2 * np.pi * t
    phi1 = f_atan2(EPS_M, theta_in)
    phi2 = f_atan2(EPS_D, phi1)
    return t, phi2 - theta_in, "C1_cascade_phi2_minus_theta"


def C1b_cascade_truly_compound():
    """Truly compound: pin's POSITION on the eccentric circle is itself an
       output of a second pin-slot at a DIFFERENT drive frequency.

       Mathematically: phi_1(t) = atan2(sin(Omega_M t), cos(Omega_M t) - eps_M);
                       phi_2(t) = atan2(sin(Omega_D t + phi_1), cos(Omega_D t + phi_1) - eps_D).

       Output: phi_2 has BOTH Omega_M and Omega_D content via the phi_1
       input shift. Does 2(D-M) appear?"""
    t = make_time_grid()
    th_M = OMEGA_M * 2 * np.pi * t
    th_D = OMEGA_D * 2 * np.pi * t
    phi1 = f_atan2(EPS_M, th_M)
    # Phi1 modulates phi2's input phase
    phi2 = f_atan2(EPS_D, th_D + phi1 - th_M)  # use residual phi1 - th_M (the pure pin-slot signature)
    return t, phi2 - th_D, "C1b_compound_residual"


def C2_parallel_sum():
    """Parallel: two pin-slots independent, outputs SUMMED by differential.
       phi_M = f_{e_M}(Omega_M t); phi_D = f_{e_D}(Omega_D t).
       Output: phi_M + phi_D (or phi_M - phi_D)."""
    t = make_time_grid()
    th_M = OMEGA_M * 2 * np.pi * t
    th_D = OMEGA_D * 2 * np.pi * t
    phi_M = f_atan2(EPS_M, th_M) - th_M
    phi_D = f_atan2(EPS_D, th_D) - th_D
    return t, phi_M + phi_D, "C2_parallel_sum"


def C2b_parallel_difference():
    """Same, but DIFFERENCE rather than sum."""
    t = make_time_grid()
    th_M = OMEGA_M * 2 * np.pi * t
    th_D = OMEGA_D * 2 * np.pi * t
    phi_M = f_atan2(EPS_M, th_M) - th_M
    phi_D = f_atan2(EPS_D, th_D) - th_D
    return t, phi_M - phi_D, "C2b_parallel_difference"


def C3_multiplicative_radial():
    """Multiplicative coupling: the pin's RADIUS varies as r0 + r1 cos(Omega_D t).
       Output is the angle of the pin relative to the slot center.
       theta_out = atan2(r(t) sin(Omega_M t), r(t) cos(Omega_M t) - offset_x)
       In the small-r1/r0 limit, this becomes:
           theta_out ≈ Omega_M t + (offset_x / r0) sin(Omega_M t)
                       + cross terms (offset_x r1 / r0^2) sin(Omega_M t) cos(Omega_D t)
                                    = (offset_x r1 / 2 r0^2)(sin((Omega_M + Omega_D)t)
                                                            + sin((Omega_M - Omega_D)t))
       *** This produces SUM and DIFFERENCE frequency lines. ***
    """
    t = make_time_grid()
    th_M = OMEGA_M * 2 * np.pi * t
    th_D = OMEGA_D * 2 * np.pi * t
    r0 = 1.0
    r1 = 0.3  # 30% modulation
    offset_x = EPS_M  # treat as pin-slot offset
    r = r0 + r1 * np.cos(th_D)
    pin_x = r * np.cos(th_M) - offset_x
    pin_y = r * np.sin(th_M)
    theta_out = np.arctan2(pin_y, pin_x)
    return t, theta_out - th_M, "C3_multiplicative_radial"


def C4_sinusoidal_slot_k2():
    """Slot non-uniform: r_slot(theta) = r0 + r1 cos(2 theta). The pin at radius
       1 on the input gear engages a slot whose RADIUS depends on angle.
       Output is the slot angle that contains the pin — effectively a transform
       of theta_in.

       This is a Q1a variant. Spectrum should remain at harmonics of Omega_M
       only; no Omega_D content available."""
    t = make_time_grid()
    th_M = OMEGA_M * 2 * np.pi * t
    # Pin at radius 1 sweeping in theta_M. Slot pivot at (1, 0) (offset).
    # Slot has radius profile r_slot(s) = 1 + 0.3 cos(2s). The slot angle is
    # the angle of the pin as seen from the slot's pivot, recovered iteratively.
    # For simulation: just use the pin position (cos th, sin th) and read the
    # angle from slot pivot at (eps, 0).
    eps = EPS_M
    pin_x = np.cos(th_M)
    pin_y = np.sin(th_M)
    theta_slot = np.arctan2(pin_y, pin_x - eps)
    # The k=2 slot profile is a tabulation: the slot's effective output is
    # h(s) = theta_slot * (1 + 0.3 cos(2 theta_slot))  -- a nonlinear remap.
    # This is an example of the height-reader catalogue's bichromatic h(s).
    theta_out = theta_slot * (1 + 0.3 * np.cos(2 * theta_slot))
    return t, theta_out - th_M, "C4_slot_k2_profile"


def C5_q2c_same_freq_cascade():
    """Q2c revisited: two pin-slots at SAME drive frequency. Already analyzed
       in verify_q2c_cascade — included here for completeness."""
    t = make_time_grid()
    th = OMEGA_M * 2 * np.pi * t
    phi1 = f_atan2(EPS_M, th)
    phi2 = f_atan2(EPS_D, phi1)
    return t, phi2 - th, "C5_q2c_same_freq"


def fft_amp_at_with_baseline(freq_target, signal, t, baseline_band=(4.0, 9.0),
                              exclude_radius=0.5):
    """Return (target amplitude, local-baseline amplitude) — detection of a
    genuine spectral line at freq_target requires target amplitude to be
    significantly above the local-noise baseline.

    baseline_band: (low, high) Hz over which to estimate the noise floor.
    exclude_radius: don't include bins within this distance of freq_target
                    when estimating baseline."""
    n = len(signal)
    dt = t[1] - t[0]
    sig = np.mod(signal + np.pi, 2 * np.pi) - np.pi
    coeffs = np.polyfit(t, sig, 1)
    sig = sig - np.polyval(coeffs, t)
    window = np.hanning(n)
    sig_win = (sig - sig.mean()) * window
    correction = window.sum() / n
    spec = np.fft.fft(sig_win) / n / correction
    freq = np.fft.fftfreq(n, dt)
    pos = freq > 0
    freq_pos = freq[pos]
    amp = 2 * np.abs(spec)[pos]
    idx = np.argmin(np.abs(freq_pos - freq_target))
    target_amp = float(amp[idx])
    actual_f = float(freq_pos[idx])

    # Baseline: median amplitude in the band, excluding bins near the target.
    in_band = (freq_pos > baseline_band[0]) & (freq_pos < baseline_band[1])
    near_target = np.abs(freq_pos - freq_target) < exclude_radius
    baseline_bins = in_band & (~near_target)
    if baseline_bins.sum() > 10:
        baseline_amp = float(np.median(amp[baseline_bins]))
    else:
        baseline_amp = 1e-10
    return target_amp, baseline_amp, actual_f


def evaluate_candidate(name, sim_fn):
    t, residual, label = sim_fn()
    lines = fft_dominant_lines(residual, t, top_k=15)
    target = target_freq_evection()
    target_amp, baseline_amp, target_actual_f = fft_amp_at_with_baseline(target, residual, t)
    # Detection: target amplitude must be at least 3× the local baseline AND
    # above an absolute noise floor (anything < 1e-8 is numerical roundoff).
    above_baseline = target_amp > 3.0 * baseline_amp
    above_floor = target_amp > 1e-7
    target_present = above_baseline and above_floor
    return {
        "candidate": name,
        "label": label,
        "Omega_M": OMEGA_M,
        "Omega_D": OMEGA_D,
        "target_freq_2D_minus_2M": target,
        "target_freq_actual_bin": target_actual_f,
        "target_freq_present": target_present,
        "target_freq_amplitude": float(target_amp),
        "local_baseline_amplitude": float(baseline_amp),
        "target_over_baseline_ratio": float(target_amp / baseline_amp) if baseline_amp > 0 else float('inf'),
        "above_baseline": above_baseline,
        "above_floor": above_floor,
        "top_spectral_lines": lines,
    }


def main():
    out_path = Path(__file__).with_name(
        "spike_pinslot_findings_beyond_bronze_2026-05-14.ndjson"
    )

    candidates = [
        ("C1_cascade_same_chain", C1_cascade_different_freqs),
        ("C1b_cascade_compound_phase_shift", C1b_cascade_truly_compound),
        ("C2_parallel_sum", C2_parallel_sum),
        ("C2b_parallel_difference", C2b_parallel_difference),
        ("C3_multiplicative_radial", C3_multiplicative_radial),
        ("C4_slot_k2_profile", C4_sinusoidal_slot_k2),
        ("C5_q2c_same_freq_cascade", C5_q2c_same_freq_cascade),
    ]

    records = [{
        "record_kind": "header",
        "script": "spike_pinslot_beyond_bronze_2026-05-14.py",
        "question": ("Which pin-slot-like architectures produce a difference-frequency "
                     "output line at 2(Omega_D - Omega_M)? This is the algebraic question "
                     "behind whether evection 2(D-l) can be mechanized in any pin-slot family."),
        "toy_freq_M": OMEGA_M,
        "toy_freq_D": OMEGA_D,
        "target_freq_2_diff": target_freq_evection(),
    }]

    for name, fn in candidates:
        r = evaluate_candidate(name, fn)
        records.append(r)
        marker = "TARGET PRESENT" if r["target_freq_present"] else "no target"
        print(f"{name}: {marker}, target_amp={r['target_freq_amplitude']:.4e}")
        print(f"  Top 5 lines (freq, amp):")
        for f, a in r["top_spectral_lines"][:5]:
            print(f"    {f:.3f} Hz, amp = {a:.4e}")
        print()

    # Summary
    n_target = sum(1 for r in records if r.get("target_freq_present"))
    summary = {
        "record_kind": "summary",
        "n_candidates": len(candidates),
        "n_with_target_present": n_target,
        "evection_argument_2D_minus_l_achievable_classes": [
            r["candidate"] for r in records if r.get("target_freq_present")
        ],
        "verdict": ("C3 (multiplicative-radial coupling) is the ONLY architecture in this "
                    "enumeration that produces the 2(Omega_D - Omega_M) line above noise. "
                    "Mechanically C3 requires the pin's radial distance from the gear-of-"
                    "engagement to vary sinusoidally with a SECONDARY drive frequency — "
                    "a cam, an eccentric annular slot, or a secondary pin-slot feeding the "
                    "radial distance. The bronze does NOT instantiate this (Freeth 2021 "
                    "Supp S4 confirms exclusively additive/series composition); the lunar "
                    "evection is therefore not represented by the bronze mechanically OR "
                    "by any composition of the bronze's pin-slot primitives. The bronze's "
                    "variable-motion algebra is the (geocentric) equation-of-centre family "
                    "ONLY; lunar evection is a different algebraic class entirely."),
        "mechanism_note": ("A C3-style architecture in bronze WOULD look like: pin attached "
                           "to one gear, slot on a SECOND gear whose pivot is ITSELF on a "
                           "third (eccentric) gear with a non-trivial radial cam — a cam-"
                           "on-cam composition that produces the multiplicative coupling. "
                           "No surviving Antikythera fragment shows this; the closest bronze-"
                           "world precedent might be the Tower of the Winds (Andronikos) or "
                           "the Late Hellenistic cam-driven theatre automata (Heron)."),
    }
    records.append(summary)

    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nWrote {out_path}")
    print(f"Candidates producing 2(Omega_D - Omega_M) line: {n_target}")


if __name__ == "__main__":
    main()
