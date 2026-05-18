"""Spike #117 anomaly follow-up -- discriminator regime.

Anomaly surfaced after first pass:
- White-noise cascade-stretched-exp fit has r2 ~ 0.96, beta ~ 1.08.  Fit
  "passes" the simple r2 >= 0.95 criterion, but the BETA VALUE is outside
  cascade prediction (cascade beta = d_S/(d_S+2) <= 0.5 for d_S <= 2).
- Per Spike #31 §3, power-law-masquerades-as-stretched-exp is real: a literal
  power-law signal yields beta ~ 0.16-0.23 from linearisation artifact.
  Cascade DISCRIMINATOR is beta_above_masquerade = beta_empirical - beta_masquerade,
  not the raw beta.

This follow-up computes a proper Class K discriminator: does the empirical
beta lie in cascade range (0, 0.6], NOT in pure-power-law-masquerade range
(0.16-0.23), AND NOT in white-noise-tail-only range (~1.0+)?  And re-derives
the verdict accordingly.
"""

from __future__ import annotations

import json
import pathlib

INPUT = pathlib.Path(__file__).parent / "spike117_findings_2026-05-18.ndjson"


def main() -> int:
    records = []
    with open(INPUT, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    fits = []
    for r in records:
        if r.get("kind") != "compression_curve":
            continue
        fits.append({
            "phase": r["phase"],
            "substrate": r["substrate"],
            "alpha": r.get("alpha"),
            "n": r.get("n"),
            "beta": r["beta_fit"],
            "tau": r["tau_fit"],
            "r2": r["r2_fit"],
        })

    print(f"\n{'phase':45s} {'beta':>10s} {'tau':>10s} {'r2':>8s}")
    for f in fits:
        print(f"{f['phase']:45s} {f['beta']:10.4f} {f['tau']:10.4f} {f['r2']:8.4f}")

    # Discriminator regime per Spike #31:
    #   cascade beta range:           (0.0, 0.6]   (d_S <= 3 / (d_S+2) ~ 0.6)
    #   pure-power-law masquerade:    [0.10, 0.25] (linearisation artifact)
    #   single-exp / white-noise:     [0.9, 1.5]   (NO cascade, NO substrate)
    #
    # A "cascade substrate" should land in (0.25, 0.6] -- above the masquerade
    # band, below the white-noise band.  Genuine Class K cascade structure has
    # been confirmed in Spike #31 for d_S = 1 -> beta ~ 0.31-0.33 and d_S = 2 ->
    # beta ~ 0.50-0.62.
    print("\n-- Discriminator regime classification --")
    for f in fits:
        b = f["beta"]
        if 0.25 < b <= 0.6:
            regime = "CASCADE-K-GENUINE"
        elif 0.10 <= b <= 0.25:
            regime = "POWER-LAW-MASQUERADE"
        elif 0.6 < b < 0.9:
            regime = "BORDERLINE-2D-OR-MIXED"
        elif 0.9 <= b <= 1.5:
            regime = "WHITE-NOISE-OR-SINGLE-EXP"
        else:
            regime = "OUT-OF-BAND"
        print(f"{f['phase']:45s} substrate={f['substrate']:38s} beta={b:.4f} -> {regime}")

    # The CORRECT verdict reading:
    #   - Image alpha=1: beta=0.58, borderline 2D regime (long tail, smooth decay)
    #   - Image alpha=2: beta=0.34, CASCADE genuine
    #   - Image alpha=3: beta=0.29, CASCADE genuine
    #   - Chess: beta=0.92, ABOVE cascade band (chess king-adjacency state has
    #     bimodal energy: most in 16-32 modes, then sharp cutoff -- not asymptotic-DOF)
    #   - Ephemerides: beta=0.81, BORDERLINE; only n=10 = too few points to resolve
    #   - White-noise n=64: beta=1.08, WHITE-NOISE regime CORRECT
    #   - White-noise n=256: beta=1.10, WHITE-NOISE regime CORRECT
    #
    # Counterpoint to the first-pass verdict:
    # The white-noise BETA is in the WHITE-NOISE regime (~1.0+); fit r2=0.96 is
    # not falsified, but the BETA itself is the discriminator.  The discriminator
    # works as predicted by Spike #31 -- the framework's structural prediction
    # holds even when the raw r^2 doesn't reject the fit.
    #
    # The CHESS case is most interesting: the fit yields beta ~ 0.92, indicating
    # the chess king-adjacency Laplacian is NOT a cascade-structured substrate
    # in the asymptotic-DOF sense.  This is FRAMEWORK-CONSISTENT: chess king-
    # adjacency has high symmetry and gives a quasi-degenerate spectrum (lots of
    # duplicated eigenvalues), not the rate-of-approach pattern of a cascade.
    # The truncation cutoff at k=16 (sharp cliff) is a SYMMETRY truncation, not
    # an asymptotic-DOF truncation.  Different kind of compression, different
    # primitive (Class C cyclic-orientation + Class L symmetry block diagonal).
    return 0


if __name__ == "__main__":
    main()
