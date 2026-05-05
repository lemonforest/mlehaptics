"""DE441 + auxiliary moon-kernel error spectrum.

The standard ``de441_error_spectrum`` sweeps J2000 ± 1262 yr at 900-d
cadence — fine for planets (DE441 covers -13201 BCE to +17191 CE), but
the supplementary moon kernels have much shorter coverage windows:

    jup365     1600-01-10 to 2200-01-10  (~600 yr)
    sat441     1749-12-30 to 2250-01-06  (~500 yr)
    mar099s    1995-01-01 to 2050-01-01  (~55 yr)

Most of the standard sweep falls OUTSIDE these kernels' coverage, so
the 90%-valid-samples filter drops every moon body from the report.

This module runs a moon-friendly sweep:

    Window: J2000 ± 200 yr  (fits inside jup365 + sat441)
    Cadence: 30 days (~12 samples per yr → resolves ~30 d periods)
    n_samples: 4866  (call it 4096 → 100.5 yr each side; use 5000 for safety)

…then FFTs each body's residual against ephemeris truth via
``bundle.lookup`` (which transparently searches the main DE441 kernel
plus the loaded auxiliaries). Mars's moons stay out of scope here —
mar099s's 55-yr window is too short for the FFT cadence we want.

Output:

    results/de441_moon_spectrum.json    machine-readable peaks
    results/de441_moon_spectrum.md      markdown summary

Run with auxiliary kernels staged at ./skyfield_data/:

    cd docs/antikythera-maths
    python -m research.de441_moon_spectrum
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.de441_error_spectrum import (
    _angular_diff, _truth_longitude, write_outputs,
)
from research.bip_instrument import EphemerisBIPInstrument, MODULO, REFERENCE_JD
from research.bodies import BODIES

__all__ = [
    "N_SAMPLES_MOONS",
    "CADENCE_DAYS_MOONS",
    "gather_moon_residuals",
    "run_moon_spectrum",
    "main",
]

try:
    from ephemerides_spectral import _native_bip
except ImportError:
    _native_bip = None  # type: ignore[assignment]


# ±200 yr around J2000 fits jup365 + sat441. Drop Phobos / Deimos —
# mar099s only covers ±25 yr, too short for these FFT params.
N_SAMPLES_MOONS: int = 4096
CADENCE_DAYS_MOONS: float = 30.0


def gather_moon_residuals(
    n_samples: int = N_SAMPLES_MOONS,
    cadence_days: float = CADENCE_DAYS_MOONS,
) -> Tuple[Dict[str, np.ndarray], np.ndarray, EphemerisBIPInstrument, float, bool]:
    """Encode the system over the moon-friendly window and return raw
    per-body angular-residual arrays.

    Used by `run_moon_spectrum` for the FFT pipeline AND by
    `author_moon_patches` / `verify_moon_patches` for time-domain
    LS-fitting at targeted moon residual peaks.

    Returns
    -------
    errors : Dict[str, np.ndarray]
        Per-body signed angular residual (rad). NaN where the body
        is out of the auxiliary kernel's coverage window at that JD.
    jd_grid : np.ndarray
        The JD sample grid (length n_samples).
    inst : EphemerisBIPInstrument
        The configured instrument (carries body_to_idx + bundle).
    elapsed : float
        Encode + truth-lookup wall-clock seconds.
    use_native : bool
        Whether the C native encoder was available.
    """
    inst = EphemerisBIPInstrument(
        D=2**12, kernel="de441", force_high_res=True,
    )
    bundle = inst.bundle
    print(f"  ready: {len(inst.body_names)} bodies, kernel = {bundle.kernel_name}",
          flush=True)
    print(f"  auxiliary kernels: {bundle.extra_kernel_names}", flush=True)

    use_native = _native_bip is not None and _native_bip.HAS_NATIVE
    if use_native:
        print(f"  using native encoder v{_native_bip.native_version()}",
              flush=True)
    bodies = [b for b in inst.body_names if b != "sun"]

    half_span_days = (n_samples * cadence_days) / 2.0
    span_yr = half_span_days / 365.25
    print(f"  sweep: {n_samples} samples @ {cadence_days:.1f} d cadence "
          f"=> J2000 ± {span_yr:.1f} yr, total span "
          f"{n_samples * cadence_days / 365.25:.1f} yr", flush=True)

    jd_grid = REFERENCE_JD + np.arange(n_samples) * cadence_days - half_span_days
    errors: Dict[str, np.ndarray] = {b: np.full(n_samples, np.nan) for b in bodies}

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
                # Out-of-coverage moon at this JD — leave as NaN.
                continue
            errors[name][k] = _angular_diff(bip_rad, truth_rad)
        if k % 256 == 0:
            print(f"    sample {k+1}/{n_samples}  "
                  f"elapsed={time.perf_counter()-t0:.1f}s", flush=True)
    elapsed = time.perf_counter() - t0
    print(f"  encode + truth lookup: {elapsed:.1f}s "
          f"({elapsed*1000/n_samples:.1f} ms/sample)", flush=True)

    return errors, jd_grid, inst, elapsed, use_native


def run_moon_spectrum(
    n_samples: int = N_SAMPLES_MOONS,
    cadence_days: float = CADENCE_DAYS_MOONS,
) -> Dict:
    """Run the FFT sweep with the moon-friendly window.

    Same FFT pipeline as `de441_error_spectrum.run_spectrum`, but
    without the 90% coverage filter — bodies with ANY valid samples
    are FFT'd over the valid subset (NaN-filled samples are ignored
    via detrending + zero-fill).
    """
    errors, _jd_grid, inst, elapsed, use_native = gather_moon_residuals(
        n_samples=n_samples, cadence_days=cadence_days,
    )
    bundle = inst.bundle

    # FFT per body. Lower the coverage threshold from 90% to 50% so
    # bodies with shorter aux-kernel windows still show up — but mark
    # them with their actual coverage so the report is honest.
    summary: Dict[str, Dict] = {}
    cadence_yr = cadence_days / 365.25
    for name, arr in errors.items():
        valid_mask = ~np.isnan(arr)
        n_valid = int(valid_mask.sum())
        coverage_pct = 100.0 * n_valid / n_samples
        if n_valid < n_samples * 0.5:
            # Too thin even for moon-friendly threshold — skip.
            continue
        # Detrend (using only valid samples) then FFT the zero-filled array.
        x = np.arange(n_samples)
        if n_valid >= 4:
            slope, intercept = np.polyfit(x[valid_mask], arr[valid_mask], 1)
        else:
            slope, intercept = 0.0, 0.0
        detrended = np.where(valid_mask, arr - (slope * x + intercept), 0.0)
        spectrum = np.fft.rfft(detrended)
        amps = np.abs(spectrum) / n_valid  # normalise by valid count
        freqs_per_yr = np.fft.rfftfreq(n_samples, d=cadence_yr)
        with np.errstate(divide="ignore"):
            periods_yr = np.where(freqs_per_yr > 0,
                                  1.0 / freqs_per_yr, np.inf)
        K = 20
        peak_idx = np.argsort(amps[1:])[-K:][::-1] + 1
        peaks = [
            {
                "rank": rank + 1,
                "freq_per_yr": float(freqs_per_yr[i]),
                "period_yr": float(periods_yr[i]),
                "period_days": float(periods_yr[i] * 365.25),
                "amp_rad": float(amps[i]),
                "amp_deg": float(np.degrees(amps[i])),
            }
            for rank, i in enumerate(peak_idx)
        ]
        summary[name] = {
            "coverage_pct": coverage_pct,
            "n_valid_samples": n_valid,
            "linear_slope_deg_per_yr": float(np.degrees(slope) / cadence_yr),
            "rms_residual_deg": float(np.degrees(
                np.sqrt(np.mean(detrended[valid_mask] ** 2))
            )) if n_valid > 0 else 0.0,
            "top_peaks": peaks,
        }

    return {
        "kernel_requested": "de441",
        "kernel_actual": bundle.kernel_name,
        "auxiliary_kernels": bundle.extra_kernel_names,
        "n_bodies": len(errors),
        "n_samples": n_samples,
        "cadence_days": cadence_days,
        "span_years": float(n_samples * cadence_days / 365.25),
        "native_available": use_native,
        "encode_seconds": float(elapsed),
        "per_body": summary,
    }


def main() -> int:
    summary = run_moon_spectrum()
    repo_root = _HERE.parents[1].parent
    output_dir = repo_root / "docs" / "antikythera-maths" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "de441_moon_spectrum.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True),
                         encoding="utf-8")

    md_lines = [
        "# DE441 + moon-kernel error spectrum",
        "",
        "Moon-friendly sweep window (±200 yr around J2000) so the "
        "supplementary moon kernels (jup365, sat441) cover the entire "
        "FFT span. Mars's moons (mar099s, ±25 yr) are out of scope at "
        "this cadence.",
        "",
        f"- Main kernel: **{summary['kernel_requested']}** "
        f"(loaded as `{summary['kernel_actual']}`)",
        f"- Auxiliary kernels: **{summary['auxiliary_kernels']}**",
        f"- Sample grid: **{summary['n_samples']}** samples @ "
        f"**{summary['cadence_days']:.1f} d** cadence "
        f"(span = **{summary['span_years']:.1f} yr** centered on J2000)",
        f"- Native encoder used: **{summary['native_available']}**",
        f"- Total encode + truth-lookup time: **{summary['encode_seconds']:.1f} s** "
        f"({summary['encode_seconds']*1000/summary['n_samples']:.1f} ms/sample)",
        "",
        "Per-body spectrum: linear slope detrended; FFT'd; top 20 peaks "
        "(excluding DC) reported.",
        "",
    ]
    for name, body in summary["per_body"].items():
        md_lines.append(f"## {name}")
        md_lines.append("")
        md_lines.append(f"- Coverage: **{body['coverage_pct']:.1f}%** "
                        f"({body['n_valid_samples']} valid samples)")
        md_lines.append(f"- Linear slope: **{body['linear_slope_deg_per_yr']:.4f} °/yr**")
        md_lines.append(f"- RMS modulation (detrended): **{body['rms_residual_deg']:.4f}°**")
        md_lines.append("")
        md_lines.append("| rank | period (yr) | period (days) | amp (deg) |")
        md_lines.append("| ---: | ---: | ---: | ---: |")
        for peak in body["top_peaks"][:10]:
            md_lines.append(f"| {peak['rank']} | {peak['period_yr']:.3f} | "
                            f"{peak['period_days']:.1f} | {peak['amp_deg']:.4f} |")
        md_lines.append("")

    md_path = output_dir / "de441_moon_spectrum.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nWrote:\n  {json_path}\n  {md_path}")
    print(f"\nBodies analysed: {len(summary['per_body'])}")
    print(f"  {sorted(summary['per_body'].keys())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
