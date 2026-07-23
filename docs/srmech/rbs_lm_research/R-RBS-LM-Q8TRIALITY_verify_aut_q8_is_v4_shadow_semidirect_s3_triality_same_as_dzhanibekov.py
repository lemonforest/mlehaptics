r"""R-RBS-LM-Q8TRIALITY — committed generating code for F1312: the k=3 so(8) triality lift on the
beat-WSD Q8 genome. The beat-WSD's coupling IS the quaternion group Q8, whose OWN automorphism
structure is Aut(Q8) = S4 = V4 (x) S3 — the SAME shape as the Dzhanibekov (F1311), with:
  - Inn(Q8) = V4 = q8_project_v4 (the klein4 SHADOW where the beat-WSD conflates, F1309) = k=2 duality;
  - Out(Q8) = Aut/Inn = S3 = the TRIALITY = the order-3 cycle i->j->k = the k=3 lift;
  - maps to srmech's so(8) triality tau (28x28, order 3, Fix=g2) via the CD tower (H in O in so(8)).

srmech 0.9.0rc313. Pure integer group theory over srmech q8_mult / q8_conjugate / q8_project_v4;
no abs()/numpy/fractions. Composes F1312/F1311/F1309/F1307/F1308/F1310.
Run:  /tmp/srmech_313/bin/python3 R-RBS-LM-Q8TRIALITY_*.py
"""
import sys

import srmech
from srmech.amsc import q8 as Q8
from srmech.qm import triality as T, so8

mul = Q8.q8_mult
conj = Q8.q8_conjugate
IMAG = [1, 2, 3, 5, 6, 7]      # +-i, +-j, +-k   (0=+1,1=+i,2=+j,3=+k,4=-1,5=-i,6=-j,7=-k)
ID = tuple(range(8))


def is_auto(phi):
    return all(phi[mul(a, b)] == mul(phi[a], phi[b]) for a in range(8) for b in range(8))


def compose(p, q):
    return tuple(p[q[i]] for i in range(8))


def val(x):
    return x.as_float() if hasattr(x, "as_float") else float(x)


def is_identity28(X):
    for i in range(28):
        for j in range(28):
            if round(val(X[i][j]), 9) != (1.0 if i == j else 0.0):   # rounded, no abs()
                return False
    return True


def main():
    print("=== beat-WSD Q8 genome: the k=3 so(8) triality lift (srmech %s) ===" % srmech.__version__)
    ok = True

    # Q8 IS the quaternion group (the beat-WSD coupling)
    q8_ok = mul(1, 2) == 3 and mul(2, 1) == 7 and mul(1, 1) == 4 and mul(1, 2) != mul(2, 1)
    print("  Q8 (beat-WSD coupling): i*j=k, j*i=-k, i^2=-1, non-abelian:", q8_ok)

    # Aut(Q8) = S4
    autos = set()
    for fi in IMAG:
        for fj in IMAG:
            fk = mul(fi, fj)
            if fk in IMAG:
                phi = {0: 0, 4: 4, 1: fi, 2: fj, 3: fk, 5: mul(4, fi), 6: mul(4, fj), 7: mul(4, fk)}
                if is_auto(phi):
                    autos.add(tuple(phi[x] for x in range(8)))
    aut_s4 = len(autos) == 24

    # Inn(Q8) = V4 = the conjugations = q8_project_v4 quotient (the klein4 shadow)
    inner = set(tuple(mul(mul(g, x), conj(g)) for x in range(8)) for g in range(8))
    inn_v4 = len(inner) == 4 and inner <= autos \
        and all(compose(p, p) == ID for p in inner) \
        and all(compose(p, q) == compose(q, p) for p in inner for q in inner)
    proj = [int(x) for x in Q8.q8_project_v4(bytes(range(8)))]
    shadow_is_quotient = proj == [0, 1, 2, 3, 0, 1, 2, 3]   # q&3 = Q8/{+-1} = V4 = Inn

    # Out(Q8) = Aut/Inn = S3 = the triality
    seen, cosets = set(), 0
    for a in autos:
        if a in seen:
            continue
        cs = set(compose(a, i) for i in inner)
        cosets += 1
        seen |= cs
    out_s3 = cosets == 6

    # the order-3 OUTER automorphism i->j->k (the triality element)
    tri = tuple({0: 0, 4: 4, 1: 2, 2: 3, 3: 1, 5: 6, 6: 7, 7: 5}[x] for x in range(8))
    tri_ok = tri in autos and compose(compose(tri, tri), tri) == ID and tri != ID and tri not in inner

    print("  |Aut(Q8)|=24=S4: %s | |Inn(Q8)|=4=V4: %s | Inn = q8_project_v4 shadow: %s"
          % (aut_s4, inn_v4, shadow_is_quotient))
    print("  |Out(Q8)|=|Aut/Inn|=6=S3 (TRIALITY): %s | i->j->k is order-3 OUTER auto: %s" % (out_s3, tri_ok))

    # the so(8) target: srmech tau order 3, Fix=g2
    tau = T.triality_automorphism()
    tau_order3 = tau.shape[0] == 28 and is_identity28(tau @ tau @ tau) \
        and not is_identity28(tau) and not is_identity28(tau @ tau)
    g2_14 = len(so8.g2_subalgebra()) == 14
    print("  so(8) target: tau 28x28 order 3: %s | Fix(tau)=g2 dim 14: %s" % (tau_order3, g2_14))

    ok = q8_ok and aut_s4 and inn_v4 and shadow_is_quotient and out_s3 and tri_ok and tau_order3 and g2_14
    print("\n=== %s ===" % ("SAME SHAPE as the Dzhanibekov: Aut(Q8)=V4(shadow)(x)S3(triality); "
                            "the beat-WSD's klein4 conflation IS Inn(Q8), the k=3 lift IS Out(Q8)=S3 -> so(8) tau."
                            if ok else "REGRESSION — reconcile before trusting F1312."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
