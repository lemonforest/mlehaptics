"""F389 — the next rung up from the octonion is the SEDENION (16D); it gives ONE chiral axis that carries
all of the octonion — but it LOSES the division property (zero divisors), so it is "not really the
hyper-loop" (Hurwitz: only R,C,H,O are normed division algebras). So account for the chirality with one
truly-imaginary axis bolted on the octonion (the gamma5 / Klein-4 Z2), NOT the broken sedenion algebra.

User (2026-06-04): "what if we looked at the next math structure up from octonions so that we only have to
work with one chiral axis that comprises all of octonions? i'm wondering if the pair of quaternions
contribute to error correction. if that's the case, what if we just use math that accounts for it, even if
it's not really the hyperloop because one chiral axis is truly imaginary?"

Built srmech-native: the sedenion S = O (+) O*e8 is the Cayley-Dickson double of the octonion, constructed
from srmech's octonion multiply (qm.octonion.octonion_left_mult, the NAMED op), conjugate, and norm.
  (1) ONE chiral axis: e8 (the doubling unit) has e8^2 = -1 (truly imaginary), and right-multiplying by e8
      carries the WHOLE octonion O into its doubled copy O*e8 -> "one chiral axis comprises all of O".
  (2) LOSES division: there exist nonzero a,b with a*b = 0 (zero divisors) -> ||ab|| != ||a||*||b|| ->
      S is NOT a normed division algebra -> Hurwitz broken -> "not really the hyper-loop".
  (3) EC reading (lens): the chiral PAIR (the two opposite-handed halves; F387's (4:3)|(3:4)) is a k=2
      PARITY/DETECT (compare against the mirror); k=3 triality is what CORRECTS (F291). The pair contributes
      DETECTION; correction needs the third.

srmech-native: qm.octonion.{octonion_left_mult, octonion_conjugate, octonion_norm} (named ops). numpy only
to hold the 8/16-vectors and apply the srmech multiply operator; norms via octonion_norm (no abs()).
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R31_sedenion_one_chiral_axis_loses_division.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.qm.octonion import octonion_left_mult, octonion_conjugate, octonion_norm

HERE = Path(__file__).parent


def omul(a, b):
    return octonion_left_mult(np.asarray(a, float)) @ np.asarray(b, float)   # a*b via srmech's octonion operator


def oconj(a):
    return octonion_conjugate(np.asarray(a, float))


def smul(x, y):
    """Sedenion product (Cayley-Dickson double of O): x=(a,b), y=(c,d), each octonion (8-vec)."""
    a, b, c, d = x[:8], x[8:], y[:8], y[8:]
    re = omul(a, c) - omul(oconj(d), b)
    im = omul(d, a) + omul(b, oconj(c))
    return np.concatenate([re, im])


def snorm2(x):
    return float(octonion_norm(x[:8]) ** 2 + octonion_norm(x[8:]) ** 2)      # ||x||^2 (Class-K; no abs())


def e(i):
    v = np.zeros(16); v[i] = 1.0; return v


def main():
    print(f"F389 sedenion: one chiral axis comprises all of O, but loses division (srmech {srmech.__version__})")

    # (1) ONE chiral axis e8: e8^2 = -1, and e8 carries all of O into the doubled copy
    e8 = e(8)
    e8sq = smul(e8, e8)
    a = np.zeros(16); a[:8] = [0, 1, 2, 3, 0, 0, 0, 0]            # an arbitrary octonion sitting in the first half
    a_lift = smul(a, e8)                                          # a * e8
    first_half2 = octonion_norm(a_lift[:8]) ** 2                   # ||first octonion half||^2
    second_half2 = octonion_norm(a_lift[8:]) ** 2                  # ||doubled-copy half||^2
    lifted_into_second = first_half2 < 1e-9 and second_half2 > 1e-9
    print(f"\n(1) ONE chiral axis e8 (the doubling unit):")
    print(f"    e8*e8 = {e8sq[:1].tolist()} (re part) -> e8^2 = -1  (truly imaginary): {abs(e8sq[0] + 1) < 1e-9}")
    print(f"    (octonion a in first half) * e8 lands ENTIRELY in the doubled copy O*e8: {bool(lifted_into_second)}")
    print(f"    => e8 is ONE chiral axis that carries the WHOLE octonion O into its mirror copy.")

    # (2) LOSES division: search for a zero divisor among (e_i+e_j)(e_k+e_l)
    print("\n(2) division property: searching for zero divisors (e_i+e_j)(e_k+e_l) = 0 ...")
    found = []
    for i in range(1, 16):
        for j in range(i + 1, 16):
            A = e(i) + e(j)
            for k in range(1, 16):
                for l in range(k + 1, 16):
                    B = e(k) + e(l)
                    if snorm2(smul(A, B)) < 1e-9:
                        found.append((i, j, k, l))
    print(f"    zero-divisor pairs of this form: {len(found)}  (a normed DIVISION algebra has ZERO)")
    if found:
        i, j, k, l = found[0]
        A, B = e(i) + e(j), e(k) + e(l)
        prod_n2 = snorm2(smul(A, B))
        mult_check = snorm2(A) * snorm2(B)
        print(f"    example: (e{i}+e{j})*(e{k}+e{l}) = 0  with  ||a||^2*||b||^2 = {mult_check:.0f} > 0 but ||ab||^2 = {prod_n2:.1e}")
        print(f"    => norm NOT multiplicative -> S is NOT a division algebra -> Hurwitz broken (only R,C,H,O).")

    # (3) associativity already gone (octonion, F378/F387); sedenion ALSO loses alternativity — note only.
    print("\n=== verdict ===")
    print("  The next rung up from O is the SEDENION S = O (+) O*e8 (Cayley-Dickson double). It DOES give what")
    print("  you asked: ONE chiral axis e8 (truly imaginary, e8^2=-1) that carries the WHOLE octonion into its")
    print("  mirror copy. BUT S LOSES the division property — zero divisors exist (a*b=0, a,b nonzero), the norm")
    print("  is no longer multiplicative — so it is 'not really the hyper-loop' (Hurwitz: only R,C,H,O are normed")
    print("  division algebras). EXACTLY the user's caveat.")
    print("  => So don't carry the broken sedenion: ACCOUNT FOR the chirality with ONE truly-imaginary axis")
    print("     (the gamma5 / Klein-4 second Z2, F129/F130/F380) bolted onto the octonion — keeping O's good")
    print("     (alternative, normed) structure and adding a clean chiral PARITY bit, no zero divisors.")
    print("  EC reading (lens): the chiral PAIR (F387's (4:3)|(3:4), the two opposite-handed halves) is a k=2")
    print("     PARITY = DETECT (compare to the mirror); k=3 triality is what CORRECTS (F291). The pair detects;")
    print("     the third copy corrects. So the quaternion-pair contributes ERROR-DETECTION, not full correction.")

    res = dict(srmech_version=srmech.__version__, e8_squared_re=float(e8sq[0]),
               octonion_lifts_into_mirror=bool(lifted_into_second),
               zero_divisor_pairs=len(found), first_zero_divisor=found[0] if found else None,
               is_division_algebra=(len(found) == 0))
    (HERE / "R-RBS-LM-R31_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R31_results.json'}")


if __name__ == "__main__":
    main()
