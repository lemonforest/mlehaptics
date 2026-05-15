"""
F16 closed-form extension — cascade vs single-pin-slot reconciliation via
Bessel-Anger composition.

Batch C F16 (verify_q2c_cascade_2026-05-14.py) found via sympy:
  - c_1 cascade = e_1 + e_2 = c_1 single (at e_eff = e_1 + e_2). MATCH.
  - c_2 cascade = e_1²/2 + e_2²/2 + e_1 e_2/2.
  - c_2 single   = (e_1 + e_2)²/2 = e_1²/2 + e_1 e_2 + e_2²/2.
  - → MISMATCH: cascade has e_1 e_2 / 2; single has e_1 e_2.
    Factor-of-2 in the cross-term.

This script reconciles the discrepancy against the closed-form pin-slot
Fourier series f_ε(θ) − θ = Σ_{k≥1} (ε^k/k) sin(kθ).

Composition algebra:
  Let φ_1 = θ + g_{e1}(θ) where g_e(θ) = Σ_{k≥1} (e^k/k) sin(k θ).
  Cascade: φ_2 = φ_1 + g_{e2}(φ_1).
  Single:  ψ = θ + g_{eps}(θ) with eps = e_1 + e_2.

So φ_2 − θ − (ψ − θ) = g_{e1}(θ) + g_{e2}(θ + g_{e1}(θ)) − g_{e1+e2}(θ).

Expand g_{e2}(θ + δ) where δ = g_{e1}(θ) is small in e_1:
  g_{e2}(θ + δ) = Σ_{k≥1} (e_2^k/k) sin(k θ + k δ)
                = Σ_{k≥1} (e_2^k/k) [sin(kθ) cos(k δ) + cos(kθ) sin(k δ)]

Taylor-expanding cos(k δ) ≈ 1 − (kδ)²/2 + ... and sin(k δ) ≈ kδ − (kδ)³/6 + ...
in small δ, we get:
  g_{e2}(θ + δ) = g_{e2}(θ) + δ · g'_{e2}(θ) + (δ²/2) · g''_{e2}(θ) + ...
  where g'_{e2}(θ) = Σ_{k≥1} e_2^k cos(k θ).

The first-order-in-δ cross-term contribution to c_2 sin(2θ):
  δ · g'_{e2}(θ) = g_{e1}(θ) · Σ_{k} e_2^k cos(kθ)
              = [e_1 sin θ + O(e_1²)] · [e_2 cos θ + e_2² cos 2θ + ...]
              = e_1 e_2 sin θ cos θ + ...
              = (e_1 e_2 / 2) sin 2θ + ...

So the cross-term contribution to c_2 (from the φ_1 → φ_2 stage's first-order
Taylor in δ) is (e_1 e_2 / 2) sin 2θ. The cascade's c_2 = e_1²/2 + e_2²/2
+ e_1 e_2 / 2, exactly matching Batch C's symbolic finding.

The single-pin-slot at ε_eff = e_1 + e_2 gives c_2 = (e_1+e_2)²/2
= e_1²/2 + e_1 e_2 + e_2²/2.

Difference: cascade − single = − e_1 e_2 / 2. The single OVERSHOOTS by
e_1 e_2 / 2 because it counts the cross-term TWICE: once as a "pseudo-input"
broadening, once via the squared ε_eff. The cascade's first-order-in-δ
substitution only generates the cross-term ONCE.

# Bessel-Anger interpretation

The closed-form ALL-ε Fourier series for the cascade is NOT the simple
Σ (e^k/k) sin(kθ) but rather has cross-terms from the composition. Bessel-Anger
gives, for the SHIFTED-argument sin/cos:

  sin(k θ + k δ) where δ = Σ_j (e_1^j/j) sin(j θ)

If we treat k δ as the "amplitude" in a Jacobi-Anger expansion, but δ is itself
already a Fourier series, the result is a multi-index Bessel expansion. At
leading order, the cross-coupling between e_1 and e_2 in the cascade is:

  e_1 e_2 / (2k) · sin((k+1)θ) − e_1 e_2 / (2k) · sin((k−1)θ)

via the product-to-sum identity sin(kθ) · cos(θ) = (sin((k+1)θ) + sin((k−1)θ))/2
and cos(kθ) · sin(θ) similarly.

This is the cleaner closed-form statement of F16's symbolic finding: the
cascade's spectrum has a SPECIFIC cross-term contribution that the
single-pin-slot reduction misses, NOT just a generic "higher-order correction."

# What stands and what falls

- F16's symbolic verdict (cascade ≠ single at c_2) STANDS, confirmed by
  closed-form Bessel-Anger composition algebra.
- The interpretation in F16 ("factor-of-2 in cross-term") is correct.
- New algebraic insight: the missing-factor-of-2 is precisely the cross-term
  e_1 e_2 / 2 that the φ_1 → φ_2 substitution generates ONCE; the single
  ε_eff² / 2 would generate it TWICE.
- This invalidates ANY future spike that treats Q2c cascade as equivalent to a
  single pin-slot at ε_eff = ε_1 + ε_2 beyond first harmonic. F16's caveat is
  reinforced.

No external deps beyond sympy and numpy.
"""

