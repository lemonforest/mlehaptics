r"""R-RBS-LM-CHUNKLAW — (A) build the CHUNKED store the capacity law implies, and (B) test whether the
"N/dim ratio" is a CONSTANT-to-be-found or a PROJECTION whose apparent value shifts with coherency/substrate.

User (2026-07-20): *"do the chunked stores at dim/16 each and also investigate if the N/dim ratio happens to
be like our physical/mechanical coupled turn ratio? I think that all of our human research, or most, treats
this like some magic number to find like pi, whereas it's more likely a projection that just happens to look
slightly different from coherency and substrate differences that make finding an exact value different than
finding an exact, perhaps k=3 ratio."*

THE USER IS CORRECTING A REAL ERROR OF MINE, and the correction is checkable. F1265 reported thresholds at
N/dim = 1/16, 1/8, 1/4, 1/2 and called the ratio law "confirmed". But I chose N as 2^k*1000 and dim as 2^m, so
**N/dim landed on powers of two BY CONSTRUCTION**. The "1/16" is where I sampled, not a measured critical
point. Worse: ratio-law (N/dim const) and square-law (N/dim^2 const) BOTH fit that data, because the two
discriminating points (N=2000 and N=4000 at dim=16384) both sat on the 0.800 plateau.

So this harness does two things the last one could not:

(B1) SAMPLE OFF THE POWER-OF-TWO GRID. N chosen on a ~1.5x geometric ladder (non-dyadic), so any structure in
     the curve is a property of the object rather than of my sampling.
(B2) DISCRIMINATE THE SCALING LAW. Measure recall(N, dim) at two dimensions and ask which rescaling collapses
     the two curves onto one: N/dim (ratio) or N/dim^2 (square, what a sqrt(N) noise argument predicts).
     Whichever collapses them is the real invariant -- and it is a RELATION, not a magic constant.
(B3) THREE REGIMES OR A SMOOTH DECAY? The k=3 reading predicts STRUCTURE (distinct regimes with a plateau);
     the "magic constant" reading predicts ONE threshold; a pure noise argument predicts a SMOOTH sigmoid.
     Dense sampling can tell these apart. FALSIFIER for k=3: if the curve is a featureless monotone decay with
     no plateau, there is no three-regime structure and the k=3 reading is not supported by this object.

(A) THE CHUNKED STORE. F1265's capacity number says one store cannot hold a corpus; chunking is the implied
    architecture and it is also what [[feedback_dim_size_2n_capacity_is_D_independent]] already prescribes
    ("chunk for capacity"). Route each item to a chunk by content, keep each chunk at the measured capacity,
    and compare recall + storage + read cost against one big store holding the same items.

srmech 0.9.0rc288. Integer accumulators; no numpy.
Composes F1265 (whose 1/16 and "ratio law confirmed" are both corrected here), F1264, F1263,
[[feedback_dim_size_2n_capacity_is_D_independent]], F1205/#263 (couple, never merge).
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-CHUNKLAW_*.py
"""
import sys
import time
from array import array

from srmech.amsc import cascade, hdc

T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


def build(bound, dim):
    C = array("i", bytes(4 * dim * 4))
    for v in bound:
        b = 0
        for s in v:
            C[b + s] += 1
            b += 4
    return C


def read_full(C, key, cands):
    best, bi = None, -1
    for j, c in enumerate(cands):
        sc, b = 0, 0
        for k, x in zip(key, c):
            sc += C[b + (k ^ x)]
            b += 4
        if best is None or sc > best:
            best, bi = sc, j
    return bi


def carriers(n, dim):
    k = [bytes(hdc.klein4_random(dim, seed=10_000 + i)) for i in range(n)]
    v = [bytes(hdc.klein4_random(dim, seed=20_000 + i)) for i in range(n)]
    b = [bytes(x ^ y for x, y in zip(a, c)) for a, c in zip(k, v)]
    return k, v, b


