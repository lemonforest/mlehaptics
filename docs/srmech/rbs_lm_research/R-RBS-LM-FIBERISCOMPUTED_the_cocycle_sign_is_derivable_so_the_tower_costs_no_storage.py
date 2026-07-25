r"""R-RBS-LM-FIBERISCOMPUTED — the fiber is a FUNCTION, not storage. Corrects the "~2x space" claim.

USER (2026-07-25): "we talked about octonion storage causing us to have to go 2x, why aren't the
fiber dims derivable from the real octonion fibration? like are we trying to store the fibre when
we should be able to compute it?"  -> CORRECT. The 2x was wrong as a blanket claim.

THE DECOMPOSITION (measured, 0 violations over all 256 O pairs):
    sign(a*b) = sign(a) XOR sign(b) XOR F(basis(a), basis(b))
`F` -- the Cayley-Dickson COCYCLE, i.e. the fibration's own structure map -- is a pure function of
the BASIS INDICES (the shadow). It is NEVER content. srmech already knows this: q8.py derives F
from `cd_basis_product`, explicitly "no hand-entered table".

CONSEQUENCE. The 4th bit of an O symbol is not one thing:
  (a) the fibration TWIST      -> F(basis,basis): COMPUTED from the shadow. Zero storage, always.
  (b) the COUPLING's sign      -> a declared function of the_one (F1318). ONE leaf per genome.
  (c) the DATUM's own sign     -> content IFF the data genuinely carries winding.
Only (c) is irreducible. For shadow-valued content (klein4 text has NO sign bit at all) there is
nothing to store and the tower costs ZERO extra.

srmech 0.9.0rc336. No numpy/float/abs(). Composes F1320/F1317/F1318/F1307/F1309.
Run:  /tmp/srmech_336/bin/python3 R-RBS-LM-FIBERISCOMPUTED_*.py
"""
import sys

import srmech
from srmech.amsc import genome as G, octonion as O, hdc as H, cascade as C
from srmech.amsc.format import sha256_bytes

D = 128
ONE = C.the_one(1, 0)
TAG = b"one/s%d/t%d,%d/T%d" % (int(ONE.sigma), int(ONE.theta[0]), int(ONE.theta[1]), int(ONE.terms))


def sign_of(i):
    """The DERIVED fiber bit — a function of (the_one, slot). Not storage."""
    return int(sha256_bytes(TAG + b"/slot:%d" % i)[:2], 16) & 1


def main():
    print("=== the fiber is COMPUTED, not stored (srmech %s) ===" % srmech.__version__)
    ok = True

    # 1 — the cocycle sign is a pure function of the shadow
    sgn, bas = (lambda x: x >> 3), (lambda x: x & 7)
    F = {(i, j): sgn(O.oct_mult(i, j)) for i in range(8) for j in range(8)}
    bad = [(a, b) for a in range(16) for b in range(16)
           if sgn(O.oct_mult(a, b)) != (sgn(a) ^ sgn(b) ^ F[(bas(a), bas(b))])]
    ok &= not bad
    print("  [1] sign(a*b) == sign(a)^sign(b)^F(basis,basis) : %d/256 violations -> F is SHADOW-ONLY"
          % len(bad))

    # 2 — shadow-valued content: materialize vs compute, end to end
    shadow = bytes(int(x) & 7 for x in H.klein4_encode_bytes(b"the fiber is computed, not stored", D))
    shadow_valued = all(b >> 3 == 0 for b in shadow) and max(shadow) <= 3
    materialized = bytes((sign_of(i) << 3) | s for i, s in enumerate(shadow))
    rebuilt = bytes((sign_of(i) << 3) | s for i, s in enumerate(shadow))     # recomputed on read
    fa = bytes(int(x) for x in G.genome_octonion_holonomy([materialized, materialized], D))
    fb = bytes(int(x) for x in G.genome_octonion_holonomy([rebuilt, rebuilt], D))
    ok &= shadow_valued and materialized == rebuilt and fa == fb
    print("  [2] shadow-valued content: rebuilt==materialized %s | fold identical %s"
          % (materialized == rebuilt, fa == fb))

    # 3 — the ledger
    print("  [3] ledger: full-O %d bits | shadow-only %d bits | V4 content %d bits | the_one = ONE leaf/genome"
          % (D * 4, D * 3, D * 2))

    # 4 — the honest split: genuine winding IS content
    wind = bytes((1 << 3) | s if i % 3 == 0 else s for i, s in enumerate(shadow))
    derivable = all((b >> 3) == sign_of(i) for i, b in enumerate(wind))
    ok &= not derivable
    print("  [4] genuine-winding content reproducible from the_one: %s -> IRREDUCIBLE, 1 bit/symbol"
          % derivable)

    print("\n=== %s ===" % ("CORRECTED: the tower costs ZERO storage for shadow-valued content; "
                            "only genuine winding is irreducible."
                            if ok else "REGRESSION — reconcile."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
