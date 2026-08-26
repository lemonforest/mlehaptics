r"""R-RBS-LM-MUSICTRIAD — committed generating code for F1308's DEMONSTRABLE claims.

The music-theory reading of op(x)operand(x)responsion, grounded at srmech 0.9.0rc313:
  (A) the octonion is 3+1+3 — two quaternion "half-beats" joined by e4; the seam-line on the
      responsions is {e3, e4, e7} (NOT {3,4,5}); the second strand is the CONJUGATE (mirror);
  (B) bit-exactness is a PRODUCT/operand property (all cd_mult products are exact sign-perms,
      incl. e4) — NOT an eigenvalue/responsion property: a graph's eigenvalues are IRRATIONAL
      (inharmonic), and best_rational (Class-N) is the rational Q-bridge that only closes tight
      at commensurate (harmonic/consonant) ratios.

Per [[feedback_computational_provenance_discipline]]. Exit non-zero if any claim regresses.
Run:  /tmp/srmech_313/bin/python3 R-RBS-LM-MUSICTRIAD_verify_*.py
Composes F1308/F1065/F1171/F1272/F1301/F1302.
"""
import sys

from srmech.amsc import cascade as C, laplacian as L, rational as R


def u(i, d=8):
    v = [0.0] * d
    v[i] = 1.0
    return v


def ff(x):
    return float(x.as_float()) if hasattr(x, "as_float") else float(x)


def prod(a, b):
    return tuple(round(ff(x)) for x in C.cd_mult(u(a), u(b)))


def unit(v):  # (sign, index) of a unit octonion, or None
    for k, x in enumerate(v):
        if x:
            return (1 if x > 0 else -1, k)
    return None


def main():
    print("=== music-triad grounding (srmech %s) ===" % __import__("srmech").__version__)
    ok = True

    # (A) octonion 3+1+3 seam
    # first strand quaternion i*j=k
    strand1 = prod(1, 2) == (0, 0, 0, 1, 0, 0, 0, 0)   # e1*e2 = +e3
    # e4 lifts strand1 -> strand2: e_k*e4 = +e_{k+4}
    lift = all(prod(k, 4) == u(k + 4) or prod(k, 4) == tuple(u(k + 4)) for k in (1, 2, 3)) \
        and unit(list(prod(1, 4))) == (1, 5) and unit(list(prod(3, 4))) == (1, 7)
    # the SEAM line on the responsions: e3 (resp of strand1) * e4 = e7 (resp of strand2)  -> {3,4,7}
    seam = unit(list(prod(3, 4))) == (1, 7)
    not_345 = unit(list(prod(3, 4))) != (1, 5)         # {3,4,5} is NOT the line
    # second strand is the CONJUGATE: e5*e6 = -e3 (mirror of e1*e2 = +e3)
    conj = unit(list(prod(5, 6))) == (-1, 3)
    ok &= strand1 and lift and seam and not_345 and conj
    print("  (A) octonion: strand1 i*j=k=%s  e_k*e4=e_{k+4} lift=%s  seam-line {3,4,7} (e3*e4=e7)=%s  not{3,4,5}=%s  strand2 CONJUGATE (e5*e6=-e3)=%s"
          % (strand1, lift, seam, not_345, conj))

    # (B) bit-exactness: product exact (incl e4) vs eigenvalue irrational
    e4_exact = unit(list(prod(4, 1))) == (-1, 5)       # e4*e1 = -e5 exactly (a sign-perm)
    E = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]       # C5
    r = L.symmetric_eigendecompose(L.dense_laplacian(5, E))
    vals = sorted(round(ff(v), 6) for v in (r[0] if isinstance(r, tuple) else r))
    lam1, lam3 = vals[1], vals[3]
    # rounded-equality checks (no abs(): tolerance via rounding at the display boundary)
    irrational = round(lam1, 3) == 1.382 and round(lam3, 3) == 3.618           # (5-+5**.5)/2, not rational
    p, q = R.best_rational(int(round(lam1 * 10**9)), 10**9, 200)               # Class-N anchor
    anchor_close = round(p / q, 3) == round(lam1, 3) and (p, q) != (0, 1)
    ratio = round(lam3 / lam1, 6)                                              # = golden^2 = 2.618..
    inharmonic = round(ratio, 3) == 2.618                                      # irrational (golden^2)
    ok &= e4_exact and irrational and anchor_close and inharmonic
    print("  (B) e4 product exact (e4*e1=-e5)=%s | C5 eigenvalues %s IRRATIONAL=%s | best_rational=%d/%d (Q-bridge)=%s | ratio %.4f INHARMONIC=%s"
          % (e4_exact, vals, irrational, p, q, anchor_close, ratio, inharmonic))

    print("\n=== %s ===" % ("BOTH GROUNDED — seam joins the two responsions; eigenvalues are inharmonic, bridged by Class-N."
                            if ok else "REGRESSION — reconcile before trusting F1308."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
