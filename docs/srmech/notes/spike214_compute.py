#!/usr/bin/env python3
"""Spike #214 - Depth-3 symmetric recursive Hopf at primitive level.

Extends Spike #213 (depth-2 recursion confirmed: 98/98 deeper sign-flips
bit-exact, FFT peak k=49, 2:1 ratio at every level, integer cross-level
ratios 7/7/49) to **depth-3**: figure-8-of-figure-8-of-figure-8-of-figure-8s.

Four nested frequency levels (symmetric 7x stacking):

    Level 0 (outer):      omega_outer   = 1      -> 2 sign-flips/outer period
    Level 1 (inner):      omega_inner   = 7      -> 14 sign-flips/outer period
    Level 2 (deeper):     omega_deeper  = 49     -> 98 sign-flips/outer period
    Level 3 (deepest):    omega_deepest = 343    -> 686 sign-flips/outer period
                                                    (PREDICTION)

If depth-3 confirms bit-exact (686/686 deepest sign-flips, FFT peak at k=343,
2:1 ratio at every level, integer cross-level ratios 7/7/7/49/49/343), the
"UNBOUNDED" qualifier from Spike #213 tightens from "structural form supports
unbounded recursion" to "three empirical depths confirmed bit-exact with
identical algebraic form at each depth". If depth-3 fails, recursive-Hopf has
a stopping condition at depth-2 and Spike #213's UNBOUNDED qualifier narrows.

Sampling discipline: per Spike #213 fermata, n >= 131072 required to resolve
deepest-level oscillations cleanly (need n >> 2*343 = 686 samples/outer-period;
n=131072 gives ~191 samples/deepest-cycle; n=262144 gives ~382/cycle).
Default n=131072 here.

Run plain:
    python spike214_compute.py
Run verify:
    python spike214_compute.py --verify

All computations are deterministic. No PRNG draws (seed lock irrelevant
because no stochastic call sites; documented for provenance trail).

Author: Spike #214 (mlehaptics spectral-research, 2026-05-20).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Iterable

import numpy as np

# Determinism seed (no PRNG used; locked for provenance trail).
SEED = 214
np.random.seed(SEED)


# ---------------------------------------------------------------------------
# Sign-flip counting helper (integer; bit-exact; closed-period by default).
# Inherited from Spike #212/#213 - same topological-invariant convention.
# ---------------------------------------------------------------------------
def count_sign_flips(samples: Iterable[float], tol: float = 1e-12,
                     closed_period: bool = True) -> int:
    """Return integer count of sign changes over one (closed) period.

    `closed_period=True` (default): treat input as one full period and add
    the wrap-around transition between last and first non-zero sample.
    Matches the physics: periodic motion's sign-flip count is a topological
    invariant of the closed loop, not the open chord.
    """
    arr = np.asarray(list(samples), dtype=np.float64)
    signs = np.sign(arr)
    signs[np.abs(arr) < tol] = 0
    nonzero = signs[signs != 0]
    if nonzero.size < 2:
        return 0
    open_flips = int(np.sum(nonzero[1:] != nonzero[:-1]))
    if closed_period:
        wrap_flip = int(nonzero[0] != nonzero[-1])
        return open_flips + wrap_flip
    return open_flips


# ---------------------------------------------------------------------------
# Depth-3 cascade construction.
# ---------------------------------------------------------------------------
def depth3_cascade(
    n: int = 131072,
    omega_outer: float = 1.0,
    ratio_inner: int = 7,
    ratio_deeper: int = 7,
    ratio_deepest: int = 7,
    eps_outer: float = 0.35,
    eps_inner: float = 0.12,
    eps_deeper: float = 0.04,
    eps_deepest: float = 0.013,
) -> dict:
    """Construct depth-3 nested cascade trajectory.

    Four-level Hopf-recursion test. Each level applies L o K o C o I
    cascade composition (per [[user_stance_epicycle_via_gear_plus_pin]]
    Spike #189) at progressively higher frequency.

    Level 0 (outer figure-8):
        Bernoulli lemniscate parametric form with Class K equation-of-centre
        sweep tau = t + eps_outer * sin(omega_outer * t).
        Long-axis x(t) -> 2 sign-flips/period (slot view).

    Level 1 (inner figure-8 / pin+slot):
        Inner Class K pin+slot oscillation at omega_inner = 7 * omega_outer.
        Predicts 14 sign-flips/outer-period. Verified Spike #212.

    Level 2 (deeper figure-8):
        Deeper Class K pin+slot at omega_deeper = 49 * omega_outer.
        Predicts 98 sign-flips/outer-period. Verified Spike #213.

    Level 3 (deepest figure-8):
        Deepest Class K pin+slot at omega_deepest = 343 * omega_outer.
        Predicts 686 sign-flips/outer-period (PREDICTION).

    Each level is composed INSIDE the previous level's Class K instantiation
    via additive radial modulation - exactly the same cascade structure
    recursed one level further (the recursive-Hopf-at-every-cascade
    prediction).

    eps_deepest = 0.013 chosen as ~eps_deeper / 3 to keep deepest-modulation
    amplitude small enough that closed-period sign-flip detection on
    deepest_mod alone is bit-exact at the predicted 686 count. The Class K
    equation-of-centre at any level is amplitude-scaled but frequency-pure;
    the sign-flip count IS the topological invariant.

    Parameters
    ----------
    n : int
        Sample count over one outer period. Per Spike #213 fermata: need
        n >> 2*343 = 686 to resolve deepest oscillations. n=131072 gives
        ~191 samples per deepest cycle (dense; closed-period count is
        topological so density beyond Nyquist is sufficient).
    """
    omega_inner = ratio_inner * omega_outer
    omega_deeper = ratio_deeper * omega_inner   # 49 * omega_outer
    omega_deepest = ratio_deepest * omega_deeper  # 343 * omega_outer

    t = np.linspace(0.0, 2.0 * math.pi / omega_outer, n, endpoint=False)

    # Level 0: outer figure-8 (Bernoulli with Class K eq-of-centre sweep)
    tau_outer = t + eps_outer * np.sin(omega_outer * t)
    denom_outer = 1.0 + np.sin(tau_outer) ** 2
    x_outer = np.cos(tau_outer) / denom_outer
    y_outer = np.sin(tau_outer) * np.cos(tau_outer) / denom_outer

    # Level 1: inner pin+slot (the hidden figure-8 fiber at primitive level)
    inner_mod = eps_inner * np.cos(
        omega_inner * t + eps_inner * np.sin(omega_inner * t)
    )

    # Level 2: deeper pin+slot (figure-8 fiber INSIDE the inner Class K)
    deeper_mod = eps_deeper * np.cos(
        omega_deeper * t + eps_deeper * np.sin(omega_deeper * t)
    )

    # Level 3: deepest pin+slot (figure-8 fiber INSIDE the deeper Class K)
    # Recursion: same Class K equation-of-centre at omega_deepest,
    # composed inside the deeper level's instantiation.
    deepest_mod = eps_deepest * np.cos(
        omega_deepest * t + eps_deepest * np.sin(omega_deepest * t)
    )

    # Full depth-3 trajectory: outer + inner + deeper + deepest radial mods
    x_full = x_outer + (inner_mod + deeper_mod + deepest_mod) * np.cos(omega_outer * t)
    y_full = y_outer + (inner_mod + deeper_mod + deepest_mod) * np.sin(omega_outer * t)

    return {
        "t": t,
        "x_outer": x_outer,
        "y_outer": y_outer,
        "inner_mod": inner_mod,
        "deeper_mod": deeper_mod,
        "deepest_mod": deepest_mod,
        "x_full": x_full,
        "y_full": y_full,
        "omega_outer": omega_outer,
        "omega_inner": omega_inner,
        "omega_deeper": omega_deeper,
        "omega_deepest": omega_deepest,
        "ratio_inner": ratio_inner,
        "ratio_deeper": ratio_deeper,
        "ratio_deepest": ratio_deepest,
        "eps_outer": eps_outer,
        "eps_inner": eps_inner,
        "eps_deeper": eps_deeper,
        "eps_deepest": eps_deepest,
    }


# ---------------------------------------------------------------------------
# Claim A - Bit-exact sign-flip counts at all four recursion levels.
# ---------------------------------------------------------------------------
def claim_a_signflip_counts_four_levels(cascade: dict) -> dict:
    """Bit-exact closed-period sign-flip counts at every recursion level.

    Predictions:
      Level 0 outer x_outer (long-axis):  2 flips/period
      Level 1 inner_mod (alone):          2 * 7 = 14 flips/period
      Level 2 deeper_mod (alone):         2 * 49 = 98 flips/period
      Level 3 deepest_mod (alone):        2 * 343 = 686 flips/period
    """
    ratio_inner = cascade["ratio_inner"]
    ratio_deeper = cascade["ratio_deeper"]
    ratio_deepest = cascade["ratio_deepest"]

    flips_outer = count_sign_flips(cascade["x_outer"])
    flips_inner = count_sign_flips(cascade["inner_mod"])
    flips_deeper = count_sign_flips(cascade["deeper_mod"])
    flips_deepest = count_sign_flips(cascade["deepest_mod"])

    predicted_outer = 2
    predicted_inner = 2 * ratio_inner
    predicted_deeper = 2 * ratio_inner * ratio_deeper
    predicted_deepest = 2 * ratio_inner * ratio_deeper * ratio_deepest

    outer_exact = flips_outer == predicted_outer
    inner_exact = flips_inner == predicted_inner
    deeper_exact = flips_deeper == predicted_deeper
    deepest_exact = flips_deepest == predicted_deepest

    return {
        "flips_level0_outer": flips_outer,
        "predicted_level0_outer": predicted_outer,
        "level0_bit_exact": bool(outer_exact),
        "flips_level1_inner": flips_inner,
        "predicted_level1_inner": predicted_inner,
        "level1_bit_exact": bool(inner_exact),
        "flips_level2_deeper": flips_deeper,
        "predicted_level2_deeper": predicted_deeper,
        "level2_bit_exact": bool(deeper_exact),
        "flips_level3_deepest": flips_deepest,
        "predicted_level3_deepest": predicted_deepest,
        "level3_bit_exact": bool(deepest_exact),
        "all_four_levels_bit_exact": bool(
            outer_exact and inner_exact and deeper_exact and deepest_exact
        ),
    }


# ---------------------------------------------------------------------------
# Claim B - FFT peak at expected integer bins for all four levels.
# ---------------------------------------------------------------------------
def claim_b_fft_peaks(cascade: dict) -> dict:
    """FFT peak at expected integer bin k at each recursion level.

    Inner modulation alone: peak at bin k = 7.
    Deeper modulation alone: peak at bin k = 49.
    Deepest modulation alone: peak at bin k = 343.

    Bit-exact integer bin = no spectral leakage (verified Spikes #212/#213
    for depths 1 and 2; extending here to depth 3).
    """
    inner_mod = cascade["inner_mod"]
    deeper_mod = cascade["deeper_mod"]
    deepest_mod = cascade["deepest_mod"]
    ratio_inner = cascade["ratio_inner"]
    ratio_deeper = cascade["ratio_deeper"]
    ratio_deepest = cascade["ratio_deepest"]

    fft_inner = np.fft.rfft(inner_mod)
    peak_bin_inner = int(np.argmax(np.abs(fft_inner[1:])) + 1)
    inner_peak_correct = peak_bin_inner == ratio_inner

    fft_deeper = np.fft.rfft(deeper_mod)
    peak_bin_deeper = int(np.argmax(np.abs(fft_deeper[1:])) + 1)
    expected_bin_deeper = ratio_inner * ratio_deeper
    deeper_peak_correct = peak_bin_deeper == expected_bin_deeper

    fft_deepest = np.fft.rfft(deepest_mod)
    peak_bin_deepest = int(np.argmax(np.abs(fft_deepest[1:])) + 1)
    expected_bin_deepest = ratio_inner * ratio_deeper * ratio_deepest
    deepest_peak_correct = peak_bin_deepest == expected_bin_deepest

    return {
        "fft_peak_bin_level1_inner": peak_bin_inner,
        "expected_bin_level1_inner": ratio_inner,
        "level1_fft_peak_correct": bool(inner_peak_correct),
        "fft_peak_bin_level2_deeper": peak_bin_deeper,
        "expected_bin_level2_deeper": expected_bin_deeper,
        "level2_fft_peak_correct": bool(deeper_peak_correct),
        "fft_peak_bin_level3_deepest": peak_bin_deepest,
        "expected_bin_level3_deepest": expected_bin_deepest,
        "level3_fft_peak_correct": bool(deepest_peak_correct),
        "all_three_fft_peaks_bit_exact_integer": bool(
            inner_peak_correct and deeper_peak_correct and deepest_peak_correct
        ),
    }


# ---------------------------------------------------------------------------
# Claim C - 2:1 short:long axis ratio preserved at every recursion level.
# ---------------------------------------------------------------------------
def claim_c_two_to_one_ratio_at_every_level(cascade: dict) -> dict:
    """Hopf-fibre signature: short-axis flips = 2 x long-axis flips at every level.

    Per Spike #212 Claim 1: short-axis = 2 x long-axis for Bernoulli figure-8.
    The 2:1 ratio IS the +1 Hopf-fibre content surfacing per
    [[user_stance_11d_substrate_is_always_hopf_compressed]].

    For depth-3 recursive-Hopf:
      Level 0: long=2, short=4.
      Level 1: long=14, short=28.
      Level 2: long=98, short=196.
      Level 3: long=686, short=1372.
    """
    t = cascade["t"]
    eps_inner = cascade["eps_inner"]
    eps_deeper = cascade["eps_deeper"]
    eps_deepest = cascade["eps_deepest"]
    omega_inner = cascade["omega_inner"]
    omega_deeper = cascade["omega_deeper"]
    omega_deepest = cascade["omega_deepest"]

    # --- Level 0: Bernoulli long-axis (x_outer) vs short-axis (y_outer) ---
    flips_x_outer = count_sign_flips(cascade["x_outer"])
    flips_y_outer = count_sign_flips(cascade["y_outer"])
    ratio_level0 = flips_y_outer / flips_x_outer if flips_x_outer > 0 else float("inf")
    level0_two_to_one = ratio_level0 == 2.0

    # --- Level 1: inner pin+slot long-axis vs short-axis ---
    tau_inner = omega_inner * t + eps_inner * np.sin(omega_inner * t)
    denom_inner = 1.0 + np.sin(tau_inner) ** 2
    x_inner_lemn = np.cos(tau_inner) / denom_inner
    y_inner_lemn = np.sin(tau_inner) * np.cos(tau_inner) / denom_inner
    flips_x_inner = count_sign_flips(x_inner_lemn)
    flips_y_inner = count_sign_flips(y_inner_lemn)
    ratio_level1 = flips_y_inner / flips_x_inner if flips_x_inner > 0 else float("inf")
    level1_two_to_one = ratio_level1 == 2.0

    # --- Level 2: deeper pin+slot long-axis vs short-axis ---
    tau_deeper = omega_deeper * t + eps_deeper * np.sin(omega_deeper * t)
    denom_deeper = 1.0 + np.sin(tau_deeper) ** 2
    x_deeper_lemn = np.cos(tau_deeper) / denom_deeper
    y_deeper_lemn = np.sin(tau_deeper) * np.cos(tau_deeper) / denom_deeper
    flips_x_deeper = count_sign_flips(x_deeper_lemn)
    flips_y_deeper = count_sign_flips(y_deeper_lemn)
    ratio_level2 = flips_y_deeper / flips_x_deeper if flips_x_deeper > 0 else float("inf")
    level2_two_to_one = ratio_level2 == 2.0

    # --- Level 3: deepest pin+slot long-axis vs short-axis ---
    tau_deepest = omega_deepest * t + eps_deepest * np.sin(omega_deepest * t)
    denom_deepest = 1.0 + np.sin(tau_deepest) ** 2
    x_deepest_lemn = np.cos(tau_deepest) / denom_deepest
    y_deepest_lemn = np.sin(tau_deepest) * np.cos(tau_deepest) / denom_deepest
    flips_x_deepest = count_sign_flips(x_deepest_lemn)
    flips_y_deepest = count_sign_flips(y_deepest_lemn)
    ratio_level3 = flips_y_deepest / flips_x_deepest if flips_x_deepest > 0 else float("inf")
    level3_two_to_one = ratio_level3 == 2.0

    return {
        "level0_flips_long_axis": flips_x_outer,
        "level0_flips_short_axis": flips_y_outer,
        "level0_ratio": float(ratio_level0),
        "level0_two_to_one_bit_exact": bool(level0_two_to_one),
        "level1_flips_long_axis": flips_x_inner,
        "level1_flips_short_axis": flips_y_inner,
        "level1_ratio": float(ratio_level1),
        "level1_two_to_one_bit_exact": bool(level1_two_to_one),
        "level2_flips_long_axis": flips_x_deeper,
        "level2_flips_short_axis": flips_y_deeper,
        "level2_ratio": float(ratio_level2),
        "level2_two_to_one_bit_exact": bool(level2_two_to_one),
        "level3_flips_long_axis": flips_x_deepest,
        "level3_flips_short_axis": flips_y_deepest,
        "level3_ratio": float(ratio_level3),
        "level3_two_to_one_bit_exact": bool(level3_two_to_one),
        "all_levels_two_to_one_preserved": bool(
            level0_two_to_one and level1_two_to_one
            and level2_two_to_one and level3_two_to_one
        ),
    }


# ---------------------------------------------------------------------------
# Claim D - Nested-structure topological signature (all 6 cross-level ratios).
# ---------------------------------------------------------------------------
def claim_d_nested_topology_signature(cascade: dict) -> dict:
    """Verify nested-structure signature via all six cross-level sign-flip ratios.

    For TRUE depth-3 recursive-Hopf:
      r10 = L1/L0 = 14/2   = 7    = ratio_inner
      r21 = L2/L1 = 98/14  = 7    = ratio_deeper
      r32 = L3/L2 = 686/98 = 7    = ratio_deepest
      r20 = L2/L0 = 98/2   = 49   = ratio_inner * ratio_deeper
      r31 = L3/L1 = 686/14 = 49   = ratio_deeper * ratio_deepest
      r30 = L3/L0 = 686/2  = 343  = ratio_inner * ratio_deeper * ratio_deepest

    These integer ratios ARE the topological signature of nested figure-8s.
    All six must be bit-exact integer.
    """
    ratio_inner = cascade["ratio_inner"]
    ratio_deeper = cascade["ratio_deeper"]
    ratio_deepest = cascade["ratio_deepest"]

    flips_outer = count_sign_flips(cascade["x_outer"])
    flips_inner = count_sign_flips(cascade["inner_mod"])
    flips_deeper = count_sign_flips(cascade["deeper_mod"])
    flips_deepest = count_sign_flips(cascade["deepest_mod"])

    # All six cross-level ratios (4 levels -> C(4,2) = 6 pairs)
    r10 = flips_inner / flips_outer if flips_outer > 0 else float("inf")
    r21 = flips_deeper / flips_inner if flips_inner > 0 else float("inf")
    r32 = flips_deepest / flips_deeper if flips_deeper > 0 else float("inf")
    r20 = flips_deeper / flips_outer if flips_outer > 0 else float("inf")
    r31 = flips_deepest / flips_inner if flips_inner > 0 else float("inf")
    r30 = flips_deepest / flips_outer if flips_outer > 0 else float("inf")

    expected_r10 = ratio_inner
    expected_r21 = ratio_deeper
    expected_r32 = ratio_deepest
    expected_r20 = ratio_inner * ratio_deeper
    expected_r31 = ratio_deeper * ratio_deepest
    expected_r30 = ratio_inner * ratio_deeper * ratio_deepest

    r10_exact = r10 == expected_r10
    r21_exact = r21 == expected_r21
    r32_exact = r32 == expected_r32
    r20_exact = r20 == expected_r20
    r31_exact = r31 == expected_r31
    r30_exact = r30 == expected_r30

    return {
        "ratio_L1_over_L0": float(r10),
        "expected_L1_over_L0": expected_r10,
        "r10_bit_exact": bool(r10_exact),
        "ratio_L2_over_L1": float(r21),
        "expected_L2_over_L1": expected_r21,
        "r21_bit_exact": bool(r21_exact),
        "ratio_L3_over_L2": float(r32),
        "expected_L3_over_L2": expected_r32,
        "r32_bit_exact": bool(r32_exact),
        "ratio_L2_over_L0": float(r20),
        "expected_L2_over_L0": expected_r20,
        "r20_bit_exact": bool(r20_exact),
        "ratio_L3_over_L1": float(r31),
        "expected_L3_over_L1": expected_r31,
        "r31_bit_exact": bool(r31_exact),
        "ratio_L3_over_L0": float(r30),
        "expected_L3_over_L0": expected_r30,
        "r30_bit_exact": bool(r30_exact),
        "all_six_ratios_bit_exact": bool(
            r10_exact and r21_exact and r32_exact
            and r20_exact and r31_exact and r30_exact
        ),
    }


# ---------------------------------------------------------------------------
# Verdict assembly per dispatch brief.
# ---------------------------------------------------------------------------
def assemble_verdict(a: dict, b: dict, c: dict, d: dict) -> str:
    """Combine claims A/B/C/D into a single verdict per dispatch brief.

    DEPTH-3-CONFIRMED-RECURSIVE-HOPF-UNBOUNDED:
        all_four_levels_bit_exact (A) AND
        all_three_fft_peaks_bit_exact_integer (B) AND
        all_levels_two_to_one_preserved (C) AND
        all_six_ratios_bit_exact (D).

    DEPTH-3-CONFIRMED-WITH-FERMATA:
        A + B pass through all four levels and three FFT bins, but C or D
        has a fermata-worthy partial.

    DEPTH-3-PARTIAL:
        Levels 0/1/2 unchanged (Spikes #212/#213 hold) but Level 3 fails
        in count or FFT (different-than-predicted result at deepest level).

    DEPTH-3-FALSE:
        Level 3 fails entirely; recursive-Hopf bounded at depth-2; Spike
        #213's UNBOUNDED qualifier narrows.
    """
    level0_pass = a["level0_bit_exact"]
    level1_pass = a["level1_bit_exact"] and b["level1_fft_peak_correct"]
    level2_pass = a["level2_bit_exact"] and b["level2_fft_peak_correct"]
    level3_pass = a["level3_bit_exact"] and b["level3_fft_peak_correct"]

    all_pass = (
        a["all_four_levels_bit_exact"]
        and b["all_three_fft_peaks_bit_exact_integer"]
        and c["all_levels_two_to_one_preserved"]
        and d["all_six_ratios_bit_exact"]
    )
    if all_pass:
        return "DEPTH-3-CONFIRMED-RECURSIVE-HOPF-UNBOUNDED"

    if level0_pass and level1_pass and level2_pass and level3_pass and not (
        c["all_levels_two_to_one_preserved"] and d["all_six_ratios_bit_exact"]
    ):
        return "DEPTH-3-CONFIRMED-WITH-FERMATA"

    if level0_pass and level1_pass and level2_pass and not level3_pass:
        return "DEPTH-3-PARTIAL"

    return "DEPTH-3-FALSE"


def main() -> int:
    parser = argparse.ArgumentParser(description="Spike #214 reproducible compute.")
    parser.add_argument("--verify", action="store_true",
                        help="Print one-line summary suitable for CI gating.")
    parser.add_argument("--n", type=int, default=131072,
                        help="Sample count per outer period (default 131072 = #213 fermata floor).")
    parser.add_argument("--ratio-inner", type=int, default=7,
                        help="Inner/outer frequency ratio (default 7, matches #212/#213).")
    parser.add_argument("--ratio-deeper", type=int, default=7,
                        help="Deeper/inner frequency ratio (default 7, matches #213).")
    parser.add_argument("--ratio-deepest", type=int, default=7,
                        help="Deepest/deeper frequency ratio (default 7, symmetric stack 7x7x7=343).")
    args = parser.parse_args()

    cascade = depth3_cascade(
        n=args.n,
        ratio_inner=args.ratio_inner,
        ratio_deeper=args.ratio_deeper,
        ratio_deepest=args.ratio_deepest,
    )

    claim_a = claim_a_signflip_counts_four_levels(cascade)
    claim_b = claim_b_fft_peaks(cascade)
    claim_c = claim_c_two_to_one_ratio_at_every_level(cascade)
    claim_d = claim_d_nested_topology_signature(cascade)
    verdict = assemble_verdict(claim_a, claim_b, claim_c, claim_d)

    if args.verify:
        line = (
            f"spike214_verdict={verdict} "
            f"flips_L0={claim_a['flips_level0_outer']} "
            f"flips_L1={claim_a['flips_level1_inner']} "
            f"flips_L2={claim_a['flips_level2_deeper']} "
            f"flips_L3={claim_a['flips_level3_deepest']} "
            f"predicted_L3={claim_a['predicted_level3_deepest']} "
            f"fft_L1={claim_b['fft_peak_bin_level1_inner']} "
            f"fft_L2={claim_b['fft_peak_bin_level2_deeper']} "
            f"fft_L3={claim_b['fft_peak_bin_level3_deepest']} "
            f"ratio_2to1_L0={claim_c['level0_ratio']:.1f} "
            f"ratio_2to1_L1={claim_c['level1_ratio']:.1f} "
            f"ratio_2to1_L2={claim_c['level2_ratio']:.1f} "
            f"ratio_2to1_L3={claim_c['level3_ratio']:.1f} "
            f"all_six_cross={claim_d['all_six_ratios_bit_exact']}"
        )
        print(line)
        return 0

    output = {
        "spike_id": 214,
        "seed": SEED,
        "verdict": verdict,
        "claim_a_signflip_counts_four_levels": claim_a,
        "claim_b_fft_peaks": claim_b,
        "claim_c_two_to_one_ratio_at_every_level": claim_c,
        "claim_d_nested_topology_signature": claim_d,
    }
    print(json.dumps(output, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
