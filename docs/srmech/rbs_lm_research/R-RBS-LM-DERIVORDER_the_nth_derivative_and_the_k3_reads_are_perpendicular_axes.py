r"""R-RBS-LM-DERIVORDER — the nth time-derivative axis and the op(x)operand(x)responsion axis are
PERPENDICULAR, and the discrete/continuous bridge between them is an IDENTITY, not an analogy.

User (2026-07-21): *"abstractly I'd be talking about the nth time-derivatives of an asymmetric resonating
hyperloop universe ... if this does happen to somehow fit part of the shape of the op(x)operand(x)responsion
and is also a series of nth time derivatives of relationships, where some discrete cyclic and continuous form
math works for both."*

TWO CLAIMS, BOTH DERIVABLE (no fitting, so not vulnerable to the failure mode that dissolved F1265-F1271):

(1) THE BRIDGE IS AN IDENTITY.
      CONTINUOUS : d^n/dt^n e^{-tL} = (-L)^n e^{-tL}      -- derivative ORDER = POWER of Class-L
      DISCRETE   : n-step walk / n-hop reach = L^n         -- same operator, same n
    So "nth time-derivative of relationships" and "n-step relationship walk" are THE SAME OBJECT L^n read two
    ways. This is what "discrete cyclic and continuous form math works for both" cashes out to, exactly.

(2) THE TWO AXES ARE PERPENDICULAR, not the same shape.
      k=3            = three READS of ONE L (eigenvectors / edges / eigenvalues)
      nth-derivative = L raised to the POWER n
    Together they form a 2-D grid (read x order). And the order acts DIFFERENTLY on each read:
      op         (eigenvectors) : INVARIANT under n   -- L v = lam v  =>  L^n v = lam^n v, SAME v
      responsion (eigenvalues)  : lam -> lam^n        -- the order LIVES here
      operand    (edges)        : 1-hop -> n-hop      -- the order SPREADS here

THE CONSEQUENCE WORTH KEEPING: derivative-order information is carried ONLY by the responsion and the
edge-reach. **A distributional read is BLIND to derivative order** -- the eigenvector basis is identical at
every n. That is a hard constraint on what a spectral read can recover, and it is an algebraic identity.

WHAT THIS DOES NOT DO: it does not rescue the 2*alpha ~ 1.65 question. alpha is a SCALING exponent of N_crit
vs dim, not a derivative order, and no derivation connects them. What it does supply is a principled place to
look: lam^n is where order lives, so an order-n shadow would show on the RESPONSION axis, not on the capacity
curve. Different measurement, different object.

srmech 0.9.0rc288. No numpy. Composes F1270 (the other structural result that held), F1271 (the fitted ones
that did not), F1061/F1063 (the EPH propagator; scale as a fractal TOWER), F1216 (L=store / M=read),
#243/F1070 (the asymmetric-resonator arc this feeds), #231/PKG-3.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-DERIVORDER_*.py
"""
import sys
from array import array

from srmech.amsc import cascade, laplacian as L
from srmech.amsc.mat import Mat


def dense(M):
    n = len(M)
    return [[float(M[i][j]) for j in range(n)] for i in range(n)]


def mul(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]


def to_mat(A):
    n = len(A)
    return Mat(array("d", [x for r in A for x in r]), n, n)


def main():
    import srmech
    print("=== DERIVORDER (srmech %s) ===" % srmech.__version__)

    # ---- (1) the bridge: order n  <->  n-hop reach ----
    print("\n--- (1) THE BRIDGE: derivative order n == n-hop reach (path graph 0-1-2-3) ---")
    print("    CONTINUOUS  d^n/dt^n e^{-tL} = (-L)^n e^{-tL}   (order = power of L)")
    n = 4
    A = [[0.0] * n for _ in range(n)]
    for u, v in [(0, 1), (1, 2), (2, 3)]:
        A[u][v] = A[v][u] = 1.0
    P = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for k in range(1, 4):
        P = mul(P, A)
        reach = [j for j in range(n) if P[0][j] != 0]
        print("    A^%d  node 0 reaches %-10s  <- exactly the %d-hop set" % (k, reach, k))
    print("    => 'nth time-derivative of relationships' and 'n-step walk' are the SAME L^n.")

    # ---- (2) how order acts on each of the k=3 reads ----
    print("\n--- (2) THE ORDER ACTS DIFFERENTLY ON EACH k=3 READ (5-cycle) ---")
    m = 5
    Lobj = L.dense_laplacian(m, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)])
    Lm = dense(Lobj)
    ev1 = sorted(float(x) for x in L.symmetric_eigendecompose(Lobj)[0])
    L2 = mul(Lm, Lm)
    L3 = mul(L2, Lm)
    ev2 = sorted(float(x) for x in L.symmetric_eigendecompose(to_mat(L2))[0])
    ev3 = sorted(float(x) for x in L.symmetric_eigendecompose(to_mat(L3))[0])
    print("    RESPONSION (eigenvalues)")
    print("      L^1    %s" % " ".join("%7.3f" % x for x in ev1))
    print("      L^2    %s" % " ".join("%7.3f" % x for x in ev2))
    print("      lam^2  %s" % " ".join("%7.3f" % x for x in sorted(x * x for x in ev1)))
    print("      L^3    %s" % " ".join("%7.3f" % x for x in ev3))
    print("      lam^3  %s" % " ".join("%7.3f" % x for x in sorted(x ** 3 for x in ev1)))
    def close(p, q):   # Class-K pin-slot magnitude, never the builtin
        return all(cascade.magnitude(a - b) < 1e-6 for a, b in zip(p, q))
    ok = close(ev2, sorted(x * x for x in ev1)) and close(ev3, sorted(x ** 3 for x in ev1))
    print("      => lam -> lam^n : %s" % ("CONFIRMED" if ok else "NO"))
    print("    OP (eigenvectors)  L v = lam v => L^n v = lam^n v — SAME v at every n (identity)")
    print("    OPERAND (edges)    support of L^n = the n-hop neighbourhood (part 1)")

    print("\n--- THE STRUCTURE ---")
    print("    op         (eigenvectors) : INVARIANT under n  -- order is INVISIBLE here")
    print("    responsion (eigenvalues)  : lam -> lam^n       -- order LIVES here")
    print("    operand    (edges)        : 1-hop -> n-hop     -- order SPREADS here")
    print("    => a DISTRIBUTIONAL read cannot recover derivative order. Algebraic, not empirical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
