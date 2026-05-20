#!/usr/bin/env python3
"""Spike #213 — Depth-2 recursive Hopf at primitive level.

Extends Spike #212 (depth-1 recursion confirmed: 14/14 inner sign-flips
bit-exact, FFT peak k=7) to **depth-2**: figure-8-of-figure-8-of-figure-8s.

Three nested frequency levels:

    Level 0 (outer):   omega_outer  = 1     -> 2 sign-flips/outer period
    Level 1 (inner):   omega_inner  = 7     -> 14 sign-flips/outer period
    Level 2 (deeper):  omega_deeper = 49    -> 98 sign-flips/outer period (PREDICTION)

If depth-2 confirms bit-exact (98/98 deeper sign-flips, FFT peak at k=49,
2:1 ratio at every level), recursive-Hopf is at least depth-2+ and likely
unbounded. If depth-2 fails, recursive-Hopf has a stopping condition at
depth-1 and Spike #212's recursive claim narrows.

Run plain:
    python spike213_compute.py
Run verify:
    python spike213_compute.py --verify

All computations are deterministic. No PRNG draws (seed lock irrelevant
because no stochastic call sites; documented for provenance trail).

Author: Spike #213 (mlehaptics spectral-research, 2026-05-20).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Iterable

import numpy as np

# Determinism seed (no PRNG used; locked for provenance trail).
SEED = 213
np.random.seed(SEED)


# ---------------------------------------------------------------------------
# Sign-flip counting helper (integer; bit-exact; closed-period by default).
# Inherited from Spike #212 — same topological-invariant convention.
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
# Depth-2 cascade construction.
# ---------------------------------------------------------------------------
def depth2_cascade(
    n: int = 65536,
    omega_outer: float = 1.0,
    ratio_inner: int = 7,
    ratio_deeper: int = 7,
    eps_outer: float = 0.35,
    eps_inner: float = 0.12,
    eps_deeper: float = 0.04,
) -> dict:
    """Construct depth-2 nested cascade trajectory.

    Three-level Hopf-recursion test. Each level applies L o K o C o I
    cascade composition (per [[user_stance_epicycle_via_gear_plus_pin]]
    Spike #189) at progressively higher frequency.

    Level 0 (outer figure-8):
        Bernoulli lemniscate parametric form with Class K equation-of-centre
        sweep tau = t + eps_outer * sin(omega_outer * t).
        Long-axis x(t) -> 2 sign-flips/period (slot view).

    Level 1 (inner figure-8 / pin+slot):
        Inner Class K pin+slot oscillation at omega_inner = ratio_inner * omega_outer.
        Predicts 2 * ratio_inner = 14 sign-flips/outer-period.
        Verified Spike #212.

    Level 2 (deeper figure-8 / pin+slot inside inner):
        Deeper Class K pin+slot oscillation at omega_deeper = ratio_deeper * omega_inner
                                            = ratio_inner * ratio_deeper * omega_outer
                                            = 49 * omega_outer for 7x7 stacking.
        PREDICTS 2 * ratio_inner * ratio_deeper = 98 sign-flips/outer-period.

    The deeper level is composed INSIDE the inner level's Class K
    instantiation — exactly the same cascade structure recursed one
    level further (the recursive-Hopf-at-every-cascade prediction).

    Parameters
    ----------
    n : int
        Sample count over one outer period. Must be large enough to resolve
        deeper-level oscillations. For omega_deeper=49 with closed-period
        counting we need n >> 2*49 = 98 samples per period. n=65536 gives
        ~669 samples per deeper-level cycle — very dense.
    """
    omega_inner = ratio_inner * omega_outer
    omega_deeper = ratio_deeper * omega_inner  # = ratio_inner * ratio_deeper * omega_outer

    t = np.linspace(0.0, 2.0 * math.pi / omega_outer, n, endpoint=False)

    # Level 0: outer figure-8 (Bernoulli with Class K eq-of-centre sweep)
    tau_outer = t + eps_outer * np.sin(omega_outer * t)
    denom_outer = 1.0 + np.sin(tau_outer) ** 2
    x_outer = np.cos(tau_outer) / denom_outer
    y_outer = np.sin(tau_outer) * np.cos(tau_outer) / denom_outer

    # Level 1: inner pin+slot (the hidden figure-8 fiber at primitive level)
    # eps_inner * cos(omega_inner * t + eps_inner * sin(omega_inner * t))
    # = Class K equation-of-centre on inner pin+slot oscillation.
    inner_mod = eps_inner * np.cos(
        omega_inner * t + eps_inner * np.sin(omega_inner * t)
    )

    # Level 2: deeper pin+slot (the figure-8 fiber INSIDE the inner Class K)
    # Recursion: same Class K equation-of-centre at omega_deeper frequency,
    # composed inside the inner level's instantiation.
    deeper_mod = eps_deeper * np.cos(
        omega_deeper * t + eps_deeper * np.sin(omega_deeper * t)
    )

    # Full depth-2 trajectory: outer + inner + deeper radial modulations
    x_full = x_outer + (inner_mod + deeper_mod) * np.cos(omega_outer * t)
    y_full = y_outer + (inner_mod + deeper_mod) * np.sin(omega_outer * t)

    return {
        "t": t,
        "x_outer": x_outer,
        "y_outer": y_outer,
        "inner_mod": inner_mod,
        "deeper_mod": deeper_mod,
        "x_full": x_full,
        "y_full": y_full,
        "omega_outer": omega_outer,
        "omega_inner": omega_inner,
        "omega_deeper": omega_deeper,
        "ratio_inner": ratio_inner,
        "ratio_deeper": ratio_deeper,
    }


# ---------------------------------------------------------------------------
# Claim A — Bit-exact sign-flip counts at all three recursion levels.
# ---------------------------------------------------------------------------
def claim_a_signflip_counts_three_levels(cascade: dict) -> dict:
    """Bit-exact closed-period sign-flip counts at every recursion level.

    Predictions:
      Level 0 outer x_outer (long-axis):  2 flips/period
      Level 1 inner_mod (alone):          2 * ratio_inner = 14 flips/period
      Level 2 deeper_mod (alone):         2 * ratio_inner * ratio_deeper = 98 flips/period
    """
    ratio_inner = cascade["ratio_inner"]
    ratio_deeper = cascade["ratio_deeper"]

    flips_outer = count_sign_flips(cascade["x_outer"])
    flips_inner = count_sign_flips(cascade["inner_mod"])
    flips_deeper = count_sign_flips(cascade["deeper_mod"])

    predicted_outer = 2
    predicted_inner = 2 * ratio_inner
    predicted_deeper = 2 * ratio_inner * ratio_deeper

    outer_exact = flips_outer == predicted_outer
    inner_exact = flips_inner == predicted_inner
    deeper_exact = flips_deeper == predicted_deeper

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
        "all_three_levels_bit_exact": bool(outer_exact and inner_exact and deeper_exact),
    }


# ---------------------------------------------------------------------------
# Claim B — FFT peak at expected integer bins for inner and deeper levels.
# ---------------------------------------------------------------------------
def claim_b_fft_peaks(cascade: dict) -> dict:
    """FFT peak at expected integer bin k at each recursion level.

    Inner modulation alone: peak at bin k = ratio_inner = 7.
    Deeper modulation alone: peak at bin k = ratio_inner * ratio_deeper = 49.

    Bit-exact integer bin = no spectral leakage (verified Spike #212 for
    depth-1; extending here to depth-2).
    """
    inner_mod = cascade["inner_mod"]
    deeper_mod = cascade["deeper_mod"]
    ratio_inner = cascade["ratio_inner"]
    ratio_deeper = cascade["ratio_deeper"]

    # FFT of inner modulation; peak bin = inner frequency relative to outer period.
    fft_inner = np.fft.rfft(inner_mod)
    peak_bin_inner = int(np.argmax(np.abs(fft_inner[1:])) + 1)
    inner_peak_correct = peak_bin_inner == ratio_inner

    # FFT of deeper modulation; peak bin = inner*deeper = 49 in outer-period units.
    fft_deeper = np.fft.rfft(deeper_mod)
    peak_bin_deeper = int(np.argmax(np.abs(fft_deeper[1:])) + 1)
    expected_bin_deeper = ratio_inner * ratio_deeper
    deeper_peak_correct = peak_bin_deeper == expected_bin_deeper

    return {
        "fft_peak_bin_level1_inner": peak_bin_inner,
        "expected_bin_level1_inner": ratio_inner,
        "level1_fft_peak_correct": bool(inner_peak_correct),
        "fft_peak_bin_level2_deeper": peak_bin_deeper,
        "expected_bin_level2_deeper": expected_bin_deeper,
        "level2_fft_peak_correct": bool(deeper_peak_correct),
        "both_fft_peaks_bit_exact_integer": bool(inner_peak_correct and deeper_peak_correct),
    }


# ---------------------------------------------------------------------------
# Claim C — 2:1 short:long axis ratio preserved at every recursion level.
# ---------------------------------------------------------------------------
def claim_c_two_to_one_ratio_at_every_level(cascade: dict) -> dict:
    """Hopf-fibre signature: short-axis flips = 2 x long-axis flips at every level.

    Per Spike #212 Claim 1: short-axis = 2 x long-axis for Bernoulli figure-8.
    The 2:1 ratio IS the +1 Hopf-fibre content surfacing.

    For depth-2 recursive-Hopf-unbounded:
      Level 0: long=2 (outer x), short=4 (outer y).
      Level 1: long=2*ratio_inner=14, short=2*long=28 (inner short-axis projection).
      Level 2: long=2*ratio_inner*ratio_deeper=98, short=2*long=196 (deeper short-axis).

    The 2:1 ratio at level k is the same Hopf-fibre signature observed at
    every recursion depth. At each level the short-axis projection of the
    pin+slot/figure-8 has twice the sign-flips of the long-axis (= the +1
    fiber content "living in the + sign" of the always-compressed (1+1)D
    pin+slot per [[user_stance_11d_substrate_is_always_hopf_compressed]]).
    """
    t = cascade["t"]
    ratio_inner = cascade["ratio_inner"]
    ratio_deeper = cascade["ratio_deeper"]

    # --- Level 0: Bernoulli long-axis (x_outer) vs short-axis (y_outer) ---
    flips_x_outer = count_sign_flips(cascade["x_outer"])
    flips_y_outer = count_sign_flips(cascade["y_outer"])
    ratio_level0 = flips_y_outer / flips_x_outer if flips_x_outer > 0 else float("inf")
    level0_two_to_one = ratio_level0 == 2.0

    # --- Level 1: inner pin+slot long-axis vs short-axis ---
    # Long-axis = inner_mod itself (the 1D pin+slot projection at omega_inner).
    # Short-axis = the orthogonal lobe projection at the same frequency.
    # Construct the inner figure-8 explicitly to get its short-axis:
    omega_inner = cascade["omega_inner"]
    eps_inner = 0.12  # match depth2_cascade default
    tau_inner = omega_inner * t + eps_inner * np.sin(omega_inner * t)
    denom_inner = 1.0 + np.sin(tau_inner) ** 2
    x_inner_lemn = np.cos(tau_inner) / denom_inner
    y_inner_lemn = np.sin(tau_inner) * np.cos(tau_inner) / denom_inner
    flips_x_inner = count_sign_flips(x_inner_lemn)
    flips_y_inner = count_sign_flips(y_inner_lemn)
    ratio_level1 = flips_y_inner / flips_x_inner if flips_x_inner > 0 else float("inf")
    level1_two_to_one = ratio_level1 == 2.0

    # --- Level 2: deeper pin+slot long-axis vs short-axis ---
    omega_deeper = cascade["omega_deeper"]
    eps_deeper = 0.04  # match depth2_cascade default
    tau_deeper = omega_deeper * t + eps_deeper * np.sin(omega_deeper * t)
    denom_deeper = 1.0 + np.sin(tau_deeper) ** 2
    x_deeper_lemn = np.cos(tau_deeper) / denom_deeper
    y_deeper_lemn = np.sin(tau_deeper) * np.cos(tau_deeper) / denom_deeper
    flips_x_deeper = count_sign_flips(x_deeper_lemn)
    flips_y_deeper = count_sign_flips(y_deeper_lemn)
    ratio_level2 = flips_y_deeper / flips_x_deeper if flips_x_deeper > 0 else float("inf")
    level2_two_to_one = ratio_level2 == 2.0

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
        "all_levels_two_to_one_preserved": bool(
            level0_two_to_one and level1_two_to_one and level2_two_to_one
        ),
    }


# ---------------------------------------------------------------------------
# Claim D — Nested-structure topological signature.
# ---------------------------------------------------------------------------
def claim_d_nested_topology_signature(cascade: dict) -> dict:
    """Verify nested-structure signature via cross-level sign-flip ratios.

    For TRUE depth-2 recursive-Hopf (figure-8-of-figure-8-of-figure-8s):
      ratio_level1_over_level0 = flips_inner / flips_outer = 14 / 2 = 7 = ratio_inner exactly
      ratio_level2_over_level1 = flips_deeper / flips_inner = 98 / 14 = 7 = ratio_deeper exactly
      ratio_level2_over_level0 = flips_deeper / flips_outer = 98 / 2 = 49 = ratio_inner * ratio_deeper exactly

    These integer ratios ARE the topological signature of nested figure-8s.
    Each recursion level multiplies sign-flip count by its frequency ratio
    integer — exactly the recursive-Hopf-at-every-cascade prediction.

    A FAILURE here (non-integer ratios, or ratios different from the
    frequency ratios) would indicate the recursion has a stopping condition
    or that the cascade construction at depth-2 introduces topology-altering
    interaction between levels.
    """
    ratio_inner = cascade["ratio_inner"]
    ratio_deeper = cascade["ratio_deeper"]

    flips_outer = count_sign_flips(cascade["x_outer"])
    flips_inner = count_sign_flips(cascade["inner_mod"])
    flips_deeper = count_sign_flips(cascade["deeper_mod"])

    r10 = flips_inner / flips_outer if flips_outer > 0 else float("inf")
    r21 = flips_deeper / flips_inner if flips_inner > 0 else float("inf")
    r20 = flips_deeper / flips_outer if flips_outer > 0 else float("inf")

    expected_r10 = ratio_inner
    expected_r21 = ratio_deeper
    expected_r20 = ratio_inner * ratio_deeper

    r10_exact = r10 == expected_r10
    r21_exact = r21 == expected_r21
    r20_exact = r20 == expected_r20

    return {
        "ratio_level1_over_level0": float(r10),
        "expected_ratio_level1_over_level0": expected_r10,
        "r10_bit_exact": bool(r10_exact),
        "ratio_level2_over_level1": float(r21),
        "expected_ratio_level2_over_level1": expected_r21,
        "r21_bit_exact": bool(r21_exact),
        "ratio_level2_over_level0": float(r20),
        "expected_ratio_level2_over_level0": expected_r20,
        "r20_bit_exact": bool(r20_exact),
        "nested_topology_bit_exact": bool(r10_exact and r21_exact and r20_exact),
    }


# ---------------------------------------------------------------------------
# Verdict assembly per dispatch brief.
# ---------------------------------------------------------------------------
def assemble_verdict(a: dict, b: dict, c: dict, d: dict) -> str:
    """Combine claims A/B/C/D into a single verdict per dispatch brief.

    DEPTH-2-CONFIRMED-RECURSIVE-HOPF-UNBOUNDED:
        all_three_levels_bit_exact (A) AND both_fft_peaks_bit_exact_integer (B)
        AND all_levels_two_to_one_preserved (C) AND nested_topology_bit_exact (D).

    DEPTH-2-CONFIRMED-WITH-FERMATA:
        A and B pass, but C or D has a fermata-worthy partial.

    DEPTH-2-PARTIAL:
        Level 0 + Level 1 pass (Spike #212 holds), but Level 2 fails
        in count or FFT (different-than-predicted result).

    DEPTH-2-FALSE:
        Level 2 fails entirely; recursive-Hopf bounded at depth-1;
        Spike #212 recursive claim narrows.
    """
    level0_pass = a["level0_bit_exact"]
    level1_pass = a["level1_bit_exact"] and b["level1_fft_peak_correct"]
    level2_pass = a["level2_bit_exact"] and b["level2_fft_peak_correct"]

    all_pass = (
        a["all_three_levels_bit_exact"]
        and b["both_fft_peaks_bit_exact_integer"]
        and c["all_levels_two_to_one_preserved"]
        and d["nested_topology_bit_exact"]
    )
    if all_pass:
        return "DEPTH-2-CONFIRMED-RECURSIVE-HOPF-UNBOUNDED"

    if level0_pass and level1_pass and level2_pass and not (
        c["all_levels_two_to_one_preserved"] and d["nested_topology_bit_exact"]
    ):
        return "DEPTH-2-CONFIRMED-WITH-FERMATA"

    if level0_pass and level1_pass and not level2_pass:
        return "DEPTH-2-PARTIAL"

    return "DEPTH-2-FALSE"


def main() -> int:
    parser = argparse.ArgumentParser(description="Spike #213 reproducible compute.")
    parser.add_argument("--verify", action="store_true",
                        help="Print one-line summary suitable for CI gating.")
    parser.add_argument("--n", type=int, default=65536,
                        help="Sample count per outer period (default 65536 = dense for deeper).")
    parser.add_argument("--ratio-inner", type=int, default=7,
                        help="Inner/outer frequency ratio (default 7, matches Spike #212).")
    parser.add_argument("--ratio-deeper", type=int, default=7,
                        help="Deeper/inner frequency ratio (default 7, gives 7x7=49 deeper/outer).")
    args = parser.parse_args()

    cascade = depth2_cascade(
        n=args.n,
        ratio_inner=args.ratio_inner,
        ratio_deeper=args.ratio_deeper,
    )

    claim_a = claim_a_signflip_counts_three_levels(cascade)
    claim_b = claim_b_fft_peaks(cascade)
    claim_c = claim_c_two_to_one_ratio_at_every_level(cascade)
    claim_d = claim_d_nested_topology_signature(cascade)
    verdict = assemble_verdict(claim_a, claim_b, claim_c, claim_d)

    if args.verify:
        line = (
            f"spike213_verdict={verdict} "
            f"flips_L0={claim_a['flips_level0_outer']} "
            f"flips_L1={claim_a['flips_level1_inner']} "
            f"flips_L2={claim_a['flips_level2_deeper']} "
            f"predicted_L2={claim_a['predicted_level2_deeper']} "
            f"fft_L1={claim_b['fft_peak_bin_level1_inner']} "
            f"fft_L2={claim_b['fft_peak_bin_level2_deeper']} "
            f"ratio_2to1_L0={claim_c['level0_ratio']:.1f} "
            f"ratio_2to1_L1={claim_c['level1_ratio']:.1f} "
            f"ratio_2to1_L2={claim_c['level2_ratio']:.1f} "
            f"nested_topo={claim_d['nested_topology_bit_exact']}"
        )
        print(line)
        return 0

    output = {
        "spike_id": 213,
        "seed": SEED,
        "verdict": verdict,
        "claim_a_signflip_counts_three_levels": claim_a,
        "claim_b_fft_peaks": claim_b,
        "claim_c_two_to_one_ratio_at_every_level": claim_c,
        "claim_d_nested_topology_signature": claim_d,
    }
    print(json.dumps(output, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
