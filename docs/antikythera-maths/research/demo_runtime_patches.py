"""Demo: runtime kernel patching — overlay vs baseline at a JD ladder.

Encodes the Sol Star System at five JDs across the +/-30 yr horizon,
once with NO patches active (v0.3.1 baseline) and once with each of
the v0.4.0 catalog patches active. Reports per-body phase deltas in
degrees so the patch contributions are visible.

Why this demo?
~~~~~~~~~~~~~~

The structural commitment of v0.4.0's runtime overlay is that
patches are an additive layer on top of the published kernel — the
baseline encode never changes. This demo makes that visible: the
``--no-patch`` column equals the v0.3.1 byte-exact encode; the
``--with-patch`` columns show the per-body sinusoidal contributions.

For each diagonal patch (Mars, Mercury), only the targeted body's
delta is non-zero. For the coupled patch (Jupiter-Saturn), the two
bodies show equal-magnitude opposite-sign deltas (anti-correlated
libration). The amplitude of the contribution at any JD is at most
the patch's ``amplitude_deg``.

For the *full* FFT-residual-shrinkage demonstration (re-run
``de441_error_spectrum`` with all three patches active), see
``figures/runtime_kernel_patching.md`` — that experiment is more
expensive (~6 s on the C native path; ~5 min in pure Python).

Usage
~~~~~

    cd docs/antikythera-maths
    python -m research.demo_runtime_patches

Output goes to stdout as a markdown table.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, List

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from research.bip_instrument import EphemerisBIPInstrument, MODULO, REFERENCE_JD  # noqa: E402
from research import diagnosed_fibers as patches  # noqa: E402


JD_LADDER: List[float] = [
    REFERENCE_JD - 20 * 365.25,
    REFERENCE_JD - 5 * 365.25,
    REFERENCE_JD,
    REFERENCE_JD + 5 * 365.25,
    REFERENCE_JD + 20 * 365.25,
]

PATCHES_TO_DEMO = [
    "mars-7.96yr-diagonal",
    "mercury-10.69yr-diagonal",
    "jupiter-saturn-9.56yr-coupled",
]


def _signed_residue(d: int) -> int:
    d &= MODULO - 1
    return d if d <= (MODULO >> 1) else d - MODULO


def _residue_to_deg(d: int) -> float:
    return _signed_residue(d) / MODULO * 360.0


def main() -> None:
    inst = EphemerisBIPInstrument(D=4096, kernel="de421")  # tiny D for speed
    bodies = inst.body_names

    print("# Runtime kernel patching demo — v0.4.0\n")
    print(
        "Each row encodes the Sol Star System at a JD; columns show "
        "per-body phase delta (in degrees) under each catalog patch "
        "vs the no-patch baseline. With no patches active, the "
        "encoder is byte-identical to v0.3.1.\n"
    )

    for patch_name in PATCHES_TO_DEMO:
        patches.clear_patches()
        baseline_encodes = {jd: inst.encode_state(jd).copy() for jd in JD_LADDER}

        patches.apply_catalog_patch(patch_name)
        patch = patches.CATALOG[patch_name]
        patched_encodes = {jd: inst.encode_state(jd).copy() for jd in JD_LADDER}
        patches.clear_patches()

        # Pick the affected bodies for the column header
        if hasattr(patch, "body"):
            shown = [patch.body]
        else:
            shown = [patch.body_a, patch.body_b]

        print(f"## `{patch_name}` ({patch.kind})\n")
        print(f"- amplitude: **{patch.amplitude_deg:.2f} deg**")
        print(f"- period:    **{patch.period_days:.1f} d** "
              f"({patch.period_days / 365.25:.2f} yr)")
        if hasattr(patch, "correlation"):
            print(f"- correlation: **{patch.correlation:+d}** "
                  f"(anti-correlated libration)" if patch.correlation == -1 else "")
        print()

        # Markdown table
        cols = ["JD", "delta_t (yr)"] + [f"delta_{name} (deg)" for name in shown]
        print("| " + " | ".join(cols) + " |")
        print("| " + " | ".join("---" for _ in cols) + " |")
        for jd in JD_LADDER:
            base_phases = baseline_encodes[jd]
            patched_phases = patched_encodes[jd]
            row = [f"{jd:.2f}", f"{(jd - REFERENCE_JD) / 365.25:+.1f}"]
            for body in shown:
                idx = bodies.index(body)
                delta = int(patched_phases[idx]) - int(base_phases[idx])
                row.append(f"{_residue_to_deg(delta):+.4f}")
            print("| " + " | ".join(row) + " |")
        print()

        # Verify untouched bodies stayed at zero delta (sanity)
        any_drift = False
        sample_jd = JD_LADDER[-1]
        for i, name in enumerate(bodies):
            if name in shown:
                continue
            d = int(patched_encodes[sample_jd][i]) - int(baseline_encodes[sample_jd][i])
            if d != 0:
                print(f"WARNING: untouched body {name!r} shifted by {d} residues "
                      f"under {patch_name!r} — overlay leak?")
                any_drift = True
        if not any_drift:
            print(f"_(sanity: all other 24 bodies untouched at JD={sample_jd:.0f})_\n")

    print("\n---\n")
    print(
        "These tables are reproducible — each row is the difference "
        "between a baseline encode (no patches) and a patched encode "
        "(the named patch active). For coupled patches, the two "
        "columns are equal in magnitude with opposite sign — the "
        "anti-correlated J-S libration signature."
    )


if __name__ == "__main__":
    main()
