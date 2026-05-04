"""DE441 full-epoch sweep for the BIP integer-ALU encoder.

Encodes the Sol Star System with the v0.3.0 BIP encoder at sample
points across the JPL DE441 epoch (~13,200 BCE to ~17,191 CE) and
reports per-body ecliptic-longitude error against the DE441 ground
truth, plus encode-state wall time per sample.

Run from a checkout where ``skyfield_data/de441.bsp`` is staged
(JPL's DE441 kernel, ~3.1 GB):

    cd docs/antikythera-maths
    python -m research.de441_sweep

Emits:
  - results/de441_sweep_summary.json  (per-body p50/p95/max error)
  - results/de441_sweep_table.md      (markdown table for inclusion
                                       in figures/de441_full_sweep.md)

The sweep avoids the expensive part of DE441 (loading the full
3.1 GB kernel) by reusing a single instrument across all samples,
so the kernel load cost is paid once.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Make the research package importable when run directly.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.bip_instrument import (                # noqa: E402
    EphemerisBIPInstrument,
    MODULO,
    REFERENCE_JD,
)


# Sample points: J2000 ± a geometric ladder out to ±15,000 yr.
# DE441 covers roughly J2000 ± 15,200 yr, so we stay just inside.
# Negative => past, positive => future.
_SWEEP_DELTAS_YEARS: List[float] = [
    0.0,
    1.0, -1.0,
    10.0, -10.0,
    100.0, -100.0,
    1000.0, -1000.0,
    5000.0, -5000.0,
    10000.0, -10000.0,
    14000.0, -14000.0,
]


def _angular_diff(a_rad: float, b_rad: float) -> float:
    """Smallest unsigned angular difference, [0, π]."""
    d = (a_rad - b_rad + np.pi) % (2.0 * np.pi) - np.pi
    return float(abs(d))


def _truth_longitude(bundle, jd_tt: float, body_name: str) -> float:
    """JPL DE441 truth ecliptic longitude (rad) for a given body.

    Mirrors the calibration logic in ``bip_instrument._calibrate_initial_phases``
    so the sweep compares like-against-like.
    """
    ts = bundle.ts
    t = ts.tt_jd(jd_tt)
    eph = bundle.eph

    moon_parent_map = {
        "moon": "earth", "phobos": "mars", "deimos": "mars",
        "io": "jupiter", "europa": "jupiter", "ganymede": "jupiter",
        "callisto": "jupiter", "titan": "saturn", "enceladus": "saturn",
        "rhea": "saturn", "titania": "uranus", "triton": "neptune",
    }

    target_key = body_name.upper()
    # Planets / asteroids use barycenters; sun is sun; moons use parent.
    from research.bodies import BODIES
    info = BODIES[body_name]

    if info.category == "planet":
        target_key += " BARYCENTER"
        center = eph["sun"]
    elif info.category == "moon":
        parent = moon_parent_map.get(body_name, "earth")
        parent_key = parent.upper()
        if parent in ("earth", "mars", "jupiter", "saturn", "uranus", "neptune"):
            parent_key += " BARYCENTER"
        center = eph[parent_key]
    else:
        center = eph["sun"]

    target = eph[target_key]
    astrometric = center.at(t).observe(target)
    _, lon, _ = astrometric.ecliptic_latlon()
    return float(lon.radians)


def run_sweep(kernel: str = "de441") -> Dict:
    """Run the full sweep. Returns the summary dict."""
    print(f"Initialising BIP instrument with kernel={kernel} (DE441 load is one-time)...",
          flush=True)
    inst = EphemerisBIPInstrument(D=2**16, kernel=kernel,
                                  force_high_res=(kernel == "de441"))
    bundle = inst.bundle
    print(f"  ready: {len(inst.body_names)} bodies, "
          f"actual kernel = {bundle.kernel_name}", flush=True)

    # Skip Sun (period_days = 0; phase residue is 0 by construction).
    bodies = [b for b in inst.body_names if b != "sun"]

    # Per-body error samples.
    errors: Dict[str, List[float]] = {b: [] for b in bodies}
    encode_times_ms: List[float] = []

    for delta_yr in _SWEEP_DELTAS_YEARS:
        jd = REFERENCE_JD + delta_yr * 365.25
        t0 = time.perf_counter()
        phases = inst.encode_state(jd)
        encode_times_ms.append((time.perf_counter() - t0) * 1000.0)

        # Ground truth at this JD via skyfield.
        for name in bodies:
            idx = inst.body_to_idx[name]
            bip_rad = (phases[idx] / MODULO) * 2.0 * np.pi
            try:
                truth_rad = _truth_longitude(bundle, jd, name)
            except (KeyError, ValueError):
                # Body might not be in the kernel (some moons / asteroids
                # only ship in supplementary kernels).
                continue
            errors[name].append(_angular_diff(bip_rad, truth_rad))

        print(f"  delta={delta_yr:>+8.0f} yr  encode={encode_times_ms[-1]:6.1f} ms  "
              f"earth_err={np.degrees(errors['earth'][-1]):.3f} deg",
              flush=True)

    # Per-body p50 / p95 / max.
    summary: Dict[str, Dict[str, float]] = {}
    for name, errs in errors.items():
        if not errs:
            continue
        arr = np.array(errs)
        summary[name] = {
            "samples": len(errs),
            "median_rad": float(np.median(arr)),
            "p95_rad": float(np.percentile(arr, 95)),
            "max_rad": float(np.max(arr)),
            "median_deg": float(np.degrees(np.median(arr))),
            "p95_deg": float(np.degrees(np.percentile(arr, 95))),
            "max_deg": float(np.degrees(np.max(arr))),
        }

    return {
        "kernel_requested": kernel,
        "kernel_actual": bundle.kernel_name,
        "n_bodies": len(bodies),
        "n_samples_per_body": len(_SWEEP_DELTAS_YEARS),
        "delta_years_min": float(min(_SWEEP_DELTAS_YEARS)),
        "delta_years_max": float(max(_SWEEP_DELTAS_YEARS)),
        "encode_ms_median": float(np.median(encode_times_ms)),
        "encode_ms_max": float(np.max(encode_times_ms)),
        "per_body": summary,
    }


def write_outputs(summary: Dict, output_dir: Path) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "de441_sweep_summary.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    md_path = output_dir / "de441_sweep_table.md"
    lines = [
        "# DE441 full-epoch sweep — per-body BIP error",
        "",
        f"- Kernel: **{summary['kernel_requested']}** (loaded as `{summary['kernel_actual']}`)",
        f"- Sample points: **{summary['n_samples_per_body']}** spaced "
        f"`J2000 + [{summary['delta_years_min']:+.0f}..{summary['delta_years_max']:+.0f}]` yr",
        f"- Encode wall time (ms): median **{summary['encode_ms_median']:.1f}**, "
        f"max **{summary['encode_ms_max']:.1f}**",
        "",
        "| Body | n | median (rad) | p95 (rad) | max (rad) | max (deg) |",
        "| :--- | --: | --: | --: | --: | --: |",
    ]
    # Sort bodies by max error descending (worst first).
    items = sorted(summary["per_body"].items(),
                   key=lambda kv: -kv[1]["max_rad"])
    for name, s in items:
        lines.append(
            f"| {name} | {s['samples']} | {s['median_rad']:.6f} | "
            f"{s['p95_rad']:.6f} | {s['max_rad']:.6f} | {s['max_deg']:.4f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    summary = run_sweep(kernel="de441")
    repo_root = _HERE.parents[1].parent
    output_dir = repo_root / "docs" / "antikythera-maths" / "results"
    json_path, md_path = write_outputs(summary, output_dir)
    print(f"\nWrote:\n  {json_path}\n  {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