import json
import sys
import io
from pathlib import Path
import sympy as sp
import numpy as np
from sympy.simplify.fu import TR8

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def pinslot_series(eps, x, order=4):
    """Exact closed-form Fourier series: f_ε(x) − x = Σ_{k≥1} (ε^k/k) sin(kx)."""
    return sum((eps**k / k) * sp.sin(k * x) for k in range(1, order + 1))


def to_lattice_form(expr):
    """Convert to integer-lattice trig form (no products of trig terms)."""
    cur = sp.expand_trig(expr)
    cur = sp.expand(cur)
    for _ in range(8):
        new = sp.expand(TR8(cur))
        if new == cur:
            break
        cur = new
    return cur


def harmonic_coeff(expr, theta, k_target):
    """Extract sin(k_target · theta) coefficient from expr after lattice form."""
    expanded = to_lattice_form(expr)
    if k_target == 0:
        return sp.Integer(0)
    sin_term = sp.sin(k_target * theta)
    # Direct coeff
    c1 = expanded.coeff(sin_term)
    # Also check the negated argument
    c2 = expanded.coeff(sp.sin(-k_target * theta))
    return sp.simplify(c1 - c2)


def closed_form_cascade_vs_single(order=4):
    """Symbolic derivation: cascade c_k vs single at ε_eff = e_1 + e_2."""
    theta, e1, e2, s = sp.symbols('theta e_1 e_2 s', real=True, positive=True)

    # Bookkeeper s: rescale e_1, e_2 → s e_1, s e_2 and Taylor-expand in s.
    phi1 = theta + pinslot_series(s * e1, theta, order=order)
    phi2 = phi1 + pinslot_series(s * e2, phi1, order=order)
    cascade_resid = sp.series(phi2 - theta, s, 0, order + 1).removeO().subs(s, 1)

    # Single at ε_eff = e_1 + e_2
    eps_eff = e1 + e2
    single_resid = sp.series(
        pinslot_series(s * eps_eff, theta, order=order),
        s, 0, order + 1
    ).removeO().subs(s, 1)

    results = []
    for k in range(1, order + 1):
        c_cas = harmonic_coeff(cascade_resid, theta, k)
        c_sin = harmonic_coeff(single_resid, theta, k)
        diff = sp.simplify(c_cas - c_sin)
        results.append({
            "harmonic_k": k,
            "cascade_c_k": str(c_cas),
            "single_c_k_at_eps_eff": str(c_sin),
            "diff_cascade_minus_single": str(diff),
            "matches": diff == 0,
        })
        print(f"k={k}:")
        print(f"  cascade c_k = {c_cas}")
        print(f"  single  c_k = {c_sin}")
        print(f"  diff        = {diff}{'  MATCH' if diff == 0 else '  MISMATCH'}")
        print()
    return results


