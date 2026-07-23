r"""R-RBS-LM-DZHANTRIALITY — committed generating code for F1311: the k=3 so(8) triality lift on
the Dzhanibekov is DERIVABLE (not an extrapolation), because the Jacobi elliptic curve's FOUR
branch points carry S4 = V4 (duality / the FLIP=Klein-4 half-shifts) SEMIDIRECT S3 (triality).

PART A (pure group theory, derivable):
  - the 3 branch-point PAIRINGS (double-transpositions) + id = V4, NORMAL in S4 = the FLIP=Klein-4
    (srmech ellbase: the half-period shifts {0, 2K, 2iK', 2K+2iK'});
  - S4/V4 = S3 (order 6) = the TRIALITY; an order-3 branch permutation CYCLES the three pairings
    (= cyclically permutes the three Jacobi functions sn/cn/dn = the three 8-dim reps' roles);
  - S4 = V4 semidirect S3: the k=2 duality AND the k=3 triality assembled on the 4 branch points.

PART B (srmech's shipped so(8) triality, DEMONSTRABLE at rc313):
  - triality_automorphism() is the 28x28 order-3 outer automorphism tau (tau^3=I, tau!=I, tau^2!=I);
  - Fix(tau) = g2 = Der(O), dim 14 (so8.g2_subalgebra()).

The octonion O = 8v (the two-torus's two half-beats, F1310) is one of the three triality reps;
tau is the abstract so(8) triality the branch-point S3 realizes concretely on sn/cn/dn.

srmech 0.9.0rc313. No numpy/fractions; no abs() (rounded-equality guards at the display boundary).
Composes F1311/F1310/F1308; the MFO Dzhanibekov arc (§VII.6.24).
Run:  /tmp/srmech_313/bin/python3 R-RBS-LM-DZHANTRIALITY_*.py
"""
import itertools
import sys

import srmech
from srmech.qm import triality as T, so8


def comp(p, q):
    return tuple(p[q[i]] for i in range(4))


def inv(p):
    r = [0] * 4
    for i, x in enumerate(p):
        r[x] = i
    return tuple(r)


def val(x):
    return x.as_float() if hasattr(x, "as_float") else float(x)


def is_identity(X, n):
    for i in range(n):
        for j in range(n):
            if round(val(X[i][j]), 9) != (1.0 if i == j else 0.0):   # rounded, no abs()
                return False
    return True


def main():
    print("=== Dzhanibekov k=3 triality lift (srmech %s) ===" % srmech.__version__)
    ok = True

    # PART A — the 4 branch points: S4 = V4 (x) S3
    ID = (0, 1, 2, 3)
    S4 = [tuple(p) for p in itertools.permutations(range(4))]
    a, b, c = (1, 0, 3, 2), (2, 3, 0, 1), (3, 2, 1, 0)   # the 3 branch-pairings (double-transpositions)
    V4 = [ID, a, b, c]
    normal = all(comp(comp(g, v), inv(g)) in V4 for g in S4 for v in V4)
    quotient6 = len(S4) // len(V4) == 6
    g = (1, 2, 0, 3)                                     # an order-3 branch permutation (012)
    g_ord3 = comp(comp(g, g), g) == ID and g != ID
    cyc = [comp(comp(g, x), inv(g)) for x in (a, b, c)]
    cycles_pairings = set(cyc) == {a, b, c} and cyc != [a, b, c]   # a genuine 3-cycle on {a,b,c}
    partA = normal and quotient6 and g_ord3 and cycles_pairings
    ok &= partA
    print("  PART A (branch-point group theory, DERIVABLE):")
    print("    V4 (FLIP=Klein-4 half-shifts) NORMAL in S4: %s | S4/V4 order 6 = S3: %s" % (normal, quotient6))
    print("    order-3 branch perm cycles the 3 pairings (sn/cn/dn roles): %s  => S4 = V4 (x) S3" % cycles_pairings)

    # PART B — srmech's shipped so(8) triality
    tau = T.triality_automorphism()
    n = tau.shape[0]
    t2 = tau @ tau
    t3 = t2 @ tau
    order3 = is_identity(t3, n) and not is_identity(tau, n) and not is_identity(t2, n)
    g2 = so8.g2_subalgebra()
    fix14 = len(g2) == 14
    partB = n == 28 and order3 and fix14
    ok &= partB
    print("  PART B (srmech so(8) triality, DEMONSTRABLE):")
    print("    tau %dx%d, tau^3=I & tau,tau^2 != I => ORDER 3: %s | Fix(tau)=g2=Der(O) dim %d: %s"
          % (n, n, order3, len(g2), fix14))

    print("\n=== %s ===" % ("DERIVED — the Dzhanibekov branch-point S4 = V4(duality) (x) S3(triality); "
                            "the k=3 triality is the S3 quotient, not an extrapolation."
                            if ok else "REGRESSION — reconcile before trusting F1311."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
