"""Author moon catalog patches via LS-fit on the v0.5.3 corrected
residuals (Phase C of the v0.5.x moon-residual programme).

Context
=======

v0.5.3 fixed 13 of 17 moons via high-precision sidereal periods —
RMS dropped from ~100° to single-digit degrees. The remaining
residuals are now Fourier-decomposable into clean dominant peaks
(see `results/de441_moon_spectrum.md`), which is the regime where
the v0.5.2 LS-fit catalog methodology earns its 96-99% shrinkage on
planets.

This script applies the same methodology to moons:

  1. Gather per-body residuals over the moon-friendly window
     (±200 yr, 30 d cadence — fits the jup365 + sat441 auxiliary
     kernels' coverage).
  2. For each MOON_PATCH_TARGETS entry, LS-fit a sinusoid at the
     targeted period directly to the residual time series. Stage 1
     is a closed-form least-squares (period fixed); stage 2 lets
     scipy refine the period within a small window.
  3. Emit a recovered patch per target with measured amplitude /
     period / cancellation phase. The cancellation phase is the
     fitted phase + π (the patch must oppose the residual).

The recovered catalog lands at
``results/moon_recovered_catalog.json``. ``verify_moon_patches.py``
is the partner script that re-runs the FFT sweep with each patch
active and reports the measured shrinkage on its target peak.

Patch targets (v0.5.5 phase C — Saturnian + Jovian moon residuals)
==================================================================

Diagonal patches authored from the v0.5.3 dominant peak per body:

  * ``dione-1.06yr-diagonal``      Dione's 387.6-d peak (1.17°)
  * ``tethys-0.38yr-diagonal``     Tethys's 138.2-d peak (1.75°)
  * ``enceladus-0.39yr-diagonal``  Enceladus's 141.9-d peak (1.52°)
  * ``titan-0.69yr-diagonal``      Titan's 252.8-d peak (1.56°)
  * ``iapetus-0.22yr-diagonal``    Iapetus's 79.3-d peak (1.58°)
  * ``hyperion-0.20yr-diagonal``   Hyperion's 72.4-d peak (5.44°)

These six are the cleanest single-peak signals in the v0.5.3
spectrum. Mimas (30° RMS, broadband near-DC) is excluded — its
remaining residual is structural, not a single sinusoid. The
unfixed-by-v0.5.3 four (metis / thebe / rhea / phoebe) are
likewise excluded — period truncation is still in play and the
LS-fit methodology assumes the encoder's underlying mean motion is
correct.

Run from the repo root with the auxiliary kernels staged:

    cd docs/antikythera-maths
    python -m research.author_moon_patches
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.author_phase_recovered_patches import _lsq_fit_sinusoid  # noqa: E402
from research.de441_moon_spectrum import (                              # noqa: E402
    N_SAMPLES_MOONS, CADENCE_DAYS_MOONS, gather_moon_residuals,
)


# Patch targets — diagonal sinusoids at the dominant FFT peak per
# moon, taken from results/de441_moon_spectrum.md (the v0.5.3 sweep).
# `expected_period_days` is the FFT-bin period; `_lsq_fit_sinusoid`
# refines this within ±60 d.
MOON_PATCH_TARGETS: Dict[str, Dict] = {
    "dione-1.06yr-diagonal": {
        "body": "dione",
        "expected_period_days": 387.6,
        "fft_amplitude_deg": 1.1678,
        "kind": "sinusoid",
    },
    "tethys-0.38yr-diagonal": {
        "body": "tethys",
        "expected_period_days": 138.2,
        "fft_amplitude_deg": 1.7511,
        "kind": "sinusoid",
    },
    "enceladus-0.39yr-diagonal": {
        "body": "enceladus",
        "expected_period_days": 141.9,
        "fft_amplitude_deg": 1.5196,
        "kind": "sinusoid",
    },
    "titan-0.69yr-diagonal": {
        "body": "titan",
        "expected_period_days": 252.8,
        "fft_amplitude_deg": 1.5645,
        "kind": "sinusoid",
    },
    "iapetus-0.22yr-diagonal": {
        "body": "iapetus",
        "expected_period_days": 79.3,
        "fft_amplitude_deg": 1.5758,
        "kind": "sinusoid",
    },
    "hyperion-0.20yr-diagonal": {
        "body": "hyperion",
        "expected_period_days": 72.4,
        "fft_amplitude_deg": 5.4392,
        "kind": "sinusoid",
    },
}


def author_moon_patches(
    n_samples: int = N_SAMPLES_MOONS,
    cadence_days: float = CADENCE_DAYS_MOONS,
) -> Dict:
    """Run the moon-window encoder and recover one patch per target.

    Returns the recovered-catalog dict (same shape as
    `author_phase_recovered_patches.author_patches` for `method='lsq'`)
    serialisable to JSON.
    """
    print("\n=== Moon catalog authoring (LS-fit on v0.5.3 residuals) ===\n",
          flush=True)
    errors, jd_grid, _inst, _elapsed, _use_native = gather_moon_residuals(
        n_samples=n_samples, cadence_days=cadence_days,
    )

    out: Dict = {
        "n_samples": n_samples,
        "cadence_days": cadence_days,
        "method": "lsq",
        "window": "moon-friendly (±200 yr, 30 d cadence)",
        "patches": {},
    }

    for patch_name, target in MOON_PATCH_TARGETS.items():
        body = target["body"]
        if body not in errors:
            out["patches"][patch_name] = {"error": f"no residual for {body}"}
            continue
        arr = errors[body]
        if np.all(np.isnan(arr)):
            out["patches"][patch_name] = {"error": f"all-nan residual for {body}"}
            continue
        arr_clean = np.where(np.isnan(arr), 0.0, arr)
        rec = _lsq_fit_sinusoid(jd_grid, arr_clean, target["expected_period_days"])
        out["patches"][patch_name] = {
            "kind": "sinusoid",
            "body": body,
            "amplitude_deg": rec["amplitude_deg"],
            "period_days": rec["period_days"],
            "phase_rad": rec["cancellation_phase_rad"],
            "fft_baseline_amp_deg": target["fft_amplitude_deg"],
            "_diagnostic": rec,
        }
    return out


def main() -> int:
    out = author_moon_patches()
    repo_root = _HERE.parents[1].parent
    output_path = (repo_root / "docs" / "antikythera-maths" / "results"
                   / "moon_recovered_catalog.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2, sort_keys=True),
                           encoding="utf-8")
    print(f"\nWrote {output_path}")
    print("\nRecovered moon catalog:")
    for name, entry in out["patches"].items():
        if "error" in entry:
            print(f"  {name}: ERROR — {entry['error']}")
            continue
        print(f"  {name}:")
        print(f"    body={entry['body']}, "
              f"amp={entry['amplitude_deg']:.4f}° "
              f"(FFT-bin baseline {entry['fft_baseline_amp_deg']:.4f}°), "
              f"period={entry['period_days']:.2f}d, "
              f"phase={entry['phase_rad']:.4f} rad "
              f"({math.degrees(entry['phase_rad']):.1f}°)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