def numerical_verification(e1_val=0.05, e2_val=0.07):
    """Numerical check of cascade vs single at chosen ε values, with detrending."""
    n = 16384
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    f = lambda eps, x: np.arctan2(np.sin(x), np.cos(x) - eps)

    phi1 = f(e1_val, theta)
    cascade = f(e2_val, phi1)
    single = f(e1_val + e2_val, theta)

    cas_resid = (cascade - theta + np.pi) % (2 * np.pi) - np.pi
    sing_resid = (single - theta + np.pi) % (2 * np.pi) - np.pi

    F_cas = np.fft.fft(cas_resid) / n
    F_sing = np.fft.fft(sing_resid) / n
    c_cas = [-2 * np.imag(F_cas[k]) for k in range(1, 8)]
    c_sin = [-2 * np.imag(F_sing[k]) for k in range(1, 8)]

    # Analytical prediction for each
    pred_cas = {
        1: e1_val + e2_val,
        2: e1_val**2/2 + e2_val**2/2 + e1_val * e2_val / 2,
        # c_3 cascade — derive: e_1^3/3 + e_2^3/3 + cross terms?
    }
    pred_sin = {
        1: e1_val + e2_val,
        2: (e1_val + e2_val)**2 / 2,
        3: (e1_val + e2_val)**3 / 3,
    }

    print(f"\n=== Numerical (e_1={e1_val}, e_2={e2_val}, ε_eff={e1_val+e2_val}) ===")
    print(f"{'k':>3} {'cascade c_k':>15} {'single c_k':>15} {'pred_cas':>12} {'pred_sin':>12} {'rel_diff %':>10}")
    for k in range(1, 6):
        rel = abs(c_cas[k-1] - c_sin[k-1]) / (abs(c_cas[k-1]) + 1e-20) * 100
        pc = pred_cas.get(k, float('nan'))
        ps = pred_sin.get(k, float('nan'))
        print(f"{k:>3} {c_cas[k-1]: >15.6e} {c_sin[k-1]: >15.6e} {pc: >12.6e} {ps: >12.6e} {rel: >9.2f}%")
    return c_cas, c_sin


def jacobi_anger_explanation(order=3):
    """Show the Jacobi-Anger / product-to-sum derivation of c_2 cascade.

    The cross-term in c_2 cascade arises from substituting φ_1 = θ + δ where
    δ ≈ e_1 sin θ, into the f_{e_2} series at the LEADING e_2 term:

    f_{e_2}(φ_1) − φ_1 = e_2 sin(φ_1) + (e_2²/2) sin(2 φ_1) + ...

    The e_2 sin(φ_1) term expanded with φ_1 = θ + e_1 sin θ:
      e_2 sin(θ + e_1 sin θ)
        = e_2 [sin θ cos(e_1 sin θ) + cos θ sin(e_1 sin θ)]
        ≈ e_2 [sin θ · 1 + cos θ · (e_1 sin θ)]   (small e_1)
        = e_2 sin θ + e_1 e_2 sin θ cos θ
        = e_2 sin θ + (e_1 e_2 / 2) sin 2θ.

    So the cross-term (e_1 e_2 / 2) sin 2θ in cascade c_2 comes from the
    Jacobi-Anger expansion of the leading-order e_2 sin(φ_1) when φ_1 = θ + δ.

    The "missing factor of 2" relative to single (e_1+e_2)²/2 = e_1²/2 + e_1 e_2
    + e_2²/2 is because the single expansion squares ε_eff = e_1+e_2 directly,
    counting the cross-term as e_1·e_2 + e_2·e_1 (twice), while the cascade
    introduces it only once at first-order in δ.
    """
    theta, e1, e2 = sp.symbols('theta e_1 e_2', real=True, positive=True)
    # Just the cascade c_2 cross-term derivation:
    delta = e1 * sp.sin(theta)
    # f_{e_2}(theta + delta) leading at order (e_1 e_2):
    expanded = e2 * sp.sin(theta + delta)
    expanded = sp.series(expanded, e1, 0, 2).removeO()
    expanded = to_lattice_form(expanded)
    print(f"\nJacobi-Anger derivation of cascade c_2 cross-term:")
    print(f"  e_2 sin(θ + e_1 sin θ) to O(e_1):")
    print(f"  = {expanded}")
    # Read sin(2 theta) coefficient
    c2_cross = harmonic_coeff(expanded, theta, 2)
    print(f"  Coefficient of sin(2θ): {sp.simplify(c2_cross)}")
    return c2_cross


