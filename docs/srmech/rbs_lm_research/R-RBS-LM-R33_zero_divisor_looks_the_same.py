"""F391 — "or looks the same anyway": a zero-divisor collapse (||ab||=0, a,b nonzero) is OBSERVATIONALLY
IDENTICAL to a legitimate zero. That is WHY the Hurwitz boundary is a "strange place to stop" — nothing
LOOKS different at it; the failure is SILENT (a false-negation, F313). The only tell is the parity check
||ab|| =? ||a||*||b|| (the k=2 chiral/magnitude parity, F385/F389), which you only have if you CARRY it.

User (2026-06-04): "or looks the same anyway".

In a DIVISION algebra (O): a*b = 0 happens ONLY when a=0 or b=0, and it is RECOVERABLE — a^-1*(a*b) = b
(alternative identity). So a zero output is INFORMATIVE: it means a true zero, and you can divide back.
In the SEDENION (S): a*b = 0 with a,b nonzero (a zero divisor). The product is the zero vector — BIT-
IDENTICAL to 0*b. And "dividing back" a^-1*(a*b) = a^-1*0 = 0, NOT b: b's information is GONE and the output
looks exactly like a plain zero. The collapse "looks the same anyway".

srmech-native: qm.octonion.{octonion_left_mult, octonion_conjugate, octonion_norm}; sedenion by Cayley-
Dickson doubling. Comparisons via squared-norm of the difference (Class-K; no abs()).
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R33_zero_divisor_looks_the_same.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.qm.octonion import octonion_left_mult, octonion_conjugate, octonion_norm

HERE = Path(__file__).parent


def omul(a, b): return octonion_left_mult(np.asarray(a, float)) @ np.asarray(b, float)
def oconj(a): return octonion_conjugate(np.asarray(a, float))
def onorm2(a): return float(octonion_norm(np.asarray(a, float)) ** 2)
def oinv(a): return oconj(a) / onorm2(a)
def smul(x, y):
    a, b, c, d = x[:8], x[8:], y[:8], y[8:]
    return np.concatenate([omul(a, c) - omul(oconj(d), b), omul(d, a) + omul(b, oconj(c))])
def sconj(x): return np.concatenate([oconj(x[:8]), -x[8:]])
def snorm2(x): return float(octonion_norm(x[:8]) ** 2 + octonion_norm(x[8:]) ** 2)
def sinv(x): return sconj(x) / snorm2(x)
def e(i, n=16):
    v = np.zeros(n); v[i] = 1.0; return v


def main():
    print(f"F391 'or looks the same anyway' — the zero-divisor collapse is observationally a zero (srmech {srmech.__version__})")
    rng = np.random.default_rng(391)

    # OCTONION: a zero output is informative + recoverable (a^-1*(a*b) = b)
    a, b = rng.standard_normal(8), rng.standard_normal(8)
    recov_O = omul(oinv(a), omul(a, b))
    recoverable_O = float(octonion_norm(recov_O - b)) < 1e-9
    print("\n  OCTONION (division algebra):")
    print(f"    a*b = 0 happens ONLY if a=0 or b=0; and a^-1*(a*b) recovers b: {recoverable_O}")
    print(f"    => a zero output is INFORMATIVE (a true zero) and the bind is reversible.")

    # SEDENION: the zero divisor — product is the zero vector, looks identical to a true zero, unrecoverable
    za, zb = e(1) + e(10), e(5) + e(14)            # the F389 zero divisor
    zab = smul(za, zb)
    true_zero = smul(np.zeros(16), zb)             # a legitimate zero (0 * zb)
    looks_like_zero = snorm2(zab - true_zero) < 1e-12 and snorm2(zab) < 1e-12
    recov_S = smul(sinv(za), smul(za, zb))         # "divide back": a^-1 * (a*b)
    recovered_b = snorm2(recov_S - zb) < 1e-9
    recov_is_zero = snorm2(recov_S) < 1e-12
    print("\n  SEDENION (zero divisor (e1+e10)(e5+e14)):")
    print(f"    a,b nonzero (||a||^2={snorm2(za):.0f}, ||b||^2={snorm2(zb):.0f}) but a*b = 0-vector")
    print(f"    a*b is BIT-IDENTICAL to a legitimate zero (0*b): {looks_like_zero}  <- 'looks the same anyway'")
    print(f"    'divide back' a^-1*(a*b) recovers b: {recovered_b}; instead returns 0: {recov_is_zero}")
    print(f"    => b's information is GONE and the output looks exactly like a plain zero (UNRECOVERABLE).")

    # the ONLY tell: the parity check ||ab|| vs ||a||*||b||
    predicted = snorm2(za) * snorm2(zb)
    actual = snorm2(zab)
    print("\n  the ONLY signal that a collapse happened (you must CARRY it):")
    print(f"    parity check ||a||^2*||b||^2 = {predicted:.0f}  vs  ||a*b||^2 = {actual:.0f}  -> mismatch = collapse detected")

    print("\n=== verdict ===")
    print("  'Or looks the same anyway' — exactly. A zero-divisor collapse (||ab||=0, a,b nonzero) is")
    print("  OBSERVATIONALLY IDENTICAL to a legitimate zero: same zero-vector output, and 'dividing back'")
    print("  returns 0 not b (unrecoverable). So the Hurwitz boundary is a STRANGE place to stop because")
    print("  NOTHING LOOKS DIFFERENT at it — the failure is SILENT (a false-negation, F313: detect can't even")
    print("  fire). The ONLY way to see it is the explicit PARITY check ||ab|| =? ||a||*||b|| (the k=2 chiral/")
    print("  magnitude parity, F385/F389) — which you only have if you CARRY the chirality/magnitude (F385).")
    print("  This is the arc's through-line: the projection collapses distinctions and 'looks the same'")
    print("  (flat shadow F380, irreducible decimal F382, zero=zero-divisor here) UNLESS you carry the")
    print("  fiber/chirality/parity that surfaces the difference.")

    res = dict(srmech_version=srmech.__version__, octonion_recoverable=recoverable_O,
               sedenion_zero_divisor_looks_like_zero=bool(looks_like_zero),
               sedenion_recovered_b=bool(recovered_b), sedenion_divideback_returns_zero=bool(recov_is_zero),
               parity_predicted=predicted, parity_actual=actual)
    (HERE / "R-RBS-LM-R33_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R33_results.json'}")


if __name__ == "__main__":
    main()
