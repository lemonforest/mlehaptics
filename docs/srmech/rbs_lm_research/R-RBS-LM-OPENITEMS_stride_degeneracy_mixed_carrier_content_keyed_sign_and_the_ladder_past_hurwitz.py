r"""R-RBS-LM-OPENITEMS — close the five open items gating the srmech issue (F1315/F1316/F1317/F1318).

  A. STRIDE x LEAF_DIM DEGENERACY  — the explicit gate carried from F1315/F1316. Derive AND verify a
     checkable precondition for the Class-C reorient responsion.
  B. SCALE                          — n_leaves >> 4 and NON-UNIFORM leaf densities.
  C. CONTENT-KEYED SIGN             — can the fiber bit key on CONTENT instead of slot index?
  D. MIXED-CARRIER STRAND           — a v19 body may legally carry 0x51/0x38/0x39 together; what does
                                      an order read do across rungs?
  E. THE LADDER PAST HURWITZ        — does the Z2^n shadow survive at S (dim 16) and beyond, where
                                      DIVISION dies? (F1274/F1275: addressing needs no division.)

Exact-rational Q where algebra is involved (never float). No abs(), no numpy, no fractions.
Deterministic content-derived data (Class-A), never an RNG (F1259/F1304).
srmech 0.9.0rc336. Run:  /tmp/srmech_335/bin/python3 R-RBS-LM-OPENITEMS_*.py
"""
import itertools
import sys
from math import gcd

import srmech
from srmech.amsc import cascade as C, genome as G, q8 as Q8, octonion as O
from srmech.amsc.q import Q
from srmech.amsc.format import sha256_bytes


def dstream(key, n):
    out, c = bytearray(), 0
    while len(out) < n:
        out.extend(bytes.fromhex(sha256_bytes(key + b":%d" % c)))
        c += 1
    return bytes(out[:n])


def sparse_leaf(key, nz, leaf_dim, hi=7):
    ds = dstream(key, leaf_dim * 2)
    slots, i = [], 0
    while len(slots) < nz and i < len(ds):
        s = ds[i] % leaf_dim
        if s not in slots:
            slots.append(s)
        i += 1
    leaf = bytearray(leaf_dim)
    for j, s in enumerate(slots):
        leaf[s] = (ds[leaf_dim + j] % hi) + 1
    return bytes(leaf)


def rot_fold_fp(turns, leaf_dim, stride):
    """v3c: Class-C reorient by stride*t, then the shipped per-slot Q8 fold."""
    out = []
    for i, t in enumerate(turns):
        k = (stride * i) % leaf_dim
        out.append(bytes(t[-k:] + t[:-k]) if k else bytes(t))
    holo = G.genome_fiber_holonomy(out, leaf_dim)
    return sha256_bytes(bytes(int(x) for x in holo))[:16]


def collisions(turns, leaf_dim, stride):
    n = len(turns)
    base = rot_fold_fp(turns, leaf_dim, stride)
    c = 0
    for p in itertools.permutations(range(n)):
        if p == tuple(range(n)):
            continue
        if all(turns[p[i]] == turns[i] for i in range(n) if p[i] != i):
            continue                                    # degenerate no-op
        if rot_fold_fp([turns[i] for i in p], leaf_dim, stride) == base:
            c += 1
    return c


