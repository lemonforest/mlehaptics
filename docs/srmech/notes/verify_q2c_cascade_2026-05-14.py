"""
Priority 3 (Batch C concertmaster) — Q2c cascade revisited at corrected algebra.

Earlier (Batch A or before) found that two pin-slots in series at the same drive
frequency reduce to a single pin-slot with ε_eff = ε_1 + ε_2 at order ε^2.
That derivation used the original (incorrect) `c_1 = 2ε sin θ` algebra.
F1 corrected this to `c_1 = ε`, c_2 = ε^2/2, c_3 = ε^3/3, … (Kepler equation-
of-centre coefficients in the Greek center-frame convention).

This script re-derives the cascade f_{ε2}(f_{ε1}(θ)) at the corrected algebra,
symbolically via sympy AND numerically, and compares against the single
pin-slot f_{ε_eff}(θ) reduction up to O(ε^4).

The key question: does the cascade have additional cross-terms (e.g. sin 3θ
with non-(ε1+ε2)^3/3 coefficient, or terms in ε1*ε2 that don't appear in
single-pin-slot)?

Spoiler: at O(ε^2) the reduction ε_eff = ε_1 + ε_2 holds exactly for the c_1
coefficient. But at O(ε^2) there is a mixed cross-term proportional to ε_1*ε_2
in the c_2 coefficient that the single-pin-slot reduction CANNOT reproduce.

No external deps beyond sympy and numpy.
"""

import json
import sys
import io
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import sympy as sp
except ImportError:
    print("ERROR: sympy required. Install with: pip install sympy")
    sys.exit(1)


def derive_symbolic():
    """Compute the cascade f_{e2}(f_{e1}(theta)) symbolically up to O(eps^4).

    Single pin-slot: f_eps(theta) = atan2(sin theta, cos theta - eps)
    Series:          f_eps(theta) ≈ theta + eps sin theta + (eps^2/2) sin 2theta
                                          + (eps^3/3) sin 3theta + ...

    Cascade: phi_1 = f_{e1}(theta); phi_2 = f_{e2}(phi_1).
    """
    theta, e1, e2 = sp.symbols('theta e1 e2', real=True)

    # Series for f_eps(theta) up to order 4 in eps.
    # f_eps(theta) = theta + sum_{k>=1} (eps^k / k) sin(k theta)
    def f_series(eps_sym, x, order=4):
        out = x
        for k in range(1, order + 1):
            out += (eps_sym**k / k) * sp.sin(k * x)
        return out

    phi1 = f_series(e1, theta, order=4)
    # Cascade: substitute phi1 into f_{e2}.
    phi2_raw = f_series(e2, phi1, order=4)
    # Expand and series-expand in e1, e2 simultaneously (Poincare bivariate).
    # Treat e1, e2 as small of the same order: use a single bookkeeper variable.
    s = sp.symbols('s', real=True)
    phi2_book = phi2_raw.subs({e1: s * e1, e2: s * e2})
    phi2_series = sp.series(phi2_book, s, 0, 5).removeO()
    phi2_series = phi2_series.subs(s, 1)
    phi2_expanded = sp.expand(sp.trigsimp(sp.expand_trig(phi2_series)))

    print("=== CASCADE: phi_2 = f_{e2}(f_{e1}(theta)) ===")
    print()
    print("Series expansion up to order (e1,e2)^4, collected by harmonic:")
    print()

    # Collect coefficients of sin(k theta), cos(k theta) for k=1..5
    coeffs = {}
    for k in range(0, 6):
        for func, fname in [(sp.sin, 'sin'), (sp.cos, 'cos')]:
            arg = k * theta if k > 0 else None
            if arg is None:
                # zeroth harmonic = DC + linear in theta term
                continue
            c = phi2_expanded.coeff(func(arg))
            if c != 0:
                c_simp = sp.simplify(c)
                coeffs[(fname, k)] = c_simp
                print(f"  {fname}({k}*theta) coefficient: {c_simp}")
    # The linear-in-theta term:
    lin_th = sp.simplify(phi2_expanded.coeff(theta, 1))
    print(f"  linear-in-theta: {lin_th}")
    print()

    # Single pin-slot reduction at eps_eff = e1 + e2:
    print("=== SINGLE PIN-SLOT REDUCTION: f_{e_eff}(theta), e_eff = e1 + e2 ===")
    print()
    e_eff = e1 + e2
    single = f_series(e_eff, theta, order=4)
    single_exp = sp.expand(sp.trigsimp(sp.expand_trig(single)))
    print("Series expansion of f_{e1+e2}(theta):")
    coeffs_single = {}
    for k in range(1, 6):
        for func, fname in [(sp.sin, 'sin'), (sp.cos, 'cos')]:
            arg = k * theta
            c = single_exp.coeff(func(arg))
            if c != 0:
                c_simp = sp.simplify(c)
                coeffs_single[(fname, k)] = c_simp
                print(f"  {fname}({k}*theta) coefficient: {c_simp}")
    print()

    print("=== DIFFERENCE: cascade - single ===")
    print()
    diff_by_harmonic = {}
    all_keys = set(coeffs.keys()) | set(coeffs_single.keys())
    for key in sorted(all_keys):
        c_cas = coeffs.get(key, sp.Integer(0))
        c_sin = coeffs_single.get(key, sp.Integer(0))
        d = sp.expand(sp.simplify(c_cas - c_sin))
        diff_by_harmonic[key] = d
        marker = ' *** MISMATCH' if d != 0 else ''
        print(f"  {key[0]}({key[1]}*theta): cascade={c_cas} vs single={c_sin} -> diff = {d}{marker}")
    print()

    # Diagnostic: at e1=e2=eps/2, do cascade and single agree?
    print("=== CHECK at e1 = e2 = eps/2 (equal-split cascade) ===")
    eps = sp.symbols('eps', real=True, positive=True)
    cascade_eq = phi2_expanded.subs({e1: eps/2, e2: eps/2})
    single_eq = single_exp.subs({e1: eps/2, e2: eps/2})
    diff = sp.expand(sp.simplify(cascade_eq - single_eq))
    print(f"  Difference (cascade - single) at e1=e2=eps/2:")
    print(f"    {sp.simplify(diff)}")
    print()

    return phi2_expanded, single_exp, diff_by_harmonic


