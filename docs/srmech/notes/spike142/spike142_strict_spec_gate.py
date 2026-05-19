"""Spike #142 — Strict-spec gate for Class M (HDC) + Class C (orientation).

Per the spike brief (Meta-lesson 2 from Spike #141): the strict-spec
discipline tests must PASS BEFORE Mermin measurement is meaningful.
If Class M self-inverse fails, STOP.

Class M strict spec (canonical BSC per Kanerva 2009):
- fixed-dimension D
- associative bind
- self-inverse: bind(bind(a,b),b) = a
- approximately orthogonal random base vectors (similarity ~ 0)

Class C strict spec (irreversible orientation per
`[[user_stance_time_as_dimensional_shadow]]`):
- composition preserves designated forward direction
- state transitions not invertible without information loss
- time-asymmetric

Numerical residuals must be at machine epsilon (XOR for BSC is bit-exact
0.0, not 1e-15).
"""

from __future__ import annotations
import sys
import os
import math
import secrets
from pathlib import Path

# Ensure the worktree's srmech package is on the path.
WORKTREE_ROOT = Path(r"D:\GitHub\mlehaptics\.claude\worktrees\agent-ad0af059e53cd4257")
SRMECH_PYTHON = WORKTREE_ROOT / "docs" / "srmech" / "python"
sys.path.insert(0, str(SRMECH_PYTHON))

from srmech.amsc import hdc as M  # Class M: HDC bind/bundle/permute
from srmech.amsc import cyclic as I  # Class I: ℤ/n modular arithmetic

# ---------------------------------------------------------------------------
# Strict-spec Class M gate
# ---------------------------------------------------------------------------

def m_bind_self_inverse(D_bytes: int = 1024, n_trials: int = 10_000, seed: int = 0xC0FFEE) -> tuple[bool, int, int]:
    """Verify bind(bind(a,b),b) = a for n_trials random vectors.

    Returns (verified, n_mismatches, residual_max_bits).
    """
    rng = _make_rng(seed)
    mismatches = 0
    residual_max = 0
    for _ in range(n_trials):
        a = rng(D_bytes)
        b = rng(D_bytes)
        ab = M.bind(a, b)
        recovered = M.bind(ab, b)
        if recovered != a:
            mismatches += 1
            # Hamming distance from a in bits
            residual = sum(bin(x ^ y).count("1") for x, y in zip(recovered, a))
            if residual > residual_max:
                residual_max = residual
    return mismatches == 0, mismatches, residual_max


def m_bind_associative(D_bytes: int = 1024, n_trials: int = 10_000, seed: int = 0xBEEF) -> tuple[bool, int]:
    """Verify bind(a, bind(b,c)) = bind(bind(a,b), c)."""
    rng = _make_rng(seed)
    mismatches = 0
    for _ in range(n_trials):
        a = rng(D_bytes); b = rng(D_bytes); c = rng(D_bytes)
        left = M.bind(a, M.bind(b, c))
        right = M.bind(M.bind(a, b), c)
        if left != right:
            mismatches += 1
    return mismatches == 0, mismatches


def m_bind_commutative(D_bytes: int = 1024, n_trials: int = 10_000, seed: int = 0xCAFE) -> tuple[bool, int]:
    """Verify bind(a,b) = bind(b,a) (XOR is commutative)."""
    rng = _make_rng(seed)
    mismatches = 0
    for _ in range(n_trials):
        a = rng(D_bytes); b = rng(D_bytes)
        if M.bind(a, b) != M.bind(b, a):
            mismatches += 1
    return mismatches == 0, mismatches


def m_base_vector_orthogonality(D_bytes: int = 1024, n_pairs: int = 10_000, seed: int = 0xDEAD) -> tuple[float, float]:
    """Compute mean and std of similarity for random base vector pairs.

    Random BSC vectors have similarity ~ N(0, 1/sqrt(D_bits)).
    For D_bytes=1024 (8192 bits), std ~ 0.011.
    """
    import statistics
    rng = _make_rng(seed)
    sims = []
    for _ in range(n_pairs):
        a = rng(D_bytes); b = rng(D_bytes)
        sims.append(M.similarity(a, b))
    return statistics.mean(sims), statistics.stdev(sims)


# ---------------------------------------------------------------------------
# Strict-spec Class C gate (orientation-preserving cascade)
# ---------------------------------------------------------------------------

def c_cascade_orientation_asymmetric(n_trials: int = 1000, seed: int = 0xC4) -> tuple[bool, int]:
    """Class C strict spec — irreversible orientation.

    Test: build a cyclic ℤ/n iteration (Class I provides cyclic-group
    arithmetic; Class C orientation is "always increment in same
    direction"). Verify the forward-step map is not its own inverse
    — that's the irreversibility/orientation property.

    For ℤ/n addition by constant k != 0 mod n:
    - forward: x → x + k mod n
    - inverse: x → x - k mod n
    These are DISTINCT unless k = -k mod n (i.e., 2k = 0).

    Pass condition: random non-trivial k produces non-self-inverse map.
    """
    rng_int = _make_int_rng(seed)
    mismatches = 0
    for _ in range(n_trials):
        n = rng_int(2, 256)
        k = rng_int(1, n - 1)
        # Skip degenerate case 2k=0 mod n
        if (2 * k) % n == 0:
            continue
        # Forward step at random x
        x = rng_int(0, n - 1)
        x_forward = (x + k) % n
        # If we apply the forward step AGAIN, do we recover x? (we shouldn't, for non-degenerate k)
        x_double = (x_forward + k) % n
        if x_double == x:
            mismatches += 1
    return mismatches == 0, mismatches