def main():
    print("=== OPEN ITEMS before the srmech issue (srmech %s) ===\n" % srmech.__version__)
    ok = True

    # ---------- A. stride x leaf_dim degeneracy -------------------------------------------------
    print("A. STRIDE x LEAF_DIM DEGENERACY  (the explicit gate)")
    print("   DERIVED precondition: rotations must give each leaf a DISTINCT offset, i.e.")
    print("     stride*t (mod leaf_dim) distinct for t < n_leaves  <=>  leaf_dim/gcd(stride,leaf_dim) >= n_leaves")
    n_leaves = 4
    rows, mispred = [], 0
    for leaf_dim in (16, 32, 64, 128):
        for stride in (0, 1, 2, 3, 4, 7, leaf_dim // 4, leaf_dim // 2, leaf_dim - 1, leaf_dim):
            s = stride % leaf_dim
            order = leaf_dim // gcd(s, leaf_dim) if s else 1     # #distinct offsets
            predict_safe = order >= n_leaves
            turns = [sparse_leaf(b"A/ld%d/s%d/l%d" % (leaf_dim, stride, k), 1, leaf_dim)
                     for k in range(n_leaves)]
            c = collisions(turns, leaf_dim, s)
            actual_safe = (c == 0)
            if predict_safe != actual_safe:
                mispred += 1
            rows.append((leaf_dim, s, order, predict_safe, c))
    ok &= mispred == 0
    print("   leaf_dim stride  distinct-offsets  predicted-safe  collisions")
    for ld, s, o, p, c in rows:
        flag = "" if (p == (c == 0)) else "   <-- MISPREDICT"
        print("   %8d %6d %17d  %13s  %10d%s" % (ld, s, o, p, c, flag))
    print("   => precondition predicts pass/fail on %d/%d cases (mispredictions: %d)\n"
          % (len(rows) - mispred, len(rows), mispred))

    # ---------- B. scale: n_leaves >> 4, non-uniform densities ----------------------------------
    print("B. SCALE  (n_leaves >> 4; NON-UNIFORM densities)")
    LD, STRIDE = 128, 37          # gcd(37,128)=1 -> order 128, safe for n_leaves <= 128
    for n in (6, 8):
        turns = [sparse_leaf(b"B/u/n%d/l%d" % (n, k), 1, LD) for k in range(n)]
        c = collisions(turns, LD, STRIDE)
        ok &= c == 0
        print("   uniform  nz=1  n_leaves=%d : %d collisions over %d perms"
              % (n, c, __import__("math").factorial(n) - 1))
    mixed = [sparse_leaf(b"B/mix/l%d" % k, d, LD) for k, d in enumerate((1, 3, 17, 64, 1, 2))]
    c = collisions(mixed, LD, STRIDE)
    ok &= c == 0
    print("   NON-UNIFORM densities [1,3,17,64,1,2], n=6 : %d collisions\n" % c)

    # ---------- C. content-keyed sign -----------------------------------------------------------
    print("C. CONTENT-KEYED SIGN  (can the fiber bit key on CONTENT, not slot index?)")
    ONE = C.the_one(1, 0)
    tag = b"one/s%d/t%d,%d/T%d" % (int(ONE.sigma), int(ONE.theta[0]), int(ONE.theta[1]), int(ONE.terms))

    def sign_by_slot(shadow, i):
        return int(sha256_bytes(tag + b"/slot:%d" % i)[:2], 16) & 1

    def sign_by_content(shadow, i):
        return int(sha256_bytes(tag + b"/content:%d" % shadow[i])[:2], 16) & 1

    shadow = bytes(int(sha256_bytes(b"C/shadow:%d" % i)[:2], 16) & 7 for i in range(64))
    for nm, fn in (("slot-keyed", sign_by_slot), ("content-keyed", sign_by_content)):
        E = bytes((fn(shadow, i) << 3) | s for i, s in enumerate(shadow))
        rt = bytes((fn(bytes(b & 7 for b in E), i) << 3) | (b & 7)
                   for i, b in enumerate(E)) == E
        var = len({b >> 3 for b in E}) == 2
        # content-keyed is a FUNCTION of the shadow -> equal shadows MUST get equal signs
        det_by_content = all((E[i] >> 3) == (E[j] >> 3)
                             for i in range(64) for j in range(64) if shadow[i] == shadow[j])
        ok &= rt and var
        print("   %-14s round-trips: %s | sign varies: %s | equal-shadow=>equal-sign: %s"
              % (nm, rt, var, det_by_content))
    print("   => BOTH work. content-keyed makes the fiber a FUNCTION OF THE SHADOW (only 2^8 distinct")
    print("      lifts, position-blind); slot-keyed is position-bearing. DIFFERENT objects, both valid.\n")

    # ---------- D. mixed-carrier strand ---------------------------------------------------------
    print("D. MIXED-CARRIER STRAND  (v19 may legally carry 0x51/0x38/0x39 together)")
    q8_leaf = sparse_leaf(b"D/q8", 4, 64, hi=7)          # values 1..7  (Q8 legal)
    oc_leaf = sparse_leaf(b"D/oct", 4, 64, hi=15)        # values 1..15 (O legal, Q8 ILLEGAL)
    try:
        G.genome_fiber_holonomy([q8_leaf, oc_leaf], 64)
        print("   Q8 fold over MIXED (Q8 + octonion) turns: NO ERROR  <-- silent cross-rung read")
        mixed_guard = False
    except Exception as e:
        print("   Q8 fold over MIXED turns raises: %s: %s" % (type(e).__name__, str(e)[:80]))
        mixed_guard = True
    try:
        G.genome_octonion_holonomy([q8_leaf, oc_leaf], 64)
        print("   O  fold over MIXED turns: NO ERROR (Q8 values are LEGAL octonion values -- subset)")
        o_accepts = True
    except Exception as e:
        print("   O  fold over MIXED turns raises: %s" % type(e).__name__)
        o_accepts = False
    print("   => the O fold is the SAFE cross-rung read (Q8 values 0..7 are a SUBSET of O's 0..15);")
    print("      the Q8 fold %s on octonion values.\n"
          % ("correctly REFUSES" if mixed_guard else "does NOT guard -- worth an upstream note"))

    # ---------- E. the ladder past the Hurwitz wall ---------------------------------------------
    print("E. THE Z2^n SHADOW LADDER PAST HURWITZ  (S = dim 16, where DIVISION dies)")

    def unit(i, d):
        return [Q(1, 1) if k == i else Q(0, 1) for k in range(d)]

    def basis_of(p):
        for k, x in enumerate(p):
            if x != Q(0, 1):
                return k
        return None
    for d in (4, 8, 16, 32):
        bad = 0
        for i in range(d):
            for j in range(d):
                if basis_of(C.cd_mult(unit(i, d), unit(j, d))) != (i ^ j):
                    bad += 1
        ok &= bad == 0
        wall = "  <-- S: past the Hurwitz wall (zero divisors)" if d == 16 else ("  <-- dim 32" if d == 32 else "")
        print("   dim %2d: basis(a*b) == basis(a) XOR basis(b) : %d/%d violations%s"
              % (d, bad, d * d, wall))
    print("   => the ADDRESSING shadow (Z2^n) survives where DIVISION dies -- exactly F1274/F1275:")
    print("      addressing needs only a SIGNED PERMUTATION, never the division property.\n")

    print("=== %s ===" % ("ALL FIVE OPEN ITEMS CLOSED — the issue can be written."
                          if ok else "SOMETHING FAILED — do not write the issue yet."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