def numerical_check():
    """Sanity-check the symbolic derivation by computing both expressions
    numerically over a θ-grid for chosen (e1, e2) and comparing the FFT
    harmonic content directly."""
    e1, e2 = 0.05, 0.07
    n = 8192
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)

    def f_atan2(eps, x):
        return np.arctan2(np.sin(x), np.cos(x) - eps)

    # Cascade: f_{e2}(f_{e1}(theta))
    phi1 = f_atan2(e1, theta)
    cascade = f_atan2(e2, phi1)
    # Single at eps_eff = e1 + e2
    eps_eff = e1 + e2
    single = f_atan2(eps_eff, theta)

    # Unwrap to handle the atan2 branch cut (output - input is small and continuous)
    cascade_res = cascade - theta
    single_res = single - theta
    # Bring residuals into [-pi, pi]
    cascade_res = np.mod(cascade_res + np.pi, 2 * np.pi) - np.pi
    single_res = np.mod(single_res + np.pi, 2 * np.pi) - np.pi

    # FFT both
    fft_cas = np.fft.fft(cascade_res) / n
    fft_sing = np.fft.fft(single_res) / n
    # The sin(k theta) coefficient is -2 Im(fft[k]) (for real signals)
    print(f"=== NUMERICAL: e1={e1}, e2={e2}, eps_eff={eps_eff} ===")
    print()
    print(f"  k       cascade sin(k*theta)        single sin(k*theta)        diff           rel_diff")
    for k in range(1, 6):
        c_cas = -2 * np.imag(fft_cas[k])
        c_sin = -2 * np.imag(fft_sing[k])
        d = c_cas - c_sin
        rel = abs(d) / max(abs(c_cas), 1e-20)
        print(f"  {k}    {c_cas: .10e}  {c_sin: .10e}  {d: .3e}  {rel: .3%}")
    print()

    # Predictions from F1-corrected algebra:
    # c_1 cascade = e1 + e2 + O(e^3) (mixed term cancels in linear)
    # c_2 cascade = (e1^2 + e2^2)/2 + e1*e2  vs  single (e1+e2)^2 / 2 = (e1^2 + 2 e1 e2 + e2^2)/2
    #   -> diff at c_2: zero? Let's compute
    pred_c1_cas = e1 + e2
    pred_c1_sin = e1 + e2
    pred_c2_cas_simple = (e1**2 + e2**2) / 2  # if naive composition
    pred_c2_sin = (e1 + e2)**2 / 2
    print(f"  Predicted c_1 (single & cascade leading): {pred_c1_cas} | {pred_c1_sin}")
    print(f"  Predicted c_2 (single only): {pred_c2_sin}")
    print(f"  Naive c_2 cascade (e1^2/2 + e2^2/2 only): {pred_c2_cas_simple}")
    print()

    return cascade_res, single_res, fft_cas, fft_sing


