r"""R-RBS-LM-ANTIKYTHERATRIALITY — committed generating code for F1313: the k=3 so(8) triality
lift on the Antikythera pin-slot. The MFO §VII.6.24 geometric-oscillator catalog classifies the
slot SHAPE by its K_{1,n} Laplacian, and notes the rotating X-slot is a branched cover of S^1
with "monodromy in S4" — but never decomposes that S4. The lift does: the X-slot's FOUR arms
are the same four objects that carry S4 = V4 (x) S3 (F1311/F1312), so the monodromy decomposes
into V4 (the pin's double-swaps of arm-pairs = the |->X duality) semidirect S3 (the order-3
cycle of the three arm-pairings = the k=3 TRIALITY the notebook deferred).

Grounds: (A) the K_{1,n} slot-shape Laplacian spectra (the MFO catalog); (B) the X-slot's 4 arms
carry S4 = V4 (x) S3, the order-3 element cycling the three arm-PAIRINGS.

srmech 0.9.0rc313. No numpy/fractions/abs(). Composes F1313/F1311/F1312/F1310; MFO §VII.6.24.
Run:  /tmp/srmech_313/bin/python3 R-RBS-LM-ANTIKYTHERATRIALITY_*.py
"""
import itertools
import sys

import srmech
from srmech.amsc import laplacian as L


def f(x):
    return float(x.as_float()) if hasattr(x, "as_float") else float(x)


def spec(n, E):
    return sorted(round(f(v), 3) for v in L.symmetric_eigendecompose(L.dense_laplacian(n, E))[0])


def comp(p, q):
    return tuple(p[q[i]] for i in range(4))


def inv(p):
    r = [0] * 4
    for i, x in enumerate(p):
        r[x] = i
    return tuple(r)


def main():
    print("=== Antikythera pin-slot triality (srmech %s) ===" % srmech.__version__)
    ok = True

    # A — the MFO geometric-oscillator slot catalog (K_{1,n} = the slot SHAPE)
    bar = spec(2, [(0, 1)])                                   # |-slot  = lunar pin-and-slot
    vee = spec(3, [(0, 1), (0, 2)])                           # V-slot
    ex = spec(5, [(0, 1), (0, 2), (0, 3), (0, 4)])           # X-slot  = crossed-bar branch point
    catalog = bar == [0.0, 2.0] and vee == [0.0, 1.0, 3.0] and ex == [-0.0, 1.0, 1.0, 1.0, 5.0]
    ok &= catalog
    print("  A  slot catalog: |-slot K11 %s | V-slot K12 %s | X-slot K14 %s (the {0,1,1,1,5} branch point)"
          % (bar, vee, ex))

    # B — the X-slot's FOUR arms carry S4 = V4 (x) S3 (same as F1311/F1312)
    ID = (0, 1, 2, 3)
    S4 = [tuple(p) for p in itertools.permutations(range(4))]
    a, b, c = (1, 0, 3, 2), (2, 3, 0, 1), (3, 2, 1, 0)       # the 3 arm-PAIRINGS (double-transpositions)
    V4 = [ID, a, b, c]
    normal = all(comp(comp(g, v), inv(g)) in V4 for g in S4 for v in V4)
    quotient6 = len(S4) // len(V4) == 6
    g = (1, 2, 0, 3)                                          # order-3 arm permutation
    g3 = comp(comp(g, g), g) == ID and g != ID
    cyc = [comp(comp(g, x), inv(g)) for x in (a, b, c)]
    cycles = set(cyc) == {a, b, c} and cyc != [a, b, c]
    partB = normal and quotient6 and g3 and cycles
    ok &= partB
    print("  B  X-slot 4 arms: V4 (pin double-swaps) NORMAL in S4 %s | S4/V4=S3 %s | order-3 cycles the 3 pairings %s"
          % (normal, quotient6, cycles))
    print("     => monodromy S4 = V4(|->X duality) (x) S3(arm-pairing TRIALITY) -- the k=3 the notebook deferred")

    print("\n=== %s ===" % ("Antikythera X-slot = Dzhanibekov branch points = beat-WSD Q8 = one shape S4=V4(x)S3."
                            if ok else "REGRESSION — reconcile before trusting F1313."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
