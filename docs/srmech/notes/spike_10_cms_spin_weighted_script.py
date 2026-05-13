"""Spike #10 — CMS Casimir identity extended to spin-weighted modes (2026-05-12).

Follow-up to Spike #9 Part C (PR #356), which established that Castro-
Maloney-Strominger 2010 (arXiv:1004.0996) hidden conformal symmetry of
low-frequency scalar Kerr gives the closed-form Casimir identity

    C_L + C_R = 2·λ_S²(ℓ)            [scalar; h_L = h_R = ℓ + 1]

This spike extends the analysis to spin-weighted modes (s ∈ {0, 1/2, 1, 2}),
combining Spike #9 Part A's spin-universality of the Hopf gap with Part C's
non-compact-hidden-symmetry framework. The LIGO/Virgo observational target
is the s = 2 case (gravitational quasinormal modes of merging black holes).

CONVENTION CAVEAT (load-bearing for honest reporting). The conformal-weight
assignment for spin-weighted CMS is documented across multiple sources with
slightly different conventions:

  Convention SCALAR (CMS 2010):  h_L = h_R = ℓ + 1  for s = 0.

  Convention SPIN-SHIFT (most common in the Kerr/CFT correspondence
  literature; e.g. Bredberg-Hartman-Song-Strominger 2010 + BCC 2009 §4.4
  review of low-frequency Kerr):

      h_L = ℓ + 1 − s
      h_R = ℓ + 1 + s

  This convention reduces to the CMS-scalar case at s = 0 and produces
  a symmetric spin-shift in the conformal weights — consistent with the
  Teukolsky master variable's spin-raising / spin-lowering structure.

  Convention HALF-SHIFT (alternate from Maldacena-Strominger 1997 +
  some Kerr/CFT works treating spin via the Frolov-Thorne thermal state):

      h_L = ℓ + 1 − s/2
      h_R = ℓ + 1 + s/2

Both reduce to scalar correctly. We compute BOTH so the structural pattern
is visible regardless of which convention is "the" right one for direct
LIGO comparison. Per the project's Gemini-CLI-taint discipline: convention
ambiguity flagged honestly; algebra is convention-agnostic.

WHAT THE SPIKE COMPUTES

1. Symbolic CMS Casimir sum C_L + C_R in both conventions, for s ∈ {0, 1/2, 1, 2}
2. The structural identity C_L + C_R − 2·λ_S²(ℓ, s) — should be a closed-form
   function of (ℓ, s); ideally simple (constant in ℓ, polynomial in s).
3. The LIGO-targeted s = 2 case: explicit closed-form identity.
4. Comparison with Spike #9 Part C scalar result (sanity check at s = 0).

Reproduce: `python -X utf8 docs/srmech/notes/spike_10_cms_spin_weighted_script.py`
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import sympy as sp
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "spike-10-cms-spin-weighted-per-test-2026-05-12.ndjson"
PLOT_FILE = OUT_DIR / "spike-10-cms-spin-weighted-2026-05-12.png"


# ── Symbolic setup ──────────────────────────────────────────────────────

ell, s = sp.symbols("ell s", real=True)

# Spin-weighted S² Laplacian eigenvalue (Goldberg-MacFarlane-Newman-
# Penrose-Spirit-Sudarshan 1967 convention; matches Spike #9 Part A):
#   λ_S²(ℓ, s) = ℓ(ℓ+1) − s²
lam_s2 = ell * (ell + 1) - s**2


def casimir(h_expr: sp.Expr) -> sp.Expr:
    """SL(2, R) Casimir: C = h(h − 1)."""
    return sp.expand(h_expr * (h_expr - 1))


# ── Convention SPIN-SHIFT ───────────────────────────────────────────────

h_L_shift = ell + 1 - s
h_R_shift = ell + 1 + s

C_L_shift = casimir(h_L_shift)
C_R_shift = casimir(h_R_shift)
sum_shift = sp.expand(C_L_shift + C_R_shift)
identity_shift = sp.expand(sum_shift - 2 * lam_s2)


# ── Convention HALF-SHIFT ───────────────────────────────────────────────

h_L_half = ell + 1 - s / 2
h_R_half = ell + 1 + s / 2

C_L_half = casimir(h_L_half)
C_R_half = casimir(h_R_half)
sum_half = sp.expand(C_L_half + C_R_half)
identity_half = sp.expand(sum_half - 2 * lam_s2)


def main() -> None:
    records: List[Dict[str, Any]] = []

    print("=" * 70)
    print("Spike #10 — CMS Casimir identity for spin-weighted modes")
    print("=" * 70)

    print("\n[Symbolic baseline] spin-weighted S² Laplacian:")
    print(f"  λ_S²(ℓ, s) = {lam_s2}")
    records.append({
        "test": "baseline_spin_weighted_s2",
        "lam_s2_formula": str(lam_s2),
        "verdict": "Goldberg et al. 1967 convention; matches Spike #9 Part A.",
    })

    # ───────────────────────────────────────────────────────────────────
    # Convention SPIN-SHIFT (h = ℓ + 1 ± s)
    # ───────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("Convention SPIN-SHIFT (h_L = ℓ + 1 − s, h_R = ℓ + 1 + s)")
    print("=" * 70)
    print(f"  C_L = h_L(h_L − 1) = {C_L_shift}")
    print(f"  C_R = h_R(h_R − 1) = {C_R_shift}")
    print(f"  C_L + C_R = {sum_shift}")
    print(f"  C_L + C_R − 2·λ_S²(ℓ, s) = {identity_shift}")

    records.append({
        "test": "convention_spin_shift_symbolic",
        "convention": "h_L = ell + 1 - s, h_R = ell + 1 + s",
        "C_L": str(C_L_shift),
        "C_R": str(C_R_shift),
        "C_L_plus_C_R": str(sum_shift),
        "identity_residual_vs_2_lam_s2": str(identity_shift),
        "verdict_template": "C_L + C_R = 2·λ_S²(ℓ, s) + (closed-form spin term)",
    })

    print("\n[Spin-by-spin numerical check, SPIN-SHIFT convention]")
    print(f"{'s':>5s} {'identity_residual':>40s}")
    print("-" * 50)
    for s_val in [sp.Integer(0), sp.Rational(1, 2), sp.Integer(1), sp.Integer(2)]:
        residual = sp.simplify(identity_shift.subs(s, s_val))
        residual_str = str(residual)
        print(f"  {str(s_val):>3s}    {residual_str:>40s}")
        records.append({
            "test": "spin_shift_per_s",
            "convention": "spin_shift",
            "s": str(s_val),
            "identity_residual": residual_str,
        })

    # Particular emphasis on s = 2 (gravitational QNMs, LIGO target)
    s2_residual_shift = sp.simplify(identity_shift.subs(s, 2))
    sum_shift_s2 = sp.simplify(sum_shift.subs(s, 2))
    lam_s2_at_s2 = sp.simplify(lam_s2.subs(s, 2))
    print(f"\n[LIGO target] s = 2 (gravitational; SPIN-SHIFT convention):")
    print(f"  C_L + C_R = {sum_shift_s2}")
    print(f"  λ_S²(ℓ, 2) = {lam_s2_at_s2}")
    print(f"  C_L + C_R − 2·λ_S²(ℓ, 2) = {s2_residual_shift}")
    print(f"  → Identity:  C_L + C_R = 2·λ_S²(ℓ, 2) + {s2_residual_shift}")
    records.append({
        "test": "ligo_target_s2_spin_shift",
        "convention": "spin_shift",
        "spin": 2,
        "C_L_plus_C_R": str(sum_shift_s2),
        "lam_s2_at_s2": str(lam_s2_at_s2),
        "identity_offset_constant": str(s2_residual_shift),
        "closed_form_identity": (
            f"C_L + C_R = 2·λ_S²(ℓ, 2) + {s2_residual_shift}"
        ),
    })

    # ───────────────────────────────────────────────────────────────────
    # Convention HALF-SHIFT (h = ℓ + 1 ± s/2)
    # ───────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("Convention HALF-SHIFT (h_L = ℓ + 1 − s/2, h_R = ℓ + 1 + s/2)")
    print("=" * 70)
    print(f"  C_L = {C_L_half}")
    print(f"  C_R = {C_R_half}")
    print(f"  C_L + C_R = {sum_half}")
    print(f"  C_L + C_R − 2·λ_S²(ℓ, s) = {identity_half}")

    records.append({
        "test": "convention_half_shift_symbolic",
        "convention": "h_L = ell + 1 - s/2, h_R = ell + 1 + s/2",
        "C_L": str(C_L_half),
        "C_R": str(C_R_half),
        "C_L_plus_C_R": str(sum_half),
        "identity_residual_vs_2_lam_s2": str(identity_half),
    })

    print("\n[Spin-by-spin numerical check, HALF-SHIFT convention]")
    print(f"{'s':>5s} {'identity_residual':>40s}")
    print("-" * 50)
    for s_val in [sp.Integer(0), sp.Rational(1, 2), sp.Integer(1), sp.Integer(2)]:
        residual = sp.simplify(identity_half.subs(s, s_val))
        residual_str = str(residual)
        print(f"  {str(s_val):>3s}    {residual_str:>40s}")
        records.append({
            "test": "half_shift_per_s",
            "convention": "half_shift",
            "s": str(s_val),
            "identity_residual": residual_str,
        })

    # ───────────────────────────────────────────────────────────────────
    # Scalar (s = 0) sanity check vs Spike #9
    # ───────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("Sanity check vs Spike #9 Part C scalar result")
    print("=" * 70)
    scalar_shift = sp.simplify(sum_shift.subs(s, 0))
    scalar_half = sp.simplify(sum_half.subs(s, 0))
    expected_scalar = 2 * ell * (ell + 1)
    print(f"  SPIN-SHIFT  at s=0:  C_L + C_R = {scalar_shift}")
    print(f"  HALF-SHIFT  at s=0:  C_L + C_R = {scalar_half}")
    print(f"  Spike #9 expected:    C_L + C_R = {expected_scalar} = 2·λ_S²(ℓ)")
    assert sp.simplify(scalar_shift - expected_scalar) == 0
    assert sp.simplify(scalar_half - expected_scalar) == 0
    print(f"  ✓ Both conventions reduce to Spike #9 scalar result at s = 0.")
    records.append({
        "test": "spike9_scalar_sanity_check",
        "spin_shift_at_s0": str(scalar_shift),
        "half_shift_at_s0": str(scalar_half),
        "spike9_expected": str(expected_scalar),
        "both_match_spike9": True,
    })

    # ───────────────────────────────────────────────────────────────────
    # Verdict
    # ───────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("Verdicts")
    print("=" * 70)

    # SPIN-SHIFT verdict
    shift_verdict = (
        "Convention SPIN-SHIFT produces the closed-form identity\n"
        f"  C_L + C_R = 2·λ_S²(ℓ, s) + {sp.simplify(identity_shift)}\n"
        "i.e. the CMS Casimir sum exceeds 2·(spin-weighted S² eigenvalue)\n"
        "by an s-dependent offset that is INDEPENDENT of ℓ. The pattern\n"
        "from Spike #9 Part C (base + Casimir-of-hidden-symmetry = total)\n"
        "extends cleanly to spin-weighted modes, with the spin-shift\n"
        "appearing as a closed-form constant in ℓ."
    )
    print(shift_verdict)
    records.append({
        "test": "verdict_spin_shift",
        "verdict": shift_verdict,
        "closed_form_offset": str(sp.simplify(identity_shift)),
    })

    print()
    half_verdict = (
        "Convention HALF-SHIFT produces the closed-form identity\n"
        f"  C_L + C_R = 2·λ_S²(ℓ, s) + {sp.simplify(identity_half)}\n"
        "Same structural pattern, different closed-form spin term — the\n"
        "convention choice rescales the spin-dependence but doesn't change\n"
        "whether the identity holds. Both conventions confirm Result B's\n"
        "Casimir-decomposition family extends to spin-weighted CMS Kerr."
    )
    print(half_verdict)
    records.append({
        "test": "verdict_half_shift",
        "verdict": half_verdict,
        "closed_form_offset": str(sp.simplify(identity_half)),
    })

    final_verdict = (
        "Spike #10 confirms that the CMS hidden-conformal Casimir identity\n"
        "extends to spin-weighted modes with closed-form, ℓ-independent\n"
        "spin offset. The identity for spin-2 (gravitational QNMs, LIGO\n"
        "target) is fully algebraic — no numerical PDE integration needed\n"
        "in the CMS low-frequency limit.\n\n"
        "WHAT THIS UNLOCKS: a closed-form algebraic anchor for low-frequency\n"
        "Kerr ringdown QNMs (s=2). LIGO observes higher-frequency overtones\n"
        "where Mω ~ 0.3-0.5 (outside strict CMS regime Mω « 1), but the\n"
        "structural identity stands as the algebraic foundation that\n"
        "perturbation corrections build on.\n\n"
        "CAVEAT: convention choice for spin-shifted conformal weights is\n"
        "literature-dependent. Both conventions tested here give consistent\n"
        "structural-extension result; matching to LIGO data quantitatively\n"
        "requires picking the convention consistent with the Teukolsky-\n"
        "master-variable construction used by the QNM-extraction pipeline."
    )
    print("\n" + "=" * 70)
    print(final_verdict)
    records.append({
        "test": "final_verdict",
        "verdict": final_verdict,
    })

    # ───────────────────────────────────────────────────────────────────
    # NDJSON output
    # ───────────────────────────────────────────────────────────────────

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"\nNDJSON written: {RESULTS_FILE}")

    # ───────────────────────────────────────────────────────────────────
    # Plot
    # ───────────────────────────────────────────────────────────────────

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ell_vals = np.arange(2, 11)
    spins = [0, 0.5, 1.0, 2.0]
    colors = {0: "k", 0.5: "C0", 1.0: "C1", 2.0: "C3"}
    for s_val in spins:
        # SPIN-SHIFT convention
        lam_s2_vals = np.array([float(lam_s2.subs([(ell, e), (s, s_val)])) for e in ell_vals])
        sum_vals = np.array([float(sum_shift.subs([(ell, e), (s, s_val)])) for e in ell_vals])
        # Only plot where eigenvalue ≥ 0 (spin-weighted physics)
        mask = lam_s2_vals >= 0
        ax.plot(ell_vals[mask], sum_vals[mask], "o-", color=colors[s_val],
                label=f"$C_L + C_R$ at $s={s_val}$")
        ax.plot(ell_vals[mask], 2 * lam_s2_vals[mask], "x--", color=colors[s_val],
                alpha=0.6, label=f"$2\\lambda_{{S^2}}$ at $s={s_val}$" if s_val == 0 else None)

    ax.set_xlabel("multipole $\\ell$")
    ax.set_ylabel("Casimir sum / eigenvalue")
    ax.set_title("Spike #10: CMS $C_L + C_R$ vs $2\\lambda_{S^2}$ across spin (SPIN-SHIFT convention)\n"
                 "Constant ℓ-independent offset between curves = spin-shift term")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(PLOT_FILE, dpi=120)
    plt.close()
    print(f"Plot written: {PLOT_FILE}")


if __name__ == "__main__":
    main()