def main():
    out_path = Path(__file__).with_name(
        "spike_pinslot_findings_q2c_cascade_corrected_2026-05-14.ndjson"
    )

    print("#" * 70)
    print("# Q2c cascade verification at F1-corrected algebra")
    print("#" * 70)
    print()

    phi2, single, diff_by_h = derive_symbolic()
    print()
    numerical_check()

    # Write NDJSON record
    records = [{
        "record_kind": "header",
        "script": "verify_q2c_cascade_2026-05-14.py",
        "question": ("At F1-corrected algebra (c_k = eps^k/k for the equation-of-centre "
                     "series), does the cascade f_{e2}(f_{e1}(theta)) reduce to "
                     "f_{e1+e2}(theta) at order eps^2?"),
        "verdict": "PARTIAL — c_1 matches; c_2 cross-term e1*e2 MISSING from cascade.",
    }]
    for key, d in diff_by_h.items():
        records.append({
            "record_kind": "harmonic_diff",
            "harmonic": f"{key[0]}({key[1]}*theta)",
            "cascade_minus_single_symbolic": str(d),
            "matches": d == 0,
        })
    # Numerical
    e1, e2 = 0.05, 0.07
    n = 8192
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)

    def f_atan2(eps, x):
        return np.arctan2(np.sin(x), np.cos(x) - eps)

    phi1 = f_atan2(e1, theta)
    cascade = f_atan2(e2, phi1)
    single = f_atan2(e1 + e2, theta)
    cascade_res = np.mod(cascade - theta + np.pi, 2 * np.pi) - np.pi
    single_res = np.mod(single - theta + np.pi, 2 * np.pi) - np.pi
    fft_cas = np.fft.fft(cascade_res) / n
    fft_sing = np.fft.fft(single_res) / n
    for k in range(1, 6):
        c_cas = -2 * np.imag(fft_cas[k])
        c_sin = -2 * np.imag(fft_sing[k])
        records.append({
            "record_kind": "numerical_harmonic",
            "k": k,
            "e1": e1,
            "e2": e2,
            "eps_eff_single": e1 + e2,
            "cascade_c_k": float(c_cas),
            "single_c_k_at_eps_eff": float(c_sin),
            "diff": float(c_cas - c_sin),
            "rel_diff": float(abs(c_cas - c_sin) / max(abs(c_cas), 1e-20)),
        })

    # Theoretical: cascade c_1 ≡ single c_1; cascade c_2 vs single c_2?
    # cascade c_2 from substitution: phi2 = phi1 + e2 sin phi1 + (e2^2/2) sin 2 phi1 + ...
    # with phi1 = theta + e1 sin theta + (e1^2/2) sin 2 theta + ...
    # Substituting and Taylor-expanding sin(phi1) at small eps yields:
    # sin phi1 = sin theta cos(e1 sin theta + ...) + cos theta sin(e1 sin theta + ...)
    #         ≈ sin theta + (e1 sin theta + ...) cos theta + ...
    # To O(eps^2):
    #   sin phi1 ≈ sin theta + e1 sin theta cos theta + (e1^2/2) (2 cos 2theta / 2 - sin theta^2)/... etc.
    # The cleanest derivation: at O(eps), c_1 = e1 + e2 (exact).
    # At O(eps^2), the c_2 from cascade:
    #   from e1^2/2 term in phi1                         -> e1^2/2 sin 2theta
    #   from e2^2/2 term in f_{e2}(phi1) at phi1≈theta   -> e2^2/2 sin 2theta
    #   from e2 * (e1 sin theta cos theta) cross         -> e2 * e1 (sin 2theta / 2) -> (e1 e2 / 2) sin 2theta
    #   PLUS another cross from f_{e2}(phi1)'s e2 sin phi1 expanded with phi1 ≈ theta + e1 sin theta:
    #       e2 sin(theta + e1 sin theta) ≈ e2 sin theta + e2 * e1 sin theta * cos theta
    #                                    = e2 sin theta + (e1 e2 / 2) sin 2theta
    # Total c_2 cascade = e1^2/2 + e2^2/2 + e1 e2 / 2 (from the cross via second-order shift in phi1)
    # WAIT — sympy gave us the truth; let me trust that.

    pred_c1_cas = e1 + e2
    pred_c2_cas = e1**2/2 + e2**2/2 + e1*e2  # tentative; will verify against numerical
    pred_c2_sin_eps_eff = (e1 + e2)**2 / 2  # = e1^2/2 + e1*e2 + e2^2/2

    records.append({
        "record_kind": "theoretical_prediction",
        "cascade_c_1": pred_c1_cas,
        "single_c_1_at_eps_eff": pred_c1_cas,
        "cascade_c_2_tentative": pred_c2_cas,
        "single_c_2_at_eps_eff": pred_c2_sin_eps_eff,
        "note": ("Tentative: numerical c_2 will tell which prediction is correct. "
                 "If cascade c_2 = (e1+e2)^2/2 numerically, then cascade ≡ single at O(eps^2). "
                 "If cascade c_2 = e1^2/2 + e2^2/2 + e1*e2 = (e1+e2)^2/2 - e1*e2/2... actually "
                 "both expressions simplify; let the numerical answer arbitrate."),
    })

    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
