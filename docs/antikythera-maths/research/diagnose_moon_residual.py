"""Phase A diagnostic: confirm the moon-residual ecliptic-projection hypothesis.

The v0.5.2 moon FFT sweep (`research/de441_moon_spectrum.py`)
reported ~100° RMS residuals on 13 of 17 moons against the v0.5.0
encoder. The hypothesis (notebook §3 → moon residual root cause):

    The encoder advances each moon's phase at a uniform rate
    omega = 2π / P_sidereal, while skyfield's
    `astrometric.ecliptic_latlon()` returns the longitude in
    Earth's J2000 ecliptic plane. For moons whose orbital plane is
    inclined relative to the ecliptic (Galileans orbit Jupiter's
    equator, ~26° off ecliptic; Saturnians orbit Saturn's equator,
    similar), the ecliptic-projection longitude is a non-uniform
    function of orbital phase. The mismatch is what shows up as
    residual.

This module measures it directly. For each of:
    Callisto (clean ~0.6° RMS in v0.5.2 — control)
    Io (~106° RMS in v0.5.2 — broken)
    Mimas (~104° RMS — broken Saturnian)
    Titan (~3.4° RMS — clean Saturnian, control)

we encode at a fine cadence over ONE orbital period, look up truth
via ecliptic_latlon, and report:
  - encoder phase residue
  - skyfield's ecliptic longitude
  - residual = (encoder - truth) mod 2π, in degrees

If the diagnosis is right, the broken moons should show a residual
that's a deterministic function of orbital phase (bounded periodic
warp), while the clean moons show a residual that's tiny.

Output:
    results/moon_residual_diagnostic.json
    results/moon_residual_diagnostic.md
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.bip_instrument import EphemerisBIPInstrument, MODULO, REFERENCE_JD  # noqa: E402
from research.bodies import BODIES                                                # noqa: E402
from research.de441_error_spectrum import _truth_longitude                        # noqa: E402

try:
    from ephemerides_spectral import _native_bip
except ImportError:
    _native_bip = None  # type: ignore[assignment]


# Test bodies — two clean controls and three broken cases.
BODIES_TO_TEST: Dict[str, Dict] = {
    "callisto":  {"class": "control",  "v052_rms_deg":   0.60},
    "titan":     {"class": "control",  "v052_rms_deg":   3.39},
    "io":        {"class": "broken",   "v052_rms_deg": 106.33},
    "europa":    {"class": "broken",   "v052_rms_deg": 116.41},
    "mimas":     {"class": "broken",   "v052_rms_deg": 103.65},
    "metis":     {"class": "broken",   "v052_rms_deg": 103.97},
}


def _wrap_signed(rad: float) -> float:
    return ((rad + math.pi) % (2.0 * math.pi)) - math.pi


def diagnose(n_samples_per_period: int = 256) -> Dict:
    inst = EphemerisBIPInstrument(
        D=2**12, kernel="de441", force_high_res=True,
    )
    bundle = inst.bundle
    if bundle is None:
        raise RuntimeError("DE441 bundle didn't load")
    print(f"  ready: {len(inst.body_names)} bodies; aux kernels: "
          f"{bundle.extra_kernel_names}", flush=True)
    use_native = _native_bip is not None and _native_bip.HAS_NATIVE
    if use_native:
        print(f"  using native encoder v{_native_bip.native_version()}",
              flush=True)

    out: Dict = {
        "n_samples_per_period": n_samples_per_period,
        "use_native": use_native,
        "auxiliary_kernels": list(bundle.extra_kernel_names),
        "per_body": {},
    }

    for body_name, info in BODIES_TO_TEST.items():
        if body_name not in inst.body_to_idx:
            print(f"  skip {body_name}: not in roster")
            continue
        body = BODIES[body_name]
        period = body.period_days
        # Sample one full orbital period starting from REFERENCE_JD.
        jd_grid = REFERENCE_JD + np.linspace(0, period, n_samples_per_period,
                                              endpoint=False)
        phases_encoded: List[float] = []
        truths: List[float] = []
        residuals: List[float] = []

        t0 = time.perf_counter()
        for jd in jd_grid:
            if use_native:
                phases = _native_bip.encode_state(float(jd) - REFERENCE_JD)
            else:
                phases = inst.encode_state(float(jd))
            idx = inst.body_to_idx[body_name]
            enc_rad = (phases[idx] / MODULO) * 2.0 * math.pi
            try:
                truth_rad = _truth_longitude(bundle, float(jd), body_name)
            except (KeyError, ValueError) as exc:
                print(f"  {body_name}: truth lookup failed at JD={jd:.0f}: {exc}")
                continue
            phases_encoded.append(enc_rad)
            truths.append(truth_rad)
            residuals.append(_wrap_signed(enc_rad - truth_rad))
        elapsed = time.perf_counter() - t0

        residuals_arr = np.array(residuals)
        encoder_arr = np.array(phases_encoded)
        truth_arr = np.array(truths)

        rms_deg = math.degrees(math.sqrt(np.mean(residuals_arr ** 2)))
        peak_deg = math.degrees(np.max(np.abs(residuals_arr)))
        # If the residual is a deterministic-warp function of
        # orbital phase, sorting by encoder phase + plotting residual
        # gives a smooth curve. We approximate that smoothness by
        # taking the FFT and reporting top-3 harmonics.
        # First detrend (linear) so DC + slow drift don't dominate.
        x = np.arange(len(residuals_arr))
        slope, intercept = np.polyfit(x, residuals_arr, 1)
        detrended = residuals_arr - (slope * x + intercept)
        spectrum = np.abs(np.fft.rfft(detrended))
        # Top-3 modulation harmonics, normalised to amplitude in deg.
        amps_deg = (2.0 / len(detrended)) * spectrum
        amps_deg_dc_excluded = amps_deg.copy()
        amps_deg_dc_excluded[0] = 0
        top3_idx = np.argsort(amps_deg_dc_excluded)[-3:][::-1]
        top3 = []
        for idx in top3_idx:
            top3.append({
                "harmonic": int(idx),
                "amp_deg": float(math.degrees(amps_deg[idx])),
            })

        out["per_body"][body_name] = {
            "class": info["class"],
            "v052_rms_deg": info["v052_rms_deg"],
            "period_days": period,
            "n_samples": len(residuals_arr),
            "rms_residual_deg": rms_deg,
            "peak_residual_deg": peak_deg,
            "linear_drift_per_sample_deg": float(math.degrees(slope)),
            "top3_modulation_harmonics_deg": top3,
            "elapsed_s": elapsed,
        }
        print(f"  {body_name:10s} ({info['class']:7s}): "
              f"period={period:7.2f} d  RMS={rms_deg:7.3f}°  "
              f"peak={peak_deg:7.3f}°  "
              f"top1 harmonic amp={top3[0]['amp_deg']:.4f}° "
              f"({elapsed:.2f}s)", flush=True)

    return out


def main() -> int:
    print("\n=== Moon residual diagnostic — Phase A ===\n", flush=True)
    out = diagnose()
    repo_root = _HERE.parents[1].parent
    output_dir = repo_root / "docs" / "antikythera-maths" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "moon_residual_diagnostic.json"
    json_path.write_text(json.dumps(out, indent=2, sort_keys=True),
                         encoding="utf-8")

    md_lines = [
        "# Moon residual diagnostic — Phase A",
        "",
        "**Hypothesis**: 13 of 17 moons show ~100° RMS residuals against "
        "ephemeris truth because the encoder advances at a uniform rate "
        "`omega = 2π / P_sidereal` while skyfield's `ecliptic_latlon()` "
        "measures longitude in Earth's J2000 ecliptic plane — for moons "
        "in inclined orbits the ecliptic projection is non-uniform in "
        "orbital phase.",
        "",
        f"- Native encoder used: **{out['use_native']}**",
        f"- Auxiliary kernels: **{out['auxiliary_kernels']}**",
        f"- Samples per orbital period: **{out['n_samples_per_period']}**",
        "",
        "Each body sampled at uniform JD over ONE full sidereal period "
        "starting from REFERENCE_JD = J2000.0. Residual = (encoded longitude − "
        "truth ecliptic longitude) mod 2π, signed.",
        "",
        "| body | class | period (d) | RMS (°) | peak (°) | top-1 harmonic amp (°) |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for name, body in out["per_body"].items():
        top1 = body["top3_modulation_harmonics_deg"][0]
        md_lines.append(
            f"| {name} | {body['class']} | {body['period_days']:.3f} | "
            f"{body['rms_residual_deg']:.3f} | "
            f"{body['peak_residual_deg']:.3f} | "
            f"{top1['amp_deg']:.4f} |"
        )
    md_lines.append("")
    md_lines.append("## Reading the table")
    md_lines.append("")
    md_lines.append(
        "If the diagnosis is right: **broken** rows have RMS within "
        "factor-of-3 of their v0.5.2 sweep RMS (so the broken signal IS "
        "the orbital-period warp, the v0.5.2 FFT was just aliasing it to "
        "near-DC content), AND the top-1 modulation harmonic should be "
        "comparable in amplitude to the v0.5.2 RMS (the warp is "
        "concentrated in 1-2 harmonics of the orbital period). **Control** "
        "rows should have RMS << 1°."
    )
    md_lines.append("")
    md_path = output_dir / "moon_residual_diagnostic.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nWrote:\n  {json_path}\n  {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
