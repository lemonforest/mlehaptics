"""DE441 error-spectrum analysis: FFT the per-body residual to find missing couplings.

The v0.3.0 ``de441_sweep.py`` reported nearly-linear per-body error
against DE441 truth across a J2000 ± 14,000 yr horizon (Earth grows
~0.0006°/yr, Mars ~0.001°/yr, Mercury / gas-giants much faster). The
linearity is the Phase-9 model's *systematic* drift; the *modulation*
on top of it is the signal of dynamics we haven't modelled yet.

This module FFTs the per-body residual error and reports the
dominant peaks. Each peak's frequency corresponds to a known orbital
period; mapping peaks to periods identifies which couplings — the
ones we're missing — drive the residual at multi-millennium horizons.

If a peak's amplitude exceeds the linear-trend amplitude, that
coupling is *more* important than the static-Laplacian background.
The relative amplitude across bodies tells us how to weight a
per-resonance ``alpha`` in Phase 9 — the empirical bridge to v0.4+'s
first-principles Hamilton/Delaunay derivation.

Sweep design
------------

Uniform spacing is essential for FFT. Default: 1024 samples at
δt = 30 d × 30 = 900 d intervals = ~2.5-yr cadence over the span
``J2000 ± (1024 × 900 / 2 / 365.25) ≈ ± 1262 yr``. Adjustable via
the CLI args.

Native C backend is used by default (1040× speedup vs Python BIP
on the +20 yr horizon makes this analysis cheap; 1024 samples × ~6 ms
= ~6 s total, plus the one-time DE441 kernel load).

Run from a checkout where ``skyfield_data/de441.bsp`` is staged:

    cd docs/antikythera-maths
    python -m research.de441_error_spectrum

Outputs:

    results/de441_error_spectrum.json    machine-readable peaks
    results/de441_error_spectrum.md      markdown summary
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.bip_instrument import (              # noqa: E402
    EphemerisBIPInstrument,
    MODULO,
    REFERENCE_JD,
)
from research.bodies import BODIES                 # noqa: E402


# Sample-grid defaults — 1024 samples at 900-day cadence give
# Nyquist period = 1800 d ≈ 4.93 yr. Resolves Earth-Moon synodic
# (29.5 d, aliases — too short to resolve at this cadence; expected),
# Mars synodic (~780 d, just below Nyquist), Saros (6585 d, ~3.6
# samples/cycle resolved). For higher-resolution analysis of
# specific bodies, drop CADENCE_DAYS and bump N_SAMPLES.
N_SAMPLES_DEFAULT: int = 1024
CADENCE_DAYS_DEFAULT: float = 900.0


def _angular_diff(a_rad: float, b_rad: float) -> float:
    d = (a_rad - b_rad + np.pi) % (2.0 * np.pi) - np.pi
    return float(d)  # signed; FFT wants signed residuals


def _truth_longitude(bundle, jd_tt: float, body_name: str) -> float:
    ts = bundle.ts
    t = ts.tt_jd(jd_tt)
    # v0.5.2: bundle.lookup searches the main DE441 + the aux moon
    # kernels (mar099s for Phobos / Deimos, jup365 for the Galileans
    # + Jovian inner regulars, sat441 for the classical Saturnians +
    # co-orbitals). Falls back to KeyError if nothing has the target
    # key — caller handles by setting NaN in the residual array.
    lookup = bundle.lookup if hasattr(bundle, "lookup") else (lambda k: bundle.eph[k])

    # v0.5.2: extended to cover the new moons added in v0.5.0.
    moon_parent_map = {
        "luna": "terra",
        "phobos": "mars", "deimos": "mars",
        # Jovian (Galileans + inner regulars from v0.5.0)
        "io": "jupiter", "europa": "jupiter", "ganymede": "jupiter",
        "callisto": "jupiter",
        "metis": "jupiter", "adrastea": "jupiter",
        "amalthea": "jupiter", "thebe": "jupiter",
        # Saturnian (classical 9 + co-orbitals from v0.5.0)
        "mimas": "saturn", "enceladus": "saturn", "tethys": "saturn",
        "dione": "saturn", "rhea": "saturn", "titan": "saturn",
        "hyperion": "saturn", "iapetus": "saturn", "phoebe": "saturn",
        "janus": "saturn", "epimetheus": "saturn",
        "titania": "uranus", "triton": "neptune",
    }

    info = BODIES[body_name]
    target_key = body_name.upper()

    if info.category == "planet":
        target_key += " BARYCENTER"
        center = lookup("sun")
    elif info.category == "moon":
        parent = moon_parent_map.get(body_name, "terra")
        parent_key = parent.upper()
        if parent in ("terra", "mars", "jupiter", "saturn", "uranus", "neptune"):
            parent_key += " BARYCENTER"
        center = lookup(parent_key)
    else:
        center = lookup("sun")

    target = lookup(target_key)
    astrometric = center.at(t).observe(target)
    _, lon, _ = astrometric.ecliptic_latlon()
    return float(lon.radians)


def _try_native_encode(jd: float, n_bodies: int) -> np.ndarray:
    """Use the bundled C library if available; fall back to Python."""
    try:
        from ephemerides_spectral import _native_bip
        if _native_bip.HAS_NATIVE:
            return _native_bip.encode_state(jd - REFERENCE_JD)
    except ImportError:
        pass
    # The caller will use the Python instrument's encode_state.
    return None  # type: ignore[return-value]


def run_spectrum(kernel: str = "de441",
                 n_samples: int = N_SAMPLES_DEFAULT,
                 cadence_days: float = CADENCE_DAYS_DEFAULT) -> Dict:
    """Run the FFT analysis. Returns the summary dict."""
    inst = EphemerisBIPInstrument(D=2**16, kernel=kernel,
                                  force_high_res=(kernel == "de441"))
    bundle = inst.bundle
    print(f"  ready: {len(inst.body_names)} bodies, "
          f"actual kernel = {bundle.kernel_name}", flush=True)

    # Try to use the native path for the encode loop.
    native_available = False
    try:
        from ephemerides_spectral import _native_bip
        if _native_bip.HAS_NATIVE:
            native_available = True
            print(f"  native encoder available (v{_native_bip.native_version()}); using it",
                  flush=True)
        else:
            print(f"  native encoder unavailable: {_native_bip.LOAD_ERROR}", flush=True)
    except ImportError:
        print("  ephemerides-spectral package not importable; using research-source Python encoder",
              flush=True)

    bodies = [b for b in inst.body_names if b != "sun"]

    # Uniform JD grid centered on J2000.
    half_span_days = (n_samples * cadence_days) / 2.0
    span_yr = half_span_days / 365.25
    print(f"  sweep: {n_samples} samples @ {cadence_days:.1f} d cadence "
          f"=> J2000 +/- {span_yr:.1f} yr, total span "
          f"{n_samples * cadence_days / 365.25:.1f} yr",
          flush=True)

    jd_grid = REFERENCE_JD + np.arange(n_samples) * cadence_days - half_span_days

    # Per-body signed error vs DE441 truth at every grid point.
    errors: Dict[str, np.ndarray] = {b: np.zeros(n_samples) for b in bodies}

    t0 = time.perf_counter()
    for k, jd in enumerate(jd_grid):
        if native_available:
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
            elapsed = time.perf_counter() - t0
            print(f"    sample {k+1}/{n_samples}  elapsed={elapsed:.1f}s", flush=True)
    elapsed = time.perf_counter() - t0
    print(f"  encode + truth lookup: {elapsed:.1f}s ({elapsed*1000/n_samples:.1f} ms/sample)",
          flush=True)

    # FFT each body's signed residual, identify peaks.
    summary: Dict[str, Dict] = {}
    cadence_yr = cadence_days / 365.25

    for name, arr in errors.items():
        valid = arr[~np.isnan(arr)]
        if len(valid) < n_samples * 0.9:
            # Body's coverage too thin — DE441 doesn't ship most moons.
            continue

        # Detrend (remove linear) so the FFT shows modulation, not the
        # systematic linear drift. Keep DC for completeness but don't
        # report it as a "peak".
        if np.any(np.isnan(arr)):
            arr = np.where(np.isnan(arr), 0.0, arr)
        x = np.arange(n_samples)
        slope, intercept = np.polyfit(x, arr, 1)
        detrended = arr - (slope * x + intercept)

        spectrum = np.fft.rfft(detrended)
        amps = np.abs(spectrum) / n_samples
        freqs_per_yr = np.fft.rfftfreq(n_samples, d=cadence_yr)
        # Convert to period in years; freq=0 is DC -> infinite period.
        with np.errstate(divide="ignore"):
            periods_yr = np.where(freqs_per_yr > 0,
                                   1.0 / freqs_per_yr, np.inf)

        # Top-K peaks excluding DC.
        # K bumped 5 -> 20 in v0.5.1 (so the patch-shrinks-residual
        # benchmark can still find the targeted peak after a successful
        # patch demotes it out of the original top-5), then 20 -> 100
        # in v0.5.2 (so the LS-fit catalog's near-100% shrinkage
        # doesn't push the peak below even the top-20 — Mars vindicated
        # at 99.2% but Mercury / J-S returned "no peak in tolerance"
        # under K=20 because the suppressed peaks fell out of the top
        # 20 entirely; under K=100 they're back).
        K = 100
        peak_idx = np.argsort(amps[1:])[-K:][::-1] + 1  # offset to skip DC
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
            "samples": n_samples,
            "linear_slope_rad_per_step": float(slope),
            "linear_slope_deg_per_yr": float(np.degrees(slope) / cadence_yr),
            "rms_residual_rad": float(np.sqrt(np.mean(detrended ** 2))),
            "rms_residual_deg": float(np.degrees(np.sqrt(np.mean(detrended ** 2)))),
            "top_peaks": peaks,
        }

    return {
        "kernel_requested": kernel,
        "kernel_actual": bundle.kernel_name,
        "n_bodies": len(bodies),
        "n_samples": n_samples,
        "cadence_days": cadence_days,
        "span_years": float(n_samples * cadence_days / 365.25),
        "native_available": native_available,
        "encode_seconds": float(elapsed),
        "per_body": summary,
    }


def write_outputs(summary: Dict, output_dir: Path) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "de441_error_spectrum.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True),
                         encoding="utf-8")

    md_path = output_dir / "de441_error_spectrum.md"
    lines = [
        "# DE441 error spectrum — FFT of per-body residual",
        "",
        f"- Kernel: **{summary['kernel_requested']}** (loaded as `{summary['kernel_actual']}`)",
        f"- Sample grid: **{summary['n_samples']}** samples @ "
        f"**{summary['cadence_days']:.1f} d** cadence "
        f"(span ≈ **{summary['span_years']:.1f} yr** centered on J2000)",
        f"- Native encoder used: **{summary['native_available']}**",
        f"- Total encode + truth-lookup time: **{summary['encode_seconds']:.1f} s** "
        f"({summary['encode_seconds']*1000/summary['n_samples']:.1f} ms/sample)",
        "",
        "Per-body spectrum: linear slope (the v0.3.0 sweep's "
        "headline drift) detrended; FFT'd; top 5 modulation peaks "
        "(excluding DC) reported.",
        "",
    ]

    for name, body_summary in summary["per_body"].items():
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- Linear slope: **{body_summary['linear_slope_deg_per_yr']:.4f}°/yr**")
        lines.append(f"- RMS modulation (detrended): **{body_summary['rms_residual_deg']:.4f}°**")
        lines.append("")
        lines.append("| rank | period (yr) | period (days) | amplitude (deg) |")
        lines.append("| ---: | ---: | ---: | ---: |")
        for peak in body_summary["top_peaks"]:
            lines.append(
                f"| {peak['rank']} | {peak['period_yr']:.3f} | "
                f"{peak['period_days']:.1f} | {peak['amp_deg']:.4f} |"
            )
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    summary = run_spectrum(kernel="de441")
    repo_root = _HERE.parents[1].parent
    output_dir = repo_root / "docs" / "antikythera-maths" / "results"
    json_path, md_path = write_outputs(summary, output_dir)
    print(f"\nWrote:\n  {json_path}\n  {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
