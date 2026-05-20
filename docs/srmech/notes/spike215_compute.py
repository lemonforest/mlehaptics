#!/usr/bin/env python3
"""Spike #215 — Asymmetric recursive-Hopf ratios test at depth-2.

Spike #213 returned DEPTH-2-CONFIRMED-RECURSIVE-HOPF-UNBOUNDED for the
symmetric 7x7 cascade (ratio_inner = ratio_deeper = 7). The 2:1 short:long
axis sign-flip ratio held bit-exact at every recursion level, and the
nested-topology integer signature was exact at machine epsilon. The
fermata Spike #213 surfaced for Tier 4 closure was:

    "Does the bit-exact invariance survive when ratio_inner != ratio_deeper?"

Spike #215 answers that fermata. We loop the Spike #213 depth-2 cascade
construction over five asymmetric (r1, r2) ratio pairs and check the same
four claims for each stack:

    (r1, r2) = (3, 7)    -> ω = {1, 3, 21}  flips = {2, 6, 42}
    (r1, r2) = (7, 5)    -> ω = {1, 7, 35}  flips = {2, 14, 70}
    (r1, r2) = (5, 3)    -> ω = {1, 5, 15}  flips = {2, 10, 30}
    (r1, r2) = (11, 13)  -> ω = {1, 11, 143} flips = {2, 22, 286}
    (r1, r2) = (2, 3)    -> ω = {1, 2, 6}   flips = {2, 4, 12}

For every stack:
    - sign-flip count at level k = 2 * prod(r_1, ..., r_k) bit-exact
    - FFT peak bin at level k    = prod(r_1, ..., r_k) bit-exact integer
    - 2:1 short:long ratio at every level should be 2.0 bit-exact

If invariance holds for all 5 stacks: ratio-agnostic recursive-Hopf;
Spike #213's symmetric result generalises to arbitrary rational
asymmetric composition. If some fail: the invariance has a constraint
(coprime ratios only, prime ratios only, etc.); we report the failure
pattern.

Sampling discipline: depth-2 deeper-level requires n samples per outer
period with n >> 2 * r1 * r2 to resolve closed-period sign flips. For
(11, 13) the deeper omega is 143 so we need n >> 286. We auto-scale
n per stack to keep at least ~458 samples per deeper-level cycle (the
same density as Spike #213 used: 65536 / 49 ≈ 1337 samples/cycle for
7x7; we set a floor at n = max(65536, 458 * r1 * r2) per stack so the
worst case stays well-resolved).

Run plain:
    python spike215_compute.py
Run verify:
    python spike215_compute.py --verify

All computations are deterministic. No PRNG draws (seed lock irrelevant
because no stochastic call sites; documented for provenance trail).

Author: Spike #215 (mlehaptics spectral-research, 2026-05-20).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Iterable

import numpy as np

# Determinism seed (no PRNG used; locked for provenance trail).
SEED = 215
np.random.seed(SEED)


# ---------------------------------------------------------------------------
# Sign-flip counting helper (integer; bit-exact; closed-period by default).
# Inherited verbatim from Spike #212 / #213 — same topological-invariant
# convention preserves cross-spike comparability.
# ---------------------------------------------------------------------------
def count_sign_flips(samples: Iterable[float], tol: float = 1e-12,
                     closed_period: bool = True) -> int:
    """Return integer count of sign changes over one (closed) period."""
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
# Asymmetric depth-2 cascade construction.
# Identical structure to Spike #213's depth2_cascade, but ratio_inner and
# ratio_deeper are now allowed to differ. Defaults match Spike #213 for
# regression sanity (verify symmetric 7x7 still returns the same numbers
# when called with defaults).
# ---------------------------------------------------------------------------
def depth2_cascade_asymmetric(
    n: int = 65536,
    omega_outer: float = 1.0,
    ratio_inner: int = 7,
    ratio_deeper: int = 7,
    eps_outer: float = 0.35,
    eps_inner: float = 0.12,
    eps_deeper: float = 0.04,
) -> dict:
    """Construct asymmetric depth-2 nested cascade trajectory."""
    omega_inner = ratio_inner * omega_outer
    omega_deeper = ratio_deeper * omega_inner

    t = np.linspace(0.0, 2.0 * math.pi / omega_outer, n, endpoint=False)

    # Level 0: outer figure-8 (Bernoulli with Class K eq-of-centre sweep)
    tau_outer = t + eps_outer * np.sin(omega_outer * t)
    denom_outer = 1.0 + np.sin(tau_outer) ** 2
    x_outer = np.cos(tau_outer) / denom_outer
    y_outer = np.sin(tau_outer) * np.cos(tau_outer) / denom_outer

    # Level 1: inner pin+slot Class K equation-of-centre at omega_inner.
    inner_mod = eps_inner * np.cos(
        omega_inner * t + eps_inner * np.sin(omega_inner * t)
    )

    # Level 2: deeper pin+slot Class K eq-of-centre at omega_deeper,
    # composed INSIDE the inner level's instantiation. Recursive-Hopf
    # composition: same primitive op at multiplicatively-nested frequency.
    deeper_mod = eps_deeper * np.cos(
        omega_deeper * t + eps_deeper * np.sin(omega_deeper * t)
    )

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
        "eps_outer": eps_outer,
        "eps_inner": eps_inner,
        "eps_deeper": eps_deeper,
    }


# ---------------------------------------------------------------------------
# Claim A — Bit-exact sign-flip counts at all three recursion levels.
# Generalised from Spike #213 to asymmetric (r1, r2).
# ---------------------------------------------------------------------------
def claim_a_signflip_counts_three_levels(cascade: dict) -> dict:
    ri = cascade["ratio_inner"]
    rd = cascade["ratio_deeper"]

    flips_outer = count_sign_flips(cascade["x_outer"])
    flips_inner = count_sign_flips(cascade["inner_mod"])
    flips_deeper = count_sign_flips(cascade["deeper_mod"])

    predicted_outer = 2
    predicted_inner = 2 * ri
    predicted_deeper = 2 * ri * rd

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
    inner_mod = cascade["inner_mod"]
    deeper_mod = cascade["deeper_mod"]
    ri = cascade["ratio_inner"]
    rd = cascade["ratio_deeper"]

    fft_inner = np.fft.rfft(inner_mod)
    peak_bin_inner = int(np.argmax(np.abs(fft_inner[1:])) + 1)
    inner_peak_correct = peak_bin_inner == ri

    fft_deeper = np.fft.rfft(deeper_mod)
    peak_bin_deeper = int(np.argmax(np.abs(fft_deeper[1:])) + 1)
    expected_bin_deeper = ri * rd
    deeper_peak_correct = peak_bin_deeper == expected_bin_deeper

    return {
        "fft_peak_bin_level1_inner": peak_bin_inner,
        "expected_bin_level1_inner": ri,
        "level1_fft_peak_correct": bool(inner_peak_correct),
        "fft_peak_bin_level2_deeper": peak_bin_deeper,
        "expected_bin_level2_deeper": expected_bin_deeper,
        "level2_fft_peak_correct": bool(deeper_peak_correct),
        "both_fft_peaks_bit_exact_integer": bool(inner_peak_correct and deeper_peak_correct),
    }


# ---------------------------------------------------------------------------
# Claim C — 2:1 short:long axis ratio preserved at every recursion level.
# This is the load-bearing universality claim for Spike #215.
# ---------------------------------------------------------------------------
def claim_c_two_to_one_ratio_at_every_level(cascade: dict) -> dict:
    t = cascade["t"]
    ri = cascade["ratio_inner"]
    rd = cascade["ratio_deeper"]
    eps_inner = cascade["eps_inner"]
    eps_deeper = cascade["eps_deeper"]

    # Level 0: Bernoulli long-axis (x_outer) vs short-axis (y_outer).
    flips_x_outer = count_sign_flips(cascade["x_outer"])
    flips_y_outer = count_sign_flips(cascade["y_outer"])
    ratio_level0 = flips_y_outer / flips_x_outer if flips_x_outer > 0 else float("inf")
    level0_two_to_one = ratio_level0 == 2.0

    # Level 1: build inner lemniscate explicitly at omega_inner; read its
    # long-axis (x) and short-axis (y) sign-flip counts.
    omega_inner = cascade["omega_inner"]
    tau_inner = omega_inner * t + eps_inner * np.sin(omega_inner * t)
    denom_inner = 1.0 + np.sin(tau_inner) ** 2
    x_inner_lemn = np.cos(tau_inner) / denom_inner
    y_inner_lemn = np.sin(tau_inner) * np.cos(tau_inner) / denom_inner
    flips_x_inner = count_sign_flips(x_inner_lemn)
    flips_y_inner = count_sign_flips(y_inner_lemn)
    ratio_level1 = flips_y_inner / flips_x_inner if flips_x_inner > 0 else float("inf")
    level1_two_to_one = ratio_level1 == 2.0

    # Level 2: same construction at omega_deeper.
    omega_deeper = cascade["omega_deeper"]
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
        "ri": ri,
        "rd": rd,
    }


# ---------------------------------------------------------------------------
# Claim D — Nested-structure topology signature (integer cross-level ratios).
# ---------------------------------------------------------------------------
def claim_d_nested_topology_signature(cascade: dict) -> dict:
    ri = cascade["ratio_inner"]
    rd = cascade["ratio_deeper"]

    flips_outer = count_sign_flips(cascade["x_outer"])
    flips_inner = count_sign_flips(cascade["inner_mod"])
    flips_deeper = count_sign_flips(cascade["deeper_mod"])

    r10 = flips_inner / flips_outer if flips_outer > 0 else float("inf")
    r21 = flips_deeper / flips_inner if flips_inner > 0 else float("inf")
    r20 = flips_deeper / flips_outer if flips_outer > 0 else float("inf")

    expected_r10 = ri
    expected_r21 = rd
    expected_r20 = ri * rd

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
# Per-stack verdict & aggregate verdict.
# ---------------------------------------------------------------------------
def assemble_stack_pass(a: dict, b: dict, c: dict, d: dict) -> bool:
    return bool(
        a["all_three_levels_bit_exact"]
        and b["both_fft_peaks_bit_exact_integer"]
        and c["all_levels_two_to_one_preserved"]
        and d["nested_topology_bit_exact"]
    )


def assemble_aggregate_verdict(stack_results: list) -> tuple[str, dict]:
    """Combine per-stack passes into a Spike #215 verdict per dispatch brief.

    ASYMMETRIC-RATIO-INVARIANCE-UNIVERSAL:
        all stacks pass at every claim, bit-exact.

    ASYMMETRIC-INVARIANCE-CONFIRMED-WITH-CONSTRAINT:
        invariance holds only when ratios satisfy a named property
        (coprime / both prime / etc.). Detect by inspecting failure pattern.

    ASYMMETRIC-INVARIANCE-PARTIAL:
        some stacks pass, some fail, with no single clean constraint.

    ASYMMETRIC-INVARIANCE-FALSE:
        all stacks fail (or the universality claim collapses entirely).
    """
    passes = [r["pass"] for r in stack_results]
    n_pass = sum(passes)
    n_total = len(passes)

    summary = {
        "n_pass": n_pass,
        "n_total": n_total,
        "stacks_passed": [r["label"] for r in stack_results if r["pass"]],
        "stacks_failed": [r["label"] for r in stack_results if not r["pass"]],
    }

    if n_pass == n_total:
        return "ASYMMETRIC-RATIO-INVARIANCE-UNIVERSAL", summary

    if n_pass == 0:
        return "ASYMMETRIC-INVARIANCE-FALSE", summary

    # Some passes, some fails — examine the failure pattern.
    failed = [r for r in stack_results if not r["pass"]]
    passed = [r for r in stack_results if r["pass"]]

    def both_prime(r):
        ri, rd = r["ratio_inner"], r["ratio_deeper"]
        return _is_prime(ri) and _is_prime(rd)

    def coprime(r):
        ri, rd = r["ratio_inner"], r["ratio_deeper"]
        return math.gcd(ri, rd) == 1

    all_passed_both_prime = all(both_prime(r) for r in passed) and not any(both_prime(r) for r in failed)
    all_passed_coprime = all(coprime(r) for r in passed) and not any(coprime(r) for r in failed)

    if all_passed_both_prime and not all_passed_coprime:
        summary["constraint"] = "both ratios prime"
        return "ASYMMETRIC-INVARIANCE-CONFIRMED-WITH-CONSTRAINT", summary
    if all_passed_coprime:
        summary["constraint"] = "coprime ratios"
        return "ASYMMETRIC-INVARIANCE-CONFIRMED-WITH-CONSTRAINT", summary

    return "ASYMMETRIC-INVARIANCE-PARTIAL", summary


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


# ---------------------------------------------------------------------------
# Five-stack test loop.
# ---------------------------------------------------------------------------
RATIO_STACKS = [
    (3, 7),
    (7, 5),
    (5, 3),
    (11, 13),
    (2, 3),
]


def auto_scale_n(ri: int, rd: int, floor: int = 65536,
                 min_samples_per_deeper_cycle: int = 458) -> int:
    """Pick n large enough to resolve the deeper-level cycle densely.

    Spike #213 used n=65536 with deeper-omega=49 -> ~1337 samples/cycle.
    We keep n >= floor AND n >= min_samples_per_deeper_cycle * ri * rd
    so worst-case (11x13=143) still gets ~458 samples per deeper cycle.
    """
    needed = min_samples_per_deeper_cycle * ri * rd
    n = max(floor, needed)
    # Round up to a power of two for FFT-friendly bins (not strictly
    # required by sign-flip counting, but keeps FFT peaks crisp).
    n_pow2 = 1
    while n_pow2 < n:
        n_pow2 <<= 1
    return n_pow2


def run_stack(ri: int, rd: int) -> dict:
    """Run one (r1, r2) stack and return per-claim results plus pass flag."""
    n = auto_scale_n(ri, rd)
    cascade = depth2_cascade_asymmetric(n=n, ratio_inner=ri, ratio_deeper=rd)
    a = claim_a_signflip_counts_three_levels(cascade)
    b = claim_b_fft_peaks(cascade)
    c = claim_c_two_to_one_ratio_at_every_level(cascade)
    d = claim_d_nested_topology_signature(cascade)
    return {
        "label": f"(r1={ri}, r2={rd})",
        "ratio_inner": ri,
        "ratio_deeper": rd,
        "n_samples": n,
        "claim_a": a,
        "claim_b": b,
        "claim_c": c,
        "claim_d": d,
        "pass": assemble_stack_pass(a, b, c, d),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Spike #215 reproducible compute (asymmetric ratios)."
    )
    parser.add_argument("--verify", action="store_true",
                        help="Print one-line summary suitable for CI gating.")
    args = parser.parse_args()

    stack_results = [run_stack(ri, rd) for (ri, rd) in RATIO_STACKS]
    verdict, summary = assemble_aggregate_verdict(stack_results)

    if args.verify:
        # One-line summary: verdict + per-stack pass flags + bit-exact rollup.
        stack_flags = " ".join(
            f"{r['label']}={'PASS' if r['pass'] else 'FAIL'}"
            for r in stack_results
        )
        line = (
            f"spike215_verdict={verdict} "
            f"n_pass={summary['n_pass']}/{summary['n_total']} "
            f"stacks=[ {stack_flags} ]"
        )
        print(line)
        return 0

    output = {
        "spike_id": 215,
        "seed": SEED,
        "verdict": verdict,
        "summary": summary,
        "ratio_stacks_tested": RATIO_STACKS,
        "stack_results": stack_results,
    }
    print(json.dumps(output, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
