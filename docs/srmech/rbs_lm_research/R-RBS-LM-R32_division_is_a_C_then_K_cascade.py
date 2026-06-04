"""F390 — what cascade "does the same thing as division"? It is Class C (conjugate / chirality-flip) then
Class K (norm / magnitude-scale): a^-1 = conj(a) / ||a||^2. And it does NOT stop at the octonion — what
stops is a DIFFERENT property (the magnitude being a homomorphism over the bind, ||ab||=||a||*||b||).

User (2026-06-04): "well then what sort of cascade does the same thing as division? that seemed like a
strange place to stop."

The "strange place to stop" is the point: the Cayley-Dickson ladder is said to stop at O because the
sedenion is "not a division algebra" (F389). But the DIVISION CASCADE itself keeps running:
  inverse  a^-1 = conj(a)/||a||^2   = Class C (conjugate) -> Class K (1/||.||^2 scale)
  divide   b/a  = b * a^-1          = Class M (bind) o Class C o Class K
This composes at EVERY rung — it relies only on a*conj(a) = ||a||^2 (the *-algebra identity), which holds
in the sedenion too. So inverses exist past O.

What ACTUALLY stops at O is the COMPOSITION-NORM law ||a*b|| = ||a||*||b|| — i.e. Class K (magnitude) being a
HOMOMORPHISM over Class M (bind). That is the Hurwitz property (only dims 1,2,4,8), and it is an
error-correction-distance law: the norm = the code distance, and multiplicative-norm = distance PRESERVED
under composition = always decodable. Zero divisors (F389) = where the distance collapses to 0 = the
uncorrectable words. So the ladder stops where the K-over-M magnitude-homomorphism breaks, NOT where
"inversion" becomes uncomputable. The user's instinct is right.

srmech-native: qm.octonion.{octonion_left_mult, octonion_conjugate, octonion_norm}; sedenion built by
Cayley-Dickson doubling (as R31). No abs(): norms via octonion_norm; squared-norm comparisons.
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R32_division_is_a_C_then_K_cascade.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.qm.octonion import octonion_left_mult, octonion_conjugate, octonion_norm

HERE = Path(__file__).parent


def omul(a, b):
    return octonion_left_mult(np.asarray(a, float)) @ np.asarray(b, float)


def oconj(a):
    return octonion_conjugate(np.asarray(a, float))


def onorm2(a):
    return float(octonion_norm(np.asarray(a, float)) ** 2)


def oinv(a):                                   # octonion inverse = Class C (conj) -> Class K (1/||.||^2)
    return oconj(a) / onorm2(a)


def smul(x, y):                                # sedenion product (Cayley-Dickson double of O)
    a, b, c, d = x[:8], x[8:], y[:8], y[8:]
    return np.concatenate([omul(a, c) - omul(oconj(d), b), omul(d, a) + omul(b, oconj(c))])


def sconj(x):                                  # sedenion conjugate = Class C
    return np.concatenate([oconj(x[:8]), -x[8:]])


def snorm2(x):
    return float(octonion_norm(x[:8]) ** 2 + octonion_norm(x[8:]) ** 2)


def sinv(x):                                   # sedenion inverse = the SAME C -> K cascade
    return sconj(x) / snorm2(x)


def e(i, n=16):
    v = np.zeros(n); v[i] = 1.0; return v


def main():
    print(f"F390 division = Class C (conjugate) -> Class K (norm-scale); what stops is K-over-M (srmech {srmech.__version__})")
    rng = np.random.default_rng(390)
    one8, one16 = e(0, 8), e(0, 16)

    # (1) the division CASCADE: inverse = conj/||.||^2 — works in O
    print("\n(1) the division cascade  a^-1 = conj(a)/||a||^2  =  Class C (conjugate) -> Class K (1/||.||^2):")
    okO = []
    for _ in range(5):
        a = rng.standard_normal(8)
        prod = omul(a, oinv(a))
        okO.append(float(octonion_norm(prod - one8)) < 1e-9)
    print(f"    OCTONION: a * a^-1 == 1 for random a : {all(okO)}  (the C->K cascade inverts)")

    # (2) does the cascade STOP at the sedenion? test a*conj(a)=||a||^2 and a*a^-1=1 in S
    print("\n(2) does the cascade stop at the SEDENION? (the rung said to 'not be a division algebra')")
    aa_is_norm, inv_ok = [], []
    for _ in range(5):
        a = rng.standard_normal(16)
        aabar = smul(a, sconj(a))                       # a * conj(a)
        aa_is_norm.append(float(octonion_norm(aabar[:8] - snorm2(a) * one8) + octonion_norm(aabar[8:])) < 1e-8)
        inv_ok.append(float(octonion_norm(smul(a, sinv(a))[:8] - one8) + octonion_norm(smul(a, sinv(a))[8:])) < 1e-8)
    print(f"    a*conj(a) == ||a||^2 * 1  (the *-identity the cascade needs): {all(aa_is_norm)}")
    print(f"    a * a^-1 == 1 for random nonzero a                          : {all(inv_ok)}")
    print(f"    => the DIVISION CASCADE (C->K) RUNS in the sedenion too — inverses exist past O.")

    # (3) what ACTUALLY stops: the composition-norm  ||a*b|| = ||a||*||b||  (K homomorphism over M)
    print("\n(3) what STOPS at O — the magnitude-homomorphism ||a*b|| = ||a||*||b|| (Class K over Class M):")
    octo_mult = all(abs(onorm2(omul(a, b)) - onorm2(a) * onorm2(b)) < 1e-7
                    for a, b in [(rng.standard_normal(8), rng.standard_normal(8)) for _ in range(20)])
    print(f"    OCTONION: ||a*b||^2 == ||a||^2*||b||^2 for random a,b : {octo_mult}  (composition algebra — holds)")
    sed_pairs = [(rng.standard_normal(16), rng.standard_normal(16)) for _ in range(20)]
    sed_mult = all(abs(snorm2(smul(a, b)) - snorm2(a) * snorm2(b)) < 1e-7 for a, b in sed_pairs)
    worst = max(abs(snorm2(smul(a, b)) - snorm2(a) * snorm2(b)) for a, b in sed_pairs)
    zda, zdb = e(1) + e(10), e(5) + e(14)               # the F389 zero divisor
    print(f"    SEDENION: ||a*b||^2 == ||a||^2*||b||^2 for random a,b : {sed_mult}  (worst gap {worst:.2f} — FAILS)")
    print(f"    SEDENION zero divisor (e1+e10)(e5+e14): ||ab||^2 = {snorm2(smul(zda, zdb)):.1f} but "
          f"||a||^2||b||^2 = {snorm2(zda)*snorm2(zdb):.0f}  -> distance collapses to 0")

    print("\n=== verdict ===")
    print("  'Division' as a cascade = Class C (conjugate / chirality-flip) -> Class K (scale by 1/||.||^2);")
    print("  dividing is Class M (bind) o C o K:  b/a = b * conj(a)/||a||^2. This cascade RUNS AT EVERY RUNG")
    print("  (it needs only a*conj(a)=||a||^2, which holds in the sedenion) — inverses do NOT stop at O.")
    print("  What STOPS at O is a DIFFERENT law: ||a*b|| = ||a||*||b|| — Class K (magnitude) being a HOMOMORPHISM")
    print("  over Class M (bind). That is the Hurwitz composition-norm (dims 1,2,4,8 only), and it is an EC-")
    print("  DISTANCE law: norm = code distance, multiplicative-norm = distance preserved under composition =")
    print("  always decodable; zero divisors = distance->0 = uncorrectable words. So the 'strange place to stop'")
    print("  is NOT division stopping — it is the magnitude-bind homomorphism (the always-decodable guarantee)")
    print("  stopping. The C->K inverse cascade keeps going; only its GUARANTEE (no zero divisors) ends at O.")

    res = dict(srmech_version=srmech.__version__, octonion_inverse_ok=all(okO),
               sedenion_aabar_is_norm=all(aa_is_norm), sedenion_inverse_ok=all(inv_ok),
               octonion_norm_multiplicative=bool(octo_mult), sedenion_norm_multiplicative=bool(sed_mult),
               sedenion_worst_gap=worst, zero_divisor_norm2=snorm2(smul(zda, zdb)))
    (HERE / "R-RBS-LM-R32_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R32_results.json'}")


if __name__ == "__main__":
    main()
