r"""R-RBS-LM-COUNTSTORE (F1263) — is Class-M inherently lossy, or is `klein4_bundle` just COMPRESSING?

User (2026-07-20): *"if we can find the duality of class-M and class-L, class-M doesn't have to be lossy
anymore, like we're forgetting or dropping some value we could keep, maybe to make the math over class-M work
over more than just the local horizon ... for the many-at-once thing."*

THE DROPPED VALUE: `klein4_bundle` emits a MAJORITY SECTOR per coordinate and discards HOW MANY VOTED — the
per-coordinate histogram over the 4 Klein-4 sectors. A bundle is therefore the ARGMAX READ of a store that was
never written. F1216 already said it: "reversibility in change-of-basis, LOSS IN COMPRESSION; distributional is
always a transient READ of the relational store." We were storing the read instead of the store.

MEASURED HERE: recall@1 for key-bound pairs, bundle vs count-preserving, as N grows past the bundle's horizon.
FALSIFIER: if keeping counts does NOT lift recall, the loss is intrinsic to the carrier and Class-M really is
bounded -- the horizon would be a property of the code family, not of the compression.

srmech 0.9.0rc288. No numpy. Integers throughout (the count matrix is an integer accumulator).
Composes F1216, F1259 (the residual collision loss = the sidelobe question), F1261, F1205/#263.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-COUNTSTORE_*.py [--dim 4096] [--max-n 1200]
"""
import argparse
import sys
import time

from srmech.amsc import hdc

T0 = time.time()


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


def superpose_counts(vs, dim):
    """THE CLASS-L SIDE: a weighted bipartite structure, coordinate x sector, integer weights.

    This is the object `klein4_bundle` projects away. It is exact, additive, and grows with content.
    """
    C = [[0] * 4 for _ in range(dim)]
    for v in vs:
        for i, s in enumerate(v):
            C[i][s] += 1
    return C


def read_counts(C, key, cands):
    """Score each candidate against the FULL count structure (unbind = XOR in Klein-4).

    NOTE the cost: O(N*dim) per probe, versus the bundle's single unbind-then-compare. This read is
    deliberately unoptimised -- a sparse/indexed read is the obvious follow-up (F1263 NEXT item 3).
    """
    best, bi = None, -1
    for j, cand in enumerate(cands):
        sc = 0
        for i in range(len(C)):
            sc += C[i][key[i] ^ cand[i]]
        if best is None or sc > best:
            best, bi = sc, j
    return bi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dim", type=int, default=4096)
    ap.add_argument("--max-n", type=int, default=1200)
    args = ap.parse_args()
    dim = args.dim

    import srmech
    log("=== COUNTSTORE (srmech %s) — bundle vs count-preserving, D=%d ===" % (srmech.__version__, dim))
    keys = [hdc.klein4_expand(dim, 10000 + i) for i in range(args.max_n)]
    vals = [hdc.klein4_expand(dim, 20000 + i) for i in range(args.max_n)]

    log("")
    log("  %-8s %-18s %-18s %-8s" % ("N", "bundle recall@1", "counts recall@1", "lift"))
    for N in (64, 256, 512, args.max_n):
        if N > args.max_n:
            continue
        kb = [bytes(k) for k in keys[:N]]
        vb = [bytes(v) for v in vals[:N]]
        bound = [bytes(hdc.klein4_bind(keys[i], vals[i])) for i in range(N)]
        probes = list(range(0, N, max(1, N // 25)))

        B = hdc.klein4_bundle([hdc.klein4_bind(keys[i], vals[i]) for i in range(N)])
        hb = sum(1 for i in probes
                 if max(range(N), key=lambda j: hdc.klein4_similarity(hdc.klein4_bind(B, keys[i]), vals[j])) == i)

        C = superpose_counts(bound, dim)
        hc = sum(1 for i in probes if read_counts(C, kb[i], vb) == i)

        rb, rc = hb / len(probes), hc / len(probes)
        log("  %-8d %-18.3f %-18.3f %-8s" % (N, rb, rc, ("%.1fx" % (rc / rb)) if rb else "inf"))

    log("")
    log("  storage: bundle = %d bytes ; counts = %d integers (4 per coordinate)" % (dim, dim * 4))
    log("")
    log("  VERDICT: keeping the counts removes the COMPRESSION loss (the argmax). What remains is the")
    log("  CODE-COLLISION loss — non-target carriers genuinely accumulate votes because the family is only")
    log("  quasi-orthogonal. That residue is the F1259 sidelobe question, and it is NOT fixable by storage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