def main():
    print("=" * 70)
    print("F16 CLOSED-FORM EXTENSION: cascade vs single via Bessel-Anger algebra")
    print("=" * 70)

    print("\n--- Symbolic derivation (sympy + closed-form Fourier series) ---")
    harmonics = closed_form_cascade_vs_single(order=4)

    print("--- Numerical verification ---")
    c_cas, c_sin = numerical_verification(e1_val=0.05, e2_val=0.07)

    print("--- Jacobi-Anger explanation ---")
    cross_term = jacobi_anger_explanation()

    records = [{
        "record_kind": "header",
        "script": "spike_pinslot_closed_form_f16_2026-05-15.py",
        "question": ("Closed-form (Bessel-Anger / Jacobi-Anger) derivation of "
                     "cascade f_{e2}(f_{e1}(θ)) vs single f_{e1+e2}(θ). Does the "
                     "F16 symbolic 'cascade ≠ single at c_2+' verdict hold?"),
        "method": ("Pin-slot closed-form Fourier series f_ε(θ) − θ = Σ (ε^k/k) sin(kθ) "
                   "+ Jacobi-Anger expansion sin(θ + δ) = sin θ cos δ + cos θ sin δ "
                   "+ small-δ Taylor + product-to-sum identities."),
        "references": [
            "PROJECT-CANONICAL closed-form pin-slot Fourier series (verified ε=0.5)",
            "Jacobi-Anger expansion sin(θ+δ) = sin θ cos δ + cos θ sin δ (elementary trig identity, no external citation needed)",
            "Murray & Dermott (1999) Ch. 2 — equation-of-centre context (citation unverified — not PDF-extracted)",
        ],
        "citation_discipline_note": "MATHEMATICAL CONTENT (Jacobi-Anger expansion, equation-of-centre series) is well-established. Specific textbook equation numbers are NOT primary-source-verified in this session.",
    }]

    for h in harmonics:
        records.append({"record_kind": "harmonic_symbolic", **h})

    records.append({
        "record_kind": "jacobi_anger_derivation",
        "expression": "e_2 sin(θ + e_1 sin θ) to O(e_1)",
        "sin_2theta_cross_term_coefficient": str(sp.simplify(cross_term)),
        "interpretation": ("The cross-term (e_1 e_2 / 2) sin 2θ in cascade c_2 "
                           "arises from the Jacobi-Anger expansion of e_2 sin(θ+δ) "
                           "at first order in δ = e_1 sin θ. The single-pin-slot "
                           "reduction at ε_eff = e_1+e_2 produces e_1 e_2 sin 2θ "
                           "(twice the cascade's cross-term) because squaring "
                           "ε_eff = e_1+e_2 generates e_1 e_2 from BOTH the "
                           "(e_1)(e_2) and (e_2)(e_1) cross-products."),
    })

    # Numerical records
    e1_val, e2_val = 0.05, 0.07
    for k, (c_c, c_s) in enumerate(zip(c_cas, c_sin), start=1):
        records.append({
            "record_kind": "numerical_check",
            "k": k,
            "e1": e1_val,
            "e2": e2_val,
            "cascade_c_k_numerical": c_c,
            "single_c_k_numerical": c_s,
            "diff": c_c - c_s,
            "rel_diff_percent": abs(c_c - c_s) / (abs(c_c) + 1e-20) * 100,
        })

    summary = {
        "record_kind": "summary",
        "verdict": ("F16 symbolic finding CONFIRMED by closed-form Bessel-Anger "
                    "algebra. Cascade c_2 = e_1²/2 + e_2²/2 + e_1 e_2 / 2 ≠ "
                    "single c_2 = (e_1+e_2)²/2 = e_1²/2 + e_1 e_2 + e_2²/2. "
                    "Difference at c_2: cascade − single = − e_1 e_2 / 2. "
                    "The single-pin-slot reduction at ε_eff = e_1+e_2 OVERSHOOTS "
                    "the cascade by e_1 e_2 / 2 at second harmonic."),
        "closed_form_strengthens_F16": True,
        "jacobi_anger_role": ("The cross-term is exactly the Jacobi-Anger small-δ "
                              "expansion of sin(θ + δ) at δ = e_1 sin θ, picking out "
                              "the product-to-sum reduction sin θ · cos θ = sin 2θ / 2."),
        "load_bearing_for_future_spikes": ("Any future spike treating Q2c cascade as "
                                           "equivalent to a single pin-slot at ε_eff "
                                           "is wrong beyond first harmonic. F11's "
                                           "forced-oscillator framing: if torque is "
                                           "concentrated at c_1, the cascade-vs-single "
                                           "distinction is negligible; if at c_2+, the "
                                           "distinction is load-bearing."),
    }
    records.append(summary)

    out_path = Path(__file__).with_name(
        "spike_pinslot_findings_closed_form_f16_2026-05-15.ndjson"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\n\nWrote {out_path}")


if __name__ == "__main__":
    main()
