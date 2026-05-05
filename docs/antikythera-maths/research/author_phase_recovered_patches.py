"""Phase-recovered catalog patch authoring.

The v0.4.0 catalog was authored from the v0.3.1 FFT residual peaks
using *magnitude only* (with `phase_rad=0`). The first
patch-shrinks-residual benchmark (v0.5.1) showed this is insufficient:

  * `mars-7.96yr-diagonal`: shrinks Mars 7.96-yr peak by only 2.5%
  * `mercury-10.69yr-diagonal`: GROWS Mercury's peak by 49.9%
  * `jupiter-saturn-9.56yr-coupled`: 30.9% on Jupiter, ~0% on Saturn

Why: the patches assume `phase_rad=0` (a bare sin shape), but the
actual residual at the target period has some other phase. With the
wrong phase, the patch either partially cancels, has no effect, or
ADDS to the residual instead of subtracting from it.

Fix: extract amplitude AND phase from the FFT's complex spectrum,
not just the magnitude. For an FFT bin `X[k]`, the residual contains
the sinusoidal component

    s(t) = (2/N) * |X[k]| * cos(2π k t / span - arg(X[k]))

To CANCEL this with a sinusoidal-patch overlay (which evaluates as
`A * sin(2π t / period + phi)`), we need

    A * sin(2π t / period + phi) = -s(t)

Working through the trig (cos vs sin offset by π/2):

    A    = (2/N) * |X[k]|
    phi  = -arg(X[k]) - π/2 + π     # the "+π" flips sign for cancellation
         = π/2 - arg(X[k])

Equivalently `A = (2/N)|X[k]|` and `phi = π/2 - arg(X[k]) (mod 2π)`.

This script:

1. Runs the v0.5.0 encoder over the same 1024-sample grid the FFT
   sweep uses (no patches active).
2. For each catalog target (body + expected_period_yr), finds the
   FFT bin whose period is closest to the target.
3. Extracts amplitude (deg) and phase (rad) from the complex bin.
4. Emits a phase-recovered patch dataclass per catalog entry.
5. Writes the recovered catalog to
   `results/phase_recovered_catalog.json`.

The benchmark (`patch_shrinks_residual.py`) then has the option to
run with the original catalog OR the phase-recovered one; if the
recovered one hits >= 80% shrinkage, the methodology is
*vindicated* — modulo phase recovery, the spectral-FFT-diagnose-
then-overlay approach IS a working forecasting tool.

Run from the repo root with `skyfield_data/de441.bsp` staged + the
native binary loaded:

    cd docs/antikythera-maths
    python -m research.author_phase_recovered_patches
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.bip_instrument import (             # noqa: E402
    EphemerisBIPInstrument,
    MODULO,
    REFERENCE_JD,
)
from research.de441_error_spectrum import (       # noqa: E402
    N_SAMPLES_DEFAULT,
    CADENCE_DAYS_DEFAULT,
    _angular_diff,
    _truth_longitude,
)

try:
    from ephemerides_spectral import _native_bip
except ImportError:
    _native_bip = None  # type: ignore[assignment]


# Catalog targets: which body + expected_period_yr each patch attacks.
# Mirrors patch_shrinks_residual.PATCH_TARGETS but explicit here so
# this module is self-contained.
PATCH_TARGETS: Dict[str, Dict] = {
    "mars-7.96yr-diagonal": {
        "body": "mars",
        "expected_period_yr": 7.96,
        "kind": "sinusoid",
    },
    "mercury-10.69yr-diagonal": {
        "body": "mercury",
        "expected_period_yr": 10.69,
        "kind": "sinusoid",
    },
    "jupiter-saturn-9.56yr-coupled": {
        "body_a": "jupiter",
        "body_b": "saturn",
        "expected_period_yr": 9.56,
        "kind": "coupled-sinusoid",
        # `correlation` for the coupled-sinusoid is recovered empirically:
        # if J and S residuals at the target period have phases offset
        # by ~π, correlation = -1 (anti-correlated, the classical
        # libration assumption); if offset by ~0, correlation = +1.
    },
}


def _gather_residuals(n_samples: int, cadence_days: float) -> Tuple[Dict[str, np.ndarray], np.ndarray, EphemerisBIPInstrument]:
    """Run the encoder over the grid, return per-body signed residual
    arrays + the JD grid + the instrument (for body_to_idx).

    Mirrors `de441_error_spectrum.run_spectrum`'s data-gathering loop;
    duplicated here because we want the residual arrays themselves
    (not just the FFT summary).
    """
    inst = EphemerisBIPInstrument(
        D=2**12, kernel="de441", force_high_res=True,
    )
    bundle = inst.bundle
    bodies = [b for b in inst.body_names if b != "sun"]
    print(f"  ready: {len(inst.body_names)} bodies, kernel = {bundle.kernel_name}",
          flush=True)

    use_native = _native_bip is not None and _native_bip.HAS_NATIVE
    if use_native:
        print(f"  using native encoder v{_native_bip.native_version()}",
              flush=True)

    half_span_days = (n_samples * cadence_days) / 2.0
    jd_grid = REFERENCE_JD + np.arange(n_samples) * cadence_days - half_span_days
    errors: Dict[str, np.ndarray] = {b: np.zeros(n_samples) for b in bodies}

    t0 = time.perf_counter()
    for k, jd in enumerate(jd_grid):
        if use_native:
            phases = _native_bip.encode_state(float(jd) - REFERENCE_JD)
        else:
            phases = inst.encode_state(float(jd))
        for name in bodies:
            idx = inst.body_to_idx[name]
            bip_rad = (phases[idx] / MODULO) * 2.0 * np.pi
            try:
                truth_rad = _truth_longitude(bundle, float(jd), name)
            except (KeyError, ValueError):
                errors[name][k] = np.nan
                continue
            errors[name][k] = _angular_diff(bip_rad, truth_rad)
        if k % 64 == 0:
            print(f"    sample {k+1}/{n_samples}  elapsed={time.perf_counter()-t0:.1f}s",
                  flush=True)
    print(f"  encode + truth lookup: {time.perf_counter()-t0:.1f}s",
          flush=True)
    return errors, jd_grid, inst


def _detrend_and_fft(arr: np.ndarray, n_samples: int, cadence_yr: float):
    """Detrend + complex FFT. Returns (complex_spectrum, periods_yr).

    The frequency-zero (DC) bin is excluded from the periods array's
    "useful" range; callers should look up bins with k >= 1.
    """
    arr = np.where(np.isnan(arr), 0.0, arr)
    x = np.arange(n_samples)
    slope, intercept = np.polyfit(x, arr, 1)
    detrended = arr - (slope * x + intercept)
    spectrum = np.fft.rfft(detrended)
    freqs_per_yr = np.fft.rfftfreq(n_samples, d=cadence_yr)
    with np.errstate(divide="ignore"):
        periods_yr = np.where(freqs_per_yr > 0,
                              1.0 / freqs_per_yr, np.inf)
    return spectrum, periods_yr


def _bin_at_period(periods_yr: np.ndarray, target_yr: float) -> int:
    """Return the FFT bin index closest to `target_yr`.

    Skips bin 0 (DC, infinite period).
    """
    finite = np.where(np.isfinite(periods_yr) & (periods_yr > 0),
                      np.abs(periods_yr - target_yr), np.inf)
    finite[0] = np.inf
    return int(np.argmin(finite))


def _recover_patch(
    spectrum: np.ndarray,
    periods_yr: np.ndarray,
    target_yr: float,
    n_samples: int,
    cadence_days: float,
) -> Dict:
    """Recover (amplitude_deg, phase_rad) for a sinusoidal-overlay
    patch that cancels the residual sinusoid at the target period.

    Math derivation (real-valued residual at FFT bin m):

      residual_k = (2/N) * (Re(X[m])*cos(θ_k) - Im(X[m])*sin(θ_k))
                where θ_k = 2π·m·k/N

    Our overlay evaluates the patch at sample k as

      patch_k = A * sin(k·θ + ψ)
              where θ = 2π·m/N, ψ = φ - 2π·half_span/period_days
              and  φ = patch's stored `phase_rad`,
                   half_span = n_samples · cadence_days / 2

    (The `-2π·half_span/period` accounts for the patch using
    `delta_t = jd - REFERENCE_JD`, which is sample N/2, while the
    FFT's phase is referenced to sample 0 = REFERENCE_JD - half_span.)

    Setting patch_k + residual_k = 0 for all k and matching cos/sin
    coefficients:

      A · sin(ψ) = -(2/N) · Re(X[m])
      A · cos(ψ) =  (2/N) · Im(X[m])

    Solving:

      A = (2/N) · |X[m]|
      ψ = atan2( -Re(X[m]),  Im(X[m]) )  =  arg(X[m]) - π/2  (mod 2π)
      φ = ψ + 2π · half_span_days / period_days              (mod 2π)

    The earlier author-pass had `φ = 3π/2 - arg`, which is OFF: it
    flips the sign of `arg` (atan2(b,a) vs atan2(-a,b)) and misses
    the `+2π·half_span/period` time-origin offset entirely. With those
    bugs the catalog patches actively REINFORCED the residual on
    Mercury (-99.2% shrinkage) and barely scratched Mars / Saturn.
    """
    k = _bin_at_period(periods_yr, target_yr)
    bin_value = spectrum[k]
    amp_rad = (2.0 / n_samples) * abs(bin_value)
    amp_deg = math.degrees(amp_rad)
    arg_rad = math.atan2(bin_value.imag, bin_value.real)

    period_days = periods_yr[k] * 365.25
    half_span_days = (n_samples * cadence_days) / 2.0

    psi = (arg_rad - math.pi / 2.0) % (2.0 * math.pi)
    phi_cancel = (psi + 2.0 * math.pi * half_span_days / period_days) % (2.0 * math.pi)

    return {
        "bin_k": int(k),
        "bin_period_yr": float(periods_yr[k]),
        "fft_amplitude_deg": float(amp_deg),
        "fft_phase_rad": float(arg_rad),
        "psi_at_sample_zero_rad": float(psi),
        "half_span_days": float(half_span_days),
        "cancellation_phase_rad": float(phi_cancel),
    }


def _recover_coupled_patch(
    spec_a: np.ndarray, spec_b: np.ndarray,
    periods_yr: np.ndarray, target_yr: float, n_samples: int,
    cadence_days: float,
) -> Dict:
    """Recover params for a coupled-sinusoid patch tying body_a and
    body_b at the target period.

    For each body, recover (A_a, phi_a) and (A_b, phi_b). The coupled
    overlay applies the SAME sinusoid `A * sin(2π t / period + phi)`
    to body_a and `correlation * A * sin(...)` to body_b. To cancel
    BOTH residuals simultaneously we'd need:

        A_a == |A_b|    (matching magnitudes)
        phi_a == phi_b  (correlation = +1)
        OR
        phi_a == phi_b + π    (correlation = -1)

    In practice the magnitudes don't match exactly and the phases are
    rarely a clean π flip. We pick the "best fit" coupled patch by:

      * amplitude = mean(A_a, A_b)
      * correlation = sign(cos(phi_a - phi_b)) — closer to +1 if same-
        phase, -1 if anti-phase
      * phi = phi_a (anchored to body_a; body_b's residual will be
        partially cancelled depending on how close phi_a - phi_b is to
        0 or π)
    """
    rec_a = _recover_patch(spec_a, periods_yr, target_yr, n_samples, cadence_days)
    rec_b = _recover_patch(spec_b, periods_yr, target_yr, n_samples, cadence_days)
    amp_mean = 0.5 * (rec_a["fft_amplitude_deg"] + rec_b["fft_amplitude_deg"])
    delta_phi = (rec_a["fft_phase_rad"] - rec_b["fft_phase_rad"]) % (2.0 * math.pi)
    # Wrap delta_phi into [-π, π]
    if delta_phi > math.pi:
        delta_phi -= 2.0 * math.pi
    correlation = 1 if abs(delta_phi) < math.pi / 2.0 else -1
    return {
        "body_a": rec_a,
        "body_b": rec_b,
        "amp_mean_deg": float(amp_mean),
        "delta_phi_rad": float(delta_phi),
        "correlation": int(correlation),
        "anchor_cancellation_phase_rad": float(rec_a["cancellation_phase_rad"]),
    }


def author_patches(
    n_samples: int = N_SAMPLES_DEFAULT,
    cadence_days: float = CADENCE_DAYS_DEFAULT,
) -> Dict:
    """Run the encoder, recover phases, and emit the phase-recovered
    catalog.
    """
    print("\n=== Phase-recovered catalog authoring ===\n", flush=True)
    errors, _, inst = _gather_residuals(n_samples, cadence_days)
    cadence_yr = cadence_days / 365.25

    # Per-body complex FFT cache.
    fft_cache: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
    for body, arr in errors.items():
        if np.all(np.isnan(arr)):
            continue
        fft_cache[body] = _detrend_and_fft(arr, n_samples, cadence_yr)

    out: Dict = {
        "n_samples": n_samples,
        "cadence_days": cadence_days,
        "patches": {},
    }
    for patch_name, target in PATCH_TARGETS.items():
        if target["kind"] == "sinusoid":
            body = target["body"]
            if body not in fft_cache:
                out["patches"][patch_name] = {"error": f"no FFT for {body}"}
                continue
            spec, periods = fft_cache[body]
            rec = _recover_patch(spec, periods, target["expected_period_yr"], n_samples, cadence_days)
            out["patches"][patch_name] = {
                "kind": "sinusoid",
                "body": body,
                "amplitude_deg": rec["fft_amplitude_deg"],
                "period_days": rec["bin_period_yr"] * 365.25,
                "phase_rad": rec["cancellation_phase_rad"],
                "_diagnostic": rec,
            }
        elif target["kind"] == "coupled-sinusoid":
            body_a, body_b = target["body_a"], target["body_b"]
            if body_a not in fft_cache or body_b not in fft_cache:
                out["patches"][patch_name] = {"error": "missing FFT"}
                continue
            spec_a, periods = fft_cache[body_a]
            spec_b, _ = fft_cache[body_b]
            rec = _recover_coupled_patch(
                spec_a, spec_b, periods,
                target["expected_period_yr"], n_samples, cadence_days,
            )
            out["patches"][patch_name] = {
                "kind": "coupled-sinusoid",
                "body_a": body_a, "body_b": body_b,
                "amplitude_deg": rec["amp_mean_deg"],
                # Use body_a's bin period for the catalog entry (both
                # bodies share the same FFT grid).
                "period_days": fft_cache[body_a][1][rec["body_a"]["bin_k"]] * 365.25,
                "phase_rad": rec["anchor_cancellation_phase_rad"],
                "correlation": rec["correlation"],
                "_diagnostic": rec,
            }
    return out


def main() -> int:
    out = author_patches()
    repo_root = _HERE.parents[1].parent
    output_path = repo_root / "docs" / "antikythera-maths" / "results" / "phase_recovered_catalog.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2, sort_keys=True),
                           encoding="utf-8")
    print(f"\nWrote {output_path}")
    print("\nRecovered catalog:")
    for name, entry in out["patches"].items():
        if "error" in entry:
            print(f"  {name}: ERROR — {entry['error']}")
            continue
        if entry["kind"] == "sinusoid":
            print(f"  {name}:")
            print(f"    body={entry['body']}, amp={entry['amplitude_deg']:.4f}°, "
                  f"period={entry['period_days']:.2f}d, "
                  f"phase={entry['phase_rad']:.4f} rad ({math.degrees(entry['phase_rad']):.1f}°)")
        else:
            print(f"  {name}:")
            print(f"    {entry['body_a']}+{entry['body_b']}, "
                  f"amp={entry['amplitude_deg']:.4f}°, "
                  f"period={entry['period_days']:.2f}d, "
                  f"phase={entry['phase_rad']:.4f} rad, "
                  f"correlation={entry['correlation']:+d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
