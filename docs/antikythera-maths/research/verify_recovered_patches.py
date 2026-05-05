"""Re-run the patch-shrinks-residual benchmark with the
phase-recovered catalog (from `author_phase_recovered_patches.py`).

If the recovered patches hit >= 80% shrinkage on their target peaks,
the spectral-FFT-diagnose-then-overlay methodology is **vindicated**
once you account for full amplitude (2× the magnitude-bin) and phase
(arg of the complex bin). The v0.4.0 catalog's REJECTION was a
phase-and-amplitude authoring bug, not a methodology failure.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.de441_error_spectrum import run_spectrum  # noqa: E402
from research.bodies import BODIES                       # noqa: E402
from research import diagnosed_fibers as _patches        # noqa: E402
from research.diagnosed_fibers import (                  # noqa: E402
    SinusoidPatch, CoupledSinusoidPatch,
)
try:
    from ephemerides_spectral import _native_bip
except ImportError:
    _native_bip = None  # type: ignore[assignment]


PATCH_TARGETS = {
    "mars-7.96yr-diagonal": {
        "body": "mars", "expected_period_yr": 7.96, "tolerance_yr": 0.30,
    },
    "mercury-10.69yr-diagonal": {
        "body": "mercury", "expected_period_yr": 10.69, "tolerance_yr": 0.50,
    },
    "jupiter-saturn-9.56yr-coupled": {
        "body": "jupiter", "secondary_body": "saturn",
        "expected_period_yr": 9.56, "tolerance_yr": 0.30,
    },
}


def _body_index(name: str) -> int:
    return sorted(BODIES.keys()).index(name)


def _apply_recovered_patch(name: str, entry: Dict) -> None:
    """Apply a recovered-catalog entry to BOTH the research-source
    Python registry and the C-side native registry.
    """
    if entry["kind"] == "sinusoid":
        patch = SinusoidPatch(
            name=name,
            body=entry["body"],
            amplitude_deg=float(entry["amplitude_deg"]),
            period_days=float(entry["period_days"]),
            phase_rad=float(entry["phase_rad"]),
            notes="phase-recovered from v0.5.0 FFT complex bin",
        )
    else:
        patch = CoupledSinusoidPatch(
            name=name,
            body_a=entry["body_a"],
            body_b=entry["body_b"],
            amplitude_deg=float(entry["amplitude_deg"]),
            period_days=float(entry["period_days"]),
            phase_rad=float(entry["phase_rad"]),
            correlation=int(entry["correlation"]),
            notes="phase-recovered from v0.5.0 FFT complex bin",
        )
    _patches.apply_patch(patch)
    if _native_bip is not None and _native_bip.HAS_NATIVE:
        if isinstance(patch, SinusoidPatch):
            rc = _native_bip.native_apply_sinusoid_patch(
                name=patch.name, body_idx=_body_index(patch.body),
                amplitude_deg=patch.amplitude_deg,
                period_days=patch.period_days,
                phase_rad=patch.phase_rad,
            )
        else:
            rc = _native_bip.native_apply_coupled_patch(
                name=patch.name,
                body_idx_a=_body_index(patch.body_a),
                body_idx_b=_body_index(patch.body_b),
                amplitude_deg=patch.amplitude_deg,
                period_days=patch.period_days,
                phase_rad=patch.phase_rad,
                correlation=patch.correlation,
            )
        if rc != 0:
            raise RuntimeError(f"native apply returned {rc} for {name!r}")


def _clear_all() -> None:
    _patches.clear_patches()
    if _native_bip is not None and _native_bip.HAS_NATIVE:
        _native_bip.native_clear_patches()


def _find_peak_at_period(body_summary, expected_period_yr, tolerance_yr):
    candidates = [
        p for p in body_summary["top_peaks"]
        if abs(p["period_yr"] - expected_period_yr) <= tolerance_yr
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p["amp_deg"])


def main() -> int:
    repo_root = _HERE.parents[1].parent
    recovered_path = (repo_root / "docs" / "antikythera-maths"
                      / "results" / "phase_recovered_catalog.json")
    if not recovered_path.exists():
        print(f"ERROR: {recovered_path} doesn't exist. Run "
              "author_phase_recovered_patches.py first.")
        return 1
    recovered = json.loads(recovered_path.read_text(encoding="utf-8"))
    print(f"Loaded recovered catalog from {recovered_path}\n")

    _clear_all()
    print("Step 1: baseline FFT (no patches)...", flush=True)
    baseline_summary = run_spectrum(kernel="de441", n_samples=1024,
                                     cadence_days=900.0)

    per_patch_results: List[Dict] = []
    for patch_name, target in PATCH_TARGETS.items():
        if patch_name not in recovered["patches"]:
            print(f"\n  WARN: no recovered entry for {patch_name}; skipping.")
            continue
        entry = recovered["patches"][patch_name]
        if "error" in entry:
            print(f"\n  WARN: recovered entry has error: {entry['error']}; skipping.")
            continue

        _clear_all()
        _apply_recovered_patch(patch_name, entry)
        print(f"\n  >> running with phase-recovered '{patch_name}' active...",
              flush=True)
        t0 = time.perf_counter()
        patched_summary = run_spectrum(
            kernel="de441", n_samples=1024, cadence_days=900.0,
        )
        t1 = time.perf_counter()
        _clear_all()
        print(f"  << finished in {t1 - t0:.1f}s", flush=True)

        bodies = [target["body"]]
        if "secondary_body" in target:
            bodies.append(target["secondary_body"])
        per_body: Dict = {}
        for body in bodies:
            base_peak = _find_peak_at_period(
                baseline_summary["per_body"][body],
                target["expected_period_yr"],
                target["tolerance_yr"],
            )
            patch_peak = _find_peak_at_period(
                patched_summary["per_body"][body],
                target["expected_period_yr"],
                target["tolerance_yr"],
            )
            if base_peak is None:
                per_body[body] = {"error": "no baseline peak in tolerance"}
                continue
            amp_b = base_peak["amp_deg"]
            if patch_peak is None:
                # The targeted period band has no peak in the patched
                # spectrum's top-K. Take that as effectively-100%
                # shrinkage: the patch zapped the band so completely
                # that even after demoting the target peak to <Kth
                # rank, no neighbouring peak remains in tolerance.
                # Approximate the patched amplitude as the smallest
                # top-K peak in the patched spectrum (a conservative
                # upper bound — actual is below that, but unmeasurable
                # without re-running with K=2N which is wasteful).
                top_peaks = patched_summary["per_body"][body].get("top_peaks", [])
                if top_peaks:
                    smallest_topk = min(p["amp_deg"] for p in top_peaks)
                else:
                    smallest_topk = 0.0
                per_body[body] = {
                    "baseline_amp_deg": amp_b,
                    "patched_amp_deg": smallest_topk,
                    "patched_amp_note": (
                        "upper bound: target peak demoted below the "
                        "K-th-strongest patched peak; actual amplitude "
                        "is <= this value"
                    ),
                    "delta_amp_deg": amp_b - smallest_topk,
                    "shrinkage_pct_of_baseline": (
                        100.0 * (amp_b - smallest_topk) / amp_b if amp_b > 0 else 0.0
                    ),
                }
                continue
            amp_p = patch_peak["amp_deg"]
            delta = amp_b - amp_p
            shrink_pct = 100.0 * delta / amp_b if amp_b > 0 else 0.0
            per_body[body] = {
                "baseline_amp_deg": amp_b,
                "patched_amp_deg": amp_p,
                "delta_amp_deg": delta,
                "shrinkage_pct_of_baseline": shrink_pct,
            }
        valid = [r["shrinkage_pct_of_baseline"] for r in per_body.values()
                 if "shrinkage_pct_of_baseline" in r]
        avg = sum(valid) / len(valid) if valid else 0.0
        per_patch_results.append({
            "patch_name": patch_name,
            "recovered_amplitude_deg": entry["amplitude_deg"],
            "recovered_phase_rad": entry["phase_rad"],
            "recovered_correlation": entry.get("correlation"),
            "per_body": per_body,
            "average_shrinkage_pct_of_baseline": avg,
            "verdict": (
                "VINDICATED" if avg >= 80.0
                else "PARTIAL" if avg >= 40.0
                else "REJECTED"
            ),
        })

    all_vindicated = all(r["verdict"] == "VINDICATED" for r in per_patch_results)
    overall = "VINDICATED" if all_vindicated else (
        "PARTIAL" if any(r["verdict"] in {"VINDICATED", "PARTIAL"}
                         for r in per_patch_results) else "REJECTED"
    )

    summary = {
        "overall_verdict": overall,
        "vindication_threshold_pct": 80.0,
        "per_patch": per_patch_results,
    }

    output_dir = repo_root / "docs" / "antikythera-maths" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_json = output_dir / "verify_recovered_patches.json"
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True),
                        encoding="utf-8")

    lines = [
        "# Phase-recovered catalog — patch-shrinks-residual verification",
        "",
        "Re-run of the benchmark using the **phase-recovered** catalog "
        "(amplitudes scaled 2× and phases extracted from the FFT's "
        "complex bin) instead of the v0.4.0 magnitude-only catalog.",
        "",
        f"- **Overall verdict:** **{overall}**",
        "- Vindication threshold: ≥80% shrinkage of the targeted peak amplitude.",
        "",
    ]
    for r in per_patch_results:
        lines.append(f"## `{r['patch_name']}` — verdict: **{r['verdict']}**")
        lines.append("")
        lines.append(f"- Recovered amplitude: **{r['recovered_amplitude_deg']:.4f}°**")
        lines.append(f"- Recovered phase: **{r['recovered_phase_rad']:.4f} rad** "
                     f"({math.degrees(r['recovered_phase_rad']):.2f}°)")
        if r["recovered_correlation"] is not None:
            lines.append(f"- Recovered correlation: **{r['recovered_correlation']:+d}**")
        lines.append(f"- Average shrinkage: **{r['average_shrinkage_pct_of_baseline']:.1f}%**")
        lines.append("")
        lines.append("| body | baseline (deg) | patched (deg) | Δ | shrinkage % |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for body, br in r["per_body"].items():
            if "error" in br:
                lines.append(f"| {body} | n/a | n/a | n/a | (error) |")
                continue
            lines.append(f"| {body} | {br['baseline_amp_deg']:.4f} | "
                         f"{br['patched_amp_deg']:.4f} | "
                         f"{br['delta_amp_deg']:+.4f} | "
                         f"{br['shrinkage_pct_of_baseline']:.1f}% |")
        lines.append("")

    out_md = output_dir / "verify_recovered_patches.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"\nOverall verdict: {overall}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
