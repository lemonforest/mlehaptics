"""Patch-shrinks-residual benchmark — earn the right to predict missing data.

For each diagnosed-fiber patch in the v0.4.0 CATALOG, run the
`de441_error_spectrum` FFT analysis twice — once with the patch
inactive (baseline) and once with the patch active — and quantify
how much the targeted residual peak shrunk.

The argument
~~~~~~~~~~~~

The catalog patches are *plausible* (each was authored from a v0.3.1
FFT residual peak with the right amplitude and period), but the
claim that they actually shrink the targeted residual is unaudited
until we measure it.

If a patch's `amplitude_deg` is `A` and the targeted FFT peak's
amplitude is `P`, then a perfect cancellation would shrink the peak
to `0` — i.e. the patch removed all `P` degrees of residual. A
no-effect patch would leave the peak at `P`. The metric we report:

    shrinkage_pct = 100 * (P_baseline - P_patched) / P_baseline

If shrinkage_pct >= 80% across all three catalog patches, the
methodology is **vindicated**: spectral-FFT-diagnosed-then-overlay
predicts missing physics, and we can author future patches the same
way with confidence (including for bodies / horizons where
ephemeris truth isn't yet available).

Implementation
~~~~~~~~~~~~~~

`run_spectrum` is the workhorse from `de441_error_spectrum.py`. It
calls `_native_bip.encode_state` (or the Python BIP fallback) per
JD. Both paths consult the runtime patch registry — so we just
manage the registry around each spectrum run via `bridge.apply_patch`
and `bridge.clear_patches`.

Run from the repo root with skyfield_data/de441.bsp staged:

    cd docs/antikythera-maths
    python -m research.patch_shrinks_residual

Outputs:

    results/patch_shrinks_residual.json    machine-readable
    results/patch_shrinks_residual.md      markdown summary
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.de441_error_spectrum import run_spectrum  # noqa: E402

# IMPORTANT — registry plumbing.
#
# `run_spectrum` calls `_native_bip.encode_state` if native is loaded;
# otherwise it falls back to `research.bip_instrument.EphemerisBIPInstrument
# .encode_state` (Python BIP). The two paths consult DIFFERENT patch
# registries:
#
#   Python BIP path: `research.diagnosed_fibers._ACTIVE` (research-source)
#   Native C path:   the C library's static patch table (via
#                    es_apply_patch / es_clear_patches)
#
# The wheel-installed `ephemerides_spectral._research.diagnosed_fibers`
# is a third, unrelated module instance whose `_ACTIVE` is what
# `bridge.apply_patch` mutates — neither encode path under test reads
# from it. (The first-pass benchmark mistakenly used `bridge.apply_patch`
# and got 0.0% shrinkage on every patch because the patches landed in
# the wrong registry. See branch history.)
#
# The fix here: apply each patch to BOTH the research-source Python
# registry AND the native C registry directly. Whichever path
# `run_spectrum` uses internally, the patch is in scope.
from research import diagnosed_fibers as _patches  # noqa: E402
from research.diagnosed_fibers import (                 # noqa: E402
    CATALOG, SinusoidPatch, CoupledSinusoidPatch,
)
try:
    from ephemerides_spectral import _native_bip
except ImportError:
    _native_bip = None  # type: ignore[assignment]


# Pretty body labels for each catalog patch + the period (in years)
# we'd expect that patch to attack. Used to identify the matching
# FFT peak in the per-body spectrum.
PATCH_TARGETS: Dict[str, Dict] = {
    "mars-7.96yr-diagonal": {
        "body": "mars",
        "expected_period_yr": 7.96,
        "tolerance_yr": 0.10,
    },
    "mercury-10.69yr-diagonal": {
        "body": "mercury",
        "expected_period_yr": 10.69,
        "tolerance_yr": 0.15,
    },
    "jupiter-saturn-9.56yr-coupled": {
        # Coupled: shrinks the matching peak on BOTH bodies. The
        # benchmark records both for completeness; the reported
        # shrinkage is the average.
        "body": "jupiter",
        "secondary_body": "saturn",
        "expected_period_yr": 9.56,
        "tolerance_yr": 0.10,
    },
}


def _body_index(name: str) -> int:
    """Return the index of `name` in the canonical sorted body list.

    The C codegen emits es_bodies in the same sorted order; the
    research source's BODIES dict is the SSOT for that order.
    """
    from research.bodies import BODIES
    return sorted(BODIES.keys()).index(name)


def _apply_patch_dual(patch_name: str) -> None:
    """Apply a CATALOG patch to BOTH the research-source Python registry
    and (if native is loaded) the C-side registry.

    The native binary uses its own patch registry; calling
    `_patches.apply_catalog_patch` only mutates the Python registry.
    For correctness across both encode paths we mirror to native here.
    """
    _patches.clear_patches()
    if _native_bip is not None and _native_bip.HAS_NATIVE:
        _native_bip.native_clear_patches()

    patch = _patches.apply_catalog_patch(patch_name)

    if _native_bip is not None and _native_bip.HAS_NATIVE:
        if isinstance(patch, SinusoidPatch):
            rc = _native_bip.native_apply_sinusoid_patch(
                name=patch.name, body_idx=_body_index(patch.body),
                amplitude_deg=patch.amplitude_deg,
                period_days=patch.period_days,
                phase_rad=patch.phase_rad,
            )
        elif isinstance(patch, CoupledSinusoidPatch):
            rc = _native_bip.native_apply_coupled_patch(
                name=patch.name,
                body_idx_a=_body_index(patch.body_a),
                body_idx_b=_body_index(patch.body_b),
                amplitude_deg=patch.amplitude_deg,
                period_days=patch.period_days,
                phase_rad=patch.phase_rad,
                correlation=patch.correlation,
            )
        else:
            raise TypeError(f"unknown patch type: {type(patch).__name__}")
        if rc != 0:
            raise RuntimeError(
                f"native_apply_*_patch returned status {rc} for "
                f"{patch_name!r}; cannot run benchmark with "
                f"out-of-sync registries."
            )


def _clear_patches_dual() -> None:
    _patches.clear_patches()
    if _native_bip is not None and _native_bip.HAS_NATIVE:
        _native_bip.native_clear_patches()


def _find_peak_at_period(
    body_summary: Dict,
    expected_period_yr: float,
    tolerance_yr: float,
) -> Optional[Dict]:
    """From a per-body summary's `top_peaks`, return the peak whose
    period most closely matches `expected_period_yr` (within
    `tolerance_yr`). Returns None if no peak is in tolerance.

    The de441_error_spectrum reports the top 5 peaks; in practice
    multiple of them often cluster around the same period (FFT
    leakage). We pick the strongest among those in tolerance.
    """
    candidates = [
        p for p in body_summary["top_peaks"]
        if abs(p["period_yr"] - expected_period_yr) <= tolerance_yr
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p["amp_deg"])


def _benchmark_one_patch(
    patch_name: str,
    baseline_summary: Dict,
    n_samples: int,
    cadence_days: float,
) -> Dict:
    """Run the FFT analysis with `patch_name` active; compare the
    targeted peak to the baseline.

    Returns a dict with the patch's name + the patched/baseline peak
    amplitudes + shrinkage metrics.
    """
    target = PATCH_TARGETS[patch_name]
    catalog_entry = CATALOG[patch_name]

    _apply_patch_dual(patch_name)
    print(f"\n  >> running with patch '{patch_name}' active...", flush=True)
    t0 = time.perf_counter()
    patched_summary = run_spectrum(
        kernel="de441",
        n_samples=n_samples,
        cadence_days=cadence_days,
    )
    t1 = time.perf_counter()
    _clear_patches_dual()
    print(f"  << finished in {t1 - t0:.1f}s; clearing patches.", flush=True)

    # Pick the peak in tolerance for each affected body.
    bodies = [target["body"]]
    if "secondary_body" in target:
        bodies.append(target["secondary_body"])

    body_results = {}
    for body in bodies:
        if body not in baseline_summary["per_body"] or body not in patched_summary["per_body"]:
            body_results[body] = {"error": "body missing from one of the spectra"}
            continue
        baseline_peak = _find_peak_at_period(
            baseline_summary["per_body"][body],
            target["expected_period_yr"],
            target["tolerance_yr"],
        )
        patched_peak = _find_peak_at_period(
            patched_summary["per_body"][body],
            target["expected_period_yr"],
            target["tolerance_yr"],
        )
        if baseline_peak is None or patched_peak is None:
            body_results[body] = {
                "error": "no peak in tolerance window",
                "baseline_peak": baseline_peak,
                "patched_peak": patched_peak,
            }
            continue

        amp_b = baseline_peak["amp_deg"]
        amp_p = patched_peak["amp_deg"]
        delta = amp_b - amp_p
        shrinkage_pct = 100.0 * delta / amp_b if amp_b > 0 else 0.0
        # Patch amplitude budget — fraction of the patch's authored
        # amplitude this body received.
        if "secondary_body" in target and body == target["secondary_body"]:
            # Coupled patch: secondary body got `correlation` * delta
            # from the same sinusoid; absolute amplitude is the same.
            patch_amp_for_body = catalog_entry.amplitude_deg
        else:
            patch_amp_for_body = catalog_entry.amplitude_deg
        shrinkage_vs_patch_pct = (
            100.0 * delta / patch_amp_for_body if patch_amp_for_body > 0 else 0.0
        )

        body_results[body] = {
            "baseline_peak_period_yr": baseline_peak["period_yr"],
            "baseline_peak_amp_deg": amp_b,
            "patched_peak_period_yr": patched_peak["period_yr"],
            "patched_peak_amp_deg": amp_p,
            "delta_amp_deg": delta,
            "shrinkage_pct_of_baseline": shrinkage_pct,
            "patch_amplitude_deg": patch_amp_for_body,
            "shrinkage_pct_of_patch_amp": shrinkage_vs_patch_pct,
        }

    # Aggregate score: average shrinkage across affected bodies.
    valid_shrinkages = [
        r["shrinkage_pct_of_baseline"]
        for r in body_results.values()
        if isinstance(r, dict) and "shrinkage_pct_of_baseline" in r
    ]
    avg_shrinkage_pct = sum(valid_shrinkages) / len(valid_shrinkages) if valid_shrinkages else 0.0

    return {
        "patch_name": patch_name,
        "patch_kind": catalog_entry.kind,
        "patch_amplitude_deg": catalog_entry.amplitude_deg,
        "patch_period_days": catalog_entry.period_days,
        "expected_period_yr": target["expected_period_yr"],
        "per_body": body_results,
        "average_shrinkage_pct_of_baseline": avg_shrinkage_pct,
        "verdict": (
            "VINDICATED" if avg_shrinkage_pct >= 80.0
            else "PARTIAL" if avg_shrinkage_pct >= 40.0
            else "REJECTED"
        ),
    }


def run_benchmark(
    n_samples: int = 1024,
    cadence_days: float = 900.0,
) -> Dict:
    """Run the full patch-shrinks-residual benchmark on every catalog
    patch.

    Returns a top-level summary with the baseline FFT, per-patch
    results, and an overall verdict (does the methodology earn the
    right to predict missing data?).
    """
    print("\n=== Patch-shrinks-residual benchmark ===\n")

    _clear_patches_dual()
    print("Step 1: baseline FFT (no patches active)...", flush=True)
    t0 = time.perf_counter()
    baseline_summary = run_spectrum(
        kernel="de441",
        n_samples=n_samples,
        cadence_days=cadence_days,
    )
    t_base = time.perf_counter() - t0
    print(f"  baseline done in {t_base:.1f}s.", flush=True)

    per_patch_results: List[Dict] = []
    for patch_name in PATCH_TARGETS:
        result = _benchmark_one_patch(
            patch_name=patch_name,
            baseline_summary=baseline_summary,
            n_samples=n_samples,
            cadence_days=cadence_days,
        )
        per_patch_results.append(result)

    # Overall verdict — METHODOLOGY VINDICATED if every patch hit >= 80%
    # shrinkage on its targeted body's targeted peak.
    all_vindicated = all(r["verdict"] == "VINDICATED" for r in per_patch_results)
    any_rejected = any(r["verdict"] == "REJECTED" for r in per_patch_results)
    overall_verdict = (
        "VINDICATED" if all_vindicated
        else "REJECTED" if any_rejected
        else "PARTIAL"
    )

    summary = {
        "n_samples": n_samples,
        "cadence_days": cadence_days,
        "kernel_actual": baseline_summary["kernel_actual"],
        "native_available": baseline_summary["native_available"],
        "baseline_encode_seconds": baseline_summary["encode_seconds"],
        "baseline_summary": baseline_summary,
        "per_patch": per_patch_results,
        "overall_verdict": overall_verdict,
        "vindication_threshold_pct": 80.0,
    }
    return summary


def write_outputs(summary: Dict, output_dir: Path) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "patch_shrinks_residual.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True),
                         encoding="utf-8")

    lines: List[str] = [
        "# Patch-shrinks-residual benchmark",
        "",
        "Earn the right to predict the missing data.",
        "",
        "**Hypothesis**: each v0.4.0 catalog patch shrinks the targeted "
        "FFT residual peak by ~the patch's authored amplitude. If true "
        "across all three patches, the spectral-FFT-diagnose-then-overlay "
        "methodology is *vindicated* and we can author future patches "
        "(for the new moons, multi-millennium horizons, missing physics) "
        "the same way with quantified confidence.",
        "",
        f"- **Overall verdict:** **{summary['overall_verdict']}**",
        f"- Vindication threshold: ≥80% shrinkage of the targeted peak amplitude.",
        f"- Sample grid: {summary['n_samples']} samples @ "
        f"{summary['cadence_days']:.1f} d cadence.",
        f"- Native encoder used: {summary['native_available']}.",
        f"- Baseline FFT time: {summary['baseline_encode_seconds']:.1f} s.",
        "",
    ]

    for r in summary["per_patch"]:
        lines.append(f"## `{r['patch_name']}` — verdict: **{r['verdict']}**")
        lines.append("")
        lines.append(f"- Kind: `{r['patch_kind']}`")
        lines.append(f"- Patch amplitude: **{r['patch_amplitude_deg']:.2f}°**")
        lines.append(f"- Patch period: **{r['patch_period_days']:.1f} d** "
                     f"({r['expected_period_yr']:.2f} yr)")
        lines.append(f"- Average shrinkage of baseline peak: "
                     f"**{r['average_shrinkage_pct_of_baseline']:.1f}%**")
        lines.append("")
        lines.append("| body | baseline peak (deg) | patched peak (deg) | "
                     "Δ (deg) | shrinkage % of baseline | shrinkage % of patch amp |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for body, br in r["per_body"].items():
            if "error" in br:
                lines.append(f"| {body} | n/a | n/a | n/a | n/a | (error: {br['error']}) |")
                continue
            lines.append(
                f"| {body} | "
                f"{br['baseline_peak_amp_deg']:.4f} | "
                f"{br['patched_peak_amp_deg']:.4f} | "
                f"{br['delta_amp_deg']:+.4f} | "
                f"{br['shrinkage_pct_of_baseline']:.1f}% | "
                f"{br['shrinkage_pct_of_patch_amp']:.1f}% |"
            )
        lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    if summary["overall_verdict"] == "VINDICATED":
        lines.append(
            "All three catalog patches shrink their targeted FFT peak "
            "by ≥80% of the baseline amplitude. The spectral-FFT-"
            "diagnose-then-overlay methodology is **vindicated**: we "
            "can author future patches the same way and trust them "
            "to do what they claim, including for residuals beyond the "
            "horizon of any available ephemeris truth (multi-millennium "
            "horizons, the new moons before sat441/jup340 are wired, "
            "etc.). The catalog has earned the right to predict missing "
            "data."
        )
    elif summary["overall_verdict"] == "REJECTED":
        lines.append(
            "At least one catalog patch fails to shrink its targeted "
            "peak meaningfully. The spectral-FFT-diagnose-then-overlay "
            "methodology is **rejected as a forecasting tool** for the "
            "currently-authored catalog. Either the patch parameters "
            "(amplitude / period / phase) are wrong, the residual peaks "
            "aren't sinusoidal at the FFT cadence, or the patches are "
            "interacting with each other in unexpected ways. Drop back "
            "to first-principles α derivation."
        )
    else:
        lines.append(
            "The catalog patches partially shrink their targeted peaks "
            "(≥40% but not ≥80%). The methodology is **partially**-"
            "earning predictive power; investigate per-patch why the "
            "shrinkage is incomplete (is the residual peak really a "
            "single sinusoid, or a cluster? does the patch period need "
            "tuning to a sub-resonance? is there a phase offset we "
            "didn't author?)."
        )
    lines.append("")

    md_path = output_dir / "patch_shrinks_residual.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    summary = run_benchmark()
    repo_root = _HERE.parents[1].parent
    output_dir = repo_root / "docs" / "antikythera-maths" / "results"
    json_path, md_path = write_outputs(summary, output_dir)
    print(f"\nWrote:\n  {json_path}\n  {md_path}")
    print(f"\nOverall verdict: {summary['overall_verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