def recall_at(n, dim, k, v, b, n_probe=8):
    C = build(b[:n], dim)
    pr = list(range(0, n, max(1, n // n_probe)))
    return sum(1 for p in pr if read_full(C, k[p], v[:n]) == p) / len(pr)


# ---------------------------------------------------------------- (B) the law
def part_b():
    log("")
    log("=== (B) IS THE RATIO A CONSTANT, OR A PROJECTION? ===")
    log("  F1265 sampled N=2^k*1000 against dim=2^m, so N/dim fell on powers of two BY CONSTRUCTION.")
    log("  Sampling here on a ~1.5x NON-DYADIC ladder so the curve's shape is the object's, not mine.")

    LADDER = [96, 144, 216, 324, 486, 729, 1093, 1640]      # 1.5x geometric, no powers of two
    curves = {}
    for dim in (2048, 4096):
        k, v, b = carriers(max(LADDER), dim)
        log("")
        log("  dim=%d" % dim)
        log("    %-7s %-9s %-9s %-9s" % ("N", "N/dim", "N/dim^2", "recall"))
        row = []
        for n in LADDER:
            r = recall_at(n, dim, k, v, b)
            row.append((n, r))
            log("    %-7d %-9.4f %-9.2e %-9.3f" % (n, n / dim, n / (dim * dim), r))
        curves[dim] = row

    # (B2) which rescaling collapses the two curves?
    log("")
    log("  --- (B2) WHICH LAW COLLAPSES THE CURVES? ---")
    log("  ratio law  predicts: recall(N, 2048) == recall(2N, 4096)")
    log("  square law predicts: recall(N, 2048) == recall(4N, 4096)")
    a = dict(curves[2048])
    c = dict(curves[4096])
    log("    %-8s %-12s %-14s %-14s" % ("N@2048", "recall", "ratio-pred(2N)", "square-pred(4N)"))
    err_r, err_s, nr, ns = 0.0, 0.0, 0, 0
    for n, r in curves[2048]:
        p2, p4 = c.get(2 * n), c.get(4 * n)
        s2 = "%.3f" % p2 if p2 is not None else "  --"
        s4 = "%.3f" % p4 if p4 is not None else "  --"
        log("    %-8d %-12.3f %-14s %-14s" % (n, r, s2, s4))
        if p2 is not None:
            err_r += cascade.magnitude(r - p2); nr += 1
        if p4 is not None:
            err_s += cascade.magnitude(r - p4); ns += 1
    log("")
    if nr and ns:
        log("    mean |error| ratio-law  = %.4f  (%d comparable points)" % (err_r / nr, nr))
        log("    mean |error| square-law = %.4f  (%d comparable points)" % (err_s / ns, ns))
        log("    => %s collapses the curves better" %
            ("RATIO (N/dim)" if err_r / nr < err_s / ns else "SQUARE (N/dim^2)"))

    # (B3) three regimes or a smooth decay?
    log("")
    log("  --- (B3) THREE REGIMES (k=3) OR A SMOOTH DECAY? ---")
    for dim in (2048, 4096):
        rs = [r for _, r in curves[dim]]
        d1 = [rs[i + 1] - rs[i] for i in range(len(rs) - 1)]
        log("    dim=%-6d recall  %s" % (dim, " ".join("%.2f" % x for x in rs)))
        log("    %-11s deltas  %s" % ("", " ".join("%+.2f" % x for x in d1)))
        flats = sum(1 for x in d1 if cascade.magnitude(x) < 0.06)   # Class-K pin-slot, not the builtin
        log("    %-11s near-flat steps: %d / %d  -> %s" %
            ("", flats, len(d1),
             "PLATEAU present (structure)" if flats >= 2 else "featureless monotone decay"))
    log("")
    log("  FALSIFIER: a featureless monotone decay means NO three-regime structure in this object,")
    log("  and the k=3 reading would not be supported by THIS measurement (it may still hold elsewhere).")


# ---------------------------------------------------------------- (A) chunked stores
def part_a():
    log("")
    log("=== (A) CHUNKED STORES — one store per capacity unit, routed by content ===")
    dim = 4096
    M = 4000
    k, v, b = carriers(M, dim)

    log("  one BIG store, M=%d, dim=%d:" % (M, dim))
    t = time.time()
    big = recall_at(M, dim, k, v, b, n_probe=8)
    log("    recall %.3f   (%.1f s)   storage %d cells" % (big, time.time() - t, dim * 4))

    log("")
    log("  CHUNKED — chunk capacity from the measured curve, routed by content hash:")
    log("    %-9s %-8s %-10s %-12s %-14s" % ("cap", "chunks", "recall", "secs", "cells total"))
    for cap in (dim // 16, dim // 8, dim // 4):
        n_ch = (M + cap - 1) // cap
        buckets = [[] for _ in range(n_ch)]
        for i in range(M):
            buckets[hash(k[i]) % n_ch].append(i)          # content-routed, deterministic per run
        stores = []
        for bk in buckets:
            stores.append(build([b[i] for i in bk], dim) if bk else None)
        t = time.time()
        probes = list(range(0, M, max(1, M // 8)))
        hits = 0
        for p in probes:
            ch = hash(k[p]) % n_ch
            members = buckets[ch]
            if not members:
                continue
            got = read_full(stores[ch], k[p], [v[i] for i in members])
            hits += (members[got] == p)
        log("    %-9d %-8d %-10.3f %-12.1f %-14d" %
            (cap, n_ch, hits / len(probes), time.time() - t, n_ch * dim * 4))
    log("")
    log("  NOTE the honest trade: chunking multiplies TOTAL cells by the chunk count, but each read")
    log("  touches ONE chunk -- so storage grows while read cost FALLS. That is the melange shape")
    log("  (couple/route, never merge), not a compression win.")


def main():
    import srmech
    log("=== CHUNKLAW (srmech %s) ===" % srmech.__version__)
    part_b()
    part_a()
    log("")
    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