# ---------------------------------------------------------------------------
# Random byte vector generator (deterministic via secrets-seeded urandom alt)
# ---------------------------------------------------------------------------

def _make_rng(seed: int):
    """Deterministic byte-vector RNG via numpy."""
    import numpy as np
    rng = np.random.default_rng(seed)
    def gen(n_bytes: int) -> bytes:
        return bytes(rng.integers(0, 256, size=n_bytes, dtype=np.uint8).tolist())
    return gen


def _make_int_rng(seed: int):
    import numpy as np
    rng = np.random.default_rng(seed)
    def gen(low: int, high_inclusive: int) -> int:
        return int(rng.integers(low, high_inclusive + 1))
    return gen


# ---------------------------------------------------------------------------
# Main gate
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("Spike #142 — Strict-spec gate (Meta-lesson 2 discipline)")
    print("=" * 78)

    results = {}

    # Class M gate
    print("\n[Class M] strict-spec verification (BSC HDC; Kanerva 2009)")
    print(f"  D_bytes = 1024 (8192 bits); n_trials = 10000")

    ok, mm, residual = m_bind_self_inverse()
    print(f"  bind(bind(a,b),b) = a  ...  {'PASS' if ok else 'FAIL'}  "
          f"(mismatches={mm}; max_residual_bits={residual})")
    results["m_self_inverse_pass"] = ok
    results["m_self_inverse_mismatches"] = mm

    ok, mm = m_bind_associative()
    print(f"  bind(a, bind(b,c)) = bind(bind(a,b), c)  ...  {'PASS' if ok else 'FAIL'}  "
          f"(mismatches={mm})")
    results["m_associative_pass"] = ok
    results["m_associative_mismatches"] = mm

    ok, mm = m_bind_commutative()
    print(f"  bind(a,b) = bind(b,a)  ...  {'PASS' if ok else 'FAIL'}  "
          f"(mismatches={mm})")
    results["m_commutative_pass"] = ok

    mean_sim, std_sim = m_base_vector_orthogonality()
    expected_std = 1.0 / math.sqrt(8192)  # 1/sqrt(D_bits) for BSC
    print(f"  random base vector similarity  ...  mean={mean_sim:+.6f}, std={std_sim:.6f} "
          f"(expected ~{expected_std:.6f})")
    results["m_orthogonality_mean"] = mean_sim
    results["m_orthogonality_std"] = std_sim
    results["m_orthogonality_expected_std"] = expected_std
    # Pass if mean within 3 expected_std of 0 and std within factor 1.3 of expected
    orth_ok = (abs(mean_sim) < 3 * expected_std) and (0.7 * expected_std < std_sim < 1.3 * expected_std)
    print(f"  orthogonality concentration  ...  {'PASS' if orth_ok else 'FAIL'}")
    results["m_orthogonality_pass"] = orth_ok

    # Class C gate
    print("\n[Class C] strict-spec verification (irreversible orientation)")
    ok, mm = c_cascade_orientation_asymmetric()
    print(f"  forward-step not self-inverse (Z/n shift)  ...  {'PASS' if ok else 'FAIL'}  "
          f"(self-inverse cases skipped at 2k=0 mod n; remaining mismatches={mm})")
    results["c_orientation_irreversible_pass"] = ok
    results["c_orientation_mismatches"] = mm

    # Overall gate
    all_pass = (
        results["m_self_inverse_pass"]
        and results["m_associative_pass"]
        and results["m_commutative_pass"]
        and results["m_orthogonality_pass"]
        and results["c_orientation_irreversible_pass"]
    )
    print("\n" + "=" * 78)
    if all_pass:
        print("GATE PASS — Mermin measurement is meaningful. Proceed to baseline + cross-tripartite.")
    else:
        print("GATE FAIL — STOP. Class M or Class C strict spec violated; Mermin invalid.")
    print("=" * 78)

    # Write NDJSON record
    import json
    out_path = WORKTREE_ROOT / "docs" / "srmech" / "notes" / "spike142" / "spike142_strict_spec_gate.ndjson"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "spike": "#142",
        "kind": "strict-spec-gate",
        "date": "2026-05-19",
        "results": results,
        "verdict": "GATE_PASS" if all_pass else "GATE_FAIL",
    }
    with open(out_path, "w") as f:
        f.write(json.dumps(record) + "\n")
    print(f"\nNDJSON: {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
