"""Re-run the moon-friendly FFT sweep with each LS-fit recovered moon
patch active, measure shrinkage on its target peak.

Mirrors `verify_recovered_patches.py` (v0.5.2 planet vindication) but
uses the moon-friendly window from `de441_moon_spectrum`.

Each patch passes the v0.5.5 vindication threshold if it shrinks its
targeted FFT peak by ≥80%. The validated patches land in
`CATALOG_V2` (in `research/diagnosed_fibers.py` and the published
package's `_research/diagnosed_fibers.py`) with their measured
shrinkage% pinned in the `notes` field — same regression-test
discipline the planets carry.

Run from the repo root with the auxiliary kernels staged:

    cd docs/antikythera-maths
    python -m research.verify_moon_patches

Reads:
    results/moon_recovered_catalog.json     (from author_moon_patches.py)

Writes:
    results/verify_moon_patches.json
    results/verify_moon_patches.md
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

from research.author_moon_patches import MOON_PATCH_TARGETS                  # noqa: E402
from research.de441_moon_spectrum import (                                    # noqa: E402
    N_SAMPLES_MOONS, CADENCE_DAYS_MOONS, run_moon_spectrum,
)
from research.bodies import BODIES                                            # noqa: E402
from research import diagnosed_fibers as _patches                             # noqa: E402
from research.diagnosed_fibers import SinusoidPatch                           # noqa: E402

try:
    from ephemerides_spectral import _native_bip
except ImportError:
    _native_bip = None  # type: ignore[assignment]


def _body_index(name: str) -> int:
    return sorted(BODIES.keys()).index(name)


def _apply_recovered_patch(name: str, entry: Dict) -> SinusoidPatch:
    """Apply a recovered-catalog entry to BOTH the research-source
    Python registry and (if available) the C-side native registry.
    """
    if entry["kind"] != "sinusoid":
        raise ValueError(
            f"moon patch {name!r} is kind={entry['kind']!r}; "
            "only 'sinusoid' is currently supported in moon Phase C."
        )
    patch = SinusoidPatch(
        name=name,
        body=entry["body"],
        amplitude_deg=float(entry["amplitude_deg"]),
        period_days=float(entry["period_days"]),
        phase_rad=float(entry["phase_rad"]),
        notes="phase-recovered LS-fit on v0.5.3 moon residuals (Phase C)",
    )
    _patches.apply_patch(patch)
    if _native_bip is not None and _native_bip.HAS_NATIVE:
        rc = _native_bip.native_apply_sinusoid_patch(
            name=patch.name, body_idx=_body_index(patch.body),
            amplitude_deg=patch.amplitude_deg,
            period_days=patch.period_days,
            phase_rad=patch.phase_rad,
        )
        if rc != 0:
            raise RuntimeError(f"native apply returned {rc} for {name!r}")
    return patch


def _clear_all() -> None:
    _patches.clear_patches()
    if _native_bip is not None and _native_bip.HAS_NATIVE:
        _native_bip.native_clear_patches()


def _peak_at_period(body_summary: Dict, target_period_days: float,
                    tolerance_days: float = 30.0) -> Dict:
    """Find the strongest peak in a body's top-K spectrum within
    ``tolerance_days`` of ``target_period_days``. Returns ``None``
    if no peak in the band.
    """
    candidates = [
        p for p in body_summary["top_peaks"]
        if abs(p["period_days"] - target_period_days) <= tolerance_days
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p["amp_deg"])


def main() -> int:
    repo_root = _HERE.parents[1].parent
    recovered_path = (repo_root / "docs" / "antikythera-maths"
                      / "results" / "moon_recovered_catalog.json")
    if not recovered_path.exists():
        print(f"ERROR: {recovered_path} doesn't exist. Run "
              "author_moon_patches.py first.", flush=True)
        return 1
    recovered = json.loads(recovered_path.read_text(encoding="utf-8"))
    print(f"Loaded recovered moon catalog from {recovered_path}\n")

    _clear_all()
    print("Step 1: baseline moon FFT (no patches)...", flush=True)
    baseline_summary = run_moon_spectrum(
        n_samples=N_SAMPLES_MOONS, cadence_days=CADENCE_DAYS_MOONS,
    )

    per_patch_results: List[Dict] = []
    for patch_name, target in MOON_PATCH_TARGETS.items():
        if patch_name not in recovered["patches"]:
            print(f"\n  WARN: no recovered entry for {patch_name}; skipping.",
                  flush=True)
            continue
        entry = recovered["patches"][patch_name]
        if "error" in entry:
            print(f"\n  WARN: recovered entry has error: {entry['error']}; "
                  "skipping.", flush=True)
            continue

        _clear_all()
        _apply_recovered_patch(patch_name, entry)
        print(f"\n  >> running with phase-recovered '{patch_name}' active...",
              flush=True)
        t0 = time.perf_counter()
        patched_summary = run_moon_spectrum(
            n_samples=N_SAMPLES_MOONS, cadence_days=CADENCE_DAYS_MOONS,
        )
        t1 = time.perf_counter()
        _clear_all()
        print(f"  << finished in {t1 - t0:.1f}s", flush=True)

        body = target["body"]
        target_period = target["expected_period_days"]
        base_peak = _peak_at_period(
            baseline_summary["per_body"][body], target_period,
        )
        patch_peak = _peak_at_period(
            patched_summary["per_body"][body], target_period,
        )
        if base_peak is None:
            per_patch_results.append({
                "patch_name": patch_name,
                "verdict": "NO_BASELINE",
                "error": "no baseline peak within tolerance",
            })
            continue
        amp_b = base_peak["amp_deg"]
        if patch_peak is None:
            top_peaks = patched_summary["per_body"][body].get("top_peaks", [])
            smallest_topk = min(p["amp_deg"] for p in top_peaks) if top_peaks else 0.0
            amp_p = smallest_topk
            note = ("upper bound: target peak demoted below the K-th-strongest "
                    "patched peak; actual amplitude is <= this value")
        else:
            amp_p = patch_peak["amp_deg"]
            note = None
        delta = amp_b - amp_p
        shrink_pct = 100.0 * delta / amp_b if amp_b > 0 else 0.0
        verdict = (
            "VINDICATED" if shrink_pct >= 80.0
            else "PARTIAL" if shrink_pct >= 40.0
            else "REJECTED"
        )
        rms_baseline = baseline_summary["per_body"][body]["rms_residual_deg"]
        rms_patched = patched_summary["per_body"][body]["rms_residual_deg"]
        per_patch_results.append({
            "patch_name": patch_name,
            "body": body,
            "recovered_amplitude_deg": float(entry["amplitude_deg"]),
            "recovered_period_days": float(entry["period_days"]),
            "recovered_phase_rad": float(entry["phase_rad"]),
            "baseline_amp_deg": float(amp_b),
            "patched_amp_deg": float(amp_p),
            "delta_amp_deg": float(delta),
            "shrinkage_pct_of_baseline": float(shrink_pct),
            "rms_baseline_deg": float(rms_baseline),
            "rms_patched_deg": float(rms_patched),
            "rms_delta_deg": float(rms_baseline - rms_patched),
            "patched_amp_note": note,
            "verdict": verdict,
        })

    n_vindicated = sum(1 for r in per_patch_results if r.get("verdict") == "VINDICATED")
    n_partial = sum(1 for r in per_patch_results if r.get("verdict") == "PARTIAL")
    n_rejected = sum(1 for r in per_patch_results if r.get("verdict") == "REJECTED")
    overall = (
        "VINDICATED" if n_vindicated == len(per_patch_results) and n_vindicated > 0
        else "PARTIAL" if (n_vindicated + n_partial) > 0
        else "REJECTED"
    )

    summary = {
        "overall_verdict": overall,
        "n_vindicated": n_vindicated,
        "n_partial": n_partial,
        "n_rejected": n_rejected,
        "n_total": len(per_patch_results),
        "vindication_threshold_pct": 80.0,
        "window": "moon-friendly (±200 yr, 30 d cadence)",
        "per_patch": per_patch_results,
    }

    output_dir = repo_root / "docs" / "antikythera-maths" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_json = output_dir / "verify_moon_patches.json"
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True),
                        encoding="utf-8")

    lines = [
        "# Moon catalog patches — patch-shrinks-residual verification",
        "",
        "Re-run of the moon FFT sweep with each LS-fit recovered moon "
        "patch active. Each patch targets one dominant peak in the "
        "v0.5.3 spectrum.",
        "",
        f"- **Overall verdict:** **{overall}** "
        f"({n_vindicated} VINDICATED / {n_partial} PARTIAL / "
        f"{n_rejected} REJECTED out of {len(per_patch_results)})",
        "- Vindication threshold: ≥80% shrinkage of the targeted peak amplitude.",
        "- Window: ±200 yr around J2000 at 30-d cadence (4096 samples).",
        "",
        "| patch | verdict | base amp | patched | shrinkage | RMS Δ |",
        "| --- | :--- | ---: | ---: | ---: | ---: |",
    ]
    for r in per_patch_results:
        if r.get("verdict") in {"NO_BASELINE"}:
            lines.append(f"| `{r['patch_name']}` | {r['verdict']} | "
                         f"n/a | n/a | n/a | n/a |")
            continue
        lines.append(
            f"| `{r['patch_name']}` | **{r['verdict']}** | "
            f"{r['baseline_amp_deg']:.3f}° | "
            f"{r['patched_amp_deg']:.3f}° | "
            f"{r['shrinkage_pct_of_baseline']:.1f}% | "
            f"{r['rms_delta_deg']:+.3f}° |"
        )
    lines.append("")

    for r in per_patch_results:
        if r.get("verdict") in {"NO_BASELINE"}:
            continue
        lines.append(f"## `{r['patch_name']}` — verdict: **{r['verdict']}**")
        lines.append("")
        lines.append(f"- Body: **{r['body']}**")
        lines.append(f"- Recovered amplitude: **{r['recovered_amplitude_deg']:.4f}°**")
        lines.append(f"- Recovered period: **{r['recovered_period_days']:.2f} d**")
        lines.append(f"- Recovered phase: **{r['recovered_phase_rad']:.4f} rad** "
                     f"({math.degrees(r['recovered_phase_rad']):.2f}°)")
        lines.append(f"- Baseline peak amplitude: **{r['baseline_amp_deg']:.4f}°**")
        lines.append(f"- Patched peak amplitude: **{r['patched_amp_deg']:.4f}°**"
                     + (f" ({r['patched_amp_note']})" if r.get("patched_amp_note") else ""))
        lines.append(f"- Shrinkage: **{r['shrinkage_pct_of_baseline']:.1f}%**")
        lines.append(f"- RMS residual: **{r['rms_baseline_deg']:.3f}° → "
                     f"{r['rms_patched_deg']:.3f}°** "
                     f"({r['rms_delta_deg']:+.3f}°)")
        lines.append("")

    out_md = output_dir / "verify_moon_patches.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"\nOverall: {n_vindicated}/{len(per_patch_results)} VINDICATED, "
          f"verdict: {overall}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
